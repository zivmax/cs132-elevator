from typing import List, Optional, TYPE_CHECKING, Tuple
from .models import ElevatorState, DoorState, MoveDirection, Task
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
            self.add_target_task(best_elevator.id - 1, floor, "outside", direction)

    def add_target_task(
        self,
        elevator_idx: int,
        floor: int,
        origin: str = "outside",
        direction: str = None,
    ) -> None:
        elevator = self.world.elevators[elevator_idx]

        # If already at the floor and doors closed, open doors and send message
        if floor == elevator.current_floor and elevator.door_state == DoorState.CLOSED:
            direction_str = direction if origin == "outside" else ""
            self.api.send_floor_arrived_message(
                elevator.id, elevator.current_floor, direction_str or ""
            )
            elevator.open_door()
            return

        # Skip if already in queue or currently at this floor with doors open
        if any(t.floor == floor for t in elevator.task_queue) or (
            floor == elevator.current_floor and elevator.door_state != DoorState.CLOSED
        ):
            return

        # Add new task
        elevator.task_queue.append(
            Task(floor, origin, direction if origin == "outside" else None)
        )
        self._optimize_task_queue(elevator)

        # If door is open, close it to start moving
        if elevator.door_state == DoorState.OPEN:
            elevator.close_door()
        else:
            elevator.request_movement_if_needed()

    def _optimize_task_queue(self, elevator: "Elevator") -> None:
        if not elevator.task_queue or len(elevator.task_queue) <= 1:
            return
        current_direction = None
        if elevator.state == ElevatorState.MOVING_UP:
            current_direction = "up"
        elif elevator.state == ElevatorState.MOVING_DOWN:
            current_direction = "down"
        if current_direction == "up":
            above = [t for t in elevator.task_queue if t.floor > elevator.current_floor]
            below = [t for t in elevator.task_queue if t.floor < elevator.current_floor]
            elevator.task_queue = sorted(above, key=lambda t: t.floor) + sorted(
                below, key=lambda t: t.floor
            )
        elif current_direction == "down":
            above = [t for t in elevator.task_queue if t.floor > elevator.current_floor]
            below = [t for t in elevator.task_queue if t.floor < elevator.current_floor]
            elevator.task_queue = sorted(below, key=lambda t: -t.floor) + sorted(
                above, key=lambda t: t.floor
            )
        else:
            closest = min(
                elevator.task_queue, key=lambda t: abs(elevator.current_floor - t.floor)
            )
            if closest.floor > elevator.current_floor:
                above = [
                    t for t in elevator.task_queue if t.floor > elevator.current_floor
                ]
                below = [
                    t for t in elevator.task_queue if t.floor < elevator.current_floor
                ]
                elevator.task_queue = sorted(above, key=lambda t: t.floor) + sorted(
                    below, key=lambda t: t.floor
                )
            else:
                above = [
                    t for t in elevator.task_queue if t.floor > elevator.current_floor
                ]
                below = [
                    t for t in elevator.task_queue if t.floor < elevator.current_floor
                ]
                elevator.task_queue = sorted(below, key=lambda t: -t.floor) + sorted(
                    above, key=lambda t: t.floor
                )
