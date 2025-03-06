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


class Scheduler:
    def __init__(self):
        self.elevators = {"1": Elevator("1"), "2": Elevator("2")}
        self.up_calls = {}  # Floors with up calls {floor: handled_status}
        self.down_calls = {}  # Floors with down calls {floor: handled_status}
        self.last_elevator = "1"  # Last elevator that received an event

    def call_up(self, floor):
        floor = int(floor)
        self.up_calls[floor] = False  # Not handled yet
        self._schedule_elevator("up", floor)

    def call_down(self, floor):
        floor = int(floor)
        self.down_calls[floor] = False  # Not handled yet
        self._schedule_elevator("down", floor)

    def select_floor(self, floor, elevator_id):
        elevator = self.elevators[elevator_id]
        elevator.add_target_floor(floor)
        if (
            elevator.state == ElevatorState.STOPPED_DOOR_CLOSED
            and not elevator.target_floors
        ):
            elevator.direction = elevator.decide_direction()
            if elevator.direction == "up":
                elevator.state = ElevatorState.UP
            elif elevator.direction == "down":
                elevator.state = ElevatorState.DOWN

    def floor_arrived(self, direction_str, floor, elevator_id):
        floor = int(floor)
        self.last_elevator = elevator_id
        elevator = self.elevators[elevator_id]
        elevator.reached_floor(floor)

        # Check if we should stop at this floor
        should_stop = elevator.should_stop_at(floor)

        # Also check for calls in the same direction
        if (
            direction_str == "up"
            and floor in self.up_calls
            and not self.up_calls[floor]
        ):
            self.up_calls[floor] = True  # Mark as handled
            should_stop = True
        elif (
            direction_str == "down"
            and floor in self.down_calls
            and not self.down_calls[floor]
        ):
            self.down_calls[floor] = True  # Mark as handled
            should_stop = True

        return should_stop

    def _schedule_elevator(self, direction, floor):
        best_elevator = None
        min_cost = float("inf")

        for e_id, elevator in self.elevators.items():
            # Calculate a cost for assigning this call to this elevator
            cost = 100  # Default high cost

            # If elevator is idle, cost is just the distance
            if (
                elevator.state == ElevatorState.STOPPED_DOOR_CLOSED
                and not elevator.direction
            ):
                cost = abs(elevator.current_floor - floor)

            # If elevator is going in the same direction and can pick up on the way
            elif (
                elevator.direction == "up"
                and direction == "up"
                and elevator.current_floor <= floor
            ) or (
                elevator.direction == "down"
                and direction == "down"
                and elevator.current_floor >= floor
            ):
                cost = abs(elevator.current_floor - floor)

            if cost < min_cost:
                min_cost = cost
                best_elevator = elevator

        if best_elevator:
            # Check if the elevator is already at the called floor
            if best_elevator.current_floor == floor and best_elevator.state == ElevatorState.STOPPED_DOOR_CLOSED:
                # Mark the call as handled since we're already here
                if direction == "up":
                    self.up_calls[floor] = True
                else:
                    self.down_calls[floor] = True
                # Set transition to opening door directly
                best_elevator.state = ElevatorState.STOPPED_OPENING_DOOR
                return
                
            # Add this floor to the elevator's targets if needed
            if direction == "up":
                best_elevator.add_target_floor(floor)
            else:
                best_elevator.add_target_floor(floor)

            # Update elevator direction if needed
            if (
                best_elevator.state == ElevatorState.STOPPED_DOOR_CLOSED
                and not best_elevator.direction
            ):
                best_elevator.direction = best_elevator.decide_direction()
                if best_elevator.direction == "up":
                    best_elevator.state = ElevatorState.UP
                elif best_elevator.direction == "down":
                    best_elevator.state = ElevatorState.DOWN

    def next_floor(self, elevator_id):
        elevator = self.elevators[elevator_id]
        if elevator.target_floors:
            return elevator.target_floors[0]
        return None

    def reset(self):
        for e_id in self.elevators:
            self.elevators[e_id] = Elevator(e_id)
        self.up_calls = {}
        self.down_calls = {}
        self.last_elevator = "1"
