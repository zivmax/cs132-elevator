"""
Test suite for Elevator class functionality.
Covers TC27-TC61 for comprehensive testing of all elevator behaviors.
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from typing import Optional

from backend.elevator import Elevator
from backend.models import ElevatorState, DoorState, MoveDirection, Task


class TestElevatorUpdate:
    """Test cases for Elevator.update() method covering TC27-TC40"""

    def test_floor_changed_flag_processing(self, mock_elevator):
        """TC27: Test floor changed flag processing"""
        elevator = mock_elevator
        elevator.floor_changed = True
        current_time = time.time()

        with patch("time.time", return_value=current_time):
            elevator.update()

        assert not elevator.floor_changed
        assert elevator.arrival_time == current_time
        assert not elevator.floor_arrival_announced
        assert not elevator.serviced_current_arrival
        assert elevator.last_state_change == current_time

    def test_is_moving_state_processing(self, mock_elevator):
        """TC28: Test processing when elevator is moving"""
        elevator = mock_elevator
        elevator.state = ElevatorState.MOVING_UP
        elevator.moving_since = time.time() - 1.0  # 1 second ago
        elevator.floor_travel_time = 2.0

        elevator.update()

        # Should not process door operations while moving
        assert elevator.state == ElevatorState.MOVING_UP

    def test_movement_time_elapsed(self, mock_elevator):
        """TC29: Test movement time elapsed logic"""
        elevator = mock_elevator
        elevator.state = ElevatorState.MOVING_UP
        elevator.current_floor = 2
        elevator.moving_since = time.time() - 3.0  # 3 seconds ago
        elevator.floor_travel_time = 2.0

        with patch.object(elevator, "_set_floor") as mock_set_floor:
            elevator.update()
            mock_set_floor.assert_called_once_with(3)  # Should move up one floor

    def test_next_floor_is_zero_skip(self, mock_elevator):
        """TC30: Test skipping floor 0"""
        elevator = mock_elevator
        elevator.state = ElevatorState.MOVING_DOWN
        elevator.current_floor = 1
        elevator.moving_since = time.time() - 3.0
        elevator.floor_travel_time = 2.0

        with patch.object(elevator, "_set_floor") as mock_set_floor:
            elevator.update()
            mock_set_floor.assert_called_once_with(-1)  # Should skip floor 0

    def test_floor_arrival_announced(self, mock_elevator):
        """TC31: Test floor arrival announcement"""
        elevator = mock_elevator
        current_time = time.time()
        elevator.arrival_time = current_time - 0.6  # Just over 0.5 seconds ago
        elevator.floor_arrival_announced = False
        elevator.task_queue = [Task(floor=2, call_id="test")]
        elevator.current_floor = 2

        with patch("time.time", return_value=current_time):
            with patch.object(
                elevator, "_handle_arrival_at_target_floor"
            ) as mock_handle:
                elevator.update()
                assert elevator.floor_arrival_announced
                mock_handle.assert_called_once_with(current_time)

    def test_reached_target_floor(self, mock_elevator):
        """TC32: Test reaching target floor"""
        elevator = mock_elevator
        elevator.task_queue = [Task(floor=3, call_id="test")]
        elevator.current_floor = 3
        elevator.arrival_time = time.time() - 0.6
        elevator.floor_arrival_announced = False

        with patch.object(elevator, "_handle_arrival_at_target_floor") as mock_handle:
            elevator.update()
            mock_handle.assert_called_once()

    def test_delay_not_completed(self, mock_elevator):
        """TC33: Test delay not completed"""
        elevator = mock_elevator
        current_time = time.time()
        elevator.floor_arrival_announced = True
        elevator.serviced_current_arrival = False
        elevator.arrival_time = current_time - 0.3  # Less than floor_arrival_delay
        elevator.floor_arrival_delay = 0.5

        with patch("time.time", return_value=current_time):
            elevator.update()

        # Should return early without processing doors
        assert elevator.door_state == DoorState.CLOSED

    def test_door_opening_state(self, mock_elevator):
        """TC34: Test door opening state transition"""
        elevator = mock_elevator
        current_time = time.time()
        elevator.door_state = DoorState.OPENING
        elevator.last_door_change = current_time - 1.5  # Beyond door_operation_time
        elevator.door_operation_time = 1.0

        with patch("time.time", return_value=current_time):
            elevator.update()

        assert elevator.door_state == DoorState.OPEN
        assert elevator.last_door_change == current_time

    def test_door_closing_state(self, mock_elevator):
        """TC35: Test door closing state transition"""
        elevator = mock_elevator
        current_time = time.time()
        elevator.door_state = DoorState.CLOSING
        elevator.last_door_change = current_time - 1.5
        elevator.door_operation_time = 1.0

        with patch("time.time", return_value=current_time):
            with patch.object(elevator, "request_movement_if_needed") as mock_request:
                elevator.update()

        assert elevator.door_state == DoorState.CLOSED
        assert elevator.last_door_change == current_time

    def test_door_open_auto_close(self, mock_elevator):
        """TC36: Test door auto-close timeout"""
        elevator = mock_elevator
        current_time = time.time()
        elevator.door_state = DoorState.OPEN
        elevator.last_door_change = current_time - 4.0  # Beyond timeout
        elevator.door_timeout = 3.0

        with patch("time.time", return_value=current_time):
            with patch.object(elevator, "close_door") as mock_close:
                elevator.update()
                mock_close.assert_called_once()

    def test_idle_with_closed_doors_at_target(self, mock_elevator):
        """TC37: Test idle with closed doors at target floor"""
        elevator = mock_elevator
        elevator.state = ElevatorState.IDLE
        elevator.door_state = DoorState.CLOSED
        elevator.floor_arrival_announced = True
        elevator.serviced_current_arrival = False
        elevator.task_queue = [Task(floor=2, call_id="test")]
        elevator.current_floor = 2

        with patch.object(elevator, "open_door") as mock_open:
            elevator.update()
            mock_open.assert_called_once()
            assert elevator.serviced_current_arrival
            assert len(elevator.task_queue) == 0  # Task should be removed

    def test_at_target_floor_condition(self, mock_elevator):
        """TC38: Test at target floor condition"""
        elevator = mock_elevator
        elevator.task_queue = [Task(floor=5, call_id="test")]
        elevator.current_floor = 5
        elevator.state = ElevatorState.IDLE
        elevator.door_state = DoorState.CLOSED
        elevator.floor_arrival_announced = True
        elevator.serviced_current_arrival = False

        with patch.object(elevator, "open_door") as mock_open:
            elevator.update()
            mock_open.assert_called_once()

    def test_no_target_floors(self, mock_elevator):
        """TC39: Test no target floors condition"""
        elevator = mock_elevator
        elevator.task_queue = []
        elevator.state = ElevatorState.IDLE
        elevator.door_state = DoorState.CLOSED
        elevator.floor_arrival_announced = True
        elevator.serviced_current_arrival = False

        with patch.object(elevator, "open_door") as mock_open:
            elevator.update()
            mock_open.assert_called_once()
            assert elevator.serviced_current_arrival

    def test_need_to_move(self, mock_elevator):
        """TC40: Test need to move condition"""
        elevator = mock_elevator
        elevator.state = ElevatorState.IDLE
        elevator.door_state = DoorState.CLOSED
        elevator.task_queue = [Task(floor=3, call_id="test")]
        elevator.current_floor = 1
        elevator.last_state_change = time.time() - 1.0

        with patch.object(elevator, "request_movement_if_needed") as mock_request:
            elevator.update()
            mock_request.assert_called_once()


class TestElevatorDirectionDetermination:
    """Test cases for Elevator._determine_direction() method covering TC41-TC50"""

    def test_no_task_queue(self, mock_elevator):
        """TC41: Test with no task queue"""
        elevator = mock_elevator
        elevator.task_queue = []

        elevator._determine_direction()

        assert elevator.direction is None

    def test_all_floors_above(self, mock_elevator):
        """TC42: Test all floors above current floor"""
        elevator = mock_elevator
        elevator.current_floor = 2
        elevator.task_queue = [Task(floor=4), Task(floor=5), Task(floor=6)]

        elevator._determine_direction()

        assert elevator.direction == MoveDirection.UP

    def test_all_floors_below(self, mock_elevator):
        """TC43: Test all floors below current floor"""
        elevator = mock_elevator
        elevator.current_floor = 5
        elevator.task_queue = [Task(floor=2), Task(floor=3), Task(floor=1)]

        elevator._determine_direction()

        assert elevator.direction == MoveDirection.DOWN

    def test_moving_up_with_floors_above(self, mock_elevator):
        """TC44: Test moving up with floors above"""
        elevator = mock_elevator
        elevator.current_floor = 3
        elevator.direction = MoveDirection.UP
        elevator.task_queue = [Task(floor=5), Task(floor=2)]  # Mixed floors

        elevator._determine_direction()

        assert elevator.direction == MoveDirection.UP

    def test_moving_down_with_floors_below(self, mock_elevator):
        """TC45: Test moving down with floors below"""
        elevator = mock_elevator
        elevator.current_floor = 4
        elevator.direction = MoveDirection.DOWN
        elevator.task_queue = [Task(floor=2), Task(floor=6)]  # Mixed floors

        elevator._determine_direction()

        assert elevator.direction == MoveDirection.DOWN

    def test_choose_closest_floor(self, mock_elevator):
        """TC46: Test choosing closest floor"""
        elevator = mock_elevator
        elevator.current_floor = 3
        elevator.direction = MoveDirection.UP  # But no floors above
        elevator.task_queue = [Task(floor=1), Task(floor=2)]  # Only floors below

        elevator._determine_direction()

        assert elevator.direction == MoveDirection.DOWN

    def test_both_above_and_below_floors(self, mock_elevator):
        """TC47: Test both above and below floors exist"""
        elevator = mock_elevator
        elevator.current_floor = 5
        elevator.task_queue = [Task(floor=3), Task(floor=7)]  # One below, one above

        elevator._determine_direction()

        # Should choose closer one (3 is 2 floors away, 7 is 2 floors away)
        # In case of tie, should choose UP based on implementation
        assert elevator.direction in [MoveDirection.UP, MoveDirection.DOWN]

    def test_only_floors_above(self, mock_elevator):
        """TC48: Test only floors above"""
        elevator = mock_elevator
        elevator.current_floor = 2
        elevator.task_queue = [Task(floor=4), Task(floor=6)]

        elevator._determine_direction()

        assert elevator.direction == MoveDirection.UP

    def test_only_floors_below(self, mock_elevator):
        """TC49: Test only floors below"""
        elevator = mock_elevator
        elevator.current_floor = 5
        elevator.task_queue = [Task(floor=2), Task(floor=1)]

        elevator._determine_direction()

        assert elevator.direction == MoveDirection.DOWN

    def test_no_valid_targets(self, mock_elevator):
        """TC50: Test no valid targets"""
        elevator = mock_elevator
        elevator.current_floor = 3
        elevator.task_queue = [Task(floor=3)]  # Same floor

        # This scenario might not occur in practice but test edge case
        elevator._determine_direction()

        # Should handle gracefully
        assert elevator.direction is None


class TestElevatorTimeEstimation:
    """Test cases for Elevator.calculate_estimated_time() method covering TC51-TC57"""

    def test_already_at_floor_with_open_door(self, mock_elevator):
        """TC51: Test already at floor with open door"""
        elevator = mock_elevator
        elevator.current_floor = 3
        elevator.door_state = DoorState.OPEN

        result = elevator.calculate_estimated_time(3, None)

        assert result == 0

    def test_door_currently_open(self, mock_elevator):
        """TC52: Test door currently open"""
        elevator = mock_elevator
        elevator.current_floor = 2
        elevator.door_state = DoorState.OPEN
        elevator.door_operation_time = 1.0
        elevator.floor_travel_time = 2.0

        result = elevator.calculate_estimated_time(4, None)

        # Should include time to close door + travel + open door
        expected = 1.0 + (2 * 2.0) + 1.0  # close + travel + open
        assert result == expected

    def test_idle_or_not_moving(self, mock_elevator):
        """TC53: Test idle or not moving"""
        elevator = mock_elevator
        elevator.state = ElevatorState.IDLE
        elevator.current_floor = 1
        elevator.door_state = DoorState.CLOSED
        elevator.floor_travel_time = 2.0
        elevator.door_operation_time = 1.0

        result = elevator.calculate_estimated_time(5, None)

        # Direct travel: 4 floors * 2.0 + door opening
        expected = 4 * 2.0 + 1.0
        assert result == expected

    def test_moving_up(self, mock_elevator):
        """TC54: Test moving up"""
        elevator = mock_elevator
        elevator.state = ElevatorState.MOVING_UP
        elevator.current_floor = 2
        elevator.task_queue = [Task(floor=4), Task(floor=6)]
        elevator.direction = MoveDirection.UP
        elevator.floor_travel_time = 2.0
        elevator.door_operation_time = 1.0

        result = elevator.calculate_estimated_time(5, MoveDirection.UP)

        # Should simulate serving existing tasks first
        assert result > 0

    def test_moving_down(self, mock_elevator):
        """TC55: Test moving down"""
        elevator = mock_elevator
        elevator.state = ElevatorState.MOVING_DOWN
        elevator.current_floor = 5
        elevator.task_queue = [Task(floor=3), Task(floor=1)]
        elevator.direction = MoveDirection.DOWN
        elevator.floor_travel_time = 2.0
        elevator.door_operation_time = 1.0

        result = elevator.calculate_estimated_time(2, MoveDirection.DOWN)

        # Should simulate serving existing tasks first
        assert result > 0

    def test_target_floor_reached_during_simulation(self, mock_elevator):
        """TC56: Test target floor reached during simulation"""
        elevator = mock_elevator
        elevator.state = ElevatorState.MOVING_UP
        elevator.current_floor = 2
        elevator.task_queue = [Task(floor=4), Task(floor=6)]
        elevator.direction = MoveDirection.UP
        elevator.floor_travel_time = 2.0
        elevator.door_operation_time = 1.0

        result = elevator.calculate_estimated_time(4, MoveDirection.UP)

        # Should return time to reach floor 4 directly
        expected = 2 * 2.0 + 1.0  # Travel to floor 4 + door operation
        assert result == expected

    def test_complex_simulation_scenario(self, mock_elevator):
        """TC57: Test complex simulation scenario"""
        elevator = mock_elevator
        elevator.state = ElevatorState.MOVING_UP
        elevator.current_floor = 3
        elevator.task_queue = [Task(floor=5), Task(floor=7), Task(floor=2)]
        elevator.direction = MoveDirection.UP
        elevator.floor_travel_time = 2.0
        elevator.door_operation_time = 1.0

        result = elevator.calculate_estimated_time(1, None)

        # Should handle complex routing scenario
        assert result > 0


class TestElevatorDoorOperations:
    """Test cases for Elevator door operations covering TC58-TC61"""

    def test_can_open_door(self, mock_elevator):
        """TC58: Test can open door conditions"""
        elevator = mock_elevator
        elevator.door_state = DoorState.CLOSED
        elevator.state = ElevatorState.IDLE

        elevator.open_door()

        assert elevator.door_state == DoorState.OPENING
        assert elevator.last_door_change > 0

    def test_cannot_open_door_already_open(self, mock_elevator):
        """TC59: Test cannot open door when already open"""
        elevator = mock_elevator
        elevator.door_state = DoorState.OPEN
        original_change_time = elevator.last_door_change

        elevator.open_door()

        # Should not change state or timestamp
        assert elevator.door_state == DoorState.OPEN
        assert elevator.last_door_change == original_change_time

    def test_cannot_open_door_while_closing(self, mock_elevator):
        """TC59: Test cannot open door while closing"""
        elevator = mock_elevator
        elevator.door_state = DoorState.CLOSING
        original_change_time = elevator.last_door_change

        elevator.open_door()

        assert elevator.door_state == DoorState.CLOSING
        assert elevator.last_door_change == original_change_time

    def test_cannot_open_door_while_moving(self, mock_elevator):
        """TC59: Test cannot open door while moving"""
        elevator = mock_elevator
        elevator.door_state = DoorState.CLOSED
        elevator.state = ElevatorState.MOVING_UP
        original_change_time = elevator.last_door_change

        elevator.open_door()

        assert elevator.door_state == DoorState.CLOSED
        assert elevator.last_door_change == original_change_time

    def test_can_close_door(self, mock_elevator):
        """TC60: Test can close door conditions"""
        elevator = mock_elevator
        elevator.door_state = DoorState.OPEN
        elevator.state = ElevatorState.IDLE

        elevator.close_door()

        assert elevator.door_state == DoorState.CLOSING
        assert elevator.last_door_change > 0

    def test_cannot_close_door_already_closed(self, mock_elevator):
        """TC61: Test cannot close door when already closed"""
        elevator = mock_elevator
        elevator.door_state = DoorState.CLOSED
        original_change_time = elevator.last_door_change

        elevator.close_door()

        assert elevator.door_state == DoorState.CLOSED
        assert elevator.last_door_change == original_change_time

    def test_cannot_close_door_while_opening(self, mock_elevator):
        """TC61: Test cannot close door while opening"""
        elevator = mock_elevator
        elevator.door_state = DoorState.OPENING
        original_change_time = elevator.last_door_change

        elevator.close_door()

        assert elevator.door_state == DoorState.OPENING
        assert elevator.last_door_change == original_change_time

    def test_cannot_close_door_while_moving(self, mock_elevator):
        """TC61: Test cannot close door while moving"""
        elevator = mock_elevator
        elevator.door_state = DoorState.OPEN
        elevator.state = ElevatorState.MOVING_DOWN
        original_change_time = elevator.last_door_change

        elevator.close_door()

        assert elevator.door_state == DoorState.OPEN
        assert elevator.last_door_change == original_change_time


class TestElevatorHelperMethods:
    """Test cases for elevator helper methods and additional scenarios"""

    def test_is_moving_true(self, mock_elevator):
        """Test _is_moving returns True for moving states"""
        elevator = mock_elevator

        elevator.state = ElevatorState.MOVING_UP
        assert elevator._is_moving()

        elevator.state = ElevatorState.MOVING_DOWN
        assert elevator._is_moving()

    def test_is_moving_false(self, mock_elevator):
        """Test _is_moving returns False for non-moving states"""
        elevator = mock_elevator
        elevator.state = ElevatorState.IDLE
        assert not elevator._is_moving()

    def test_get_movement_direction_up(self, mock_elevator):
        """Test _get_movement_direction for up movement"""
        elevator = mock_elevator
        elevator.state = ElevatorState.MOVING_UP
        assert elevator._get_movement_direction() == 1

    def test_get_movement_direction_down(self, mock_elevator):
        """Test _get_movement_direction for down movement"""
        elevator = mock_elevator
        elevator.state = ElevatorState.MOVING_DOWN
        assert elevator._get_movement_direction() == -1

    def test_get_movement_direction_idle(self, mock_elevator):
        """Test _get_movement_direction for idle state"""
        elevator = mock_elevator
        elevator.state = ElevatorState.IDLE
        assert elevator._get_movement_direction() == 0

    def test_set_floor_changes_floor(self, mock_elevator):
        """Test _set_floor properly updates floor and flags"""
        elevator = mock_elevator
        elevator.current_floor = 2

        elevator._set_floor(5)

        assert elevator.previous_floor == 2
        assert elevator.current_floor == 5
        assert elevator.floor_changed
        assert elevator.moving_since is not None

    def test_set_moving_state_up(self, mock_elevator):
        """Test _set_moving_state for upward movement"""
        elevator = mock_elevator

        elevator._set_moving_state(MoveDirection.UP.value)

        assert elevator.state == ElevatorState.MOVING_UP
        assert elevator.moving_since is not None
        assert elevator.last_state_change is not None

    def test_set_moving_state_down(self, mock_elevator):
        """Test _set_moving_state for downward movement"""
        elevator = mock_elevator

        elevator._set_moving_state(MoveDirection.DOWN.value)

        assert elevator.state == ElevatorState.MOVING_DOWN
        assert elevator.moving_since is not None

    def test_set_moving_state_idle(self, mock_elevator):
        """Test _set_moving_state for idle state"""
        elevator = mock_elevator

        elevator._set_moving_state("idle")

        assert elevator.state == ElevatorState.IDLE
        assert elevator.moving_since is None

    def test_handle_arrival_at_target_floor_with_call(self, mock_elevator):
        """Test _handle_arrival_at_target_floor with call ID"""
        elevator = mock_elevator
        elevator.task_queue = [Task(floor=3, call_id="test_call")]
        elevator.current_floor = 3

        # Mock dispatcher methods
        elevator.world.dispatcher.get_call_direction.return_value = MoveDirection.UP
        elevator.world.dispatcher.complete_call.return_value = None

        current_time = time.time()
        elevator._handle_arrival_at_target_floor(current_time)

        assert elevator.state == ElevatorState.IDLE
        assert elevator.last_state_change == current_time
        elevator.world.dispatcher.get_call_direction.assert_called_once_with(
            "test_call"
        )
        elevator.world.dispatcher.complete_call.assert_called_once_with("test_call")
        elevator.api.send_floor_arrived_message.assert_called_once_with(
            elevator.id, 3, MoveDirection.UP
        )

    def test_handle_arrival_at_target_floor_inside_call(self, mock_elevator):
        """Test _handle_arrival_at_target_floor for inside call"""
        elevator = mock_elevator
        elevator.task_queue = [Task(floor=3), Task(floor=5)]  # No call_id = inside call
        elevator.current_floor = 3

        current_time = time.time()
        elevator._handle_arrival_at_target_floor(current_time)

        assert elevator.state == ElevatorState.IDLE
        elevator.api.send_floor_arrived_message.assert_called_once_with(
            elevator.id, 3, MoveDirection.UP  # Direction determined from next task
        )

    def test_request_movement_if_needed_with_tasks(self, mock_elevator):
        """Test request_movement_if_needed with tasks"""
        elevator = mock_elevator
        elevator.task_queue = [Task(floor=5)]
        elevator.current_floor = 2
        elevator.door_state = DoorState.CLOSED

        with patch.object(elevator, "_determine_direction") as mock_determine:
            with patch.object(elevator, "_set_moving_state") as mock_set_moving:
                elevator.direction = MoveDirection.UP
                elevator.request_movement_if_needed()

                mock_determine.assert_called_once()
                mock_set_moving.assert_called_once_with(MoveDirection.UP.value)

    def test_request_movement_if_needed_no_tasks(self, mock_elevator):
        """Test request_movement_if_needed without tasks"""
        elevator = mock_elevator
        elevator.task_queue = []
        elevator.state = ElevatorState.MOVING_UP

        elevator.request_movement_if_needed()

        assert elevator.state == ElevatorState.IDLE
        assert elevator.moving_since is None

    def test_reset_elevator(self, mock_elevator):
        """Test elevator reset functionality"""
        elevator = mock_elevator
        elevator.current_floor = 5
        elevator.task_queue = [Task(floor=3)]
        elevator.state = ElevatorState.MOVING_UP
        elevator.door_state = DoorState.OPEN
        elevator.direction = MoveDirection.UP

        elevator.reset()

        assert elevator.current_floor == 1
        assert elevator.previous_floor == 1
        assert elevator.task_queue == []
        assert elevator.state == ElevatorState.IDLE
        assert elevator.door_state == DoorState.CLOSED
        assert elevator.direction is None
        assert not elevator.floor_changed
        assert not elevator.floor_arrival_announced
        assert elevator.arrival_time is None
        assert not elevator.serviced_current_arrival
        assert elevator.moving_since is None
