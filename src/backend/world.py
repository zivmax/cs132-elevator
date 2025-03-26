import time
from typing import List, Tuple, Deque
from collections import deque

from .net_client import ZmqClientThread
from .elevator import Elevator
from .engine import Engine
from .dispatcher import Dispatcher


class World:
    def __init__(self) -> None:
        self.testclient: ZmqClientThread = ZmqClientThread(identity="Team17")
        self.engine: Engine = Engine(self)  # Create engine first
        self.elevators: List[Elevator] = [Elevator(1, self), Elevator(2, self)]
        self.dispatcher: Dispatcher = Dispatcher(self)

        # Message queue for storing messages from any source
        self._message_queue: Deque[Tuple[str, int]] = deque()
        self._last_checked_timestamp: int = -1

        time.sleep(1)  # Give time for the client to connect

    def update(self) -> None:
        # Check for new messages from network client
        self._check_testclient_msg()

        # Update components in the correct order
        self.dispatcher.update()  # Process user requests
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
        """Add a message from any source (e.g., Qt API)"""
        timestamp = int(round(time.time() * 1000))
        self._message_queue.append((message, timestamp))

    def get_next_msg(self) -> Tuple[str, int]:
        """Get the next message from the queue"""
        if self._message_queue:
            return self._message_queue.popleft()
        return ("", -1)

    def has_msg(self) -> bool:
        """Check if there are messages in the queue"""
        return len(self._message_queue) > 0

    def send_msg(self, message: str) -> None:
        self.testclient.sendMsg(message)
