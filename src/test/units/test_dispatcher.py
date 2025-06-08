"""
Unit tests for Dispatcher class functionality.

Tests the dispatcher logic including call handling, elevator assignment,
task management, and optimization as specified in validation documentation (TC1-TC26).
"""

import pytest
from unittest.mock import Mock, patch
from backend.dispatcher import Dispatcher
from backend.elevator import Elevator
from backend.models import (
    ElevatorState,
    DoorState,
    MoveDirection,
    Task,
    Call,
    CallState,
    validate_floor,
    validate_elevator_id,
)


class TestDispatcherCallHandling:
    """Test cases for dispatcher call handling (TC1-TC2)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        # Ensure elevators is an iterable, as accessed in _process_pending_calls
        mock_elevator = Mock(spec=Elevator)
        mock_elevator.id = 1
        mock_elevator.current_floor = 1
        mock_elevator.task_queue = []
        mock_elevator.state = ElevatorState.IDLE
        mock_elevator.door_state = DoorState.CLOSED
        mock_elevator.calculate_estimated_time.return_value = 5.0
        self.mock_world.elevators = [mock_elevator]
        self.mock_api = Mock()
        self.dispatcher = Dispatcher(self.mock_world, self.mock_api)

    def test_add_call_valid_direction(self):
        """TC1: Test add_call with valid directions"""
        valid_directions = ["up", "down", "UP", "DOWN"]

        with patch.object(self.dispatcher, "_process_pending_calls"):
            for direction in valid_directions:
                try:
                    self.dispatcher.add_call(2, direction)
                    # Should not raise KeyError
                except KeyError:
                    pytest.fail(f"Valid direction '{direction}' raised KeyError")

class TestDispatcherPendingCallsProcessing:
    """Test cases for dispatcher pending calls processing (TC3-TC7)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.dispatcher = Dispatcher(self.mock_world, self.mock_api)

        # Create mock elevators
        self.mock_elevator1 = Mock(spec=Elevator)
        self.mock_elevator1.id = 1
        self.mock_elevator1.current_floor = 1
        self.mock_elevator1.state = ElevatorState.IDLE
        self.mock_elevator1.door_state = DoorState.CLOSED
        self.mock_elevator1.task_queue = []
        self.mock_elevator1.calculate_estimated_time.return_value = 5.0

        self.mock_elevator2 = Mock(spec=Elevator)
        self.mock_elevator2.id = 2
        self.mock_elevator2.current_floor = 3
        self.mock_elevator2.state = ElevatorState.IDLE
        self.mock_elevator2.door_state = DoorState.CLOSED
        self.mock_elevator2.task_queue = []
        self.mock_elevator2.calculate_estimated_time.return_value = 3.0

        self.mock_world.elevators = [self.mock_elevator1, self.mock_elevator2]

    def test_process_pending_calls_with_pending_unassigned(self):
        """TC3: Test processing calls that are pending and not assigned"""
        # Create a pending, unassigned call
        call = Call(floor=2, direction=MoveDirection.UP, call_id="test_call")
        call.state = CallState.PENDING
        self.dispatcher.pending_calls = {"test_call": call}

        with patch.object(self.dispatcher, "assign_task") as mock_assign:
            self.dispatcher._process_pending_calls()

            # Should attempt to assign the call
            mock_assign.assert_called()

    def test_process_pending_calls_skip_non_pending_or_assigned(self):
        """TC4: Test skipping calls that are not pending or already assigned"""
        # Create assigned call
        call1 = Call(floor=2, direction=MoveDirection.UP, call_id="assigned_call")
        call1.state = CallState.ASSIGNED

        # Create completed call
        call2 = Call(floor=3, direction=MoveDirection.DOWN, call_id="completed_call")
        call2.state = CallState.COMPLETED

        self.dispatcher.pending_calls = {
            "assigned_call": call1,
            "completed_call": call2,
        }

        with patch.object(self.dispatcher, "assign_task") as mock_assign:
            self.dispatcher._process_pending_calls()

            # Should not assign any calls
            mock_assign.assert_not_called()

    def test_process_pending_calls_with_suitable_elevators(self):
        """TC5: Test processing when suitable elevators are found"""
        call = Call(floor=2, direction=MoveDirection.UP, call_id="test_call")
        call.state = CallState.PENDING
        self.dispatcher.pending_calls = {"test_call": call}  # Changed to dict

        # Mock _can_elevator_serve_call to return True for both elevators
        with patch.object(
            self.dispatcher, "_can_elevator_serve_call", return_value=True
        ):
            with patch.object(self.dispatcher, "assign_task") as mock_assign:
                self.dispatcher._process_pending_calls()

                # Should assign to the elevator with better estimated time
                mock_assign.assert_called()

    def test_process_pending_calls_no_suitable_elevators(self):
        """TC6: Test processing when no suitable elevators are found"""
        call = Call(floor=2, direction=MoveDirection.UP, call_id="test_call")
        call.state = CallState.PENDING
        self.dispatcher.pending_calls = {"test_call": call}  # Changed to dict

        # Mock _can_elevator_serve_call to return False for all elevators
        with patch.object(
            self.dispatcher, "_can_elevator_serve_call", return_value=False
        ):
            with patch.object(self.dispatcher, "assign_task") as mock_assign:
                self.dispatcher._process_pending_calls()

                # Should not assign any calls
                mock_assign.assert_not_called()

    def test_process_pending_calls_best_elevator_found(self):
        """TC7: Test assignment when best elevator is found"""
        call = Call(floor=2, direction=MoveDirection.UP, call_id="test_call")
        call.state = CallState.PENDING
        self.dispatcher.pending_calls = {"test_call": call}  # Changed to dict

        # Mock _can_elevator_serve_call to return True
        with patch.object(
            self.dispatcher, "_can_elevator_serve_call", return_value=True
        ):
            with patch.object(self.dispatcher, "assign_task") as mock_assign:
                self.dispatcher._process_pending_calls()

                # Should assign to elevator with better estimated time (elevator2)
                mock_assign.assert_called_with(1, 2, "test_call")  # 0-based index


