import json
import time  # Added import for time.sleep
from typing import TYPE_CHECKING, Dict, Any, Optional, List

# Import ZmqClientThread directly
from .net_client import ZmqClientThread

if TYPE_CHECKING:
    from backend.world import World
    from backend.elevator import Elevator


class ElevatorAPI:
    """API for interacting with the elevator backend"""

    # Modified __init__ to instantiate ZmqClientThread
    def __init__(self, world: Optional["World"] = None):
        self.world = world
        # Instantiate ZmqClientThread here
        self.client: ZmqClientThread = ZmqClientThread(identity="Team17")
        self._last_checked_timestamp: int = -1  # For tracking client messages
        print("ElevatorAPI: ZmqClientThread initialized.")
        time.sleep(1)  # Give time for the client to connect
        print("ElevatorAPI: ZmqClientThread should be connected.")

    def set_world(self, world: "World"):
        """Update the world reference"""
        self.world = world

    # Removed set_client method as client is instantiated internally

    def update(self):
        """Checks for new messages from the ZMQ client and adds them to the world's queue."""
        if not self.client or not self.world:
            # print(\"API Update: Client or World not set, skipping message check.\") # Optional debug
            return

        if self.client.messageTimeStamp > self._last_checked_timestamp:
            self._last_checked_timestamp = self.client.messageTimeStamp
            message = self.client.receivedMessage
            if message:
                # Add message to world's queue
                print(f"API Update: New message from ZMQ client: {message}")
                self.world.add_msg(message)

    # Methods to receive and parse messages from frontend/clients
    def parse_and_handle_message(self, message_str: str) -> Optional[str]:
        """Parses a message string and calls the appropriate handler."""
        print(f"API received message: {message_str}")
        if not self.world:
            return json.dumps({"status": "error", "message": "World not initialized"})

        try:
            if message_str.startswith("call_"):  # e.g. call_up@1, call_down@3
                parts = message_str.split("@")
                direction_floor = parts[0].split("_")[1]
                floor = int(parts[1])
                return self.handle_call_elevator_internal(floor, direction_floor)
            elif message_str.startswith("select_floor@"):  # e.g. select_floor@5#1
                parts = message_str.split("@")[1].split("#")
                floor = int(parts[0])
                elevator_id = int(parts[1])
                return self.handle_select_floor_internal(floor, elevator_id)
            elif message_str.startswith("open_door#"):  # e.g. open_door#1
                elevator_id = int(message_str.split("#")[1])
                return self.handle_open_door_internal(elevator_id)
            elif message_str.startswith("close_door#"):  # e.g. close_door#1
                elevator_id = int(message_str.split("#")[1])
                return self.handle_close_door_internal(elevator_id)
            elif message_str == "reset":
                return self.handle_reset_internal()
            else:
                print(f"Unknown message format: {message_str}")
                return json.dumps(
                    {"status": "error", "message": f"Unknown message format: {message_str}"}
                )
        except Exception as e:
            print(f"Error parsing message '{message_str}': {e}")
            return json.dumps({"status": "error", "message": f"Error parsing message: {str(e)}"})

    # Internal handlers, previously part of Dispatcher or direct calls from old API methods
    def handle_call_elevator_internal(self, floor: int, direction: str) -> str:
        """Internal handler for elevator calls from a floor."""
        if not self.world or not self.world.dispatcher:
            return json.dumps({"status": "error", "message": "World or Dispatcher not initialized"})
        print(f"API: Calling elevator to floor {floor}, direction {direction}")
        self.world.dispatcher.assign_elevator(floor, direction)
        return json.dumps({"status": "success", "action": "call_elevator"})

    def handle_select_floor_internal(self, floor: int, elevator_id: int) -> str:
        """Internal handler for floor selections from inside an elevator."""
        if not self.world or not self.world.dispatcher:
            return json.dumps({"status": "error", "message": "World or Dispatcher not initialized"})
        print(f"API: Elevator {elevator_id} selecting floor {floor}")
        # Dispatcher's _add_target_floor expects 0-based elevator_idx
        self.world.dispatcher.add_target_floor(elevator_id - 1, floor, "inside")
        return json.dumps({"status": "success", "action": "select_floor"})

    def handle_open_door_internal(self, elevator_id: int) -> str:
        """Internal handler to open a specific elevator's door."""
        if not self.world:
            return json.dumps({"status": "error", "message": "World not initialized"})
        if 0 <= elevator_id - 1 < len(self.world.elevators):
            print(f"API: Opening door for elevator {elevator_id}")
            self.world.elevators[elevator_id - 1].open_door()
            return json.dumps({"status": "success", "action": "open_door"})
        return json.dumps({"status": "error", "message": f"Elevator {elevator_id} not found"})

    def handle_close_door_internal(self, elevator_id: int) -> str:
        """Internal handler to close a specific elevator's door."""
        if not self.world:
            return json.dumps({"status": "error", "message": "World not initialized"})
        if 0 <= elevator_id - 1 < len(self.world.elevators):
            print(f"API: Closing door for elevator {elevator_id}")
            self.world.elevators[elevator_id - 1].close_door()
            return json.dumps({"status": "success", "action": "close_door"})
        return json.dumps({"status": "error", "message": f"Elevator {elevator_id} not found"})

    def handle_reset_internal(self) -> str:
        """Internal handler for resetting the simulation."""
        if not self.world:
            return json.dumps({"status": "error", "message": "World not initialized"})
        print("API: Resetting simulation")
        for elevator in self.world.elevators:
            elevator.reset()
        # Potentially reset dispatcher or other world states if necessary
        return json.dumps({"status": "success", "action": "reset"})

    # Methods to send messages/updates to the frontend/client
    def send_message_to_client(self, message: str):
        """Sends a generic message to the ZMQ client."""
        # Use the direct client reference
        if self.client:
            print(f"API sending to client: {message}")
            self.client.sendMsg(message)
        else:
            # This case should ideally not happen if client is initialized in __init__
            print(f"API cannot send to client (client not initialized): {message}")

    def send_floor_arrived_message(self, elevator_id: int, floor: int, direction_str: str):
        """Sends a floor arrival message."""
        # direction_str could be "up_", "down_", or ""
        message = f"{direction_str}floor_arrived@{floor}#{elevator_id}"
        self.send_message_to_client(message)

    def send_door_opened_message(self, elevator_id: int):
        """Sends a door opened message."""
        message = f"door_opened#{elevator_id}"
        self.send_message_to_client(message)

    def send_door_closed_message(self, elevator_id: int):
        """Sends a door closed message."""
        message = f"door_closed#{elevator_id}"
        self.send_message_to_client(message)

    # Existing methods that are called by the frontend (e.g., via webserver)
    # These will now use the internal handlers or directly call world/dispatcher methods.
    def handle_call_elevator(self, data: Dict[str, Any]) -> str:
        """Handle call elevator request from frontend"""
        try:
            floor = data.get("floor")
            direction = data.get("direction")  # "up" or "down"

            if floor is None or direction is None:
                return json.dumps({"status": "error", "message": "Missing floor or direction"})

            print(f"API: Frontend call elevator: floor={floor}, direction={direction}")
            # Use the internal handler which now calls dispatcher directly
            return self.handle_call_elevator_internal(int(floor), direction)
        except Exception as e:
            print(f"Error in handle_call_elevator: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def handle_select_floor(self, data: Dict[str, Any]) -> str:
        """Handle floor selection request from frontend"""
        try:
            floor = data.get("floor")
            elevator_id = data.get("elevatorId")

            if floor is None or elevator_id is None:
                return json.dumps({"status": "error", "message": "Missing floor or elevatorId"})

            print(f"API: Frontend select floor: floor={floor}, elevator_id={elevator_id}")
            # Use the internal handler
            return self.handle_select_floor_internal(int(floor), int(elevator_id))
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
            return self.handle_open_door_internal(int(elevator_id))
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
            return self.handle_close_door_internal(int(elevator_id))
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
                direction_str = direction_val.name if hasattr(direction_val, "name") else str(direction_val)

            elevator_state = {
                "elevator_id": elevator.id,
                "floor": elevator.current_floor,
                "state": state_str,
                "door_state": door_state_str,
                "direction": direction_str,  # Use the processed direction string
                "target_floors": elevator.target_floors,
                "target_floors_origin": elevator.target_floors_origin,
            }

            elevator_states.append(elevator_state)
        # print(f"API: Fetched states: {elevator_states}") # Optional: for debugging
        return elevator_states
