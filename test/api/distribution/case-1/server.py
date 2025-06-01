import time
import zmq
import threading
import sys
import os
import queue


class ZmqServerThread(threading.Thread):
    _port = 19982
    clients_addr = set()

    def __init__(self, server_port: int = None) -> None:
        threading.Thread.__init__(self)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.bound_client = None
        self._sent_timestamp: int = None
        self.recv_queue = queue.Queue()
        self._last_received = {
            "message": "",
            "timestamp": -1,
        }
        self.msg_queue: queue.Queue = queue.Queue()

        if server_port is not None:
            self.port = server_port

        print(f"Start hosting at port:{self._port}")
        self.t = threading.Thread(target=self.listen_queue)
        self.t.start()
        print("Start listening queue")
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
    def message_timestamp(self) -> int:
        return self._last_received["timestamp"]

    @property
    def received_message(self) -> str:
        try:
            msg = self.recv_queue.get_nowait()
            self._last_received["message"] = msg["message"]
            self._last_received["timestamp"] = msg["timestamp"]
        except queue.Empty:
            pass
        return self._last_received["message"]

    @property
    def sent_timestamp(self) -> int:
        if self._sent_timestamp is None:
            return -1
        else:
            return self._sent_timestamp

    @sent_timestamp.setter
    def sent_timestamp(self, value: int):
        self._sent_timestamp = value

    def hosting(self, server_port: int = None) -> None:
        if server_port is not None:
            self.port = server_port
        self.socket.bind(f"tcp://127.0.0.1:{self.port}")
        while True:
            [address, contents] = self.socket.recv_multipart()
            address_str = address.decode()
            contents_str = contents.decode()
            self.clients_addr.add(address_str)
            timestamp = int(round(time.time() * 1000))
            if contents_str.endswith("is online") or ("door_closed" in contents_str):
                print(
                    f"(skipped message) Client:[{address_str}] message:{contents_str} Timestamp:{timestamp}\n"
                )
                continue
            self.recv_queue.put({"message": contents_str, "timestamp": timestamp})
            print(
                f"Client:[{address_str}] message:{contents_str} Timestamp:{timestamp}\n"
            )

    def listen_queue(self):
        while True:
            if (not self.msg_queue.empty()) and (
                (int(round(time.time() * 1000)) - self.sent_timestamp) > 800
            ):
                self.sent_timestamp = int(round(time.time() * 1000))
                self.__send_string(self.bound_client, self.msg_queue.get())

    def send_string(self, address: str, msg: str = ""):
        self.msg_queue.put(msg)

    def __send_string(self, address: str, msg: str = ""):
        if not self.socket.closed:
            print(f"Server:[{str(address)}] message:{str(msg)}\n")
            self.socket.send_multipart([address.encode(), msg.encode()])
        else:
            print("socket is closed,can't send message...")

    def run(self):
        self.hosting()
