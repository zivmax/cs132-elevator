from typing import List, Optional, TYPE_CHECKING, Tuple
from .models import ElevatorState, DoorState, MoveDirection  # Added MoveDirection
from .elevator import Elevator


if TYPE_CHECKING:
    from .world import World
    from .api import ElevatorAPI  # Added API import


class Dispatcher:
    # Added api parameter to __init__
    def __init__(self, world: "World", api: "ElevatorAPI") -> None:
        self.world: "World" = world
        self.api: "ElevatorAPI" = api  # Store API instance

    def assign_elevator(self, floor: int, direction: str) -> None:
        best_elevator: Optional["Elevator"] = None
        min_time: float = float("inf")

        # Convert string direction to MoveDirection for calculate_estimated_time
        move_direction: Optional[MoveDirection] = None
        if direction.lower() == "up":
            move_direction = MoveDirection.UP
        elif direction.lower() == "down":
            move_direction = MoveDirection.DOWN

        for elevator in self.world.elevators:
            # Pass MoveDirection enum or None to calculate_estimated_time
            est_time: float = elevator.calculate_estimated_time(floor, move_direction)
            if est_time < min_time:
                min_time = est_time
                best_elevator = elevator

        if best_elevator:
            self.add_target_floor(best_elevator.id - 1, floor, "outside")

    def add_target_floor(
        self, elevator_idx: int, floor: int, origin: str = "outside"
    ) -> None:
        elevator = self.world.elevators[elevator_idx]

        if floor == elevator.current_floor and elevator.door_state == DoorState.CLOSED:
            direction_str: str = (
                ""  # No specific direction for arrival at current floor for door opening
            )
            # Use API to send message
            self.api.send_floor_arrived_message(
                elevator.id, elevator.current_floor, direction_str
            )
            elevator.open_door()
            return

        # Skip if already in target list or currently at this floor
        if floor in elevator.target_floors or (
            floor == elevator.current_floor and elevator.door_state != DoorState.CLOSED
        ):
            return

        # Add floor to target list
        elevator.target_floors.append(floor)

        # Store the origin of this floor request
        elevator.target_floors_origin[floor] = origin

        # Optimize the sequence for efficiency
        self._optimize_target_sequence(elevator)

        # If door is open, close it to start moving
        if elevator.door_state == DoorState.OPEN:
            elevator.close_door()
        else:
            # Request movement if possible
            elevator.request_movement_if_needed()

    def _optimize_target_sequence(self, elevator: "Elevator") -> None:
        """Optimize the sequence of target floors for efficiency"""
        if not elevator.target_floors or len(elevator.target_floors) <= 1:
            return

        # Determine current direction if elevator is moving
        current_direction = None
        if elevator.state == ElevatorState.MOVING_UP:
            current_direction = "up"
        elif elevator.state == ElevatorState.MOVING_DOWN:
            current_direction = "down"

        # If elevator has a direction, prioritize floors in that direction first
        if current_direction == "up":
            # Serve floors above current floor first, in ascending order
            above_floors = sorted(
                [f for f in elevator.target_floors if f > elevator.current_floor]
            )
            below_floors = sorted(
                [f for f in elevator.target_floors if f < elevator.current_floor]
            )
            elevator.target_floors = above_floors + below_floors
        elif current_direction == "down":
            # Serve floors below current floor first, in descending order
            above_floors = sorted(
                [f for f in elevator.target_floors if f > elevator.current_floor]
            )
            below_floors = sorted(
                [f for f in elevator.target_floors if f < elevator.current_floor],
                reverse=True,
            )
            elevator.target_floors = below_floors + above_floors
        else:
            # If idle, pick the closest direction
            closest_floor = min(
                elevator.target_floors, key=lambda f: abs(elevator.current_floor - f)
            )
            if closest_floor > elevator.current_floor:
                # Move up first
                above_floors = sorted(
                    [f for f in elevator.target_floors if f > elevator.current_floor]
                )
                below_floors = sorted(
                    [f for f in elevator.target_floors if f < elevator.current_floor],
                    reverse=True,
                )
                elevator.target_floors = above_floors + below_floors
            else:
                # Move down first
                above_floors = sorted(
                    [f for f in elevator.target_floors if f > elevator.current_floor]
                )
                below_floors = sorted(
                    [f for f in elevator.target_floors if f < elevator.current_floor],
                    reverse=True,
                )
                elevator.target_floors = below_floors + above_floors
