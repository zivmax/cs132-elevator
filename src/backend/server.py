import asyncio
import json
import websockets
import threading
from typing import Dict, Any, Callable, Set, Optional
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import functools  # Add functools import


class WebSocketServer:
    """WebSocket server for communication between backend and frontend"""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 18765,
        message_handler: Optional[Callable[[str], str]] = None,
    ):
        self.host = host
        self.port = port
        self._clients: Set[websockets.WebSocketServerProtocol] = set()
        self.message_handler = message_handler
        self._server = None
        self._thread = None
        self._stop_event = threading.Event()
        self.loop: Optional[asyncio.AbstractEventLoop] = (
            None  # Added for storing the event loop
        )

    async def _process_message(
        self, websocket: websockets.WebSocketServerProtocol, message: str
    ) -> str:
        """Process incoming message from client"""
        try:
            # Log the message for debugging
            print(f"WebSocket: Received from client: {message}")

            if self.message_handler:
                return self.message_handler(message)

            # If no message handler, return an error
            return json.dumps(
                {"status": "error", "message": "No message handler registered"}
            )
        except Exception as e:
            print(f"Error processing message: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    async def _handle_connection(
        self, websocket: websockets.WebSocketServerProtocol
    ) -> None:
        """Handle a new WebSocket connection"""
        self._clients.add(websocket)
        try:
            async for message in websocket:
                # Process message and send response
                response = await self._process_message(websocket, message)
                await websocket.send(response)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._clients.remove(websocket)

    async def broadcast(self, message: str) -> None:
        """Send a message to all connected clients"""
        if not self._clients:  # No clients connected
            return

        tasks = [client.send(message) for client in self._clients]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_server(self) -> None:
        """Run the WebSocket server"""
        async with websockets.serve(self._handle_connection, self.host, self.port):
            print(f"WebSocket server started on ws://{self.host}:{self.port}")
            while not self._stop_event.is_set():
                await asyncio.sleep(0.1)  # Small sleep to avoid CPU hogging

    def _run_in_thread(self) -> None:
        """Run the server in a separate thread"""
        self.loop = asyncio.new_event_loop()  # Assign the new loop to self.loop
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._run_server())
        finally:
            if self.loop.is_running():
                self.loop.stop()  # Stop the loop if it's still running
            self.loop.close()  # Close the loop

    def start(self) -> "WebSocketServer":
        """Start the WebSocket server in a separate thread"""
        self._thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self._thread.start()
        print(f"WebSocket server thread started")
        return self

    def stop(self) -> None:
        """Stop the WebSocket server"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(
                timeout=2.0
            )  # Increased timeout slightly for graceful shutdown
        print("WebSocket server stopped")

    @property
    def is_running(self) -> bool:
        """Return True if the server is running (not stopped)."""
        return not self._stop_event.is_set()

    def send_elevator_states(self, data: Dict[str, Any]) -> None:
        """Send elevator state update to frontend"""
        message = json.dumps({"type": "elevatorUpdated", "payload": data})

        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.broadcast(message), self.loop  # Use the stored loop
            )
        else:
            print(
                "WebSocket server loop not available or closed when trying to send elevator_updated."
            )


class ElevatorHTTPServer(threading.Thread):
    """Simple HTTP server to serve static files for the frontend"""

    def __init__(
        self, host: str = "127.0.0.1", port: int = 8080, directory: str = None
    ) -> None:
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        # Determine the directory for static files
        if directory is None:
            # Assuming server.py is in src/backend, navigate to src/frontend/ui
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.directory = os.path.join(current_dir, "..", "frontend", "ui")
        else:
            self.directory = directory
        self.httpd = None

    def run(self) -> None:
        # Use functools.partial to pass the directory to SimpleHTTPRequestHandler
        handler_with_directory = functools.partial(
            SimpleHTTPRequestHandler, directory=self.directory
        )
        self.httpd = HTTPServer((self.host, self.port), handler_with_directory)
        print(
            f"HTTP server started on http://{self.host}:{self.port}, serving from {os.path.abspath(self.directory)}"
        )
        self.httpd.serve_forever()

    def stop(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            print("HTTP server stopped")
