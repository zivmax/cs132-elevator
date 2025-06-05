import time
from typing import Dict, TYPE_CHECKING

from .models import MoveRequest

if TYPE_CHECKING:
    from .world import World


class Engine:
    def __init__(self, world: "World") -> None:
        self.world: "World" = world
        self.movement_requests: Dict[int, str] = {}  # elevator_id -> direction

    def request_movement(self, request: MoveRequest) -> None:
        """Process movement request from an elevator"""
        self.movement_requests[request.elevator_id] = request.direction.value
        # Set the elevator's state according to the requested direction
        elevator = self.world.elevators[request.elevator_id - 1]
        elevator.set_moving_state(request.direction.value)

    def update(self) -> None:
        current_time: float = time.time()

        # Process each elevator's movement
        for elevator in self.world.elevators:
            # Check if elevator is moving and has a movement request
            if (
                elevator.is_moving()
                and elevator.id in self.movement_requests
                and elevator.moving_since is not None
            ):  # Check if enough time has passed to reach next floor
                if current_time - elevator.moving_since >= elevator.floor_travel_time:
                    # Determine the next floor based on direction
                    direction = elevator.get_movement_direction()
                    next_floor = elevator.current_floor + direction

                    # Skip floor 0 since it doesn't exist in the system
                    if next_floor == 0:
                        next_floor = next_floor + direction

                    # Update elevator's floor
                    elevator.set_floor(next_floor)

                    # Remove the request once processed
                    if not elevator.task_queue or (
                        elevator.task_queue
                        and next_floor == elevator.task_queue[0].floor
                    ):
                        self.movement_requests.pop(elevator.id, None)
