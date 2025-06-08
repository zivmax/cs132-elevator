"""
Shared fixtures and utilities for unit tests.
This file provides common test fixtures, mock objects, and utilities
that are used across multiple test modules.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock
from typing import List

# Import all backend modules for testing
from backend.models import (
    ElevatorState,
    DoorState,
    MoveDirection,
    Task,
    Call,
    CallState,
    MIN_FLOOR,
    MAX_FLOOR,
    MIN_ELEVATOR_ID,
    MAX_ELEVATOR_ID,
)
from backend.elevator import Elevator
from backend.dispatcher import Dispatcher
from backend.simulator import Simulator
from backend.api.core import ElevatorAPI


@pytest.fixture
def mock_world():
    """Mock world/simulator fixture"""
    world = Mock(spec=Simulator)
    world.elevators = []
    world.dispatcher = None
    return world


@pytest.fixture
def mock_api():
    """Mock ElevatorAPI fixture"""
    api = Mock(spec=ElevatorAPI)
    api.world = None
    return api


@pytest.fixture  
def api_without_zmq():
    """ElevatorAPI instance without ZMQ for unit testing"""
    # Create a mock ZMQ client to avoid actual network connections
    from unittest.mock import patch
    
    with patch('backend.api.core.ZmqClientThread') as mock_zmq:
        mock_client = Mock()
        mock_client.connect_and_start = Mock()
        mock_client.stop = Mock()
        mock_client.is_alive = Mock(return_value=False)
        mock_zmq.return_value = mock_client
        
        api = ElevatorAPI(world=None)
        api.zmq_client = mock_client
        yield api


@pytest.fixture
def mock_elevator():
    """Real elevator fixture with mock dependencies for testing"""
    # Create mock dependencies
    mock_world = Mock(spec=Simulator)
    mock_api = Mock(spec=ElevatorAPI)

    # Setup mock dispatcher
    mock_dispatcher = Mock()
    mock_dispatcher.get_call_direction.return_value = MoveDirection.UP
    mock_dispatcher.complete_call.return_value = None
    mock_world.dispatcher = mock_dispatcher

    # Setup mock API methods
    mock_api.send_door_opened_message = Mock()
    mock_api.send_door_closed_message = Mock()
    mock_api.send_floor_arrived_message = Mock()

    # Create real elevator instance with mock dependencies
    elevator = Elevator(1, mock_world, mock_api)

    return elevator


@pytest.fixture
def real_elevator(mock_world, mock_api):
    """Real elevator instance for integration tests"""
    return Elevator(1, mock_world, mock_api)


@pytest.fixture
def mock_elevator_pair(mock_world):
    """Fixture providing two mock elevators"""
    elevator1 = Mock(spec=Elevator)
    elevator1.id = 1
    elevator1.current_floor = 1
    elevator1.door_state = DoorState.CLOSED
    elevator1.state = ElevatorState.IDLE
    elevator1.task_queue = []
    elevator1.calculate_estimated_time.return_value = 5.0

    elevator2 = Mock(spec=Elevator)
    elevator2.id = 2
    elevator2.current_floor = 3
    elevator2.door_state = DoorState.CLOSED
    elevator2.state = ElevatorState.IDLE
    elevator2.task_queue = []
    elevator2.calculate_estimated_time.return_value = 3.0

    mock_world.elevators = [elevator1, elevator2]
    return elevator1, elevator2


@pytest.fixture
def dispatcher(mock_world, mock_api):
    """Real dispatcher instance"""
    return Dispatcher(mock_world, mock_api)


@pytest.fixture
def elevator_api():
    """Real ElevatorAPI instance with proper cleanup"""
    api = ElevatorAPI(world=None)
    yield api
    # Cleanup ZMQ thread to prevent hanging
    if hasattr(api, 'zmq_client') and api.zmq_client:
        api.zmq_client.stop()
        if api.zmq_client.is_alive():
            api.zmq_client.join(timeout=1.0)  # Wait up to 1 second for thread to stop


@pytest.fixture
def sample_task():
    """Sample task fixture"""
    return Task(floor=3, call_id="test_call_123")


@pytest.fixture
def sample_call():
    """Sample call fixture"""
    return Call(floor=2, direction=MoveDirection.UP, call_id="call_456")


@pytest.fixture
def time_mock():
    """Time mock fixture"""
    with pytest.MonkeyPatch().context() as m:
        mock_time = Mock()
        mock_time.return_value = 100.0
        m.setattr(time, "time", mock_time)
        yield mock_time


# Test data constants
class TestConstants:
    """Constants for testing"""

    VALID_FLOORS = [MIN_FLOOR, 1, 2, 3, MAX_FLOOR]
    INVALID_FLOORS = [MIN_FLOOR - 1, MAX_FLOOR + 1, 0]
    VALID_ELEVATOR_IDS = [MIN_ELEVATOR_ID, MAX_ELEVATOR_ID]
    INVALID_ELEVATOR_IDS = [MIN_ELEVATOR_ID - 1, MAX_ELEVATOR_ID + 1, 0, 3]
    VALID_DIRECTIONS = ["up", "down", "UP", "DOWN"]
    INVALID_DIRECTIONS = ["invalid", "", "left", "right", "stop"]


# Helper functions
def create_test_elevator(
    elevator_id: int = 1,
    floor: int = 1,
    state: ElevatorState = ElevatorState.IDLE,
    door_state: DoorState = DoorState.CLOSED,
    world=None,
    api=None,
) -> Elevator:
    """Helper function to create test elevator with specific properties"""
    if world is None:
        world = Mock()
    if api is None:
        api = Mock()

    elevator = Elevator(elevator_id, world, api)
    elevator.current_floor = floor
    elevator.state = state
    elevator.door_state = door_state
    return elevator


def create_test_task(floor: int, call_id: str = None) -> Task:
    """Helper function to create test task"""
    return Task(floor=floor, call_id=call_id)


def assert_state_transition(
    elevator, expected_state: ElevatorState, expected_door_state: DoorState = None
):
    """Helper function to assert elevator state transitions"""
    assert elevator.state == expected_state
    if expected_door_state is not None:
        assert elevator.door_state == expected_door_state


def setup_moving_elevator(elevator, target_floor: int, direction: MoveDirection):
    """Helper function to setup elevator in moving state"""
    elevator.task_queue = [Task(floor=target_floor)]
    elevator.direction = direction
    if direction == MoveDirection.UP:
        elevator.state = ElevatorState.MOVING_UP
    else:
        elevator.state = ElevatorState.MOVING_DOWN
    elevator.moving_since = time.time()
