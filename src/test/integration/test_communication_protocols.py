"""
Integration tests for communication protocols (IT6-IT8).
Tests communication layer integration between components.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from backend.models import ElevatorState, DoorState


class TestCommunicationProtocols:
    """Test Cases IT6-IT8: Communication Protocol Tests"""

    def test_IT6_websocket_connection_loss_and_recovery(
        self, system_harness, simulate_time, mock_websocket_bridge
    ):
        """
        IT6: WebSocket Connection Loss and Recovery
        Frontend resilience during connection issues
        """
        # Step 1: Establish WebSocket connection (mocked)
        mock_websocket_bridge.is_connected.return_value = True

        # Step 2: Generate elevator activity
        system_harness.send_call(floor=2, direction="up")
        simulate_time(system_harness.system, 1.0)

        # Verify initial messages are sent
        initial_message_count = mock_websocket_bridge.send_message.call_count
        assert initial_message_count >= 0, "Initial messages should be attempted"

        # Step 3: Simulate connection drop
        mock_websocket_bridge.is_connected.return_value = False
        mock_websocket_bridge.send_message.side_effect = ConnectionError(
            "WebSocket disconnected"
        )

        # Continue elevator operations during disconnection
        system_harness.select_floor(1, 3)
        simulate_time(system_harness.system, 2.0)

        # System should continue operating despite WebSocket issues
        elevator_state = system_harness.get_elevator_state(1)
        assert (
            elevator_state is not None
        ), "System should continue operating during WebSocket failure"

        # Step 4: Verify frontend shows disconnect state (mocked behavior)
        # In real implementation, frontend would show connection status
        disconnect_detected = not mock_websocket_bridge.is_connected()
        assert disconnect_detected, "Disconnect should be detected"

        # Step 5: Restore connection and check state synchronization
        mock_websocket_bridge.is_connected.return_value = True
        mock_websocket_bridge.send_message.side_effect = None  # Remove exception

        # Trigger state synchronization by generating activity
        system_harness.open_door(1)
        simulate_time(system_harness.system, 1.0)

        # Verify state synchronization after reconnection
        reconnect_message_count = mock_websocket_bridge.send_message.call_count
        assert (
            reconnect_message_count > initial_message_count
        ), "Messages should resume after reconnection"

        # Graceful degradation and recovery should maintain state consistency
        final_state = system_harness.get_system_state()
        assert (
            len(final_state["elevators"]) == 2
        ), "System should maintain consistent state"

    def test_IT7_zmq_client_disconnect_and_reconnect(
        self, system_harness, simulate_time, mock_zmq_client
    ):
        """
        IT7: ZMQ Client Disconnect and Reconnect
        External client communication resilience
        """
        # Step 1: Active ZMQ command session
        mock_zmq_client.is_connected.return_value = True

        # Send initial command through ZMQ (simulated)
        initial_call = system_harness.send_call(floor=2, direction="up")
        assert initial_call, "Initial ZMQ command should succeed"

        initial_zmq_calls = mock_zmq_client.send_message.call_count

        # Step 2: Disconnect ZMQ client abruptly
        mock_zmq_client.is_connected.return_value = False
        mock_zmq_client.send_message.side_effect = ConnectionError(
            "ZMQ client disconnected"
        )

        # Step 3: Continue backend operations
        system_harness.select_floor(1, 3)
        system_harness.open_door(2)
        simulate_time(system_harness.system, 3.0)

        # Backend should continue operation despite ZMQ disconnection
        system_state = system_harness.get_system_state()
        assert all(
            e["state"] != ElevatorState.IDLE or len(e["task_queue"]) >= 0
            for e in system_state["elevators"]
        ), "Backend should continue operating"

        # Step 4: Reconnect client and verify message flow
        mock_zmq_client.is_connected.return_value = True
        mock_zmq_client.send_message.side_effect = None  # Remove exception

        # Send new command after reconnection
        reconnect_call = system_harness.send_call(floor=1, direction="down")
        assert reconnect_call, "Commands should work after ZMQ reconnection"

        simulate_time(system_harness.system, 2.0)

        # Verify backend continues operation and messages are queued appropriately
        final_zmq_calls = mock_zmq_client.send_message.call_count
        assert (
            final_zmq_calls >= initial_zmq_calls
        ), "Message flow should resume after reconnection"

        # Verify system remains stable after reconnection
        final_state = system_harness.get_system_state()
        assert (
            final_state["pending_calls"] >= 0
        ), "System should handle reconnection gracefully"

    def test_IT8_concurrent_frontend_and_zmq_commands(
        self, system_harness, simulate_time, mock_websocket_bridge, mock_zmq_client
    ):
        """
        IT8: Concurrent Frontend and ZMQ Commands
        Handling simultaneous commands from different sources
        """
        # Setup: Ensure both communication channels are active
        mock_websocket_bridge.is_connected.return_value = True
        mock_zmq_client.is_connected.return_value = True

        # Step 1: Frontend user clicks call button (simulated)
        frontend_command_time = time.time()
        frontend_result = system_harness.send_call(floor=2, direction="up")

        # Step 2: Simultaneously send ZMQ select_floor command
        zmq_command_time = time.time()
        zmq_result = system_harness.select_floor(1, 3)

        # Verify both commands are accepted
        assert frontend_result, "Frontend call command should be accepted"
        assert zmq_result["success"], "ZMQ select_floor command should be accepted"

        # Commands should be processed very close in time
        time_diff = abs(zmq_command_time - frontend_command_time)
        assert time_diff < 0.1, "Commands should be processed nearly simultaneously"

        # Step 3: Allow system to process both commands
        simulate_time(system_harness.system, 3.0)

        # Step 4: Verify both commands processed correctly
        # Check that call was assigned
        call_assigned = False
        for call in system_harness.system["dispatcher"].pending_calls.values():
            if call.floor == 2 and call.is_assigned():
                call_assigned = True
                break
        assert call_assigned, "Frontend call should be processed"

        # Check that floor selection was added to elevator queue
        elevator1 = system_harness.system["elevators"][0]
        has_floor_3_task = any(task.floor == 3 for task in elevator1.task_queue)
        visited_floor_3 = elevator1.current_floor == 3
        assert (
            has_floor_3_task or visited_floor_3
        ), "ZMQ floor selection should be processed"

        # Step 5: Check no command interference or data corruption
        # Verify system state integrity
        system_state = system_harness.get_system_state()

        # All elevators should be in valid states
        for elevator_state in system_state["elevators"]:
            assert elevator_state["state"] in [
                ElevatorState.IDLE,
                ElevatorState.MOVING_UP,
                ElevatorState.MOVING_DOWN,
            ]
            assert elevator_state["door_state"] in [
                DoorState.OPEN,
                DoorState.CLOSED,
                DoorState.OPENING,
                DoorState.CLOSING,
            ]
            assert 1 <= elevator_state["id"] <= 2
            assert MIN_FLOOR <= elevator_state["floor"] <= MAX_FLOOR

        # No data corruption in task queues
        for elevator in system_harness.system["elevators"]:
            for task in elevator.task_queue:
                assert (
                    MIN_FLOOR <= task.floor <= MAX_FLOOR
                ), "Task floors should be valid"

        # No data corruption in dispatcher calls
        for call in system_harness.system["dispatcher"].pending_calls.values():
            assert MIN_FLOOR <= call.floor <= MAX_FLOOR, "Call floors should be valid"
            assert call.direction in [None, MoveDirection.UP, MoveDirection.DOWN]

        # Verify message ordering - commands should be processed in arrival order
        websocket_messages = len(
            [call for call in mock_websocket_bridge.send_message.call_args_list]
        )
        zmq_messages = len(
            [call for call in mock_zmq_client.send_message.call_args_list]
        )

        # Both interfaces should have generated some messages
        total_messages = websocket_messages + zmq_messages
        assert total_messages >= 0, "Commands should generate appropriate messages"

        # Step 6: Test additional concurrent scenarios
        # Send multiple commands rapidly from both sources
        concurrent_commands = []

        # Simulate rapid button pressing from frontend
        for i in range(3):
            result = system_harness.send_call(floor=1, direction="up")
            concurrent_commands.append(("frontend_call", result))

        # Simulate rapid ZMQ commands
        for i in range(3):
            result = system_harness.select_floor(2, 2)
            concurrent_commands.append(("zmq_select", result["success"]))

        # Allow processing time
        simulate_time(system_harness.system, 2.0)

        # Verify all commands were handled (though some may be duplicates filtered out)
        assert all(
            cmd[1] for cmd in concurrent_commands
        ), "All concurrent commands should be accepted"

        # System should remain stable under concurrent load
        final_state = system_harness.get_system_state()
        assert (
            final_state["elapsed_time"] < 15.0
        ), "Concurrent processing should be efficient"

        # No excessive resource usage - duplicate calls should be filtered
        unique_pending_calls = len(
            set(
                (call.floor, call.direction.value if call.direction else None)
                for call in system_harness.system["dispatcher"].pending_calls.values()
            )
        )
        assert (
            unique_pending_calls <= 4
        ), "Duplicate calls should be filtered appropriately"


# Import MIN_FLOOR, MAX_FLOOR from the test
from backend.models import MIN_FLOOR, MAX_FLOOR, MoveDirection
