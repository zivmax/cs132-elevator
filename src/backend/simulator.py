import time
from typing import List, TYPE_CHECKING, Optional
from .elevator import Elevator
from .dispatcher import Dispatcher

# ZmqCoordinator is no longer initialized or used directly by Simulator
# from .api.zmq import ZmqCoordinator

if TYPE_CHECKING:
    from .api.core import ElevatorAPI


class Simulator:
    def __init__(self) -> None:
        self.api: Optional["ElevatorAPI"] = None
        self.elevators: List[Elevator] = []
        self.dispatcher: Optional[Dispatcher] = None
        print(
            "Simulator: Initialized. API and components to be set via set_api_and_initialize_components."
        )

    def set_api_and_initialize_components(self, api: "ElevatorAPI") -> None:
        """Sets the ElevatorAPI instance and initializes components that depend on it."""
        self.api = api
        if self.api is None:
            raise ValueError("API instance cannot be None when initializing components")

        # Pass the API instance to components that need it (e.g., for sending floor_arrived messages)
        self.elevators = [
            Elevator(1, self, self.api),  # Elevator needs API to send floor_arrived
            Elevator(2, self, self.api),  # Elevator needs API to send floor_arrived
        ]
        self.dispatcher = Dispatcher(
            self, self.api
        )  # Dispatcher might need API for logging or complex signals
        print("Simulator: ElevatorAPI set and dependent components initialized.")

    def update(self) -> None:
        # ZMQ message polling and processing is now handled by ZmqClientThread within ElevatorAPI.
        # No direct ZMQ polling call needed here.

        # Update simulation components.
        for elevator in self.elevators:
            elevator.update()

        if self.dispatcher:
            self.dispatcher.update()

    def stop(self) -> None:
        """Stops simulator components, including the ZMQ client via the API."""
        print("Simulator: Stopping...")
        self.api.stop()
        print("Simulator: Stopped.")
