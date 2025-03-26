import os
import sys
from typing import TYPE_CHECKING, Dict, Any
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

from frontend.bridge import WebBridge
from backend.api import ElevatorAPI

if TYPE_CHECKING:
    from backend.world import World


class ElevatorWebview(QMainWindow):
    """Main window for the elevator UI using QtWebEngine"""

    def __init__(self, world: "World" = None):
        super().__init__()
        self.world = world
        self.api = ElevatorAPI(world)
        self.bridge = WebBridge(self)

        # Register callbacks
        self.bridge.register_callback("callElevator", self.api.handle_call_elevator)
        self.bridge.register_callback("selectFloor", self.api.handle_select_floor)
        self.bridge.register_callback("openDoor", self.api.handle_open_door)
        self.bridge.register_callback("closeDoor", self.api.handle_close_door)

        # Setup the UI
        self.setWindowTitle("Elevator Simulation")
        self.resize(1024, 768)

        # Create the web view
        self.web_view = QWebEngineView(self)
        self.setCentralWidget(self.web_view)

        # Set up web channel for communication
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # Load the HTML file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, "ui", "index.html")
        self.web_view.load(QUrl.fromLocalFile(html_path))

    def _sync_backend(self):
        """Update the UI based on backend state"""
        if not self.world:
            return

        # Get elevator states from the API
        elevator_states = self.api.fetch_elevator_states()

        # Update the UI for each elevator
        for elevator_state in elevator_states:
            self.bridge.sync_elevator_state(
                elevator_id=elevator_state["elevator_id"],
                floor=elevator_state["floor"],
                state=elevator_state["state"],
                door_state=elevator_state["door_state"],
                direction=elevator_state["direction"],
                target_floors=elevator_state["target_floors"],
            )

    def update(self):
        self._sync_backend()


def run_standalone():
    """Run the elevator UI as a standalone application for testing"""
    app = QApplication(sys.argv)
    window = ElevatorWebview()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_standalone()
