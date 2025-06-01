import time
import signal
import argparse
import threading  # Added for background tasks

from backend.world import World
from backend.api import ElevatorAPI  # Import ElevatorAPI
from frontend.webview import ElevatorWebview
from frontend.bridge import WebSocketBridge  # Import WebSocketBridge
from backend.server import ElevatorHTTPServer  # Import HTTPServer


class ElevatorApp:
    def __init__(
        self,
        show_debug=False,
        ws_port=18675,
        http_port=19090,
        headless=False,
    ):
        self.headless = headless
        self.running = True
        self._cleanup_done = False
        self.frontend = None  # Initialize frontend attribute
        self.backend_thread = None  # Initialize backend_thread attribute


        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.backend = World()
        self.elevator_api = ElevatorAPI(self.backend, self.backend.zmq_coordinator)
        self.backend.set_api_and_initialize_components(self.elevator_api)
        self.bridge = WebSocketBridge(
            world=self.backend, api=self.elevator_api, port=ws_port
        )

        self.http_server = None
        if http_port is not None:
            self.http_server = ElevatorHTTPServer(port=http_port)
            self.http_server.start()
            # show_debug is used here for the informational print message
            print(
                f"HTTP server running. Access frontend at http://127.0.0.1:{http_port}/?wsPort={ws_port}&showDebug={str(show_debug).lower()}"
            )

        if headless:
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
            # Initialize frontend with pywebview
            self.frontend = ElevatorWebview(
                ws_port=ws_port,
                http_port=http_port,  # Pass http_port, webview will construct its own URL
                show_debug=show_debug,  # Pass show_debug to frontend
            )
            # self.frontend.start() will be called in the run() method

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

        # If running in headless mode or if webview.start() hasn't been called yet,
        # setting self.running = False should be enough for the run() loop to terminate.
        # Cleanup is called in the finally block of run().

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
                        self.backend.api.parse_and_handle_message(
                            command_or_error_obj
                        )

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Elevator Simulation")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug features (passed to frontend URL)"
    )
    # Removed --cdp argument as it's no longer used
    # parser.add_argument(
    #     "--cdp", type=int, default=19982, help="Chromium debugging port"
    # )
    parser.add_argument(
        "--ws-port", type=int, default=18675, help="WebSocket server port"
    )
    parser.add_argument(
        "--http-port",
        type=int,
        default=19090,
        help="HTTP server port. If specified, an HTTP server will host the frontend.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode without launching webview",
    )
    args = parser.parse_args()

    app = ElevatorApp(
        show_debug=args.debug,
        # remote_debugging_port=args.cdp, # Removed
        ws_port=args.ws_port,
        http_port=args.http_port,
        headless=args.headless,
    )

    app.run()