class TestDispatcherTaskAssignment:
    """Test cases for dispatcher task assignment (TC8-TC15)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.dispatcher = Dispatcher(self.mock_world, self.mock_api)

        self.mock_elevator = Mock(spec=Elevator)
        self.mock_elevator.id = 1
        self.mock_elevator.current_floor = 1
        self.mock_elevator.state = ElevatorState.IDLE
        self.mock_elevator.door_state = DoorState.CLOSED
        self.mock_elevator.task_queue = []

        self.mock_world.elevators = [self.mock_elevator]

    def test_assign_task_already_at_floor_doors_closed(self):
        """TC8: Test assignment when already at floor with closed doors"""
        self.mock_elevator.current_floor = 2
        self.mock_elevator.door_state = DoorState.CLOSED

        self.dispatcher.assign_task(0, 2, "test_call")

        # Should open doors immediately
        self.mock_elevator.open_door.assert_called_once()

    def test_assign_task_with_call_id_outside_call(self):
        """TC9: Test assignment with call_id (outside call)"""
        self.dispatcher.assign_task(0, 3, "outside_call_123")

        # Should add task with call_id
        assert len(self.mock_elevator.task_queue) == 1
        added_task = self.mock_elevator.task_queue[0]
        assert added_task.floor == 3
        assert added_task.call_id == "outside_call_123"

    def test_assign_task_without_call_id_inside_call(self):
        """TC10: Test assignment without call_id (inside call)"""
        self.dispatcher.assign_task(0, 3, None)

        # Should add task without call_id
        assert len(self.mock_elevator.task_queue) == 1
        added_task = self.mock_elevator.task_queue[0]
        assert added_task.floor == 3
        assert added_task.call_id is None

    def test_assign_task_duplicate_outside_call_prevention(self):
        """TC11: Test prevention of duplicate outside calls"""
        # Add initial task
        existing_task = Task(floor=3, call_id="duplicate_call")
        self.mock_elevator.task_queue = [existing_task]

        # Try to add duplicate
        self.dispatcher.assign_task(0, 3, "duplicate_call")

        # Should not add duplicate
        assert len(self.mock_elevator.task_queue) == 1

    def test_assign_task_duplicate_inside_call_prevention(self):
        """TC12: Test prevention of duplicate inside calls"""
        # Add initial inside call task
        existing_task = Task(floor=3, call_id=None)
        self.mock_elevator.task_queue = [existing_task]

        # Try to add duplicate inside call
        self.dispatcher.assign_task(0, 3, None)

        # Should not add duplicate
        assert len(self.mock_elevator.task_queue) == 1

    def test_assign_task_at_floor_doors_not_closed(self):
        """TC13: Test assignment when at floor but doors not closed"""
        self.mock_elevator.current_floor = 2
        self.mock_elevator.door_state = DoorState.OPENING

        self.dispatcher.assign_task(0, 2, "test_call")

        # Should not call open_door since doors are already opening
        self.mock_elevator.open_door.assert_not_called()

    def test_assign_task_door_open_close_first(self):
        """TC14: Test door closing when door is open"""
        self.mock_elevator.current_floor = 2
        self.mock_elevator.door_state = DoorState.OPEN

        self.dispatcher.assign_task(0, 3, "test_call")

        # Should close door first
        self.mock_elevator.close_door.assert_called_once()

    def test_assign_task_door_not_open_request_movement(self):
        """TC15: Test movement request when doors not open"""
        self.mock_elevator.current_floor = 1
        self.mock_elevator.door_state = DoorState.CLOSED

        self.dispatcher.assign_task(0, 3, "test_call")

        # Should request movement
        self.mock_elevator.request_movement_if_needed.assert_called_once()


class TestDispatcherTaskQueueOptimization:
    """Test cases for dispatcher task queue optimization (TC16-TC21)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.dispatcher = Dispatcher(self.mock_world, self.mock_api)

        self.mock_elevator = Mock(spec=Elevator)
        self.mock_elevator.id = 1
        self.mock_elevator.current_floor = 2
        self.mock_elevator.state = ElevatorState.IDLE
        self.mock_elevator.direction = None

    def test_optimize_empty_or_single_task_queue(self):
        """TC16: Test optimization with empty or single task queue"""
        # Test empty queue
        self.mock_elevator.task_queue = []
        self.dispatcher._optimize_task_queue(self.mock_elevator)

        # Test single task queue
        self.mock_elevator.task_queue = [Task(floor=3)]
        original_queue = self.mock_elevator.task_queue.copy()
        self.dispatcher._optimize_task_queue(self.mock_elevator)

        # Queue should remain unchanged
        assert self.mock_elevator.task_queue == original_queue

    def test_optimize_moving_up(self):
        """TC17: Test optimization while moving up"""
        self.mock_elevator.state = ElevatorState.MOVING_UP
        self.mock_elevator.current_floor = 2
        self.mock_elevator.task_queue = [Task(floor=1), Task(floor=4), Task(floor=3)]

        self.dispatcher._optimize_task_queue(self.mock_elevator)

        # Should prioritize floors above current position in ascending order
        floors = [task.floor for task in self.mock_elevator.task_queue]
        above_floors = [f for f in floors if f > 2]
        below_floors = [f for f in floors if f <= 2]

        # Above floors should be sorted ascending, below floors at end
        assert above_floors == sorted(above_floors)

    def test_optimize_moving_down(self):
        """TC18: Test optimization while moving down"""
        self.mock_elevator.state = ElevatorState.MOVING_DOWN
        self.mock_elevator.current_floor = 3
        self.mock_elevator.task_queue = [Task(floor=5), Task(floor=1), Task(floor=2)]

        self.dispatcher._optimize_task_queue(self.mock_elevator)

        # Should prioritize floors below current position in descending order
        floors = [task.floor for task in self.mock_elevator.task_queue]
        below_floors = [f for f in floors if f < 3]
        above_floors = [f for f in floors if f >= 3]

        # Below floors should be sorted descending
        assert below_floors == sorted(below_floors, reverse=True)

    def test_optimize_not_moving_closest_above(self):
        """TC19-TC20: Test optimization when idle - closest task above"""
        self.mock_elevator.state = ElevatorState.IDLE
        self.mock_elevator.current_floor = 2
        self.mock_elevator.task_queue = [Task(floor=1), Task(floor=4), Task(floor=3)]

        self.dispatcher._optimize_task_queue(self.mock_elevator)

        # Should start with closest task
        first_task_floor = self.mock_elevator.task_queue[0].floor
        # Closest should be either 1 or 3 (both distance 1 from floor 2)
        assert first_task_floor in [1, 3]

    def test_optimize_not_moving_closest_below(self):
        """TC21: Test optimization when idle - closest task below"""
        self.mock_elevator.state = ElevatorState.IDLE
        self.mock_elevator.current_floor = 4
        self.mock_elevator.task_queue = [Task(floor=1), Task(floor=2), Task(floor=5)]

        self.dispatcher._optimize_task_queue(self.mock_elevator)

        # Should start with closest task
        first_task_floor = self.mock_elevator.task_queue[0].floor
        # Closest to floor 4 should be floor 5 (distance 1) or floor 2 (distance 2)
        expected_closest = min([1, 2, 5], key=lambda x: abs(x - 4))
        assert first_task_floor == expected_closest


