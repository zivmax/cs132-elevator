import time
import zmq
import threading
import sys
import os
import queue


class ZmqServerThread(threading.Thread):
    _port = 27132
    clients_addr = set()

    def __init__(self, server_port: int = None) -> None:
        threading.Thread.__init__(self)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.bondClient = None
        self._sentTimeStamp: int = None
        # 新增接收队列和最后消息缓存
        self.recv_queue = queue.Queue()
        self._last_received = {
            "message": "",
            "timestamp": -1,
        }  # 第一个为message，第二个为timestamp
        self.msgQueue: queue.Queue = queue.Queue()

        if server_port is not None:
            self.port = server_port

        print("Start hosting at port:{port}".format(port=self._port))
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
    def messageTimeStamp(self) -> int:
        return self._last_received["timestamp"]

    @property
    def receivedMessage(self) -> str:
        try:
            msg = self.recv_queue.get_nowait()

            self._last_received["message"] = msg["message"]
            self._last_received["timestamp"] = msg["timestamp"]
        except queue.Empty:
            pass
        return self._last_received["message"]

    @property
    def sentTimeStamp(self) -> int:
        if self._sentTimeStamp == None:
            return -1
        else:
            return self._sentTimeStamp

    @sentTimeStamp.setter
    def sentTimeStamp(self, value: int):
        self._sentTimeStamp = value

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
            timestamp = int(round(time.time() * 1000))
            if contents_str.endswith("is online") or ("door_closed" in contents_str):
                print(
                    "(skipped message) Client:[%s] message:%s Timestamp:%s\n"
                    % (address_str, contents_str, str(timestamp))
                )
                continue
            self.recv_queue.put({"message": contents_str, "timestamp": timestamp})
            print(
                "Client:[%s] message:%s Timestamp:%s\n"
                % (address_str, contents_str, str(timestamp))
            )

    def listen_queue(self):
        while True:
            if (not self.msgQueue.empty()) and (
                (int(round(time.time() * 1000)) - self.sentTimeStamp) > 800
            ):
                self.sentTimeStamp = int(round(time.time() * 1000))
                self.__send_string(self.bondClient, self.msgQueue.get())

    def send_string(self, address: str, msg: str = ""):
        self.msgQueue.put(msg)

    def __send_string(self, address: str, msg: str = ""):
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
