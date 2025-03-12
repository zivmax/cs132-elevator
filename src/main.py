import os
import time
import sys
from enum import Enum, auto
from typing import List, Optional, Dict, Union, Set, Any
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
        self.moving_since: Optional[float] = None  # Timestamp when movement started (used by Engine)
        self.floor_changed: bool = False  # Flag to detect floor changes

    def update(self) -> None:
        current_time: float = time.time()
        
        # Check if floor has changed (set by Engine)
        if self.floor_changed:
            self.floor_changed = False
            
            # Notify that we've arrived at a floor
            direction_str: str = "up_" if self.state == ElevatorState.MOVING_UP else "down_" if self.state == ElevatorState.MOVING_DOWN else ""
            self.world.send_message(f"{direction_str}floor_arrived@{self.current_floor}#{self.id}")
            
            # Check if we've reached a target floor
            if self.current_floor in self.target_floors:
                self.target_floors.remove(self.current_floor)
                self.open_door()
            else:
                # Continue moving if we have more target floors
                if self.target_floors:
                    self._determine_direction()
                    # Update state if direction changed
                    if self.direction == "up" and self.state != ElevatorState.MOVING_UP:
                        self.state = ElevatorState.MOVING_UP
                    elif self.direction == "down" and self.state != ElevatorState.MOVING_DOWN:
                        self.state = ElevatorState.MOVING_DOWN
                else:
                    # No more target floors, stop and open door
                    self.open_door()
        
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
                
                # If we have target floors, start moving
                if self.target_floors:
                    self._determine_direction()
                    if self.direction == "up":
                        self.state = ElevatorState.MOVING_UP
                        self.moving_since = current_time
                    else:
                        self.state = ElevatorState.MOVING_DOWN
                        self.moving_since = current_time
                    self.last_state_change = current_time
                else:
                    self.state = ElevatorState.IDLE
        
        elif self.state == ElevatorState.DOOR_CLOSED:
            # If we have target floors, start moving
            if self.target_floors:
                self._determine_direction()
                if self.direction == "up":
                    self.state = ElevatorState.MOVING_UP
                    self.moving_since = current_time
                else:
                    self.state = ElevatorState.MOVING_DOWN
                    self.moving_since = current_time
                self.last_state_change = current_time
    
    def set_floor(self, new_floor: int) -> None:
        """Called by Engine to update the elevator's floor position"""
        if self.current_floor != new_floor:
            self.previous_floor = self.current_floor
            self.current_floor = new_floor
            self.floor_changed = True  # Set flag to process floor change in next update
            self.moving_since = time.time()  # Reset moving timer for next floor
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
    
    def add_target_floor(self, floor: int) -> None:
        if floor not in self.target_floors and floor != self.current_floor:
            self.target_floors.append(floor)
            self.target_floors.sort()  # Sort for more efficient path planning
            
            # If we're idle and door is closed, start moving
            if self.state == ElevatorState.IDLE and self.door_state == DoorState.CLOSED:
                self._determine_direction()
                if self.direction == "up":
                    self.state = ElevatorState.MOVING_UP
                    self.moving_since = time.time()

                else:
                    self.state = ElevatorState.MOVING_DOWN
                    self.moving_since = time.time()
                self.last_state_change = time.time()
            
            # If door is open, close it to start moving
            elif self.state == ElevatorState.DOOR_OPEN:
                self.close_door()
        
        # If selecting current floor and door is closed, send arrival notification and open door
        elif floor == self.current_floor and self.door_state == DoorState.CLOSED:
            # Send floor arrival notification first
            direction_str: str = "up_"  # Default direction when already at floor
            self.world.send_message(f"{direction_str}floor_arrived@{self.current_floor}#{self.id}")
            # Then open the door
            self.open_door()
    
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
        
        # If elevator is idle
        if self.state == ElevatorState.IDLE:
            return abs(self.current_floor - floor) * self.floor_travel_time
        
        # If elevator is already moving in the same direction
        if (self.direction == "up" and direction == "up" and self.current_floor < floor) or \
           (self.direction == "down" and direction == "down" and self.current_floor > floor):
            return abs(self.current_floor - floor) * self.floor_travel_time
        
        # If elevator needs to finish current journey and reverse
        else:
            # Find furthest floor in current direction
            if self.target_floors:
                furthest: int = max(self.target_floors) if self.direction == "up" else min(self.target_floors)
                return (abs(self.current_floor - furthest) + abs(furthest - floor)) * self.floor_travel_time
            else:
                return abs(self.current_floor - floor) * self.floor_travel_time
    
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
        # Check for new messages
        if self.world.client.messageTimeStamp != self.last_message_timestamp:
            self.last_message_timestamp = self.world.client.messageTimeStamp
            message: str = self.world.client.receivedMessage
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
            self.world.elevators[elevator_id - 1].add_target_floor(floor)
        
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
            best_elevator.add_target_floor(floor)

class Engine:
    def __init__(self, world: 'World') -> None:
        self.world: 'World' = world
    
    def update(self) -> None:
        current_time: float = time.time()
        
        # Update each elevator's physical position
        for elevator in self.world.elevators:
            # Check if elevator is moving and should reach next floor
            if elevator.is_moving() and elevator.moving_since is not None:
                # Check if enough time has passed to reach next floor
                if current_time - elevator.moving_since >= elevator.floor_travel_time:
                    # Determine the next floor based on direction
                    direction: int = elevator.get_movement_direction()
                    next_floor: int = elevator.current_floor + direction
                    
                    # Update elevator's floor (elevator will handle notifications)
                    elevator.set_floor(next_floor)

class World:
    def __init__(self) -> None:
        self.client: ZmqClientThread = ZmqClientThread(identity="Team17")
        self.elevators: List[Elevator] = [Elevator(1, self), Elevator(2, self)]
        self.dispatcher: Dispatcher = Dispatcher(self)
        self.engine: Engine = Engine(self)
        
        time.sleep(1)  # Give time for the client to connect
    
    def update(self) -> None:
        # Update each component
        for elevator in self.elevators:
            elevator.update()
        
        # Update the dispatcher (which handles messages)
        self.dispatcher.update()
        
        # Update the engine
        self.engine.update()
    
    def handle_message(self, message: str) -> None:
        self.dispatcher.handle_request(message)
    
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

