from enum import IntEnum


class ElevatorState(IntEnum):
    UP = 0
    DOWN = 1
    STOPPED_DOOR_CLOSED = 2
    STOPPED_DOOR_OPENED = 3
    STOPPED_OPENING_DOOR = 4
    STOPPED_CLOSING_DOOR = 5


class Elevator:
    def __init__(self, elevator_id):
        self.id = elevator_id
        self.current_floor = 1  # Initial floor
        self.target_floors = []  # Floors the elevator needs to visit
        self.direction = None  # 'up', 'down', or None (stopped)
        self.state = ElevatorState.STOPPED_DOOR_CLOSED

    def add_target_floor(self, floor):
        floor = int(floor)  # Convert to integer
        if floor not in self.target_floors:
            self.target_floors.append(floor)
            self.target_floors.sort(reverse=(self.direction == "down"))

    def reached_floor(self, floor):
        floor = int(floor)
        self.current_floor = floor
        if floor in self.target_floors:
            self.target_floors.remove(floor)

    def decide_direction(self):
        if not self.target_floors:
            return None
        next_floor = self.target_floors[0]
        if next_floor > self.current_floor:
            return "up"
        elif next_floor < self.current_floor:
            return "down"
        return None

    def should_stop_at(self, floor):
        return int(floor) in self.target_floors
