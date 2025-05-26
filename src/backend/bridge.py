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
        # Pass the message handler directly to the WebSocketServer constructor
        self.server = WebSocketServer(host=host, port=port, message_handler=self._handle_message)
        
        # Start the WebSocket server
        self.server.start()

    def _handle_message(self, message: str) -> str:
        """Parse JSON message, call API function, and return result as JSON string"""
        try:
            data = json.loads(message)
            func_name = data.get("function")
            params = data.get("params", {})
            if not func_name:
                return json.dumps({"status": "error", "message": "Missing 'function' in request"})
            
            # Get the function from ElevatorAPI by its string name
            func = getattr(self.api, func_name, None)
            
            if not func or not callable(func):
                return json.dumps({"status": "error", "message": f"No such API function: {func_name}"})
            
            # Call the function with params
            # The API functions are expected to handle the params dictionary directly
            result = func(params) 
            
            # Ensure the result is a JSON string before returning
            if not isinstance(result, str):
                 # If api returned a dict, dump it to json string
                return json.dumps(result) 
            return result
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

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
        if self.server.is_running:
            self.server.send_elevator_states(data)

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
        
    def stop(self):
        """Stop the WebSocket server"""
        self.server.stop()
