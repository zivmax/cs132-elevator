# Elevator System Simulation and Testing

This document describes how to set up, run, and interact with a simulated elevator system, along with its testing framework. The system uses ZeroMQ (pyzmq) for inter-process communication.

## 1. Environment Setup

- **Python:** Version 3.10 or higher.
- **Dependencies:** Install the required dependencies using pip:
  - `pip install -r requirements.txt`

## 2. Code Structure

The project is organized into the following directories and files:

- `/src/` - Contains your elevator control logic.

  - `net_client.py`: Handles communication with the testing server (from `/test/`). _You generally don't need to modify this._
  - `main.py`: This is the main file for _your_ elevator control system. Modify this file to implement your logic.

- `/test/` - Contains the testing framework.
  - `main.py`: The main file for the test case runner. This interacts with your system and sends/receives events.
  - `server.py`: Handles communication with your `net_client.py`. _You generally don't need to modify this._

## 3. Running the Code

Follow these steps to run the simulation and tests:

1.  **Start the Test Server:**

    - Open a terminal.
    - Navigate to the `/test/` directory.
    - Run: `python main.py`

2.  **Start Your Elevator System:**

    - Open a _separate_ terminal.
    - Navigate to the `/src/` directory.
    - Run: `python main.py`

3.  **Run the Test Case:**
    - In the terminal where you ran `/test/main.py`, you should see a prompt.
    - Type `y` and press Enter to start the naive test case.

## 4. Operations and Events

The system uses strings to represent operations (actions initiated by users) and events (notifications from the system).

### 4.1 User Operations (Your System Sends)

These are the commands your elevator system can send to the test environment:

- `"open_door"`: Opens the door of the _currently targeted_ elevator (see `floor_arrived` event). You should determine which elevator to open the door for based on the current state of your system.
- `"close_door"`: Closes the door of the _currently targeted_ elevator.
- `"call_up": [floor]` : Simulates a user pressing the "up" button on the specified floor.
  - `floor`: A string representing the floor number: `"-1"`, `"1"`, `"2"`.
  - Example: `"call_up@1"` - User on floor 1 presses the "up" button.
- `"call_down": [floor]` : Simulates a user pressing the "down" button on the specified floor.
  - `floor`: A string representing the floor number: `"3"`, `"2"`, `"1"`.
  - Example: `"call_down@3"` - User on floor 3 presses the "down" button.
- `"select_floor": [floor#elevator]` : Simulates a user inside an elevator selecting a destination floor.
  - `floor`: A string representing the floor number: `"-1"`, `"1"`, `"2"`, `"3"`.
  - `elevator`: A string representing the elevator number: `"1"`, `"2"`.
  - Example: `"select_floor@2#1"` - User in elevator #1 selects floor 2.
- `"reset"`: Resets your elevator system to its initial state (both elevators at floor 1, doors closed).

### 4.2 System Events (Your System Receives)

These are the events your elevator system will receive from the test environment:

- `"door_opened": [elevator]` : Indicates that the door of the specified elevator has opened.
  - `elevator`: A string representing the elevator number: `"1"`, `"2"`.
  - Example: `"door_opened#1"` - Elevator #1's door has opened.
- `"door_closed": [elevator]` : Indicates that the door of the specified elevator has closed.
  - `elevator`: A string representing the elevator number: `"1"`, `"2"`.
  - Example: `"door_closed#1"` - Elevator #1's door has closed.
- `"floor_arrived": [direction], [floor], [elevator]` : Indicates that an elevator has arrived at a floor.
  - `direction`: A string: `"up"`, `"down"`, or `""` (empty string for stopped). Indicates the direction the elevator was traveling.
  - `floor`: A string representing the floor number: `"-1"`, `"1"`, `"2"`, `"3"`.
  - `elevator`: A string representing the elevator number: `"1"`, `"2"`.
  - Example: `"floor_arrived@up,1,#1"` - Elevator #1 arrived at floor 1 while moving upwards.
  - Example: `"floor_arrived@,1,#1"` - Elevator #1 arrived at floor 1 and is now stopped.

## 5. Initial System State

- Both elevators (#1 and #2) start on the **first floor (1)**.
- The doors of both elevators are initially **closed**.

## 6. Important Considerations (Added for clarity)

- **Targeted Elevator:** The `"open_door"` and `"close_door"` commands operate on the elevator that is currently considered "targeted". This is typically the elevator that most recently triggered a `"floor_arrived"` event. Your logic needs to track which elevator is at which floor.
- **State Management:** Your `main.py` will need to maintain the state of each elevator (current floor, direction, door status, requested floors).
- **Event Handling:** Your code should listen for events from the `Server.py` (via `NetClient.py`) and update the elevator state accordingly. It should then send appropriate commands back to the server.
- **Error Handling:** Consider adding error handling (e.g., what happens if you try to open a door that's already open?). The provided instructions don't specify error behavior, so you have some flexibility in how you handle these situations.
- **String Formatting**: I've used the "@" character to join parts of the operation/event strings.

This refactored version should be much easier to understand and use as a guide for developing your elevator system. Good luck!
