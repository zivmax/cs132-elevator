// Global variables for backend communication
// let backend; // Will be replaced by the const backend object below

// Helper function to create event emitters
function createEventEmitter() {
    const listeners = [];
    return {
        connect: function(callback) {
            listeners.push(callback);
        },
        emit: function(data) {
            listeners.forEach(cb => {
                try {
                    cb(data);
                } catch (e) {
                    console.error("Error in event listener:", e);
                }
            });
        }
        // Optional: disconnect function if needed later
        // disconnect: function(callback) {
        //     const index = listeners.indexOf(callback);
        //     if (index > -1) {
        //         listeners.splice(index, 1);
        //     }
        // }
    };
}

// Define the backend object for WebSocket communication
const backend = {
    socket: null,
    _isConnected: false,
    elevatorUpdated: createEventEmitter(), // Emitter for elevator updates
    floorCalled: createEventEmitter(),   // Emitter for floor calls
    _pendingPromise: null, // ADDED: To store resolve/reject for sendToBackend

    init: function(url) {
        this.socket = new WebSocket(url);

        this.socket.onopen = () => {
            this._isConnected = true; // Set connected flag
            console.log("js: WebSocket connection established to", url);
            // If there was a promise pending from a previous connection attempt,
            // it should ideally be handled or cleared. For now, we assume fresh init.
        };

        this.socket.onmessage = (event) => {
            console.log("[Debug] Raw event.data:", event.data);
            console.log("[Debug] Type of event.data:", typeof event.data);

            let message;
            try {
                message = JSON.parse(event.data);
            } catch (e) {
                console.error("js: Error parsing JSON from backend:", e, "Raw data:", event.data);
                if (this._pendingPromise && typeof this._pendingPromise.reject === 'function') {
                    this._pendingPromise.reject(new Error("Error parsing JSON from backend: " + e.message));
                    this._pendingPromise = null;
                }
                return;
            }

            console.log("[Debug] Parsed message object:", message);
            if (message !== null && typeof message === 'object') {
                console.log("[Debug] Keys in parsed message:", Object.keys(message));
                console.log("[Debug] Value of message.status:", message.status);
                console.log("[Debug] Type of message.status:", typeof message.status);
                console.log("[Debug] Value of message.type:", message.type);
                console.log("[Debug] Type of message.type:", typeof message.type);
            } else {
                console.log("[Debug] Parsed message is not an object or is null:", message);
            }

            // Check for direct reply first, ensure message is an object and status is a string
            if (this._pendingPromise && message && typeof message.status === 'string') {
                console.log("js: Received direct reply:", message);
                if (message.status === 'success') {
                    this._pendingPromise.resolve(message);
                } else {
                    const errorMessage = message.message || 'Backend request failed';
                    this._pendingPromise.reject(new Error(errorMessage));
                }
                this._pendingPromise = null;
            } else if (message && message.type === "elevatorUpdated") {
                console.log("js: Received elevatorUpdated broadcast:", message.payload);
                this.elevatorUpdated.emit(message.payload);
            } else if (message && message.type === "floorCalled") {
                console.log("js: Received floorCalled broadcast:", message.payload);
                this.floorCalled.emit(message.payload);
            } else {
                console.error("js: Received unknown or malformed message type from backend (final else):", message);
                if (this._pendingPromise) {
                    const errorDetail = message ? JSON.stringify(message) : String(message);
                    this._pendingPromise.reject(new Error('Malformed or unexpected reply from backend. Message: ' + errorDetail));
                    this._pendingPromise = null;
                }
            }
        };

        this.socket.onclose = (event) => {
            // MODIFIED: onclose handler
            console.log("WebSocket connection closed.", event.reason || "No reason provided");
            this._isConnected = false;
            if (this._pendingPromise) {
                this._pendingPromise.reject(new Error("WebSocket connection closed"));
                this._pendingPromise = null;
            }
        };

        this.socket.onerror = (error) => {
            // MODIFIED: onerror handler
            console.error("WebSocket error:", error);
            this._isConnected = false;
            if (this._pendingPromise) {
                this._pendingPromise.reject(new Error("WebSocket error"));
                this._pendingPromise = null;
            }
        };
    },

    sendToBackend: function(messageString) {
        // MODIFIED: sendToBackend implementation
        return new Promise((resolve, reject) => {
            if (!this.isConnected()) {
                // Try to connect if not connected, or reject immediately
                // For simplicity, rejecting immediately here.
                console.error("js: WebSocket not connected. Cannot send message.");
                return reject(new Error("WebSocket not connected"));
            }
            if (this._pendingPromise) {
                console.warn("js: Another request is already in flight. Blocking new request.");
                return reject(new Error("Another request is already in flight"));
            }

            this._pendingPromise = { resolve, reject };

            try {
                this.socket.send(messageString);
                console.log("js: Sent to backend:", messageString);
            } catch (e) {
                console.error("js: Error sending message to backend:", e);
                this._pendingPromise.reject(e); // Reject the stored promise
                this._pendingPromise = null; // Clear it
                return; // Exit early
            }

            // Timeout for the request
            setTimeout(() => {
                // Check if the promise is still pending and belongs to this timeout
                if (this._pendingPromise && this._pendingPromise.reject === reject) {
                    console.warn("js: Request timed out for message:", messageString);
                    this._pendingPromise.reject(new Error("Request timed out"));
                    this._pendingPromise = null;
                }
            }, 10000); // 10-second timeout
        });
    },

    isConnected: function() {
        return this._isConnected && this.socket && this.socket.readyState === WebSocket.OPEN;
    }
};

