"""
Unit tests for command parsing functionality in the elevator system.

This module tests the parsing of ZMQ messages into command objects,
including validation of different command formats and error handling.
"""

import pytest
from unittest.mock import MagicMock  # Added for mocking

# Import ElevatorAPI, as it now handles parsing and execution.
# Command classes like CallCommand, ParseError are not directly returned by _parse_and_execute
# so they are not imported here for testing the output of _parse_and_execute.
from backend.api.core import ElevatorAPI

# We might need to define expected error strings or import them if they are constants.


# Mock the Simulator class as ElevatorAPI expects a 'world' instance
class MockSimulator:
    def __init__(self):
        self.dispatcher = MagicMock()
        self.elevators = [MagicMock(), MagicMock()]
        # Add any other attributes or methods ElevatorAPI might access during parsing/initial execution
        self.api = None  # Will be set by ElevatorAPI if it tries to link back


# Define constants for expected responses if they are not available from elsewhere
# These would correspond to what _format_failure_for_zmq and successful command processing return.
# Example (actual values depend on ElevatorAPI implementation):
MSG_DOOR_OPENED_1 = "door_opened#1"
MSG_DOOR_CLOSED_2 = "door_closed#2"
# ... other success messages

# Example error messages based on the new _format_failure_for_zmq
ERR_WORLD_NOT_INITIALIZED = "error:world_not_initialized"
ERR_UNKNOWN_OPERATION = "error:unknown_command_failed:unknown_operation_unknown_command"  # Example, adjust to actual format
ERR_INVALID_CALL_FORMAT = (
    "error:call_up_failed:missing_floor_for_call_command"  # Example
)
ERR_INVALID_SELECT_FLOOR_FORMAT = "error:select_floor_failed:invalid_format_for_select_floor._expected_select_floor@floor#elevator_id"  # Example
ERR_MISSING_ELEVATOR_ID_OPEN = (
    "error:open_door_failed:missing_elevator_id_for_open_door"  # Example
)
ERR_INVALID_ARG_VALUE = "error:call_up@abc_failed:invalid_argument_value_invalid_literal_for_int()_with_base_10_\\'abc\\'"  # Example, very specific


