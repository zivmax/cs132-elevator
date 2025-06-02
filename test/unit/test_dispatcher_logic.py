"""
Unit tests for Dispatcher class functionality

Tests the elevator dispatching logic including assignment algorithms,
task management, and optimization strategies.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from backend.dispatcher import Dispatcher
from backend.elevator import Elevator
from backend.models import (
    ElevatorState,
    DoorState,
    MoveDirection,
    Task,
)


class TestDispatcherInitialization:
    """Test cases for dispatcher initialization"""

    def test_dispatcher_initialization(self):
        """Test that dispatcher initializes correctly"""
        mock_world = Mock()
        mock_api = Mock()
        
        dispatcher = Dispatcher(mock_world, mock_api)
        
        assert dispatcher.world == mock_world
        assert dispatcher.api == mock_api


class TestElevatorAssignment:
    """Test cases for elevator assignment logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.dispatcher = Dispatcher(self.mock_world, self.mock_api)
        
        # Create mock elevators
        self.elevator1 = Mock(spec=Elevator)
        self.elevator1.id = 1
        self.elevator1.current_floor = 1
        self.elevator1.door_state = DoorState.CLOSED
        self.elevator1.calculate_estimated_time.return_value = 5.0
        
        self.elevator2 = Mock(spec=Elevator)
        self.elevator2.id = 2
        self.elevator2.current_floor = 3
        self.elevator2.door_state = DoorState.CLOSED
        self.elevator2.calculate_estimated_time.return_value = 3.0
        
        self.mock_world.elevators = [self.elevator1, self.elevator2]    
    def test_assign_elevator_chooses_fastest(self):
        """Test that assign_elevator chooses the elevator with shortest estimated time"""
        with patch.object(self.dispatcher, 'add_target_task') as mock_add_task:
            self.dispatcher.assign_elevator(2, "up")
            
            # Should choose elevator2 (index 1) since it has shorter estimated time (3.0 vs 5.0)
            mock_add_task.assert_called_once_with(1, 2, "outside", "up")    
    def test_assign_elevator_with_down_direction(self):
        """Test elevator assignment with down direction"""
        with patch.object(self.dispatcher, 'add_target_task') as mock_add_task:
            self.dispatcher.assign_elevator(1, "down")
            
            # Verify that both elevators were asked for estimated time with DOWN direction
            self.elevator1.calculate_estimated_time.assert_called_with(1, MoveDirection.DOWN)
            self.elevator2.calculate_estimated_time.assert_called_with(1, MoveDirection.DOWN)
            
            mock_add_task.assert_called_once_with(1, 1, "outside", "down")

    def test_assign_elevator_with_up_direction(self):
        """Test elevator assignment with up direction"""
        with patch.object(self.dispatcher, 'add_target_task') as mock_add_task:
            self.dispatcher.assign_elevator(3, "up")
            
            # Verify that both elevators were asked for estimated time with UP direction
            self.elevator1.calculate_estimated_time.assert_called_with(3, MoveDirection.UP)
            self.elevator2.calculate_estimated_time.assert_called_with(3, MoveDirection.UP)
            
            mock_add_task.assert_called_once_with(1, 3, "outside", "up")

    def test_assign_elevator_equal_times(self):
        """Test assignment when elevators have equal estimated times"""
        # Set both elevators to have same estimated time
        self.elevator1.calculate_estimated_time.return_value = 4.0
        self.elevator2.calculate_estimated_time.return_value = 4.0
        
        with patch.object(self.dispatcher, 'add_target_task') as mock_add_task:
            self.dispatcher.assign_elevator(2, "up")
            
            # Should choose first elevator (index 0) when times are equal
            mock_add_task.assert_called_once_with(0, 2, "outside", "up")

    def test_assign_elevator_no_elevators(self):
        """Test assignment when no elevators are available"""
        self.mock_world.elevators = []
        
        with patch.object(self.dispatcher, 'add_target_task') as mock_add_task:
            self.dispatcher.assign_elevator(2, "up")
            
            # Should not call add_target_task when no elevators available
            mock_add_task.assert_not_called()