// Floor heights (% values from bottom)
const floorHeights = {
    0: 0,    // Floor -1 (basement) at bottom 0%
    1: 25,   // Floor 1 at 25% from bottom
    2: 50,   // Floor 2 at 50% from bottom
    3: 75    // Floor 3 at 75% from bottom
};

// NEW: Stores animation state for each elevator
let elevatorAnimations = {}; 
// NEW: Defines the time (in seconds) for the elevator to travel one floor.
// This should ideally match your backend's elevator.floor_travel_time and the default CSS transition for a single floor.
const SINGLE_FLOOR_TRAVEL_TIME_SECONDS = 2.0; 

// Initialize the web channel connection to the backend
window.onload = function() {
    // Add CSS rule to determine debug panel visibility
    const style = document.createElement('style');
    document.head.appendChild(style);
    
    // Function to update CSS based on showDebugPanel state
    const updateDebugPanelVisibility = function() {
        // Default to showing if not explicitly set to false
        const isVisible = window.showDebugPanel !== false;
        console.log("Debug panel visibility set to:", isVisible);
        
        // Update CSS rule
        style.textContent = '.debug-section { display: ' + (isVisible ? 'block' : 'none') + ' !important; }';
    };
    
    // Initial setup
    updateDebugPanelVisibility();
    
    // Set up listener for when Python sets the variable later
    let _showDebugPanel = window.showDebugPanel;
    Object.defineProperty(window, 'showDebugPanel', {
        set: function(value) {
            console.log("showDebugPanel property set to:", value);
            _showDebugPanel = value;
            updateDebugPanelVisibility();
        },
        get: function() {
            return _showDebugPanel;
        }
    });

    // Initialize WebSocket connection
    backend.init('ws://127.0.0.1:8765');
    // Note: "Backend connection established" log will come from backend.socket.onopen

    // Register for elevator updates - these listeners are attached to our custom emitters
    backend.elevatorUpdated.connect(function(message) {
        console.log("Elevator updated:", message); // This log comes from the event listener
        const data = message; // MODIFIED: Use the message object directly
        // Handle target_floors_origin - convert to regular object if needed
        if (data.target_floors_origin) {
            data.targetFloorsOrigin = data.target_floors_origin;
        }
        updateElevatorUI(data);
    });
    
    // Register for floor call updates
    backend.floorCalled.connect(function(message) {
        console.log("Floor called:", message); // This log comes from the event listener
        const data = message; // MODIFIED: Use the message object directly
        highlightFloorButton(data.floor, data.direction);
    });
    // The QWebChannel part is removed.
};

