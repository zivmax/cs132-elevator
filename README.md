# Elevator Simulation System

This project is a simulation of a multi-elevator system, featuring a Python-based backend for logic and state management, and a web-based frontend for visualization and interaction. It supports both a graphical user interface (GUI) mode and a headless mode for backend-only operations.

## Features

- **Multi-Elevator Simulation:** Simulates a system with multiple elevators (defaults to 2).
- **User Interaction:** Handles various user requests:
    - Calling an elevator to a specific floor (up/down).
    - Selecting a target floor from within an elevator.
    - Manually opening/closing elevator doors.
    - Resetting the system to its initial state.
- **Real-time Frontend Updates:** Elevator states, positions, and door statuses are updated in real-time on the web frontend.
- **GUI Mode:** Utilizes PyQt6 and QWebEngineView to display an HTML/CSS/JavaScript frontend, providing a visual representation of the elevator system.
- **Headless Mode:** Allows the simulation backend to run without the GUI, useful for testing or integration with custom clients.
    - Exposes a WebSocket server for custom frontend connections.
    - Optionally runs an HTTP server to serve the frontend static files.
- **External System Communication:** Interacts with an external test server or client application via ZMQ for receiving commands and sending system responses.
- **Efficient Dispatching:** Implements logic to dispatch elevators efficiently based on calls and current loads.
- **Automatic Operations:** Features automatic door closing after a timeout period.

## System Architecture

The system is composed of a backend, a frontend (in GUI mode), and communication layers.

### Backend

The backend is written in Python and manages the core simulation logic:

- **`World`**: The main orchestrator of the simulation. It contains all simulation entities (elevators, engine, dispatcher), manages the main update loop, and handles communication with the ZMQ test server.
- **`Elevator`**: Represents an individual elevator. It manages its current floor, task queue (target floors), movement state (idle, moving up/down), door state (open, closed, opening, closing), and handles automatic door operations. It communicates its state changes and requests movement from the `Engine`.
- **`Dispatcher`**: Responsible for receiving elevator call requests (from outside the elevators) and assigning them to the most suitable elevator to optimize efficiency. It manages and optimizes the task queue for each elevator.
- **`Engine`**: Simulates the physical movement of the elevators. It processes movement requests from `Elevator` objects and updates their floor positions over time.
- **`ElevatorAPI`**: Acts as a central interface for handling incoming requests from both the ZMQ client (test server) and WebSocket clients (frontend). It parses these requests and delegates actions to the `Dispatcher` or `Elevator` objects. It also formats and sends system responses/events.
- **`ZmqCoordinator`**: Manages ZMQ communication with an external test server, handling incoming commands and sending outgoing messages.
- **`WebSocketServer`**: (Used by `WebSocketBridge`) Provides a WebSocket endpoint for frontend clients to connect to, enabling real-time bidirectional communication.
- **`ElevatorHTTPServer`**: An optional simple HTTP server to serve the static frontend files (HTML, CSS, JS).

### Frontend (GUI Mode)

- **`ElevatorWebview`**: A PyQt6 `QMainWindow` that uses `QWebEngineView` to render the web-based user interface.
- **User Interface:** Built with HTML, CSS, and JavaScript, located in `src/frontend/ui/`. It visualizes elevator positions, states, and allows user interaction.
- **`WebSocketBridge`**: Facilitates communication between the Python backend (specifically `ElevatorAPI` and `World`) and the JavaScript frontend through WebSockets. It sends state updates to the frontend and relays user actions from the frontend to the backend.

### Communication Protocols

- **External Test Server (ZMQ):**
    - The backend listens for commands from a ZMQ client.
    - It sends system event messages back to the ZMQ client.
- **Frontend (WebSockets):**
    - The frontend connects to a WebSocket server hosted by the backend.
    - Real-time state synchronization and user commands are exchanged as JSON messages.

## User Requests (ZMQ Interface)

The system accepts the following commands, typically sent via a ZMQ client. The format often includes the elevator ID (e.g., `#1`, `#2`) and floor numbers.

- **`open_door#{elevator_id}`**: A user inside `elevator_id` presses the open door button.
    - Example: `open_door#1`
- **`close_door#{elevator_id}`**: A user inside `elevator_id` presses the close door button.
    - Example: `close_door#2`
- **`call_up@{floor}`**: A user on `floor` presses the button to call an elevator to go upwards.
    - Valid floors: -1, 1, 2, 3 (example, verify with system configuration)
    - Example: `call_up@1`
