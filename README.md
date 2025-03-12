# System Behaviour
  - 2 Elevators in all
  - Automatically close the door if user don't close it.
  - Response with floor arrived before open door arriving a floor calling up/down.
  - Schedule the elevator for best efficiency according expected time cost.
  - Any other behaviour a elevator system will have in real life.

# Available Request/Response
  ## Available User Requests
  - "open_door", For example, `open_door#1` means a user in the elevator1 press the open door button.
  - "close_door", For example, `close_door#2` means a user in the elevator2 press the close door button.
  - "call_up": ["-1", "1", "2"], For example, `call_up@1` means a user on the first floor presses the button to call the elevator to go upwards.
  - "call_down": ["3", "2", "1"], For instance, `call_down@3` signifies a user on the third floor pressing the button to call the elevator to go downwards.
  - "select_floor": ["-1#1", "-1#2", "1#1", "1#2", "2#1", "2#2", "3#1", "3#2"], For example, `select_floor@2#1` means a user in elevator #1 selects to go to the second floor.
  - "reset": When your elevator system receives a reset signal, it should reset the elevator's state machine to its initial state

  ## Available System Responses
  - "door_opened": ["#1", "#2"], `door_opened#1` means the doors of elevator #1 have opened.
  - "door_closed": ["#1", "#2"], `door_closed#1` means the doors of elevator #1 have closed.
  - "floor_arrived":["up","down",""],["-1","1","2","3"],["#1", "#2"] "up_floor_1_arrived#1", indicating that elevator #1 has arrived at the first floor while moving upwards. "floor_1_arrived#1",indicating that elevator #1 has stopped at the first floor.

# Elevator system initial assumption
Assume that both elevators(#1, #2) initially stop on the first floor and the doors are closed. 

# System Design

- A `Elevator` class, 
  - It will handle all the operation itself, including:
    - Multi target floor assignment planning, by changing the state of the elevator. 
    - User indoor floor selection.
    - Open and close door automatically besides manual control.
    - Changing the current state like `MOVING_UP`, `STOPPED` etc..
  - It will receives command from the dispatcher, including:
    - `X_floor` assigning from the dispatcher.
  - It will sends event signal to the user test server, including:
    - `door_opened`
    - `door_closed`
    - `floor_arrived`
- A `Dispatcher` class,
  - It will receive and parse the request from the user test server, and assign the target called floor task to the most suitable elevator.
- A `Engine` class,
  - Move the elevators floor by floor according to their states, in every update loop.
- A `World` class,
  - Simluate the world.
  - Manage all instances's update.