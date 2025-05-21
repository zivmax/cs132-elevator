import sys
import os
import time
import argparse
from PyQt6.QtWidgets import QApplication

from backend.world import World
from frontend.webview import ElevatorWebSocketView


class ElevatorApplication:
    def __init__(self, show_debug=True, remote_debugging_port=0):
        # Create Qt application
        self.app = QApplication(sys.argv)

        # Initialize backend
        self.backend = World()

        # Initialize frontend with WebSocket communication
        self.frontend = ElevatorWebSocketView(
            self.backend, 
            show_debug=show_debug, 
            remote_debugging_port=remote_debugging_port
        )
        self.frontend.show()

        # Setup timer for UI updates
        self.last_update_time = time.time()

    def update(self):
        """Update the UI based on backend state"""
        current_time = time.time()
        if current_time - self.last_update_time >= 0.1:  # Update 10 times per second
            self.frontend.update()
            self.backend.update()  # Update backend state
            self.last_update_time = current_time

    def run(self):
        """Run the application main loop"""
        while True:
            self.app.processEvents()
            self.update()
            time.sleep(0.01)  # Small sleep to avoid CPU hogging


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Elevator Simulation")
    parser.add_argument("--debug", action="store_true", help="Show debug information panel")
    parser.add_argument("--cdp", type=int, default=0, help="Chromium debugging port")
    args = parser.parse_args()
    
    # Create and run the application
    app = ElevatorApplication(show_debug=args.debug, remote_debugging_port=args.cdp)
    app.run()
    os._exit(0)
