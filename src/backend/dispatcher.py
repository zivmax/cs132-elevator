from typing import List, Optional, TYPE_CHECKING, Tuple
from .models import ElevatorState, DoorState
from .elevator import Elevator


if TYPE_CHECKING:
    from .world import World


class Dispatcher:
    def __init__(self, world: "World") -> None:
        self.world: "World" = world

    def update(self) -> None:
        # Check for new messages from the world
        while self.world.has_msg():
            message, _ = self.world.get_next_msg()
            if message:
                self.handle_request(message)

    def handle_request(self, request: str) -> None:
        if request.startswith("open_door"):
            elevator_id: int = int(request.split("#")[1])
            self.world.elevators[elevator_id - 1].open_door()

        elif request.startswith("close_door"):
            elevator_id: int = int(request.split("#")[1])
            self.world.elevators[elevator_id - 1].close_door()

        elif request.startswith("call_up"):
            floor: int = int(request.split("@")[1])
            self._assign_elevator(floor, "up")

        elif request.startswith("call_down"):
            floor: int = int(request.split("@")[1])
            self._assign_elevator(floor, "down")

        elif request.startswith("select_floor"):
            parts: List[str] = request.split("@")[1].split("#")
            floor: int = int(parts[0])
            elevator_id: int = int(parts[1])
            self._add_target_floor(elevator_id - 1, floor)

        elif request == "reset":
            for elevator in self.world.elevators:
                elevator.reset()

    def _assign_elevator(self, floor: int, direction: str) -> None:
        # Find the elevator that can service the request with minimal estimated time
        best_elevator: Optional["Elevator"] = None
        min_time: float = float("inf")

        for elevator in self.world.elevators:
            est_time: float = elevator.calculate_estimated_time(floor, direction)
            if est_time < min_time:
                min_time = est_time
                best_elevator = elevator

        if best_elevator:
            self._add_target_floor(best_elevator.id - 1, floor)

    def _add_target_floor(self, elevator_idx: int, floor: int) -> None:
        """Add target floor to elevator and optimize the sequence"""
        elevator = self.world.elevators[elevator_idx]

        # If elevator is already at this floor and door is closed, open door
        if floor == elevator.current_floor and elevator.door_state == DoorState.CLOSED:
            # Send floor arrival notification first
            direction_str: str = ""
            self.world.send_msg(
                f"{direction_str}floor_arrived@{elevator.current_floor}#{elevator.id}"
            )
            # Then open door
            elevator.open_door()
            return

        # Skip if already in target list or currently at this floor
        if floor in elevator.target_floors or (
            floor == elevator.current_floor and elevator.door_state != DoorState.CLOSED
        ):
            return

        # Add floor to target list
        elevator.target_floors.append(floor)

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
