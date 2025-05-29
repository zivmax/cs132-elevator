from enum import Enum, auto
from typing import NamedTuple, Optional


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
    def __init__(self, elevator_id: int, direction: MoveDirection):
        self.elevator_id = elevator_id
        self.direction = direction  # "up" or "down"


class Task(NamedTuple):
    floor: int
    origin: str  # 'inside' or 'outside'
    direction: Optional[str] = None  # 'up', 'down', or None for inside
