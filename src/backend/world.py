import time
from typing import List, TYPE_CHECKING, Optional  # Added Optional
from .elevator import Elevator
from .engine import Engine
from .dispatcher import Dispatcher
from .net_client import ZmqCoordinator  # Import ZmqCoordinator

if TYPE_CHECKING:
    from .api import ElevatorAPI  # Keep for type hinting


class World:
    def __init__(self, zmq_port: str = "19982") -> None:  # Added zmq_port parameter
        # Create ZmqCoordinator, which owns ZmqClientThread and the incoming message queue.
        # ZmqCoordinator handles ZMQ client prints.
        self.zmq_coordinator: ZmqCoordinator = ZmqCoordinator(identity="Team17", zmq_port=zmq_port)

        # API, Elevators, and Dispatcher will be initialized via set_api_and_initialize_components
        self.api: Optional["ElevatorAPI"] = None
        self.engine: Engine = Engine(self)  # Engine might not need API directly at init
        self.elevators: List[Elevator] = []
        self.dispatcher: Optional[Dispatcher] = None

        # Message queue and its management methods (add_msg, get_next_msg, has_msg) are now in ZmqCoordinator.
        print(f"World: Initialized with ZMQ port {zmq_port}. API and components to be set later.")

    def set_api_and_initialize_components(self, api: "ElevatorAPI") -> None:
        """Sets the ElevatorAPI instance and initializes components that depend on it."""
        self.api = api
        if self.api is None:  # Should not happen if logic is correct
            raise ValueError("API instance cannot be None when initializing components")

        self.elevators = [
            Elevator(1, self, self.api),
            Elevator(2, self, self.api),
        ]
        self.dispatcher = Dispatcher(self, self.api)
        print("World: ElevatorAPI set and dependent components initialized.")

    def update(self) -> None:
        # Tell ZmqCoordinator to poll ZMQ and queue any new messages internally.
        if self.zmq_coordinator:
            self.zmq_coordinator.poll_and_queue_incoming_messages()

        # The loop for processing messages from ZmqCoordinator's queue is in main.py.

        # Update simulation components.
        self.engine.update()
        for elevator in self.elevators:
            elevator.update()
