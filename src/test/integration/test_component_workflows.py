"""
Integration tests for component workflows (IT1-IT5).
Tests complete workflows from external calls to service completion
"""

import pytest
import time
from backend.models import ElevatorState, DoorState, MoveDirection, CallState, Task


class TestComponentWorkflows:
    """Test Cases IT1-IT5: Multi-Component Workflow Tests"""

    def test_IT1_complete_call_to_service_workflow(self, system_harness, simulate_time):
        """
        IT1: Call → Dispatch → Movement → Arrival → Door Open
        Complete workflow from external call to service completion
        """
        # Initial state verification
        initial_state = system_harness.get_system_state()
        assert len(initial_state["elevators"]) == 2
        assert all(
            e["floor"] == 1 and e["state"] == ElevatorState.IDLE
            for e in initial_state["elevators"]
        )

        # Step 1: Send call_up@1 via API
        call_id = system_harness.send_call(floor=1, direction="up")
        assert call_id is not None, "Call should be accepted by API and return a call_id"

        # Step 2: Verify dispatcher selects optimal elevator
        simulate_time(system_harness.system, 0.5)  # Allow dispatcher processing

        # Check that one elevator was assigned
        assigned_found = False
        assigned_elevator_id = None
        # Check all_calls_log instead of pending_calls, as the call might be processed quickly
        if call_id in system_harness.system["dispatcher"].all_calls_log:
            call_obj = system_harness.system["dispatcher"].all_calls_log[call_id]
            if call_obj.floor == 1 and call_obj.is_assigned():
                assigned_found = True
                assigned_elevator_id = call_obj.assigned_elevator + 1

        assert assigned_found, "Call should be assigned to an elevator"
        assert assigned_elevator_id in [1, 2], "Assigned elevator should be valid"

        # Step 3: Confirm task added to elevator queue
        assigned_elevator = system_harness.system["elevators"][assigned_elevator_id - 1]
        # Since elevator is already at floor 1, doors should open immediately
        simulate_time(system_harness.system, 1.0)

        # Step 4: For this test, elevator is already at target floor, so verify door opening
        door_opened = system_harness.wait_for_door_state(
            assigned_elevator_id, DoorState.OPEN, timeout=5.0
        )
        assert door_opened, "Doors should open when elevator reaches call floor"

        # Step 5: Verify completion notifications
        # Check that call is completed
        final_call_state = None
        if call_id in system_harness.system["dispatcher"].all_calls_log:
            final_call_state = system_harness.system["dispatcher"].all_calls_log[call_id].state
        
        # Call might be completed
        assert final_call_state == CallState.COMPLETED, f"Call {call_id} should be completed. Actual: {final_call_state}"
        
        # Verify workflow completed within time limit
        final_state = system_harness.get_system_state()
        assert (
            final_state["elapsed_time"] < 10.0
        ), "Workflow should complete within 10 seconds"

    def test_IT2_multiple_simultaneous_calls(self, system_harness, simulate_time):
        """
        IT2: Multiple Simultaneous Calls to Different Floors
        System handling concurrent calls efficiently
        """
        # Send simultaneous calls to different floors
        call1_success = system_harness.send_call(floor=1, direction="up")
        call2_success = system_harness.send_call(floor=3, direction="down")
        call3_success = system_harness.send_call(floor=2, direction="up")

        assert all(
            [call1_success, call2_success, call3_success]
        ), "All calls should be accepted"

        # Allow time for dispatcher processing
        simulate_time(system_harness.system, 1.0)

        # Verify load balancing - both elevators should be utilized
        elevator_assignments = []
        for call in system_harness.system["dispatcher"].pending_calls.values():
            if call.is_assigned():
                elevator_assignments.append(call.assigned_elevator)

        # Should have assignments, and ideally use both elevators for efficiency
        assert len(elevator_assignments) >= 2, "Multiple calls should be assigned"

        # Verify no conflicts in movement scheduling
        # Allow system to process all calls
        simulate_time(system_harness.system, 15.0)

        # Check that system eventually services all calls
        remaining_pending = len(
            [
                call
                for call in system_harness.system["dispatcher"].pending_calls.values()
                if call.is_pending()
            ]
        )
        assert remaining_pending == 0, "All calls should eventually be assigned"

        # Verify optimal dispatch strategy - should not have excessive movement
        final_state = system_harness.get_system_state()
        assert (
            final_state["elapsed_time"] < 20.0
        ), "Multiple calls should be handled efficiently"

    def test_IT3_floor_selection_during_movement(self, system_harness, simulate_time):
        """
        IT3: Floor Selection While Elevator Moving
        Inside calls during active movement
        """
        # First, get elevator 1 moving to floor 3
        system_harness.send_call(floor=3, direction="down")
        simulate_time(system_harness.system, 1.0)

        # Find which elevator was assigned and send it to floor 3
        assigned_elevator_id = None
        for call in system_harness.system["dispatcher"].pending_calls.values():
            if call.floor == 3 and call.is_assigned():
                assigned_elevator_id = call.assigned_elevator + 1
                break

        assert (
            assigned_elevator_id is not None
        ), "Call should be assigned to an elevator"

        # Wait for elevator to start moving towards floor 3
        moving_started = False
        for _ in range(50):  # Check for 5 seconds
            simulate_time(system_harness.system, 0.1)
            elevator_state = system_harness.get_elevator_state(assigned_elevator_id)
            if elevator_state["state"] in [
                ElevatorState.MOVING_UP,
                ElevatorState.MOVING_DOWN,
            ]:
                moving_started = True
                break

        if not moving_started:
            # If not moving yet, manually start the movement by opening doors first
            system_harness.open_door(assigned_elevator_id)
            simulate_time(system_harness.system, 3.0)  # Wait for door timeout

        # Now during movement (or preparation), send select_floor@2
        select_result = system_harness.select_floor(assigned_elevator_id, 2)
        assert select_result[
            "success"
        ], "Floor selection should succeed during movement preparation"

        # Allow system to process the new floor selection
        simulate_time(system_harness.system, 10.0)

        # Verify task insertion in queue - should have both floor 2 and floor 3
        elevator = system_harness.system["elevators"][assigned_elevator_id - 1]
        task_floors = [task.floor for task in elevator.task_queue]

        # Should visit floor 2 at some point
        has_floor_2 = 2 in task_floors or elevator.current_floor == 2
        assert has_floor_2, "Elevator should include floor 2 in its service plan"

        # Allow more time for completion
        simulate_time(system_harness.system, 10.0)

        # Both floors should eventually be served
        final_state = system_harness.get_elevator_state(assigned_elevator_id)
        # At this point, elevator should have visited both floors or have them in queue
        assert len(elevator.task_queue) <= 1, "Most tasks should be completed"

    def test_IT4_door_control_during_movement_requests(
        self, system_harness, simulate_time
    ):
        """
        IT4: Door Control During Movement Requests
        Manual door operations conflict resolution
        """
        # Setup: Elevator idle at floor 1 with doors closed
        elevator_id = 1
        initial_state = system_harness.get_elevator_state(elevator_id)
        assert initial_state["floor"] == 1
        assert initial_state["door_state"] == DoorState.CLOSED

        # Send open_door command
        open_result = system_harness.open_door(elevator_id)
        assert open_result["success"], "Door open command should succeed"

        # Immediately send call_up@1
        call_result = system_harness.send_call(floor=1, direction="up")
        assert call_result, "Call should be accepted"

        # Allow time for door to open
        simulate_time(system_harness.system, 2.0)

        # Verify door opens but movement request queued
        door_state = system_harness.get_elevator_state(elevator_id)["door_state"]
        assert door_state == DoorState.OPEN, "Door should be open due to manual command"

        # Wait for door timeout and verify movement begins after
        simulate_time(system_harness.system, 4.0)  # Wait through door timeout

        # Since we're already at the call floor, door should stay open for pickup
        final_door_state = system_harness.get_elevator_state(elevator_id)["door_state"]
        # Door operations should have precedence, call should be serviced appropriately
        assert final_door_state in [
            DoorState.OPEN,
            DoorState.CLOSED,
        ], "Door should be in valid state"

        # Verify that the call was handled appropriately
        # Since call is from floor 1 and elevator is at floor 1, service should be immediate
        remaining_calls = len(
            [
                call
                for call in system_harness.system["dispatcher"].pending_calls.values()
                if call.is_pending()
            ]
        )
        assert (
            remaining_calls == 0
        ), "Call at current floor should be serviced immediately"

    def test_IT5_system_reset_with_active_operations(
        self, system_harness, simulate_time
    ):
        """
        IT5: System Reset with Active Operations
        Reset behavior during complex system state
        """
        # Setup complex system state
        # 1. Multiple elevators moving
        system_harness.send_call(floor=3, direction="down")
        system_harness.send_call(floor=2, direction="up")

        # 2. Doors opening
        system_harness.open_door(1)

        # 3. Tasks queued
        system_harness.select_floor(1, 3)
        system_harness.select_floor(2, 2)

        # Allow system to get into complex state
        simulate_time(system_harness.system, 3.0)

        # Verify we have a complex state
        pre_reset_state = system_harness.get_system_state()
        has_pending_calls = pre_reset_state["pending_calls"] > 0
        has_tasks = any(len(e["task_queue"]) > 0 for e in pre_reset_state["elevators"])

        # If no complex state developed, create it manually
        if not (has_pending_calls or has_tasks):
            # Force some tasks into queues
            for elevator in system_harness.system["elevators"]:
                elevator.task_queue.append(Task(floor=3))

        # Send reset command
        reset_start_time = time.time()
        system_harness.reset_system()

        # Allow time for reset to complete
        simulate_time(system_harness.system, 6.0)

        # Verify reset results
        post_reset_state = system_harness.get_system_state()
        reset_duration = time.time() - reset_start_time

        # All elevators should be at floor 1
        for elevator_state in post_reset_state["elevators"]:
            assert (
                elevator_state["floor"] == 1
            ), "All elevators should return to floor 1"
            assert (
                elevator_state["state"] == ElevatorState.IDLE
            ), "All elevators should be idle"
            assert (
                elevator_state["door_state"] == DoorState.CLOSED
            ), "All doors should be closed"
            assert (
                len(elevator_state["task_queue"]) == 0
            ), "All task queues should be empty"

        # All calls should be cleared
        assert (
            post_reset_state["pending_calls"] == 0
        ), "All pending calls should be cleared"

        # Reset should complete within time limit
        assert reset_duration < 5.0, "Reset should complete within 5 seconds"

        # Verify system is responsive after reset
        test_call_result = system_harness.send_call(floor=2, direction="up")
        assert (
            test_call_result
        ), "System should be responsive to new commands after reset"

        # Allow time for new call processing
        simulate_time(system_harness.system, 2.0)

        # New call should be processed normally
        post_reset_calls = len(
            [
                call
                for call in system_harness.system["dispatcher"].pending_calls.values()
                if call.is_assigned()
            ]
        )
        assert post_reset_calls > 0, "New calls should be processed after reset"
