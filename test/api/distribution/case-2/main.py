import sys
import os
import server
import time
import random
from enum import IntEnum

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
    def __init__(self, start_floor, target_floor, name="test"):
        self.start_floor: int = start_floor
        self.target_floor: int = target_floor
        self.direction = "up" if self.target_floor > self.start_floor else "down"
        self._elevator_code = -1
        self.current_floor = start_floor
        self.finished = False if self.target_floor != self.start_floor else True
        self.finished_print = False
        self.name = name
        self.matching_signal = (
            f"up_floor_arrived@{self.current_floor}"
            if self.direction == "up"
            else f"down_floor_arrived@{self.current_floor}"
        )
        self.state = PassengerState.OUT_ELEVATOR_0_AT_OTHER_FLOOR

    def change_state(self, target_state: PassengerState) -> str:
        self.state = target_state

    def is_finished(self):
        return self.finished

    def set_elevator_code(self, value):
        self._elevator_code = value

    def get_elevator_code(self):
        return self._elevator_code


def testing(server: server.ZmqServerThread):
    ############ Initialize Passengers ############
    passengers = [Passenger(-1, 3, "A"), Passenger(3, 1, "B")]
    timestamp = -1  # default time stamp is -1
    client_message = ""  # default received message is ""
    count = 0
    server.send_string(server.bound_client, "reset")  # Reset the client
    server.send_string(server.bound_client, "call_up@-1")
    server.send_string(server.bound_client, "call_down@3")

    def is_received_new_message(
        old_timestamp: int, old_server_message: str, msg_unprocessed: bool = False
    ) -> bool:
        if msg_unprocessed:
            return True
        else:
            tmp_msg = server.received_message
            tmp_ts = server.message_timestamp

            if old_timestamp == tmp_ts and old_server_message == tmp_msg:
                return False
            else:
                nonlocal timestamp, client_message
                timestamp = tmp_ts
                client_message = tmp_msg
                return True

    ############ Passenger timed automata ############
    while True:
        has_new_message = is_received_new_message(timestamp, client_message)
        if has_new_message:
            for passenger in passengers:
                if passenger.state == PassengerState.IN_ELEVATOR_1_AT_OTHER_FLOOR:
                    if client_message.endswith(
                        f"floor_arrived@{passenger.target_floor}#{passenger.get_elevator_code()}"
                    ):
                        passenger.current_floor = passenger.target_floor
                        passenger.change_state(
                            PassengerState.IN_ELEVATOR_1_AT_TARGET_FLOOR
                        )
                        continue
                elif passenger.state == PassengerState.IN_ELEVATOR_1_AT_TARGET_FLOOR:
                    if client_message == f"door_opened#1":
                        print(f"Passenger {passenger.name} is Leaving the elevator")
                        passenger.change_state(
                            PassengerState.OUT_ELEVATOR_0_AT_TARGET_FLOOR
                        )
                        passenger.finished = True
                        continue
                elif passenger.state == PassengerState.IN_ELEVATOR_2_AT_OTHER_FLOOR:
                    if client_message.endswith(
                        f"floor_arrived@{passenger.target_floor}#{passenger.get_elevator_code()}"
                    ):
                        passenger.current_floor = passenger.target_floor
                        passenger.change_state(
                            PassengerState.IN_ELEVATOR_2_AT_TARGET_FLOOR
                        )
                        continue
                elif passenger.state == PassengerState.IN_ELEVATOR_2_AT_TARGET_FLOOR:
                    if client_message == f"door_opened#2":
                        print(f"Passenger {passenger.name} is Leaving the elevator")
                        passenger.change_state(
                            PassengerState.OUT_ELEVATOR_0_AT_TARGET_FLOOR
                        )
                        passenger.finished = True
                        continue
                elif passenger.state == PassengerState.OUT_ELEVATOR_0_AT_OTHER_FLOOR:
                    if (
                        client_message.startswith(passenger.matching_signal)
                        and passenger.current_floor == passenger.start_floor
                    ):
                        if passenger.get_elevator_code() == -1:
                            passenger.set_elevator_code(
                                int(client_message.split("#")[-1])
                            )
                            continue
                    if client_message == f"door_opened#{passenger.get_elevator_code()}":
                        print(
                            f"Passenger {passenger.name} is Entering the elevator {passenger.get_elevator_code()}"
                        )
                        if passenger.get_elevator_code() == 1:
                            passenger.change_state(
                                PassengerState.IN_ELEVATOR_1_AT_OTHER_FLOOR
                            )
                        elif passenger.get_elevator_code() == 2:
                            passenger.change_state(
                                PassengerState.IN_ELEVATOR_2_AT_OTHER_FLOOR
                            )
                        server.send_string(
                            server.bound_client,
                            f"select_floor@{passenger.target_floor}#{passenger.get_elevator_code()}",
                        )
                        continue
        for each_passenger in passengers:
            if each_passenger.is_finished() and not each_passenger.finished_print:
                print(
                    f"Passenger {each_passenger.name} has arrived at the target floor."
                )
                each_passenger.finished_print = True
                count += 1
        if count == len(passengers):
            print("PASSED: ALL PASSENGERS HAS ARRIVED AT THE TARGET FLOOR!")
            time.sleep(1)
            server.send_string(server.bound_client, "reset")
            break


if __name__ == "__main__":
    my_server = server.ZmqServerThread()
    while True:
        if len(my_server.clients_addr) == 0:
            continue
        elif len(my_server.clients_addr) >= 2:
            print("more than 1 client address stored. server will exit")
            sys.exit()
        else:
            addr = list(my_server.clients_addr)[0]
            msg = input(f"Initiate evaluation for {addr}?: (y/n)\n")
            if msg == "y":
                my_server.bound_client = addr
                testing(my_server)
            else:
                continue
