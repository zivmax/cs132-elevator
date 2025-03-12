import zmq
import os
import threading
import time
from typing import Optional


class ZmqClientThread(threading.Thread):

    def __init__(self, serverIp: str = "127.0.0.1", port: str = "27132", identity: str = "GroupX") -> None:
        threading.Thread.__init__(self)
        self._context: zmq.Context = zmq.Context()
        self._socket: zmq.Socket = self._context.socket(zmq.DEALER)
        self._serverIp: str = serverIp
        self._identity: str = identity
        self._port: str = port
        self._socket.setsockopt_string(
            zmq.IDENTITY, identity
        )  # default encoding is UTF-8 #Set your IDENTITY before connection.
        self._receivedMessage: Optional[str] = None
        self._messageTimeStamp: Optional[int] = None  # UNIX Time Stamp, should be int

        self._socket.connect(
            f"tcp://{serverIp}:{port}"
        )  # Both ("tcp://localhost:27132") and ("tcp://127.0.0.1:27132") are OK

        self.sendMsg(
            f"Client[{self._identity}] is online"
        )  ##Telling server I'm online
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
                self.receivedMessage = message_str
                self.messageTimeStamp = int(
                    round(time.time() * 1000)
                )  # UNIX Time Stamp
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
