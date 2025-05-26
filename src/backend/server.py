import asyncio
import json
import websockets
import threading
from typing import Dict, Any, Callable, Set, Optional, TYPE_CHECKING

class WebSocketServer:
    """WebSocket server for communication between backend and frontend"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8765, message_handler: Optional[Callable[[str], str]] = None):
        self.host = host
        self.port = port
        self._clients: Set[websockets.WebSocketServerProtocol] = set()
        self.message_handler = message_handler # New: message handler
        self._server = None
        self._thread = None
        self._stop_event = threading.Event()
        self.loop: Optional[asyncio.AbstractEventLoop] = None # Added for storing the event loop

    async def _process_message(self, websocket, message: str) -> str:
        """Process incoming message from client"""
        try:
            # Log the message for debugging
            print(f"Received from client: {message}")

            if self.message_handler:
                return self.message_handler(message)
            
            # If no message handler, return an error
            return json.dumps(
                {"status": "error", "message": "No message handler registered"}
            )
        except Exception as e:
            print(f"Error processing message: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    async def _handle_connection(self, websocket):
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

    async def broadcast(self, message: str):
        """Send a message to all connected clients"""
        if not self._clients:  # No clients connected
            return
            
        tasks = [client.send(message) for client in self._clients]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_server(self):
        """Run the WebSocket server"""
        async with websockets.serve(self._handle_connection, self.host, self.port):
            print(f"WebSocket server started on ws://{self.host}:{self.port}")
            while not self._stop_event.is_set():
                await asyncio.sleep(0.1)  # Small sleep to avoid CPU hogging

    def _run_in_thread(self):
        """Run the server in a separate thread"""
        self.loop = asyncio.new_event_loop() # Assign the new loop to self.loop
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._run_server())
        finally:
            if self.loop.is_running():
                self.loop.stop() # Stop the loop if it's still running
            self.loop.close() # Close the loop

    def start(self):
        """Start the WebSocket server in a separate thread"""
        self._thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self._thread.start()
        print(f"WebSocket server thread started")
        return self

    def stop(self):
        """Stop the WebSocket server"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0) # Increased timeout slightly for graceful shutdown
        print("WebSocket server stopped")
        
    @property
    def is_running(self):
        """Return True if the server is running (not stopped)."""
        return not self._stop_event.is_set()

    def send_elevator_updated(self, data: Dict[str, Any]):
        """Send elevator state update to frontend"""
        message = json.dumps({
            "type": "elevatorUpdated",
            "payload": data
        })
        
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.broadcast(message),
                self.loop # Use the stored loop
            )
        else:
            print("WebSocket server loop not available or closed when trying to send elevator_updated.")
