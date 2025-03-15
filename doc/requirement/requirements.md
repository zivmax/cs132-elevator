# Requirement Document

Team 18 Project：Elevator
Made by : Guo YU

---

## Table of Contents
- [Requirement Document](#requirement-document)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
    - [Overview](#overview)
    - [Basic Requirements](#basic-requirements)
    - [Product Line Analysis](#product-line-analysis)
  - [UML](#uml)
    - [Use Case Diagram](#use-case-diagram)
    - [UML Activity Diagram](#uml-activity-diagram)
    - [UML Class Diagram](#uml-class-diagram)
  - [Detailed Requirement](#detailed-requirement)
    - [Overview](#overview-1)
    - [Passengers’ Perspective](#passengers-perspective)
    - [Visual Components](#visual-components)
    - [Elevator’s Perspective](#elevators-perspective)
    - [Control System](#control-system)

---

## Introduction

### Overview

This project aims to develop a software which controls two elevators' movement under various user operations and system events. 

### Basic Requirements

- Both elevators start at the ground floor with doors closed.  
- Doors open automatically when the elevator is called via "up" or "down" button.  
- Inside each elevator, floor buttons light up when pressed, indicating the target floor.  
- The control panel displays current floor and direction.  
- Upon reaching the target floor, floor buttons reset, doors open, and the trip ends.  

### Product Line Analysis

The domain focuses on managing two elevators as they respond to user commands (open/close doors, call floors, select floors) and system events (door opened/closed, floor arrivals). Each elevator must track its state (location, door status) and handle incoming requests efficiently. The system must ensure correct scheduling of elevator movements, resolve conflicts when multiple commands are issued, and reset to first-floor-closed-door mode on demand.

---

## UML 

### Use Case Diagram

The use case diagram consists of the following functions:
- **Enter Elevator**: The interaction starts when a user steps inside the elevator.
- **Exit Elevator**: The ride concludes once the user reaches their desired floor and exits the elevator.
- **Press Up/Down Button**: A passenger selects a floor by pressing the corresponding button to go up or down.
- **Press Open/Close Button**: The user manually opens or closes the elevator doors by pressing the respective button.
- **Open Door**: The system automatically or manually opens the doors upon arrival at a floor or in response to a user request.
- **Close Door**: The system automatically or manually closes the doors after a set delay or in response to a user request.
- **Move Up**: The elevator ascends to a higher targeted floor.
- **Move Down**: The elevator descends to a lower targeted floor.
- **Stop**: The elevator halts either at the initial state or when it reaches the target floor and the user steps out.

![UCD](./imgs/use_case/use_case.png)


### UML Activity Diagram

- **Start**: The process begins when the user starts interacting with the elevator.
- **Which Direction?**: The user selects the direction by pressing either the Up or Down button.
- **Enter The Elevator?**: The user decides whether to enter the elevator.
  - **Yes**: The user enters the elevator and selects a floor.
  - **No**: The user does not enter the elevator, and the process ends.
- **Select Floor**: The user selects the desired floor.
- **Press Open Button**: The user presses the button to open the elevator door.
- **Press Close Button**: The user presses the button to close the elevator door.
- **Is current floor the target floor?**: The elevator checks if it has reached the target floor.
  - **Yes**: The elevator opens the door.
  - **No**: The elevator moves to the target floor.
- **Currently/Stop?**: The elevator checks if it is stopped.
  - **Yes**: The elevator checks if the door is open.
  - **No**: The elevator continues moving.
- **Door Open?**: The elevator checks if the door is open.
  - **Yes**: The elevator closes the door.
  - **No**: The elevator waits for the door to open.
- **Close Door**: The elevator closes the door.
- **Move to target floor**: The elevator moves to the selected floor.
- **Exit?**: The user decides whether to exit the elevator.
  - **Yes**: The user exits the elevator.
  - **No**: The user remains in the elevator.
- **Waiting for the door to open/close**: The user waits for the door to open or close.

![UAD](./imgs/activity/activity.png)

### UML Class Diagram

- The system consists of four classes, dispatcher, client, elevator, and engine.
- In the elevator's lifecycle, each blocks are update and evaluate the current status information, in the order of client -> dispatcher -> every
elevator -> engine
- The elevator class mimics the elevator compartment, which needs to be pulled up or down by the tie rope system controlled by the engine.

- The dispatcher processes the requests received through the client, decides the optimal elevator to dispatch and order the engine accordingly.

![UCD](./imgs/class_plot/class.drawio.png)


## Detailed Requirement

### Overview
Overall, the main participants in this elevator system are the passengers and the elevator. The specific interaction process between them can be divided into interactions with the panel and the elevator control system.

### Passengers’ Perspective
1. For passengers, they should be able to:  
   1. Know the floor information where the elevator is located.  
   1. Understand the current operating status of the elevator (ascending/descending/stationary).  
   1. Outside the elevator, press the corresponding floor button according to their destination floor, thereby controlling the elevator to reach the current floor of the passenger, and convey this information to the panel.  
   1. When the elevator reaches the passenger's floor, they can control the opening and closing of the elevator doors at that floor, with the highest priority given to the operations performed by passengers on that floor.  
   1. Inside the elevator, they can press the button for their destination floor to control the elevator to travel to the corresponding floor, and convey this information to the panel.  
   1. Press the emergency help button at any time, and convey this information to the panel.  

### Visual Components
1. For the panel:  
   1. The buttons for controlling the opening and closing of the elevator doors are ineffective during the operation of the elevator.  
   1. Receive all relevant information conveyed by passengers through the panel, and pass this information to the elevator control system.  
   1. Instantly display the current floor information of the elevator, the current operating status of the elevator (ascending/descending/stationary), and whether the elevator is malfunctioning, etc., and pass this information to the elevator control system.  

### Elevator’s Perspective
1. For the elevator itself, it should be able to:  
   1. Receive signals from the elevator control system to ascend/descend/stay stationary.  
   1. Receive signals from the elevator control system to open/close doors.  
   1. Upload all current status of the elevator to the elevator control system.  
   1. Stop operating and close the doors when receiving an emergency stop signal.  

### Control System
1. For the elevator control system, it should be able to:  
   1. Receive and process all information about the elevator's floor position and current operating status from the panel. When multiple users control the elevator concurrently, it should select the optimal algorithm to schedule the elevators, including:  
      1. When there are multiple passenger requests, the elevator should first go to the floor where the nearest passenger is located and take them to their destination, minimizing the waiting time for passengers.  
      1. When responding to multiple passenger requests, the elevator can use an intelligent route planning algorithm to choose the appropriate stopping sequence and route, transporting passengers to their destinations in the fastest time possible, thus minimizing the total journey time.  
   1. Adjust the elevator's door opening and closing status, and the direction of travel.  
   1. Adjust the speed of the elevator based on the position of the target floor and the distance from the current floor to the target floor (reflected in the time required for elevator travel).  
   1. Immediately stop the elevator operation upon receiving an emergency signal from the panel and report any malfunction through the panel.  