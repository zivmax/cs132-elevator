import json
from typing import TYPE_CHECKING, Optional

from backend.api.server import WebSocketServer
from backend.models import MoveDirection

if TYPE_CHECKING:
    from backend.api.core import ElevatorAPI


class WebSocketBridge:
    """Bridge class for communication between Python backend and JavaScript frontend using WebSocket"""

    def __init__(
        self,
        backend_api: "ElevatorAPI",  # Changed type hint
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
        """Parse JSON message from WebSocket, call the appropriate API function,
        and return the JSON string response directly from the API function."""
        request_id = None  # Initialize request_id
        try:
            data = json.loads(message)
            func_name = data.get("function")
            params = data.get("params", {})
            request_id = data.get("requestId")  # Extract requestId

            if not func_name:
                error_state = self.backend_api.fetch_states()
                error_response = {
                    "success": False,
                    "message": "Missing function name",
                    "state": error_state,
                }
                if request_id:
                    error_response["requestId"] = request_id
                return json.dumps(error_response)

            func = getattr(self.backend_api, func_name, None)

            if not func or not callable(func):
                error_state = self.backend_api.fetch_states()
                error_response = {
                    "success": False,
                    "message": f"No such API function: {func_name}",
                    "state": error_state,
                }
                if request_id:
                    error_response["requestId"] = request_id
                return json.dumps(error_response)

            # Define the parameter map for your ElevatorAPI functions
            # Adjust this map according to your actual ElevatorAPI methods and their parameters
            func_param_map = {
                "ui_call_elevator": ["floor", "direction"],
                "ui_select_floor": ["floor", "elevatorId"],
                "ui_open_door": ["elevatorId"],
                "ui_close_door": ["elevatorId"],
                "fetch_states": [],  # Added for functions that take no params from the frontend
            }

            if func_name not in func_param_map:
                error_state = self.backend_api.fetch_states()
                error_response = {
                    "success": False,
                    "message": f"Function {func_name} not configured in bridge.",
                    "state": error_state,
                }
                if request_id:
                    error_response["requestId"] = request_id
                return json.dumps(error_response)

            arg_names = func_param_map[func_name]

            if (
                not arg_names
            ):  # For functions like fetch_states that expect no arguments from client
                json_response_from_api = func()
            else:
                # For UI functions that expect a 'params' dictionary
                # Validate that all expected parameter keys are present in the 'params' dict
                missing_params = [name for name in arg_names if name not in params]
                if missing_params:
                    error_state = self.backend_api.fetch_states()
                    error_response = {
                        "success": False,
                        "message": f"Missing parameter(s): {', '.join(missing_params)} for {func_name}",
                        "state": error_state,
                    }
                    if request_id:
                        error_response["requestId"] = request_id
                    return json.dumps(error_response)

                # Call the function with the 'params' dictionary itself
                json_response_from_api = func(params)

            if request_id:
                try:
                    # Parse the API's JSON response to add requestId
                    response_dict = json.loads(json_response_from_api)
                    response_dict["requestId"] = request_id
                    return json.dumps(response_dict)
                except json.JSONDecodeError:
                    return json_response_from_api
            else:
                return json_response_from_api

        except json.JSONDecodeError:
            try:
                error_state = self.backend_api.fetch_states()
            except Exception:  # Guard against failure in fetching state
                error_state = None
            error_response = {
                "success": False,
                "message": "Invalid JSON message",  # Changed "Invalid JSON message received" to "Invalid JSON message"
                "state": error_state,
            }
            if request_id:  # request_id might be null if JSON parsing failed early
                error_response["requestId"] = request_id
            return json.dumps(error_response)
        except Exception as e:
            print(f"WebSocketBridge: Error handling message '{message}': {e}")
            try:
                error_state = self.backend_api.fetch_states()
            except Exception:  # Guard against failure in fetching state
                error_state = None
            error_response = {
                "success": False,
                "message": f"Internal error: {str(e)}",
                "state": error_state,
            }
            if request_id:
                error_response["requestId"] = request_id
            return json.dumps(error_response)

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
