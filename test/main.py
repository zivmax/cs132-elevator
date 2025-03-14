import sys
import os
import server
import time
import random
from enum import IntEnum
from typing import List, Optional, Dict, Any, Tuple


#######   ELEVATOR PROJECT    #######


### Simple Test Case ###
class PassengerState(IntEnum):
    # only for reference, it may be complex in other testcase.
    IN_ELEVATOR_1_AT_TARGET_FLOOR = 1
    IN_ELEVATOR_1_AT_OTHER_FLOOR = 2
    IN_ELEVATOR_2_AT_TARGET_FLOOR = 3
    IN_ELEVATOR_2_AT_OTHER_FLOOR = 4
    OUT_ELEVATOR_0_AT_TARGET_FLOOR = 5
    OUT_ELEVATOR_0_AT_OTHER_FLOOR = 6


class Passenger:
    def __init__(self, start_floor: int, target_floor: int, name: str = "test", delay: float = 0) -> None:
        self.start_floor: int = start_floor
        self.target_floor: int = target_floor
        self.direction: str = "up" if self.target_floor > self.start_floor else "down"
        self._elevator_code: int = -1
        self.current_floor: int = start_floor
        self.finished: bool = False if self.target_floor != self.start_floor else True
        self.finished_print: bool = False
        self.name: str = name
        self.matching_signal: str = (
            f"up_floor_arrived@{self.current_floor}"
            if self.direction == "up"
            else f"down_floor_arrived@{self.current_floor}"
        )
        self.state: PassengerState = PassengerState.OUT_ELEVATOR_0_AT_OTHER_FLOOR
        self.delay: float = delay  # Time to wait before calling elevator
        self.has_called_elevator: bool = False
        self.arrival_time: Optional[float] = None  # To track when passenger completed journey
        self.start_time: Optional[float] = None  # When passenger started journey

    def change_state(self, target_state: PassengerState) -> None:
        self.state = target_state

    def is_finished(self) -> bool:
        return self.finished

    def set_elevator_code(self, value: int) -> None:
        self._elevator_code = value

    def get_elevator_code(self) -> int:
        return self._elevator_code

    def __str__(self) -> str:
        return f"Passenger {self.name} (Floor {self.start_floor} → {self.target_floor}, Direction: {self.direction})"


class TestScenario:
    def __init__(self, name: str, passengers: List[Passenger], description: str = ""):
        self.name = name
        self.passengers = passengers
        self.description = description


def create_test_scenarios() -> Dict[str, TestScenario]:
    scenarios = {}
    
    # Basic scenario - single passenger
    passengers = [Passenger(1, 3, "A")]
    scenarios["basic"] = TestScenario("Basic Test", passengers, 
                                     "Single passenger going from floor 1 to floor 3")
    
    # Multiple passengers - same direction
    passengers = [
        Passenger(1, 5, "A"),
        Passenger(2, 4, "B", delay=1.0),
        Passenger(3, 6, "C", delay=2.0)
    ]
    scenarios["same_direction"] = TestScenario("Same Direction Test", passengers, 
                                              "Multiple passengers going up from different floors")
    
    # Multiple passengers - opposite directions
    passengers = [
        Passenger(1, 5, "A"),
        Passenger(6, 2, "B", delay=0.5),
        Passenger(3, 1, "C", delay=1.0),
        Passenger(2, 6, "D", delay=1.5)
    ]
    scenarios["mixed_directions"] = TestScenario("Mixed Directions Test", passengers, 
                                               "Passengers going both up and down from different floors")
    
    # Heavy traffic scenario
    passengers = [
        Passenger(1, 6, "A"),
        Passenger(2, 5, "B", delay=0.2),
        Passenger(3, 1, "C", delay=0.4),
        Passenger(5, 2, "D", delay=0.6),
        Passenger(4, 6, "E", delay=0.8),
        Passenger(6, 3, "F", delay=1.0),
        Passenger(2, 4, "G", delay=1.2),
        Passenger(1, 5, "H", delay=1.4),
    ]
    scenarios["heavy_traffic"] = TestScenario("Heavy Traffic Test", passengers, 
                                             "Many passengers calling elevators in quick succession")
    
    # Same floor pickup scenario
    passengers = [
        Passenger(1, 5, "A"),
        Passenger(1, 3, "B", delay=0.1),
        Passenger(1, 6, "C", delay=0.2),
        Passenger(5, 1, "D", delay=2.0),
    ]
    scenarios["same_floor_pickup"] = TestScenario("Same Floor Pickup Test", passengers, 
                                                "Multiple passengers calling from the same floor")
    
    # Random stress test
    passengers = []
    floor_count = 10  # Assuming 10 floors
    for i in range(15):  # 15 random passengers
        start = random.randint(1, floor_count)
        target = random.randint(1, floor_count)
        while target == start:  # Ensure different start and target
            target = random.randint(1, floor_count)
        passengers.append(Passenger(start, target, chr(65 + i), delay=random.uniform(0, 3)))
    scenarios["random_stress"] = TestScenario("Random Stress Test", passengers, 
                                            "Random passenger patterns to stress test the system")
    
    return scenarios


