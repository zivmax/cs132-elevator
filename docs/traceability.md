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
- **UC-01** through **UC-10**: System use cases

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

### REQ-R1: Passenger Perspective Requirements

| ID       | Description                                            | Priority | Status        |
| -------- | ------------------------------------------------------ | -------- | ------------- |
| REQ-R1.1 | See elevator's current movement direction and location | High     | ✅ Implemented |
| REQ-R1.2 | Request elevator service by pressing up/down buttons   | High     | ✅ Implemented |
| REQ-R1.3 | Control doors manually (open/close buttons)            | Medium   | ✅ Implemented |
| REQ-R1.4 | Select destination floor using internal panel          | High     | ✅ Implemented |

### REQ-R2: Elevator Compartment Requirements

| ID       | Description                                               | Priority | Status        |
| -------- | --------------------------------------------------------- | -------- | ------------- |
| REQ-R2.1 | Receive commands from passengers through buttons          | High     | ✅ Implemented |
| REQ-R2.2 | Automatically close/open doors when passengers enter/exit | High     | ✅ Implemented |
| REQ-R2.3 | Take orders from control system and move to target floor  | High     | ✅ Implemented |

### REQ-R3: Elevator Control System Requirements

| ID       | Description                                                | Priority | Status        |
| -------- | ---------------------------------------------------------- | -------- | ------------- |
| REQ-R3.1 | Receive signals from elevator compartments                 | High     | ✅ Implemented |
| REQ-R3.2 | Resolve conflicts when multiple passengers request service | High     | ✅ Implemented |
| REQ-R3.3 | Arrange optimal elevator route scheduling                  | High     | ✅ Implemented |
| REQ-R3.4 | Dispatch the closest elevator                              | High     | ✅ Implemented |

### REQ-R4: Visual Component Requirements

| ID       | Description                                        | Priority | Status        |
| -------- | -------------------------------------------------- | -------- | ------------- |
| REQ-R4.1 | Display door status and current floor location     | High     | ✅ Implemented |
| REQ-R4.2 | Provide visual feedback for pressed buttons        | Medium   | ✅ Implemented |
| REQ-R4.3 | Offer intuitive user interface with clear labeling | Medium   | ✅ Implemented |
| REQ-R4.4 | Show real-time updates of elevator status          | High     | ✅ Implemented |

### Use Cases

| ID    | Description                | Actors                  | Status        |
| ----- | -------------------------- | ----------------------- | ------------- |
| UC-01 | Call Elevator from Floor   | User, External System   | ✅ Implemented |
| UC-02 | Select Destination Floor   | User, External System   | ✅ Implemented |
| UC-03 | Open Door Manually         | User, External System   | ✅ Implemented |
| UC-04 | Close Door Manually        | User, External System   | ✅ Implemented |
| UC-05 | Reset System               | Admin, External System  | ✅ Implemented |
| UC-06 | Dispatch Elevator          | System                  | ✅ Implemented |
| UC-07 | Move Elevator              | System                  | ✅ Implemented |
| UC-08 | Auto Door Operations       | System                  | ✅ Implemented |
| UC-09 | State Synchronization      | System                  | ✅ Implemented |
| UC-10 | External API Communication | System, External System | ✅ Implemented |

---

## Specifications Traceability

### SPEC-S1: Target Floor Implementation

| ID        | Description                             | Related Requirements | Status        |
| --------- | --------------------------------------- | -------------------- | ------------- |
| SPEC-S1.1 | Floor button GUI design and states      | REQ-R1.4, REQ-R4.2   | ✅ Implemented |
| SPEC-S1.2 | Floor button state logic implementation | REQ-R1.4, REQ-R2.1   | ✅ Implemented |
| SPEC-S1.3 | Multiple floor selection stacking       | REQ-R3.3             | ✅ Implemented |
| SPEC-S1.4 | Backend command processing              | REQ-R2.1, REQ-R3.1   | ✅ Implemented |

### SPEC-S2: Call Up/Down Implementation

| ID        | Description                        | Related Requirements | Status        |
| --------- | ---------------------------------- | -------------------- | ------------- |
| SPEC-S2.1 | Call button GUI design             | REQ-R1.2, REQ-R4.2   | ✅ Implemented |
| SPEC-S2.2 | Call button click event handling   | REQ-R1.2, REQ-R2.1   | ✅ Implemented |
| SPEC-S2.3 | Direction-based floor restrictions | REQ-R1.2             | ✅ Implemented |
| SPEC-S2.4 | Backend call processing            | REQ-R3.1, REQ-R3.4   | ✅ Implemented |

### SPEC-S3: Door Control Implementation

