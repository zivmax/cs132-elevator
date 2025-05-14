// Global variables for backend communication
let backend;

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
    new QWebChannel(qt.webChannelTransport, function(channel) {
        backend = channel.objects.backend;
        console.log("Backend connection established");
        
        // Register for elevator updates
        backend.elevatorUpdated.connect(function(message) {
            console.log("Elevator updated:", message);
            const data = JSON.parse(message);
            // Handle target_floors_origin - convert to regular object if needed
            if (data.target_floors_origin) {
                data.targetFloorsOrigin = data.target_floors_origin;
            }
            updateElevatorUI(data);
        });
        
        // Register for floor call updates
        backend.floorCalled.connect(function(message) {
            console.log("Floor called:", message);
            const data = JSON.parse(message);
            highlightFloorButton(data.floor, data.direction);
        });
    });
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

    // Always update textual information
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
    if (!backend) {
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
    if (!backend) {
        console.log("Backend not connected, running simulation");
        simulateElevator();
    }
}, 2000);
