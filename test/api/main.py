import sys
import os
import server
import time
import random
from enum import IntEnum
#######   ELEVATOR PROJECT    #######

### Simple Test Case ###
class PassengerState(IntEnum):
    #only for reference, it may be complex in other testcase.
    IN_ELEVATOR_1_AT_TARGET_FLOOR = 1
    IN_ELEVATOR_1_AT_OTHER_FLOOR = 2
    IN_ELEVATOR_2_AT_TARGET_FLOOR = 3
    IN_ELEVATOR_2_AT_OTHER_FLOOR = 4
    OUT_ELEVATOR_0_AT_TARGET_FLOOR = 5
    OUT_ELEVATOR_0_AT_OTHER_FLOOR = 6


class Passenger:
    def __init__(self, start_floor, target_floor,name = "test"):
        self.start_floor:int = start_floor
        self.target_floor:int = target_floor
        self.direction = "up" if self.target_floor >self.start_floor else "down"
        self._elevator_code = -1
        self.current_floor = start_floor
        self.finished = False if self.target_floor != self.start_floor else True
        self.finished_print = False
        self.name = name
        self.matching_signal = f"up_floor_arrived@{self.current_floor}" if self.direction == "up" else f"down_floor_arrived@{self.current_floor}"
        self.state = PassengerState.OUT_ELEVATOR_0_AT_OTHER_FLOOR

        
    def change_state(self, target_state:PassengerState)-> str:
        self.state = target_state

    def is_finished(self):
        return self.finished
    def set_elevator_code(self,value):
        self._elevator_code = value
    def get_elevator_code(self):
        return self._elevator_code


def testing(server:server.ZmqServerThread):


    ############ Initialize Passengers ############
    passengers = [Passenger(1, 3,"A")] ##There can be many passengers in testcase.
    timeStamp = -1 #default time stamp is -1
    clientMessage = "" #default received message is ""
    count = 0
    server.send_string(server.bindedClient,"reset") #Reset the client
    time.sleep(1)

    # for passenger in passengers:
    #     time.sleep(1)
    server.send_string(server.bindedClient,"call_up@1")


    def is_received_new_message(oldTimeStamp:int, oldServerMessage:str, Msgunprocessed:bool = False)->bool:
        if(Msgunprocessed):
            return True
        else:
            tmp_msg = server.receivedMessage
            tmp_ts = server.messageTimeStamp

            if(oldTimeStamp == tmp_ts and 
            oldServerMessage == tmp_msg):
                return False
            else:
                nonlocal timeStamp, clientMessage
                timeStamp = tmp_ts
                clientMessage = tmp_msg
                return True
    


    
    ############ Passenger timed automata ############
    while(True):
        # 检查是否有新消息（单次拉取）
        has_new_message = is_received_new_message(timeStamp, clientMessage)
        # 广播消息给所有乘客处理
        if has_new_message:
            for passenger in passengers:
                # 处理IN_ELEVATOR_1_AT_OTHER_FLOOR状态
                if passenger.state == PassengerState.IN_ELEVATOR_1_AT_OTHER_FLOOR:
                    if clientMessage.endswith(f"floor_arrived@{passenger.target_floor}#{passenger.get_elevator_code()}"):
                        passenger.current_floor = passenger.target_floor
                        passenger.change_state(PassengerState.IN_ELEVATOR_1_AT_TARGET_FLOOR)
                
                # 处理IN_ELEVATOR_1_AT_TARGET_FLOOR状态        
                elif passenger.state == PassengerState.IN_ELEVATOR_1_AT_TARGET_FLOOR:
                    if clientMessage == f"door_opened#1":
                        print(f"Passenger {passenger.name} is Leaving the elevator")
                        passenger.change_state(PassengerState.OUT_ELEVATOR_0_AT_TARGET_FLOOR)
                        passenger.finished = True

                elif passenger.state == PassengerState.IN_ELEVATOR_2_AT_OTHER_FLOOR:
                        if(clientMessage.endswith(f"floor_arrived@{each_passenger.target_floor}#{each_passenger.get_elevator_code()}")):
                            each_passenger.current_floor = each_passenger.target_floor
                            each_passenger.change_state(PassengerState.IN_ELEVATOR_2_AT_TARGET_FLOOR)

                elif passenger.state == PassengerState.IN_ELEVATOR_2_AT_TARGET_FLOOR:
                        if(clientMessage == f"door_opened#2"):
                            print(f"Passenger {each_passenger.name} is Leaving the elevator")
                            each_passenger.change_state(PassengerState.OUT_ELEVATOR_0_AT_TARGET_FLOOR)
                            each_passenger.finished = True
                
                # 处理OUT_ELEVATOR_0_AT_OTHER_FLOOR状态
                elif passenger.state == PassengerState.OUT_ELEVATOR_0_AT_OTHER_FLOOR:
                    if clientMessage.startswith(passenger.matching_signal) and passenger.current_floor == passenger.start_floor:
                        if passenger.get_elevator_code() == -1:
                            passenger.set_elevator_code(int(clientMessage.split("#")[-1]))
                    
                    if clientMessage == f"door_opened#{passenger.get_elevator_code()}":
                        print(f"Passenger {passenger.name} is Entering the elevator {passenger.get_elevator_code()}")
                        # time.sleep(1)
                        if passenger.get_elevator_code() == 1:
                            passenger.change_state(PassengerState.IN_ELEVATOR_1_AT_OTHER_FLOOR)
                        elif passenger.get_elevator_code() == 2:
                            passenger.change_state(PassengerState.IN_ELEVATOR_2_AT_OTHER_FLOOR)
                        server.send_string(server.bindedClient,f"select_floor@{passenger.target_floor}#{passenger.get_elevator_code()}")
        
        # 检查乘客是否完成
        for each_passenger in passengers:
            if each_passenger.is_finished() and not each_passenger.finished_print:
                print(f"Passenger {each_passenger.name} has arrived at the target floor.")
                each_passenger.finished_print = True
                count += 1
                    
            
        if(count == len(passengers)):
            print("PASSED: ALL PASSENGERS HAS ARRIVED AT THE TARGET FLOOR!")
            time.sleep(1)
            server.send_string(server.bindedClient,"reset")
            break





if __name__ == "__main__":
    my_server = server.ZmqServerThread()
    while(True):
        if(len(my_server.clients_addr) == 0):
            continue
        elif(len(my_server.clients_addr) >=2 ):
            print('more than 1 client address stored. server will exit')
            sys.exit()
        else:
            addr = list(my_server.clients_addr)[0]
            msg = input(f"Initiate evaluation for {addr}?: (y/n)\n")
            if msg == 'y':
                my_server.bindedClient = addr
                testing(my_server)
            else:
                continue