def testing(server: server.ZmqServerThread, selected_scenario: str = "basic") -> None:
    def is_received_new_message(
        oldTimeStamp: int, oldServerMessage: str, Msgunprocessed: bool = False
    ) -> bool:
        if Msgunprocessed:
            return True
        else:
            if (
                oldTimeStamp == server.messageTimeStamp
                and oldServerMessage == server.receivedMessage
            ):
                return False
            else:
                return True

    ############ Initialize Test Scenario ############
    scenarios = create_test_scenarios()
    if selected_scenario not in scenarios:
        print(f"Unknown scenario: {selected_scenario}. Defaulting to basic test.")
        selected_scenario = "basic"
    
    current_scenario = scenarios[selected_scenario]
    passengers = current_scenario.passengers
    
    print(f"\n=== STARTING TEST SCENARIO: {current_scenario.name} ===")
    print(f"Description: {current_scenario.description}")
    print(f"Passengers: {len(passengers)}")
    for p in passengers:
        print(f"  - {p}")
    print("=" * 60 + "\n")
    
    timeStamp: int = -1  # default time stamp is -1
    clientMessage: str = ""  # default received message is ""
    messageUnprocessed: bool = False  # Used when receiving new message
    count: int = 0
    test_start_time = time.time()
    
    # Reset the client
    server.send_string(server.bindedClient, "reset")
    time.sleep(1)
    
    # Recording metrics
    elevator_usage = {1: 0, 2: 0}  # Count how many times each elevator is used
    passenger_wait_times = []
    passenger_journey_times = []

    ############ Passenger timed automata ############
    while True:
        current_time = time.time()
        elapsed_time = current_time - test_start_time
        
        # Call elevators for passengers with expired delay
        for passenger in passengers:
            if not passenger.has_called_elevator and elapsed_time >= passenger.delay:
                if passenger.direction == "up":
                    server.send_string(server.bindedClient, f"call_up@{passenger.start_floor}")
                else:
                    server.send_string(server.bindedClient, f"call_down@{passenger.start_floor}")
                passenger.has_called_elevator = True
                passenger.start_time = current_time
                print(f"[{elapsed_time:.1f}s] {passenger.name} called the elevator at floor {passenger.start_floor} going {passenger.direction}")

        for each_passenger in passengers:
            if not each_passenger.has_called_elevator:
                continue  # Skip passengers who haven't called an elevator yet
                
            match each_passenger.state:
                case PassengerState.IN_ELEVATOR_1_AT_OTHER_FLOOR:
                    if is_received_new_message(timeStamp, clientMessage, messageUnprocessed):
                        if not messageUnprocessed:
                            timeStamp = server.messageTimeStamp
                            clientMessage = server.receivedMessage
                        messageUnprocessed = False
                        if clientMessage.endswith(
                            f"floor_arrived@{each_passenger.target_floor}#{each_passenger.get_elevator_code()}"
                        ):
                            each_passenger.current_floor = each_passenger.target_floor
                            each_passenger.change_state(
                                PassengerState.IN_ELEVATOR_1_AT_TARGET_FLOOR
                            )
                            print(f"[{elapsed_time:.1f}s] Elevator {each_passenger.get_elevator_code()} arrived at target floor {each_passenger.target_floor} with passenger {each_passenger.name}")

                case PassengerState.IN_ELEVATOR_1_AT_TARGET_FLOOR:
                    if is_received_new_message(timeStamp, clientMessage, messageUnprocessed):
                        if not messageUnprocessed:
                            timeStamp = server.messageTimeStamp
                            clientMessage = server.receivedMessage
                        messageUnprocessed = False
                        if clientMessage == f"door_opened#{each_passenger.get_elevator_code()}":
                            print(
                                f"[{elapsed_time:.1f}s] Passenger {each_passenger.name} is leaving elevator {each_passenger.get_elevator_code()} at floor {each_passenger.target_floor}"
                            )
                            each_passenger.change_state(
                                PassengerState.OUT_ELEVATOR_0_AT_TARGET_FLOOR
                            )
                            each_passenger.finished = True
                            each_passenger.arrival_time = current_time

                case PassengerState.IN_ELEVATOR_2_AT_OTHER_FLOOR:
                    if is_received_new_message(timeStamp, clientMessage, messageUnprocessed):
                        if not messageUnprocessed:
                            timeStamp = server.messageTimeStamp
                            clientMessage = server.receivedMessage
                        messageUnprocessed = False
                        if clientMessage.endswith(
                            f"floor_arrived@{each_passenger.target_floor}#{each_passenger.get_elevator_code()}"
                        ):
                            each_passenger.current_floor = each_passenger.target_floor
                            each_passenger.change_state(
                                PassengerState.IN_ELEVATOR_2_AT_TARGET_FLOOR
                            )
                            print(f"[{elapsed_time:.1f}s] Elevator {each_passenger.get_elevator_code()} arrived at target floor {each_passenger.target_floor} with passenger {each_passenger.name}")

                case PassengerState.IN_ELEVATOR_2_AT_TARGET_FLOOR:
                    if is_received_new_message(timeStamp, clientMessage, messageUnprocessed):
                        if not messageUnprocessed:
                            timeStamp = server.messageTimeStamp
                            clientMessage = server.receivedMessage
                        messageUnprocessed = False
                        if clientMessage == f"door_opened#{each_passenger.get_elevator_code()}":
                            print(
                                f"[{elapsed_time:.1f}s] Passenger {each_passenger.name} is leaving elevator {each_passenger.get_elevator_code()} at floor {each_passenger.target_floor}"
                            )
                            each_passenger.change_state(
                                PassengerState.OUT_ELEVATOR_0_AT_TARGET_FLOOR
                            )
                            each_passenger.finished = True
                            each_passenger.arrival_time = current_time

                case PassengerState.OUT_ELEVATOR_0_AT_OTHER_FLOOR:
                    if is_received_new_message(timeStamp, clientMessage, messageUnprocessed):
                        if not messageUnprocessed:
                            timeStamp = server.messageTimeStamp
                            clientMessage = server.receivedMessage
                        messageUnprocessed = False
                        if (
                            clientMessage.startswith(each_passenger.matching_signal)
                            and each_passenger.current_floor == each_passenger.start_floor
                        ):
                            elevator_code = int(clientMessage.split("#")[-1])
                            each_passenger.set_elevator_code(elevator_code)
                            elevator_usage[elevator_code] += 1
                            print(f"[{elapsed_time:.1f}s] Elevator {elevator_code} arrived for passenger {each_passenger.name} at floor {each_passenger.current_floor}")

                        if (
                            clientMessage
                            == f"door_opened#{each_passenger.get_elevator_code()}"
                            and each_passenger.get_elevator_code() > 0
                        ):
                            print(
                                f"[{elapsed_time:.1f}s] Passenger {each_passenger.name} is entering elevator {each_passenger.get_elevator_code()} at floor {each_passenger.current_floor}"
                            )
                            time.sleep(0.5)  # Reduced delay for faster testing
                            if each_passenger.get_elevator_code() == 1:
                                each_passenger.change_state(
                                    PassengerState.IN_ELEVATOR_1_AT_OTHER_FLOOR
                                )
                            elif each_passenger.get_elevator_code() == 2:
                                each_passenger.change_state(
                                    PassengerState.IN_ELEVATOR_2_AT_OTHER_FLOOR
                                )
                            server.send_string(
                                server.bindedClient,
                                f"select_floor@{each_passenger.target_floor}#{each_passenger.get_elevator_code()}",
                            )
                            print(f"[{elapsed_time:.1f}s] Passenger {each_passenger.name} selected floor {each_passenger.target_floor}")

                case PassengerState.OUT_ELEVATOR_0_AT_TARGET_FLOOR:
                    if each_passenger.is_finished() and not each_passenger.finished_print:
                        journey_time = each_passenger.arrival_time - each_passenger.start_time
                        print(
                            f"[{elapsed_time:.1f}s] Passenger {each_passenger.name} completed journey from floor {each_passenger.start_floor} to {each_passenger.target_floor} in {journey_time:.1f}s"
                        )
                        each_passenger.finished_print = True
                        passenger_journey_times.append(journey_time)
                        count += 1

        if count == len([p for p in passengers if p.has_called_elevator]):
            all_done = True
            for p in passengers:
                if not p.has_called_elevator:
                    all_done = False
                    break
            if all_done:
                print("\n=== TEST COMPLETED SUCCESSFULLY ===")
                print(f"Total test time: {elapsed_time:.1f} seconds")
                print(f"Elevator usage: Elevator 1: {elevator_usage[1]}, Elevator 2: {elevator_usage[2]}")
                if passenger_journey_times:
                    avg_time = sum(passenger_journey_times) / len(passenger_journey_times)
                    print(f"Average journey time: {avg_time:.1f} seconds")
                print("=" * 60)
                time.sleep(1)
                server.send_string(server.bindedClient, "reset")
                break

        time.sleep(0.01)


if __name__ == "__main__":
    my_server: server.ZmqServerThread = server.ZmqServerThread()
    
    # Display available test scenarios
    scenarios = create_test_scenarios()
    print("\nAvailable test scenarios:")
    for key, scenario in scenarios.items():
        print(f"  - {key}: {scenario.name}")
    
    while True:
        if len(my_server.clients_addr) == 0:
            continue
        elif len(my_server.clients_addr) >= 2:
            print("More than 1 client address stored. Server will exit")
            sys.exit()
        else:
            addr: str = list(my_server.clients_addr)[0]
            print(f"\nClient connected: {addr}")
            
            # Prompt for test scenario
            scenario = input("Select test scenario (or 'exit' to quit): ")
            if scenario.lower() == 'exit':
                print("Exiting...")
                sys.exit()
            
            if scenario not in scenarios:
                print(f"Unknown scenario: {scenario}. Available scenarios: {', '.join(scenarios.keys())}")
                continue
            
            msg: str = input(f"Initiate '{scenarios[scenario].name}' for {addr}? (y/n)\n")
            if msg.lower() == "y":
                my_server.bindedClient = addr
                testing(my_server, scenario)
            else:
                continue
