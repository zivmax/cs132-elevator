import time
from typing import List

from .net_client import ZmqClientThread
from .elevator import Elevator
from .engine import Engine
from .dispatcher import Dispatcher


class World:
    def __init__(self) -> None:
        self.client: ZmqClientThread = ZmqClientThread(identity="Team17")
        self.engine: Engine = Engine(self)  # Create engine first
        self.elevators: List[Elevator] = [Elevator(1, self), Elevator(2, self)]
        self.dispatcher: Dispatcher = Dispatcher(self)

        time.sleep(1)  # Give time for the client to connect

    def update(self) -> None:
        # Update components in the correct order
        self.dispatcher.update()  # Process user requests
        self.engine.update()  # Process movement

        # Update elevators last
        for elevator in self.elevators:
            elevator.update()

    def send_message(self, message: str) -> None:
        self.client.sendMsg(message)

    def run(self) -> None:
        try:
            while True:
                self.update()
                time.sleep(0.01)  # 10ms Fupdate interval
        except KeyboardInterrupt:
            print("Elevator simulation terminated.")
