# User Manual 

- Team-17 
- Project: Elevator

## Elevator System 

This documentation shows how to set up the recommended environment configuration for the elevator system and demonstrates the detailed usage of the software .

## Content

- [Environment Setup](#environment-setup)
- [Detailed Usage](#detailed-usage)
- [Elevator States](#elevator-states)
- [Button Logic](#button-logic)


## Environment Setup

- **Python:** Version 3.10 or higher.
- **Dependencies:** Install the required dependencies using pip:
  - `pip install -r requirements.txt`

## Detailed Usage

### User Interface Explanation

- **Floor Buttons**  
  Select any floor in the elevator panel. Once pressed, the button highlights and remains active until that floor is reached. Multiple floors can be selected and will be served in an optimized order.

<div align=center>
<img src="./imgs/GUIs/target_floor.png" width="400"/>
</div>
  
- **Call Up/Down Buttons**  
  Press these on a specific floor to request an elevator moving in the desired direction. Buttons stay active until an elevator arrives. Each floor has only the valid direction buttons (e.g., top floor has only "down").

<div align=center>
<img src="./imgs/GUIs/call.png" width="200"/>
</div>

- **Door Open/Close Buttons**  
  Can only be used if the elevator is idle or the door is already opening/open. 
<div align=center>
<img src="./imgs/GUIs/ele_door.png" width="400"/>
</div>
  The door takes about a second to change states, then automatically closes after a short delay unless held open.
<div align=center>
<img src="./imgs/GUIs/door.png" width="400"/>
</div>

- **Status Display Panel**  
  Shows current floor, current state (IDLE, MOVING_UP, MOVING_DOWN), target floors still in queue, and door status.
<div align=center>
<img src="./imgs/GUIs/panel.png" width="400"/>
</div>

## Elevator States

Each elevator compartment can be in one of the following states:
- **IDLE:** Stationary, waiting for requests.
- **MOVING_UP:** Moving upward to a requested floor.
- **MOVING_DOWN:** Moving downward to a requested floor.

The elevator door can be in one of:
- **OPEN:** Door is fully open.
- **CLOSED:** Door is fully closed.
- **OPENING:** Door is in the process of opening.
- **CLOSING:** Door is in the process of closing.

Both elevators start IDLE at the ground floor with doors CLOSED.

## Button Logic

- **Floor Buttons:**  
  - Can be pressed at any time; each press adds a target floor to the elevator's queue.
  - Button lights up (red) when active, returns to idle (blue) after arrival.
  - Multiple selections are allowed; the elevator will serve all selected floors in an optimized sequence.

- **Call Up/Down Buttons:**  
  - Press to request an elevator in a specific direction from a floor.
  - Button lights up (red) and remains active until an elevator arrives.
  - Only valid direction buttons are shown per floor.

- **Door Open/Close Buttons:**  
  - Open: Only works when elevator is IDLE or door is already opening/open.
  - Close: Only works when door is OPEN or OPENING.
  - Door transitions take about 1 second; open doors auto-close after a short delay unless held open.


For further questions on configuration or troubleshooting, consult the [Specification Documentation](../../Specification/specification.md).


