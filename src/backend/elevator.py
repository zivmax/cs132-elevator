import time
from typing import List, Optional, Dict, TYPE_CHECKING

from .models import ElevatorState, DoorState, MoveDirection, Task
from .models import MoveRequest

if TYPE_CHECKING:
    from .simulator import Simulator
    from .api.core import ElevatorAPI  # Added API import


class Elevator:
    # Added api parameter to __init__
    def __init__(
        self, elevator_id: int, world: "Simulator", api: "ElevatorAPI"
    ) -> None:
        self.id: int = elevator_id
        self.world: "Simulator" = world
        self.api: "ElevatorAPI" = api  # Store API instance
        self.current_floor: int = 1  # Initial floor is 1
        self.previous_floor: int = 1  # Track previous floor for change detection
        self.task_queue: List[Task] = (
            []
        )  # Replaces target_floors and target_floors_origin
        self.state: ElevatorState = ElevatorState.IDLE  # Movement state
        self.door_state: DoorState = DoorState.CLOSED  # Door state
        self.direction: Optional[MoveDirection] = None  # Use MoveDirection enum
        self.last_state_change: float = time.time()
        self.last_door_change: float = (
            time.time()
        )  # Separate timestamp for door changes
        self.door_timeout: float = 3.0  # seconds before automatically closing doors
        self.floor_travel_time: float = 2.0  # seconds to travel between floors
        self.door_operation_time: float = 1.0  # seconds to open or close doors
        self.floor_arrival_delay: float = (
            0.5  # reduced delay after arrival before door opening
        )
        self.moving_since: Optional[float] = None  # Timestamp when movement started
        self.floor_changed: bool = False  # Flag to detect floor changes
        self.floor_arrival_announced: bool = (
            False  # Track if floor arrival was announced
        )
        self.arrival_time: Optional[float] = (
            None  # When the elevator arrived at a floor
        )
        self.serviced_current_arrival: bool = (
            False  # Flag to prevent door reopening at same floor
        )

    def update(self) -> None:
        current_time: float = time.time()

        # Check if floor has changed (previously set by Engine, now internal)
        if self.floor_changed:
            self.floor_changed = False
            self.arrival_time = current_time
            self.floor_arrival_announced = False
            self.serviced_current_arrival = False  # Reset serviced flag on floor change
            self.last_state_change = current_time

        # First, check if elevator is moving
        if self._is_moving():
            # Handle movement logic previously in Engine
            if (
                self.moving_since is not None
                and current_time - self.moving_since >= self.floor_travel_time
            ):
                current_direction_value = self._get_movement_direction()
                next_floor = self.current_floor + current_direction_value
                if next_floor == 0:  # Skip floor 0
                    next_floor += current_direction_value
                self._set_floor(next_floor)  # This will set floor_changed = True

            # While moving, also handle floor announcements (original logic)
            if (
                self.arrival_time  # This is set when floor_changed is true
                and not self.floor_arrival_announced
                and current_time - self.arrival_time
                >= 0.5  # Original delay for announcement
            ):
                self.floor_arrival_announced = True

                # Check if we've reached a target floor in the task_queue
                if self.task_queue and self.current_floor == self.task_queue[0].floor:
                    self._handle_arrival_at_target_floor(current_time)

            return  # Skip other processing while moving or just after floor change

        # Check if delay is time up before proceeding with door operations
        if (
            self.floor_arrival_announced
            and not self.serviced_current_arrival
            and self.arrival_time
            and current_time - self.arrival_time < self.floor_arrival_delay
        ):
            return  # Wait for delay to complete

        # Handle door state transitions
        if self.door_state == DoorState.OPENING:
            if current_time - self.last_door_change > self.door_operation_time:
                self.door_state = DoorState.OPEN
                self.last_door_change = current_time
                # Use API to send message
                self.api.send_door_opened_message(self.id)

        elif self.door_state == DoorState.CLOSING:
            if current_time - self.last_door_change > self.door_operation_time:
                self.door_state = DoorState.CLOSED
                self.last_door_change = current_time
                # Use API to send message
                self.api.send_door_closed_message(self.id)

                # After door is closed, check if we need to move
                if current_time - self.last_door_change >= 0.3:
                    self.request_movement_if_needed()

        elif self.door_state == DoorState.OPEN:
            # Auto-close doors after timeout
            if current_time - self.last_door_change > self.door_timeout:
                self.close_door()

        # If idle with closed doors, check if we arrived at a target floor
        elif (
            self.state == ElevatorState.IDLE
            and self.door_state == DoorState.CLOSED
            and self.floor_arrival_announced
            and not self.serviced_current_arrival
        ):
            if self.task_queue and self.current_floor == self.task_queue[0].floor:
                # Open doors for target floor
                self.open_door()
                self.serviced_current_arrival = True
                # Remove this task from the queue
                self.task_queue.pop(0)
            elif not self.task_queue:
                # Open doors if we have no targets (e.g., initial floor)
                self.open_door()
                self.serviced_current_arrival = True

        # Check if we have remaining target floors and need to move
        elif (
            self.state == ElevatorState.IDLE
            and self.door_state == DoorState.CLOSED
            and self.task_queue
            and current_time - self.last_state_change >= 0.5
        ):
            self.request_movement_if_needed()

    def _handle_arrival_at_target_floor(self, current_time: float) -> None:
        """Handles logic when elevator arrives at a target floor in its task queue."""
        self.state = ElevatorState.IDLE  # Stop at this floor

        # Announce floor arrival with correct prefix
        task = self.task_queue[0]
        direction_to_send = None

        if task.call_id:
            # For outside calls, get direction from dispatcher
            direction_to_send = self.world.dispatcher.get_call_direction(task.call_id)
            # Mark call as completed
            self.world.dispatcher.complete_call(task.call_id)
        elif len(self.task_queue) > 1:  # For inside calls, determine from next stop
            next_task_floor = self.task_queue[1].floor
            if next_task_floor > self.current_floor:
                direction_to_send = MoveDirection.UP
            elif next_task_floor < self.current_floor:
                direction_to_send = MoveDirection.DOWN

        self.api.send_floor_arrived_message(
            self.id, self.current_floor, direction_to_send
        )
        self.last_state_change = current_time  # State changed to IDLE

    def request_movement_if_needed(self) -> None:
        """Set elevator to move if there are target floors and doors are closed."""
        if self.task_queue:
            self._determine_direction()
            if self.direction and self.door_state == DoorState.CLOSED:
                # Directly set moving state instead of sending request to Engine
                self._set_moving_state(self.direction.value)
        else:
            if self.state != ElevatorState.IDLE:  # Ensure it becomes IDLE if no tasks
                self.state = ElevatorState.IDLE
                self.moving_since = None  # Clear moving_since when becoming IDLE
                self.last_state_change = time.time()

    def _set_floor(self, new_floor: int) -> None:
        """Called internally to update the elevator's floor position"""
        if self.current_floor != new_floor:
            self.previous_floor = self.current_floor
            self.current_floor = new_floor
            self.floor_changed = True  # Set flag to process floor change in next update
            self.moving_since = (
                time.time()
            )  # Reset moving timer for next floor travel segment
            # last_state_change is updated in update() when floor_changed is processed or state changes

    def _set_moving_state(self, direction_value: str) -> None:
        """Called internally to set the elevator's moving state"""
        new_state = ElevatorState.IDLE
        if direction_value == MoveDirection.UP.value:
            new_state = ElevatorState.MOVING_UP
        elif direction_value == MoveDirection.DOWN.value:
            new_state = ElevatorState.MOVING_DOWN

        current_time = time.time()  # Get current time for state change
        if (
            self.state != new_state or new_state == ElevatorState.IDLE
        ):  # Update if state changes OR if it's set to IDLE (even if already IDLE)
            self.state = new_state
            self.moving_since = current_time
            self.last_state_change = self.moving_since
            if new_state == ElevatorState.IDLE:
                self.moving_since = None  # Clear if becoming IDLE

    def _is_moving(self) -> bool:
        """Check if elevator is in a moving state"""
        return self.state in [ElevatorState.MOVING_UP, ElevatorState.MOVING_DOWN]

    def _get_movement_direction(self) -> int:
        """Returns 1 for up, -1 for down, 0 for not moving"""
        if self.state == ElevatorState.MOVING_UP:
            return 1
        elif self.state == ElevatorState.MOVING_DOWN:
            return -1
        return 0

    def open_door(self) -> None:
        if (
            self.door_state != DoorState.OPEN
            and self.door_state != DoorState.CLOSING
            and not self._is_moving()
        ):
            self.door_state = DoorState.OPENING
            self.last_door_change = time.time()

    def close_door(self) -> None:
        if (
            self.door_state != DoorState.CLOSED
            and self.door_state != DoorState.OPENING
            and not self._is_moving()
        ):
            self.door_state = DoorState.CLOSING
            self.last_door_change = time.time()

    def _determine_direction(self) -> None:
        if not self.task_queue:
            self.direction = None
            return
        # If all target floors are above current floor
        if all(task.floor > self.current_floor for task in self.task_queue):
            self.direction = MoveDirection.UP
        # If all target floors are below current floor
        elif all(task.floor < self.current_floor for task in self.task_queue):
            self.direction = MoveDirection.DOWN
        # If current direction is up, keep going up until no more floors above
        elif self.direction == MoveDirection.UP and any(
            task.floor > self.current_floor for task in self.task_queue
        ):
            self.direction = MoveDirection.UP
        # If current direction is down, keep going down until no more floors below
        elif self.direction == MoveDirection.DOWN and any(
            task.floor < self.current_floor for task in self.task_queue
        ):
            self.direction = MoveDirection.DOWN
        # Otherwise pick the closest floor
        else:
            closest_above: Optional[int] = min(
                [
                    task.floor
                    for task in self.task_queue
                    if task.floor > self.current_floor
                ],
                default=None,
            )
            closest_below: Optional[int] = max(
                [
                    task.floor
                    for task in self.task_queue
                    if task.floor < self.current_floor
                ],
                default=None,
            )
            if closest_above and closest_below:
                self.direction = (
                    MoveDirection.UP
                    if closest_above - self.current_floor
                    <= self.current_floor - closest_below
                    else MoveDirection.DOWN
                )
            elif closest_above:
                self.direction = MoveDirection.UP
            elif closest_below:
                self.direction = MoveDirection.DOWN
            else:
                self.direction = None  # No valid targets

    def calculate_estimated_time(
        self, floor: int, direction: Optional[MoveDirection]
    ) -> float:
        if self.current_floor == floor and self.door_state in [
            DoorState.OPEN,
            DoorState.OPENING,
        ]:
            return 0  # Already at floor with open door

        total_time = 0.0
        # Account for door closing time if currently open or opening
        if self.door_state in [DoorState.OPEN, DoorState.OPENING]:
            total_time += self.door_operation_time  # Time to close doors

        # Simulate elevator movement
        simulated_current_floor = self.current_floor

        # If idle or not moving towards the requested floor's direction,
        # calculate direct travel time.
        if self.state == ElevatorState.IDLE or not self._is_moving():
            total_time += abs(simulated_current_floor - floor) * self.floor_travel_time
            # Add door opening time at destination
            total_time += self.door_operation_time
            return total_time

        # If moving, simulate serving existing tasks then moving to the new floor

        # Preserve original state for restoration
        original_floor = self.current_floor
        original_task_queue = self.task_queue.copy()
        original_state = self.state
        original_direction = self.direction

        def _simulate_serving_targets(
            current_sim_floor: int,
            targets: List[int],
            current_total_time: float,
            target_direction: Optional[MoveDirection],  # Direction of the *new* call
            is_final_leg: bool = False,  # True if this is the leg towards the new requested floor
        ) -> tuple[int, float, bool]:
            """
            Simulates serving a list of target floors.
            Returns the new current floor, updated total time, and if the target floor was reached.
            """
            reached_target_floor = False
            for target_stop in targets:
                current_total_time += (
                    abs(target_stop - current_sim_floor) * self.floor_travel_time
                )
                current_sim_floor = target_stop
                current_total_time += (
                    self.door_operation_time
                )  # Door cycle at each stop

                # Check if this stop is the requested floor and direction matches
                if target_stop == floor:
                    if (
                        target_direction is None
                    ):  # Any direction is fine if not specified
                        reached_target_floor = True
                        break
                    elif (
                        self.direction == MoveDirection.UP
                        and target_direction == MoveDirection.UP
                    ):
                        reached_target_floor = True
                        break
                    elif (
                        self.direction == MoveDirection.DOWN
                        and target_direction == MoveDirection.DOWN
                    ):
                        reached_target_floor = True
                        break

            return current_sim_floor, current_total_time, reached_target_floor

        simulated_task_queue = self.task_queue.copy()  # Use a copy for simulation

        if self.state == ElevatorState.MOVING_UP:
            # Serve stops above current floor in current direction
            stops_above = sorted(
                [
                    t.floor
                    for t in simulated_task_queue
                    if t.floor > simulated_current_floor
                ]
            )
            simulated_current_floor, total_time, reached = _simulate_serving_targets(
                simulated_current_floor, stops_above, total_time, direction
            )
            if reached:
                self.current_floor, self.task_queue, self.state, self.direction = (
                    original_floor,
                    original_task_queue,
                    original_state,
                    original_direction,
                )
                return total_time

            # If the target floor is below, or above but not reached (e.g. different direction call)
            # simulate serving stops below (turnaround)
            if floor < simulated_current_floor or (
                floor > simulated_current_floor and not reached
            ):
                # Time for potential turnaround if no more stops in current direction
                stops_below = sorted(
                    [
                        t.floor
                        for t in simulated_task_queue
                        if t.floor < simulated_current_floor
                    ],
                    reverse=True,
                )
                if stops_below:
                    simulated_current_floor, total_time, reached = (
                        _simulate_serving_targets(
                            simulated_current_floor, stops_below, total_time, direction
                        )
                    )
                    if reached:
                        (
                            self.current_floor,
                            self.task_queue,
                            self.state,
                            self.direction,
                        ) = (
                            original_floor,
                            original_task_queue,
                            original_state,
                            original_direction,
                        )
                        return total_time

            # After serving all relevant existing tasks, travel to the new floor
            total_time += abs(simulated_current_floor - floor) * self.floor_travel_time

        elif self.state == ElevatorState.MOVING_DOWN:
            # Serve stops below current floor
            stops_below = sorted(
                [
                    t.floor
                    for t in simulated_task_queue
                    if t.floor < simulated_current_floor
                ],
                reverse=True,
            )
            simulated_current_floor, total_time, reached = _simulate_serving_targets(
                simulated_current_floor, stops_below, total_time, direction
            )
            if reached:
                self.current_floor, self.task_queue, self.state, self.direction = (
                    original_floor,
                    original_task_queue,
                    original_state,
                    original_direction,
                )
                return total_time

            # If the target floor is above, or below but not reached
            if floor > simulated_current_floor or (
                floor < simulated_current_floor and not reached
            ):
                stops_above = sorted(
                    [
                        t.floor
                        for t in simulated_task_queue
                        if t.floor > simulated_current_floor
                    ]
                )
                # Similar to MOVING_UP, if stops_above exist, they'd be served.
                if stops_above:
                    simulated_current_floor, total_time, reached = (
                        _simulate_serving_targets(
                            simulated_current_floor, stops_above, total_time, direction
                        )
                    )
                    if reached:
                        (
                            self.current_floor,
                            self.task_queue,
                            self.state,
                            self.direction,
                        ) = (
                            original_floor,
                            original_task_queue,
                            original_state,
                            original_direction,
                        )
                        return total_time

            # After serving all relevant existing tasks, travel to the new floor
            total_time += abs(simulated_current_floor - floor) * self.floor_travel_time

        # Add door opening time at the final destination floor
        total_time += self.door_operation_time

        # Restore original state
        self.current_floor = original_floor
        self.task_queue = original_task_queue
        self.state = original_state
        self.direction = original_direction

        return total_time

    def reset(self) -> None:
        self.current_floor = 1
        self.previous_floor = 1
        self.task_queue = []
        self.state = ElevatorState.IDLE
        self.door_state = DoorState.CLOSED
        self.direction = None
        self.last_state_change = time.time()
        self.last_door_change = time.time()
        self.moving_since = None
        self.floor_changed = False
        self.floor_arrival_announced = False
        self.arrival_time = None
        self.serviced_current_arrival = False
