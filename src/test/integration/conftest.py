"""
Integration test fixtures and utilities.
Provides shared fixtures for testing component interactions.
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

# Import backend modules for integration testing
from backend.models import (
    ElevatorState,
    DoorState,
    MoveDirection,
    Task,
    Call,
    CallState,
    MIN_FLOOR,
    MAX_FLOOR,
)
from backend.elevator import Elevator
from backend.dispatcher import Dispatcher
from backend.simulator import Simulator
from backend.api.core import ElevatorAPI


@pytest.fixture
def mock_zmq_client():
    """Mock ZMQ client for testing external communication"""
    client = Mock()
    client.send_message = Mock()
    client.start = Mock()
    client.stop = Mock()
    client.is_connected = Mock(return_value=True)
    return client


@pytest.fixture
def mock_websocket_bridge():
    """Mock WebSocket bridge for testing frontend communication"""
    bridge = Mock()
    bridge.send_message = Mock()
    bridge.broadcast_state = Mock()
    bridge.is_connected = Mock(return_value=True)
    return bridge


@pytest.fixture
def integration_api(mock_zmq_client):
    """Integration test API instance with mocked dependencies"""
    api = ElevatorAPI(world=None)  # Pass None initially
    # Mock the ZMQ client to avoid actual network operations
    api.zmq_client = mock_zmq_client
    return api


@pytest.fixture
def test_world(integration_api):
    """World/Simulator instance for integration testing"""
    world = Simulator()
    world.set_api_and_initialize_components(integration_api)
    return world


@pytest.fixture
def dual_elevator_system(test_world, integration_api):
    """Complete dual elevator system for integration testing"""
    # Create two elevators
    elevator1 = Elevator(
        elevator_id=1,
        world=test_world,
        api=integration_api
    )
    elevator2 = Elevator(
        elevator_id=2, 
        world=test_world,
        api=integration_api
    )

    test_world.elevators = [elevator1, elevator2]

    # Create dispatcher
    dispatcher = Dispatcher(test_world, integration_api)
    test_world.dispatcher = dispatcher

    # Link API to world
    integration_api.world = test_world

    return {
        "world": test_world,
        "api": integration_api,
        "dispatcher": dispatcher,
        "elevators": [elevator1, elevator2],
    }


@pytest.fixture
def system_state_monitor():
    """Monitor for tracking system state changes during tests"""
    monitor = {"states": [], "messages": [], "timing": []}

    def record_state(component, state, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        monitor["states"].append(
            {"component": component, "state": state, "timestamp": timestamp}
        )

    def record_message(source, destination, message, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        monitor["messages"].append(
            {
                "source": source,
                "destination": destination,
                "message": message,
                "timestamp": timestamp,
            }
        )

    monitor["record_state"] = record_state
    monitor["record_message"] = record_message

    return monitor


@pytest.fixture
def integration_test_timeout():
    """Standard timeout for integration tests"""
    return 15.0  # 15 seconds should be enough for most integration scenarios


@pytest.fixture
def wait_for_condition():
    """Utility function to wait for specific conditions with timeout"""

    def _wait_for_condition(condition_func, timeout=10.0, check_interval=0.1):
        """
        Wait for condition_func to return True within timeout

        Args:
            condition_func: Callable that returns True when condition is met
            timeout: Maximum time to wait in seconds
            check_interval: How often to check the condition

        Returns:
            bool: True if condition was met, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(check_interval)
        return False

    return _wait_for_condition


@pytest.fixture
def simulate_time():
    """Utility to simulate time passing for elevator operations"""

    def _simulate_time(system, duration, update_interval=0.1):
        """
        Simulate time passing by repeatedly calling system updates

        Args:
            system: System with elevators and dispatcher to update
            duration: Total time to simulate in seconds
            update_interval: How often to call update methods
        """
        steps = int(duration / update_interval)
        for _ in range(steps):
            # Update all elevators
            for elevator in system["elevators"]:
                elevator.update()

            # Update dispatcher
            if system["dispatcher"]:
                system["dispatcher"].update()

            time.sleep(update_interval)

    return _simulate_time


