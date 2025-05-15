import os
import sys
from typing import TYPE_CHECKING, Dict, Any
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtGui import QIcon  # Add this import

from frontend.bridge import WebBridge

if TYPE_CHECKING:
    from backend.world import World


class ElevatorWebview(QMainWindow):
    """Main window for the elevator UI using QtWebEngine"""

    def __init__(self, world: "World" = None, show_debug: bool = True):
        super().__init__()
        self.bridge = WebBridge(parent=self, world=world)
        self.show_debug = show_debug

        # Setup the UI
        self.setWindowTitle("Elevator Simulation")
        self.resize(1024, 768)

        # Set the window icon
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "ui", "assets", "elevator.png")
        self.setWindowIcon(QIcon(icon_path))

        # Create the web view
        self.web_view = QWebEngineView(self)
        self.setCentralWidget(self.web_view)        # Set up web channel for communication
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        # Load the HTML file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, "ui", "index.html")
        
        # Prepare to pass the debug flag to the web page
        self.web_view.loadFinished.connect(self.on_load_finished)
        
        # Load the HTML
        self.web_view.load(QUrl.fromLocalFile(html_path))
        
    def update(self):
        self.bridge.sync_backend()
        
    def on_load_finished(self, success):
        if success:
            # Pass the debug flag to JavaScript
            script = f"window.showDebugPanel = {str(self.show_debug).lower()}; console.log('Python set showDebugPanel to: {str(self.show_debug).lower()}');"
            self.web_view.page().runJavaScript(script)


def run_standalone():
    """Run the elevator UI as a standalone application for testing"""
    app = QApplication(sys.argv)
    window = ElevatorWebview()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_standalone()
