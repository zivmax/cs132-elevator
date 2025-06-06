// Main entry point for the modular elevator UI
import { backend } from './backend.js';
import { updateElevatorUI } from './elevator-UI.js';
import { callElevator, selectFloor, openDoor, closeDoor, simulateElevator } from './actions.js';

window.callElevator = callElevator;
window.selectFloor = selectFloor;
window.openDoor = openDoor;
window.closeDoor = closeDoor;

window.onload = function () {
    const urlParams = new URLSearchParams(window.location.search);
    const wsPort = urlParams.get('wsPort') || '18765';
    const showDebug = urlParams.get('showDebug') === 'true';

    const style = document.createElement('style');
    document.head.appendChild(style);
    const updateDebugPanelVisibility = function () {
        // Use the showDebug value from URL parameters
        style.textContent = '.debug-section { display: ' + (showDebug ? 'block' : 'none') + ' !important; }';
    };
    updateDebugPanelVisibility();

    // The Object.defineProperty for window.showDebugPanel might still be useful if you want to toggle it from console
    // but its initial state is now controlled by the URL parameter.
    let _showDebugPanel = showDebug; // Initialize with URL param value
    Object.defineProperty(window, 'showDebugPanel', {
        set(value) {
            _showDebugPanel = value;
            // Update visibility if changed dynamically via console
            style.textContent = '.debug-section { display: ' + (_showDebugPanel ? 'block' : 'none') + ' !important; }';
        },
        get() { return _showDebugPanel; }
    });

    backend.init(`ws://127.0.0.1:${wsPort}`);
    backend.elevatorUpdated.connect(function (message) {
        const data = message;
        if (data.target_floors_origin) {
            data.targetFloorsOrigin = data.target_floors_origin;
        }
        updateElevatorUI(data);
    });
    backend.floorCalled.connect(function (message) {
        const data = message;
        import('./ui-helpers.js').then(({ highlightFloorButton }) => {
            highlightFloorButton(data.floor, data.direction);
        });
    });
};
setTimeout(() => {
    if (!backend.isConnected()) {
        simulateElevator();
    }
}, 2000);
