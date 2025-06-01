"""
Unit tests for Task and Model data structures

Tests the data models including Task creation, validation,
enums, and data structure behavior.
"""

import pytest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from backend.models import (
    ElevatorState,
    DoorState,
    MoveDirection,
    MoveRequest,
    Task,
    MIN_FLOOR,
    MAX_FLOOR,
    MIN_ELEVATOR_ID,
    MAX_ELEVATOR_ID,
)


class TestElevatorStateEnum:
    """Test cases for ElevatorState enum"""

    def test_elevator_state_values(self):
        """Test that ElevatorState enum has expected values"""
        assert ElevatorState.IDLE
        assert ElevatorState.MOVING_UP
        assert ElevatorState.MOVING_DOWN

    def test_elevator_state_comparison(self):
        """Test ElevatorState enum comparison"""
        assert ElevatorState.IDLE == ElevatorState.IDLE
        assert ElevatorState.IDLE != ElevatorState.MOVING_UP
        assert ElevatorState.MOVING_UP != ElevatorState.MOVING_DOWN

    def test_elevator_state_in_collection(self):
        """Test ElevatorState enum can be used in collections"""
        moving_states = [ElevatorState.MOVING_UP, ElevatorState.MOVING_DOWN]
        
        assert ElevatorState.MOVING_UP in moving_states
        assert ElevatorState.MOVING_DOWN in moving_states
        assert ElevatorState.IDLE not in moving_states

    def test_elevator_state_string_representation(self):
        """Test ElevatorState string representation"""
        idle_str = str(ElevatorState.IDLE)
        up_str = str(ElevatorState.MOVING_UP)
        down_str = str(ElevatorState.MOVING_DOWN)
        
        assert "IDLE" in idle_str
        assert "MOVING_UP" in up_str
        assert "MOVING_DOWN" in down_str


class TestDoorStateEnum:
    """Test cases for DoorState enum"""

    def test_door_state_values(self):
        """Test that DoorState enum has expected values"""
        assert DoorState.OPEN
        assert DoorState.CLOSED
        assert DoorState.OPENING
        assert DoorState.CLOSING

    def test_door_state_comparison(self):
        """Test DoorState enum comparison"""
        assert DoorState.OPEN == DoorState.OPEN
        assert DoorState.OPEN != DoorState.CLOSED
        assert DoorState.OPENING != DoorState.CLOSING

    def test_door_state_transitions(self):
        """Test logical door state transitions"""
        # Test that all door states are distinct
        states = [DoorState.OPEN, DoorState.CLOSED, DoorState.OPENING, DoorState.CLOSING]
        assert len(set(states)) == 4

    def test_door_state_in_collection(self):
        """Test DoorState enum can be used in collections"""
        transitional_states = [DoorState.OPENING, DoorState.CLOSING]
        stable_states = [DoorState.OPEN, DoorState.CLOSED]
        
        assert DoorState.OPENING in transitional_states
        assert DoorState.CLOSING in transitional_states
        assert DoorState.OPEN in stable_states
        assert DoorState.CLOSED in stable_states
        
        assert DoorState.OPEN not in transitional_states
        assert DoorState.OPENING not in stable_states


class TestMoveDirectionEnum:
    """Test cases for MoveDirection enum"""

    def test_move_direction_values(self):
        """Test that MoveDirection enum has expected values"""
        assert MoveDirection.UP
        assert MoveDirection.DOWN

    def test_move_direction_string_values(self):
        """Test MoveDirection enum string values"""
        assert MoveDirection.UP.value == "up"
        assert MoveDirection.DOWN.value == "down"

    def test_move_direction_comparison(self):
        """Test MoveDirection enum comparison"""
        assert MoveDirection.UP == MoveDirection.UP
        assert MoveDirection.UP != MoveDirection.DOWN

    def test_move_direction_from_string(self):
        """Test creating MoveDirection from string values"""
        up_from_string = MoveDirection("up")
        down_from_string = MoveDirection("down")
        
        assert up_from_string == MoveDirection.UP
        assert down_from_string == MoveDirection.DOWN

    def test_move_direction_invalid_string(self):
        """Test creating MoveDirection from invalid string raises error"""
        with pytest.raises(ValueError):
            MoveDirection("invalid")
        
        with pytest.raises(ValueError):
            MoveDirection("left")


