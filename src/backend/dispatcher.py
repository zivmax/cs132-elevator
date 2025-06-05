from typing import List, Optional, TYPE_CHECKING, Tuple, Dict, Any
from uuid import uuid4
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
        self.pending_calls: Dict[str, Dict[str, Any]] = (
            {}
        )  # {call_id: {"floor": int, "direction": MoveDirection}}

    def assign_elevator(self, floor: int, direction: str) -> None:
        try:
            move_direction = MoveDirection[direction.upper()]
            call_id = self.add_outside_call(floor, move_direction)
            self._process_pending_calls()
        except KeyError:
            # Invalid direction, handle gracefully
            call_id = self.add_outside_call(floor, None)
            self._process_pending_calls()

    def _process_pending_calls(self) -> None:
        for call_id, call_info in list(self.pending_calls.items()):
            floor = call_info["floor"]
            direction = call_info["direction"]
            best_elevator: Optional["Elevator"] = None
            min_time: float = float("inf")

            for elevator in self.world.elevators:
                # Pass MoveDirection enum or None to calculate_estimated_time
                est_time: float = elevator.calculate_estimated_time(floor, direction)
                if est_time < min_time:
                    min_time = est_time
                    best_elevator = elevator

            if best_elevator:
                self.add_target_task(best_elevator.id - 1, floor, call_id)

    def add_outside_call(self, floor: int, direction: Optional[MoveDirection]) -> str:
        """Add an outside call and return its call_id."""
        call_id = str(uuid4())
        self.pending_calls[call_id] = {"floor": floor, "direction": direction}
        return call_id

    def get_call_direction(self, call_id: str) -> Optional[MoveDirection]:
        """Get the direction for a pending call."""
        if call_id in self.pending_calls:
            return self.pending_calls[call_id]["direction"]
        return None

    def complete_call(self, call_id: str) -> None:
        """Remove a completed call from pending."""
        self.pending_calls.pop(call_id, None)

    def add_target_task(
        self,
        elevator_idx: int,
        floor: int,
        call_id: Optional[str] = None,
    ) -> None:
        elevator = self.world.elevators[elevator_idx]

        # If already at the floor and doors closed, open doors and send message
        if floor == elevator.current_floor and elevator.door_state == DoorState.CLOSED:
            # Get direction from call_id if it's an outside call
            direction_to_send = None
            if call_id:
                direction_to_send = self.get_call_direction(call_id)
                self.complete_call(call_id)

            self.api.send_floor_arrived_message(
                elevator.id, elevator.current_floor, direction_to_send
            )
            elevator.open_door()
            return  # Skip if already in queue or currently at this floor with doors open
        # For outside calls (with call_id), prevent duplicates by call_id
        # For inside calls (no call_id), prevent duplicates by floor
        if call_id:
            # Outside call - check if same call_id already exists
            if any(t.call_id == call_id for t in elevator.task_queue):
                return
        else:
            # Inside call - check if same floor already exists for inside calls
            if any(t.floor == floor and t.call_id is None for t in elevator.task_queue):
                return

        # Skip if currently at this floor with doors open
        if floor == elevator.current_floor and elevator.door_state != DoorState.CLOSED:
            return

        # Add new task with call_id
        elevator.task_queue.append(Task(floor, call_id))
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
