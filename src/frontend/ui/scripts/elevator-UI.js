// Elevator UI logic and DOM manipulation
import { floorHeights, SINGLE_FLOOR_TRAVEL_TIME_SECONDS, elevatorAnimations } from './constants.js';

export function updateElevatorUI(data) {
    const elevatorId = data.id;
    const actualCurrentFloor = data.floor;
    const state = data.state;
    const doorState = data.doorState;
    const targetFloors = data.targetFloors;
    const targetFloorsOrigin = data.targetFloorsOrigin || {};
    const elevatorElement = document.getElementById(`elevator-${elevatorId}`);
    if (!elevatorElement) return;
    if (!elevatorAnimations[elevatorId]) {
        elevatorAnimations[elevatorId] = { visualTargetFloor: null };
    }
    let animState = elevatorAnimations[elevatorId];
    document.getElementById(`real-elevator-${elevatorId}-floor`).textContent = actualCurrentFloor;
    const upArrow = document.getElementById(`elevator-${elevatorId}-up-arrow`);
    const downArrow = document.getElementById(`elevator-${elevatorId}-down-arrow`);
    upArrow.classList.remove('active');
    downArrow.classList.remove('active');
    if (state === 'MOVING_UP') upArrow.classList.add('active');
    else if (state === 'MOVING_DOWN') downArrow.classList.add('active');
    document.getElementById(`elevator-${elevatorId}-floor`).textContent = actualCurrentFloor;
    document.getElementById(`elevator-${elevatorId}-status`).textContent = state;
    document.getElementById(`elevator-${elevatorId}-door`).textContent = doorState;
    document.getElementById(`elevator-${elevatorId}-targets`).textContent = targetFloors.join(', ');
    elevatorElement.classList.remove('doors-open', 'doors-closed', 'doors-opening', 'doors-closing');
    if (doorState === 'OPEN') elevatorElement.classList.add('doors-open');
    else if (doorState === 'CLOSED') elevatorElement.classList.add('doors-closed');
    else if (doorState === 'OPENING') elevatorElement.classList.add('doors-opening');
    else if (doorState === 'CLOSING') elevatorElement.classList.add('doors-closing');
    if (state === "MOVING_UP" || state === "MOVING_DOWN") {
        if (targetFloors.length > 0) {
            const nextStopFloor = targetFloors[0];
            if (animState.visualTargetFloor !== nextStopFloor) {
                animState.visualTargetFloor = nextStopFloor;
                const travelDistance = Math.abs(nextStopFloor - actualCurrentFloor);
                if (travelDistance > 0) {
                    const animationDuration = travelDistance * SINGLE_FLOOR_TRAVEL_TIME_SECONDS;
                    elevatorElement.style.transition = `bottom ${animationDuration}s ease-in-out`;
                    elevatorElement.style.bottom = `${floorHeights[nextStopFloor]}%`;
                } else {
                    elevatorElement.style.transition = 'none';
                    elevatorElement.style.bottom = `${floorHeights[actualCurrentFloor]}%`;
                    void elevatorElement.offsetHeight;
                    elevatorElement.style.transition = `bottom ${SINGLE_FLOOR_TRAVEL_TIME_SECONDS}s ease-in-out`;
                }
            }
        } else {
            animState.visualTargetFloor = null;
            elevatorElement.style.transition = 'none';
            elevatorElement.style.bottom = `${floorHeights[actualCurrentFloor]}%`;
            void elevatorElement.offsetHeight;
            elevatorElement.style.transition = `bottom ${SINGLE_FLOOR_TRAVEL_TIME_SECONDS}s ease-in-out`;
        }
    } else {
        animState.visualTargetFloor = null;
        elevatorElement.style.transition = 'none';
        elevatorElement.style.bottom = `${floorHeights[actualCurrentFloor]}%`;
        void elevatorElement.offsetHeight;
        elevatorElement.style.transition = `bottom ${SINGLE_FLOOR_TRAVEL_TIME_SECONDS}s ease-in-out`;
    }
    const controlPanel = document.getElementById(`panel-${elevatorId}`);
    if (controlPanel) {
        const buttons = controlPanel.querySelectorAll('.floor-buttons button');        buttons.forEach(button => {
            let buttonFloorText = button.textContent;
            let buttonFloor = parseInt(buttonFloorText);
            if (targetFloors.includes(buttonFloor) && targetFloorsOrigin[buttonFloor] === "inside") {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
    }
}
