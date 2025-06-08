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
        # self.api will be set in each test method using the api_without_zmq fixture
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
        self.api = api_without_zmq
        self.api.world = self.mock_world

        with patch.object(self.api, "_handle_call_elevator") as mock_handle:
            mock_handle.return_value = {"status": "success"}

            result = self.api._parse_and_execute("call_up@2")

            mock_handle.assert_called_once_with(2, "up")
            assert result is None  # Successful calls return None

    def test_parse_select_floor_command_valid(self, api_without_zmq):
        """TC64: Test parsing valid select_floor command"""
        self.api = api_without_zmq
        self.api.world = self.mock_world

        with patch.object(self.api, "_handle_select_floor") as mock_handle:
            mock_handle.return_value = {"status": "success"}

            result = self.api._parse_and_execute("select_floor@3#1")

            mock_handle.assert_called_once_with(3, 1)
            assert result is None  # Successful selections return None

    def test_parse_open_door_command_valid(self, api_without_zmq):
        """TC65: Test parsing valid open_door command"""
        self.api = api_without_zmq
        self.api.world = self.mock_world
        with patch.object(self.api, "_handle_open_door") as mock_handle:
            mock_handle.return_value = {"status": "success"}

            result = self.api._parse_and_execute("open_door@1")

            mock_handle.assert_called_once_with(1)
            assert result == "door_opened#1"

    def test_parse_close_door_command_valid(self, api_without_zmq):
        """TC66: Test parsing valid close_door command"""
        self.api = api_without_zmq
        self.api.world = self.mock_world
        with patch.object(self.api, "_handle_close_door") as mock_handle:
            mock_handle.return_value = {"status": "success"}

            result = self.api._parse_and_execute("close_door@2")

            mock_handle.assert_called_once_with(2)
            assert result == "door_closed#2"

    def test_parse_reset_command(self, api_without_zmq):
        """TC67: Test parsing reset command"""
        self.api = api_without_zmq
        self.api.world = self.mock_world
        with patch.object(self.api, "_handle_reset") as mock_handle:
            mock_handle.return_value = {"status": "success"}

            result = self.api._parse_and_execute("reset")

            mock_handle.assert_called_once()
            assert result is None  # Successful reset returns None

    def test_parse_unknown_operation(self, api_without_zmq):
        """TC68: Test parsing unknown operation"""
        self.api = api_without_zmq
        self.api.world = self.mock_world
        result = self.api._parse_and_execute("unknown_command@1")

        assert isinstance(result, str)
        assert "error:unknown_command_failed:unknown_operation" in result.lower()

    def test_parse_call_missing_floor(self, api_without_zmq):
        """TC69: Test call command with missing floor argument"""
        self.api = api_without_zmq
        self.api.world = self.mock_world
        result = self.api._parse_and_execute("call_up@")

        assert isinstance(result, str)
        assert "error:call_up_failed:missing_floor_for_call_command" in result.lower()

    def test_parse_select_floor_invalid_format(self, api_without_zmq):
        """TC70: Test select_floor with invalid format"""
        self.api = api_without_zmq
        self.api.world = self.mock_world
        result = self.api._parse_and_execute("select_floor@3")  # Missing elevator ID

        assert isinstance(result, str)
        assert (
            "error:select_floor_failed:invalid_format_for_select_floor"
            in result.lower()
        )

    def test_parse_door_command_missing_elevator_id(self, api_without_zmq):
        """TC71: Test door command with missing elevator ID"""
        self.api = api_without_zmq
        self.api.world = self.mock_world
        # Test with open_door
        result_open = self.api._parse_and_execute("open_door@")
        assert isinstance(result_open, str)
        assert (
            "error:open_door_failed:missing_elevator_id_for_open_door"
            in result_open.lower()
        )

        # Test with close_door
        result_close = self.api._parse_and_execute("close_door@")
        assert isinstance(result_close, str)
        assert (
            "error:close_door_failed:missing_elevator_id_for_close_door"
            in result_close.lower()
        )

    def test_parse_command_value_error_exception(self, api_without_zmq):
        """TC72: Test ValueError exception handling"""
        self.api = api_without_zmq
        self.api.world = self.mock_world
        result = self.api._parse_and_execute("call_up@invalid_floor")

        assert isinstance(result, str)
        assert "error:call_up_failed:invalid_argument_value" in result.lower()

    def test_parse_command_general_exception(self, api_without_zmq):
        """TC73: Test general exception handling"""
        self.api = api_without_zmq
        self.api.world = self.mock_world
        with patch.object(self.api, "_handle_call_elevator") as mock_handle:
            mock_handle.side_effect = Exception("Test exception")

            result = self.api._parse_and_execute("call_up@1")

            assert isinstance(result, str)
            assert "error:call_up_failed:internal_error" in result.lower()


