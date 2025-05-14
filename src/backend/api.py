import json
from typing import TYPE_CHECKING, Dict, Any, Optional, List

if TYPE_CHECKING:
    from backend.world import World


class ElevatorAPI:
    """API for interacting with the elevator backend"""

    def __init__(self, world: Optional["World"] = None):
        self.world = world

    def set_world(self, world: "World"):
        """Update the world reference"""
        self.world = world

    def handle_call_elevator(self, data: Dict[str, Any]) -> str:
        """Handle call elevator request from frontend"""
        try:
            floor = data.get("floor")
            direction = data.get("direction")

            print(f"Call elevator: floor={floor}, direction={direction}")

            if self.world:
                # Construct the message format expected by the backend
                message = f"call_{direction}@{floor}"
                self.world.add_msg(message)  # Send to world instead of client
                return json.dumps({"status": "success"})
            return json.dumps({"status": "error", "message": "World not initialized"})
        except Exception as e:
            print(f"Error in handle_call_elevator: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def handle_select_floor(self, data: Dict[str, Any]) -> str:
        """Handle floor selection request from frontend"""
        try:
            floor = data.get("floor")
            elevator_id = data.get("elevatorId")

            print(f"Select floor: floor={floor}, elevator_id={elevator_id}")

            if self.world:
                message = f"select_floor@{floor}#{elevator_id}"
                self.world.add_msg(message)  # Send to world instead of client
                return json.dumps({"status": "success"})
            return json.dumps({"status": "error", "message": "World not initialized"})
        except Exception as e:
            print(f"Error in handle_select_floor: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def handle_open_door(self, data: Dict[str, Any]) -> str:
        """Handle open door request from frontend"""
        try:
            elevator_id = data.get("elevatorId")

            print(f"Open door: elevator_id={elevator_id}")

            if self.world:
                message = f"open_door#{elevator_id}"
                self.world.add_msg(message)  # Send to world instead of client
                return json.dumps({"status": "success"})
            return json.dumps({"status": "error", "message": "World not initialized"})
        except Exception as e:
            print(f"Error in handle_open_door: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def handle_close_door(self, data: Dict[str, Any]) -> str:
        """Handle close door request from frontend"""
        try:
            elevator_id = data.get("elevatorId")

            print(f"Close door: elevator_id={elevator_id}")

            if self.world:
                message = f"close_door#{elevator_id}"
                self.world.add_msg(message)  # Send to world instead of client
                return json.dumps({"status": "success"})
            return json.dumps({"status": "error", "message": "World not initialized"})
        except Exception as e:
            print(f"Error in handle_close_door: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def fetch_elevator_states(self) -> List[Dict[str, Any]]:
        """Get updated elevator states from the backend"""
        elevator_states = []

        if not self.world:
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
            )  # Create a dictionary with elevator state information
            elevator_state = {
                "elevator_id": elevator.id,
                "floor": elevator.current_floor,
                "state": state_str,
                "door_state": door_state_str,
                "direction": elevator.direction if elevator.direction else "none",
                "target_floors": elevator.target_floors,
                "target_floors_origin": elevator.target_floors_origin,
            }

            elevator_states.append(elevator_state)

        return elevator_states
