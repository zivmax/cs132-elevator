import sys
import os
import time
import argparse
from PyQt6.QtWidgets import QApplication

from backend.world import World
from backend.api import ElevatorAPI  # Import ElevatorAPI
from frontend.webview import ElevatorWebSocketView


class ElevatorApplication:
    def __init__(self, show_debug=True, remote_debugging_port=0, ws_port=8765):
        # Create Qt application
        self.app = QApplication(sys.argv)

        # Initialize backend World first (without API yet)
        self.backend = World()

        # Instantiate ElevatorAPI, passing the world and its zmq_coordinator
        # This assumes World initializes zmq_coordinator in its __init__
        self.elevator_api = ElevatorAPI(self.backend, self.backend.zmq_coordinator)

        # Now, set the API for the world and initialize its dependent components
        self.backend.set_api_and_initialize_components(self.elevator_api)

        # Initialize frontend with WebSocket communication, passing the API and ws_port
        self.frontend = ElevatorWebSocketView(
            self.backend,  # World instance
            self.elevator_api,  # ElevatorAPI instance
            show_debug=show_debug,
            remote_debugging_port=remote_debugging_port,
            ws_port=ws_port,
        )
        self.frontend.show()

        # Setup timer for UI updates
        self.last_update_time = time.time()

    def update(self):
        """Update the UI based on backend state"""
        current_time = time.time()
        if current_time - self.last_update_time >= 0.1:  # Update 10 times per second
            self.frontend.update()

            # Process messages from the backend's ZmqCoordinator queue using its API
            if (
                self.backend
                and hasattr(self.backend, "zmq_coordinator")
                and hasattr(self.backend.zmq_coordinator, "has_queued_messages")
                and hasattr(self.backend.zmq_coordinator, "get_next_msg_for_processing")
                and hasattr(self.backend, "api")
            ):
                zmq_coord = self.backend.zmq_coordinator
                while zmq_coord.has_queued_messages():
                    # get_next_msg_for_processing now returns a command object (or ParseError) and a timestamp
                    command_or_error_obj, timestamp = (
                        zmq_coord.get_next_msg_for_processing()
                    )
                    if (
                        command_or_error_obj
                    ):  # Check if an object was returned (not None)
                        # print(f"MainApp: Processing command/error object from ZmqCoordinator: {command_or_error_obj}") # Optional debug
                        self.backend.api.parse_and_handle_message(
                            command_or_error_obj
                        )  # Pass the object directly

            self.backend.update()  # Backend update (polls ZMQ via ZmqCoordinator, updates engine, elevators)
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
    parser.add_argument(
        "--debug", action="store_true", help="Show debug information panel"
    )
    parser.add_argument("--cdp", type=int, default=0, help="Chromium debugging port")
    parser.add_argument("--ws-port", type=int, default=8765, help="WebSocket server port")
    args = parser.parse_args()

    # Create and run the application
    app = ElevatorApplication(show_debug=args.debug, remote_debugging_port=args.cdp, ws_port=args.ws_port)
    app.run()
    os._exit(0)
