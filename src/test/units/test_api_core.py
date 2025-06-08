"""
Unit tests for ElevatorAPI class functionality.

Tests the API command parsing, execution, and error handling
as specified in the validation documentation (TC62-TC92).
"""

import pytest
from unittest.mock import Mock, patch
from backend.api.core import ElevatorAPI
from backend.simulator import Simulator
from backend.dispatcher import Dispatcher
from backend.elevator import Elevator
from backend.models import (
    ElevatorState,
    DoorState,
    validate_floor,
    validate_elevator_id,
)


class TestElevatorAPIInitialization:
    """Test cases for ElevatorAPI initialization"""

    def test_api_creation(self, api_without_zmq):
        """Test basic API creation"""
        api = api_without_zmq

        assert api is not None
        assert hasattr(api, "world")
        assert api.world is None  # Initially None


class TestAPICommandParsing:
    """Test cases for API command parsing and execution (TC62-TC73)"""    
    def setup_method(self):
        """Set up test fixtures"""
        # This will be set in each test method using the fixture
        self.api = None
        self.mock_world = Mock(spec=Simulator)
        self.mock_dispatcher = Mock(spec=Dispatcher)
        self.mock_world.dispatcher = self.mock_dispatcher

    def test_parse_command_world_not_initialized(self, api_without_zmq):
        """TC62: Test command parsing when world is not initialized"""
        api = api_without_zmq
        api.world = None
        
        result = api._parse_and_execute("call_up@1")
        
        assert result == "error:world_not_initialized"

    def test_parse_call_command_valid(self, api_without_zmq):
        """TC63: Test parsing valid call command"""
        api = api_without_zmq
        api.world = self.mock_world
        
        with patch.object(api, "_handle_call_elevator") as mock_handle:
            mock_handle.return_value = {"status": "success"}

            result = api._parse_and_execute("call_up@2")

            mock_handle.assert_called_once_with(2, "up")            
            assert result["status"] == "success"

    def test_parse_select_floor_command_valid(self, api_without_zmq):
        """TC64: Test parsing valid select_floor command"""
        api = api_without_zmq
        api.world = self.mock_world
        
        with patch.object(api, "_handle_select_floor") as mock_handle:
            mock_handle.return_value = {"status": "success"}

            result = api._parse_and_execute("select_floor@3#1")

            mock_handle.assert_called_once_with(3, 1)
            assert result["status"] == "success"

    def test_parse_open_door_command_valid(self):
        """TC65: Test parsing valid open_door command"""
        with patch.object(self.api, "_handle_open_door") as mock_handle:
            mock_handle.return_value = {"status": "success"}

            result = self.api._parse_and_execute("open_door#1")

            mock_handle.assert_called_once_with(1)
            assert result["status"] == "success"

    def test_parse_close_door_command_valid(self):
        """TC66: Test parsing valid close_door command"""
        with patch.object(self.api, "_handle_close_door") as mock_handle:
            mock_handle.return_value = {"status": "success"}

            result = self.api._parse_and_execute("close_door#2")

            mock_handle.assert_called_once_with(2)
            assert result["status"] == "success"

    def test_parse_reset_command(self):
        """TC67: Test parsing reset command"""
        with patch.object(self.api, "_handle_reset") as mock_handle:
            mock_handle.return_value = {"status": "success"}

            result = self.api._parse_and_execute("reset")

            mock_handle.assert_called_once()
            assert result["status"] == "success"

    def test_parse_unknown_operation(self):
        """TC68: Test parsing unknown operation"""
        result = self.api._parse_and_execute("unknown_command@1")

        assert result["status"] == "error"
        assert "unknown operation" in result["message"].lower()

    def test_parse_call_missing_floor(self):
        """TC69: Test call command with missing floor argument"""
        result = self.api._parse_and_execute("call_up@")

        assert result["status"] == "error"
        assert (
            "missing" in result["message"].lower()
            or "invalid" in result["message"].lower()
        )

    def test_parse_select_floor_invalid_format(self):
        """TC70: Test select_floor with invalid format"""
        result = self.api._parse_and_execute("select_floor@3")  # Missing elevator ID

        assert result["status"] == "error"
        assert (
            "invalid" in result["message"].lower()
            or "format" in result["message"].lower()
        )

    def test_parse_door_command_missing_elevator_id(self):
        """TC71: Test door command with missing elevator ID"""
        result = self.api._parse_and_execute("open_door#")

        assert result["status"] == "error"
        assert (
            "missing" in result["message"].lower()
            or "invalid" in result["message"].lower()
        )

    def test_parse_command_value_error_exception(self):
        """TC72: Test ValueError exception handling"""
        result = self.api._parse_and_execute("call_up@invalid_floor")

        assert result["status"] == "error"
        assert "error" in result["message"].lower()

    def test_parse_command_general_exception(self):
        """TC73: Test general exception handling"""
        with patch.object(self.api, "_handle_call_elevator") as mock_handle:
            mock_handle.side_effect = Exception("Test exception")

            result = self.api._parse_and_execute("call_up@1")

            assert result["status"] == "error"
            assert "error" in result["message"].lower()


