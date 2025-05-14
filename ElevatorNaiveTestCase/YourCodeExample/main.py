import os
import NetClient
import time
from enum import IntEnum

##Example Code For Elevator Project
#Feel free to rewrite this file!


############ Elevator state ############
#Feel free to design the states of your elevator system.
class ElevatorState(IntEnum):
    up = 0
    down = 1
    stopped_door_closed = 2
    stopped_door_opened = 3
    stopped_opening_door = 4

# This function is just a prototype; it has no actual functionality
def elevator_control_function():
    for i in range(1,100): # some functions may cost time.
        i += 1 
    return None

# This function determines whether a new message has been received
def is_received_new_message(oldTimeStamp:int, oldServerMessage:str, Msgunprocessed:bool = False)->bool:
    if(Msgunprocessed):
        return True
    else:
        if(oldTimeStamp == zmqThread.messageTimeStamp and 
           oldServerMessage == zmqThread.receivedMessage):
            return False
        else:
            return True

if __name__=='__main__':

    ############ Connect the Server ############
    identity = "TeamX" #write your team name here.
    zmqThread = NetClient.ZmqClientThread(identity=identity)


    ############ Initialize Elevator System ############
    timeStamp = -1 #Used when receiving new message
    serverMessage = "" #Used when receiving new message
    messageUnprocessed = False #Used when receiving new message 
    elevatorState = ElevatorState.stopped_door_closed #Initialize your elevator system
    

    while(True):
        
        ############ Your timed automata design ############
        ##Example for the naive testcase
        


        match elevatorState: # Available on Python 3.10+ 
            case ElevatorState.stopped_door_closed:
                if(is_received_new_message(timeStamp,serverMessage,messageUnprocessed)):
                    if(not messageUnprocessed):
                        timeStamp = zmqThread.messageTimeStamp
                        serverMessage = zmqThread.receivedMessage
                    messageUnprocessed = False

                    if(serverMessage == "call_up@1"):
                        zmqThread.sendMsg("up_floor_arrived@1#1") #assume the elevator #1 stopped at floor 1.
                        elevator_control_function()
                        messageUnprocessed = True
                        elevatorState = ElevatorState.stopped_opening_door

                    if(serverMessage == "select_floor@3#1"):
                        elevator_control_function()
                        messageUnprocessed = True
                        elevatorState = ElevatorState.up

                    if(serverMessage == "reset"):
                        timeStamp = -1 #Used when receiving new message
                        serverMessage = "" #Used when receiving new message
                        messageUnprocessed = False #Used when receiving new message 
                        elevatorState = ElevatorState.stopped_door_closed #Initialize your elevator system

                else:
                    continue

            case ElevatorState.stopped_opening_door:
                if(is_received_new_message(timeStamp,serverMessage,messageUnprocessed)):
                    elevator_control_function()
                    messageUnprocessed = True
                    zmqThread.sendMsg("door_opened#1")
                    elevatorState = ElevatorState.stopped_door_opened

                if(serverMessage == "reset"):
                    timeStamp = -1 #Used when receiving new message
                    serverMessage = "" #Used when receiving new message
                    messageUnprocessed = False #Used when receiving new message 
                    elevatorState = ElevatorState.stopped_door_closed #Initialize your elevator system

                    
            case ElevatorState.stopped_door_opened:
                if(is_received_new_message(timeStamp,serverMessage,messageUnprocessed)):
                    if(not messageUnprocessed):
                        timeStamp = zmqThread.messageTimeStamp
                        serverMessage = zmqThread.receivedMessage
                    messageUnprocessed = False

                    if(serverMessage == "call_up@1"):
                        elevator_control_function()
                        zmqThread.sendMsg("door_closed#1")
                        elevatorState = ElevatorState.stopped_door_closed
                    
                    if(serverMessage == "reset"):
                        timeStamp = -1 #Used when receiving new message
                        serverMessage = "" #Used when receiving new message
                        messageUnprocessed = False #Used when receiving new message 
                        elevatorState = ElevatorState.stopped_door_closed #Initialize your elevator system
                else:
                    continue

            case ElevatorState.up:
                if(is_received_new_message(timeStamp,serverMessage,messageUnprocessed)):
                    if(not messageUnprocessed):
                        timeStamp = zmqThread.messageTimeStamp
                        serverMessage = zmqThread.receivedMessage
                    messageUnprocessed = True

                    elevator_control_function()
                    zmqThread.sendMsg("floor_arrived@3#1")
                    elevatorState = ElevatorState.stopped_opening_door

                    if(serverMessage == "reset"):
                        timeStamp = -1 #Used when receiving new message
                        serverMessage = "" #Used when receiving new message
                        messageUnprocessed = False #Used when receiving new message 
                        elevatorState = ElevatorState.stopped_door_closed #Initialize your elevator system
                pass
            case ElevatorState.down:
                pass

        time.sleep(0.01)

            

    '''
    For Other kinds of available serverMessage, see readMe.txt
    '''
    