"""
Unit tests for Elevator class functionality

Tests the core elevator operations including state management,
door operations, movement logic, and task queue handling.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from backend.elevator import Elevator
from backend.models import (
    ElevatorState,
    DoorState,
    MoveDirection,
    Task,
)


class TestElevatorInitialization:
    """Test cases for elevator initialization and basic properties"""

    def test_elevator_initialization(self):
        """Test that elevator initializes with correct default values"""
        mock_world = Mock()
        mock_api = Mock()

        elevator = Elevator(1, mock_world, mock_api)

        assert elevator.id == 1
        assert elevator.current_floor == 1
        assert elevator.previous_floor == 1
        assert elevator.state == ElevatorState.IDLE
        assert elevator.door_state == DoorState.CLOSED
        assert elevator.direction is None
        assert elevator.task_queue == []
        assert elevator.door_timeout == 3.0
        assert elevator.floor_travel_time == 2.0
        assert elevator.door_operation_time == 1.0

    def test_elevator_different_ids(self):
        """Test elevators can be created with different IDs"""
        mock_world = Mock()
        mock_api = Mock()

        elevator1 = Elevator(1, mock_world, mock_api)
        elevator2 = Elevator(2, mock_world, mock_api)

        assert elevator1.id == 1
        assert elevator2.id == 2


class TestElevatorMovementState:
    """Test cases for elevator movement state management"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.elevator = Elevator(1, self.mock_world, self.mock_api)

    def test_is_moving_when_idle(self):
        """Test is_moving returns False when elevator is idle"""
        self.elevator.state = ElevatorState.IDLE
        assert not self.elevator.is_moving()

    def test_is_moving_when_moving_up(self):
        """Test is_moving returns True when elevator is moving up"""
        self.elevator.state = ElevatorState.MOVING_UP
        assert self.elevator.is_moving()

    def test_is_moving_when_moving_down(self):
        """Test is_moving returns True when elevator is moving down"""
        self.elevator.state = ElevatorState.MOVING_DOWN
        assert self.elevator.is_moving()

    def test_get_movement_direction_when_idle(self):
        """Test get_movement_direction returns 0 when idle"""
        self.elevator.state = ElevatorState.IDLE
        assert self.elevator.get_movement_direction() == 0

    def test_get_movement_direction_when_moving_up(self):
        """Test get_movement_direction returns 1 when moving up"""
        self.elevator.state = ElevatorState.MOVING_UP
        assert self.elevator.get_movement_direction() == 1

    def test_get_movement_direction_when_moving_down(self):
        """Test get_movement_direction returns -1 when moving down"""
        self.elevator.state = ElevatorState.MOVING_DOWN
        assert self.elevator.get_movement_direction() == -1

    def test_set_moving_state_up(self):
        """Test setting moving state to up"""
        with patch("time.time", return_value=100.0):
            self.elevator.set_moving_state(MoveDirection.UP.value)

        assert self.elevator.state == ElevatorState.MOVING_UP
        assert self.elevator.moving_since == 100.0
        assert self.elevator.last_state_change == 100.0

    def test_set_moving_state_down(self):
        """Test setting moving state to down"""
        with patch("time.time", return_value=200.0):
            self.elevator.set_moving_state(MoveDirection.DOWN.value)

        assert self.elevator.state == ElevatorState.MOVING_DOWN
        assert self.elevator.moving_since == 200.0
        assert self.elevator.last_state_change == 200.0

    def test_set_moving_state_invalid(self):
        """Test setting invalid moving state results in idle"""
        self.elevator.set_moving_state("invalid")
        assert self.elevator.state == ElevatorState.IDLE


