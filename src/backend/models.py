from enum import Enum, auto
from typing import NamedTuple, Optional

# System constants (matching UPPAAL model)
MIN_FLOOR = -1
MAX_FLOOR = 3
MIN_ELEVATOR_ID = 1
MAX_ELEVATOR_ID = 2


class CallState(Enum):
    """State of a pending call"""

    PENDING = "pending"  # Call is waiting to be assigned
    ASSIGNED = "assigned"  # Call has been assigned to an elevator
    COMPLETED = "completed"  # Call has been completed


class Call:
    """Represents an outside call request with state tracking"""

    def __init__(
        self, call_id: str, floor: int, direction: Optional["MoveDirection"] = None
    ):
        self.call_id = call_id
        self.floor = floor
        self.direction = direction
        self.state = CallState.PENDING
        self.assigned_elevator: Optional[int] = None

    def assign_to_elevator(self, elevator_idx: int) -> None:
        """Assign this call to a specific elevator"""
        self.state = CallState.ASSIGNED
        self.assigned_elevator = elevator_idx

    def complete(self) -> None:
        """Mark this call as completed"""
        self.state = CallState.COMPLETED

    def is_pending(self) -> bool:
        """Check if this call is still pending assignment"""
        return self.state == CallState.PENDING

    def is_assigned(self) -> bool:
        """Check if this call has been assigned to an elevator"""
        return self.state == CallState.ASSIGNED

    def is_completed(self) -> bool:
        """Check if this call has been completed"""
        return self.state == CallState.COMPLETED

    def __repr__(self) -> str:
        return f"Call(id={self.call_id}, floor={self.floor}, direction={self.direction}, state={self.state.value})"


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
