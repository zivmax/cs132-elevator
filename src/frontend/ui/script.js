// Global variables for backend communication
let backend;

// Floor heights (% values from bottom)
const floorHeights = {
    0: 0,    // Floor -1 (basement) at bottom 0%
    1: 25,   // Floor 1 at 25% from bottom
    2: 50,   // Floor 2 at 50% from bottom
    3: 75    // Floor 3 at 75% from bottom
};

// Initialize the web channel connection to the backend
window.onload = function() {
    new QWebChannel(qt.webChannelTransport, function(channel) {
        backend = channel.objects.backend;
        console.log("Backend connection established");
        
        // Register for elevator updates
        backend.elevatorUpdated.connect(function(message) {
            console.log("Elevator updated:", message);
            const data = JSON.parse(message);
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
    const floor = data.floor;
    const state = data.state;
    const doorState = data.doorState;
    const direction = data.direction;
    const targetFloors = data.targetFloors;
    
    // Update elevator position
    const elevatorElement = document.getElementById(`elevator-${elevatorId}`);
    if (elevatorElement) {
        // Update position (with animation)
        elevatorElement.style.bottom = `${floorHeights[floor]}%`;
        
        // Update door state
        elevatorElement.classList.remove('doors-open', 'doors-closed', 'doors-opening', 'doors-closing');
        
        if (doorState === 'OPEN') {
            elevatorElement.classList.add('doors-open');
        } else if (doorState === 'CLOSED') {
            elevatorElement.classList.add('doors-closed');
        } else if (doorState === 'OPENING') {
            elevatorElement.classList.add('doors-opening');
        } else if (doorState === 'CLOSING') {
            elevatorElement.classList.add('doors-closing');
        }
    }
    
    // Update status displays
    document.getElementById(`elevator-${elevatorId}-floor`).textContent = floor === 0 ? "-1" : floor;
    document.getElementById(`elevator-${elevatorId}-status`).textContent = state;
    document.getElementById(`elevator-${elevatorId}-door`).textContent = doorState;
    document.getElementById(`elevator-${elevatorId}-targets`).textContent = targetFloors.map(floor => floor === 0 ? "-1" : floor).join(', ');
    
    // Update active floor buttons - fix to ensure ALL buttons are properly set
    const controlPanel = document.getElementById(`panel-${elevatorId}`);
    if (controlPanel) {
        const buttons = controlPanel.querySelectorAll('.floor-buttons button');
        buttons.forEach(button => {
            // Need to convert "-1" text to 0 for basement floor
            let buttonFloor = button.textContent;
            buttonFloor = buttonFloor === "-1" ? 0 : parseInt(buttonFloor);
            
            // Set or remove active class based on targetFloors list
            if (targetFloors.includes(buttonFloor)) {
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
            if (parseInt(button.textContent) === floor) {
                button.classList.add('active');
                // Don't remove the highlight - let the backend response handle it via updateElevatorUI
            }
        });
    }
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
