"""
Unit tests for the utility module.

This module tests utility functions including:
- Port availability checking and scanning
- Network socket operations
- Error handling for port operations
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
import socket
from unittest.mock import patch, MagicMock
from backend.utility import find_available_port


class TestFindAvailablePort:
    """Test the find_available_port function."""

    def test_find_available_port_success(self):
        """Test finding an available port successfully."""
        # Use a high port number that's likely to be available
        result = find_available_port("127.0.0.1", 50000, 50010)

        assert result is not None
        assert 50000 <= result <= 50010

    def test_find_available_port_in_range(self):
        """Test that returned port is within specified range."""
        result = find_available_port("127.0.0.1", 40000, 40005)

        if result is not None:  # If a port is found
            assert 40000 <= result <= 40005

    @patch("socket.socket")
    def test_find_available_port_first_port_available(self, mock_socket):
        """Test when the first port in range is available."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance
        mock_socket_instance.bind.return_value = (
            None  # No exception means port is available
        )

        result = find_available_port("127.0.0.1", 8000, 8010)

        assert result == 8000
        mock_socket_instance.bind.assert_called_once_with(("127.0.0.1", 8000))

    @patch("socket.socket")
    def test_find_available_port_second_port_available(self, mock_socket):
        """Test when the first port is busy but second is available."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance

        # First call raises OSError (port busy), second call succeeds
        mock_socket_instance.bind.side_effect = [OSError("Port busy"), None]

        result = find_available_port("127.0.0.1", 8000, 8010)

        assert result == 8001
        assert mock_socket_instance.bind.call_count == 2
        mock_socket_instance.bind.assert_any_call(("127.0.0.1", 8000))
        mock_socket_instance.bind.assert_any_call(("127.0.0.1", 8001))

    @patch("socket.socket")
    def test_find_available_port_no_ports_available(self, mock_socket):
        """Test when no ports are available in the range."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance
        mock_socket_instance.bind.side_effect = OSError("Port busy")

        result = find_available_port("127.0.0.1", 8000, 8002)

        assert result is None
        assert mock_socket_instance.bind.call_count == 3  # 8000, 8001, 8002

    @patch("socket.socket")
    def test_find_available_port_different_host(self, mock_socket):
        """Test finding port on different host."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance
        mock_socket_instance.bind.return_value = None

        result = find_available_port("0.0.0.0", 9000, 9000)

        assert result == 9000
        mock_socket_instance.bind.assert_called_once_with(("0.0.0.0", 9000))

    @patch("socket.socket")
    def test_find_available_port_single_port_range(self, mock_socket):
        """Test with a single port range (start_port == end_port)."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance
        mock_socket_instance.bind.return_value = None

        result = find_available_port("127.0.0.1", 7777, 7777)

        assert result == 7777
        mock_socket_instance.bind.assert_called_once_with(("127.0.0.1", 7777))

    @patch("socket.socket")
    def test_find_available_port_single_port_busy(self, mock_socket):
        """Test with a single port that's busy."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance
        mock_socket_instance.bind.side_effect = OSError("Port busy")

        result = find_available_port("127.0.0.1", 7777, 7777)

        assert result is None
        mock_socket_instance.bind.assert_called_once_with(("127.0.0.1", 7777))

    def test_find_available_port_default_end_port(self):
        """Test using default end port (65535)."""
        # This test uses a high start port to avoid conflicts and limit the range
        result = find_available_port("127.0.0.1", 65530)

        # Should find a port or return None if all high ports are busy
        if result is not None:
            assert 65530 <= result <= 65535

    @patch("socket.socket")
    def test_find_available_port_socket_creation_error(self, mock_socket):
        """Test handling of socket creation errors."""
        mock_socket.side_effect = socket.error("Socket creation failed")

        # This should raise an exception since we can't create a socket
        with pytest.raises(socket.error):
            find_available_port("127.0.0.1", 8000, 8000)

    @patch("socket.socket")
    def test_find_available_port_context_manager(self, mock_socket):
        """Test that socket context manager is used correctly."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance
        mock_socket_instance.bind.return_value = None

        result = find_available_port("127.0.0.1", 8000, 8000)

        # Verify socket was created with correct parameters
        mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)

        # Verify context manager was used
        mock_socket.return_value.__enter__.assert_called_once()
        mock_socket.return_value.__exit__.assert_called_once()

    def test_find_available_port_edge_cases(self):
        """Test edge cases for port range parameters."""
        # Test with minimum valid port
        result = find_available_port("127.0.0.1", 1, 1)
        # May succeed or fail depending on system permissions
        assert result is None or result == 1

        # Test with maximum valid port
        result = find_available_port("127.0.0.1", 65535, 65535)
        assert result is None or result == 65535

    @patch("socket.socket")
    def test_find_available_port_specific_error_types(self, mock_socket):
        """Test handling of specific socket error types."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance

        # Test different OSError scenarios
        error_scenarios = [
            OSError(98, "Address already in use"),  # Linux
            OSError(10048, "Address already in use"),  # Windows
            OSError(48, "Address already in use"),  # macOS
        ]

        for error in error_scenarios:
            mock_socket_instance.bind.side_effect = error
            result = find_available_port("127.0.0.1", 8000, 8000)
            assert result is None

    def test_find_available_port_real_socket_integration(self):
        """Integration test with real socket operations."""
        # This test creates an actual socket to occupy a port, then tests finding the next available one
        test_host = "127.0.0.1"
        test_start_port = 45000

        # Create a socket and bind it to occupy a port
        occupied_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            occupied_socket.bind((test_host, test_start_port))

            # Now try to find an available port starting from the same port
            result = find_available_port(
                test_host, test_start_port, test_start_port + 5
            )

            # Should find the next available port (not the occupied one)
            assert result is not None
            assert result != test_start_port
            assert test_start_port < result <= test_start_port + 5

        except OSError:
            # If the test port is already in use, skip this test
            pytest.skip(f"Test port {test_start_port} is already in use")
        finally:
            occupied_socket.close()

    def test_find_available_port_performance(self):
        """Test performance of port scanning."""
        import time

        start_time = time.time()
        result = find_available_port("127.0.0.1", 50000, 50100)
        end_time = time.time()

        # Should complete within reasonable time (adjust threshold as needed)
        assert end_time - start_time < 5.0  # 5 seconds max

        if result is not None:
            assert 50000 <= result <= 50100

    @patch("socket.socket")
    def test_error_recovery_scenarios(self, mock_socket):
        """Test various error recovery scenarios."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance

        # Scenario: First few ports fail, then one succeeds
        mock_socket_instance.bind.side_effect = [
            OSError("Port 1 busy"),
            OSError("Port 2 busy"),
            OSError("Port 3 busy"),
            None,  # Port 4 available
        ]

        result = find_available_port("127.0.0.1", 9000, 9010)
        assert result == 9003  # Fourth port tried (9000 + 3)
        assert mock_socket_instance.bind.call_count == 4