@pytest.fixture
def message_collector(mock_zmq_client, mock_websocket_bridge):
    """Collect all messages sent during test execution"""
    messages = {"zmq": [], "websocket": []}

    def zmq_send_side_effect(message):
        messages["zmq"].append(message)
        return True

    def websocket_send_side_effect(message):
        messages["websocket"].append(message)
        return True

    mock_zmq_client.send_message.side_effect = zmq_send_side_effect
    mock_websocket_bridge.send_message.side_effect = websocket_send_side_effect

    return messages


class SystemTestHarness:
    """Test harness for complex multi-component integration scenarios"""

    def __init__(self, system, monitor, wait_for_condition):
        self.system = system
        self.monitor = monitor
        self.wait_for_condition = wait_for_condition
        self.start_time = time.time()

    def send_call(self, floor: int, direction: str, expected_elevator_id=None):
        """Send a call and optionally verify which elevator responds"""
        self.system["api"]._handle_call_elevator(floor, direction)
        self.monitor["record_message"]("test", "api", f"call_{direction}@{floor}")

        if expected_elevator_id:
            # Wait for assignment
            def call_assigned():
                for call in self.system["dispatcher"].pending_calls.values():
                    if call.floor == floor and call.is_assigned():
                        return call.assigned_elevator == expected_elevator_id - 1
                return False

            return self.wait_for_condition(call_assigned, timeout=5.0)
        return True

    def select_floor(self, elevator_id: int, floor: int):
        """Select a floor from inside an elevator"""
        result = self.system["api"]._handle_select_floor(floor, elevator_id)
        self.monitor["record_message"](
            "test", "api", f"select_floor@{floor}#{elevator_id}"
        )
        return result

    def open_door(self, elevator_id: int):
        """Open elevator door manually"""
        result = self.system["api"]._handle_open_door(elevator_id)
        self.monitor["record_message"]("test", "api", f"open_door#{elevator_id}")
        return result

    def close_door(self, elevator_id: int):
        """Close elevator door manually"""
        result = self.system["api"]._handle_close_door(elevator_id)
        self.monitor["record_message"]("test", "api", f"close_door#{elevator_id}")
        return result

    def reset_system(self):
        """Reset the entire system"""
        # Implementation would depend on actual reset mechanism
        for elevator in self.system["elevators"]:
            elevator.current_floor = 1
            elevator.state = ElevatorState.IDLE
            elevator.door_state = DoorState.CLOSED
            elevator.task_queue.clear()

        self.system["dispatcher"].pending_calls.clear()
        self.monitor["record_message"]("test", "api", "reset")

    def wait_for_elevator_at_floor(self, elevator_id: int, floor: int, timeout=10.0):
        """Wait for specific elevator to reach specific floor"""

        def at_floor():
            return self.system["elevators"][elevator_id - 1].current_floor == floor

        return self.wait_for_condition(at_floor, timeout)

    def wait_for_door_state(self, elevator_id: int, door_state: DoorState, timeout=5.0):
        """Wait for elevator door to reach specific state"""

        def door_ready():
            return self.system["elevators"][elevator_id - 1].door_state == door_state

        return self.wait_for_condition(door_ready, timeout)

    def get_elevator_state(self, elevator_id: int):
        """Get current state of specific elevator"""
        elevator = self.system["elevators"][elevator_id - 1]
        return {
            "id": elevator_id,
            "floor": elevator.current_floor,
            "state": elevator.state,
            "door_state": elevator.door_state,
            "task_queue": list(elevator.task_queue),
            "direction": getattr(elevator, "direction", None),
        }

    def get_system_state(self):
        """Get complete system state snapshot"""
        return {
            "elevators": [
                self.get_elevator_state(i)
                for i in range(1, len(self.system["elevators"]) + 1)
            ],
            "pending_calls": len(self.system["dispatcher"].pending_calls),
            "elapsed_time": time.time() - self.start_time,
        }


@pytest.fixture
def system_harness(dual_elevator_system, system_state_monitor, wait_for_condition):
    """Complete system test harness"""
    return SystemTestHarness(
        dual_elevator_system, system_state_monitor, wait_for_condition
    )
