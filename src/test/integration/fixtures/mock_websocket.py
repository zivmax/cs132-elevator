"""
Mock WebSocket bridge for integration tests.
Simulates frontend WebSocket communication without actual WebSocket connections.
"""

from unittest.mock import Mock
import json
import time


class MockWebSocket:
    """Mock WebSocket connection for testing."""
    
    def __init__(self):
        self.connected = False
        self.messages_sent = []
        self.messages_received = []
        self.send_mock = Mock(return_value=True)
        self.close_mock = Mock()
        
    def send(self, message: str):
        """Simulate sending a message through WebSocket."""
        if not self.connected:
            raise ConnectionError("WebSocket not connected")
        
        self.messages_sent.append({
            'message': message,
            'timestamp': time.time()
        })
        return self.send_mock(message)
    
    def close(self):
        """Simulate closing WebSocket connection."""
        self.connected = False
        self.close_mock()
    
    def connect(self):
        """Simulate connecting WebSocket."""
        self.connected = True
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.connected


class MockWebSocketBridge:
    """Mock WebSocket bridge for testing frontend communication."""
    
    def __init__(self):
        self.websockets = []
        self.broadcast_mock = Mock()
        self.send_message_mock = Mock(return_value=True)
        self.messages_broadcast = []
        self.connected_clients = 0
        
    def add_websocket(self, websocket: MockWebSocket):
        """Add a mock WebSocket connection."""
        self.websockets.append(websocket)
        self.connected_clients += 1
        
    def remove_websocket(self, websocket: MockWebSocket):
        """Remove a mock WebSocket connection."""
        if websocket in self.websockets:
            self.websockets.remove(websocket)
            self.connected_clients -= 1
    
    def send_message(self, message: str) -> bool:
        """Send message to all connected WebSockets."""
        try:
            message_data = {
                'message': message,
                'timestamp': time.time(),
                'clients_reached': 0
            }
            
            for websocket in self.websockets:
                if websocket.is_connected():
                    websocket.send(message)
                    message_data['clients_reached'] += 1
            
            self.messages_broadcast.append(message_data)
            return self.send_message_mock(message)
        except Exception:
            return False
    
    def broadcast_state(self, state_data: dict) -> bool:
        """Broadcast state update to all connected clients."""
        state_message = json.dumps(state_data)
        return self.send_message(state_message)
    
    def is_connected(self) -> bool:
        """Check if any WebSocket clients are connected."""
        return any(ws.is_connected() for ws in self.websockets)
    
    def get_connected_count(self) -> int:
        """Get number of connected clients."""
        return sum(1 for ws in self.websockets if ws.is_connected())
    
    def simulate_disconnect_all(self):
        """Simulate all clients disconnecting."""
        for websocket in self.websockets:
            websocket.close()
        self.connected_clients = 0
    
    def simulate_reconnect_all(self):
        """Simulate all clients reconnecting."""
        for websocket in self.websockets:
            websocket.connect()
        self.connected_clients = len(self.websockets)
    
    def clear_message_history(self):
        """Clear broadcast message history."""
        self.messages_broadcast.clear()
        for websocket in self.websockets:
            websocket.messages_sent.clear()
    
    def get_all_messages(self) -> list:
        """Get all messages sent through this bridge."""
        return self.messages_broadcast
    
    def simulate_client_message(self, message: str, client_index: int = 0):
        """Simulate receiving a message from a client."""
        if 0 <= client_index < len(self.websockets):
            websocket = self.websockets[client_index]
            websocket.messages_received.append({
                'message': message,
                'timestamp': time.time()
            })
            return True
        return False
