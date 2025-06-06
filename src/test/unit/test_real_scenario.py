#!/usr/bin/env python3
"""
Unit test to reproduce the exact scenario from the user's logs.
This simulates the specific sequence that caused the issue in production logs.
"""
import sys
import os
import time
import pytest

# Add the src/backend directory to the path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "src", "backend")
)

from backend.simulator import Simulator
from backend.api.core import ElevatorAPI
from backend.models import MoveDirection


def test_real_scenario():
    """Test the exact scenario from the logs."""
    # Create the simulator and components
    simulator = Simulator("19982")
    api = ElevatorAPI(simulator, simulator.zmq_coordinator)
    simulator.set_api_and_initialize_components(api)

    # 1. Passenger A calls UP at floor 1
    api.ui_call_elevator({"floor": 1, "direction": "up"})
    # Passenger A selects floor 3 in elevator 1
    api.ui_select_floor({"floor": 3, "elevatorId": 1})

    # 2. Passenger B calls UP at floor 2
    api.ui_call_elevator({"floor": 2, "direction": "up"})
    # Passenger B selects floor 3 in elevator 2
    api.ui_select_floor({"floor": 3, "elevatorId": 2})

    # 3. Passenger C calls DOWN at floor 2 (problematic call)
    api.ui_call_elevator({"floor": 2, "direction": "down"})

    # Verify the DOWN call is still pending (deferred)
    down_calls = [
        call
        for call in simulator.dispatcher.pending_calls.values()
        if call.direction == MoveDirection.DOWN and call.floor == 2
    ]
    assert (
        len(down_calls) == 1
    ), "DOWN call at floor 2 should be deferred but was assigned"

    # Clean up ZMQ threads
    simulator.zmq_coordinator.stop()