class TestAPICallHandling:
    """Test cases for API call handling (TC74-TC77)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock(spec=Simulator)
        self.mock_dispatcher = Mock(spec=Dispatcher)
        self.mock_world.dispatcher = self.mock_dispatcher

    def test_handle_call_world_not_initialized(self, api_without_zmq):
        """TC74: Test call handling when world/dispatcher not initialized"""
        api = api_without_zmq
        api.world = None

        result = api._handle_call_elevator(1, "up")

        assert result["status"] == "error"
        assert "not initialized" in result["message"].lower()

    def test_handle_call_invalid_floor(self, api_without_zmq):
        """TC75: Test call handling with invalid floor"""
        api = api_without_zmq
        api.world = self.mock_world
        result = api._handle_call_elevator(99, "up")  # Assuming 99 is invalid

        assert result["status"] == "error"
        assert "invalid floor" in result["message"].lower()

    def test_handle_call_successful(self, api_without_zmq):
        """TC76: Test successful call handling"""
        api = api_without_zmq
        api.world = self.mock_world
        result = api._handle_call_elevator(2, "up")

        # Should call dispatcher.add_call
        self.mock_dispatcher.add_call.assert_called_once_with(2, "up")
        assert result["status"] == "success"

    def test_handle_call_exception(self, api_without_zmq):
        """TC77: Test exception during call handling"""
        api = api_without_zmq
        api.world = self.mock_world
        self.mock_dispatcher.add_call.side_effect = Exception("Test exception")

        result = api._handle_call_elevator(1, "up")

        assert result["status"] == "error"
        assert "failed to call elevator" in result["message"].lower()


class TestAPIFloorSelection:
    """Test cases for API floor selection handling (TC78-TC82)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock(spec=Simulator)
        self.mock_dispatcher = Mock(spec=Dispatcher)
        self.mock_world.dispatcher = self.mock_dispatcher

    def test_handle_select_floor_world_not_initialized(self, api_without_zmq):
        """TC78: Test floor selection when world/dispatcher not initialized"""
        api = api_without_zmq
        api.world = None

        result = api._handle_select_floor(2, 1)

        assert result["status"] == "error"
        assert "not initialized" in result["message"].lower()

    def test_handle_select_floor_invalid_floor(self, api_without_zmq):
        """TC79: Test floor selection with invalid floor"""
        api = api_without_zmq
        api.world = self.mock_world
        result = api._handle_select_floor(99, 1)  # Assuming 99 is invalid

        assert result["status"] == "error"
        assert "invalid floor" in result["message"].lower()

    def test_handle_select_floor_invalid_elevator_id(self, api_without_zmq):
        """TC80: Test floor selection with invalid elevator ID"""
        api = api_without_zmq
        api.world = self.mock_world
        result = api._handle_select_floor(2, 99)  # Assuming 99 is invalid

        assert result["status"] == "error"
        assert "invalid elevator" in result["message"].lower()

    def test_handle_select_floor_successful(self, api_without_zmq):
        """TC81: Test successful floor selection"""
        api = api_without_zmq
        api.world = self.mock_world
        result = api._handle_select_floor(2, 1)

        # Should call dispatcher.assign_task with 0-based index
        self.mock_dispatcher.assign_task.assert_called_once_with(0, 2, None)
        assert result["status"] == "success"

    def test_handle_select_floor_exception(self, api_without_zmq):
        """TC82: Test exception during floor selection"""
        api = api_without_zmq
        api.world = self.mock_world
        self.mock_dispatcher.assign_task.side_effect = Exception("Test exception")

        result = api._handle_select_floor(2, 1)

        assert result["status"] == "error"
        assert "failed to select floor" in result["message"].lower()


