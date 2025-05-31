import sys
import os
import time
import signal
import argparse

from backend.world import World
from backend.api import ElevatorAPI  # Import ElevatorAPI
from frontend.webview import ElevatorWebview
from frontend.bridge import WebSocketBridge  # Import WebSocketBridge
from backend.server import HTTPServer  # Import HTTPServer


class ElevatorApplication:
    def __init__(
        self,
        show_debug=False,
        remote_debugging_port=0,
        ws_port=8765,
        http_port=None,
        headless=False,
    ):  # MODIFIED
        self.headless = headless  # Store headless state
        self.running = True  # Add running flag for clean shutdown
        self._cleanup_done = False  # Add cleanup guard to prevent redundant cleanup
        
        if not self.headless:
            from PyQt6.QtWidgets import QApplication  # Conditional import

            self.app = QApplication(sys.argv)
            # Connect aboutToQuit signal to cleanup
            self.app.aboutToQuit.connect(self.cleanup)
        else:
            self.app = None

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Initialize backend World first (without API yet)
        self.backend = World()

        # Instantiate ElevatorAPI, passing the world and its zmq_coordinator
        # This assumes World initializes zmq_coordinator in its __init__
        self.elevator_api = ElevatorAPI(self.backend, self.backend.zmq_coordinator)

        # Now, set the API for the world and initialize its dependent components
        self.backend.set_api_and_initialize_components(
            self.elevator_api
        )  # Initialize WebSocketBridge
        self.bridge = WebSocketBridge(
            world=self.backend, api=self.elevator_api, port=ws_port
        )

        # self.headless = headless # Duplicate assignment removed
        self.http_server = None

        if http_port is not None:
            # Start HTTP server if http_port is specified
            self.http_server = HTTPServer(port=http_port)
            self.http_server.start()
            print(
                f"HTTP server running. Access frontend at http://127.0.0.1:{http_port}/?ws_port={ws_port}&show_debug={str(show_debug).lower()}"
            )

        if headless:
            # In headless mode, only WebSocket server runs for custom frontend connections
            if http_port is None:
                print(f"Running in headless mode with WebSocket server only.")
                print(f"WebSocket server accessible at: ws://127.0.0.1:{ws_port}")
                print(f"Connect your custom frontend to this WebSocket endpoint.")
                print(f"API documentation: See backend/api.py for available functions.")
            else:
                print(
                    f"Running in headless mode with both HTTP server and WebSocket server."
                )
                print(f"WebSocket server accessible at: ws://127.0.0.1:{ws_port}")
        else:
            # Initialize frontend with WebSocket communication, passing the API and ws_port
            self.frontend = ElevatorWebview(
                self.bridge,  # Pass WebSocketBridge instance
                show_debug=show_debug,
                remote_debugging_port=remote_debugging_port,
                ws_port=ws_port,
                app_cleanup_callback=self.cleanup,  # Pass cleanup callback
            )
            self.frontend.show()

        # Setup timer for UI updates
        self.last_update_time = time.time()

    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        print(f"\nReceived signal {signum}. Initiating shutdown...")
        self.running = False
        if self.app:
            self.app.quit()

    def cleanup(self):
        """Clean up all resources"""
        if self._cleanup_done:
            return  # Prevent redundant cleanup
        
        print("Cleaning up application resources...")
        self._cleanup_done = True
        self.running = False
        
        try:
            # Stop WebSocket bridge
            if hasattr(self, 'bridge') and self.bridge:
                self.bridge.stop()
                print("WebSocket bridge stopped.")
        except Exception as e:
            print(f"Error stopping WebSocket bridge: {e}")

        try:
            # Stop HTTP server if running
            if hasattr(self, 'http_server') and self.http_server:
                self.http_server.stop()
                print("HTTP server stopped.")
        except Exception as e:
            print(f"Error stopping HTTP server: {e}")

        try:
            # Stop backend ZMQ coordinator
            if hasattr(self, 'backend') and self.backend and hasattr(self.backend, 'zmq_coordinator'):
                self.backend.zmq_coordinator.stop()
                print("ZMQ coordinator stopped.")
        except Exception as e:
            print(f"Error stopping ZMQ coordinator: {e}")

        print("Application cleanup completed.")

    def update(self):
        """Update the UI based on backend state"""
        current_time = time.time()
        if current_time - self.last_update_time >= 0.1:  # Update 10 times per second
            if not self.headless:
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
            self.bridge.sync_backend()
            self.last_update_time = current_time

    def run(self):
        """Run the application main loop"""
        try:
            while self.running:
                if self.app:  # This check correctly handles if self.app is None
                    self.app.processEvents()
                    if not self.running:  # Check again after processing events
                        break
                self.update()
                time.sleep(0.01)  # Small sleep to avoid CPU hogging
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
        finally:
            self.cleanup()


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Elevator Simulation")
    parser.add_argument(
        "--debug", action="store_true", help="Show debug information panel"
    )
    parser.add_argument("--cdp", type=int, default=0, help="Chromium debugging port")
    parser.add_argument(
        "--ws-port", type=int, default=8765, help="WebSocket server port"
    )
    parser.add_argument(
        "--http-port",
        type=int,
        default=None,
        help="HTTP server port. If specified, an HTTP server will host the frontend.",
    )  # MODIFIED
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode without launching webview",
    )
    args = parser.parse_args()

    # Create and run the application
    app = ElevatorApplication(
        show_debug=args.debug,
        remote_debugging_port=args.cdp,
        ws_port=args.ws_port,
        http_port=args.http_port,
        headless=args.headless,
    )

    app.run()
