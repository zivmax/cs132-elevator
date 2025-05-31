import os
import sys
from typing import TYPE_CHECKING, Dict, Any
from PyQt6.QtCore import QUrl, QUrlQuery  # Import QUrlQuery
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QIcon

from frontend.bridge import WebSocketBridge

if TYPE_CHECKING:
    from backend.world import World


class ElevatorWebview(QMainWindow):
    """Main window for the elevator UI using QtWebEngine with WebSocket communication"""

    def __init__(
        self,
        bridge: WebSocketBridge,  # Changed to accept WebSocketBridge instance
        show_debug: bool = False,  # Default changed to False
        remote_debugging_port: int = 0,
        ws_port: int = 8765,  # ws_port is still needed for the URL query
        app_cleanup_callback=None,  # Add cleanup callback parameter
    ):
        super().__init__()
        self.bridge = bridge  # Use the passed WebSocketBridge instance
        self.show_debug = show_debug  # Store show_debug status
        self.ws_port = ws_port
        self.app_cleanup_callback = app_cleanup_callback  # Store cleanup callback

        # Enable remote debugging if a port is specified
        if remote_debugging_port > 0:
            os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = str(remote_debugging_port)

        # Setup the UI
        self.setWindowTitle("Elevator Simulation")
        self.resize(1024, 768)

        # Set the window icon
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "ui", "assets", "elevator.png")
        self.setWindowIcon(QIcon(icon_path))

        # Create the web view
        self.web_view = QWebEngineView(self)
        self.setCentralWidget(self.web_view)

        # Load the HTML file that uses WebSockets, append ws_port and show_debug as URL params
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, "ui", "index.html")
        url = QUrl.fromLocalFile(html_path)

        query = QUrlQuery()
        query.addQueryItem("wsPort", str(ws_port))
        query.addQueryItem(
            "showDebug", "true" if self.show_debug else "false"
        )  # Pass show_debug as a URL parameter
        url.setQuery(query)

        self.web_view.load(url)

    def update(self):
        """Update the UI based on backend state"""
        self.bridge.sync_backend()

    def closeEvent(self, event):
        """Clean up resources when the window is closed"""
        print("Window close event triggered")
        if self.app_cleanup_callback:
            self.app_cleanup_callback()
        super().closeEvent(event)


def run_standalone():
    """Run the elevator UI as a standalone application for testing"""
    # This function would need a mock World and API to run standalone now.
    # For simplicity, I'll comment out its direct runnability without them.
    # app = QApplication(sys.argv)
    # window = ElevatorWebSocketView() # This would fail without world and api
    # window.show()
    # sys.exit(app.exec())
    print(
        "run_standalone needs to be updated to provide World and ElevatorAPI instances."
    )


if __name__ == "__main__":
    # run_standalone()
    print("To run webview standalone, it now requires World and ElevatorAPI instances.")
