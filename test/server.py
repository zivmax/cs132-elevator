import time
import zmq
import threading
import sys
import os
from typing import Set, Optional, Any, List, Tuple


class ZmqServerThread(threading.Thread):
    _port: int = 27132
    clients_addr: Set[str] = set()

    def __init__(self, server_port: Optional[int] = None) -> None:
        threading.Thread.__init__(self)
        self.context: zmq.Context = zmq.Context()
        self.socket: zmq.Socket = self.context.socket(zmq.ROUTER)
        self.bindedClient: Optional[str] = None
        self._receivedMessage: Optional[str] = None
        self._messageTimeStamp: Optional[int] = None  # UNIX Time Stamp, should be int

        if server_port is not None:
            self.port = server_port

        print(f"Start hosting at port:{self._port}")
        self.start()

    @property
    def port(self) -> int:
        return self._port

    @port.setter
    def port(self, value: int) -> None:
        if value < 0 or value > 65535:
            raise ValueError("score must between 0 ~ 65535!")
        self._port = value

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

    # start listening
    def hosting(self, server_port: Optional[int] = None) -> None:

        if server_port is not None:
            self.port = server_port
        self.socket.bind(f"tcp://{'127.0.0.1'}:{self.port}")

        while True:
            address_and_contents: List[bytes] = self.socket.recv_multipart()
            address: bytes = address_and_contents[0]
            contents: bytes = address_and_contents[1]
            address_str: str = address.decode()
            contents_str: str = contents.decode()
            self.clients_addr.add(address_str)
            self.messageTimeStamp = int(round(time.time() * 1000))  # UNIX Time Stamp
            self.receivedMessage = contents_str
            print(f"Client:[{address_str}] message:{contents_str}\n")

    def send_string(self, address: str, msg: str = "") -> None:
        if not self.socket.closed:
            print(f"Server:[{str(address)}] message:{str(msg)}\n")
            self.socket.send_multipart(
                [address.encode(), msg.encode()]
            )  # send msg to address
        else:
            print("socket is closed,can't send message...")

    # override
    def run(self) -> None:
        self.hosting()
