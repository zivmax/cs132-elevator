from enum import Enum, auto
from typing import NamedTuple, Optional

# System constants (matching UPPAAL model)
MIN_FLOOR = -1
MAX_FLOOR = 3
MIN_ELEVATOR_ID = 1
MAX_ELEVATOR_ID = 2


# Elevator States (only movement states)
class ElevatorState(Enum):
    IDLE = auto()
    MOVING_UP = auto()
    MOVING_DOWN = auto()


# Door States (all door-related states)
class DoorState(Enum):
    OPEN = auto()
    CLOSED = auto()
    OPENING = auto()
    CLOSING = auto()


class MoveDirection(Enum):
    UP = "up"
    DOWN = "down"


class MoveRequest:
    def __init__(self, elevator_id: int, direction: MoveDirection) -> None:
        self.elevator_id = elevator_id
        self.direction = direction  # "up" or "down"


class Task(NamedTuple):
    floor: int
    origin: str  # 'inside' or 'outside'
    direction: Optional[str] = None  # 'up', 'down', or None for inside


# Validation utility functions
def validate_floor(floor: int) -> bool:
    """Validate if floor is within acceptable range."""
    return MIN_FLOOR <= floor <= MAX_FLOOR


def validate_elevator_id(elevator_id: int) -> bool:
    """Validate if elevator ID is within acceptable range."""
    return MIN_ELEVATOR_ID <= elevator_id <= MAX_ELEVATOR_ID


def validate_direction(direction: str) -> bool:
    """Validate if direction is acceptable."""
    return direction in ["up", "down"]