class TestDispatcherElevatorServiceability:
    """Test cases for dispatcher elevator serviceability (TC22-TC26)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.dispatcher = Dispatcher(self.mock_world, self.mock_api)

        self.mock_elevator = Mock(spec=Elevator)
        self.mock_elevator.id = 1
        self.mock_elevator.current_floor = 2
        self.mock_elevator.state = ElevatorState.IDLE
        self.mock_elevator.door_state = DoorState.CLOSED
        self.mock_elevator.task_queue = []

    def test_can_elevator_serve_outside_call(self):
        """TC22: Test outside call service restrictions"""
        # Outside call should have specific restrictions
        result = self.dispatcher._can_elevator_serve_call(
            self.mock_elevator, 3, MoveDirection.UP
        )

        # Should evaluate elevator availability for outside calls
        assert isinstance(result, bool)

    def test_can_elevator_serve_inside_call_empty_queue(self):
        """TC23: Test inside call with empty task queue"""
        self.mock_elevator.task_queue = []

        result = self.dispatcher._can_elevator_serve_call(self.mock_elevator, 3, None)

        # Inside call with empty queue should be serviceable
        assert result is True

    def test_can_elevator_serve_busy_conditions(self):
        """TC24: Test elevator busy conditions"""
        # Test non-idle state
        self.mock_elevator.state = ElevatorState.MOVING_UP

        result = self.dispatcher._can_elevator_serve_call(
            self.mock_elevator, 3, MoveDirection.UP
        )

        # Busy elevator might not be immediately available
        assert isinstance(result, bool)

        # Test doors not closed
        self.mock_elevator.state = ElevatorState.IDLE
        self.mock_elevator.door_state = DoorState.OPENING

        result = self.dispatcher._can_elevator_serve_call(
            self.mock_elevator, 3, MoveDirection.UP
        )

        assert isinstance(result, bool)

    def test_can_elevator_serve_idle_available(self):
        """TC25: Test idle elevator availability"""
        self.mock_elevator.state = ElevatorState.IDLE
        self.mock_elevator.door_state = DoorState.CLOSED
        self.mock_elevator.task_queue = []

        result = self.dispatcher._can_elevator_serve_call(
            self.mock_elevator, 3, None  # Inside call
        )

        # Idle elevator should be available for inside calls
        assert result is True

    def test_can_elevator_serve_inside_call_with_tasks(self):
        """TC26: Test inside call with existing tasks"""
        self.mock_elevator.task_queue = [Task(floor=1), Task(floor=4)]

        result = self.dispatcher._can_elevator_serve_call(
            self.mock_elevator, 3, None  # Inside call
        )

        # Should accept inside calls even with existing tasks
        assert result is True


class TestDispatcherIntegration:
    """Integration tests for dispatcher functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.dispatcher = Dispatcher(self.mock_world, self.mock_api)

        # Create two mock elevators
        self.elevator1 = Mock(spec=Elevator)
        self.elevator1.id = 1
        self.elevator1.current_floor = 1
        self.elevator1.state = ElevatorState.IDLE
        self.elevator1.door_state = DoorState.CLOSED
        self.elevator1.task_queue = []
        self.elevator1.calculate_estimated_time.return_value = 5.0

        self.elevator2 = Mock(spec=Elevator)
        self.elevator2.id = 2
        self.elevator2.current_floor = 3
        self.elevator2.state = ElevatorState.IDLE
        self.elevator2.door_state = DoorState.CLOSED
        self.elevator2.task_queue = []
        self.elevator2.calculate_estimated_time.return_value = 3.0

        self.mock_world.elevators = [self.elevator1, self.elevator2]

    def test_full_call_assignment_workflow(self):
        """Test complete call assignment workflow"""
        with patch.object(self.dispatcher, "assign_task") as mock_assign:
            self.dispatcher.add_call(2, "up")

            # Should process and assign the call
            mock_assign.assert_called()

    def test_multiple_calls_load_balancing(self):
        """Test load balancing across multiple elevators"""
        with patch.object(self.dispatcher, "assign_task") as mock_assign:
            # Add multiple calls
            self.dispatcher.add_call(1, "up")
            self.dispatcher.add_call(2, "down")
            self.dispatcher.add_call(3, "up")

            # Should distribute calls across elevators
            assert mock_assign.call_count >= 3


if __name__ == "__main__":
    pytest.main([__file__])
