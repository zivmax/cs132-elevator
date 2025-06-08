"""
Unit tests for models and validation functions.

Tests the data models including Call, Task, validation functions,
and model behavior as specified in validation documentation (TC93-TC111).
"""

import pytest
from backend.models import (
    Call,
    CallState,
    Task,
    ElevatorState,
    DoorState,
    MoveDirection,
    validate_floor,
    validate_elevator_id,
    validate_direction,
    MIN_FLOOR,
    MAX_FLOOR,
    MIN_ELEVATOR_ID,
    MAX_ELEVATOR_ID,
)


class TestCallModel:
    """Test cases for Call model (TC93-TC100)"""

    def test_call_assign_to_elevator(self):
        """TC93: Test Call.assign_to_elevator sets state and assigned_elevator"""
        call = Call(floor=2, direction=MoveDirection.UP, call_id="test_call")

        call.assign_to_elevator(1)

        assert call.state == CallState.ASSIGNED
        assert call.assigned_elevator == 1

    def test_call_complete(self):
        """TC94: Test Call.complete sets state to COMPLETED"""
        call = Call(floor=2, direction=MoveDirection.UP, call_id="test_call")

        call.complete()

        assert call.state == CallState.COMPLETED

    def test_call_is_pending_true(self):
        """TC95: Test Call.is_pending returns True when state is PENDING"""
        call = Call(floor=2, direction=MoveDirection.UP, call_id="test_call")
        call.state = CallState.PENDING

        assert call.is_pending() is True

    def test_call_is_pending_false(self):
        """TC96: Test Call.is_pending returns False when state is not PENDING"""
        call = Call(floor=2, direction=MoveDirection.UP, call_id="test_call")
        call.state = CallState.ASSIGNED

        assert call.is_pending() is False

        call.state = CallState.COMPLETED
        assert call.is_pending() is False

    def test_call_is_assigned_true(self):
        """TC97: Test Call.is_assigned returns True when state is ASSIGNED"""
        call = Call(floor=2, direction=MoveDirection.UP, call_id="test_call")
        call.state = CallState.ASSIGNED

        assert call.is_assigned() is True

    def test_call_is_assigned_false(self):
        """TC98: Test Call.is_assigned returns False when state is not ASSIGNED"""
        call = Call(floor=2, direction=MoveDirection.UP, call_id="test_call")
        call.state = CallState.PENDING

        assert call.is_assigned() is False

        call.state = CallState.COMPLETED
        assert call.is_assigned() is False

    def test_call_is_completed_true(self):
        """TC99: Test Call.is_completed returns True when state is COMPLETED"""
        call = Call(floor=2, direction=MoveDirection.UP, call_id="test_call")
        call.state = CallState.COMPLETED

        assert call.is_completed() is True

    def test_call_is_completed_false(self):
        """TC100: Test Call.is_completed returns False when state is not COMPLETED"""
        call = Call(floor=2, direction=MoveDirection.UP, call_id="test_call")
        call.state = CallState.PENDING

        assert call.is_completed() is False

        call.state = CallState.ASSIGNED
        assert call.is_completed() is False


class TestTaskModel:
    """Test cases for Task model (TC101-TC102)"""

    def test_task_is_outside_call_true(self):
        """TC101: Test Task.is_outside_call returns True when call_id is not None"""
        task = Task(floor=3, call_id="test_call_123")

        assert task.is_outside_call is True

    def test_task_is_outside_call_false(self):
        """TC102: Test Task.is_outside_call returns False when call_id is None"""
        task = Task(floor=3, call_id=None)

        assert task.is_outside_call is False


class TestFloorValidation:
    """Test cases for floor validation (TC103-TC105)"""

    def test_validate_floor_within_range(self):
        """TC103: Test validate_floor returns True for valid floors"""
        # Test minimum floor
        assert validate_floor(MIN_FLOOR) is True

        # Test maximum floor
        assert validate_floor(MAX_FLOOR) is True

        # Test floor between min and max
        if MIN_FLOOR < MAX_FLOOR:
            mid_floor = (MIN_FLOOR + MAX_FLOOR) // 2
            assert validate_floor(mid_floor) is True

    def test_validate_floor_below_minimum(self):
        """TC104: Test validate_floor returns False for floor below minimum"""
        assert validate_floor(MIN_FLOOR - 1) is False

    def test_validate_floor_above_maximum(self):
        """TC105: Test validate_floor returns False for floor above maximum"""
        assert validate_floor(MAX_FLOOR + 1) is False


