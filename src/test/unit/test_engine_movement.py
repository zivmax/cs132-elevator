"""
Unit tests for Engine class functionality

Tests the movement engine logic including movement requests,
state management, and floor transitions.
"""

import pytest
import time
from unittest.mock import Mock


from backend.engine import Engine
from backend.models import MoveRequest, MoveDirection, ElevatorState
from backend.elevator import Elevator


class TestEngineInitialization:
    """Test cases for engine initialization"""

    def test_engine_initialization(self):
        """Test that engine initializes correctly"""
        mock_world = Mock()

        engine = Engine(mock_world)

        assert engine.world == mock_world
        assert engine.movement_requests == {}


class TestMovementRequests:
    """Test cases for movement request handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.engine = Engine(self.mock_world)

        # Create mock elevators
        self.mock_elevator1 = Mock(spec=Elevator)
        self.mock_elevator1.id = 1
        self.mock_elevator1.current_floor = 1
        self.mock_elevator1.moving_since = None
        self.mock_elevator1.floor_travel_time = 2.0
        self.mock_elevator1.task_queue = []

        self.mock_elevator2 = Mock(spec=Elevator)
        self.mock_elevator2.id = 2
        self.mock_elevator2.current_floor = 3
        self.mock_elevator2.moving_since = None
        self.mock_elevator2.floor_travel_time = 2.0
        self.mock_elevator2.task_queue = []

        self.mock_world.elevators = [self.mock_elevator1, self.mock_elevator2]

    def test_request_movement_up(self):
        """Test requesting upward movement"""
        move_request = MoveRequest(1, MoveDirection.UP)

        self.engine.request_movement(move_request)

        # Should store the movement request
        assert self.engine.movement_requests[1] == MoveDirection.UP.value

        # Should set elevator's moving state
        self.mock_elevator1.set_moving_state.assert_called_once_with(
            MoveDirection.UP.value
        )

    def test_request_movement_down(self):
        """Test requesting downward movement"""
        move_request = MoveRequest(2, MoveDirection.DOWN)

        self.engine.request_movement(move_request)

        # Should store the movement request
        assert self.engine.movement_requests[2] == MoveDirection.DOWN.value

        # Should set elevator's moving state
        self.mock_elevator2.set_moving_state.assert_called_once_with(
            MoveDirection.DOWN.value
        )

    def test_request_movement_multiple_elevators(self):
        """Test requesting movement for multiple elevators"""
        move_request1 = MoveRequest(1, MoveDirection.UP)
        move_request2 = MoveRequest(2, MoveDirection.DOWN)

        self.engine.request_movement(move_request1)
        self.engine.request_movement(move_request2)

        # Should store both requests
        assert self.engine.movement_requests[1] == MoveDirection.UP.value
        assert self.engine.movement_requests[2] == MoveDirection.DOWN.value

        # Should set both elevators' moving states
        self.mock_elevator1.set_moving_state.assert_called_with(MoveDirection.UP.value)
        self.mock_elevator2.set_moving_state.assert_called_with(
            MoveDirection.DOWN.value
        )

    def test_request_movement_overwrite_existing(self):
        """Test that new movement request overwrites existing one"""
        # First request
        move_request1 = MoveRequest(1, MoveDirection.UP)
        self.engine.request_movement(move_request1)

        # Second request for same elevator
        move_request2 = MoveRequest(1, MoveDirection.DOWN)
        self.engine.request_movement(move_request2)

        # Should have the latest request
        assert self.engine.movement_requests[1] == MoveDirection.DOWN.value

        # Should have called set_moving_state twice
        assert self.mock_elevator1.set_moving_state.call_count == 2


class TestMovementUpdates:
    """Test cases for movement update processing"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.engine = Engine(self.mock_world)

        # Create mock elevator
        self.mock_elevator = Mock(spec=Elevator)
        self.mock_elevator.id = 1
        self.mock_elevator.current_floor = 2
        self.mock_elevator.floor_travel_time = 2.0
        self.mock_elevator.task_queue = []

        self.mock_world.elevators = [self.mock_elevator]

    def test_update_no_movement_requests(self):
        """Test update when there are no movement requests"""
        self.mock_elevator.is_moving.return_value = False

        self.engine.update()

        # Should not attempt to move elevator
        self.mock_elevator.set_floor.assert_not_called()

    def test_update_elevator_not_moving(self):
        """Test update when elevator is not in moving state"""
        self.engine.movement_requests[1] = MoveDirection.UP.value
        self.mock_elevator.is_moving.return_value = False

        self.engine.update()

        # Should not move elevator if it's not in moving state
        self.mock_elevator.set_floor.assert_not_called()

    def test_update_moving_time_not_elapsed(self):
        """Test update when moving time has not elapsed"""
        self.engine.movement_requests[1] = MoveDirection.UP.value
        self.mock_elevator.is_moving.return_value = True
        self.mock_elevator.moving_since = time.time()  # Just started moving
        self.mock_elevator.get_movement_direction.return_value = 1

        self.engine.update()

        # Should not move to next floor yet
        self.mock_elevator.set_floor.assert_not_called()

    def test_update_moving_up_time_elapsed(self):
        """Test update when moving up and enough time has elapsed"""
        self.engine.movement_requests[1] = MoveDirection.UP.value
        self.mock_elevator.is_moving.return_value = True
        self.mock_elevator.moving_since = (
            time.time() - 2.5
        )  # More than floor_travel_time
        self.mock_elevator.get_movement_direction.return_value = 1
        self.mock_elevator.current_floor = 2
        self.mock_elevator.task_queue = []

        self.engine.update()

        # Should move to next floor up
        self.mock_elevator.set_floor.assert_called_once_with(3)
        # Should remove movement request when no more tasks
        assert 1 not in self.engine.movement_requests

    def test_update_moving_down_time_elapsed(self):
        """Test update when moving down and enough time has elapsed"""
        self.engine.movement_requests[1] = MoveDirection.DOWN.value
        self.mock_elevator.is_moving.return_value = True
        self.mock_elevator.moving_since = (
            time.time() - 2.5
        )  # More than floor_travel_time
        self.mock_elevator.get_movement_direction.return_value = -1
        self.mock_elevator.current_floor = 2
        self.mock_elevator.task_queue = []

        self.engine.update()

        # Should move to next floor down
        self.mock_elevator.set_floor.assert_called_once_with(1)
        # Should remove movement request when no more tasks
        assert 1 not in self.engine.movement_requests

    def test_update_reached_target_floor(self):
        """Test update when elevator reaches target floor"""
        from backend.models import Task

        self.engine.movement_requests[1] = MoveDirection.UP.value
        self.mock_elevator.is_moving.return_value = True
        self.mock_elevator.moving_since = time.time() - 2.5
        self.mock_elevator.get_movement_direction.return_value = 1
        self.mock_elevator.current_floor = 2
        # Next floor (3) is the target
        self.mock_elevator.task_queue = [Task(floor=3, call_id="call_1")]

        self.engine.update()

        # Should move to target floor
        self.mock_elevator.set_floor.assert_called_once_with(3)
        # Should remove movement request when reaching target
        assert 1 not in self.engine.movement_requests

    def test_update_continue_past_target(self):
        """Test update when elevator has more floors to visit"""
        from backend.models import Task

        self.engine.movement_requests[1] = MoveDirection.UP.value
        self.mock_elevator.is_moving.return_value = True
        self.mock_elevator.moving_since = time.time() - 2.5
        self.mock_elevator.get_movement_direction.return_value = 1
        self.mock_elevator.current_floor = 1  # Multiple target floors
        self.mock_elevator.task_queue = [
            Task(floor=2, call_id="call_1"),
            Task(floor=3),
        ]

        self.engine.update()

        # Should move to next floor
        self.mock_elevator.set_floor.assert_called_once_with(2)
        # Movement request should be removed as the first task's floor is reached
        assert 1 not in self.engine.movement_requests

    def test_update_multiple_elevators(self):
        """Test update with multiple elevators moving"""
        # Set up second elevator
        mock_elevator2 = Mock(spec=Elevator)
        mock_elevator2.id = 2
        mock_elevator2.current_floor = 3
        mock_elevator2.floor_travel_time = 2.0
        mock_elevator2.task_queue = []
        self.mock_world.elevators.append(mock_elevator2)

        # Set up movement requests for both
        self.engine.movement_requests[1] = MoveDirection.UP.value
        self.engine.movement_requests[2] = MoveDirection.DOWN.value

        # Both elevators ready to move
        self.mock_elevator.is_moving.return_value = True
        self.mock_elevator.moving_since = time.time() - 2.5
        self.mock_elevator.get_movement_direction.return_value = 1

        mock_elevator2.is_moving.return_value = True
        mock_elevator2.moving_since = time.time() - 2.5
        mock_elevator2.get_movement_direction.return_value = -1

        self.engine.update()

        # Both elevators should move
        self.mock_elevator.set_floor.assert_called_once_with(3)
        mock_elevator2.set_floor.assert_called_once_with(2)


