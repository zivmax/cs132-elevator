import zmq
import threading
import time
from typing import Optional, List, Tuple
from collections import deque


class ZmqClientThread(threading.Thread):

    def __init__(
        self, serverIp: str = "127.0.0.1", port: str = "27132", identity: str = "GroupX"
    ) -> None:
        threading.Thread.__init__(self)
        self._context: zmq.Context = zmq.Context()
        self._socket: zmq.Socket = self._context.socket(zmq.DEALER)
        self._serverIp: str = serverIp
        self._identity: str = identity
        self._port: str = port
        self._socket.setsockopt_string(
            zmq.IDENTITY, identity
        )  # default encoding is UTF-8 #Set your IDENTITY before connection.

        # Instead of single message, use queues to store multiple messages
        self._messageQueue: deque = deque()
        self._timestampQueue: deque = deque()
        self._lock = threading.Lock()  # Thread safety for queue operations

        # Keep the original variables for backwards compatibility
        self._receivedMessage: Optional[str] = None
        self._messageTimeStamp: Optional[int] = None

        self._socket.connect(
            f"tcp://{serverIp}:{port}"
        )  # Both ("tcp://localhost:27132") and ("tcp://127.0.0.1:27132") are OK

        self.sendMsg(f"Client[{self._identity}] is online")  ##Telling server I'm online
        self.start()  # start the client thread

    @property
    def messageTimeStamp(self) -> int:
        if self._messageTimeStamp == None:
            return -1
        else:
            return self._messageTimeStamp

    @messageTimeStamp.setter
    def messageTimeStamp(self, value: int) -> None:
        self._messageTimeStamp = value

    @property
    def receivedMessage(self) -> str:
        if self._receivedMessage == None:
            return ""
        else:
            return self._receivedMessage

    @receivedMessage.setter
    def receivedMessage(self, value: str) -> None:
        self._receivedMessage = value

    # Get all messages in the queue
    def get_all_messages(self) -> List[Tuple[str, int]]:
        with self._lock:
            return list(zip(self._messageQueue, self._timestampQueue))

    # Get the latest message without removing it
    def peek_latest_message(self) -> Tuple[str, int]:
        with self._lock:
            if self._messageQueue:
                return (self._messageQueue[-1], self._timestampQueue[-1])
            return ("", -1)

    # Get and remove the oldest message (FIFO)
    def get_next_message(self) -> Tuple[str, int]:
        with self._lock:
            if self._messageQueue:
                message = self._messageQueue.popleft()
                timestamp = self._timestampQueue.popleft()
                return (message, timestamp)
            return ("", -1)

    # Listen from the server
    # You can rewrite this part as long as it can receive messages from server.
    def __launch(self, socket: zmq.Socket) -> None:
        while True:
            if not socket.closed:
                message: bytes = socket.recv()  # recv_multipart
                message_str: str = message.decode()
                print(
                    f"Message from server: {message_str}"
                )  # Helpful for debugging. You can comment out this statement.

                # Add to queue and also maintain compatibility with old code
                timestamp = int(round(time.time() * 1000))  # UNIX Time Stamp
                with self._lock:
                    self._messageQueue.append(message_str)
                    self._timestampQueue.append(timestamp)

                # Keep the previous behavior for backward compatibility
                self.receivedMessage = message_str
                self.messageTimeStamp = timestamp
            else:
                print("socket is closed,can't receive any message...")
                break

    # Override the function in threading.Thread
    def run(self) -> None:
        self.__launch(self._socket)

    # Send messages to the server
    # You can rewrite this part as long as you can send messages to server.
    def sendMsg(self, data: str) -> None:
        if not self._socket.closed:
            self._socket.send_string(data)
        else:
            print("socket is closed,can't send message...")