// Call elevator from a floor
function callElevator(floor, direction) {
    console.log(`Calling elevator at floor ${floor} direction ${direction}`);
    highlightFloorButton(floor, direction);
    
    if (backend) {
        const message = {
            action: "callElevator",
            floor: floor,
            direction: direction
        };
        
        backend.sendToBackend(JSON.stringify(message))
            .then(response => {
                console.log("Response:", response);
            })
            .catch(error => {
                console.error("Error calling elevator:", error);
            });
    } else {
        console.error("Backend not initialized");
    }
}

// Select a floor inside the elevator
function selectFloor(floor, elevatorId) {
    console.log(`Selecting floor ${floor} in elevator ${elevatorId}`);
    highlightElevatorButton(floor, elevatorId);
    
    if (backend) {
        const message = {
            action: "selectFloor",
            floor: floor,
            elevatorId: elevatorId
        };
        
        backend.sendToBackend(JSON.stringify(message))
            .then(response => {
                console.log("Response:", response);
            })
            .catch(error => {
                console.error("Error selecting floor:", error);
            });
    } else {
        console.error("Backend not initialized");
    }
}

// Open elevator door
function openDoor(elevatorId) {
    console.log(`Opening door for elevator ${elevatorId}`);
    
    if (backend) {
        const message = {
            action: "openDoor",
            elevatorId: elevatorId
        };
        
        backend.sendToBackend(JSON.stringify(message))
            .then(response => {
                console.log("Response:", response);
            })
            .catch(error => {
                console.error("Error opening door:", error);
            });
    } else {
        console.error("Backend not initialized");
    }
}

// Close elevator door
function closeDoor(elevatorId) {
    console.log(`Closing door for elevator ${elevatorId}`);
    
    if (backend) {
        const message = {
            action: "closeDoor",
            elevatorId: elevatorId
        };
        
        backend.sendToBackend(JSON.stringify(message))
            .then(response => {
                console.log("Response:", response);
            })
            .catch(error => {
                console.error("Error closing door:", error);
            });
    } else {
        console.error("Backend not initialized");
    }
}

