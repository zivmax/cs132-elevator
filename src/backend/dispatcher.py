from typing import List, Optional, TYPE_CHECKING, Tuple, Dict, Any
from uuid import uuid4
from .models import ElevatorState, DoorState, MoveDirection, Task, CallState, Call
from .elevator import Elevator


if TYPE_CHECKING:
    from .simulator import Simulator
    from .api.core import ElevatorAPI  # Added API import


class Dispatcher:
    # Added api parameter to __init__
    def __init__(self, world: "Simulator", api: "ElevatorAPI") -> None:
        self.world: "Simulator" = world
        self.api: "ElevatorAPI" = api  # Store API instance
        self.pending_calls: Dict[str, Call] = {}  # {call_id: Call}

    def add_call(self, floor: int, direction: str) -> None:
        try:
            move_direction = MoveDirection[direction.upper()]
            call_id = self.add_outside_call(floor, move_direction)
            self._process_pending_calls()
        except KeyError:
            # Invalid direction, handle gracefully
            call_id = self.add_outside_call(floor, None)
            self._process_pending_calls()

    def _process_pending_calls(self) -> None:
        for call_id, call in list(self.pending_calls.items()):
            # Skip calls that are already assigned or completed
            if not call.is_pending() or call.is_assigned():
                continue

            floor = call.floor
            direction = call.direction
            best_elevator: Optional["Elevator"] = None
            min_time: float = float("inf")

            # Check if any elevator can serve this call without direction conflict
            suitable_elevators = []

            for elevator in self.world.elevators:
                # Check if this elevator can serve the call without conflicting with its direction
                if self._can_elevator_serve_call(elevator, floor, direction):
                    est_time: float = elevator.calculate_estimated_time(
                        floor, direction
                    )
                    suitable_elevators.append((elevator, est_time))

            # If we have suitable elevators, pick the one with minimum time
            if suitable_elevators:
                suitable_elevators.sort(key=lambda x: x[1])
                best_elevator = suitable_elevators[0][0]
                min_time = suitable_elevators[0][1]
            else:
                # No suitable elevator found, defer this call for later processing
                continue

            if best_elevator:
                # Mark call as assigned before processing to prevent duplicates
                call.assign_to_elevator(best_elevator.id - 1)
                self.assign_task(best_elevator.id - 1, floor, call_id)

    def add_outside_call(self, floor: int, direction: Optional[MoveDirection]) -> str:
        """Add an outside call and return its call_id."""
        call_id = str(uuid4())
        self.pending_calls[call_id] = Call(call_id, floor, direction)
        return call_id

    def get_call_direction(self, call_id: str) -> Optional[MoveDirection]:
        """Get the direction for a pending call."""
        if call_id in self.pending_calls:
            return self.pending_calls[call_id].direction
        return None

    def complete_call(self, call_id: str) -> None:
        """Mark a call as completed and remove it from pending."""
        if call_id in self.pending_calls:
            self.pending_calls[call_id].complete()
            # Remove completed calls to free up memory
            self.pending_calls.pop(call_id, None)

    def assign_task(
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
                # Mark the call as completed since we're already at the floor
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

    def update(self) -> None:
        """Process all pending calls and assign them to the most suitable elevators."""
        self._process_pending_calls()

    def reset(self) -> None:
        """Resets the dispatcher state, clearing all pending calls."""
        self.pending_calls.clear()
        print("Dispatcher: Reset successful, all pending calls cleared.")

    def _get_elevator_committed_direction(
        self, elevator: "Elevator"
    ) -> Optional[MoveDirection]:
        """
        Determine the direction the elevator is committed to based on its current state and task queue.
        """
        # Priority 1: Elevator's own determined direction (from _determine_direction)
        if elevator.direction:
            return elevator.direction

        # Priority 2: Current movement state
        if elevator.state == ElevatorState.MOVING_UP:
            return MoveDirection.UP
        elif elevator.state == ElevatorState.MOVING_DOWN:
            return MoveDirection.DOWN

        # Priority 3: If idle/doors open, and servicing an outside call at the current floor
        if (
            elevator.task_queue
            and elevator.current_floor == elevator.task_queue[0].floor
        ):
            first_task = elevator.task_queue[0]
            if first_task.call_id:
                # Check the original call object from pending_calls
                call_obj = self.pending_calls.get(first_task.call_id)
                if call_obj and call_obj.direction:
                    return call_obj.direction

        # Priority 4: Fallback to next task in queue if not covered above
        if elevator.task_queue:
            # Consider the first task first.
            first_task_floor = elevator.task_queue[0].floor
            if first_task_floor > elevator.current_floor:
                return MoveDirection.UP
            elif first_task_floor < elevator.current_floor:
                return MoveDirection.DOWN
            else:  # first_task_floor == elevator.current_floor
                if len(elevator.task_queue) > 1:
                    second_task_floor = elevator.task_queue[1].floor
                    if second_task_floor > elevator.current_floor:
                        return MoveDirection.UP
                    elif second_task_floor < elevator.current_floor:
                        return MoveDirection.DOWN

        return None

    def _can_elevator_serve_call(
        self, elevator: "Elevator", floor: int, direction: Optional[MoveDirection]
    ) -> bool:
        """
        Determine if an elevator can take an outside call only when it's fully idle (no tasks, doors closed, not moving), otherwise defer.
        """
        # For outside calls, only assign to completely idle and ready elevators
        if direction is not None:
            if (
                elevator.state != ElevatorState.IDLE
                or elevator.door_state != DoorState.CLOSED
                or elevator.task_queue
            ):
                return False
            return True

        # For inside calls (direction is None), prevent duplicates but allow assignment
        # existing logic for internal requests
        if not elevator.task_queue:
            return True
        else:
            return True  # no further restriction for inside calls
