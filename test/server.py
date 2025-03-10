import time
import zmq
import threading
import sys
import os


class ZmqServerThread(threading.Thread):
    _port = 27132
    clients_addr = set()

    def __init__(self, server_port: int = None) -> None:
        threading.Thread.__init__(self)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.bindedClient = None
        self._receivedMessage: str = None
        self._messageTimeStamp: int = None  # UNIX Time Stamp, should be int

        if server_port is not None:
            self.port = server_port

        print("Start hosting at port:{port}".format(port=self._port))
        self.start()

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value: int):
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
    def messageTimeStamp(self, value: int):
        self._messageTimeStamp = value

    @property
    def receivedMessage(self) -> str:
        if self._receivedMessage == None:
            return ""
        else:
            return self._receivedMessage

    @receivedMessage.setter
    def receivedMessage(self, value: str):
        self._receivedMessage = value

    # start listening
    def hosting(self, server_port: int = None) -> None:

        if server_port is not None:
            self.port = server_port
        self.socket.bind("tcp://{0}:{1}".format("127.0.0.1", self.port))

        while True:
            [address, contents] = self.socket.recv_multipart()
            address_str = address.decode()
            contents_str = contents.decode()
            self.clients_addr.add(address_str)
            self.messageTimeStamp = int(round(time.time() * 1000))  # UNIX Time Stamp
            self.receivedMessage = contents_str
            print("Client:[%s] message:%s\n" % (address_str, contents_str))

    def send_string(self, address: str, msg: str = ""):
        if not self.socket.closed:
            print("Server:[%s] message:%s\n" % (str(address), str(msg)))
            self.socket.send_multipart(
                [address.encode(), msg.encode()]
            )  # send msg to address
        else:
            print("socket is closed,can't send message...")

    # override
    def run(self):
        self.hosting()
