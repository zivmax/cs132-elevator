// UI helper functions for highlighting buttons
export function highlightFloorButton(floor, direction) {
    const floorElement = document.getElementById(`floor-${floor}`);
    if (floorElement) {
        const button = floorElement.querySelector(`.call-btn.${direction}`);
        if (button) {
            button.classList.add('active');
            setTimeout(() => {
                button.classList.remove('active');
            }, 5000);
        }
    }
}

export function highlightElevatorButton(floor, elevatorId) {
    const panel = document.getElementById(`panel-${elevatorId}`);
    if (panel) {
        const buttons = panel.querySelectorAll('.floor-buttons button');        buttons.forEach(button => {
            if ((button.textContent === "-1" ? -1 : parseInt(button.textContent)) === floor) {
                button.classList.add('active');
            }
        });
    }
    const allFloorButtons = document.querySelectorAll('.call-btn');
    allFloorButtons.forEach(button => {
        button.classList.remove('active');
    });
}
