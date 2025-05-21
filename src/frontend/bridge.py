import json
from typing import Dict, Any, TYPE_CHECKING

from backend.api import ElevatorAPI
from backend.server import WebSocketServer

if TYPE_CHECKING:
    from backend.world import World

class WebSocketBridge:
    """Bridge class for communication between Python backend and JavaScript frontend using WebSocket"""

    def __init__(self, world: "World" = None, host: str = '127.0.0.1', port: int = 8765):
        self.api = ElevatorAPI(world)
        self.server = WebSocketServer(host=host, port=port, world=world)
        
        # Register callbacks
        self.server.register_callback("callElevator", self.api.handle_call_elevator)
        self.server.register_callback("selectFloor", self.api.handle_select_floor)
        self.server.register_callback("openDoor", self.api.handle_open_door)
        self.server.register_callback("closeDoor", self.api.handle_close_door)
        
        # Start the WebSocket server
        self.server.start()

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
        self.server.send_elevator_updated(data)

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
        self.server.send_floor_called(floor, direction)
        
    def stop(self):
        """Stop the WebSocket server"""
        self.server.stop()
