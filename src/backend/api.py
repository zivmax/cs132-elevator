import json
from typing import TYPE_CHECKING, Dict, Any, Optional, List, Union  # Added Union

from .net_client import (
    ZmqCoordinator,
    BaseCommand,
    CallCommand,
    SelectFloorCommand,
    OpenDoorCommand,
    CloseDoorCommand,
    ResetCommand,
    ParseError,
)  # Import new command/error types


# ZMQ client now provided by World; no direct instantiation needed
if TYPE_CHECKING:
    from backend.world import World


class ElevatorAPI:
    """API for interacting with the elevator backend"""

    def __init__(self, world: Optional["World"], zmq_coordinator: "ZmqCoordinator"):
        self.world = world
        self.zmq_coordinator = zmq_coordinator  # Changed from zmq_manager
        print("ElevatorAPI: Initialized with ZmqCoordinator.")

    def set_world(
        self, world: "World"
    ) -> None:  # This method might still be useful if world is set later
        """Update the world reference"""
        self.world = world

    # Removed set_client method

    # Removed update(self) method as ZMQ message polling is now handled by World via ZmqManager

    # Methods to receive and parse messages from frontend/clients (WebSocket) or ZMQ (via World)
    def parse_and_handle_message(
        self, command_or_error: Union[BaseCommand, ParseError]
    ) -> None:
        """Handles a parsed command object or a ParseError from ZmqCoordinator.
        Passes resulting data or error information to ZmqCoordinator for formatting and sending.
        """
        print(f"API received command/error object: {command_or_error}")

        if not self.world:
            # Prepare error data for ZmqCoordinator to format and send
            error_info = {"type": "world_not_initialized_error"}
            print(f"API Error: World not initialized.")
            self.zmq_coordinator.send_formatted_message_to_server(error_info)
            return

        response_data_from_handler: Optional[Dict[str, Any]] = None
        command_context_str: str = ""
        parsed_elevator_id_for_response: Optional[int] = None

        if isinstance(command_or_error, ParseError):
            # Pass ParseError details to ZmqCoordinator for formatting
            error_info = {
                "type": "parse_error",
                "error_type": command_or_error.error_type,
                "detail": command_or_error.detail,
            }
            print(
                f"API received ParseError: type='{command_or_error.error_type}', detail='{command_or_error.detail}'"
            )
            self.zmq_coordinator.send_formatted_message_to_server(
                error_info, command_context_str=command_or_error.original_message
            )
            return

        command_context_str = command_or_error.original_message

        try:
            if isinstance(command_or_error, CallCommand):
                response_data_from_handler = self._handle_call_elevator_internal(
                    command_or_error.floor, command_or_error.direction
                )
            elif isinstance(command_or_error, SelectFloorCommand):
                response_data_from_handler = self._handle_select_floor_internal(
                    command_or_error.floor, command_or_error.elevator_id
                )
            elif isinstance(command_or_error, OpenDoorCommand):
                parsed_elevator_id_for_response = command_or_error.elevator_id
                response_data_from_handler = self._handle_open_door_internal(
                    command_or_error.elevator_id
                )
            elif isinstance(command_or_error, CloseDoorCommand):
                parsed_elevator_id_for_response = command_or_error.elevator_id
                response_data_from_handler = self._handle_close_door_internal(
                    command_or_error.elevator_id
                )
            elif isinstance(command_or_error, ResetCommand):
                response_data_from_handler = self._handle_reset_internal()
            else:
                error_info = {
                    "type": "unknown_command_type_error",
                    "detail": command_context_str,
                }
                print(f"API Error: Unknown command type for '{command_context_str}'")
                self.zmq_coordinator.send_formatted_message_to_server(
                    error_info, command_context_str=command_context_str
                )
                return

        except Exception as e:  # Catch errors from internal handlers
            error_info = {
                "type": "handler_processing_error",
                "error_type": "handler_exception",  # Generic slug for this type of error
                "detail": f"{command_context_str}:{str(e)}",
            }
            print(
                f"API Error during handler execution for '{command_context_str}': {str(e)}"
            )
            self.zmq_coordinator.send_formatted_message_to_server(
                error_info, command_context_str=command_context_str
            )
            return

        # Pass response from internal handlers to ZmqCoordinator for formatting and sending
        if response_data_from_handler:
            self.zmq_coordinator.send_formatted_message_to_server(
                response_data_from_handler,
                command_context_str=command_context_str,
                parsed_elevator_id_for_response=parsed_elevator_id_for_response,
            )
        else:
            # This case should ideally be covered by handlers always returning a dict,
            # or specific error handling above.
            error_info = {
                "type": "internal_processing_error",
                "detail": command_context_str,
            }
            print(
                f"API Warning: No response data from handler for command '{command_context_str}'"
            )
            self.zmq_coordinator.send_formatted_message_to_server(
                error_info, command_context_str=command_context_str
            )

    # Internal handlers, previously part of Dispatcher or direct calls from old API methods
    # Modified to return Dict instead of JSON string
    def _handle_call_elevator_internal(
        self, floor: int, direction: str
    ) -> Dict[str, Any]:
        """Internal handler for elevator calls from a floor."""
        if not self.world or not self.world.dispatcher:
            return {"status": "error", "message": "World or Dispatcher not initialized"}
        print(f"API: Calling elevator to floor {floor}, direction {direction}")
        # Assuming assign_elevator doesn't return a value indicating immediate success/failure of the call itself,
        # but rather queues the request. So, we assume success at this stage if no exceptions.
        try:
            self.world.dispatcher.assign_elevator(floor, direction)
            return {
                "status": "success",
                "action": "call_elevator",
                "message": f"Elevator called to floor {floor} {direction}",
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to call elevator: {str(e)}"}

    def _handle_select_floor_internal(
        self, floor: int, elevator_id: int
    ) -> Dict[str, Any]:
        """Internal handler for floor selections from inside an elevator."""
        if not self.world or not self.world.dispatcher:
            return {"status": "error", "message": "World or Dispatcher not initialized"}
        print(f"API: Elevator {elevator_id} selecting floor {floor}")
        try:
            # Dispatcher's add_target_task expects 0-based elevator_idx
            self.world.dispatcher.add_target_task(elevator_id - 1, floor, "inside")
            return {
                "status": "success",
                "action": "select_floor",
                "message": f"Elevator {elevator_id} selected floor {floor}",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to select floor for elevator {elevator_id}: {str(e)}",
            }

    def _handle_open_door_internal(self, elevator_id: int) -> Dict[str, Any]:
        """Internal handler to open a specific elevator's door."""
        if not self.world:
            return {"status": "error", "message": "World not initialized"}
        if 0 <= elevator_id - 1 < len(self.world.elevators):
            print(f"API: Opening door for elevator {elevator_id}")
            try:
                self.world.elevators[
                    elevator_id - 1
                ].open_door()  # Assume this might raise an error or return status
                return {
                    "status": "success",
                    "action": "open_door",
                    "message": f"Door opening for elevator {elevator_id}",
                }
            except (
                Exception
            ) as e:  # Replace with specific exceptions if `open_door` can raise them
                return {
                    "status": "error",
                    "message": f"Failed to open door for elevator {elevator_id}: {str(e)}",
                }
        return {"status": "error", "message": f"Elevator {elevator_id} not found"}

    def _handle_close_door_internal(self, elevator_id: int) -> Dict[str, Any]:
        """Internal handler to close a specific elevator's door."""
        if not self.world:
            return {"status": "error", "message": "World not initialized"}
        if 0 <= elevator_id - 1 < len(self.world.elevators):
            print(f"API: Closing door for elevator {elevator_id}")
            try:
                self.world.elevators[
                    elevator_id - 1
                ].close_door()  # Assume this might raise an error or return status
                return {
                    "status": "success",
                    "action": "close_door",
                    "message": f"Door closing for elevator {elevator_id}",
                }
            except (
                Exception
            ) as e:  # Replace with specific exceptions if `close_door` can raise them
                return {
                    "status": "error",
                    "message": f"Failed to close door for elevator {elevator_id}: {str(e)}",
                }
        return {"status": "error", "message": f"Elevator {elevator_id} not found"}

    def _handle_reset_internal(self) -> Dict[str, Any]:
        """Internal handler for resetting the simulation."""
        if not self.world:
            return {"status": "error", "message": "World not initialized"}
        print("API: Resetting simulation")
        try:
            for elevator in self.world.elevators:
                elevator.reset()
            # Potentially reset dispatcher or other world states if necessary
            # self.world.dispatcher.reset() # If dispatcher has a reset method
            return {
                "status": "success",
                "action": "reset",
                "message": "Simulation reset successfully",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to reset simulation: {str(e)}",
            }  # Methods to send messages/updates to the ZMQ client (test server)

    def _send_message_to_client(self, message: str) -> None:
        """Sends a generic raw message to the ZMQ client via ZmqCoordinator.
        This is now primarily for messages not originating from parse_and_handle_message flow,
        like floor_arrived.
        """
        if self.zmq_coordinator:
            self.zmq_coordinator.send_message_to_server(
                message
            )  # Direct send, no formatting here
            print(f"API: Sent ZMQ message: {message}")
        else:
            print(
                f"API: ZmqCoordinator not available. Cannot send ZMQ message: {message}"
            )

    def send_floor_arrived_message(
        self, elevator_id: int, floor: int, direction_str: str
    ) -> None:
        """Sends a floor arrival message in the format: {direction_prefix}floor_arrived@{floor_number}#{elevator_id}
        e.g., up_floor_arrived@1#1, floor_arrived@2#2
        """
        prefix = f"{direction_str}_" if direction_str else ""

        # Correct floor representation for the message
        display_floor = -1 if floor == 0 else floor

        # Corrected message format to match the specification
        message = f"{prefix}floor_arrived@{display_floor}#{elevator_id}"
        self._send_message_to_client(message)

    def send_door_opened_message(self, elevator_id: int) -> None:
        """Sends a door opened message."""
        message = f"door_opened#{elevator_id}"
        self._send_message_to_client(message)

    def send_door_closed_message(self, elevator_id: int) -> None:
        """Sends a door closed message."""
        message = f"door_closed#{elevator_id}"
        self._send_message_to_client(message)

    # Existing methods that are called by the frontend (e.g., via webserver)
    # These will now use the internal handlers or directly call world/dispatcher methods.
    # Their return type might change if they are expected to return the raw dict now,
    # or they can still return JSON if the webserver part expects JSON.
    # For now, let's assume they still need to return JSON for the webserver.

    def handle_call_elevator(self, data: Dict[str, Any]) -> str:
        """Handle call elevator request from frontend"""
        try:
            floor = data.get("floor")
            direction = data.get("direction")  # "up" or "down"

            if floor is None or direction is None:
                return json.dumps(
                    {"status": "error", "message": "Missing floor or direction"}
                )

            print(f"API: Frontend call elevator: floor={floor}, direction={direction}")
            # Use the internal handler which now calls dispatcher directly
            result_dict = self._handle_call_elevator_internal(int(floor), direction)
            return json.dumps(result_dict)  # Still return JSON for this path
        except Exception as e:
            print(f"Error in handle_call_elevator: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def handle_select_floor(self, data: Dict[str, Any]) -> str:
        """Handle floor selection request from frontend"""
        try:
            floor = data.get("floor")
            elevator_id = data.get("elevatorId")

            if floor is None or elevator_id is None:
                return json.dumps(
                    {"status": "error", "message": "Missing floor or elevatorId"}
                )

            print(
                f"API: Frontend select floor: floor={floor}, elevator_id={elevator_id}"
            )
            # Use the internal handler
            result_dict = self._handle_select_floor_internal(
                int(floor), int(elevator_id)
            )
            return json.dumps(result_dict)  # Still return JSON for this path
        except Exception as e:
            print(f"Error in handle_select_floor: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def handle_open_door(self, data: Dict[str, Any]) -> str:
        """Handle open door request from frontend"""
        try:
            elevator_id = data.get("elevatorId")
            if elevator_id is None:
                return json.dumps({"status": "error", "message": "Missing elevatorId"})

            print(f"API: Frontend open door: elevator_id={elevator_id}")
            result_dict = self._handle_open_door_internal(int(elevator_id))
            return json.dumps(result_dict)  # Still return JSON for this path
        except Exception as e:
            print(f"Error in handle_open_door: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def handle_close_door(self, data: Dict[str, Any]) -> str:
        """Handle close door request from frontend"""
        try:
            elevator_id = data.get("elevatorId")
            if elevator_id is None:
                return json.dumps({"status": "error", "message": "Missing elevatorId"})

            print(f"API: Frontend close door: elevator_id={elevator_id}")
            result_dict = self._handle_close_door_internal(int(elevator_id))
            return json.dumps(result_dict)  # Still return JSON for this path
        except Exception as e:
            print(f"Error in handle_close_door: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def fetch_elevator_states(self) -> List[Dict[str, Any]]:
        """Get updated elevator states from the backend"""
        elevator_states = []

        if not self.world:
            print("API: World not initialized, cannot fetch states.")  # Added log
            return elevator_states

        for elevator in self.world.elevators:
            # Convert enum values to strings for JSON
            state_str = (
                elevator.state.name
                if hasattr(elevator.state, "name")
                else str(elevator.state)
            )
            door_state_str = (
                elevator.door_state.name
                if hasattr(elevator.door_state, "name")
                else str(elevator.door_state)
            )
            # Ensure direction is a string, and handle None case
            direction_val = elevator.direction
            direction_str = "none"
            if direction_val:
                direction_str = (
                    direction_val.name
                    if hasattr(direction_val, "name")
                    else str(direction_val)
                )

            # Compose targetFloors and targetFloorsOrigin for frontend compatibility
            target_floors = [task.floor for task in elevator.task_queue]
            target_floors_origin = {
                task.floor: task.origin for task in elevator.task_queue
            }

            elevator_state = {
                "elevator_id": elevator.id,
                "floor": elevator.current_floor,
                "state": state_str,
                "door_state": door_state_str,
                "direction": direction_str,  # Use the processed direction string
                "target_floors": target_floors,
                "target_floors_origin": target_floors_origin,
            }

            elevator_states.append(elevator_state)
        return elevator_states