class TestElevatorDoorOperations:
    """Test cases for elevator door operations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.elevator = Elevator(1, self.mock_world, self.mock_api)

    def test_open_door_when_closed(self):
        """Test opening door when it's closed"""
        self.elevator.door_state = DoorState.CLOSED
        self.elevator.state = ElevatorState.IDLE

        with patch("time.time", return_value=100.0):
            self.elevator.open_door()

        assert self.elevator.door_state == DoorState.OPENING
        assert self.elevator.last_door_change == 100.0

    def test_open_door_when_already_open(self):
        """Test opening door when it's already open (should not change)"""
        self.elevator.door_state = DoorState.OPEN
        original_time = self.elevator.last_door_change

        self.elevator.open_door()

        assert self.elevator.door_state == DoorState.OPEN
        assert self.elevator.last_door_change == original_time

    def test_open_door_when_moving(self):
        """Test opening door when elevator is moving (should not open)"""
        self.elevator.door_state = DoorState.CLOSED
        self.elevator.state = ElevatorState.MOVING_UP
        original_time = self.elevator.last_door_change

        self.elevator.open_door()

        assert self.elevator.door_state == DoorState.CLOSED
        assert self.elevator.last_door_change == original_time

    def test_close_door_when_open(self):
        """Test closing door when it's open"""
        self.elevator.door_state = DoorState.OPEN
        self.elevator.state = ElevatorState.IDLE

        with patch("time.time", return_value=150.0):
            self.elevator.close_door()

        assert self.elevator.door_state == DoorState.CLOSING
        assert self.elevator.last_door_change == 150.0

    def test_close_door_when_already_closed(self):
        """Test closing door when it's already closed (should not change)"""
        self.elevator.door_state = DoorState.CLOSED
        original_time = self.elevator.last_door_change

        self.elevator.close_door()

        assert self.elevator.door_state == DoorState.CLOSED
        assert self.elevator.last_door_change == original_time

    def test_close_door_when_moving(self):
        """Test closing door when elevator is moving (should not close)"""
        self.elevator.door_state = DoorState.OPEN
        self.elevator.state = ElevatorState.MOVING_DOWN
        original_time = self.elevator.last_door_change

        self.elevator.close_door()

        assert self.elevator.door_state == DoorState.OPEN
        assert self.elevator.last_door_change == original_time


class TestElevatorFloorManagement:
    """Test cases for elevator floor management"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.elevator = Elevator(1, self.mock_world, self.mock_api)

    def test_set_floor_updates_current_and_previous(self):
        """Test that set_floor correctly updates current and previous floors"""
        self.elevator.current_floor = 1

        with patch("time.time", return_value=100.0):
            self.elevator.set_floor(3)

        assert self.elevator.current_floor == 3
        assert self.elevator.previous_floor == 1
        assert self.elevator.floor_changed is True
        assert self.elevator.moving_since == 100.0

    def test_set_floor_same_floor_no_change(self):
        """Test that setting same floor doesn't change previous floor"""
        self.elevator.current_floor = 2
        self.elevator.previous_floor = 1
        original_moving_since = self.elevator.moving_since

        self.elevator.set_floor(2)

        assert self.elevator.current_floor == 2
        assert self.elevator.previous_floor == 1
        assert self.elevator.floor_changed is False
        assert self.elevator.moving_since == original_moving_since


