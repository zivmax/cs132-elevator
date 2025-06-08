# Traceability Documentation

## Table of Contents

- [Traceability Documentation](#traceability-documentation)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [ID Assignment Scheme](#id-assignment-scheme)
    - [Requirements (REQ)](#requirements-req)
    - [Use Cases (UC)](#use-cases-uc)
    - [Specifications (SPEC)](#specifications-spec)
    - [Implementation (CODE)](#implementation-code)
    - [Test Cases (TEST)](#test-cases-test)
  - [Requirements Traceability](#requirements-traceability)
    - [REQ-R1: Passenger Perspective Requirements](#req-r1-passenger-perspective-requirements)
    - [REQ-R2: Elevator Compartment Requirements](#req-r2-elevator-compartment-requirements)
    - [REQ-R3: Elevator Control System Requirements](#req-r3-elevator-control-system-requirements)
    - [REQ-R4: Visual Component Requirements](#req-r4-visual-component-requirements)
    - [Use Cases](#use-cases)
  - [Specifications Traceability](#specifications-traceability)
    - [SPEC-S1: Target Floor Implementation](#spec-s1-target-floor-implementation)
    - [SPEC-S2: Call Up/Down Implementation](#spec-s2-call-updown-implementation)
    - [SPEC-S3: Door Control Implementation](#spec-s3-door-control-implementation)
    - [SPEC-S4: Movement Control Implementation](#spec-s4-movement-control-implementation)
    - [SPEC-S5: Dispatcher Implementation](#spec-s5-dispatcher-implementation)
    - [SPEC-S6: Communication Protocols](#spec-s6-communication-protocols)
    - [SPEC-S7: State Update Implementation](#spec-s7-state-update-implementation)
  - [Implementation Traceability](#implementation-traceability)
    - [CODE-C1: Core Backend Classes](#code-c1-core-backend-classes)
    - [CODE-C2: API and Communication](#code-c2-api-and-communication)
    - [CODE-C3: Frontend Implementation](#code-c3-frontend-implementation)
    - [CODE-C4: Utility and Support](#code-c4-utility-and-support)
  - [Test Coverage Traceability](#test-coverage-traceability)
    - [TEST-UT: Unit Tests](#test-ut-unit-tests)
    - [TEST-IT: Integration Tests](#test-it-integration-tests)
    - [TEST-ST: System Tests](#test-st-system-tests)
  - [Master Traceability Matrix](#master-traceability-matrix)

---

## Overview

This document establishes complete traceability from high-level requirements through specifications, implementation, and test coverage for the Elevator Simulation System. Every requirement is mapped to its implementation and verification to ensure comprehensive coverage and compliance.

---

## ID Assignment Scheme

### Requirements (REQ)
- **REQ-R1.x**: Passenger perspective requirements
- **REQ-R2.x**: Elevator compartment requirements
- **REQ-R3.x**: Control system requirements
- **REQ-R4.x**: Visual component requirements

### Use Cases (UC)
- **UC-01** through **UC-09**: System use cases

### Specifications (SPEC)
- **SPEC-S1.x**: Target floor implementation
- **SPEC-S2.x**: Call up/down implementation
- **SPEC-S3.x**: Door control implementation
- **SPEC-S4.x**: Movement control implementation
- **SPEC-S5.x**: Dispatcher implementation
- **SPEC-S6.x**: Communication protocols
- **SPEC-S7.x**: State update implementation

### Implementation (CODE)
- **CODE-C1.x**: Core backend classes
- **CODE-C2.x**: API and communication
- **CODE-C3.x**: Frontend implementation
- **CODE-C4.x**: Utility and support

### Test Cases (TEST)
- **TEST-UT.x**: Unit tests
- **TEST-IT.x**: Integration tests
- **TEST-ST.x**: System tests

---

## Requirements Traceability

Based on the functional requirements from requirement.md, the following requirements have been identified:

### FR1: Elevator Movement Management

| ID      | Description                                                    | Priority | Status        | Source    |
| ------- | -------------------------------------------------------------- | -------- | ------------- | --------- |
| FR1.1   | System shall operate two elevators independently across floors -1, 1, 2, and 3 | High | ✅ Implemented | FR1.1 |
| FR1.2   | Each elevator shall move at a rate of one floor per 2 seconds | High     | ✅ Implemented | FR1.2     |
| FR1.3   | System shall skip floor 0 during movement calculations        | High     | ✅ Implemented | FR1.3     |
| FR1.4   | Elevators shall announce arrival at each floor with directional context | Medium | ✅ Implemented | FR1.4 |

### FR2: Door Operation Management

| ID      | Description                                                    | Priority | Status        | Source    |
| ------- | -------------------------------------------------------------- | -------- | ------------- | --------- |
| FR2.1   | Elevator doors shall automatically open upon arrival at target floors | High | ✅ Implemented | FR2.1 |
| FR2.2   | Doors shall remain open for 3 seconds before automatically closing | High | ✅ Implemented | FR2.2 |
| FR2.3   | Users shall be able to manually open and close doors         | Medium   | ✅ Implemented | FR2.3     |
| FR2.4   | Door operations (opening/closing) shall take 1 second each   | Medium   | ✅ Implemented | FR2.4     |
| FR2.5   | System shall prevent movement while doors are not fully closed | High   | ✅ Implemented | FR2.5     |

### FR3: Call Dispatching System

| ID      | Description                                                    | Priority | Status        | Source    |
| ------- | -------------------------------------------------------------- | -------- | ------------- | --------- |
| FR3.1   | System shall accept floor calls with directional preference (up/down) | High | ✅ Implemented | FR3.1 |
| FR3.2   | Dispatcher shall assign calls to the elevator with minimum estimated service time | High | ✅ Implemented | FR3.2 |
| FR3.3   | System shall handle multiple simultaneous calls efficiently  | High     | ✅ Implemented | FR3.3     |
| FR3.4   | Inside elevator calls shall take priority over outside calls for the same elevator | Medium | ✅ Implemented | FR3.4 |

### FR4: User Interface Requirements

| ID      | Description                                                    | Priority | Status        | Source    |
| ------- | -------------------------------------------------------------- | -------- | ------------- | --------- |
| FR4.1   | Web interface shall provide real-time elevator status updates | High     | ✅ Implemented | FR4.1     |
| FR4.2   | Users shall be able to call elevators from any floor         | High     | ✅ Implemented | FR4.2     |
| FR4.3   | Users shall be able to select destination floors from inside elevators | High | ✅ Implemented | FR4.3 |
| FR4.4   | System shall provide visual feedback for all user interactions | Medium  | ✅ Implemented | FR4.4     |
| FR4.5   | Debug panel shall display detailed elevator states when enabled | Low    | ✅ Implemented | FR4.5     |

### Use Cases

Based on the use case descriptions from requirement.md:

| ID    | Description                | Actors                  | Priority | Status        | Source |
| ----- | -------------------------- | ----------------------- | -------- | ------------- | ------ |
| UC-01 | Call Elevator from Floor   | User, External System   | High     | ✅ Implemented | UC1    |
| UC-02 | Select Destination Floor   | User, External System   | High     | ✅ Implemented | UC2    |
| UC-03 | Open Door Manually         | User, External System   | Medium   | ✅ Implemented | UC3    |
| UC-04 | Close Door Manually        | User, External System   | Medium   | ✅ Implemented | UC4    |
| UC-05 | Reset System               | Admin, External System  | Low      | ✅ Implemented | UC5    |
| UC-06 | Dispatch Elevator          | System                  | High     | ✅ Implemented | UC6    |
| UC-07 | Move Elevator              | System                  | High     | ✅ Implemented | UC7    |
| UC-08 | Auto Door Operations       | System                  | High     | ✅ Implemented | UC8    |
| UC-09 | State Synchronization      | System                  | High     | ✅ Implemented | UC9    |

---

## Specifications Traceability

Based on the method specifications from specification.md:

### SPEC-S1: Simulator Implementation

| ID        | Description                                  | Related Requirements | Status        | Methods |
| --------- | -------------------------------------------- | -------------------- | ------------- | ------- |
| SPEC-S1.1 | Initialize simulation with empty references  | FR1.1                | ✅ Implemented | `Simulator.__init__()` |
| SPEC-S1.2 | Set API reference and initialize components  | FR1.1, FR3.1         | ✅ Implemented | `Simulator.set_api_and_initialize_components()` |
| SPEC-S1.3 | Main update loop for simulation state       | FR1.1, FR4.1         | ✅ Implemented | `Simulator.update()` |
| SPEC-S1.4 | Reset all simulation components to initial state | UC-05             | ✅ Implemented | `Simulator.reset()` |

### SPEC-S2: ElevatorAPI Implementation

| ID        | Description                                  | Related Requirements | Status        | Methods |
| --------- | -------------------------------------------- | -------------------- | ------------- | ------- |
| SPEC-S2.1 | Initialize API with ZMQ communication       | FR3.1                | ✅ Implemented | `ElevatorAPI.__init__()` |
| SPEC-S2.2 | Parse and execute incoming ZMQ commands     | FR3.1, FR4.2, FR4.3  | ✅ Implemented | `ElevatorAPI._parse_and_execute()` |
| SPEC-S2.3 | Handle elevator call requests from floors   | FR3.1, FR4.2         | ✅ Implemented | `ElevatorAPI._handle_call_elevator()` |
| SPEC-S2.4 | Handle floor selection from within elevators | FR4.3               | ✅ Implemented | `ElevatorAPI._handle_select_floor()` |
| SPEC-S2.5 | Manual door open operations                  | FR2.3                | ✅ Implemented | `ElevatorAPI._handle_open_door()` |
| SPEC-S2.6 | Manual door close operations                 | FR2.3                | ✅ Implemented | `ElevatorAPI._handle_close_door()` |
| SPEC-S2.7 | Send door opened messages via ZMQ           | FR1.4                | ✅ Implemented | `ElevatorAPI.send_door_opened_message()` |
| SPEC-S2.8 | Send door closed messages via ZMQ           | FR1.4                | ✅ Implemented | `ElevatorAPI.send_door_closed_message()` |
| SPEC-S2.9 | Send floor arrival messages with direction  | FR1.4                | ✅ Implemented | `ElevatorAPI.send_floor_arrived_message()` |
| SPEC-S2.10| Fetch current state of all elevators        | FR4.1                | ✅ Implemented | `ElevatorAPI.fetch_states()` |
| SPEC-S2.11| Handle UI-originated call elevator requests | FR4.2                | ✅ Implemented | `ElevatorAPI.ui_call_elevator()` |
| SPEC-S2.12| Handle UI-originated floor selection        | FR4.3                | ✅ Implemented | `ElevatorAPI.ui_select_floor()` |
| SPEC-S2.13| Handle UI-originated door open requests     | FR2.3                | ✅ Implemented | `ElevatorAPI.ui_open_door()` |
| SPEC-S2.14| Handle UI-originated door close requests    | FR2.3                | ✅ Implemented | `ElevatorAPI.ui_close_door()` |

### SPEC-S3: Dispatcher Implementation

| ID        | Description                                  | Related Requirements | Status        | Methods |
| --------- | -------------------------------------------- | -------------------- | ------------- | ------- |
| SPEC-S3.1 | Initialize dispatcher with world and API refs| FR3.1               | ✅ Implemented | `Dispatcher.__init__()` |
| SPEC-S3.2 | Add outside call request and process queue   | FR3.1, FR3.2         | ✅ Implemented | `Dispatcher.add_call()` |
| SPEC-S3.3 | Create new call object with unique ID       | FR3.1                | ✅ Implemented | `Dispatcher.add_outside_call()` |
| SPEC-S3.4 | Assign task to specific elevator            | FR3.2, FR3.4         | ✅ Implemented | `Dispatcher.assign_task()` |
| SPEC-S3.5 | Retrieve direction for pending call by ID   | FR3.1                | ✅ Implemented | `Dispatcher.get_call_direction()` |
| SPEC-S3.6 | Mark call as completed and remove from queue| FR3.3                | ✅ Implemented | `Dispatcher.complete_call()` |
| SPEC-S3.7 | Process all pending calls with optimization | FR3.2, FR3.3         | ✅ Implemented | `Dispatcher._process_pending_calls()` |
| SPEC-S3.8 | Optimize elevator task queue using SCAN     | FR3.2, FR3.3         | ✅ Implemented | `Dispatcher._optimize_task_queue()` |

### SPEC-S4: Elevator Control and Movement

| ID        | Description                                  | Related Requirements | Status        | Source |
| --------- | -------------------------------------------- | -------------------- | ------------- | ------ |
| SPEC-S4.1 | Elevator movement states and transitions    | FR1.2, FR1.3, FR2.5  | ✅ Implemented | Elevator class |
| SPEC-S4.2 | Direction determination logic               | FR1.2, FR3.2         | ✅ Implemented | Elevator class |
| SPEC-S4.3 | Floor-by-floor movement simulation         | FR1.2, FR1.3         | ✅ Implemented | Elevator class |
| SPEC-S4.4 | Movement request handling and validation    | FR2.5                | ✅ Implemented | Elevator class |

### SPEC-S5: Door Control Implementation

| ID        | Description                                  | Related Requirements | Status        | Source |
| --------- | -------------------------------------------- | -------------------- | ------------- | ------ |
| SPEC-S5.1 | Automatic door operations on arrival       | FR2.1                | ✅ Implemented | Elevator class |
| SPEC-S5.2 | Door timeout and auto-close mechanism      | FR2.2                | ✅ Implemented | Elevator class |
| SPEC-S5.3 | Manual door control interface               | FR2.3                | ✅ Implemented | API + Elevator |
| SPEC-S5.4 | Door operation timing (1 second each)      | FR2.4                | ✅ Implemented | Elevator class |
| SPEC-S5.5 | Door state management and validation        | FR2.5                | ✅ Implemented | Elevator class |

### SPEC-S6: Communication Protocols

| ID        | Description                                  | Related Requirements | Status        | Source |
| --------- | -------------------------------------------- | -------------------- | ------------- | ------ |
| SPEC-S6.1 | ZMQ external API communication              | FR3.1                | ✅ Implemented | ElevatorAPI + ZMQ |
| SPEC-S6.2 | WebSocket frontend communication            | FR4.1                | ✅ Implemented | WebSocketBridge |
| SPEC-S6.3 | Message formatting and parsing              | FR3.1, FR4.1         | ✅ Implemented | ElevatorAPI |
| SPEC-S6.4 | Real-time state synchronization             | FR4.1                | ✅ Implemented | WebSocketBridge |

### SPEC-S7: User Interface Implementation

| ID        | Description                                  | Related Requirements | Status        | Source |
| --------- | -------------------------------------------- | -------------------- | ------------- | ------ |
| SPEC-S7.1 | Web interface for real-time status updates  | FR4.1, FR4.4         | ✅ Implemented | Frontend |
| SPEC-S7.2 | Floor call buttons and visual feedback      | FR4.2, FR4.4         | ✅ Implemented | Frontend |
| SPEC-S7.3 | Destination floor selection interface       | FR4.3, FR4.4         | ✅ Implemented | Frontend |
| SPEC-S7.4 | Debug panel for detailed elevator states    | FR4.5                | ✅ Implemented | Frontend |

---

## Implementation Traceability

### CODE-C1: Core Backend Classes

| ID        | File/Class                              | Description                      | Related Specifications                     |
| --------- | --------------------------------------- | -------------------------------- | ------------------------------------------ |
| CODE-C1.1 | `src/backend/elevator.py::Elevator`     | Main elevator control logic      | SPEC-S1.2, SPEC-S3.2, SPEC-S4.1, SPEC-S7.1 |
| CODE-C1.2 | `src/backend/dispatcher.py::Dispatcher` | Call assignment and optimization | SPEC-S5.1, SPEC-S5.2, SPEC-S5.3, SPEC-S5.4 |
| CODE-C1.3 | `src/backend/simulator.py::Simulator`   | Main simulation orchestrator     | SPEC-S7.3, SPEC-S7.4                       |
| CODE-C1.4 | `src/backend/models.py`                 | Data structures and enums        | SPEC-S4.1, SPEC-S3.3                       |

### CODE-C2: API and Communication

| ID        | File/Class                                | Description                | Related Specifications          |
| --------- | ----------------------------------------- | -------------------------- | ------------------------------- |
| CODE-C2.1 | `src/backend/api/core.py::ElevatorAPI`    | Central API interface      | SPEC-S6.3, SPEC-S1.4, SPEC-S2.4 |
| CODE-C2.2 | `src/backend/api/server.py`               | WebSocket and HTTP servers | SPEC-S6.1                       |
| CODE-C2.3 | `src/backend/api/zmq.py`                  | ZMQ communication handler  | SPEC-S6.2                       |
| CODE-C2.4 | `src/frontend/bridge.py::WebSocketBridge` | Frontend-backend bridge    | SPEC-S6.1, SPEC-S6.4            |

### CODE-C3: Frontend Implementation

| ID        | File/Path                                | Description                  | Related Specifications          |
| --------- | ---------------------------------------- | ---------------------------- | ------------------------------- |
| CODE-C3.1 | `src/frontend/ui/index.html`             | Main HTML interface          | SPEC-S1.1, SPEC-S2.1, SPEC-S3.1 |
| CODE-C3.2 | `src/frontend/ui/styles.css`             | Visual styling and layout    | SPEC-S1.1, SPEC-S2.1, SPEC-S3.1 |
| CODE-C3.3 | `src/frontend/ui/scripts/elevator-UI.js` | Elevator visualization logic | SPEC-S7.3, SPEC-S6.4            |
| CODE-C3.4 | `src/frontend/ui/scripts/backend.js`     | Backend communication        | SPEC-S6.1                       |
| CODE-C3.5 | `src/frontend/ui/scripts/actions.js`     | User interaction handling    | SPEC-S1.2, SPEC-S2.2, SPEC-S3.2 |

### CODE-C4: Utility and Support

| ID        | File/Class                | Description                    | Related Specifications |
| --------- | ------------------------- | ------------------------------ | ---------------------- |
| CODE-C4.1 | `src/backend/utility.py`  | Helper functions and utilities | SPEC-S7.4              |
| CODE-C4.2 | `src/main.py`             | Application entry point        | All specifications     |
| CODE-C4.3 | `src/frontend/webview.py` | PyQt6 webview wrapper          | SPEC-S6.1              |

---

## Test Coverage Traceability

### TEST-UT: Unit Tests

| ID        | Test File/Class                                           | Description                   | Tested Code | Related Requirements         |
| --------- | --------------------------------------------------------- | ----------------------------- | ----------- | ---------------------------- |
| TEST-UT.1 | `test_elevator_states.py::TestElevatorDoorOperations`     | Door operation unit tests     | CODE-C1.1   | REQ-R1.3, REQ-R2.2           |
| TEST-UT.2 | `test_elevator_states.py::TestElevatorFloorManagement`    | Floor management tests        | CODE-C1.1   | REQ-R1.4, REQ-R2.3           |
| TEST-UT.3 | `test_elevator_states.py::TestElevatorMovementAndUpdates` | Movement and state tests      | CODE-C1.1   | REQ-R2.3, REQ-R4.1           |
| TEST-UT.4 | Dispatcher unit tests (planned)                           | Call assignment logic         | CODE-C1.2   | REQ-R3.1, REQ-R3.2, REQ-R3.4 |
| TEST-UT.5 | API unit tests (planned)                                  | Command parsing and execution | CODE-C2.1   | REQ-R3.1                     |

### TEST-IT: Integration Tests

| ID        | Test Description                      | Components Tested             | Related Specifications |
| --------- | ------------------------------------- | ----------------------------- | ---------------------- |
| TEST-IT.1 | Multi-elevator dispatch coordination  | Dispatcher + Elevators        | SPEC-S5.1, SPEC-S5.4   |
| TEST-IT.2 | Floor selection during movement       | Elevator + Dispatcher + API   | SPEC-S1.3, SPEC-S5.2   |
| TEST-IT.3 | Door control during movement requests | Elevator + API                | SPEC-S3.2, SPEC-S4.4   |
| TEST-IT.4 | WebSocket communication flow          | Frontend + Backend API        | SPEC-S6.1, SPEC-S6.4   |
| TEST-IT.5 | ZMQ external API integration          | Backend API + External System | SPEC-S6.2, SPEC-S6.3   |

### TEST-ST: System Tests

| ID        | Test Scenario                   | Description                                    | End-to-End Coverage               |
| --------- | ------------------------------- | ---------------------------------------------- | --------------------------------- |
| TEST-ST.1 | Basic call and ride             | Complete user journey from call to destination | UC-01, UC-02, UC-06, UC-07, UC-08 |
| TEST-ST.2 | Multi-floor journey with stops  | Multiple users, optimal routing                | UC-01, UC-02, UC-06, UC-09        |
| TEST-ST.3 | Door control operations         | Manual door overrides                          | UC-03, UC-04, UC-08               |
| TEST-ST.4 | System reset functionality      | Complete state restoration                     | UC-05                             |
| TEST-ST.5 | Concurrent multi-user scenarios | Load testing and race conditions               | All use cases                     |
| TEST-ST.6 | Edge case handling              | Boundary conditions and error cases            | All use cases                     |
| TEST-ST.7 | Multi-interface commands        | ZMQ and WebSocket simultaneous use             | UC-09                      |
| TEST-ST.8 | Long-duration operation         | System stability over time                     | All use cases                     |

---

## Master Traceability Matrix

| Requirement | Use Case            | Specification                   | Implementation       | Unit Test            | Integration Test     | System Test | Status |
| ----------- | ------------------- | ------------------------------- | -------------------- | -------------------- | -------------------- | ----------- | ------ |
| REQ-R1.1    | UC-09               | SPEC-S7.3                       | CODE-C3.3            | -                    | TEST-IT.4            | TEST-ST.1   | ✅      |
| REQ-R1.2    | UC-01               | SPEC-S2.1, SPEC-S2.2            | CODE-C3.5, CODE-C2.1 | -                    | TEST-IT.1            | TEST-ST.1   | ✅      |
| REQ-R1.3    | UC-03, UC-04        | SPEC-S3.1, SPEC-S3.2            | CODE-C1.1, CODE-C3.5 | TEST-UT.1            | TEST-IT.3            | TEST-ST.3   | ✅      |
| REQ-R1.4    | UC-02               | SPEC-S1.1, SPEC-S1.2            | CODE-C1.1, CODE-C3.5 | TEST-UT.2            | TEST-IT.2            | TEST-ST.1   | ✅      |
| REQ-R2.1    | UC-02, UC-03, UC-04 | SPEC-S1.2, SPEC-S2.2, SPEC-S3.2 | CODE-C1.1, CODE-C2.1 | TEST-UT.1, TEST-UT.2 | TEST-IT.3            | TEST-ST.1   | ✅      |
| REQ-R2.2    | UC-08               | SPEC-S3.2, SPEC-S3.3, SPEC-S3.4 | CODE-C1.1            | TEST-UT.1            | TEST-IT.3            | TEST-ST.3   | ✅      |
| REQ-R2.3    | UC-07               | SPEC-S4.1, SPEC-S4.2, SPEC-S4.3 | CODE-C1.1            | TEST-UT.3            | TEST-IT.2            | TEST-ST.1   | ✅      |
| REQ-R3.1    | UC-06               | SPEC-S2.4, SPEC-S6.2, SPEC-S6.3 | CODE-C2.1, CODE-C2.3 | TEST-UT.5            | TEST-IT.5            | TEST-ST.7   | ✅      |
| REQ-R3.2    | UC-06               | SPEC-S5.1, SPEC-S5.4            | CODE-C1.2            | TEST-UT.4            | TEST-IT.1            | TEST-ST.5   | ✅      |
| REQ-R3.3    | UC-06, UC-07        | SPEC-S5.2, SPEC-S4.2            | CODE-C1.2, CODE-C1.1 | TEST-UT.4, TEST-UT.3 | TEST-IT.1, TEST-IT.2 | TEST-ST.2   | ✅      |
| REQ-R3.4    | UC-06               | SPEC-S5.1, SPEC-S5.3            | CODE-C1.2            | TEST-UT.4            | TEST-IT.1            | TEST-ST.1   | ✅      |
| REQ-R4.1    | UC-09               | SPEC-S3.3, SPEC-S7.2            | CODE-C3.1, CODE-C3.3 | -                    | TEST-IT.4            | TEST-ST.1   | ✅      |
| REQ-R4.2    | UC-01, UC-02        | SPEC-S1.1, SPEC-S2.1            | CODE-C3.1, CODE-C3.2 | -                    | TEST-IT.4            | TEST-ST.1   | ✅      |
| REQ-R4.3    | -                   | SPEC-S1.1, SPEC-S2.1, SPEC-S3.1 | CODE-C3.1, CODE-C3.2 | -                    | TEST-IT.4            | TEST-ST.1   | ✅      |
| REQ-R4.4    | UC-09               | SPEC-S6.4, SPEC-S7.3            | CODE-C2.4, CODE-C3.3 | -                    | TEST-IT.4            | TEST-ST.1   | ✅      |
