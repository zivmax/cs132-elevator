import os
import time
import sys
from enum import Enum, auto
from typing import List, Optional, Dict, Union, Set, Any, Tuple
from net_client import ZmqClientThread

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

# Request type for movement
class MoveRequest:
    def __init__(self, elevator_id: int, direction: str):
        self.elevator_id = elevator_id
        self.direction = direction  # "up" or "down"

class Elevator:
    def __init__(self, elevator_id: int, world: 'World') -> None:
        self.id: int = elevator_id
        self.world: 'World' = world
        self.current_floor: int = 1  # Initial floor is 1
        self.previous_floor: int = 1  # Track previous floor for change detection
        self.target_floors: List[int] = []
        self.state: ElevatorState = ElevatorState.IDLE
        self.door_state: DoorState = DoorState.CLOSED
        self.direction: Optional[str] = None  # "up", "down", or None
        self.last_state_change: float = time.time()
        self.door_timeout: float = 3.0  # seconds before automatically closing doors
        self.floor_travel_time: float = 2.0  # seconds to travel between floors
        self.moving_since: Optional[float] = None  # Timestamp when movement started
        self.floor_changed: bool = False  # Flag to detect floor changes

    def update(self) -> None:
        current_time: float = time.time()
        
        # Check if floor has changed (set by Engine)
        if self.floor_changed:
            self.floor_changed = False
            
            # Notify that we've arrived at a floor
            self._handle_floor_arrival()
            
            # Continue movement if we haven't reached a target floor
            if self.current_floor not in self.target_floors:
                self.request_movement_if_needed()
        
        # If elevator is at a target floor with closed doors, handle arrival
        elif self.current_floor in self.target_floors and self.door_state == DoorState.CLOSED:
            self._handle_floor_arrival()
            return
        
        # Handle automatic door closing
        if self.door_state == DoorState.OPEN:
            if current_time - self.last_state_change > self.door_timeout:
                self.close_door()
        
        # Update state based on current state
        if self.state == ElevatorState.DOOR_OPENING:
            if current_time - self.last_state_change > 1.0:  # 1 second to open door
                self.door_state = DoorState.OPEN
                self.state = ElevatorState.DOOR_OPEN
                self.last_state_change = current_time
                self.world.send_message(f"door_opened#{self.id}")
        
        elif self.state == ElevatorState.DOOR_CLOSING:
            if current_time - self.last_state_change > 1.0:  # 1 second to close door
                self.door_state = DoorState.CLOSED
                self.state = ElevatorState.DOOR_CLOSED
                self.last_state_change = current_time
                self.world.send_message(f"door_closed#{self.id}")
                
                # Request movement if we have target floors
                self.request_movement_if_needed()
        
        elif self.state == ElevatorState.DOOR_CLOSED:
            # Request movement if we have target floors
            self.request_movement_if_needed()

    def _handle_floor_arrival(self) -> None:
        """Handle logic for arriving at a floor"""
        # Determine direction string based on current state
        direction_str: str = "up_" if self.state == ElevatorState.MOVING_UP else "down_" if self.state == ElevatorState.MOVING_DOWN else "up_"
        
        # Notify arrival
        self.world.send_message(f"{direction_str}floor_arrived@{self.current_floor}#{self.id}")
        
        # If this is a target floor, remove it and open door
        if self.current_floor in self.target_floors:
            self.target_floors.remove(self.current_floor)
            print(f"Elevator {self.id} target sequence: {self.target_floors}")
            self.open_door()

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
            self.last_state_change = self.moving_since
    
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
        if self.door_state != DoorState.OPEN and self.state != ElevatorState.DOOR_OPENING:
            self.state = ElevatorState.DOOR_OPENING
            self.door_state = DoorState.OPENING
            self.last_state_change = time.time()
    
    def close_door(self) -> None:
        if self.door_state != DoorState.CLOSED and self.state != ElevatorState.DOOR_CLOSING:
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
        elif self.direction == "up" and any(floor > self.current_floor for floor in self.target_floors):
            self.direction = "up"
        # If current direction is down, keep going down until no more floors below
        elif self.direction == "down" and any(floor < self.current_floor for floor in self.target_floors):
            self.direction = "down"
        # Otherwise pick the closest floor
        else:
            closest_above: Optional[int] = min([f for f in self.target_floors if f > self.current_floor], default=None)
            closest_below: Optional[int] = max([f for f in self.target_floors if f < self.current_floor], default=None)
            
            if closest_above and closest_below:
                self.direction = "up" if closest_above - self.current_floor <= self.current_floor - closest_below else "down"
            elif closest_above:
                self.direction = "up"
            else:
                self.direction = "down"
    
    def calculate_estimated_time(self, floor: int, direction: str) -> float:
        # Calculate estimated time to service a request at floor with given direction
        if self.current_floor == floor and self.door_state in [DoorState.OPEN, DoorState.OPENING]:
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
                for target in sorted([f for f in simulated_targets if f > self.current_floor]):
                    total_time += abs(target - self.current_floor) * self.floor_travel_time
                    self.current_floor = target  # Simulated position
                    
                    # If this is our requested floor with matching direction
                    if target == floor and (direction == "up" or direction == ""):
                        return total_time
                
                # Then handle all floors below in descending order
                for target in sorted([f for f in simulated_targets if f < self.current_floor], reverse=True):
                    total_time += abs(target - self.current_floor) * self.floor_travel_time
                    self.current_floor = target  # Simulated position
                    
                    # If this is our requested floor with matching direction
                    if target == floor and (direction == "down" or direction == ""):
                        return total_time
            else:
                # First handle all floors below current in descending order
                for target in sorted([f for f in simulated_targets if f < self.current_floor], reverse=True):
                    total_time += abs(target - self.current_floor) * self.floor_travel_time
                    self.current_floor = target  # Simulated position
                    
                    # If this is our requested floor with matching direction
                    if target == floor and (direction == "down" or direction == ""):
                        return total_time
                
                # Then handle all floors above in ascending order
                for target in sorted([f for f in simulated_targets if f > self.current_floor]):
                    total_time += abs(target - self.current_floor) * self.floor_travel_time
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