class TestMoveRequest:
    """Test cases for MoveRequest class"""

    def test_move_request_creation_up(self):
        """Test creating MoveRequest for upward movement"""
        request = MoveRequest(1, MoveDirection.UP)
        
        assert request.elevator_id == 1
        assert request.direction == MoveDirection.UP

    def test_move_request_creation_down(self):
        """Test creating MoveRequest for downward movement"""
        request = MoveRequest(2, MoveDirection.DOWN)
        
        assert request.elevator_id == 2
        assert request.direction == MoveDirection.DOWN

    def test_move_request_different_elevators(self):
        """Test creating MoveRequest for different elevators"""
        request1 = MoveRequest(1, MoveDirection.UP)
        request2 = MoveRequest(2, MoveDirection.UP)
        
        assert request1.elevator_id != request2.elevator_id
        assert request1.direction == request2.direction

    def test_move_request_attribute_access(self):
        """Test accessing MoveRequest attributes"""
        request = MoveRequest(1, MoveDirection.DOWN)
        
        # Should be able to access attributes
        elevator_id = request.elevator_id
        direction = request.direction
        
        assert elevator_id == 1
        assert direction == MoveDirection.DOWN

    def test_move_request_attribute_modification(self):
        """Test modifying MoveRequest attributes"""
        request = MoveRequest(1, MoveDirection.UP)
        
        # Should be able to modify attributes
        request.elevator_id = 2
        request.direction = MoveDirection.DOWN
        
        assert request.elevator_id == 2
        assert request.direction == MoveDirection.DOWN


class TestTask:
    """Test cases for Task NamedTuple"""

    def test_task_creation_outside_call(self):
        """Test creating Task for outside call"""
        task = Task(floor=2, origin="outside", direction="up")
        
        assert task.floor == 2
        assert task.origin == "outside"
        assert task.direction == "up"

    def test_task_creation_inside_call(self):
        """Test creating Task for inside call"""
        task = Task(floor=3, origin="inside")
        
        assert task.floor == 3
        assert task.origin == "inside"
        assert task.direction is None  # Default value

    def test_task_creation_with_all_parameters(self):
        """Test creating Task with all parameters specified"""
        task = Task(floor=1, origin="outside", direction="down")
        
        assert task.floor == 1
        assert task.origin == "outside"
        assert task.direction == "down"

    def test_task_creation_basement_floor(self):
        """Test creating Task for basement floor"""
        task = Task(floor=-1, origin="inside")
        
        assert task.floor == -1
        assert task.origin == "inside"

    def test_task_immutability(self):
        """Test that Task is immutable (NamedTuple behavior)"""
        task = Task(floor=2, origin="outside", direction="up")
        
        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            task.floor = 3
        
        with pytest.raises(AttributeError):
            task.origin = "inside"

    def test_task_equality(self):
        """Test Task equality comparison"""
        task1 = Task(floor=2, origin="outside", direction="up")
        task2 = Task(floor=2, origin="outside", direction="up")
        task3 = Task(floor=3, origin="outside", direction="up")
        
        assert task1 == task2
        assert task1 != task3

    def test_task_as_tuple(self):
        """Test Task can be used as tuple"""
        task = Task(floor=2, origin="outside", direction="up")
        
        # Should be able to unpack like a tuple
        floor, origin, direction = task
        
        assert floor == 2
        assert origin == "outside"
        assert direction == "up"

    def test_task_indexing(self):
        """Test Task supports indexing like tuple"""
        task = Task(floor=2, origin="outside", direction="up")
        
        assert task[0] == 2
        assert task[1] == "outside"
        assert task[2] == "up"

    def test_task_different_origins(self):
        """Test Tasks with different origins"""
        outside_task = Task(floor=2, origin="outside", direction="up")
        inside_task = Task(floor=2, origin="inside")
        
        assert outside_task.origin == "outside"
        assert inside_task.origin == "inside"
        assert outside_task != inside_task

    def test_task_different_directions(self):
        """Test Tasks with different directions"""
        up_task = Task(floor=2, origin="outside", direction="up")
        down_task = Task(floor=2, origin="outside", direction="down")
        no_direction_task = Task(floor=2, origin="outside")
        
        assert up_task.direction == "up"
        assert down_task.direction == "down"
        assert no_direction_task.direction is None
        
        assert up_task != down_task
        assert up_task != no_direction_task