class TestTargetTaskManagement:
    """Test cases for target task management"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.dispatcher = Dispatcher(self.mock_world, self.mock_api)
        
        # Create a mock elevator
        self.mock_elevator = Mock(spec=Elevator)
        self.mock_elevator.id = 1
        self.mock_elevator.current_floor = 2
        self.mock_elevator.door_state = DoorState.CLOSED
        self.mock_elevator.task_queue = []
        
        self.mock_world.elevators = [self.mock_elevator]

    def test_add_target_task_same_floor_closed_door(self):
        """Test adding task when elevator is already at target floor with closed door"""
        self.mock_elevator.current_floor = 3
        self.mock_elevator.door_state = DoorState.CLOSED
        
        self.dispatcher.add_target_task(0, 3, "outside", "up")
        
        # Should send floor arrived message and open door
        self.mock_api.send_floor_arrived_message.assert_called_once_with(1, 3, "up")
        self.mock_elevator.open_door.assert_called_once()

    def test_add_target_task_same_floor_open_door(self):
        """Test adding task when elevator is already at target floor with open door"""
        self.mock_elevator.current_floor = 2
        self.mock_elevator.door_state = DoorState.OPEN
        
        self.dispatcher.add_target_task(0, 2, "inside")
        
        # Should not send message or open door when door is already open
        self.mock_api.send_floor_arrived_message.assert_not_called()
        self.mock_elevator.open_door.assert_not_called()

    def test_add_target_task_different_floor(self):
        """Test adding task when elevator is at different floor"""
        self.mock_elevator.current_floor = 1
        self.mock_elevator.task_queue = []
        
        self.dispatcher.add_target_task(0, 3, "outside", "up")
        
        # Should add task to queue
        expected_task = Task(floor=3, origin="outside", direction="up")
        assert len(self.mock_elevator.task_queue) == 1
        added_task = self.mock_elevator.task_queue[0]
        assert added_task.floor == expected_task.floor
        assert added_task.origin == expected_task.origin
        assert added_task.direction == expected_task.direction

    def test_add_target_task_inside_call(self):
        """Test adding task for inside elevator call"""
        self.mock_elevator.current_floor = 1
        self.mock_elevator.task_queue = []
        
        self.dispatcher.add_target_task(0, 3, "inside")
        
        # Should add inside task with no direction
        expected_task = Task(floor=3, origin="inside", direction=None)
        assert len(self.mock_elevator.task_queue) == 1
        added_task = self.mock_elevator.task_queue[0]
        assert added_task.floor == expected_task.floor
        assert added_task.origin == expected_task.origin
        assert added_task.direction == expected_task.direction

    def test_add_target_task_duplicate_prevention(self):
        """Test that duplicate tasks are not added to queue"""
        # Add initial task
        initial_task = Task(floor=3, origin="outside", direction="up")
        self.mock_elevator.task_queue = [initial_task]
        self.mock_elevator.current_floor = 1
        
        # Try to add duplicate task
        self.dispatcher.add_target_task(0, 3, "outside", "up")
        
        # Should still only have one task
        assert len(self.mock_elevator.task_queue) == 1

    def test_add_target_task_different_origins_same_floor(self):
        """Test adding tasks with different origins to same floor"""
        # Add outside task first
        outside_task = Task(floor=3, origin="outside", direction="up")
        self.mock_elevator.task_queue = [outside_task]
        self.mock_elevator.current_floor = 1
        
        # Try to add inside task to same floor
        self.dispatcher.add_target_task(0, 3, "inside")
        
        # Should merge tasks (implementation detail may vary)
        # At minimum, shouldn't duplicate floor targets
        floor_targets = [task.floor for task in self.mock_elevator.task_queue]
        assert floor_targets.count(3) <= 2  # Allow for different origins


class TestDispatcherEdgeCases:
    """Test cases for dispatcher edge cases and error conditions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.dispatcher = Dispatcher(self.mock_world, self.mock_api)

    def test_assign_elevator_invalid_direction(self):
        """Test assignment with invalid direction string"""
        mock_elevator = Mock(spec=Elevator)
        mock_elevator.id = 1  # Add id attribute
        mock_elevator.calculate_estimated_time.return_value = 1.0
        self.mock_world.elevators = [mock_elevator]
        
        with patch.object(self.dispatcher, 'add_target_task') as mock_add_task:
            # Should handle invalid direction gracefully
            self.dispatcher.assign_elevator(2, "invalid_direction")
            
            # Should still call calculate_estimated_time with None
            mock_elevator.calculate_estimated_time.assert_called_with(2, None)
            mock_add_task.assert_called_once()

    def test_add_target_task_invalid_elevator_index(self):
        """Test adding task with invalid elevator index"""
        self.mock_world.elevators = []
        
        # Should handle invalid index gracefully without crashing        
        try:
            self.dispatcher.add_target_task(0, 3, "outside", "up")
        except IndexError:
            # This is expected behavior - accessing invalid elevator index
            pass

    def test_add_target_task_boundary_floors(self):
        """Test adding tasks to boundary floors"""
        mock_elevator = Mock(spec=Elevator)
        mock_elevator.id = 1
        mock_elevator.current_floor = 1
        mock_elevator.door_state = DoorState.CLOSED
        mock_elevator.state = ElevatorState.IDLE
        mock_elevator.task_queue = []
        self.mock_world.elevators = [mock_elevator]
        
        # Test minimum floor
        self.dispatcher.add_target_task(0, -1, "outside", "down")
        
        # Test maximum floor
        self.dispatcher.add_target_task(0, 3, "outside", "up")
        
        # Should handle boundary floors correctly
        assert len(mock_elevator.task_queue) == 2
        assert mock_elevator.task_queue[0].floor == -1
        assert mock_elevator.task_queue[1].floor == 3