class TestAPIDoorControl:
    """Test cases for API door control (TC83-TC87)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock(spec=Simulator)
        self.mock_elevator = Mock(spec=Elevator)
        self.mock_world.elevators = [self.mock_elevator]

    def test_handle_open_door_world_not_initialized(self, api_without_zmq):
        """TC83: Test door opening when world not initialized"""
        api = api_without_zmq
        api.world = None

        result = api._handle_open_door(1)

        assert result["status"] == "error"
        assert "not initialized" in result["message"].lower()

    def test_handle_open_door_valid_elevator_id(self, api_without_zmq):
        """TC84: Test door opening with valid elevator ID"""
        api = api_without_zmq
        api.world = self.mock_world
        result = api._handle_open_door(1)

        self.mock_elevator.open_door.assert_called_once()
        assert result["status"] == "success"

    def test_handle_open_door_invalid_elevator_id(self, api_without_zmq):
        """TC85: Test door opening with invalid elevator ID"""
        api = api_without_zmq
        api.world = self.mock_world
        result = api._handle_open_door(99)  # Invalid ID

        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    def test_handle_close_door_successful(self, api_without_zmq):
        """TC86: Test successful door closing"""
        api = api_without_zmq
        api.world = self.mock_world
        result = api._handle_close_door(1)

        self.mock_elevator.close_door.assert_called_once()
        assert result["status"] == "success"

    def test_handle_door_operation_exception(self, api_without_zmq):
        """TC87: Test exception during door operation"""
        api = api_without_zmq
        api.world = self.mock_world
        self.mock_elevator.open_door.side_effect = Exception("Test exception")

        result = api._handle_open_door(1)

        assert result["status"] == "error"
        assert "failed to open door" in result["message"].lower()


class TestAPIStateFetching:
    """Test cases for API state fetching (TC88-TC92)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_world = Mock(spec=Simulator)
        self.mock_elevator = Mock(spec=Elevator)
        self.mock_elevator.id = 1
        self.mock_elevator.current_floor = 2
        self.mock_elevator.state = ElevatorState.IDLE
        self.mock_elevator.door_state = DoorState.CLOSED
        self.mock_elevator.direction = None
        self.mock_elevator.task_queue = []  # Ensure task_queue is initialized
        self.mock_world.elevators = [self.mock_elevator]

    def test_fetch_states_world_not_initialized(self, api_without_zmq):
        """TC88: Test state fetching when world not initialized"""
        api = api_without_zmq
        api.world = None  # Set world to None for this specific test case

        result = api.fetch_states()

        assert isinstance(result, list)  # Should return an empty list
        assert len(result) == 0

    def test_fetch_states_with_state_name_attribute(self, api_without_zmq):
        """TC89: Test state fetching when state has name attribute"""
        api = api_without_zmq
        api.world = self.mock_world
        # Mock state with name attribute
        mock_state = Mock()
        mock_state.name = "IDLE"
        self.mock_elevator.state = mock_state

        result = api.fetch_states()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["state"] == "IDLE"

    def test_fetch_states_with_door_state_name_attribute(self, api_without_zmq):
        """TC90: Test state fetching when door_state has name attribute"""
        api = api_without_zmq
        api.world = self.mock_world
        # Mock door state with name attribute
        mock_door_state = Mock()
        mock_door_state.name = "CLOSED"
        self.mock_elevator.door_state = mock_door_state

        result = api.fetch_states()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["door_state"] == "CLOSED"

    def test_fetch_states_with_direction_value(self, api_without_zmq):
        """TC91: Test state fetching when direction exists"""
        api = api_without_zmq
        api.world = self.mock_world
        from backend.models import MoveDirection

        self.mock_elevator.direction = MoveDirection.UP

        result = api.fetch_states()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["direction"] == "UP"  # Expect string "UP"

    def test_fetch_states_with_direction_name_attribute(self, api_without_zmq):
        """TC92: Test state fetching when direction has name attribute"""
        api = api_without_zmq
        api.world = self.mock_world
        # Mock direction with name attribute
        mock_direction = Mock()
        mock_direction.name = "UP"
        self.mock_elevator.direction = mock_direction

        result = api.fetch_states()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["direction"] == "UP"


if __name__ == "__main__":
    pytest.main([__file__])
