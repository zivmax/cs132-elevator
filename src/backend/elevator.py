import time
from typing import List, Optional, Dict, TYPE_CHECKING

from .models import ElevatorState, DoorState, MoveDirection  # Add MoveDirection import
from .models import MoveRequest

if TYPE_CHECKING:
    from .world import World


class Elevator:
    def __init__(self, elevator_id: int, world: "World") -> None:
        self.id: int = elevator_id
        self.world: "World" = world
        self.current_floor: int = 1  # Initial floor is 1
        self.previous_floor: int = 1  # Track previous floor for change detection
        self.target_floors: List[int] = []
        self.target_floors_origin: dict = (
            {}
        )  # Track origin of target floors: "inside" or "outside"
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
        self.floor_arrival_delay: float = 2.0  # delay after arrival before door opening
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
                # Announce floor arrival
                direction_str: str = (
                    "up_"
                    if self.state == ElevatorState.MOVING_UP
                    else "down_" if self.state == ElevatorState.MOVING_DOWN else ""
                )
                self.world.send_msg(
                    f"{direction_str}floor_arrived@{self.current_floor}#{self.id}"
                )
                self.floor_arrival_announced = True

                # Check if we've reached a target floor
                if self.current_floor in self.target_floors:
                    # Stop at this floor
                    self.state = ElevatorState.IDLE
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
                self.world.send_msg(f"door_opened#{self.id}")

        elif self.door_state == DoorState.CLOSING:
            if current_time - self.last_door_change > self.door_operation_time:
                self.door_state = DoorState.CLOSED
                self.last_door_change = current_time
                self.world.send_msg(f"door_closed#{self.id}")

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
        ):  # Check if this floor is a target
            if self.current_floor in self.target_floors:
                # Open doors for target floor
                self.open_door()
                self.serviced_current_arrival = True

                # Remove this floor from targets and origins
                self.target_floors.remove(self.current_floor)
                if self.current_floor in self.target_floors_origin:
                    del self.target_floors_origin[self.current_floor]
            elif not self.target_floors:
                # Open doors if we have no targets (e.g., initial floor)
                self.open_door()
                self.serviced_current_arrival = True

        # Check if we have remaining target floors and need to move
        elif (
            self.state == ElevatorState.IDLE
            and self.door_state == DoorState.CLOSED
            and self.target_floors
            and current_time - self.last_state_change >= 0.5
        ):
            self.request_movement_if_needed()

    def request_movement_if_needed(self) -> None:
        """Request movement from the Engine if there are target floors"""
        if self.target_floors:
            self._determine_direction()
            if self.direction and self.door_state == DoorState.CLOSED:
                # Send move request to Engine instead of changing state directly
                move_request = MoveRequest(self.id, self.direction) # self.direction is now MoveDirection
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
        if direction == MoveDirection.UP.value: # Use MoveDirection enum value
            self.state = ElevatorState.MOVING_UP
        elif direction == MoveDirection.DOWN.value: # Use MoveDirection enum value
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
        if not self.target_floors:
            self.direction = None
            return

        # If all target floors are above current floor
        if all(floor > self.current_floor for floor in self.target_floors):
            self.direction = MoveDirection.UP
        # If all target floors are below current floor
        elif all(floor < self.current_floor for floor in self.target_floors):
            self.direction = MoveDirection.DOWN
        # If current direction is up, keep going up until no more floors above
        elif self.direction == MoveDirection.UP and any(
            floor > self.current_floor for floor in self.target_floors
        ):
            self.direction = MoveDirection.UP
        # If current direction is down, keep going down until no more floors below
        elif self.direction == MoveDirection.DOWN and any(
            floor < self.current_floor for floor in self.target_floors
        ):
            self.direction = MoveDirection.DOWN
        # Otherwise pick the closest floor
        else:
            closest_above: Optional[int] = min(
                [f for f in self.target_floors if f > self.current_floor], default=None
            )
            closest_below: Optional[int] = max(
                [f for f in self.target_floors if f < self.current_floor], default=None
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
            elif closest_below:  # Added explicit check for closest_below
                self.direction = MoveDirection.DOWN
            else:
                self.direction = None  # No valid targets

    def calculate_estimated_time(self, floor: int, direction: Optional[MoveDirection]) -> float:  # Change direction type to MoveDirection also allow None
        # Calculate estimated time to service a request at floor with given direction
        if self.current_floor == floor and self.door_state in [
            DoorState.OPEN,
            DoorState.OPENING,
        ]:
            return 0  # Already at floor with open door

        # Calculate time based on current state and target floors
        total_time = 0.0

        # Time to close door if open
        if self.door_state in [DoorState.OPEN, DoorState.OPENING]:
            total_time += 1.0  # Door closing time

        # Simulate the path to determine time
        # Store original state to restore later
        original_floor = self.current_floor
        original_target_floors = self.target_floors.copy()
        original_state = self.state

        simulated_current_floor = self.current_floor

        if self.state == ElevatorState.IDLE or not self.is_moving():
            # Direct path to requested floor
            total_time += abs(simulated_current_floor - floor) * self.floor_travel_time
        else:
            # We need to consider the current direction and all target floors
            simulated_targets = self.target_floors.copy()

            # Determine when this floor would be serviced based on current direction
            currently_moving_up = self.state == ElevatorState.MOVING_UP

            # Calculate time based on elevator movement pattern
            if currently_moving_up:
                # First handle all floors above current in ascending order
                for target in sorted(
                    [f for f in simulated_targets if f > simulated_current_floor]
                ):
                    total_time += (
                        abs(target - simulated_current_floor) * self.floor_travel_time
                    )
                    simulated_current_floor = target  # Simulated position

                    # If this is our requested floor with matching direction
                    if target == floor and (direction == MoveDirection.UP or direction == None):  # Use MoveDirection.UP
                        # Restore original state before returning
                        self.current_floor = original_floor
                        self.target_floors = original_target_floors
                        self.state = original_state
                        return total_time

                # Then handle all floors below in descending order
                # This part assumes the elevator turns around
                # If the request is in the opposite direction of current travel,
                # it will be serviced after the current direction's requests are done.
                if simulated_targets and simulated_current_floor != floor:  # if there were targets upwards or we are not at the floor
                    # Time to turn around (if it was moving up and now needs to go down)
                    # No explicit turn around time, but new direction starts
                    pass

                for target in sorted(
                    [f for f in simulated_targets if f < simulated_current_floor],
                    reverse=True,
                ):
                    total_time += (
                        abs(target - simulated_current_floor) * self.floor_travel_time
                    )
                    simulated_current_floor = target  # Simulated position

                    # If this is our requested floor with matching direction
                    if target == floor and (direction == MoveDirection.DOWN or direction == None):  # Use MoveDirection.DOWN
                        # Restore original state
                        self.current_floor = original_floor
                        self.target_floors = original_target_floors
                        self.state = original_state
                        return total_time
            else:  # Currently moving down
                # First handle all floors below current in descending order
                for target in sorted(
                    [f for f in simulated_targets if f < simulated_current_floor],
                    reverse=True,
                ):
                    total_time += (
                        abs(target - simulated_current_floor) * self.floor_travel_time
                    )
                    simulated_current_floor = target  # Simulated position

                    # If this is our requested floor with matching direction
                    if target == floor and (direction == MoveDirection.DOWN or direction == None):  # Use MoveDirection.DOWN
                        # Restore original state
                        self.current_floor = original_floor
                        self.target_floors = original_target_floors
                        self.state = original_state
                        return total_time

                # Then handle all floors above in ascending order
                if simulated_targets and simulated_current_floor != floor:  # if there were targets downwards or we are not at the floor
                    # Time to turn around
                    pass

                for target in sorted(
                    [f for f in simulated_targets if f > simulated_current_floor]
                ):
                    total_time += (
                        abs(target - simulated_current_floor) * self.floor_travel_time
                    )
                    simulated_current_floor = target  # Simulated position

                    # If this is our requested floor with matching direction
                    if target == floor and (direction == MoveDirection.UP or direction == None):  # Use MoveDirection.UP
                        # Restore original state
                        self.current_floor = original_floor
                        self.target_floors = original_target_floors
                        self.state = original_state
                        return total_time

            # If we didn't find it in the normal path (e.g. it's a new call not in target_floors or requires a turn)
            # Add time for direct path from the last simulated position
            total_time += abs(simulated_current_floor - floor) * self.floor_travel_time

        # Restore original state
        self.current_floor = original_floor
        self.target_floors = original_target_floors
        self.state = original_state
        return total_time

    def reset(self) -> None:
        self.current_floor = 1
        self.previous_floor = 1
        self.target_floors = []
        self.target_floors_origin = {}  # Clear the origins dictionary
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