class TestAPICallHandling:
    """Test cases for API call handling (TC74-TC77)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.api = ElevatorAPI()
        self.mock_world = Mock(spec=Simulator)
        self.mock_dispatcher = Mock(spec=Dispatcher)
        self.mock_world.dispatcher = self.mock_dispatcher
        self.api.world = self.mock_world

    def test_handle_call_world_not_initialized(self):
        """TC74: Test call handling when world/dispatcher not initialized"""
        self.api.world = None

        result = self.api._handle_call_elevator(1, "up")

        assert result["status"] == "error"
        assert "not initialized" in result["message"].lower()

    def test_handle_call_invalid_floor(self):
        """TC75: Test call handling with invalid floor"""
        result = self.api._handle_call_elevator(99, "up")  # Assuming 99 is invalid

        assert result["status"] == "error"
        assert "invalid floor" in result["message"].lower()

    def test_handle_call_successful(self):
        """TC76: Test successful call handling"""
        result = self.api._handle_call_elevator(2, "up")

        # Should call dispatcher.add_call
        self.mock_dispatcher.add_call.assert_called_once_with(2, "up")
        assert result["status"] == "success"

    def test_handle_call_exception(self):
        """TC77: Test exception during call handling"""
        self.mock_dispatcher.add_call.side_effect = Exception("Test exception")

        result = self.api._handle_call_elevator(1, "up")

        assert result["status"] == "error"
        assert "error" in result["message"].lower()


class TestAPIFloorSelection:
    """Test cases for API floor selection handling (TC78-TC82)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.api = ElevatorAPI()
        self.mock_world = Mock(spec=Simulator)
        self.mock_dispatcher = Mock(spec=Dispatcher)
        self.mock_world.dispatcher = self.mock_dispatcher
        self.api.world = self.mock_world

    def test_handle_select_floor_world_not_initialized(self):
        """TC78: Test floor selection when world/dispatcher not initialized"""
        self.api.world = None

        result = self.api._handle_select_floor(2, 1)

        assert result["status"] == "error"
        assert "not initialized" in result["message"].lower()

    def test_handle_select_floor_invalid_floor(self):
        """TC79: Test floor selection with invalid floor"""
        result = self.api._handle_select_floor(99, 1)  # Assuming 99 is invalid

        assert result["status"] == "error"
        assert "invalid floor" in result["message"].lower()

    def test_handle_select_floor_invalid_elevator_id(self):
        """TC80: Test floor selection with invalid elevator ID"""
        result = self.api._handle_select_floor(2, 99)  # Assuming 99 is invalid

        assert result["status"] == "error"
        assert "invalid elevator" in result["message"].lower()

    def test_handle_select_floor_successful(self):
        """TC81: Test successful floor selection"""
        result = self.api._handle_select_floor(2, 1)

        # Should call dispatcher.assign_task with 0-based index
        self.mock_dispatcher.assign_task.assert_called_once_with(0, 2, None)
        assert result["status"] == "success"

    def test_handle_select_floor_exception(self):
        """TC82: Test exception during floor selection"""
        self.mock_dispatcher.assign_task.side_effect = Exception("Test exception")

        result = self.api._handle_select_floor(2, 1)

        assert result["status"] == "error"
        assert "error" in result["message"].lower()


