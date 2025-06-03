import os
import sys
import webview


class ElevatorWebview:  # Renamed from VendingWebview
    """Main window for the Elevator UI using pywebview to display the webpage."""
    
    def __init__(
        self,
        http_port: int,  # Now required - no longer optional
        ws_port: int = 8765,  # Default from your pywebview code, main.py uses 18675
        show_debug: bool = False,  # Added for consistency with main.py
    ) -> None:
        self.ws_port = ws_port
        self.http_port = http_port
        self.window = None

        # Always use HTTP server - http_port is guaranteed to be provided
        self.html_url = f"http://localhost:{self.http_port}?wsPort={self.ws_port}&showDebug={str(show_debug).lower()}"
        print(f"ElevatorWebview: Initializing with pywebview. HTTP URL: {self.html_url}")

    def start(self) -> None:
        """Create and show the pywebview window."""
        # No js_api is passed if all communication is handled by existing WebSocket bridge
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "ui", "assets", "elevator.ico")
        self.window = webview.create_window(
            "Elevator Simulation",
            url=self.html_url,
            width=1200,  # Adjust as needed
            height=800,  # Adjust as needed
        )
        webview.start(icon=icon_path)

    def stop(self) -> None:
        """Stops the pywebview window and application."""
        if self.window:
            print("ElevatorWebview: Destroying window.")
            self.window.destroy()
        # Note: webview.start() is blocking. Stopping might need to be handled
        # from another thread or by how the main application loop is structured
        # if pywebview doesn't exit the process on window close.
