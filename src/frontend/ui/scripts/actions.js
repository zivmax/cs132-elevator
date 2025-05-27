// Elevator actions and simulation logic
import { backend } from './backend.js';
import { updateElevatorUI } from './elevator-UI.js';
import { highlightFloorButton, highlightElevatorButton } from './ui-helpers.js';

export function callElevator(floor, direction) {
    highlightFloorButton(floor, direction);
    if (backend) {
        const message = { function: "handle_call_elevator", params: { floor, direction } };
        backend.sendToBackend(JSON.stringify(message))
            .then(() => {})
            .catch(error => { console.error("Error calling elevator:", error); });
    }
}

export function selectFloor(floor, elevatorId) {
    highlightElevatorButton(floor, elevatorId);
    if (backend) {
        const message = { function: "handle_select_floor", params: { floor, elevatorId } };
        backend.sendToBackend(JSON.stringify(message))
            .then(() => {})
            .catch(error => { console.error("Error selecting floor:", error); });
    }
}

export function openDoor(elevatorId) {
    if (backend) {
        const message = { function: "handle_open_door", params: { elevatorId } };
        backend.sendToBackend(JSON.stringify(message))
            .then(() => {})
            .catch(error => { console.error("Error opening door:", error); });
    }
}

export function closeDoor(elevatorId) {
    if (backend) {
        const message = { function: "handle_close_door", params: { elevatorId } };
        backend.sendToBackend(JSON.stringify(message))
            .then(() => {})
            .catch(error => { console.error("Error closing door:", error); });
    }
}

export function simulateElevator() {
    if (!backend.isConnected()) {
        setTimeout(() => {
            updateElevatorUI({ id: 1, floor: 1, state: "MOVING_UP", doorState: "CLOSED", direction: "up", targetFloors: [3] });
        }, 1000);
        setTimeout(() => {
            updateElevatorUI({ id: 1, floor: 2, state: "MOVING_UP", doorState: "CLOSED", direction: "up", targetFloors: [3] });
        }, 3000);
        setTimeout(() => {
            updateElevatorUI({ id: 1, floor: 3, state: "IDLE", doorState: "OPENING", direction: "none", targetFloors: [] });
        }, 5000);
        setTimeout(() => {
            updateElevatorUI({ id: 1, floor: 3, state: "DOOR_OPEN", doorState: "OPEN", direction: "none", targetFloors: [] });
        }, 6000);
        setTimeout(() => {
            updateElevatorUI({ id: 2, floor: 1, state: "MOVING_DOWN", doorState: "CLOSED", direction: "down", targetFloors: [0] });
        }, 2000);
        setTimeout(() => {
            updateElevatorUI({ id: 2, floor: 0, state: "IDLE", doorState: "OPENING", direction: "none", targetFloors: [] });
        }, 4000);
        setTimeout(() => {
            updateElevatorUI({ id: 2, floor: 0, state: "DOOR_OPEN", doorState: "OPEN", direction: "none", targetFloors: [] });
        }, 5000);
    }
}
