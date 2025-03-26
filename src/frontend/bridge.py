from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal
import json


class WebBridge(QObject):
    """Bridge class for communication between Python backend and JavaScript frontend"""

    # Signals to send data to the web frontend
    elevatorUpdated = pyqtSignal(str)
    floorCalled = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._callbacks = {}

    @pyqtSlot(str, result=str)
    def sendToBackend(self, message: str) -> str:
        """Receive messages from JavaScript"""
        try:
            data = json.loads(message)
            action = data.get("action")

            # Log the message for debugging
            print(f"Received from frontend: {message}")

            # Call the registered callback if it exists
            if action in self._callbacks:
                return self._callbacks[action](data)
            return json.dumps(
                {"status": "error", "message": f"No handler for action: {action}"}
            )
        except Exception as e:
            print(f"Error processing message from frontend: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def register_callback(self, action: str, callback):
        """Register a callback function for a specific action"""
        self._callbacks[action] = callback

    def sync_elevator_state(
        self,
        elevator_id: int,
        floor: int,
        state: str,
        door_state: str,
        direction: str,
        target_floors: list,
    ):
        """Send elevator state update to frontend"""
        data = {
            "id": elevator_id,
            "floor": floor,
            "state": state,
            "doorState": door_state,
            "direction": direction,
            "targetFloors": target_floors,
        }
        self.elevatorUpdated.emit(json.dumps(data))

    def notify_floor_called(self, floor: int, direction: str):
        """Send floor called notification to frontend"""
        data = {"floor": floor, "direction": direction}
        self.floorCalled.emit(json.dumps(data))
