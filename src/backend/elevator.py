import time
from typing import List, Optional, TYPE_CHECKING

from .models import ElevatorState, DoorState
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
        self.state: ElevatorState = ElevatorState.IDLE
        self.door_state: DoorState = DoorState.CLOSED
        self.direction: Optional[str] = None  # "up", "down", or None
        self.last_state_change: float = time.time()
        self.door_timeout: float = 3.0  # seconds before automatically closing doors
        self.floor_travel_time: float = 2.0  # seconds to travel between floors
        self.door_operation_time: float = 1.0  # seconds to open or close doors
        self.floor_arrival_delay: float = 2.0  # delay after arrival before door opening
        self.moving_since: Optional[float] = None  # Timestamp when movement started
        self.floor_changed: bool = False  # Flag to detect floor changes
        self.floor_arrival_announced: bool = False  # Track if floor arrival was announced
        self.arrival_time: Optional[float] = None  # When the elevator arrived at a floor
        self.serviced_current_arrival: bool = False  # Flag to prevent door reopening at same floor

    def update(self) -> None:
        current_time: float = time.time()

        # Check if floor has changed (set by Engine)
        if self.floor_changed:
            self.floor_changed = False
            self.arrival_time = current_time
            self.floor_arrival_announced = False
            self.serviced_current_arrival = False  # Reset serviced flag on floor change
            self.last_state_change = current_time

        # Handle floor arrival announcement with proper timing
        if self.arrival_time and not self.floor_arrival_announced and current_time - self.arrival_time >= 0.5:
            # Notify that we've arrived at a floor
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
                # Flag this floor as a target but don't remove it yet
                # We'll remove it after opening the door
                self.state = ElevatorState.IDLE
                self.last_state_change = current_time
            else:
                # Continue movement if we have more floors to visit
                self.request_movement_if_needed()

        # Only start opening doors after arrival announcement and proper delay
        # AND if we haven't already serviced this arrival
        if (self.floor_arrival_announced and 
            not self.serviced_current_arrival and
            self.state == ElevatorState.IDLE and 
            self.door_state == DoorState.CLOSED and
            current_time - self.last_state_change >= self.floor_arrival_delay and
            self.arrival_time and current_time - self.arrival_time >= self.floor_arrival_delay):
            # Open doors if this floor was in the target list
            if self.current_floor in self.target_floors:
                self.open_door()
                self.serviced_current_arrival = True  # Mark that we've serviced this arrival
                # Remove from target list after deciding to open door
                self.target_floors.remove(self.current_floor)
            elif self.target_floors == []:
                # Also open doors if we have no targets (e.g., initial floor)
                self.open_door()
                self.serviced_current_arrival = True

        # Handle automatic door closing
        if self.door_state == DoorState.OPEN:
            if current_time - self.last_state_change > self.door_timeout:
                self.close_door()

        # Update state based on current state
        if self.state == ElevatorState.DOOR_OPENING:
            if current_time - self.last_state_change > self.door_operation_time:
                self.door_state = DoorState.OPEN
                self.state = ElevatorState.DOOR_OPEN
                self.last_state_change = current_time
                self.world.send_msg(f"door_opened#{self.id}")

        elif self.state == ElevatorState.DOOR_CLOSING:
            if current_time - self.last_state_change > self.door_operation_time:
                self.door_state = DoorState.CLOSED
                self.state = ElevatorState.DOOR_CLOSED
                self.last_state_change = current_time
                self.world.send_msg(f"door_closed#{self.id}")

                # Request movement if we have target floors - with a small delay
                if current_time - self.last_state_change >= 0.3:
                    self.request_movement_if_needed()

        elif self.state == ElevatorState.DOOR_CLOSED:
            # Request movement if we have target floors - wait a moment before starting
            if current_time - self.last_state_change >= 0.3:
                self.request_movement_if_needed()
        
        # Fix for IDLE elevators with remaining targets - ensure they start moving again
        elif self.state == ElevatorState.IDLE and self.door_state == DoorState.CLOSED and self.target_floors:
            if current_time - self.last_state_change >= 0.5:  # Small delay before starting movement
                self.request_movement_if_needed()

    def request_movement_if_needed(self) -> None:
        """Request movement from the Engine if there are target floors"""
        if self.target_floors:
            self._determine_direction()
            if self.direction and self.door_state == DoorState.CLOSED:
                # Send move request to Engine instead of changing state directly
                move_request = MoveRequest(self.id, self.direction)
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
        if direction == "up":
            self.state = ElevatorState.MOVING_UP
        elif direction == "down":
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
            and self.state != ElevatorState.DOOR_OPENING
        ):
            self.state = ElevatorState.DOOR_OPENING
            self.door_state = DoorState.OPENING
            self.last_state_change = time.time()

    def close_door(self) -> None:
        if (
            self.door_state != DoorState.CLOSED
            and self.state != ElevatorState.DOOR_CLOSING
        ):
            self.state = ElevatorState.DOOR_CLOSING
            self.door_state = DoorState.CLOSING
            self.last_state_change = time.time()

    def _determine_direction(self) -> None:
        if not self.target_floors:
            self.direction = None
            return

        # If all target floors are above current floor
        if all(floor > self.current_floor for floor in self.target_floors):
            self.direction = "up"
        # If all target floors are below current floor
        elif all(floor < self.current_floor for floor in self.target_floors):
            self.direction = "down"
        # If current direction is up, keep going up until no more floors above
        elif self.direction == "up" and any(
            floor > self.current_floor for floor in self.target_floors
        ):
            self.direction = "up"
        # If current direction is down, keep going down until no more floors below
        elif self.direction == "down" and any(
            floor < self.current_floor for floor in self.target_floors
        ):
            self.direction = "down"
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
                    "up"
                    if closest_above - self.current_floor
                    <= self.current_floor - closest_below
                    else "down"
                )
            elif closest_above:
                self.direction = "up"
            elif closest_below:  # Added explicit check for closest_below
                self.direction = "down"
            else:
                self.direction = None  # No valid targets

    def calculate_estimated_time(self, floor: int, direction: str) -> float:
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
        if self.state == ElevatorState.IDLE or not self.is_moving():
            # Direct path to requested floor
            total_time += abs(self.current_floor - floor) * self.floor_travel_time
        else:
            # We need to consider the current direction and all target floors
            # Clone the target floors list and add the new request
            simulated_targets = self.target_floors.copy()

            # Determine when this floor would be serviced based on current direction
            currently_moving_up = self.state == ElevatorState.MOVING_UP

            # Calculate time based on elevator movement pattern
            if currently_moving_up:
                # First handle all floors above current in ascending order
                for target in sorted(
                    [f for f in simulated_targets if f > self.current_floor]
                ):
                    total_time += (
                        abs(target - self.current_floor) * self.floor_travel_time
                    )
                    self.current_floor = target  # Simulated position

                    # If this is our requested floor with matching direction
                    if target == floor and (direction == "up" or direction == ""):
                        return total_time

                # Then handle all floors below in descending order
                for target in sorted(
                    [f for f in simulated_targets if f < self.current_floor],
                    reverse=True,
                ):
                    total_time += (
                        abs(target - self.current_floor) * self.floor_travel_time
                    )
                    self.current_floor = target  # Simulated position

                    # If this is our requested floor with matching direction
                    if target == floor and (direction == "down" or direction == ""):
                        return total_time
            else:
                # First handle all floors below current in descending order
                for target in sorted(
                    [f for f in simulated_targets if f < self.current_floor],
                    reverse=True,
                ):
                    total_time += (
                        abs(target - self.current_floor) * self.floor_travel_time
                    )
                    self.current_floor = target  # Simulated position

                    # If this is our requested floor with matching direction
                    if target == floor and (direction == "down" or direction == ""):
                        return total_time

                # Then handle all floors above in ascending order
                for target in sorted(
                    [f for f in simulated_targets if f > self.current_floor]
                ):
                    total_time += (
                        abs(target - self.current_floor) * self.floor_travel_time
                    )
                    self.current_floor = target  # Simulated position

                    # If this is our requested floor with matching direction
                    if target == floor and (direction == "up" or direction == ""):
                        return total_time

            # If we didn't find it in the normal path, add time for direct path
            total_time += abs(self.current_floor - floor) * self.floor_travel_time

        return total_time

    def reset(self) -> None:
        self.current_floor = 1
        self.previous_floor = 1
        self.target_floors = []
        self.state = ElevatorState.IDLE
        self.door_state = DoorState.CLOSED
        self.direction = None
        self.last_state_change = time.time()
        self.moving_since = None
        self.floor_changed = False
        self.floor_arrival_announced = False
        self.arrival_time = None
        self.serviced_current_arrival = False
