"""
Unit tests for Elevator class movement and state changes.
Previously, some of these tests might have been in a test_engine_movement.py
if the Engine class was responsible for detailed movement physics.
Now, Elevator handles its own movement.
"""

import pytest
import time
from unittest.mock import Mock, patch

from backend.elevator import Elevator
from backend.models import (
    ElevatorState,
    DoorState,
    MoveDirection,
    Task,
    # MoveRequest, # MoveRequest might not be directly used by Elevator tests now
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
        # self.mock_engine = Mock() # Engine is not directly interacted with by Elevator for movement
        # self.mock_world.engine = self.mock_engine
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
        with patch("time.time", return_value=300.0):
            self.elevator.set_moving_state("invalid_direction_value")
        assert self.elevator.state == ElevatorState.IDLE
        assert self.elevator.moving_since is None  # Should be None if set to IDLE
        assert self.elevator.last_state_change == 300.0


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
            Task(floor=2, call_id="call_1"),  # Outside call
            Task(floor=3),  # Inside call
        ]

        self.elevator._determine_direction()
        assert self.elevator.direction == MoveDirection.UP

    def test_determine_direction_all_below(self):
        """Test direction determination when all tasks are below current floor"""
        self.elevator.current_floor = 3
        self.elevator.task_queue = [
            Task(floor=1, call_id="call_1"),
            Task(floor=0),
        ]

        self.elevator._determine_direction()
        assert self.elevator.direction == MoveDirection.DOWN

    def test_determine_direction_mixed_closest_above(self):
        """Test direction determination chooses closest when mixed floors"""
        self.elevator.current_floor = 2
        self.elevator.task_queue = [
            Task(floor=3, call_id="call_1"),  # 1 floor above
            Task(floor=0),  # 2 floors below
        ]

        self.elevator._determine_direction()
        assert self.elevator.direction == MoveDirection.UP

    def test_determine_direction_mixed_closest_below(self):
        """Test direction determination chooses closest when mixed floors"""
        self.elevator.current_floor = 2
        self.elevator.task_queue = [
            Task(floor=3, call_id="call_3"),  # 1 floor above
            Task(floor=1),  # 1 floor below
        ]

        self.elevator._determine_direction()
        # Should choose UP as it's first in tie-breaking
        assert self.elevator.direction == MoveDirection.UP

    def test_determine_direction_continue_up_when_more_above(self):
        """Test continuing up when current direction is up and more floors above"""
        self.elevator.current_floor = 2
        self.elevator.direction = MoveDirection.UP
        self.elevator.task_queue = [
            Task(floor=3, call_id="call_1"),
            Task(floor=1),
        ]

        self.elevator._determine_direction()
        assert self.elevator.direction == MoveDirection.UP

    def test_determine_direction_continue_down_when_more_below(self):
        """Test continuing down when current direction is down and more floors below"""
        self.elevator.current_floor = 2
        self.elevator.direction = MoveDirection.DOWN
        self.elevator.task_queue = [
            Task(floor=1, call_id="call_1"),
            Task(floor=3),
        ]

        self.elevator._determine_direction()
        assert self.elevator.direction == MoveDirection.DOWN


