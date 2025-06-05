import time
import signal
import argparse
import threading

from backend.simulator import Simulator
from backend.api import ElevatorAPI
from frontend.webview import ElevatorWebview
from frontend.bridge import WebSocketBridge
from backend.server import ElevatorHTTPServer


class ElevatorApp:
    def __init__(
        self,
        show_debug=False,
        ws_port: int | None = None,
        http_port: int | None = None,
        zmq_port: str = "19982",
        headless=False,
    ):
        self.headless = headless
        self.running = True
        self._cleanup_done = False
        self.frontend = None
        self.backend_thread = None

        # Store initial port parameters for allocation
        self._initial_ws_port = ws_port
        self._initial_http_port = http_port

        # Allocate all required ports
        self._allocate_ports()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.backend = Simulator(zmq_port=zmq_port)
        self.elevator_api = ElevatorAPI(self.backend, self.backend.zmq_coordinator)
        self.backend.set_api_and_initialize_components(self.elevator_api)
        self.bridge = WebSocketBridge(
            world=self.backend,
            api=self.elevator_api,
            port=self.ws_port,
        )

        self.http_server = None
        if self.http_port is not None:
            self.http_server = ElevatorHTTPServer(port=self.http_port)
            self.http_server.start()
            print(
                f"HTTP server running. Access frontend at http://127.0.0.1:{self.http_port}/?wsPort={self.ws_port}&showDebug={str(show_debug).lower()}"
            )

        if headless:
            if self.http_port is None:
                print(f"Running in headless mode with WebSocket server only.")
                print(f"WebSocket server accessible at: ws://127.0.0.1:{self.ws_port}")
                print(f"Connect your custom frontend to this WebSocket endpoint.")
                print(f"API documentation: See backend/api.py for available functions.")
            else:
                print(
                    f"Running in headless mode with both HTTP server and WebSocket server."
                )
                print(f"WebSocket server accessible at: ws://127.0.0.1:{self.ws_port}")
        else:
            # For GUI mode, HTTP server is compulsory and http_port is guaranteed to be set
            assert self.http_port is not None, "HTTP port should be set for GUI mode"
            # Initialize frontend with pywebview
            self.frontend = ElevatorWebview(
                http_port=self.http_port,
                ws_port=self.ws_port,
                show_debug=show_debug,
            )

        self.last_update_time = time.time()

    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        if not self.running:  # Avoid multiple calls if already shutting down
            return
        print(f"\nReceived signal {signum}. Initiating shutdown...")
        self.running = False  # Signal all loops to stop

        if not self.headless and hasattr(self, "frontend") and self.frontend:
            print("Attempting to stop webview from signal handler...")
            # This should cause webview.start() in the main thread to return
            self.frontend.stop()

    def cleanup(self):
        """Clean up all resources"""
        if self._cleanup_done:
            return

        print("Cleaning up application resources...")
        self._cleanup_done = True
        self.running = False  # Ensure all loops are signaled to stop

        # Stop frontend if it exists and was initialized
        if hasattr(self, "frontend") and self.frontend:
            try:
                print("Stopping frontend...")
                self.frontend.stop()
                print("Frontend stopped.")
            except Exception as e:
                print(f"Error stopping frontend: {e}")

        # Stop WebSocket bridge
        if hasattr(self, "bridge") and self.bridge:
            try:
                self.bridge.stop()
                print("WebSocket bridge stopped.")
            except Exception as e:
                print(f"Error stopping WebSocket bridge: {e}")

        # Stop HTTP server if running
        if hasattr(self, "http_server") and self.http_server:
            try:
                self.http_server.stop()
                print("HTTP server stopped.")
            except Exception as e:
                print(f"Error stopping HTTP server: {e}")

        # Stop backend ZMQ coordinator
        if (
            hasattr(self, "backend")
            and self.backend
            and hasattr(self.backend, "zmq_coordinator")
        ):
            try:
                self.backend.zmq_coordinator.stop()
                print("ZMQ coordinator stopped.")
            except Exception as e:
                print(f"Error stopping ZMQ coordinator: {e}")

        # Join the backend thread if it's running
        if self.backend_thread and self.backend_thread.is_alive():
            print("Waiting for backend thread to finish...")
            self.backend_thread.join(timeout=5)  # Wait for up to 5 seconds
            if self.backend_thread.is_alive():
                print("Backend thread did not finish in time.")

        print("Application cleanup completed.")

    def update(self):
        """Update the backend state and process messages"""
        current_time = time.time()
        if current_time - self.last_update_time >= 0.1:  # Update 10 times per second
            # Removed self.frontend.update() as pywebview handles its own rendering
            # based on WebSocket messages.

            if (
                self.backend
                and hasattr(self.backend, "zmq_coordinator")
                and hasattr(self.backend.zmq_coordinator, "has_queued_messages")
                and hasattr(self.backend.zmq_coordinator, "get_next_msg_for_processing")
                and hasattr(self.backend, "api")
            ):
                zmq_coord = self.backend.zmq_coordinator
                while zmq_coord.has_queued_messages():
                    command_or_error_obj, timestamp = (
                        zmq_coord.get_next_msg_for_processing()
                    )
                    if command_or_error_obj:
                        self.backend.api.parse_and_handle_message(command_or_error_obj)

            self.backend.update()
            self.bridge.sync_backend()
            self.last_update_time = current_time

    def _background_tasks_loop(self):
        """Runs backend updates in a loop for non-headless mode."""
        print("Backend update loop started.")
        try:
            while self.running:
                self.update()
                time.sleep(0.01)
        except Exception as e:
            print(f"Exception in background task loop: {e}")
        finally:
            print("Backend update loop finished.")

    def run(self):
        """Run the application main loop"""
        try:
            if not self.headless:
                if not self.frontend:
                    print("Error: Frontend not initialized for non-headless mode.")
                    self.running = False  # Prevent loop execution
                    return  # Exit early

                # Start background tasks in a separate thread
                self.backend_thread = threading.Thread(
                    target=self._background_tasks_loop, daemon=True
                )
                self.backend_thread.start()

                print("Starting pywebview frontend...")
                # webview.start() is blocking and must run on the main thread.
                self.frontend.start()

                # This point is reached when the webview window is closed by the user
                print("pywebview frontend closed.")
                self.running = False  # Signal background thread to stop

            else:  # Headless mode
                print("Running in headless mode. Backend tasks on main thread.")
                while self.running:
                    self.update()
                    time.sleep(0.01)
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received by main thread.")
            self.running = False  # Signal all loops to stop
        except Exception as e:
            print(f"An unexpected error occurred in the main run loop: {e}")
            self.running = False  # Ensure shutdown on unexpected error
        finally:
            # Ensure cleanup is called regardless of how the loop exits
            # If backend_thread was started, make sure it's joined
            if self.backend_thread and self.backend_thread.is_alive():
                print("Waiting for backend thread to complete upon exiting run()...")
                self.backend_thread.join(timeout=5)
            self.cleanup()

    def _allocate_ports(self) -> None:
        """Centralized port allocation for all services."""
        from backend.utility import find_available_port

        HOST = "127.0.0.1"

        # Allocate WebSocket port if not specified
        if self._initial_ws_port is None:
            print(
                "WebSocket port not specified, attempting to find an available port starting from 18675..."
            )
            found_ws_port = find_available_port(HOST, 18675, 18775)
            if found_ws_port is None:
                print(
                    "ElevatorApp: Error - Could not find an available WebSocket port in range 18675-18775."
                )
                raise ConnectionError("Failed to find an available WebSocket port.")
            self.ws_port = found_ws_port
            print(f"ElevatorApp: Auto-selected WebSocket port {self.ws_port}")
        else:
            self.ws_port = self._initial_ws_port
            print(f"Using user-specified WebSocket port: {self.ws_port}")

        # Allocate HTTP port based on mode
        if not self.headless:  # GUI mode always needs HTTP server
            if self._initial_http_port is None:
                print(
                    "HTTP port not specified, attempting to find an available port starting from 19090..."
                )
                found_http_port = find_available_port(HOST, 19090, 19190)
                if found_http_port is None:
                    print(
                        "ElevatorApp: Error - Could not find an available HTTP port for GUI mode."
                    )
                    raise ConnectionError(
                        "Failed to find an available HTTP port for GUI mode."
                    )
                self.http_port = found_http_port
                print(
                    f"ElevatorApp: Auto-selected HTTP port {self.http_port} for GUI mode"
                )
            else:
                self.http_port = self._initial_http_port
                print(f"Using user-specified HTTP port: {self.http_port}")
        else:  # Headless mode - HTTP server is optional
            if self._initial_http_port is not None:
                if self._initial_http_port == 0:  # 0 means find available port
                    found_http_port = find_available_port(HOST, 19090, 19190)
                    if found_http_port is None:
                        print(
                            "ElevatorApp: Warning - Could not find an available HTTP port for headless mode."
                        )
                        self.http_port = None  # Disable HTTP server
                    else:
                        self.http_port = found_http_port
                        print(
                            f"ElevatorApp: Auto-selected HTTP port {self.http_port} for headless mode"
                        )
                else:
                    self.http_port = self._initial_http_port
                    print(f"Using user-specified HTTP port: {self.http_port}")
            else:
                self.http_port = None
                print("ElevatorApp: No HTTP server for headless mode")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Elevator Simulation")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug features (passed to frontend URL)",
    )
    parser.add_argument(
        "--ws-port",
        type=int,
        default=None,
        help="WebSocket server port (default: find available)",
    )
    parser.add_argument(
        "--http-port",
        type=int,
        default=None,
        help="HTTP server port. If not specified, an attempt will be made to find an available port. (default: find available)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode without launching webview",
    )
    parser.add_argument(
        "--zmq-port",
        type=str,
        default="19982",
        help="ZMQ server port for client communication (default: 19982)",
    )
    parser.add_argument(
        "--console", action="store_true", help="Force output to console"
    )
    args = parser.parse_args()

    # Conditionally allocate console for headless/debug mode if packaged as windowed app
    if args.headless or args.debug or args.console:
        from backend.utility import allocate_console_if_needed

        allocate_console_if_needed()

    app = ElevatorApp(
        show_debug=args.debug,
        ws_port=args.ws_port,
        http_port=args.http_port,
        zmq_port=args.zmq_port,
        headless=args.headless,
    )

    app.run()
