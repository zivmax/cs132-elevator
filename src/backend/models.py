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


class Task:
    """Represents a task for the elevator to service a floor.

    Attributes:
        floor: The target floor number.
        call_id: Optional[str]. If present, links to an outside call in the dispatcher.
                If None, this is an inside call (from elevator panel).
    """

    def __init__(self, floor: int, call_id: Optional[str] = None) -> None:
        self.floor = floor
        self.call_id = call_id

    def __repr__(self) -> str:
        return f"Task(floor={self.floor}, call_id={self.call_id})"

    @property
    def is_outside_call(self) -> bool:
        """Returns True if this task is from an outside call."""
        return self.call_id is not None


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