class TestCommandParsingAndExecutionOutput:
    """
    Test cases for command parsing and the resulting ZMQ string output from ElevatorAPI._parse_and_execute.
    These tests will check the string response, not intermediate command objects.
    """

    def setup_method(self):
        """Set up test fixtures"""
        # ElevatorAPI requires a 'world' object. We'll use a mock.
        # It also takes ZMQ connection params, which are used by ZmqClientThread.
        # For testing _parse_and_execute in isolation, these might not be critical if ZmqClientThread
        # is not directly involved in the parsing logic itself, but they are needed for instantiation.
        self.mock_world = MockSimulator()
        self.api = ElevatorAPI(
            world=self.mock_world, zmq_ip="127.0.0.1", zmq_port="19999"
        )
        # If ZmqClientThread's auto-start is an issue for unit tests, consider a flag or mock.
        # For now, assume it's okay or doesn't interfere with _parse_and_execute's direct call.
        # We also need to stop the client thread after tests if it starts.
        self.api.zmq_client.running = (
            False  # Prevent thread from actually running its loop for these tests
        )
        self.api.zmq_client.stop()  # Ensure client is stopped

    def teardown_method(self):
        """Clean up after tests"""
        if self.api and self.api.zmq_client and self.api.zmq_client.is_alive():
            self.api.zmq_client.stop()
            self.api.zmq_client.join(timeout=1)

    def test_parse_call_up_command(self):
        """Test parsing call up command - successful call returns None or specific ack."""
        # Assuming _handle_call_elevator is mocked or its side effects are acceptable/controlled.
        # For this test, we focus on what _parse_and_execute returns.
        # Successful calls in the new API return None if no direct ZMQ ack is needed.
        self.mock_world.dispatcher.add_call = MagicMock()  # Mock the actual operation
        result = self.api._parse_and_execute("call_up@2")
        assert result is None  # Or expected ack string if spec changes
        self.mock_world.dispatcher.add_call.assert_called_once_with(2, "up")

    def test_parse_call_down_command(self):
        """Test parsing call down command"""
        self.mock_world.dispatcher.add_call = MagicMock()
        result = self.api._parse_and_execute("call_down@1")
        assert result is None
        self.mock_world.dispatcher.add_call.assert_called_once_with(1, "down")

    def test_parse_select_floor_command(self):
        """Test parsing select floor command"""
        self.mock_world.dispatcher.assign_task = MagicMock()
        result = self.api._parse_and_execute("select_floor@3#1")
        assert result is None
        self.mock_world.dispatcher.assign_task.assert_called_once_with(
            0, 3, None
        )  # elevator_id 1 -> index 0

    def test_parse_open_door_command(self):
        """Test parsing open door command - expects 'door_opened#id'"""
        # Mock the elevator's open_door method
        mock_elevator = MagicMock()
        self.api.world.elevators = [
            mock_elevator,
            MagicMock(),
        ]  # Assuming elevator_id 1 is index 0
        result = self.api._parse_and_execute("open_door#1")
        assert result == MSG_DOOR_OPENED_1
        mock_elevator.open_door.assert_called_once()

    def test_parse_close_door_command(self):
        """Test parsing close door command - expects 'door_closed#id'"""
        mock_elevator = MagicMock()
        self.api.world.elevators = [
            MagicMock(),
            mock_elevator,
        ]  # Assuming elevator_id 2 is index 1
        result = self.api._parse_and_execute("close_door#2")
        assert result == MSG_DOOR_CLOSED_2
        mock_elevator.close_door.assert_called_once()

    def test_parse_reset_command(self):
        """Test parsing reset command - successful reset returns None or specific ack."""
        # Mock reset methods
        for elev in self.api.world.elevators:
            elev.reset = MagicMock()
        self.api.world.dispatcher.reset = MagicMock()
        result = self.api._parse_and_execute("reset")
        assert result is None  # Or expected ack string
        for elev in self.api.world.elevators:
            elev.reset.assert_called_once()
        self.api.world.dispatcher.reset.assert_called_once()

    # --- Error Handling Tests ---
    # These tests will check the formatted error string returned by _parse_and_execute

    def test_parse_empty_command(self):
        """Test parsing empty command returns specific error string"""
        result = self.api._parse_and_execute("")
        # The exact error format depends on _format_failure_for_zmq
        # Example: "error:failed:unknown_operation_"
        assert "error:" in result
        assert (
            "unknown_operation" in result
        )  # Or a more specific slug for empty command

    def test_parse_unknown_command(self):
        """Test parsing unknown command returns specific error string"""
        result = self.api._parse_and_execute("unknown_command")
        # Example: "error:unknown_command_failed:unknown_operation_unknown_command"
        assert (
            "error:unknown_command_failed:unknown_operation_unknown_command" == result
        )

    def test_parse_invalid_call_format_missing_floor(self):
        """Test parsing invalid call command format (missing floor)"""
        result = self.api._parse_and_execute("call_up@")  # Missing floor
        # Example: "error:call_up_failed:missing_floor_for_call_command"
        assert result == ERR_INVALID_CALL_FORMAT

    def test_parse_invalid_select_floor_format_missing_id(self):
        """Test parsing invalid select floor format (missing elevator ID)"""
        result = self.api._parse_and_execute("select_floor@2")  # Missing #elevator_id
        # Example: "error:select_floor_failed:invalid_format_for_select_floor..."
        assert result == ERR_INVALID_SELECT_FLOOR_FORMAT

    def test_parse_open_door_missing_id(self):
        """Test parsing open_door without elevator ID"""
        result = self.api._parse_and_execute("open_door@")  # Missing ID
        assert result == ERR_MISSING_ELEVATOR_ID_OPEN

    def test_parse_invalid_floor_number_in_call(self):
        """Test parsing invalid floor number in call command"""
        result = self.api._parse_and_execute("call_up@abc")
        # Example: "error:call_up@abc_failed:invalid_argument_value_..."
        # This error message can be very specific to the exception.
        # A more generic check might be better if the exact exception message varies.
        assert (
            "error:call_up@abc_failed:invalid_argument_value_invalid_literal_for_int"
            in result
        )

    def test_parse_invalid_elevator_id_in_open(self):
        """Test parsing invalid elevator ID in open_door command"""
        result = self.api._parse_and_execute("open_door#abc")
        # Example: "error:open_door#abc_failed:invalid_argument_value_..."
        assert (
            "error:open_door#abc_failed:invalid_argument_value_invalid_literal_for_int"
            in result
        )

    def test_world_not_initialized(self):
        """Test command when world is not initialized"""
        self.api.world = None  # Simulate world not being initialized
        result = self.api._parse_and_execute("call_up@1")
        assert result == ERR_WORLD_NOT_INITIALIZED


if __name__ == "__main__":
    pytest.main([__file__])