- **`call_down@{floor}`**: A user on `floor` presses the button to call an elevator to go downwards.
    - Valid floors: -1, 1, 2, 3 (example, verify with system configuration)
    - Example: `call_down@3`
- **`select_floor@{floor}#{elevator_id}`**: A user inside `elevator_id` selects `floor` as their destination.
    - Example: `select_floor@2#1` (go to floor 2 in elevator 1)
- **`reset`**: Resets the elevator system state machines to their initial conditions.

## System Responses (ZMQ Interface)

The system sends the following responses/events, typically to a ZMQ client:

- **`door_opened#{elevator_id}`**: The doors of `elevator_id` have opened.
    - Example: `door_opened#1`
- **`door_closed#{elevator_id}`**: The doors of `elevator_id` have closed.
    - Example: `door_closed#1`
- **Floor Arrival Messages**:
    - Format: `{direction_prefix}floor_{floor_number}_arrived#{elevator_id}`
    - `direction_prefix` can be `up_`, `down_`, or empty (if stopped or direction not relevant for arrival).
    - Examples:
        - `up_floor_1_arrived#1`: Elevator #1 arrived at floor 1 moving upwards.
        - `floor_2_arrived#2`: Elevator #2 arrived and stopped at floor 2.

## Initial System State

- The system starts with two elevators (Elevator #1 and Elevator #2).
- Both elevators are initially positioned at the first floor (Floor 1).
- The doors of both elevators are closed.

## Setup and Installation

1.  **Python:** Ensure you have Python 3.x installed.
2.  **Dependencies:** Install the required Python packages using pip and the provided `requirements.txt` file:
    ```bash
    pip install -r release/requirements.txt
    ```
    Key dependencies include `PyQt6`, `websockets`, and `pyzmq`.

## Running the Application

The application can be run in several modes using `src/main.py`:

### 1. Standard GUI Mode

This mode launches the backend simulation along with the PyQt6-based web frontend.

```bash
python src/main.py
```

### 2. Headless Mode (WebSocket Server Only)

This mode runs the backend simulation and exposes a WebSocket server for custom frontend applications or test clients to connect. No GUI window is launched.

```bash
python src/main.py --headless --ws-port <port>
```

- Replace `<port>` with your desired WebSocket port number.
- Default WebSocket port: `18675`.
- Example: `python src/main.py --headless --ws-port 18675`
- The WebSocket server will be available at `ws://127.0.0.1:<port>`.

### 3. Headless Mode (WebSocket Server + HTTP Server for Frontend Files)

This mode runs the backend simulation, the WebSocket server, and an additional HTTP server to serve the static frontend files (HTML, CSS, JS). This is useful if you want to access the standard web frontend via a browser while running the backend headlessly.

```bash
python src/main.py --headless --ws-port <ws_port> --http-port <http_port>
```

- Replace `<ws_port>` and `<http_port>` with your desired port numbers.
- Default WebSocket port: `18675`.
- Default HTTP port: `19090`.
- Example: `python src/main.py --headless --ws-port 18675 --http-port 19090`
- The frontend can then be accessed at `http://127.0.0.1:<http_port>`.

### Command-Line Options

- `--debug`: Action, if specified, may enable debug features (e.g., show debug panel in GUI).
- `--cdp <port>`: Specify the Chromium DevTools Protocol port for debugging the QWebEngineView content. Default: `19982`.
- `--ws-port <port>`: Set the port for the WebSocket server. Default: `18675`.
- `--http-port <port>`: Set the port for the HTTP server (for serving frontend files). Default: `19090`.
- `--headless`: Action, if specified, runs the application in headless mode (no GUI).

## Directory Structure

- `src/`: Contains the main source code.
    - `main.py`: The main entry point for the application.
    - `backend/`: Core backend logic (simulation engine, elevator controls, API, ZMQ/WebSocket servers).
    - `frontend/`: Components related to the graphical frontend (PyQt6 webview, WebSocket bridge, HTML/CSS/JS UI files in `frontend/ui/`).
- `doc/`: Project documentation, including requirements, design specifications, and user manuals.
- `test/`: Test scripts and related files for verifying system functionality.
- `release/`: Files related to packaging and distribution, including `requirements.txt`.
- `LICENSE`: Project license file.
- `README.md`: This file.

## License

This project is distributed under the terms specified in the `LICENSE` file.