class TestSystemConstants:
    """Test cases for system constants"""

    def test_floor_constants(self):
        """Test floor boundary constants"""
        assert MIN_FLOOR == -1
        assert MAX_FLOOR == 3
        assert MIN_FLOOR < MAX_FLOOR

    def test_elevator_id_constants(self):
        """Test elevator ID boundary constants"""
        assert MIN_ELEVATOR_ID == 1
        assert MAX_ELEVATOR_ID == 2
        assert MIN_ELEVATOR_ID <= MAX_ELEVATOR_ID

    def test_constants_are_integers(self):
        """Test that all constants are integers"""
        assert isinstance(MIN_FLOOR, int)
        assert isinstance(MAX_FLOOR, int)
        assert isinstance(MIN_ELEVATOR_ID, int)
        assert isinstance(MAX_ELEVATOR_ID, int)

    def test_floor_range_calculation(self):
        """Test floor range calculations"""
        floor_range = MAX_FLOOR - MIN_FLOOR + 1
        assert floor_range == 5  # -1, 0, 1, 2, 3

    def test_elevator_count_calculation(self):
        """Test elevator count calculations"""
        elevator_count = MAX_ELEVATOR_ID - MIN_ELEVATOR_ID + 1
        assert elevator_count == 2  # 1, 2

    def test_constants_consistency(self):
        """Test that constants are consistent with system design"""
        # Floor range should be reasonable
        assert MAX_FLOOR - MIN_FLOOR >= 0
        assert MAX_FLOOR - MIN_FLOOR <= 10  # Sanity check
        
        # Elevator count should be reasonable
        assert MAX_ELEVATOR_ID - MIN_ELEVATOR_ID >= 0
        assert MAX_ELEVATOR_ID - MIN_ELEVATOR_ID <= 5  # Sanity check


class TestModelIntegration:
    """Integration test cases for model interactions"""

    def test_task_with_enums(self):
        """Test Task creation with enum values where applicable"""
        # Create task for different directions
        up_task = Task(floor=2, origin="outside", direction=MoveDirection.UP.value)
        down_task = Task(floor=1, origin="outside", direction=MoveDirection.DOWN.value)
        
        assert up_task.direction == "up"
        assert down_task.direction == "down"

    def test_move_request_with_boundary_values(self):
        """Test MoveRequest with boundary elevator IDs"""
        request_min = MoveRequest(MIN_ELEVATOR_ID, MoveDirection.UP)
        request_max = MoveRequest(MAX_ELEVATOR_ID, MoveDirection.DOWN)
        
        assert request_min.elevator_id == MIN_ELEVATOR_ID
        assert request_max.elevator_id == MAX_ELEVATOR_ID

    def test_task_with_boundary_floors(self):
        """Test Task creation with boundary floor values"""
        min_floor_task = Task(floor=MIN_FLOOR, origin="outside", direction="up")
        max_floor_task = Task(floor=MAX_FLOOR, origin="outside", direction="down")
        
        assert min_floor_task.floor == MIN_FLOOR
        assert max_floor_task.floor == MAX_FLOOR

    def test_realistic_task_scenarios(self):
        """Test realistic task scenarios"""
        # Basement call going up
        basement_call = Task(floor=-1, origin="outside", direction="up")
        
        # Top floor call going down
        top_call = Task(floor=3, origin="outside", direction="down")
        
        # Inside floor selection
        inside_selection = Task(floor=2, origin="inside")
        
        assert basement_call.floor == -1 and basement_call.direction == "up"
        assert top_call.floor == 3 and top_call.direction == "down"
        assert inside_selection.origin == "inside" and inside_selection.direction is None

    def test_model_combinations(self):
        """Test various combinations of model elements"""
        # Test all elevator states with move directions
        for state in ElevatorState:
            assert state in [ElevatorState.IDLE, ElevatorState.MOVING_UP, ElevatorState.MOVING_DOWN]
        
        # Test all door states
        for door_state in DoorState:
            assert door_state in [DoorState.OPEN, DoorState.CLOSED, DoorState.OPENING, DoorState.CLOSING]
        
        # Test move directions
        for direction in MoveDirection:
            assert direction in [MoveDirection.UP, MoveDirection.DOWN]


if __name__ == "__main__":
    # Allow running the test file directly
    pytest.main([__file__])
