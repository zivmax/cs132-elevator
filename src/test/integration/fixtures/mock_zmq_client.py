"""
Mock ZMQ client for integration tests.
Simulates external ZMQ client behavior without actual network operations.
"""

from unittest.mock import Mock


class MockZmqClient:
    """Mock ZMQ client for simulating external client interactions."""

    def __init__(self, host="localhost", port=5555):
        self.host = host
        self.port = port
        self.connected = False
        self.send_message_mock = Mock(return_value=True)  # Mock for send_message
        self.receive_message_mock = Mock(return_value=None)  # Mock for receive_message
        self.start_mock = Mock()
        self.stop_mock = Mock()
        self.messages_sent = []
        self.messages_received = []

    def start(self):
        """Simulate starting the ZMQ client."""
        self.start_mock()
        self.connected = True

    def stop(self):
        """Simulate stopping the ZMQ client."""
        self.stop_mock()
        self.connected = False

    def send_message(self, message: str) -> bool:
        """Simulate sending a message via ZMQ."""
        if not self.connected:
            raise ConnectionError("ZMQ client not connected")

        self.messages_sent.append(message)
        return self.send_message_mock(message)

    def receive_message(self, timeout: int = 1000) -> str | None:
        """Simulate receiving a message via ZMQ."""
        if not self.connected:
            raise ConnectionError("ZMQ client not connected")

        response = self.receive_message_mock(timeout)
        if response:
            self.messages_received.append(response)
        return response

    def is_connected(self) -> bool:
        """Check if the ZMQ client is connected."""
        return self.connected

    def clear_messages(self):
        """Clear sent and received message logs."""
        self.messages_sent.clear()
        self.messages_received.clear()

    def set_receive_response(self, response: str | None):
        """Set the next response for receive_message."""
        self.receive_message_mock.return_value = response

    def get_sent_messages(self) -> list[str]:
        """Get all messages sent by this mock client."""
        return self.messages_sent
