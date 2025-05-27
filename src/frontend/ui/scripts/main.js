// Main entry point for the modular elevator UI
import { backend } from './backend.js';
import { updateElevatorUI } from './elevator-UI.js';
import { callElevator, selectFloor, openDoor, closeDoor, simulateElevator } from './actions.js';

window.callElevator = callElevator;
window.selectFloor = selectFloor;
window.openDoor = openDoor;
window.closeDoor = closeDoor;

window.onload = function() {
    const style = document.createElement('style');
    document.head.appendChild(style);
    const updateDebugPanelVisibility = function() {
        const isVisible = window.showDebugPanel !== false;
        style.textContent = '.debug-section { display: ' + (isVisible ? 'block' : 'none') + ' !important; }';
    };
    updateDebugPanelVisibility();
    let _showDebugPanel = window.showDebugPanel;
    Object.defineProperty(window, 'showDebugPanel', {
        set(value) {
            _showDebugPanel = value;
            updateDebugPanelVisibility();
        },
        get() { return _showDebugPanel; }
    });
    backend.init('ws://127.0.0.1:8765');
    backend.elevatorUpdated.connect(function(message) {
        const data = message;
        if (data.target_floors_origin) {
            data.targetFloorsOrigin = data.target_floors_origin;
        }
        updateElevatorUI(data);
    });
    backend.floorCalled.connect(function(message) {
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
