import pytest
import socket
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to sys.path to allow for `from src...` imports
# The test file is in test/units/, so ../.. goes to the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# Assuming find_available_port is accessible for testing.
# If it's in src.backend.server, you might need to adjust the import path
# For example: from src.backend.server import find_available_port
# Or, if you've added it to a common utils module, import from there.
# For this example, let's assume it's in a module that can be imported like this:
from backend.utility import find_available_port
# If it's also in src.frontend.webview, we only need to test one implementation
# as they should be identical.

def test_start_port_is_available():
    """Test that if the start_port is available, it is returned."""
    host = "localhost"
    start_port = 60000
    # Ensure the port is actually available for the test
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, start_port))
            # If bind succeeds, port is in use by this test, so we expect find_available_port
            # to find the *next* one if we didn't control the mock.
            # However, for this specific test, we want to mock `s.bind` to *not* raise OSError
            # for the start_port.
            pass # Port was free, now bound by us.
    except OSError:
        # This shouldn't happen if 60000 is typically free. If it does, pick another port.
        pytest.skip(f"Port {start_port} was already in use before test setup.")

    # We want to test the scenario where find_available_port *finds* start_port
    # So, we mock socket.socket().bind() to succeed for start_port
    mock_socket_instance = MagicMock()
    mock_socket_instance.bind.return_value = None # Simulate successful bind

    with patch('socket.socket') as mock_socket_constructor:
        mock_socket_constructor.return_value.__enter__.return_value = mock_socket_instance
        found_port = find_available_port(host, start_port, start_port + 5)
        assert found_port == start_port
        mock_socket_instance.bind.assert_called_once_with((host, start_port))

def test_start_port_occupied_next_available():
    """Test that if start_port is occupied, the next available port is returned."""
    host = "localhost"
    occupied_port = 60010
    expected_port = 60011

    def mock_bind_side_effect(address):
        if address[1] == occupied_port:
            raise OSError("Port already in use")
        return None # Success for other ports

    mock_socket_instance = MagicMock()
    mock_socket_instance.bind.side_effect = mock_bind_side_effect

    with patch('socket.socket') as mock_socket_constructor:
        mock_socket_constructor.return_value.__enter__.return_value = mock_socket_instance
        found_port = find_available_port(host, occupied_port, expected_port + 5)
        assert found_port == expected_port
        assert mock_socket_instance.bind.call_count == 2
        mock_socket_instance.bind.assert_any_call((host, occupied_port))
        mock_socket_instance.bind.assert_any_call((host, expected_port))

def test_all_ports_in_range_occupied():
    """Test that None is returned if all ports in the specified range are occupied."""
    host = "localhost"
    start_port = 60020
    end_port = 60022 # A small range

    mock_socket_instance = MagicMock()
    mock_socket_instance.bind.side_effect = OSError("Port already in use")

    with patch('socket.socket') as mock_socket_constructor:
        mock_socket_constructor.return_value.__enter__.return_value = mock_socket_instance
        found_port = find_available_port(host, start_port, end_port)
        assert found_port is None
        # bind should be called for each port in the range
        assert mock_socket_instance.bind.call_count == (end_port - start_port + 1)
        for port_to_check in range(start_port, end_port + 1):
            mock_socket_instance.bind.assert_any_call((host, port_to_check))

def test_port_found_at_end_of_range():
    """Test finding a port that is the last one in the specified end_port range."""
    host = "localhost"
    start_port = 60030
    end_port = 60032
    available_port_at_end = 60032

    def mock_bind_side_effect(address):
        if address[1] < available_port_at_end:
            raise OSError("Port already in use")
        return None # Success for available_port_at_end

    mock_socket_instance = MagicMock()
    mock_socket_instance.bind.side_effect = mock_bind_side_effect

    with patch('socket.socket') as mock_socket_constructor:
        mock_socket_constructor.return_value.__enter__.return_value = mock_socket_instance
        found_port = find_available_port(host, start_port, end_port)
        assert found_port == available_port_at_end
        assert mock_socket_instance.bind.call_count == (available_port_at_end - start_port + 1)

def test_no_port_available_up_to_end_port():
    """Test that None is returned if no port is available up to a specified end_port."""
    host = "localhost"
    start_port = 60040
    end_port = 60041 # Small range, all will be mocked as occupied

    mock_socket_instance = MagicMock()
    mock_socket_instance.bind.side_effect = OSError("Port already in use")

    with patch('socket.socket') as mock_socket_constructor:
        mock_socket_constructor.return_value.__enter__.return_value = mock_socket_instance
        found_port = find_available_port(host, start_port, end_port)
        assert found_port is None
        assert mock_socket_instance.bind.call_count == (end_port - start_port + 1)

def test_end_port_less_than_start_port():
    """Test behavior when end_port is less than start_port (should find nothing)."""
    host = "localhost"
    start_port = 60050
    end_port = 60049 # end_port < start_port

    # No need to mock socket.bind as the loop in find_available_port should not even run.
    found_port = find_available_port(host, start_port, end_port)
    assert found_port is None

def test_default_end_port_usage():
    """Test that find_available_port works with default end_port, finding a port soon."""
    host = "localhost"
    start_port = 60060
    # Mock bind to succeed on the second try
    def mock_bind_side_effect(address):
        if address[1] == start_port:
            raise OSError("Port already in use")
        return None

    mock_socket_instance = MagicMock()
    mock_socket_instance.bind.side_effect = mock_bind_side_effect

    with patch('socket.socket') as mock_socket_constructor:
        mock_socket_constructor.return_value.__enter__.return_value = mock_socket_instance
        # Not specifying end_port, so it uses the default 65535
        found_port = find_available_port(host, start_port)
        assert found_port == start_port + 1
        assert mock_socket_instance.bind.call_count == 2
