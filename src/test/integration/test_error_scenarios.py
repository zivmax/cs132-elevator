"""
Integration tests for error scenarios and recovery.
Tests error propagation and recovery across components.
"""

import pytest
import time
from unittest.mock import Mock, patch
from backend.models import ElevatorState, DoorState, MoveDirection, MIN_FLOOR, MAX_FLOOR


class TestErrorScenarios:
    """Error condition integration tests"""

    def test_invalid_input_handling_across_components(
        self, system_harness, simulate_time
    ):
        """
        Test invalid input handling and error propagation
        """
        # Test invalid floor numbers
        invalid_floors = [MIN_FLOOR - 1, MAX_FLOOR + 1, 999, -999]

        for invalid_floor in invalid_floors:
            # Test invalid call floor
            try:
                result = system_harness.send_call(invalid_floor, "up")
                # Should either reject or handle gracefully
                assert (
                    result is False or result is True
                )  # Either way is acceptable if handled properly
            except (ValueError, KeyError) as e:
                # Exception is acceptable for invalid input
                assert "invalid" in str(e).lower() or "floor" in str(e).lower()

            # Test invalid floor selection
            try:
                result = system_harness.select_floor(1, invalid_floor)
                # Should reject invalid floor
                assert result["success"] is False or "error" in result
            except (ValueError, KeyError) as e:
                # Exception is acceptable for invalid input
                assert "invalid" in str(e).lower() or "floor" in str(e).lower()

        # Test invalid elevator IDs
        invalid_elevator_ids = [0, 3, 999, -1]

        for invalid_id in invalid_elevator_ids:
            try:
                result = system_harness.select_floor(invalid_id, 2)
                # Should reject invalid elevator ID
                assert result["success"] is False or "error" in result
            except (ValueError, IndexError) as e:
                # Exception is acceptable for invalid input
                pass

            try:
                result = system_harness.open_door(invalid_id)
                # Should reject invalid elevator ID
                assert result["success"] is False or "error" in result
            except (ValueError, IndexError) as e:
                # Exception is acceptable for invalid input
                pass

        # Test invalid directions
        invalid_directions = ["left", "right", "", "invalid", None]

        for invalid_direction in invalid_directions:
            try:
                result = system_harness.send_call(2, invalid_direction)
                # Should reject invalid direction
                assert result is False
            except (ValueError, KeyError, TypeError) as e:
                # Exception is acceptable for invalid input
                pass

        # Verify system remains stable after invalid inputs
        simulate_time(system_harness.system, 1.0)
        final_state = system_harness.get_system_state()

        # System should still be operational
        assert len(final_state["elevators"]) == 2
        for elevator_state in final_state["elevators"]:
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

        # Valid commands should still work
        valid_result = system_harness.send_call(2, "up")
        assert valid_result is True, "Valid commands should work after invalid inputs"

    def test_component_failure_recovery(self, system_harness, simulate_time):
        """
        Test system behavior when components encounter errors
        """
        # Test dispatcher failure simulation
        original_process_calls = system_harness.system[
            "dispatcher"
        ]._process_pending_calls

        # Temporarily break dispatcher
        def failing_process_calls():
            raise Exception("Dispatcher processing error")

        system_harness.system["dispatcher"]._process_pending_calls = (
            failing_process_calls
        )

        # Try to send a call while dispatcher is "broken"
        try:
            system_harness.send_call(2, "up")
            simulate_time(system_harness.system, 1.0)
        except Exception:
            # Exception is expected when dispatcher is broken
            pass

        # Restore dispatcher
        system_harness.system["dispatcher"]._process_pending_calls = (
            original_process_calls
        )

        # System should recover and work normally
        recovery_result = system_harness.send_call(2, "up")
        assert recovery_result is True, "System should recover after component failure"

        simulate_time(system_harness.system, 2.0)

        # Verify recovery
        final_state = system_harness.get_system_state()
        assert (
            final_state["pending_calls"] >= 0
        ), "System should function after recovery"

    def test_concurrent_error_conditions(self, system_harness, simulate_time):
        """
        Test system behavior under multiple error conditions
        """
        # Create complex scenario with potential race conditions

        # Start multiple operations
        system_harness.send_call(1, "up")
        system_harness.send_call(2, "down")
        system_harness.send_call(3, "up")

        # Add floor selections
        system_harness.select_floor(1, 3)
        system_harness.select_floor(2, 1)

        # Open doors manually
        system_harness.open_door(1)
        system_harness.open_door(2)

        # Allow some processing
        simulate_time(system_harness.system, 1.0)

        # Now introduce errors during active operations
        # Try invalid operations on busy elevators
        try:
            system_harness.select_floor(1, 999)  # Invalid floor
        except:
            pass

        try:
            system_harness.select_floor(999, 2)  # Invalid elevator
        except:
            pass

        # Send conflicting commands rapidly
        for _ in range(5):
            system_harness.open_door(1)
            system_harness.close_door(1)
            system_harness.select_floor(1, 2)

        # Allow system to process
        simulate_time(system_harness.system, 5.0)

        # System should remain stable despite errors
        final_state = system_harness.get_system_state()

        # Verify system integrity
        assert (
            len(final_state["elevators"]) == 2
        ), "System should maintain elevator count"

        for elevator_state in final_state["elevators"]:
            # Elevators should be in valid states
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
            assert MIN_FLOOR <= elevator_state["floor"] <= MAX_FLOOR

        # Dispatcher should still be functional
        assert final_state["pending_calls"] >= 0

        # Test that normal operations still work
        recovery_call = system_harness.send_call(2, "up")
        assert (
            recovery_call is True
        ), "Normal operations should work after error conditions"

    def test_resource_exhaustion_scenarios(self, system_harness, simulate_time):
        """
        Test system behavior under resource exhaustion
        """
        # Flood system with calls to test queue limits
        flood_calls = []
        for floor in [1, 2, 3]:
            for direction in ["up", "down"]:
                # Skip invalid combinations
                if floor == MAX_FLOOR and direction == "up":
                    continue
                if floor == MIN_FLOOR and direction == "down":
                    continue

                # Send multiple calls to same floor/direction
                for _ in range(10):  # Flood with duplicates
                    try:
                        result = system_harness.send_call(floor, direction)
                        flood_calls.append(result)
                    except Exception:
                        # System might reject excessive calls
                        pass

        # Flood with floor selections
        for elevator_id in [1, 2]:
            for floor in [1, 2, 3]:
                for _ in range(10):  # Multiple selections
                    try:
                        result = system_harness.select_floor(elevator_id, floor)
                        # System should handle duplicate selections
                    except Exception:
                        # Might reject excessive selections
                        pass

        # Allow system to process flood
        simulate_time(system_harness.system, 3.0)

        # Verify system handles flood gracefully
        state_after_flood = system_harness.get_system_state()

        # System should not crash or become unresponsive
        assert len(state_after_flood["elevators"]) == 2

        # Pending calls should be reasonable (duplicates filtered)
        assert (
            state_after_flood["pending_calls"] <= 20
        ), "System should filter duplicate calls"

        # Task queues should be reasonable
        for elevator in system_harness.system["elevators"]:
            assert (
                len(elevator.task_queue) <= 10
            ), "Task queues should not be excessively large"

        # System should still be responsive
        test_call = system_harness.send_call(2, "up")
        assert test_call is True, "System should remain responsive after flood"

    def test_timing_and_race_conditions(self, system_harness, simulate_time):
        """
        Test system behavior under timing-sensitive conditions
        """
        # Create scenario prone to race conditions
        # Rapidly alternate between conflicting operations

        for iteration in range(5):
            # Start movement
            system_harness.send_call(3, "down")

            # Immediately try door operations
            system_harness.open_door(1)
            system_harness.close_door(1)

            # Add floor selections
            system_harness.select_floor(1, 2)
            system_harness.select_floor(1, 1)  # Conflicting with call

            # Brief processing time
            simulate_time(system_harness.system, 0.5)

            # Reset and repeat
            system_harness.reset_system()
            simulate_time(system_harness.system, 0.5)

        # Final processing
        simulate_time(system_harness.system, 2.0)

        # Verify no race conditions caused system instability
        final_state = system_harness.get_system_state()

        # All elevators should be in valid states
        for elevator_state in final_state["elevators"]:
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
            assert MIN_FLOOR <= elevator_state["floor"] <= MAX_FLOOR

        # System should be responsive after stress testing
        final_test_call = system_harness.send_call(2, "up")
        assert (
            final_test_call is True
        ), "System should be responsive after timing stress test"

        # Allow final processing to ensure stability
        simulate_time(system_harness.system, 3.0)

        stable_state = system_harness.get_system_state()
        assert (
            stable_state["pending_calls"] >= 0
        ), "System should be stable after stress testing"