class TestAPIDoorControl:
    """Test cases for API door control (TC83-TC87)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.api = ElevatorAPI()
        self.mock_world = Mock(spec=Simulator)
        self.mock_elevator = Mock(spec=Elevator)
        self.mock_world.elevators = [self.mock_elevator]
        self.api.world = self.mock_world

    def test_handle_open_door_world_not_initialized(self):
        """TC83: Test door opening when world not initialized"""
        self.api.world = None

        result = self.api._handle_open_door(1)

        assert result["status"] == "error"
        assert "not initialized" in result["message"].lower()

    def test_handle_open_door_valid_elevator_id(self):
        """TC84: Test door opening with valid elevator ID"""
        result = self.api._handle_open_door(1)

        self.mock_elevator.open_door.assert_called_once()
        assert result["status"] == "success"

    def test_handle_open_door_invalid_elevator_id(self):
        """TC85: Test door opening with invalid elevator ID"""
        result = self.api._handle_open_door(99)  # Invalid ID

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    def test_handle_close_door_successful(self):
        """TC86: Test successful door closing"""
        result = self.api._handle_close_door(1)

        self.mock_elevator.close_door.assert_called_once()
        assert result["status"] == "success"

    def test_handle_door_operation_exception(self):
        """TC87: Test exception during door operation"""
        self.mock_elevator.open_door.side_effect = Exception("Test exception")

        result = self.api._handle_open_door(1)

        assert result["status"] == "error"
        assert "error" in result["message"].lower()


class TestAPIStateFetching:
    """Test cases for API state fetching (TC88-TC92)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.api = ElevatorAPI()
        self.mock_world = Mock(spec=Simulator)
        self.mock_elevator = Mock(spec=Elevator)
        self.mock_elevator.id = 1
        self.mock_elevator.current_floor = 2
        self.mock_elevator.state = ElevatorState.IDLE
        self.mock_elevator.door_state = DoorState.CLOSED
        self.mock_elevator.direction = None
        self.mock_world.elevators = [self.mock_elevator]
        self.api.world = self.mock_world

    def test_fetch_states_world_not_initialized(self):
        """TC88: Test state fetching when world not initialized"""
        self.api.world = None

        result = self.api.fetch_states()

        assert result["status"] == "error"
        assert "not initialized" in result["message"].lower()

    def test_fetch_states_with_state_name_attribute(self):
        """TC89: Test state fetching when state has name attribute"""
        # Mock state with name attribute
        mock_state = Mock()
        mock_state.name = "IDLE"
        self.mock_elevator.state = mock_state

        result = self.api.fetch_states()

        assert result["status"] == "success"
        assert "elevators" in result
        assert result["elevators"][0]["state"] == "IDLE"

    def test_fetch_states_with_door_state_name_attribute(self):
        """TC90: Test state fetching when door_state has name attribute"""
        # Mock door state with name attribute
        mock_door_state = Mock()
        mock_door_state.name = "CLOSED"
        self.mock_elevator.door_state = mock_door_state

        result = self.api.fetch_states()

        assert result["status"] == "success"
        assert "elevators" in result
        assert result["elevators"][0]["door_state"] == "CLOSED"

    def test_fetch_states_with_direction_value(self):
        """TC91: Test state fetching when direction exists"""
        from backend.models import MoveDirection

        self.mock_elevator.direction = MoveDirection.UP

        result = self.api.fetch_states()

        assert result["status"] == "success"
        assert "elevators" in result
        # Direction should be included in the response

    def test_fetch_states_with_direction_name_attribute(self):
        """TC92: Test state fetching when direction has name attribute"""
        # Mock direction with name attribute
        mock_direction = Mock()
        mock_direction.name = "UP"
        self.mock_elevator.direction = mock_direction

        result = self.api.fetch_states()

        assert result["status"] == "success"
        assert "elevators" in result
        assert result["elevators"][0]["direction"] == "UP"


if __name__ == "__main__":
    pytest.main([__file__])