class TestElevatorIdValidation:
    """Test cases for elevator ID validation (TC106-TC108)"""

    def test_validate_elevator_id_within_range(self):
        """TC106: Test validate_elevator_id returns True for valid IDs"""
        # Test minimum elevator ID
        assert validate_elevator_id(MIN_ELEVATOR_ID) is True

        # Test maximum elevator ID
        assert validate_elevator_id(MAX_ELEVATOR_ID) is True

    def test_validate_elevator_id_below_minimum(self):
        """TC107: Test validate_elevator_id returns False for ID below minimum"""
        assert validate_elevator_id(MIN_ELEVATOR_ID - 1) is False

    def test_validate_elevator_id_above_maximum(self):
        """TC108: Test validate_elevator_id returns False for ID above maximum"""
        assert validate_elevator_id(MAX_ELEVATOR_ID + 1) is False


class TestDirectionValidation:
    """Test cases for direction validation (TC109-TC111)"""

    def test_validate_direction_up(self):
        """TC109: Test validate_direction returns True for 'up'"""
        assert validate_direction("up") is True

    def test_validate_direction_down(self):
        """TC110: Test validate_direction returns True for 'down'"""
        assert validate_direction("down") is True

    def test_validate_direction_invalid(self):
        """TC111: Test validate_direction returns False for invalid directions"""
        assert validate_direction("invalid") is False
        assert validate_direction("") is False
        assert validate_direction("left") is False
        assert validate_direction("right") is False
        assert validate_direction("stop") is False


class TestModelEnums:
    """Test cases for model enums"""

    def test_elevator_state_enum_values(self):
        """Test ElevatorState enum has expected values"""
        assert ElevatorState.IDLE
        assert ElevatorState.MOVING_UP
        assert ElevatorState.MOVING_DOWN

    def test_door_state_enum_values(self):
        """Test DoorState enum has expected values"""
        assert DoorState.CLOSED
        assert DoorState.OPENING
        assert DoorState.OPEN
        assert DoorState.CLOSING

    def test_move_direction_enum_values(self):
        """Test MoveDirection enum has expected values"""
        assert MoveDirection.UP
        assert MoveDirection.DOWN

    def test_call_state_enum_values(self):
        """Test CallState enum has expected values"""
        assert CallState.PENDING
        assert CallState.ASSIGNED
        assert CallState.COMPLETED


class TestModelIntegration:
    """Integration tests for model interactions"""

    def test_call_lifecycle(self):
        """Test complete call lifecycle"""
        call = Call(floor=3, direction=MoveDirection.UP, call_id="lifecycle_test")

        # Initially pending
        assert call.is_pending()
        assert not call.is_assigned()
        assert not call.is_completed()

        # Assign to elevator
        call.assign_to_elevator(1)
        assert not call.is_pending()
        assert call.is_assigned()
        assert not call.is_completed()

        # Complete the call
        call.complete()
        assert not call.is_pending()
        assert not call.is_assigned()
        assert call.is_completed()

    def test_task_creation_outside_call(self):
        """Test task creation for outside call"""
        task = Task(floor=2, call_id="outside_call_123")

        assert task.floor == 2
        assert task.call_id == "outside_call_123"
        assert task.is_outside_call

    def test_task_creation_inside_call(self):
        """Test task creation for inside call"""
        task = Task(floor=3, call_id=None)

        assert task.floor == 3
        assert task.call_id is None
        assert not task.is_outside_call

    def test_validation_boundary_conditions(self):
        """Test validation functions at boundary conditions"""
        # Floor boundaries
        assert validate_floor(MIN_FLOOR) is True
        assert validate_floor(MAX_FLOOR) is True
        assert validate_floor(MIN_FLOOR - 1) is False
        assert validate_floor(MAX_FLOOR + 1) is False

        # Elevator ID boundaries
        assert validate_elevator_id(MIN_ELEVATOR_ID) is True
        assert validate_elevator_id(MAX_ELEVATOR_ID) is True
        assert validate_elevator_id(MIN_ELEVATOR_ID - 1) is False
        assert validate_elevator_id(MAX_ELEVATOR_ID + 1) is False

        # Direction validation
        assert validate_direction("up") is True
        assert validate_direction("down") is True
        assert validate_direction("UP") is False  # Case sensitive
        assert validate_direction("DOWN") is False  # Case sensitive


if __name__ == "__main__":
    pytest.main([__file__])