class TestEngineEdgeCases:
    """Test cases for engine edge cases and error conditions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.engine = Engine(self.mock_world)

    def test_update_empty_elevators_list(self):
        """Test update with no elevators"""
        self.mock_world.elevators = []

        # Should not crash
        self.engine.update()

    def test_update_elevator_missing_moving_since(self):
        """Test update when elevator has None for moving_since"""
        mock_elevator = Mock(spec=Elevator)
        mock_elevator.id = 1
        mock_elevator.moving_since = None
        mock_elevator.is_moving.return_value = True
        self.mock_world.elevators = [mock_elevator]
        self.engine.movement_requests[1] = MoveDirection.UP.value

        # Should not move elevator when moving_since is None
        self.engine.update()
        mock_elevator.set_floor.assert_not_called()

    def test_request_movement_invalid_elevator_id(self):
        """Test movement request for non-existent elevator"""
        self.mock_world.elevators = []
        move_request = MoveRequest(99, MoveDirection.UP)

        # Should handle gracefully without crashing
        try:
            self.engine.request_movement(move_request)
            # Should still store the request even if elevator doesn't exist
            assert self.engine.movement_requests[99] == MoveDirection.UP.value
        except IndexError:
            # This is acceptable behavior
            pass

    def test_update_boundary_floors(self):
        """Test movement update at boundary floors"""
        mock_elevator = Mock(spec=Elevator)
        mock_elevator.id = 1
        mock_elevator.current_floor = 3  # At max floor
        mock_elevator.floor_travel_time = 2.0
        mock_elevator.is_moving.return_value = True
        mock_elevator.moving_since = time.time() - 2.5
        mock_elevator.get_movement_direction.return_value = 1  # Still trying to go up
        mock_elevator.task_queue = []

        self.mock_world.elevators = [mock_elevator]
        self.engine.movement_requests[1] = MoveDirection.UP.value

        self.engine.update()

        # Should attempt to move even beyond boundary (boundary checking is elsewhere)
        mock_elevator.set_floor.assert_called_once_with(4)


class TestEngineIntegration:
    """Integration test cases for engine with realistic scenarios"""

    def setup_method(self):
        """Set up test fixtures for integration tests"""
        self.mock_world = Mock()
        self.engine = Engine(self.mock_world)

    def test_complete_movement_cycle(self):
        """Test a complete movement cycle from request to completion"""
        from backend.models import Task

        # Set up elevator
        mock_elevator = Mock(spec=Elevator)
        mock_elevator.id = 1
        mock_elevator.current_floor = 1
        mock_elevator.floor_travel_time = 2.0
        mock_elevator.task_queue = [Task(floor=3, call_id="call_1")]
        self.mock_world.elevators = [mock_elevator]

        # Initial movement request
        move_request = MoveRequest(1, MoveDirection.UP)
        self.engine.request_movement(move_request)

        # Simulate elevator starting to move
        mock_elevator.is_moving.return_value = True
        mock_elevator.get_movement_direction.return_value = 1

        # First update - not enough time elapsed
        mock_elevator.moving_since = time.time()
        self.engine.update()
        mock_elevator.set_floor.assert_not_called()

        # Second update - enough time elapsed to reach floor 2
        mock_elevator.moving_since = time.time() - 2.5
        mock_elevator.current_floor = 1
        self.engine.update()
        mock_elevator.set_floor.assert_called_with(2)

        # Simulate reaching final target floor
        mock_elevator.moving_since = time.time() - 2.5
        mock_elevator.current_floor = 2
        self.engine.update()
        mock_elevator.set_floor.assert_called_with(3)

        # Movement request should be removed when target reached
        assert 1 not in self.engine.movement_requests


if __name__ == "__main__":
    # Allow running the test file directly
    pytest.main([__file__])