| ID        | Description                   | Related Requirements | Status        |
| --------- | ----------------------------- | -------------------- | ------------- |
| SPEC-S3.1 | Manual door control interface | REQ-R1.3, REQ-R4.1   | ✅ Implemented |
| SPEC-S3.2 | Automatic door operations     | REQ-R2.2             | ✅ Implemented |
| SPEC-S3.3 | Door state management         | REQ-R2.2, REQ-R4.1   | ✅ Implemented |
| SPEC-S3.4 | Door timeout and auto-close   | REQ-R2.2             | ✅ Implemented |

### SPEC-S4: Movement Control Implementation

| ID        | Description                        | Related Requirements | Status        |
| --------- | ---------------------------------- | -------------------- | ------------- |
| SPEC-S4.1 | Elevator movement states           | REQ-R2.3, REQ-R4.1   | ✅ Implemented |
| SPEC-S4.2 | Direction determination logic      | REQ-R3.3             | ✅ Implemented |
| SPEC-S4.3 | Floor-by-floor movement simulation | REQ-R2.3             | ✅ Implemented |
| SPEC-S4.4 | Movement request handling          | REQ-R2.3, REQ-R3.1   | ✅ Implemented |

### SPEC-S5: Dispatcher Implementation

| ID        | Description                     | Related Requirements | Status        |
| --------- | ------------------------------- | -------------------- | ------------- |
| SPEC-S5.1 | Call assignment algorithm       | REQ-R3.2, REQ-R3.4   | ✅ Implemented |
| SPEC-S5.2 | Task queue optimization         | REQ-R3.3             | ✅ Implemented |
| SPEC-S5.3 | Elevator suitability evaluation | REQ-R3.4             | ✅ Implemented |
| SPEC-S5.4 | Conflict resolution             | REQ-R3.2             | ✅ Implemented |

### SPEC-S6: Communication Protocols

| ID        | Description                      | Related Requirements | Status        |
| --------- | -------------------------------- | -------------------- | ------------- |
| SPEC-S6.1 | WebSocket frontend communication | REQ-R4.4             | ✅ Implemented |
| SPEC-S6.2 | ZMQ external API communication   | REQ-R3.1             | ✅ Implemented |
| SPEC-S6.3 | Message formatting and parsing   | REQ-R3.1             | ✅ Implemented |
| SPEC-S6.4 | Real-time state synchronization  | REQ-R4.4             | ✅ Implemented |

### SPEC-S7: State Update Implementation

| ID        | Description                  | Related Requirements | Status        |
| --------- | ---------------------------- | -------------------- | ------------- |
| SPEC-S7.1 | Timed movement updates       | REQ-R2.3             | ✅ Implemented |
| SPEC-S7.2 | Door and state transitions   | REQ-R2.2, REQ-R4.1   | ✅ Implemented |
| SPEC-S7.3 | Event notification system    | REQ-R4.4             | ✅ Implemented |
| SPEC-S7.4 | State consistency management | REQ-R4.4             | ✅ Implemented |

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
| TEST-ST.7 | Multi-interface commands        | ZMQ and WebSocket simultaneous use             | UC-10, UC-09                      |
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
| REQ-R3.1    | UC-06, UC-10        | SPEC-S2.4, SPEC-S6.2, SPEC-S6.3 | CODE-C2.1, CODE-C2.3 | TEST-UT.5            | TEST-IT.5            | TEST-ST.7   | ✅      |
| REQ-R3.2    | UC-06               | SPEC-S5.1, SPEC-S5.4            | CODE-C1.2            | TEST-UT.4            | TEST-IT.1            | TEST-ST.5   | ✅      |
| REQ-R3.3    | UC-06, UC-07        | SPEC-S5.2, SPEC-S4.2            | CODE-C1.2, CODE-C1.1 | TEST-UT.4, TEST-UT.3 | TEST-IT.1, TEST-IT.2 | TEST-ST.2   | ✅      |
| REQ-R3.4    | UC-06               | SPEC-S5.1, SPEC-S5.3            | CODE-C1.2            | TEST-UT.4            | TEST-IT.1            | TEST-ST.1   | ✅      |
| REQ-R4.1    | UC-09               | SPEC-S3.3, SPEC-S7.2            | CODE-C3.1, CODE-C3.3 | -                    | TEST-IT.4            | TEST-ST.1   | ✅      |
| REQ-R4.2    | UC-01, UC-02        | SPEC-S1.1, SPEC-S2.1            | CODE-C3.1, CODE-C3.2 | -                    | TEST-IT.4            | TEST-ST.1   | ✅      |
| REQ-R4.3    | -                   | SPEC-S1.1, SPEC-S2.1, SPEC-S3.1 | CODE-C3.1, CODE-C3.2 | -                    | TEST-IT.4            | TEST-ST.1   | ✅      |
| REQ-R4.4    | UC-09               | SPEC-S6.4, SPEC-S7.3            | CODE-C2.4, CODE-C3.3 | -                    | TEST-IT.4            | TEST-ST.1   | ✅      |
