import os
import time
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from net_client import ZmqClientThread
from elevator import ElevatorState
from scheduler import Scheduler


# This function determines whether a new message has been received
def is_received_new_message(
    oldTimeStamp: int, oldServerMessage: str, Msgunprocessed: bool = False
) -> bool:
    if Msgunprocessed:
        return True
    else:
        if (
            oldTimeStamp == zmqThread.messageTimeStamp
            and oldServerMessage == zmqThread.receivedMessage
        ):
            return False
        else:
            return True


if __name__ == "__main__":
    # Connect to the server
    identity = "Team18"  # Your team name
    zmqThread = ZmqClientThread(identity=identity)

    # Initialize tracking variables
    timeStamp = -1
    serverMessage = ""
    messageUnprocessed = False

    # Initialize elevator scheduler
    scheduler = Scheduler()

    # Elevator control loop
    while True:
        # Check for new messages
        if is_received_new_message(timeStamp, serverMessage, messageUnprocessed):
            if not messageUnprocessed:
                timeStamp = zmqThread.messageTimeStamp
                serverMessage = zmqThread.receivedMessage
                print(f"Received: {serverMessage}")  # Debug
            messageUnprocessed = False

            # Process messages
            if serverMessage.startswith("call_up@"):
                floor = serverMessage.split("@")[1]
                scheduler.call_up(floor)

            elif serverMessage.startswith("call_down@"):
                floor = serverMessage.split("@")[1]
                scheduler.call_down(floor)

            elif serverMessage.startswith("select_floor@"):
                parts = serverMessage.split("@")[1].split("#")
                floor = parts[0]
                elevator_id = parts[1]
                scheduler.select_floor(floor, elevator_id)

            elif serverMessage == "reset":
                scheduler.reset()
                timeStamp = -1
                serverMessage = ""
                messageUnprocessed = False

            elif serverMessage == "open_door":
                target_elevator_id = scheduler.last_elevator
                target_elevator = scheduler.elevators[target_elevator_id]
                if target_elevator.state == ElevatorState.STOPPED_DOOR_CLOSED:
                    zmqThread.sendMsg(f"door_opened#{target_elevator_id}")
                    target_elevator.state = ElevatorState.STOPPED_OPENING_DOOR

            elif serverMessage == "close_door":
                target_elevator_id = scheduler.last_elevator
                target_elevator = scheduler.elevators[target_elevator_id]
                if target_elevator.state == ElevatorState.STOPPED_DOOR_OPENED:
                    zmqThread.sendMsg(f"door_closed#{target_elevator_id}")
                    target_elevator.state = ElevatorState.STOPPED_DOOR_CLOSED

        # Process each elevator based on its state
        for elevator_id, elevator in scheduler.elevators.items():
            match elevator.state:
                case ElevatorState.STOPPED_DOOR_CLOSED:
                    # If we have target floors, start moving
                    if elevator.target_floors:
                        elevator.direction = elevator.decide_direction()
                        if elevator.direction == "up":
                            elevator.state = ElevatorState.UP
                        elif elevator.direction == "down":
                            elevator.state = ElevatorState.DOWN
                        elif elevator.direction is None:
                            # No direction, stop at current floor
                            zmqThread.sendMsg(
                                f"floor_arrived@,{elevator.current_floor},#{elevator_id}"
                            )
                            elevator.state = ElevatorState.STOPPED_OPENING_DOOR

                case ElevatorState.UP:
                    # Simulate elevator moving up
                    next_floor = scheduler.next_floor(elevator_id)
                    if next_floor is not None:
                        # Check if we're at the next floor or need to move
                        if elevator.current_floor < next_floor:
                            # Moving to next floor up
                            new_floor = elevator.current_floor + 1
                            zmqThread.sendMsg(
                                f"floor_arrived@up,{new_floor}#{elevator_id}"
                            )
                            elevator.current_floor = new_floor

                            # Check if we should stop at this floor
                            if scheduler.floor_arrived("up", new_floor, elevator_id):
                                elevator.state = ElevatorState.STOPPED_OPENING_DOOR
                        else:
                            # We've reached or passed our target
                            elevator.state = ElevatorState.STOPPED_OPENING_DOOR
                    else:
                        # No more targets, stop at current floor
                        zmqThread.sendMsg(
                            f"floor_arrived@,{elevator.current_floor},#{elevator_id}"
                        )
                        elevator.direction = None
                        elevator.state = ElevatorState.STOPPED_OPENING_DOOR

                case ElevatorState.DOWN:
                    # Simulate elevator moving down
                    next_floor = scheduler.next_floor(elevator_id)
                    if next_floor is not None:
                        # Check if we're at the next floor or need to move
                        if elevator.current_floor > next_floor:
                            # Moving to next floor down
                            new_floor = elevator.current_floor - 1
                            zmqThread.sendMsg(
                                f"floor_arrived@down,{new_floor}#{elevator_id}"
                            )
                            elevator.current_floor = new_floor

                            # Check if we should stop at this floor
                            if scheduler.floor_arrived("down", new_floor, elevator_id):
                                elevator.state = ElevatorState.STOPPED_OPENING_DOOR
                        else:
                            # We've reached or passed our target
                            elevator.state = ElevatorState.STOPPED_OPENING_DOOR
                    else:
                        # No more targets, stop at current floor
                        zmqThread.sendMsg(
                            f"floor_arrived@,{elevator.current_floor},#{elevator_id}"
                        )
                        elevator.direction = None
                        elevator.state = ElevatorState.STOPPED_OPENING_DOOR

                case ElevatorState.STOPPED_OPENING_DOOR:
                    # Open the door
                    zmqThread.sendMsg(f"door_opened#{elevator_id}")
                    elevator.state = ElevatorState.STOPPED_DOOR_OPENED
                    # Start a timer to close the door after a delay
                    elevator.door_timer = time.time()

                case ElevatorState.STOPPED_DOOR_OPENED:
                    # After a delay, close the door
                    if (
                        time.time() - getattr(elevator, "door_timer", 0) > 2.0
                    ):  # 2 second delay
                        zmqThread.sendMsg(f"door_closed#{elevator_id}")
                        elevator.state = ElevatorState.STOPPED_DOOR_CLOSED

                        # Check for new direction
                        elevator.direction = elevator.decide_direction()
                        if elevator.direction == "up":
                            elevator.state = ElevatorState.UP
                        elif elevator.direction == "down":
                            elevator.state = ElevatorState.DOWN

        time.sleep(0.1)  # Small delay to prevent high CPU usage
