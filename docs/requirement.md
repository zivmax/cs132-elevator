# Elevator System Requirements Documentation

## Table of Contents

- [Elevator System Requirements Documentation](#elevator-system-requirements-documentation)
  - [Table of Contents](#table-of-contents)
  - [System Overview](#system-overview)
    - [Key System Components:](#key-system-components)
  - [Use Case Diagram](#use-case-diagram)
    - [Use Case Descriptions:](#use-case-descriptions)
  - [Class Diagram](#class-diagram)
    - [Class Descriptions:](#class-descriptions)
  - [Activity Diagrams](#activity-diagrams)
    - [1. Elevator Call Processing Workflow](#1-elevator-call-processing-workflow)
    - [2. Door Operation Workflow](#2-door-operation-workflow)
  - [Sequence Diagrams](#sequence-diagrams)
    - [1. External System Elevator Call Sequence](#1-external-system-elevator-call-sequence)
    - [2. Frontend Floor Selection Sequence](#2-frontend-floor-selection-sequence)
    - [3. System State Synchronization Sequence](#3-system-state-synchronization-sequence)
  - [Functional Requirements](#functional-requirements)
    - [FR1: Elevator Movement Management](#fr1-elevator-movement-management)
    - [FR2: Door Operation Management](#fr2-door-operation-management)
    - [FR3: Call Dispatching System](#fr3-call-dispatching-system)
    - [FR4: User Interface Requirements](#fr4-user-interface-requirements)
    - [FR5: External API Requirements](#fr5-external-api-requirements)
    - [FR6: State Management](#fr6-state-management)

---

## System Overview

The Elevator Simulation System is a comprehensive multi-elevator management system that simulates real-world elevator operations. The system manages two elevators operating across four floors (-1, 1, 2, 3) and handles various user interactions including floor calls, destination selections, and manual door operations.

### Key System Components:
- **Backend Simulation Engine**: Python-based core simulation logic
- **Frontend Interface**: Web-based user interface with real-time updates
- **Communication Layer**: WebSocket and ZMQ protocols for real-time communication
- **External API**: ZMQ interface for external test server integration

---

## Use Case Diagram

```mermaid
graph LR
    subgraph "Elevator System"
        subgraph "User Interactions"
            UC1[Call Elevator from Floor]
            UC2[Select Destination Floor]
            UC3[Open Door Manually]
            UC4[Close Door Manually]
            UC5[Reset System]
        end
        
        subgraph "System Operations"
            UC6[Dispatch Elevator]
            UC7[Move Elevator]
            UC8[Auto Door Operations]
            UC9[State Synchronization]
            UC10[External API Communication]
        end
    end
    
    subgraph "Actors"
        USER[Building User]
        ADMIN[System Administrator]
        EXT_SYS[External Test System]
        WEB_UI[Web Frontend]
    end
    
    USER --> UC1
    USER --> UC2
    USER --> UC3
    USER --> UC4
    
    ADMIN --> UC5
    
    EXT_SYS --> UC1
    EXT_SYS --> UC2
    EXT_SYS --> UC3
    EXT_SYS --> UC4
    EXT_SYS --> UC5
    
    WEB_UI --> UC9
    
    UC1 --> UC6
    UC2 --> UC6
    UC6 --> UC7
    UC7 --> UC8
    UC6 --> UC9
    UC7 --> UC9
    UC8 --> UC9
    
    UC1 --> UC10
    UC2 --> UC10
    UC3 --> UC10
    UC4 --> UC10
    UC5 --> UC10
```

### Use Case Descriptions:

**Primary Use Cases:**
- **UC1 - Call Elevator from Floor**: Users can call an elevator to their current floor with directional preference (up/down)
- **UC2 - Select Destination Floor**: Users inside an elevator can select their destination floor
- **UC3 - Open Door Manually**: Users can manually open elevator doors
- **UC4 - Close Door Manually**: Users can manually close elevator doors
- **UC5 - Reset System**: Administrators can reset the entire system to initial state

**System Operation Use Cases:**
- **UC6 - Dispatch Elevator**: System intelligently assigns the most suitable elevator to service calls
- **UC7 - Move Elevator**: System handles elevator movement between floors
- **UC8 - Auto Door Operations**: System automatically opens/closes doors based on arrival and timeout
- **UC9 - State Synchronization**: System maintains real-time state updates across all interfaces
- **UC10 - External API Communication**: System communicates with external test systems via ZMQ

---

## Class Diagram

```mermaid
classDiagram
    class ElevatorApp {
        -bool headless
        -bool running
        -Simulator backend
        -ElevatorAPI elevator_api
        -WebSocketBridge bridge
        -ElevatorHTTPServer http_server
        +__init__(show_debug, ws_port, http_port, zmq_port, headless)
        +run()
        +update()
        +cleanup()
    }

    class Simulator {
        -Optional~ElevatorAPI~ api
        -List~Elevator~ elevators
        -Optional~Dispatcher~ dispatcher
        +__init__()
        +set_api_and_initialize_components(api)
        +update()
        +stop()
    }

    class Elevator {
        -int id
        -int current_floor
        -List~Task~ task_queue
        -ElevatorState state
        -DoorState door_state
        -Optional~MoveDirection~ direction
        -float door_timeout
        -float floor_travel_time
        -Simulator world
        -ElevatorAPI api
        +__init__(elevator_id, world, api)
        +update()
        +open_door()
        +close_door()
        +calculate_estimated_time(floor, direction) Optional~float~
        +request_movement_if_needed()
    }

    class Dispatcher {
        -Simulator world
        -ElevatorAPI api
        -Dict~str,Call~ pending_calls
        +__init__(world, api)
        +add_call(floor, direction)
        +assign_task(elevator_idx, floor, call_id)
        +update()
        +add_outside_call(floor, direction) str
        +get_call_direction(call_id) Optional~MoveDirection~
        +complete_call(call_id)
        +reset()
        -_process_pending_calls()
        -_can_elevator_serve_call(elevator, floor, direction) bool
        -_optimize_task_queue(elevator)
        -_get_elevator_committed_direction(elevator) Optional~MoveDirection~
    }

    class ElevatorAPI {
        -Optional~Simulator~ world
        -ZmqClientThread zmq_client
        +__init__(world, zmq_ip, zmq_port)
        +set_world(world)
        +ui_call_elevator(data) str
        +ui_select_floor(data) str
        +ui_open_door(data) str
        +ui_close_door(data) str
        +fetch_states() List~Dict~
        +stop()
        +send_floor_arrived_message(elevator_id, floor, direction)
        +send_door_opened_message(elevator_id)
        +send_door_closed_message(elevator_id)
        -_parse_and_execute(command) Optional~str~
        -_handle_call_elevator(floor, direction) Dict
        -_handle_select_floor(floor, elevator_id) Dict
        -_handle_open_door(elevator_id) Dict
        -_handle_close_door(elevator_id) Dict
        -_handle_reset() Dict
        -_send_message_to_client(message)
    }

    class WebSocketBridge {
        -ElevatorAPI backend_api
        -WebSocketServer server
        +__init__(backend_api, host, port)
        +sync_backend()
        +stop()
        -_handle_message(message) str
    }

    class ElevatorHTTPServer {
        -str host
        -int port
        -str directory
        -HTTPServer httpd
        +__init__(host, port, directory)
        +run()
        +stop()
    }

    class WebSocketServer {
        -str host
        -int port
        -Set~ServerConnection~ _clients
        -Callable _message_handler
        -Server _server
        -Thread _thread
        -Event _stop_event
        -Optional~AbstractEventLoop~ loop
        +__init__(host, port, message_handler)
        +start()
        +stop()
        +broadcast(message)
        +send_elevator_states(data)
        +is_running() bool
        -_process_message(websocket, message) str
        -_handle_connection(websocket)
        -_run_server()
        -_run_in_thread()
    }

    class ZmqClientThread {
        -Context _context
        -Socket _socket
        -str _serverIp
        -str _identity
        -str _port
        -ElevatorAPI _api_instance
        -deque _messageQueue
        -deque _timestampQueue
        -Lock _lock
        -Optional~str~ _receivedMessage
        -Optional~int~ _messageTimeStamp
        -bool running
        +__init__(serverIp, port, identity, api_instance)
        +connect_and_start()
        +get_all_messages() List
        +peek_latest_message() Tuple
        +get_next_message() Tuple
        +run()
        +send_msg(data)
        +stop()
        -__launch()
    }

    class Task {
        -int floor
        -Optional~str~ call_id
        +__init__(floor, call_id)
        +is_outside_call() bool
    }

    class Call {
        -str call_id
        -int floor
        -Optional~MoveDirection~ direction
        -CallState state
        -Optional~int~ assigned_elevator
        +__init__(call_id, floor, direction)
        +assign_to_elevator(elevator_idx)
        +complete()
        +is_pending() bool
        +is_assigned() bool
        +is_completed() bool
    }

    class ElevatorState {
        <<enumeration>>
        IDLE
        MOVING_UP
        MOVING_DOWN
    }

    class DoorState {
        <<enumeration>>
        OPEN
        CLOSED
        OPENING
        CLOSING
    }

    class MoveDirection {
        <<enumeration>>
        UP
        DOWN
    }

    class CallState {
        <<enumeration>>
        PENDING
        ASSIGNED
        COMPLETED
    }

    %% Relationships
    ElevatorApp o-- Simulator
    ElevatorApp o-- ElevatorAPI
    ElevatorApp o-- WebSocketBridge
    ElevatorApp o-- ElevatorHTTPServer

    Simulator o-- Elevator : contains 2
    Simulator o-- Dispatcher
    Simulator ..> ElevatorAPI : uses

    Elevator o-- Task : has queue of
    Elevator --> ElevatorState
    Elevator --> DoorState
    Elevator --> MoveDirection

    Dispatcher o-- Call : manages
    Call --> CallState
    Call --> MoveDirection

    ElevatorAPI o-- Simulator : uses
    ElevatorAPI o-- ZmqClientThread

    WebSocketBridge o-- ElevatorAPI
    WebSocketBridge o-- WebSocketServer

    %% User Interfaces
    class WebFrontend {
        <<interface>>
        +callElevator(floor, direction)
        +selectFloor(floor, elevatorId)
        +openDoor(elevatorId)
        +closeDoor(elevatorId)
        +updateElevatorUI(data)
    }

    class ZMQClient {
        <<interface>>
        +call_up@floor
        +call_down@floor
        +select_floor@floor#elevator_id
        +open_door#elevator_id
        +close_door#elevator_id
        +reset
    }

    WebFrontend --> WebSocketBridge
    ZMQClient --> ElevatorAPI
```

### Class Descriptions:

**Core System Classes:**
- **ElevatorApp**: Main application orchestrator managing all system components
- **Simulator**: Central simulation engine coordinating elevators and dispatcher
- **Elevator**: Individual elevator entity with state management and door operations
- **Dispatcher**: Intelligent elevator assignment system optimizing service efficiency
- **ElevatorAPI**: Central API hub handling all external communications

**Data Model Classes:**
- **Task**: Represents elevator service requests with call tracking
- **Call**: Tracks outside call requests with state management
- **State Enumerations**: Define elevator states, door states, movement directions, and call states

**Communication Classes:**
- **WebSocketBridge**: Facilitates real-time frontend-backend communication
- **User Interfaces**: Web frontend and ZMQ client interfaces for system interaction

---

## Activity Diagrams

### 1. Elevator Call Processing Workflow

```mermaid
flowchart TD
    START([User Calls Elevator]) --> INPUT{Input Source?}
    INPUT -->|Web UI| WEB_CALL[WebSocket Call]
    INPUT -->|External System| ZMQ_CALL[ZMQ Call]
    
    WEB_CALL --> PARSE_WEB[Parse WebSocket Message]
    ZMQ_CALL --> PARSE_ZMQ[Parse ZMQ Command]
    
    PARSE_WEB --> VALIDATE
    PARSE_ZMQ --> VALIDATE
    
    VALIDATE{Validate Floor & Direction?} -->|Invalid| ERROR[Return Error]
    VALIDATE -->|Valid| CREATE_CALL[Create Call Object]
    
    CREATE_CALL --> DISPATCH[Dispatcher.add_call]
    DISPATCH --> PROCESS[Process Pending Calls]
    
    PROCESS --> EVAL_ELEVATORS[Evaluate All Elevators]
    EVAL_ELEVATORS --> CALC_TIME[Calculate Estimated Time for Each]
    CALC_TIME --> SELECT[Select Best Elevator]
    
    SELECT --> ASSIGN[Assign Call to Elevator]
    ASSIGN --> ADD_TASK[Add Task to Elevator Queue]
    ADD_TASK --> NOTIFY[Notify Frontend]
    
    NOTIFY --> CHECK_MOVE{Elevator Ready to Move?}
    CHECK_MOVE -->|Yes| START_MOVE[Start Movement]
    CHECK_MOVE -->|No| WAIT[Wait for Current Operation]
    
    START_MOVE --> MOVING[Elevator Moving]
    MOVING --> ARRIVE[Arrive at Floor]
    ARRIVE --> OPEN_DOORS[Open Doors]
    OPEN_DOORS --> COMPLETE[Mark Call Complete]
    
    WAIT --> MOVING
    ERROR --> END([End])
    COMPLETE --> END
```

### 2. Door Operation Workflow

```mermaid
flowchart TD
    START([Door Operation Request]) --> TYPE{Operation Type?}
    
    TYPE -->|Open Door| OPEN_REQ[Open Door Request]
    TYPE -->|Close Door| CLOSE_REQ[Close Door Request]
    TYPE -->|Auto Open| AUTO_OPEN[Auto Open on Arrival]
    TYPE -->|Auto Close| AUTO_CLOSE[Auto Close on Timeout]
    
    OPEN_REQ --> CHECK_OPEN{Can Open?}
    CLOSE_REQ --> CHECK_CLOSE{Can Close?}
    AUTO_OPEN --> CHECK_AUTO_OPEN{At Target Floor?}
    AUTO_CLOSE --> CHECK_TIMEOUT{Timeout Reached?}
    
    CHECK_OPEN -->|Yes| SET_OPENING[Set Door State: OPENING]
    CHECK_OPEN -->|No| IGNORE1[Ignore Request]
    
    CHECK_CLOSE -->|Yes| SET_CLOSING[Set Door State: CLOSING]
    CHECK_CLOSE -->|No| IGNORE2[Ignore Request]
    
    CHECK_AUTO_OPEN -->|Yes| SET_OPENING
    CHECK_AUTO_OPEN -->|No| IGNORE3[Wait]
    
    CHECK_TIMEOUT -->|Yes| SET_CLOSING
    CHECK_TIMEOUT -->|No| IGNORE4[Continue Waiting]
    
    SET_OPENING --> OPENING_TIMER[Start Opening Timer]
    SET_CLOSING --> CLOSING_TIMER[Start Closing Timer]
    
    OPENING_TIMER --> WAIT_OPEN[Wait Door Operation Time]
    CLOSING_TIMER --> WAIT_CLOSE[Wait Door Operation Time]
    
    WAIT_OPEN --> DOORS_OPEN[Set Door State: OPEN]
    WAIT_CLOSE --> DOORS_CLOSED[Set Door State: CLOSED]
    
    DOORS_OPEN --> NOTIFY_OPEN[Send door_opened Message]
    DOORS_CLOSED --> NOTIFY_CLOSED[Send door_closed Message]
    
    NOTIFY_OPEN --> CHECK_NEXT1{More Targets?}
    NOTIFY_CLOSED --> CHECK_NEXT2{More Targets?}
    
    CHECK_NEXT1 -->|No| START_TIMEOUT[Start Auto-Close Timer]
    CHECK_NEXT1 -->|Yes| COMPLETE1[Complete Task]
    
    CHECK_NEXT2 -->|Yes| START_MOVEMENT[Request Movement]
    CHECK_NEXT2 -->|No| IDLE[Return to Idle]
    
    START_TIMEOUT --> AUTO_CLOSE
    START_MOVEMENT --> END([End])
    COMPLETE1 --> END
    IDLE --> END
    IGNORE1 --> END
    IGNORE2 --> END
    IGNORE3 --> IGNORE3
    IGNORE4 --> IGNORE4
```

---

## Sequence Diagrams

### 1. External System Elevator Call Sequence

```mermaid
sequenceDiagram
    participant EXT as External System
    participant API as ElevatorAPI
    participant DISP as Dispatcher
    participant ELV as Elevator
    participant WS as WebSocketBridge
    participant UI as Web Frontend
    
    EXT->>+API: call_up@2
    API->>API: _parse_and_execute()
    API->>+DISP: add_call(2, "up")
    DISP->>DISP: create Call object
    DISP->>DISP: _process_pending_calls()
    
    loop For each elevator
        DISP->>+ELV: calculate_estimated_time(2, "up")
        ELV-->>-DISP: estimated_time
    end
    
    DISP->>DISP: select best elevator
    DISP->>+ELV: assign_task(2, call_id)
    ELV->>ELV: add Task to queue
    ELV-->>-DISP: task assigned
    DISP-->>-API: call processed
    API-->>-EXT: success/failure response
    
    ELV->>ELV: request_movement_if_needed()
    ELV->>ELV: state = MOVING_UP
    
    loop Until arrival
        ELV->>ELV: update() - movement logic
    end
    
    ELV->>ELV: arrive at floor 2
    ELV->>+API: send_floor_arrived_message()
    API-->>EXT: up_floor_2_arrived#1
    API-->>-ELV: message sent
    
    ELV->>ELV: open_door()
    ELV->>ELV: door_state = OPENING
    ELV->>+API: send_door_opened_message()
    API-->>EXT: door_opened#1
    API-->>-ELV: message sent
    
    ELV->>+WS: state update
    WS->>+UI: elevator state update
    UI->>UI: updateElevatorUI()
    UI-->>-WS: UI updated
    WS-->>-ELV: sync complete
```

### 2. Frontend Floor Selection Sequence

```mermaid
sequenceDiagram
    participant USER as User
    participant UI as Web Frontend
    participant WS as WebSocketBridge
    participant API as ElevatorAPI
    participant ELV as Elevator
    participant DISP as Dispatcher
    
    USER->>+UI: selectFloor(3, 1)
    UI->>UI: highlightElevatorButton(3, 1)
    UI->>+WS: {"function": "ui_select_floor", "params": {"floor": 3, "elevatorId": 1}}
    
    WS->>WS: _handle_message()
    WS->>+API: ui_select_floor({"floor": 3, "elevatorId": 1})
    API->>API: _handle_select_floor(3, 1)
    API->>+DISP: assign_task(0, 3, None)
    
    DISP->>+ELV: add Task(floor=3, call_id=None)
    ELV->>ELV: task_queue.append(Task)
    ELV-->>-DISP: task added
    DISP-->>-API: task assigned
    
    API->>API: {"status": "success", "message": "..."}
    API-->>-WS: JSON response
    WS-->>-UI: success response
    UI-->>-USER: visual feedback
    
    ELV->>ELV: request_movement_if_needed()
    ELV->>ELV: _determine_direction()
    ELV->>ELV: state = MOVING_UP
    
    loop Movement and Updates
        ELV->>ELV: update()
        ELV->>+WS: state change
        WS->>+UI: real-time update
        UI->>UI: updateElevatorUI()
        UI-->>-WS: updated
        WS-->>-ELV: synced
    end
    
    ELV->>ELV: arrive at floor 3
    ELV->>ELV: open doors automatically
    ELV->>ELV: remove completed task
```

### 3. System State Synchronization Sequence

```mermaid
sequenceDiagram
    participant APP as ElevatorApp
    participant SIM as Simulator
    participant ELV as Elevator
    participant DISP as Dispatcher
    participant WS as WebSocketBridge
    participant UI as Web Frontend
    
    loop Main Update Loop (10 FPS)
        APP->>APP: update()
        APP->>+SIM: update()
        
        SIM->>+ELV: update() [for each elevator]
        ELV->>ELV: process movement/doors
        ELV-->>-SIM: state updated
        
        SIM->>+DISP: update()
        DISP->>DISP: _process_pending_calls()
        DISP-->>-SIM: dispatch updated
        
        SIM-->>-APP: backend updated
        
        APP->>+WS: sync_backend()
        WS->>WS: fetch_states()
        WS->>WS: _broadcast_state_update()
        WS->>+UI: state update message
        UI->>UI: updateElevatorUI()
        UI-->>-WS: UI updated
        WS-->>-APP: sync complete
    end
```

---

## Functional Requirements

### FR1: Elevator Movement Management
- **FR1.1**: System shall operate two elevators independently across floors -1, 1, 2, and 3
- **FR1.2**: Each elevator shall move at a rate of one floor per 2 seconds
- **FR1.3**: System shall skip floor 0 during movement calculations
- **FR1.4**: Elevators shall announce arrival at each floor with directional context

### FR2: Door Operation Management
- **FR2.1**: Elevator doors shall automatically open upon arrival at target floors
- **FR2.2**: Doors shall remain open for 3 seconds before automatically closing
- **FR2.3**: Users shall be able to manually open and close doors
- **FR2.4**: Door operations (opening/closing) shall take 1 second each
- **FR2.5**: System shall prevent movement while doors are not fully closed

### FR3: Call Dispatching System
- **FR3.1**: System shall accept floor calls with directional preference (up/down)
- **FR3.2**: Dispatcher shall assign calls to the elevator with minimum estimated service time
- **FR3.3**: System shall handle multiple simultaneous calls efficiently
- **FR3.4**: Inside elevator calls shall take priority over outside calls for the same elevator

### FR4: User Interface Requirements
- **FR4.1**: Web interface shall provide real-time elevator status updates
- **FR4.2**: Users shall be able to call elevators from any floor
- **FR4.3**: Users shall be able to select destination floors from inside elevators
- **FR4.4**: System shall provide visual feedback for all user interactions
- **FR4.5**: Debug panel shall display detailed elevator states when enabled

### FR5: External API Requirements
- **FR5.1**: System shall support ZMQ protocol for external system integration
- **FR5.2**: API shall respond to standardized command formats
- **FR5.3**: System shall send event notifications for door operations and floor arrivals
- **FR5.4**: System shall support reset functionality to return to initial state

### FR6: State Management
- **FR6.1**: System shall maintain consistent state across all interfaces
- **FR6.2**: Each elevator shall track its current floor, direction, and task queue
- **FR6.3**: System shall persist call states until completion
- **FR6.4**: State updates shall be synchronized at 10 FPS minimum
