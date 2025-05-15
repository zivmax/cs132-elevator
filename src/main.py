import sys
import os
import time
import argparse
from PyQt6.QtWidgets import QApplication

from backend.world import World
from frontend.webview import ElevatorWebview


class ElevatorApplication:
    def __init__(self, show_debug=True):
        # Create Qt application
        self.app = QApplication(sys.argv)

        # Initialize backend
        self.backend = World()

        # Initialize frontend
        self.frontend = ElevatorWebview(self.backend, show_debug)
        self.frontend.show()

        # Setup timer for UI updates
        self.last_update_time = time.time()

    def run(self):
        # Start the application event loop
        try:
            # Main loop
            while True:
                # Process Qt events
                self.app.processEvents()

                # Update backend
                self.backend.update()

                # Update UI every 100ms
                current_time = time.time()
                if current_time - self.last_update_time >= 0.1:
                    self.frontend.update()
                    self.last_update_time = current_time

                # Sleep to prevent high CPU usage
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("Elevator simulation terminated.")

            # Process any pending events before closing
            self.app.processEvents()

            # Close UI
            self.frontend.close()

            # Ensure application quits
            self.app.quit()

            # Process events one final time
            self.app.processEvents()


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Elevator Simulation")
    parser.add_argument("--debug", action="store_true", help="Show debug information panel")
    args = parser.parse_args()
    
    # Create and run the application
    app = ElevatorApplication(show_debug=args.debug)
    app.run()
    os._exit(0)
