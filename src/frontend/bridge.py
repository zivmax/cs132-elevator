from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal
import json
from backend.api import ElevatorAPI
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from backend.world import World


class WebBridge(QObject):
    """Bridge class for communication between Python backend and JavaScript frontend"""

    # Signals to send data to the web frontend
    elevatorUpdated = pyqtSignal(str)
    floorCalled = pyqtSignal(str)

    def __init__(self, parent=None, world: "World" = None):
        super().__init__(parent)
        self._callbacks = {}
        self.api = ElevatorAPI(world)

        # Register callbacks
        self.register_callback("callElevator", self.api.handle_call_elevator)
        self.register_callback("selectFloor", self.api.handle_select_floor)
        self.register_callback("openDoor", self.api.handle_open_door)
        self.register_callback("closeDoor", self.api.handle_close_door)

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

    def _sync_elevator_state(
        self,
        elevator_id: int,
        floor: int,
        state: str,
        door_state: str,
        direction: str,
        target_floors: list,
        target_floors_origin: dict = None,
    ):
        """Send elevator state update to frontend"""
        data = {
            "id": elevator_id,
            "floor": floor,
            "state": state,
            "doorState": door_state,
            "direction": direction,
            "targetFloors": target_floors,
            "target_floors_origin": target_floors_origin or {},
        }
        self.elevatorUpdated.emit(json.dumps(data))

    def sync_backend(self):
        """Update the UI based on backend state"""
        # Get elevator states from the API
        elevator_states = self.api.fetch_elevator_states()

        # Update the UI for each elevator
        for elevator_state in elevator_states:
            self._sync_elevator_state(
                elevator_id=elevator_state["elevator_id"],
                floor=elevator_state["floor"],
                state=elevator_state["state"],
                door_state=elevator_state["door_state"],
                direction=elevator_state["direction"],
                target_floors=elevator_state["target_floors"],
                target_floors_origin=elevator_state.get("target_floors_origin", {}),
            )

    def notify_floor_called(self, floor: int, direction: str):
        """Send floor called notification to frontend"""
        data = {"floor": floor, "direction": direction}
        self.floorCalled.emit(json.dumps(data))
