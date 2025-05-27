import time
from typing import List, Tuple, Deque

from collections import deque

from .net_client import ZmqClientThread
from .elevator import Elevator
from .engine import Engine
from .dispatcher import Dispatcher
from .api import ElevatorAPI


class World:
    def __init__(self) -> None:
        self.testclient: ZmqClientThread = ZmqClientThread(identity="Team17")
        self.api: ElevatorAPI = ElevatorAPI(self)  # Create API instance and pass self (world)
        self.engine: Engine = Engine(self)  # Create engine first
        # Pass the api instance to Elevator and Dispatcher
        self.elevators: List[Elevator] = [Elevator(1, self, self.api), Elevator(2, self, self.api)]
        self.dispatcher: Dispatcher = Dispatcher(self, self.api)

        # Message queue for storing messages from any source
        self._message_queue: Deque[Tuple[str, int]] = deque()
        self._last_checked_timestamp: int = -1

        time.sleep(1)  # Give time for the client to connect

    def update(self) -> None:
        # Check for new messages from network client
        self._check_testclient_msg()

        # Process messages from the queue using the API
        while self.has_msg():
            message, _ = self.get_next_msg()
            if message:
                self.api.parse_and_handle_message(message)  # API handles parsing

        # Update components in the correct order
        # Dispatcher no longer directly processes messages from world queue in its update
        self.dispatcher.update()  # Dispatcher update might be simplified or removed if all actions are API-triggered
        self.engine.update()  # Process movement

        # Update elevators last
        for elevator in self.elevators:
            elevator.update()

    def _check_testclient_msg(self) -> None:
        """Check for new messages from the network client"""
        if self.testclient.messageTimeStamp > self._last_checked_timestamp:
            self._last_checked_timestamp = self.testclient.messageTimeStamp
            message = self.testclient.receivedMessage
            if message:
                # Add message to queue with current timestamp
                timestamp = int(round(time.time() * 1000))
                self._message_queue.append((message, timestamp))

    def add_msg(self, message: str) -> None:
        """Add a message from any source (e.g., Qt API handlers in api.py)."""
        # This method is still used by the API's frontend handlers to queue requests
        # that originate from external sources like the web UI.
        timestamp = int(round(time.time() * 1000))
        self._message_queue.append((message, timestamp))
        print(f"World: Message added to queue by API: {message}")

    def get_next_msg(self) -> Tuple[str, int]:
        """Get the next message from the queue"""
        if self._message_queue:
            return self._message_queue.popleft()
        return ("", -1)

    def has_msg(self) -> bool:
        """Check if there are messages in the queue"""
        return len(self._message_queue) > 0
