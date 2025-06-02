import os
import sys
import webview


class ElevatorWebview:  # Renamed from VendingWebview
    """Main window for the Elevator UI using pywebview to display the webpage."""

    def __init__(
        self,
        ws_port: int = 8765,  # Default from your pywebview code, main.py uses 18675
        http_port: int | None = None,
        show_debug: bool = False,  # Added for consistency with main.py
    ) -> None:
        self.ws_port = ws_port
        self.http_port = http_port  # Store http_port
        self.window = None

        if self.http_port:
            # Load from HTTP server if http_port is provided
            self.html_url = f"http://localhost:{self.http_port}?wsPort={self.ws_port}&showDebug={str(show_debug).lower()}"
            print(
                f"ElevatorWebview: Initializing with pywebview. HTTP URL: {self.html_url}"
            )
        else:
            # Fallback to file URL if http_port is not available (though less ideal)
            html_file_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "ui", "index.html")
            )
            if not os.path.exists(html_file_path):
                print(
                    f"Error: HTML file not found at {html_file_path}", file=sys.stderr
                )
                sys.exit(1)
            self.html_url = f"file://{html_file_path}?wsPort={self.ws_port}"
            print(
                f"ElevatorWebview: Initializing with pywebview. File URL: {self.html_url}"
            )

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
