import zmq
import os
import threading
import time
from typing import Optional, List, Tuple
from collections import deque


class ZmqClientThread(threading.Thread):

    # Modified: Now accepts an API instance for automatic message processing
    def __init__(
        self,
        serverIp: str = "127.0.0.1",
        port: str = "19983",
        identity: str = "Group17",  # Using Group17 identity
        api_instance=None,  # API instance for message processing
    ) -> None:
        threading.Thread.__init__(self)
        self._context: zmq.Context = zmq.Context()
        # Using DEALER socket as per original file content
        self._socket: zmq.Socket = self._context.socket(zmq.DEALER)
        self._serverIp: str = serverIp
        self._identity: str = identity
        self._port: str = port
        self._api_instance = api_instance  # Store API instance for message processing
        self._socket.setsockopt_string(
            zmq.IDENTITY, identity
        )  # Set IDENTITY before connection for DEALER.

        self._messageQueue: deque = deque()
        self._timestampQueue: deque = deque()
        self._lock = threading.Lock()

        self._receivedMessage: Optional[str] = None
        self._messageTimeStamp: Optional[int] = None

        self.running = False  # Flag to control the loop

    # Connect method to be called explicitly after creation
    def connect_and_start(self) -> None:
        try:
            connection_string = f"tcp://{self._serverIp}:{self._port}"
            print(f"NetClient: Connecting to server at {connection_string}...")
            self._socket.connect(connection_string)
            print("NetClient: Connected.")
            self.running = True
            # Send initial online message directly
            self.send_msg(f"Client[{self._identity}] is online")
            self.start()  # Start the thread's run method (which calls __launch)
        except zmq.ZMQError as e:
            print(f"NetClient: Error connecting ZMQ socket: {e}")
            self.running = False
        except Exception as e:
            print(f"NetClient: Unexpected error during connection: {e}")
            self.running = False

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
                # Update compatibility variables as well
                self.receivedMessage = message
                self.messageTimeStamp = timestamp
                return (message, timestamp)
            # Reset compatibility variables if queue is empty
            self.receivedMessage = None
            self.messageTimeStamp = None
            return ("", -1)

    def __launch(self) -> None:
        """Main loop for receiving messages and processing them automatically."""
        poller = zmq.Poller()
        poller.register(self._socket, zmq.POLLIN)

        while self.running:
            try:
                # Poll with a timeout (e.g., 100ms) to allow checking self.running
                socks = dict(poller.poll(100))
                if self._socket in socks and socks[self._socket] == zmq.POLLIN:
                    # Using recv_multipart with DEALER in case server sends identity frame first
                    message_parts: List[bytes] = self._socket.recv_multipart()
                    # Assuming the last part is the actual message content
                    message_str: str = message_parts[-1].decode()
                    print(f"NetClient: Received message: {message_str}")  # Debugging

                    timestamp = int(round(time.time() * 1000))

                    # If API instance is available, process message immediately
                    if self._api_instance and hasattr(
                        self._api_instance, "_parse_and_execute"
                    ):
                        try:
                            response = self._api_instance._parse_and_execute(
                                message_str
                            )
                            if response:
                                self.send_msg(response)
                        except Exception as e:
                            print(
                                f"NetClient: Error processing message automatically: {e}"
                            )

                    # Also store in queue for backward compatibility
                    with self._lock:
                        self._messageQueue.append(message_str)
                        self._timestampQueue.append(timestamp)

            except zmq.ZMQError as e:
                if e.errno == zmq.ETERM:
                    print("NetClient: ZMQ context terminated, exiting loop.")
                    break
                else:
                    print(f"NetClient: ZMQ Error receiving: {e}")
                    self.running = False  # Stop on other ZMQ errors
                    break
            except Exception as e:
                print(f"NetClient: Unexpected error in receive loop: {e}")
                # Decide whether to continue or break
                time.sleep(1)  # Avoid busy-looping

        print("NetClient: Receive loop finished.")
        # Clean up socket and context
        if not self._socket.closed:
            self._socket.close(linger=0)  # Ensure linger is 0 for immediate close
        if not self._context.closed:
            self._context.term()
        print("NetClient: Socket and context closed.")

    # Override the function in threading.Thread
    def run(self) -> None:
        self.__launch()

    # Send messages to the server (This method is called by the API)
    def send_msg(self, data: str) -> None:
        if not self.running or self._socket.closed:
            print("NetClient: Cannot send message, socket not running or closed.")
            return
        try:
            print(f"NetClient: Sending message: {data}")  # Debugging send
            # With DEALER, just send the data. Server (ROUTER) will know identity.
            self._socket.send_string(data)
        except zmq.ZMQError as e:
            print(f"NetClient: Error sending message: {e}")
            # Consider if sending error should stop the client
            # self.running = False
        except Exception as e:
            print(f"NetClient: Unexpected error sending message: {e}")

    def stop(self) -> None:
        """Signals the thread to stop."""
        print("NetClient: Stopping...")
        self.running = False
