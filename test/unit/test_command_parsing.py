"""
Unit tests for command parsing functionality in the elevator system.

This module tests the parsing of ZMQ messages into command objects,
including validation of different command formats and error handling.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from backend.api.zmq import (
    BaseCommand,
    CallCommand,
    SelectFloorCommand,
    OpenDoorCommand,
    CloseDoorCommand,
    ResetCommand,
    ParseError,
    ZmqCoordinator,
)


class TestCommandDataClasses:
    """Test cases for command data classes"""

    def test_base_command_creation(self):
        """Test BaseCommand can be instantiated"""
        cmd = BaseCommand()
        assert isinstance(cmd, BaseCommand)

    def test_call_command_creation(self):
        """Test CallCommand creation with valid data"""
        cmd = CallCommand(floor=2, direction="up", original_message="call_up@2")
        assert cmd.floor == 2
        assert cmd.direction == "up"
        assert cmd.original_message == "call_up@2"
        assert isinstance(cmd, BaseCommand)

    def test_select_floor_command_creation(self):
        """Test SelectFloorCommand creation with valid data"""
        cmd = SelectFloorCommand(
            floor=3, elevator_id=1, original_message="select_floor@3#1"
        )
        assert cmd.floor == 3
        assert cmd.elevator_id == 1
        assert cmd.original_message == "select_floor@3#1"
        assert isinstance(cmd, BaseCommand)

    def test_open_door_command_creation(self):
        """Test OpenDoorCommand creation with valid data"""
        cmd = OpenDoorCommand(elevator_id=1, original_message="open_door#1")
        assert cmd.elevator_id == 1
        assert cmd.original_message == "open_door#1"
        assert isinstance(cmd, BaseCommand)

    def test_close_door_command_creation(self):
        """Test CloseDoorCommand creation with valid data"""
        cmd = CloseDoorCommand(elevator_id=2, original_message="close_door#2")
        assert cmd.elevator_id == 2
        assert cmd.original_message == "close_door#2"
        assert isinstance(cmd, BaseCommand)

    def test_reset_command_creation(self):
        """Test ResetCommand creation"""
        cmd = ResetCommand(original_message="reset")
        assert cmd.original_message == "reset"
        assert isinstance(cmd, BaseCommand)

    def test_parse_error_creation(self):
        """Test ParseError creation with error details"""
        error = ParseError(
            error_type="invalid_format",
            original_message="bad_command",
            detail="Invalid command format",
        )
        assert error.error_type == "invalid_format"
        assert error.original_message == "bad_command"
        assert error.detail == "Invalid command format"


class TestCommandParsing:
    """Test cases for command parsing logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.coordinator = ZmqCoordinator("test_identity", 19999)

    def test_parse_call_up_command(self):
        """Test parsing call up command"""
        result = self.coordinator._parse_message_to_command("call_up@2")
        assert isinstance(result, CallCommand)
        assert result.floor == 2
        assert result.direction == "up"

    def test_parse_call_down_command(self):
        """Test parsing call down command"""
        result = self.coordinator._parse_message_to_command("call_down@1")
        assert isinstance(result, CallCommand)
        assert result.floor == 1
        assert result.direction == "down"

    def test_parse_call_basement_floor(self):
        """Test parsing call to basement floor"""
        result = self.coordinator._parse_message_to_command("call_up@-1")
        assert isinstance(result, CallCommand)
        assert result.floor == -1
        assert result.direction == "up"

    def test_parse_select_floor_command(self):
        """Test parsing select floor command"""
        result = self.coordinator._parse_message_to_command("select_floor@3#1")
        assert isinstance(result, SelectFloorCommand)
        assert result.floor == 3
        assert result.elevator_id == 1

    def test_parse_select_basement_floor(self):
        """Test parsing select basement floor command"""
        result = self.coordinator._parse_message_to_command("select_floor@-1#2")
        assert isinstance(result, SelectFloorCommand)
        assert result.floor == -1
        assert result.elevator_id == 2

    def test_parse_open_door_command(self):
        """Test parsing open door command"""
        result = self.coordinator._parse_message_to_command("open_door#1")
        assert isinstance(result, OpenDoorCommand)
        assert result.elevator_id == 1

    def test_parse_close_door_command(self):
        """Test parsing close door command"""
        result = self.coordinator._parse_message_to_command("close_door#2")
        assert isinstance(result, CloseDoorCommand)
        assert result.elevator_id == 2

    def test_parse_reset_command(self):
        """Test parsing reset command"""
        result = self.coordinator._parse_message_to_command("reset")
        assert isinstance(result, ResetCommand)


class TestCommandParsingErrors:
    """Test cases for command parsing error handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.coordinator = ZmqCoordinator("test_identity", 19999)

    def test_parse_empty_command(self):
        """Test parsing empty command returns error"""
        result = self.coordinator._parse_message_to_command("")
        assert isinstance(result, ParseError)
        assert result.error_type == "unknown_message_format"

    def test_parse_unknown_command(self):
        """Test parsing unknown command returns error"""
        result = self.coordinator._parse_message_to_command("unknown_command")
        assert isinstance(result, ParseError)
        assert result.error_type == "unknown_message_format"

    def test_parse_invalid_call_format(self):
        """Test parsing invalid call command format"""
        result = self.coordinator._parse_message_to_command("call_up")
        assert isinstance(result, ParseError)
        assert result.error_type == "invalid_call_format"

    def test_parse_invalid_select_floor_format(self):
        """Test parsing invalid select floor format"""
        result = self.coordinator._parse_message_to_command(
            "select_floor@2"
        )  # Missing elevator ID
        assert isinstance(result, ParseError)
        assert result.error_type == "invalid_select_floor_format"

    def test_parse_invalid_door_format(self):
        """Test parsing invalid door command format"""
        result = self.coordinator._parse_message_to_command(
            "open_door"
        )  # Missing elevator ID
        assert isinstance(result, ParseError)
        assert result.error_type == "unknown_message_format"

    def test_parse_invalid_floor_number(self):
        """Test parsing invalid floor number"""
        result = self.coordinator._parse_message_to_command("call_up@abc")
        assert isinstance(result, ParseError)
        assert result.error_type == "invalid_parameter"

    def test_parse_invalid_elevator_id(self):
        """Test parsing invalid elevator ID"""
        result = self.coordinator._parse_message_to_command("open_door#abc")
        assert isinstance(result, ParseError)
        assert result.error_type == "invalid_parameter"


if __name__ == "__main__":
    # Allow running the test file directly
    pytest.main([__file__])
