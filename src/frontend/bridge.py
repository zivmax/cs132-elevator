import json
from typing import TYPE_CHECKING, Optional

from backend.api.core import ElevatorAPI
from backend.api.server import WebSocketServer
from backend.models import MoveDirection


class WebSocketBridge:
    """Bridge class for communication between Python backend and JavaScript frontend using WebSocket"""

    def __init__(
        self,
        backend_api: ElevatorAPI,
        host: str = "127.0.0.1",
        port: int = 18675,
    ):
        # The ElevatorAPI instance now manages ZMQ communication internally.
        # WebSocketBridge primarily interacts with ElevatorAPI for data and commands.
        self.backend_api = backend_api
        self.server = WebSocketServer(
            host=host, port=port, message_handler=self._handle_message
        )

        # Start the WebSocket server
        self.server.start()
        print("WebSocketBridge: Initialized and WebSocket server started.")

    def _handle_message(self, message: str) -> str:
        """Parse JSON message, call API function, and return result as JSON string"""
        try:
            data = json.loads(message)
            func_name = data.get("function")
            params = data.get("params", {})
            if not func_name:
                return json.dumps(
                    {"status": "error", "message": "Missing 'function' in request"}
                )

            func = getattr(self.backend_api, func_name, None)

            if not func or not callable(func):
                print(
                    f"WebSocketBridge: No such API function or function not callable: {func_name}"
                )
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"No such API function or function not callable: {func_name}",
                    }
                )

            # Call the function. Ensure it's designed to be called this way.
            result = func(
                params
            )  # Assuming API methods like ui_call_elevator take params dict

            if not isinstance(result, str):
                return json.dumps(result)  # If API returns dict, convert to JSON string
            return result  # If API already returns JSON string

        except Exception as e:
            print(f"WebSocketBridge: Error handling message: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def sync_backend(self):
        """Update the UI based on backend state by merging elevator state sync and backend fetching."""
        # Get elevator states from the API
        elevator_states = self.backend_api.fetch_states()

        # Update the UI for each elevator
        for elevator_state in elevator_states:
            direction = elevator_state["direction"]
            if isinstance(direction, MoveDirection):
                direction_value = direction.value
            else:
                direction_value = None

            data = {
                "id": elevator_state["elevator_id"],
                "floor": elevator_state["floor"],
                "state": elevator_state["state"],
                "doorState": elevator_state["door_state"],
                "direction": direction_value,
                "targetFloors": elevator_state["target_floors"],
                "targetFloorsOrigin": elevator_state.get("target_floors_origin", {}),
            }
            if self.server.is_running:
                self.server.send_elevator_states(data)

    def stop(self):
        """Stop the WebSocket server"""
        self.server.stop()