class TestElevatorMovementAndUpdates:  # Renamed from TestElevatorMovementRequests
    """Test cases for elevator movement, including floor changes and task handling via update()"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        # self.mock_engine = Mock() # Engine is not directly part of these tests
        # self.mock_world.engine = self.mock_engine
        self.elevator = Elevator(1, self.mock_world, self.mock_api)
        self.elevator.floor_travel_time = 2.0  # Ensure consistent travel time for tests

    def test_request_movement_with_tasks_sets_state_moving(self):
        """Test request_movement_if_needed sets state to MOVING_UP when tasks are present and doors closed."""
        self.elevator.current_floor = 1
        self.elevator.task_queue = [Task(floor=3, call_id="call_1")]
        self.elevator.door_state = DoorState.CLOSED

        with patch("time.time", return_value=100.0) as mock_time:
            self.elevator.request_movement_if_needed()

        assert self.elevator.direction == MoveDirection.UP
        assert self.elevator.state == ElevatorState.MOVING_UP
        assert self.elevator.moving_since == 100.0
        # self.mock_engine.request_movement.assert_not_called() # Engine not called directly

    def test_request_movement_no_tasks_sets_idle(self):
        """Test request_movement_if_needed sets state to IDLE when no tasks."""
        self.elevator.task_queue = []
        self.elevator.state = ElevatorState.MOVING_UP  # Simulate it was moving
        with patch("time.time", return_value=100.0):
            self.elevator.request_movement_if_needed()

        assert self.elevator.state == ElevatorState.IDLE
        assert self.elevator.moving_since is None
        # self.mock_engine.request_movement.assert_not_called()

    def test_request_movement_doors_open_no_state_change(self):
        """Test movement is not initiated and state doesn't change if doors are open."""
        self.elevator.current_floor = 1
        self.elevator.task_queue = [Task(floor=3, call_id="call_1")]
        self.elevator.door_state = DoorState.OPEN
        original_state = self.elevator.state

        self.elevator.request_movement_if_needed()

        assert self.elevator.state == original_state  # Should not change state
        # self.mock_engine.request_movement.assert_not_called()

    @patch("time.time")
    def test_update_moves_elevator_one_floor_up(self, mock_time):
        """Test update moves elevator up one floor after floor_travel_time."""
        mock_time.return_value = 100.0
        self.elevator.current_floor = 1
        self.elevator.task_queue = [Task(floor=3, call_id="call_1")]
        self.elevator.door_state = DoorState.CLOSED
        self.elevator.request_movement_if_needed()  # Sets state to MOVING_UP, moving_since = 100.0

        assert self.elevator.state == ElevatorState.MOVING_UP
        assert self.elevator.current_floor == 1

        # Simulate time passing for travel
        mock_time.return_value = (
            100.0 + self.elevator.floor_travel_time + 0.1
        )  # Time elapsed
        self.elevator.update()

        assert self.elevator.current_floor == 2
        assert self.elevator.floor_changed is True  # set_floor should set this
        assert (
            self.elevator.state == ElevatorState.MOVING_UP
        )  # Should still be moving towards 3
        assert (
            self.elevator.moving_since == mock_time.return_value
        )  # Reset by set_floor

    @patch("time.time")
    def test_update_moves_elevator_one_floor_down(self, mock_time):
        """Test update moves elevator down one floor after floor_travel_time."""
        mock_time.return_value = 100.0
        self.elevator.current_floor = 3
        self.elevator.task_queue = [Task(floor=1, call_id="call_1")]
        self.elevator.door_state = DoorState.CLOSED
        self.elevator.request_movement_if_needed()

        assert self.elevator.state == ElevatorState.MOVING_DOWN
        assert self.elevator.current_floor == 3

        mock_time.return_value = 100.0 + self.elevator.floor_travel_time + 0.1
        self.elevator.update()

        assert self.elevator.current_floor == 2
        assert self.elevator.state == ElevatorState.MOVING_DOWN

    @patch("time.time")
    def test_update_stops_at_target_floor_and_opens_door(self, mock_time):
        """Test update stops at target floor, becomes IDLE, and initiates door opening."""
        mock_time.return_value = 100.0
        self.elevator.current_floor = 1
        self.elevator.task_queue = [
            Task(floor=2, call_id="call_1")
        ]  # Target is next floor
        self.elevator.door_state = DoorState.CLOSED
        self.elevator.request_movement_if_needed()  # MOVING_UP, moving_since = 100.0

        # Simulate travel to floor 2
        mock_time.return_value = 100.0 + self.elevator.floor_travel_time + 0.1
        self.elevator.update()  # Moves to floor 2, floor_changed = True, moving_since updated

        assert self.elevator.current_floor == 2
        assert (
            self.elevator.state == ElevatorState.MOVING_UP
        )  # Still moving as floor_changed needs processing

        # Next update cycle: process floor_changed, announce arrival, become IDLE
        # The arrival_time is set, floor_arrival_announced becomes true after 0.5s
        # Then, if current_floor is task_queue[0].floor, state becomes IDLE

        # Process floor_changed flag set by previous update()
        mock_time.return_value += 0.1  # Small time increment
        self.elevator.update()  # Processes floor_changed, sets arrival_time

        assert self.elevator.floor_arrival_announced is False  # Needs 0.5s delay

        # Simulate announcement delay
        mock_time.return_value = self.elevator.arrival_time + 0.5 + 0.1
        self.elevator.update()  # Announces arrival, becomes IDLE

        assert self.elevator.floor_arrival_announced is True
        assert self.elevator.state == ElevatorState.IDLE
        self.mock_api.send_floor_arrived_message.assert_called_once()

        # Further update to handle door opening
        mock_time.return_value += 0.1  # Small time increment
        self.elevator.update()  # Should open door

        assert self.elevator.door_state == DoorState.OPENING
        assert self.elevator.serviced_current_arrival is True
        assert not self.elevator.task_queue  # Task should be popped

    @patch("time.time")
    def test_update_skips_floor_zero_moving_up(self, mock_time):
        """Test elevator skips floor 0 when moving up from -1 to 1."""
        mock_time.return_value = 100.0
        self.elevator.current_floor = -1
        self.elevator.task_queue = [Task(floor=1)]
        self.elevator.door_state = DoorState.CLOSED
        self.elevator.request_movement_if_needed()  # State MOVING_UP

        assert self.elevator.state == ElevatorState.MOVING_UP

        # Simulate time to pass floor 0 (which is one floor_travel_time from -1)
        mock_time.return_value = 100.0 + self.elevator.floor_travel_time + 0.1
        self.elevator.update()  # Moves to floor 1, sets floor_changed

        assert self.elevator.current_floor == 1  # Should have skipped 0 and landed on 1

        # Additional updates to process arrival and become IDLE
        mock_time.return_value += 0.1
        self.elevator.update()  # Processes floor_changed, sets arrival_time

        assert self.elevator.floor_arrival_announced is False

        mock_time.return_value = (
            self.elevator.arrival_time + 0.5 + 0.1
        )  # Announcement delay
        self.elevator.update()  # Announces arrival, becomes IDLE

        assert self.elevator.state == ElevatorState.IDLE  # Reached target
        self.mock_api.send_floor_arrived_message.assert_called_once()

    @patch("time.time")
    def test_update_skips_floor_zero_moving_down(self, mock_time):
        """Test elevator skips floor 0 when moving down from 1 to -1."""
        mock_time.return_value = 100.0
        self.elevator.current_floor = 1
        self.elevator.task_queue = [Task(floor=-1)]
        self.elevator.door_state = DoorState.CLOSED
        self.elevator.request_movement_if_needed()  # State MOVING_DOWN

        assert self.elevator.state == ElevatorState.MOVING_DOWN

        # Simulate time to pass floor 0
        mock_time.return_value = 100.0 + self.elevator.floor_travel_time + 0.1
        self.elevator.update()  # Moves to floor -1, sets floor_changed

        assert (
            self.elevator.current_floor == -1
        )  # Should have skipped 0 and landed on -1

        # Additional updates to process arrival and become IDLE
        mock_time.return_value += 0.1
        self.elevator.update()  # Processes floor_changed, sets arrival_time

        assert self.elevator.floor_arrival_announced is False

        mock_time.return_value = (
            self.elevator.arrival_time + 0.5 + 0.1
        )  # Announcement delay
        self.elevator.update()  # Announces arrival, becomes IDLE

        assert self.elevator.state == ElevatorState.IDLE  # Reached target
        self.mock_api.send_floor_arrived_message.assert_called_once()

    def test_movement_continues_if_not_at_target_floor(
        self,
    ):
        """Test that elevator continues moving if current floor is not the head of task queue after a move."""
        with patch("time.time") as mock_time:
            mock_time.return_value = 100.0
            self.elevator.current_floor = 1
            self.elevator.task_queue = [
                Task(floor=3),
                Task(floor=4),
            ]  # Target is 3, then 4
            self.elevator.door_state = DoorState.CLOSED
            self.elevator.request_movement_if_needed()  # MOVING_UP

            # Simulate travel to floor 2
            mock_time.return_value = 100.0 + self.elevator.floor_travel_time + 0.1
            self.elevator.update()  # Moves to floor 2

            assert self.elevator.current_floor == 2
            assert (
                self.elevator.state == ElevatorState.MOVING_UP
            )  # Still moving towards 3

            # Process floor_changed flag
            mock_time.return_value += 0.1
            self.elevator.update()  # Processes floor_changed, sets arrival_time

            # Simulate announcement delay
            mock_time.return_value = self.elevator.arrival_time + 0.5 + 0.1
            self.elevator.update()  # Announces arrival (but not a target, so no state change to IDLE yet)

            assert self.elevator.floor_arrival_announced is True
            assert self.elevator.state == ElevatorState.MOVING_UP  # Still moving
            self.mock_api.send_floor_arrived_message.assert_not_called()  # Not a target floor from queue head

            # Next update should continue movement as state is still MOVING_UP
            mock_time.return_value += (
                self.elevator.floor_travel_time
            )  # Enough time for next floor
            self.elevator.update()
            assert self.elevator.current_floor == 3  # Reached first target
            assert (
                self.elevator.state == ElevatorState.MOVING_UP
            )  # Will become IDLE in next cycle


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