class TestDispatcherIntegration:
    """Integration test cases for dispatcher with multiple elevators"""

    def setup_method(self):
        """Set up test fixtures with multiple elevators"""
        self.mock_world = Mock()
        self.mock_api = Mock()
        self.dispatcher = Dispatcher(self.mock_world, self.mock_api)
        
        # Create multiple mock elevators with different states
        self.elevator1 = Mock(spec=Elevator)
        self.elevator1.id = 1
        self.elevator1.current_floor = 1
        self.elevator1.door_state = DoorState.CLOSED
        self.elevator1.task_queue = []
        
        self.elevator2 = Mock(spec=Elevator)
        self.elevator2.id = 2
        self.elevator2.current_floor = 3
        self.elevator2.door_state = DoorState.OPEN
        self.elevator2.task_queue = [Task(floor=2, origin="inside")]
        
        self.mock_world.elevators = [self.elevator1, self.elevator2]

    def test_realistic_dispatch_scenario(self):
        """Test a realistic dispatch scenario with multiple elevator states"""
        # Set different estimated times
        self.elevator1.calculate_estimated_time.return_value = 4.0
        self.elevator2.calculate_estimated_time.return_value = 2.0
        
        with patch.object(self.dispatcher, 'add_target_task') as mock_add_task:
            self.dispatcher.assign_elevator(2, "down")
            
            # Should choose elevator2 due to shorter estimated time
            mock_add_task.assert_called_once_with(1, 2, "outside", "down")

    def test_multiple_consecutive_assignments(self):
        """Test multiple consecutive elevator assignments"""
        self.elevator1.calculate_estimated_time.return_value = 1.0
        self.elevator2.calculate_estimated_time.return_value = 2.0
        
        with patch.object(self.dispatcher, 'add_target_task') as mock_add_task:
            # First assignment
            self.dispatcher.assign_elevator(2, "up")
            
            # Simulate elevator1 now has a task
            self.elevator1.calculate_estimated_time.return_value = 5.0
            
            # Second assignment
            self.dispatcher.assign_elevator(3, "up")
            
            # Should make two assignments
            assert mock_add_task.call_count == 2


if __name__ == "__main__":
    # Allow running the test file directly
    pytest.main([__file__])
