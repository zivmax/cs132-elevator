from enum import Enum, auto

# Elevator States
class ElevatorState(Enum):
    IDLE = auto()
    MOVING_UP = auto()
    MOVING_DOWN = auto()
    DOOR_OPENING = auto()
    DOOR_OPEN = auto()
    DOOR_CLOSING = auto()
    DOOR_CLOSED = auto()

# Door States
class DoorState(Enum):
    OPEN = auto()
    CLOSED = auto()
    OPENING = auto()
    CLOSING = auto()

class MoveRequest:
    def __init__(self, elevator_id: int, direction: str):
        self.elevator_id = elevator_id
        self.direction = direction  # "up" or "down"

