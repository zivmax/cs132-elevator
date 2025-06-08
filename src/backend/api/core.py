import json
from typing import Dict, Any, Optional, List

from backend.models import (
    MoveDirection,
)  # Assuming this is the correct import for MoveDirection
from ..models import (
    validate_floor,
    validate_elevator_id,
    MIN_FLOOR,
    MAX_FLOOR,
)
from .zmq import (
    ZmqClientThread,
)  # Changed from ZmqCoordinator and other specific command/error types


# TYPE_CHECKING import for Simulator can remain if used elsewhere, or be removed if not.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.simulator import Simulator


class ElevatorAPI:
    """API for interacting with the elevator backend"""

    def __init__(
        self,
        world: Optional["Simulator"],
        zmq_ip: str = "127.0.0.1",
        zmq_port: str = "19982",
    ):
        self.world = world
        # Initialize ZmqClientThread directly, passing self for message processing
        self.zmq_client = ZmqClientThread(
            serverIp=zmq_ip,
            port=zmq_port,
            api_instance=self,  # Pass the API instance itself
        )
        # Start the ZMQ client connection and listening thread
        self.zmq_client.connect_and_start()
        print(
            "ElevatorAPI: Initialized with ZmqClientThread for automatic message processing."
        )

    def set_world(
        self, world: "Simulator"
    ) -> None:  # This method might still be useful if world is set later
        """Update the world reference"""
        self.world = world

    # _parse_and_execute will be called by ZmqClientThread when a message is received.
    def _parse_and_execute(self, command: str) -> Optional[str]:
        """
        Parses a command string (from ZMQ) and executes it.
        Returns a response string to be sent back to the ZMQ server, or None.

        ZMQ Command Format Examples:
        - call_up@1 / call_down@1
        - select_floor@3#1 (floor 3, elevator 1)
        - open_door#1
        - close_door#1
        - reset
        """
        print(f"API: Received command: {command}")

        if not self.world:
            print(
                f"API Error: World not initialized. Cannot process command: {command}"
            )
            # Format error for ZMQ as per spec (e.g., error:world_not_initialized)
            return "error:world_not_initialized"

        parts = command.strip().split("@")
        operation_full = parts[0]
        args_str = parts[1] if len(parts) > 1 else ""

        try:
            if operation_full.startswith("call_"):
                direction = operation_full.split("_")[1]  # up or down
                if not args_str:  # Ensure floor number is provided
                    return self._format_failure_for_zmq(
                        command, "Missing floor for call command"
                    )
                floor = int(args_str)
                response_dict = self._handle_call_elevator(floor, direction)
                if response_dict.get("status") == "error":
                    return self._format_failure_for_zmq(
                        command, response_dict.get("message", "call_failed")
                    )
                return None  # Or a specific success ack if defined by a new spec

            elif operation_full == "select_floor":
                if (
                    not args_str or "#" not in args_str
                ):  # Ensure args are present and correct format
                    return self._format_failure_for_zmq(
                        command,
                        "Invalid format for select_floor. Expected: select_floor@FLOOR#ELEVATOR_ID",
                    )
                floor_str, elevator_id_str = args_str.split("#")
                floor = int(floor_str)
                elevator_id = int(elevator_id_str)
                response_dict = self._handle_select_floor(floor, elevator_id)
                # Similar to call, select_floor success might not need a direct ZMQ response unless an error occurs.
                if response_dict.get("status") == "error":
                    return self._format_failure_for_zmq(
                        command, response_dict.get("message", "select_floor_failed")
                    )
                return None  # Or a specific success ack

            elif operation_full == "open_door":
                if not args_str:  # Ensure elevator ID is provided
                    return self._format_failure_for_zmq(
                        command, "Missing elevator ID for open_door"
                    )
                elevator_id = int(
                    args_str.replace("#", "")
                )  # Allow open_door#1 or open_door@1
                response_dict = self._handle_open_door(elevator_id)
                if response_dict.get("status") == "success":
                    return f"door_opened#{elevator_id}"
                else:
                    return self._format_failure_for_zmq(
                        command, response_dict.get("message", "open_door_failed")
                    )

            elif operation_full == "close_door":
                if not args_str:  # Ensure elevator ID is provided
                    return self._format_failure_for_zmq(
                        command, "Missing elevator ID for close_door"
                    )
                elevator_id = int(
                    args_str.replace("#", "")
                )  # Allow close_door#1 or close_door@1
                response_dict = self._handle_close_door(elevator_id)
                if response_dict.get("status") == "success":
                    return f"door_closed#{elevator_id}"
                else:
                    return self._format_failure_for_zmq(
                        command, response_dict.get("message", "close_door_failed")
                    )

            elif operation_full == "reset":
                response_dict = self._handle_reset()
                # Reset success might not need a direct ZMQ response unless an error occurs.
                if response_dict.get("status") == "error":
                    return self._format_failure_for_zmq(
                        command, response_dict.get("message", "reset_failed")
                    )
                # The spec implies reset is acknowledged by the system resetting, not a specific message.
                # However, if a success message is desired: return "system_reset_acknowledged" or similar.
                return None

            else:
                return self._format_failure_for_zmq(
                    command, f"Unknown operation: {operation_full}"
                )

        except ValueError as ve:
            # Error during parsing arguments (e.g., int conversion)
            return self._format_failure_for_zmq(
                command, f"Invalid argument value: {ve}"
            )
        except Exception as e:
            # Catch-all for other unexpected errors during command processing
            print(f"API Error executing command '{command}': {e}")
            return self._format_failure_for_zmq(command, "internal_error")

    def _format_failure_for_zmq(self, operation_string: str, reason: str) -> str:
        """Formats a failure message for ZMQ.
        Example: error:call_up@1_failed:invalid_floor
        The exact format might need to align with a specific spec if provided.
        A common pattern is error:original_command:reason_slug
        """
        reason_slug = reason.lower().replace(" ", "_").replace("'", "")
        action_type = operation_string.split("@")[0].split("#")[
            0
        ]  # get base action like call_up, select_floor, open_door

        formatted_error = f"error:{action_type}_failed:{reason_slug}"
        print(
            f"API: Operation '{operation_string}' failed. Sending ZMQ error: {formatted_error}"
        )
        return formatted_error

    def stop(self):
        """Stops the ZMQ client thread gracefully."""
        print("Elevator: Stopping ZMQ client...")
        self.zmq_client.stop()
        self.zmq_client.join()  # Wait for the thread to finish
        print("Elevator: ZMQ client stopped.")

    # Internal handlers, previously part of Dispatcher or direct calls from old API methods
    # Modified to return Dict instead of JSON string
    def _handle_call_elevator(self, floor: int, direction: str) -> Dict[str, Any]:
        """Internal handler for elevator calls from a floor."""
        if not self.world or not self.world.dispatcher:
            return {
                "status": "error",
                "message": "World or Dispatcher not initialized",
            }  # Validate floor bounds
        if not validate_floor(floor):
            return {
                "status": "error",
                "message": f"Invalid floor: {floor}. Must be between {MIN_FLOOR} and {MAX_FLOOR}",
            }

        print(f"API: Calling elevator at floor {floor}, direction {direction}")
        # Assuming assign_elevator doesn't return a value indicating immediate success/failure of the call itself,
        # but rather queues the request. So, we assume success at this stage if no exceptions.
        try:
            self.world.dispatcher.add_call(floor, direction)
            return {
                "status": "success",
                "action": "call_elevator",
                "message": f"Elevator called to floor {floor} {direction}",
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to call elevator: {str(e)}"}

    def _handle_select_floor(self, floor: int, elevator_id: int) -> Dict[str, Any]:
        """Internal handler for floor selections from inside an elevator."""
        if not self.world or not self.world.dispatcher:
            return {"status": "error", "message": "World or Dispatcher not initialized"}
        # Validate floor bounds
        if not validate_floor(floor):
            return {
                "status": "error",
                "message": f"Invalid floor: {floor}. Must be between {MIN_FLOOR} and {MAX_FLOOR}",
            }  # Validate elevator ID
        if not validate_elevator_id(elevator_id):
            return {
                "status": "error",
                "message": f"Invalid elevator ID: {elevator_id}. Must be between 1 and 2",
            }

        print(f"API: Elevator {elevator_id} selecting floor {floor}")
        try:
            # Dispatcher's add_target_task expects 0-based elevator_idx
            # For inside calls, call_id should be None
            self.world.dispatcher.assign_task(elevator_id - 1, floor, None)
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

    def _handle_open_door(self, elevator_id: int) -> Dict[str, Any]:
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

    def _handle_close_door(self, elevator_id: int) -> Dict[str, Any]:
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

    def _handle_reset(self) -> Dict[str, Any]:
        """Internal handler for resetting the simulation."""
        if not self.world:
            return {"status": "error", "message": "World not initialized"}
        print("API: Resetting simulation")
        try:
            for elevator in self.world.elevators:
                elevator.reset()
            if self.world.dispatcher:
                self.world.dispatcher.reset()  # Assuming dispatcher has a reset method
            return {
                "status": "success",
                "action": "reset",
                "message": "Simulation reset successfully",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to reset simulation: {str(e)}",
            }

    # Methods to send messages/updates to the ZMQ client (test server)
    # These are now called by the ZmqClientThread directly if _parse_and_execute returns a message,
    # or can be called by other parts of the system (e.g. Simulator for floor_arrived)
    def _send_message_to_client(self, message: str) -> None:
        """Sends a generic raw message to the ZMQ client via ZmqClientThread's send_msg method."""
        if self.zmq_client:
            self.zmq_client.send_msg(message)
            print(f"API: Sent ZMQ message: {message}")
        else:
            print(
                f"API: ZmqClientThread not available. Cannot send ZMQ message: {message}"
            )

    def send_floor_arrived_message(
        self, elevator_id: int, floor: int, direction: Optional[MoveDirection]
    ) -> None:
        """Sends a floor arrival message in the format: {direction_prefix}floor_arrived@{floor_number}#{elevator_id}
        e.g., up_floor_arrived@1#1, floor_arrived@2#2 (no direction if IDLE/target reached)
        """
        prefix = ""
        if direction == MoveDirection.UP:
            prefix = "up_"
        elif direction == MoveDirection.DOWN:
            prefix = "down_"
        # If direction is None or IDLE, no prefix is used, as per spec for arrival at target.

        message = f"{prefix}floor_arrived@{floor}#{elevator_id}"
        self._send_message_to_client(message)

    def send_door_opened_message(self, elevator_id: int) -> None:
        """Sends a door opened message."""
        message = f"door_opened#{elevator_id}"
        self._send_message_to_client(message)

    def send_door_closed_message(self, elevator_id: int) -> None:
        """Sends a door closed message."""
        message = f"door_closed#{elevator_id}"
        self._send_message_to_client(message)

    def ui_call_elevator(self, data: Dict[str, Any]) -> str:
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
            result_dict = self._handle_call_elevator(int(floor), direction)
            return json.dumps(result_dict)  # Still return JSON for this path
        except Exception as e:
            print(f"Error in call_elevator: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def ui_select_floor(self, data: Dict[str, Any]) -> str:
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
            result_dict = self._handle_select_floor(int(floor), int(elevator_id))
            return json.dumps(result_dict)  # Still return JSON for this path
        except Exception as e:
            print(f"Error in select_floor: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def ui_open_door(self, data: Dict[str, Any]) -> str:
        """Handle open door request from frontend"""
        try:
            elevator_id = data.get("elevatorId")
            if elevator_id is None:
                return json.dumps({"status": "error", "message": "Missing elevatorId"})

            print(f"API: Frontend open door: elevator_id={elevator_id}")
            result_dict = self._handle_open_door(int(elevator_id))
            return json.dumps(result_dict)  # Still return JSON for this path
        except Exception as e:
            print(f"Error in open_door: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def ui_close_door(self, data: Dict[str, Any]) -> str:
        """Handle close door request from frontend"""
        try:
            elevator_id = data.get("elevatorId")
            if elevator_id is None:
                return json.dumps({"status": "error", "message": "Missing elevatorId"})

            print(f"API: Frontend close door: elevator_id={elevator_id}")
            result_dict = self._handle_close_door(int(elevator_id))
            return json.dumps(result_dict)  # Still return JSON for this path
        except Exception as e:
            print(f"Error in close_door: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def fetch_states(self) -> List[Dict[str, Any]]:
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
                task.floor: "outside" if task.is_outside_call else "inside"
                for task in elevator.task_queue
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