// Update elevator UI based on data from backend
function updateElevatorUI(data) {
    const elevatorId = data.id;
    const actualCurrentFloor = data.floor; // Backend's reported current floor
    const state = data.state; // IDLE, MOVING_UP, MOVING_DOWN, etc.
    const doorState = data.doorState;
    const targetFloors = data.targetFloors; // List of next stops
    const targetFloorsOrigin = data.targetFloorsOrigin || {}; // Origin of each target floor

    const elevatorElement = document.getElementById(`elevator-${elevatorId}`);
    if (!elevatorElement) return;

    // Initialize animation state for this elevator if it doesn't exist
    if (!elevatorAnimations[elevatorId]) {
        elevatorAnimations[elevatorId] = {
            visualTargetFloor: null // The ultimate destination of the current multi-floor visual travel
        };
    }
    let animState = elevatorAnimations[elevatorId];

    // Update real elevator panel
    document.getElementById(`real-elevator-${elevatorId}-floor`).textContent = actualCurrentFloor === 0 ? "-1" : actualCurrentFloor;
    
    // Update direction indicators
    const upArrow = document.getElementById(`elevator-${elevatorId}-up-arrow`);
    const downArrow = document.getElementById(`elevator-${elevatorId}-down-arrow`);
    
    // Reset both arrows first
    upArrow.classList.remove('active');
    downArrow.classList.remove('active');
    
    // Set active arrow based on state
    if (state === 'MOVING_UP') {
        upArrow.classList.add('active');
    } else if (state === 'MOVING_DOWN') {
        downArrow.classList.add('active');
    }

    // Update debug panel information
    document.getElementById(`elevator-${elevatorId}-floor`).textContent = actualCurrentFloor === 0 ? "-1" : actualCurrentFloor;
    document.getElementById(`elevator-${elevatorId}-status`).textContent = state;
    document.getElementById(`elevator-${elevatorId}-door`).textContent = doorState;
    document.getElementById(`elevator-${elevatorId}-targets`).textContent = targetFloors.map(f => f === 0 ? "-1" : f).join(', ');

    // Update door visuals (this part remains unchanged)
    elevatorElement.classList.remove('doors-open', 'doors-closed', 'doors-opening', 'doors-closing');
    if (doorState === 'OPEN') elevatorElement.classList.add('doors-open');
    else if (doorState === 'CLOSED') elevatorElement.classList.add('doors-closed');
    else if (doorState === 'OPENING') elevatorElement.classList.add('doors-opening');
    else if (doorState === 'CLOSING') elevatorElement.classList.add('doors-closing');

    // Handle elevator vertical movement visualization
    if (state === "MOVING_UP" || state === "MOVING_DOWN") {
        if (targetFloors.length > 0) {
            const nextStopFloor = targetFloors[0]; // The immediate next floor the elevator will stop at

            // If this is a new movement segment OR the ultimate target has changed
            if (animState.visualTargetFloor !== nextStopFloor) {
                animState.visualTargetFloor = nextStopFloor;

                const travelDistance = Math.abs(nextStopFloor - actualCurrentFloor);

                if (travelDistance > 0) {
                    const animationDuration = travelDistance * SINGLE_FLOOR_TRAVEL_TIME_SECONDS;
                    elevatorElement.style.transition = `bottom ${animationDuration}s ease-in-out`;
                    elevatorElement.style.bottom = `${floorHeights[nextStopFloor]}%`;
                } else {
                    // MOVING but travelDistance is 0 to nextStopFloor (e.g., at the floor but backend says MOVING)
                    // Snap to the floor and reset transition
                    elevatorElement.style.transition = 'none';
                    elevatorElement.style.bottom = `${floorHeights[actualCurrentFloor]}%`;
                    void elevatorElement.offsetHeight; // Force reflow
                    elevatorElement.style.transition = `bottom ${SINGLE_FLOOR_TRAVEL_TIME_SECONDS}s ease-in-out`; // Default for next
                }
            }
            // If animState.visualTargetFloor === nextStopFloor, it's an intermediate floor update.
            // The visual animation is already in progress towards visualTargetFloor. Only text was updated.
        } else {
            // MOVING but no target_floors: Inconsistent state. Snap to current floor.
            animState.visualTargetFloor = null;
            elevatorElement.style.transition = 'none';
            elevatorElement.style.bottom = `${floorHeights[actualCurrentFloor]}%`;
            void elevatorElement.offsetHeight; // Force reflow
            elevatorElement.style.transition = `bottom ${SINGLE_FLOOR_TRAVEL_TIME_SECONDS}s ease-in-out`;
        }
    } else { // Elevator is IDLE, OPENING, CLOSING, OPEN, CLOSED
        animState.visualTargetFloor = null; // Clear any ongoing visual long-travel target

        // Ensure the elevator is visually at its actualCurrentFloor.
        // Snap to the actualCurrentFloor. If it was in a long animation, this stops it correctly.
        elevatorElement.style.transition = 'none';
        elevatorElement.style.bottom = `${floorHeights[actualCurrentFloor]}%`;
        void elevatorElement.offsetHeight; // Force reflow to apply the 'none' transition and new bottom immediately

        // Restore default transition for any subsequent small adjustments or next moves
        elevatorElement.style.transition = `bottom ${SINGLE_FLOOR_TRAVEL_TIME_SECONDS}s ease-in-out`;
    }    // Update active floor buttons inside the elevator panel based on origin
    const controlPanel = document.getElementById(`panel-${elevatorId}`);
    if (controlPanel) {
        const buttons = controlPanel.querySelectorAll('.floor-buttons button');
        buttons.forEach(button => {
            let buttonFloorText = button.textContent;
            let buttonFloor = buttonFloorText === "-1" ? 0 : parseInt(buttonFloorText);
            
            // Only highlight if the floor was requested from inside the elevator
            if (targetFloors.includes(buttonFloor) && targetFloorsOrigin[buttonFloor] === "inside") {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
    }
}

// Highlight a floor call button
function highlightFloorButton(floor, direction) {
    const floorElement = document.getElementById(`floor-${floor}`);
    if (floorElement) {
        const button = floorElement.querySelector(`.call-btn.${direction}`);
        if (button) {
            button.classList.add('active');
            // Remove the highlight after a delay
            setTimeout(() => {
                button.classList.remove('active');
            }, 5000);
        }
    }
}

// Highlight an elevator floor button
function highlightElevatorButton(floor, elevatorId) {
    const panel = document.getElementById(`panel-${elevatorId}`);
    if (panel) {
        const buttons = panel.querySelectorAll('.floor-buttons button');
        buttons.forEach(button => {
            if ((buttonFloor = button.textContent === "-1" ? 0 : parseInt(button.textContent)) === floor) {
                button.classList.add('active');
                // Don't remove the highlight - let the backend response handle it via updateElevatorUI
            }
        });
    }
    
    // When an inside button is pressed, unhighlight all outside call buttons
    const allFloorButtons = document.querySelectorAll('.call-btn');
    allFloorButtons.forEach(button => {
        button.classList.remove('active');
    });
}

// Simulate elevator movement for testing (if not connected to backend)
function simulateElevator() {
    if (!backend.isConnected()) { // Check if WebSocket is connected
        // Elevator 1: Move from floor 1 to 3
        setTimeout(() => {
            updateElevatorUI({
                id: 1,
                floor: 1,
                state: "MOVING_UP",
                doorState: "CLOSED",
                direction: "up",
                targetFloors: [3]
            });
        }, 1000);
        
        setTimeout(() => {
            updateElevatorUI({
                id: 1,
                floor: 2,
                state: "MOVING_UP",
                doorState: "CLOSED",
                direction: "up",
                targetFloors: [3]
            });
        }, 3000);
        
        setTimeout(() => {
            updateElevatorUI({
                id: 1,
                floor: 3,
                state: "IDLE",
                doorState: "OPENING",
                direction: "none",
                targetFloors: []
            });
        }, 5000);
        
        setTimeout(() => {
            updateElevatorUI({
                id: 1,
                floor: 3,
                state: "DOOR_OPEN",
                doorState: "OPEN",
                direction: "none",
                targetFloors: []
            });
        }, 6000);
        
        // Elevator 2: Move from floor 1 to 0
        setTimeout(() => {
            updateElevatorUI({
                id: 2,
                floor: 1,
                state: "MOVING_DOWN",
                doorState: "CLOSED",
                direction: "down",
                targetFloors: [0]
            });
        }, 2000);
        
        setTimeout(() => {
            updateElevatorUI({
                id: 2,
                floor: 0,
                state: "IDLE",
                doorState: "OPENING",
                direction: "none",
                targetFloors: []
            });
        }, 4000);
        
        setTimeout(() => {
            updateElevatorUI({
                id: 2,
                floor: 0,
                state: "DOOR_OPEN",
                doorState: "OPEN",
                direction: "none",
                targetFloors: []
            });
        }, 5000);
    }
}

// Run the simulation if not connected to backend after 2 seconds
setTimeout(() => {
    if (!backend.isConnected()) { // Check if WebSocket is connected
        console.log("Backend not connected, running simulation");
        simulateElevator();
    }
}, 2000);