class TestElevatorDirectionDetermination:
    """Test cases for elevator direction determination logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.elevator = Elevator(1, self.mock_world, self.mock_api)

    def test_determine_direction_no_tasks(self):
        """Test direction determination with no tasks"""
        self.elevator.task_queue = []
        self.elevator._determine_direction()
        assert self.elevator.direction is None

    def test_determine_direction_all_above(self):
        """Test direction determination when all tasks are above current floor"""
        self.elevator.current_floor = 1
        self.elevator.task_queue = [
            Task(floor=2, origin="outside"),
            Task(floor=3, origin="inside"),
        ]

        self.elevator._determine_direction()
        assert self.elevator.direction == MoveDirection.UP

    def test_determine_direction_all_below(self):
        """Test direction determination when all tasks are below current floor"""
        self.elevator.current_floor = 3
        self.elevator.task_queue = [
            Task(floor=1, origin="outside"),
            Task(floor=0, origin="inside"),
        ]

        self.elevator._determine_direction()
        assert self.elevator.direction == MoveDirection.DOWN

    def test_determine_direction_mixed_closest_above(self):
        """Test direction determination chooses closest when mixed floors"""
        self.elevator.current_floor = 2
        self.elevator.task_queue = [
            Task(floor=3, origin="outside"),  # 1 floor above
            Task(floor=0, origin="inside"),  # 2 floors below
        ]

        self.elevator._determine_direction()
        assert self.elevator.direction == MoveDirection.UP

    def test_determine_direction_mixed_closest_below(self):
        """Test direction determination chooses closest when mixed floors"""
        self.elevator.current_floor = 2
        self.elevator.task_queue = [
            Task(floor=3, origin="outside", direction="up"),  # 1 floor above
            Task(floor=1, origin="inside"),  # 1 floor below
        ]

        self.elevator._determine_direction()
        # Should choose UP as it's first in tie-breaking
        assert self.elevator.direction == MoveDirection.UP

    def test_determine_direction_continue_up_when_more_above(self):
        """Test continuing up when current direction is up and more floors above"""
        self.elevator.current_floor = 2
        self.elevator.direction = MoveDirection.UP
        self.elevator.task_queue = [
            Task(floor=3, origin="outside"),
            Task(floor=1, origin="inside"),
        ]

        self.elevator._determine_direction()
        assert self.elevator.direction == MoveDirection.UP

    def test_determine_direction_continue_down_when_more_below(self):
        """Test continuing down when current direction is down and more floors below"""
        self.elevator.current_floor = 2
        self.elevator.direction = MoveDirection.DOWN
        self.elevator.task_queue = [
            Task(floor=1, origin="outside"),
            Task(floor=3, origin="inside"),
        ]

        self.elevator._determine_direction()
        assert self.elevator.direction == MoveDirection.DOWN


class TestElevatorMovementRequests:
    """Test cases for elevator movement request handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.mock_engine = Mock()
        self.mock_world.engine = self.mock_engine
        self.elevator = Elevator(1, self.mock_world, self.mock_api)

    def test_request_movement_with_tasks(self):
        """Test requesting movement when there are tasks in queue"""
        self.elevator.current_floor = 1
        self.elevator.task_queue = [Task(floor=3, origin="outside")]
        self.elevator.door_state = DoorState.CLOSED

        self.elevator.request_movement_if_needed()

        # Should determine direction and send move request
        assert self.elevator.direction == MoveDirection.UP
        self.mock_engine.request_movement.assert_called_once()

        # Verify the move request contains correct data
        call_args = self.mock_engine.request_movement.call_args[0][0]
        assert call_args.elevator_id == 1
        assert call_args.direction == MoveDirection.UP

    def test_request_movement_no_tasks(self):
        """Test requesting movement when there are no tasks"""
        self.elevator.task_queue = []

        self.elevator.request_movement_if_needed()

        assert self.elevator.state == ElevatorState.IDLE
        self.mock_engine.request_movement.assert_not_called()

    def test_request_movement_doors_open(self):
        """Test that movement is not requested when doors are open"""
        self.elevator.current_floor = 1
        self.elevator.task_queue = [Task(floor=3, origin="outside")]
        self.elevator.door_state = DoorState.OPEN

        self.elevator.request_movement_if_needed()

        # Should not send move request when doors are open
        self.mock_engine.request_movement.assert_not_called()


class TestElevatorEstimatedTime:
    """Test cases for elevator estimated time calculation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.elevator = Elevator(1, self.mock_world, self.mock_api)

    def test_estimated_time_same_floor_door_open(self):
        """Test estimated time when already at target floor with door open"""
        self.elevator.current_floor = 2
        self.elevator.door_state = DoorState.OPEN

        estimated_time = self.elevator.calculate_estimated_time(2, MoveDirection.UP)
        assert estimated_time == 0.0

    def test_estimated_time_same_floor_door_opening(self):
        """Test estimated time when already at target floor with door opening"""
        self.elevator.current_floor = 2
        self.elevator.door_state = DoorState.OPENING

        estimated_time = self.elevator.calculate_estimated_time(2, MoveDirection.UP)
        assert estimated_time == 0.0

    def test_estimated_time_direct_travel_idle(self):
        """Test estimated time for direct travel when idle"""
        self.elevator.current_floor = 1
        self.elevator.state = ElevatorState.IDLE
        self.elevator.door_state = DoorState.CLOSED
        self.elevator.floor_travel_time = 2.0

        estimated_time = self.elevator.calculate_estimated_time(3, MoveDirection.UP)
        expected_time = abs(3 - 1) * 2.0  # 2 floors * 2 seconds = 4 seconds
        assert estimated_time == expected_time

    def test_estimated_time_with_door_closing(self):
        """Test estimated time includes door closing time when door is open"""
        self.elevator.current_floor = 1
        self.elevator.state = ElevatorState.IDLE
        self.elevator.door_state = DoorState.OPEN
        self.elevator.floor_travel_time = 2.0

        estimated_time = self.elevator.calculate_estimated_time(2, MoveDirection.UP)
        expected_time = (
            1.0 + abs(2 - 1) * 2.0
        )  # 1 sec door close + 1 floor * 2 sec = 3 seconds
        assert estimated_time == expected_time


if __name__ == "__main__":
    # Allow running the test file directly
    pytest.main([__file__])