class Dispatcher:
    def __init__(self, world: 'World') -> None:
        self.world: 'World' = world
        self.last_message_timestamp: int = -1
    
    def update(self) -> None:
        # Process all pending messages in the queue
        while True:
            message, timestamp = self.world.client.get_next_message()
            if message == "" or timestamp == -1:
                break  # No more messages in the queue
            
            # Update timestamp for backward compatibility
            self.last_message_timestamp = timestamp
            
            # Handle the message
            if message:
                self.handle_request(message)
    
    def handle_request(self, request: str) -> None:
        if request.startswith("open_door"):
            elevator_id: int = int(request.split("#")[1])
            self.world.elevators[elevator_id - 1].open_door()
        
        elif request.startswith("close_door"):
            elevator_id: int = int(request.split("#")[1])
            self.world.elevators[elevator_id - 1].close_door()
        
        elif request.startswith("call_up"):
            floor: int = int(request.split("@")[1])
            self._assign_elevator(floor, "up")
        
        elif request.startswith("call_down"):
            floor: int = int(request.split("@")[1])
            self._assign_elevator(floor, "down")
        
        elif request.startswith("select_floor"):
            parts: List[str] = request.split("@")[1].split("#")
            floor: int = int(parts[0])
            elevator_id: int = int(parts[1])
            self._add_target_floor(elevator_id - 1, floor)
        
        elif request == "reset":
            for elevator in self.world.elevators:
                elevator.reset()
    
    def _assign_elevator(self, floor: int, direction: str) -> None:
        # Find the elevator that can service the request with minimal estimated time
        best_elevator: Optional[Elevator] = None
        min_time: float = float('inf')
        
        for elevator in self.world.elevators:
            est_time: float = elevator.calculate_estimated_time(floor, direction)
            if est_time < min_time:
                min_time = est_time
                best_elevator = elevator
        
        if best_elevator:
            self._add_target_floor(best_elevator.id - 1, floor)
    
    def _add_target_floor(self, elevator_idx: int, floor: int) -> None:
        """Add target floor to elevator and optimize the sequence"""
        elevator = self.world.elevators[elevator_idx]
        
        # Skip if already in target list or currently at this floor
        if floor in elevator.target_floors:
            return
        
        # Add floor to target list
        elevator.target_floors.append(floor)
        
        # Optimize the sequence for efficiency
        self._optimize_target_sequence(elevator)
        print(f"Elevator {elevator.id} target sequence: {elevator.target_floors}")
        
        # If door is open, close it to start moving
        if elevator.door_state == DoorState.OPEN:
            elevator.close_door()
        else:
            # Request movement if possible
            elevator.request_movement_if_needed()
    
    def _optimize_target_sequence(self, elevator: Elevator) -> None:
        """Optimize the sequence of target floors for efficiency"""
        pass

class Engine:
    def __init__(self, world: 'World') -> None:
        self.world: 'World' = world
        self.movement_requests: Dict[int, str] = {}  # elevator_id -> direction
    
    def request_movement(self, request: MoveRequest) -> None:
        """Process movement request from an elevator"""
        self.movement_requests[request.elevator_id] = request.direction
        # Set the elevator's state according to the requested direction
        elevator = self.world.elevators[request.elevator_id - 1]
        elevator.set_moving_state(request.direction)
    
    def update(self) -> None:
        current_time: float = time.time()
        
        # Process each elevator's movement
        for elevator in self.world.elevators:
            # Check if elevator is moving and has a movement request
            if elevator.is_moving() and elevator.id in self.movement_requests and elevator.moving_since is not None:
                # Check if enough time has passed to reach next floor
                if current_time - elevator.moving_since >= elevator.floor_travel_time:
                    # Determine the next floor based on direction
                    direction = elevator.get_movement_direction()
                    next_floor = elevator.current_floor + direction
                    
                    # Update elevator's floor
                    elevator.set_floor(next_floor)
                    
                    # Remove the request once processed
                    if not elevator.target_floors or next_floor == elevator.target_floors[0]:
                        self.movement_requests.pop(elevator.id, None)

class World:
    def __init__(self) -> None:
        self.client: ZmqClientThread = ZmqClientThread(identity="Team17")
        self.engine: Engine = Engine(self)  # Create engine first
        self.elevators: List[Elevator] = [Elevator(1, self), Elevator(2, self)]
        self.dispatcher: Dispatcher = Dispatcher(self)
        
        time.sleep(1)  # Give time for the client to connect
    
    def update(self) -> None:
        self.dispatcher.update()  # Process user requests

        for elevator in self.elevators:
            elevator.update()
        
        self.engine.update()      # Process movement
        
    
    def send_message(self, message: str) -> None:
        self.client.sendMsg(message)
    
    def run(self) -> None:
        try:
            while True:
                self.update()
                time.sleep(0.01)  # 10ms update interval
        except KeyboardInterrupt:
            print("Elevator simulation terminated.")

if __name__ == "__main__":
    world: World = World()
    world.run()

