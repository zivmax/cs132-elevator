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

        # Check if floor has changed (set by Engine)
        if self.floor_changed:
            self.floor_changed = False
            self.arrival_time = current_time
            self.floor_arrival_announced = False
            self.serviced_current_arrival = False  # Reset serviced flag on floor change
            self.last_state_change = current_time

        # First, check if elevator is moving
        if self.is_moving():
            # While moving, only handle floor announcements
            if (
                self.arrival_time
                and not self.floor_arrival_announced
                and current_time - self.arrival_time >= 0.5
            ):
                self.floor_arrival_announced = True

                # Check if we've reached a target floor
                if self.task_queue and self.current_floor == self.task_queue[0].floor:
                    # Stop at this floor
                    self.state = ElevatorState.IDLE

                    # Announce floor arrival with correct prefix
                    task = self.task_queue[0]
                    direction_to_send = None

                    if task.call_id:
                        # For outside calls, get direction from dispatcher
                        direction_to_send = self.world.dispatcher.get_call_direction(
                            task.call_id
                        )
                        # Mark call as completed
                        self.world.dispatcher.complete_call(task.call_id)
                    elif (
                        len(self.task_queue) > 1
                    ):  # For inside calls, determine from next stop
                        next_task_floor = self.task_queue[1].floor
                        if next_task_floor > self.current_floor:
                            direction_to_send = MoveDirection.UP
                        elif next_task_floor < self.current_floor:
                            direction_to_send = MoveDirection.DOWN

                    self.api.send_floor_arrived_message(
                        self.id, self.current_floor, direction_to_send
                    )
                    self.last_state_change = current_time
                else:
                    # Continue movement if we have more floors to visit
                    self.request_movement_if_needed()
            return  # Skip other processing while moving

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

    def request_movement_if_needed(self) -> None:
        """Request movement from the Engine if there are target floors"""
        if self.task_queue:
            self._determine_direction()
            if self.direction and self.door_state == DoorState.CLOSED:
                # Send move request to Engine instead of changing state directly
                move_request = MoveRequest(
                    self.id, self.direction
                )  # self.direction is now MoveDirection
                self.world.engine.request_movement(move_request)
        else:
            self.state = ElevatorState.IDLE

    def set_floor(self, new_floor: int) -> None:
        """Called by Engine to update the elevator's floor position"""
        if self.current_floor != new_floor:
            self.previous_floor = self.current_floor
            self.current_floor = new_floor
            self.floor_changed = True  # Set flag to process floor change in next update
            self.moving_since = time.time()  # Reset moving timer for next floor
            # Don't update last_state_change here - it's updated in update() when floor_changed is processed

    def set_moving_state(self, direction: str) -> None:
        """Called by Engine to set the elevator's moving state"""
        if direction == MoveDirection.UP.value:  # Use MoveDirection enum value
            self.state = ElevatorState.MOVING_UP
        elif direction == MoveDirection.DOWN.value:  # Use MoveDirection enum value
            self.state = ElevatorState.MOVING_DOWN
        else:
            self.state = ElevatorState.IDLE
        self.moving_since = time.time()
        self.last_state_change = self.moving_since

    def is_moving(self) -> bool:
        """Check if elevator is in a moving state"""
        return self.state in [ElevatorState.MOVING_UP, ElevatorState.MOVING_DOWN]

    def get_movement_direction(self) -> int:
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
            and not self.is_moving()
        ):
            self.door_state = DoorState.OPENING
            self.last_door_change = time.time()

    def close_door(self) -> None:
        if (
            self.door_state != DoorState.CLOSED
            and self.door_state != DoorState.OPENING
            and not self.is_moving()
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
        if self.door_state in [DoorState.OPEN, DoorState.OPENING]:
            total_time += 1.0  # Door closing time
        original_floor = self.current_floor
        original_task_queue = self.task_queue.copy()
        original_state = self.state
        simulated_current_floor = self.current_floor
        if self.state == ElevatorState.IDLE or not self.is_moving():
            total_time += abs(simulated_current_floor - floor) * self.floor_travel_time
        else:
            simulated_targets = self.task_queue.copy()
            currently_moving_up = self.state == ElevatorState.MOVING_UP
            if currently_moving_up:
                for target in sorted(
                    [
                        task.floor
                        for task in simulated_targets
                        if task.floor > simulated_current_floor
                    ]
                ):
                    total_time += (
                        abs(target - simulated_current_floor) * self.floor_travel_time
                    )
                    simulated_current_floor = target
                    if target == floor and (
                        direction == MoveDirection.UP or direction is None
                    ):
                        self.current_floor = original_floor
                        self.task_queue = original_task_queue
                        self.state = original_state
                        return total_time
                if simulated_targets and simulated_current_floor != floor:
                    pass
                for target in sorted(
                    [
                        task.floor
                        for task in simulated_targets
                        if task.floor < simulated_current_floor
                    ],
                    reverse=True,
                ):
                    total_time += (
                        abs(target - simulated_current_floor) * self.floor_travel_time
                    )
                    simulated_current_floor = target
                    if target == floor and (
                        direction == MoveDirection.DOWN or direction is None
                    ):
                        self.current_floor = original_floor
                        self.task_queue = original_task_queue
                        self.state = original_state
                        return total_time
            else:
                for target in sorted(
                    [
                        task.floor
                        for task in simulated_targets
                        if task.floor < simulated_current_floor
                    ],
                    reverse=True,
                ):
                    total_time += (
                        abs(target - simulated_current_floor) * self.floor_travel_time
                    )
                    simulated_current_floor = target
                    if target == floor and (
                        direction == MoveDirection.DOWN or direction is None
                    ):
                        self.current_floor = original_floor
                        self.task_queue = original_task_queue
                        self.state = original_state
                        return total_time
                if simulated_targets and simulated_current_floor != floor:
                    pass
                for target in sorted(
                    [
                        task.floor
                        for task in simulated_targets
                        if task.floor > simulated_current_floor
                    ]
                ):
                    total_time += (
                        abs(target - simulated_current_floor) * self.floor_travel_time
                    )
                    simulated_current_floor = target
                    if target == floor and (
                        direction == MoveDirection.UP or direction is None
                    ):
                        self.current_floor = original_floor
                        self.task_queue = original_task_queue
                        self.state = original_state
                        return total_time
            total_time += abs(simulated_current_floor - floor) * self.floor_travel_time
        self.current_floor = original_floor
        self.task_queue = original_task_queue
        self.state = original_state
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
