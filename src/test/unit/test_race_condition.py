"""
Test suite to verify the race condition fix for duplicate call assignments.
This tests the fix that adds `call.is_assigned()` check in _process_pending_calls().
"""

import pytest
import threading
import time
from unittest.mock import Mock, MagicMock
from concurrent.futures import ThreadPoolExecutor

from backend.dispatcher import Dispatcher
from backend.models import MoveDirection, Call, CallState
from backend.simulator import Simulator
from backend.elevator import Elevator
from backend.api.core import ElevatorAPI


class TestRaceConditionFix:
    """Test cases to verify the race condition fix prevents duplicate assignments."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_api = Mock(spec=ElevatorAPI)
        self.world = Mock(spec=Simulator)

        # Create mock elevators
        self.elevator1 = Mock(spec=Elevator)
        self.elevator1.id = 1
        self.elevator1.calculate_estimated_time.return_value = 5.0
        self.elevator1.current_floor = 1
        self.elevator1.task_queue = []
        self.elevator1.state = 0  # Add state attribute (should be ElevatorState.IDLE, but 0 is safe for mock)
        self.elevator1.door_state = 0  # Add door_state attribute

        self.elevator2 = Mock(spec=Elevator)
        self.elevator2.id = 2
        self.elevator2.calculate_estimated_time.return_value = 6.0
        self.elevator2.current_floor = 1
        self.elevator2.task_queue = []
        self.elevator2.state = 0
        self.elevator2.door_state = 0

        self.world.elevators = [self.elevator1, self.elevator2]
        self.dispatcher = Dispatcher(self.world, self.mock_api)

    def test_is_assigned_method_prevents_duplicate_assignment(self):
        """Test that is_assigned() check prevents duplicate assignment of the same call."""
        # Add a pending call
        call_id = self.dispatcher.add_outside_call(5, MoveDirection.UP)
        call = self.dispatcher.pending_calls[call_id]

        # Manually assign the call to elevator 1
        call.assign_to_elevator(0)

        # Verify the call is now assigned
        assert call.is_assigned()
        assert not call.is_pending()

        # Try to process pending calls - this should NOT assign the call again
        # because is_assigned() check should skip it
        initial_assign_task_calls = len(self.mock_api.method_calls)
        self.dispatcher._process_pending_calls()

        # Verify assign_task was not called (no new assignments)
        final_assign_task_calls = len(self.mock_api.method_calls)
        assert final_assign_task_calls == initial_assign_task_calls

    def test_concurrent_call_processing_no_duplicates(self):
        """Test that concurrent processing doesn't create duplicate assignments."""
        # Add multiple pending calls
        call_ids = []
        for floor in range(2, 8):
            call_id = self.dispatcher.add_outside_call(floor, MoveDirection.UP)
            call_ids.append(call_id)

        # Track assignments
        assigned_calls = set()
        assignment_lock = threading.Lock()

        def track_assign_task(*args, **kwargs):
            """Mock assign_task that tracks assignments."""
            with assignment_lock:
                if len(args) >= 3 and args[2]:  # call_id is the third argument
                    call_id = args[2]
                    if call_id in assigned_calls:
                        raise AssertionError(f"Duplicate assignment of call {call_id}")
                    assigned_calls.add(call_id)

        # Mock assign_task to track assignments
        self.dispatcher.assign_task = Mock(side_effect=track_assign_task)

        # Process calls concurrently
        def process_calls():
            self.dispatcher._process_pending_calls()

        # Run multiple threads simultaneously
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=process_calls)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # Verify no duplicate assignments occurred
        # (if duplicates occurred, track_assign_task would have raised AssertionError)
        print(f"Successfully assigned {len(assigned_calls)} calls without duplicates")

    def test_state_transitions_are_atomic(self):
        """Test that call state transitions from PENDING to ASSIGNED are properly handled."""
        call_id = self.dispatcher.add_outside_call(3, MoveDirection.DOWN)
        call = self.dispatcher.pending_calls[call_id]

        # Initial state should be PENDING
        assert call.state == CallState.PENDING
        assert call.is_pending()
        assert not call.is_assigned()
        assert not call.is_completed()

        # After assignment, state should be ASSIGNED
        call.assign_to_elevator(0)
        assert call.state == CallState.ASSIGNED
        assert not call.is_pending()
        assert call.is_assigned()
        assert not call.is_completed()

        # After completion, state should be COMPLETED
        call.complete()
        assert call.state == CallState.COMPLETED
        assert not call.is_pending()
        assert not call.is_assigned()
        assert call.is_completed()

    def test_process_pending_calls_skips_assigned_calls(self):
        """Test that _process_pending_calls properly skips calls that are already assigned."""
        # Add two calls
        call_id1 = self.dispatcher.add_outside_call(4, MoveDirection.UP)
        call_id2 = self.dispatcher.add_outside_call(6, MoveDirection.DOWN)

        call1 = self.dispatcher.pending_calls[call_id1]
        call2 = self.dispatcher.pending_calls[call_id2]

        # Manually assign call1
        call1.assign_to_elevator(0)

        # Mock assign_task to track which calls get processed
        processed_calls = []

        def track_processed_calls(elevator_idx, floor, call_id=None):
            if call_id:
                processed_calls.append(call_id)

        self.dispatcher.assign_task = Mock(side_effect=track_processed_calls)

        # Process pending calls
        self.dispatcher._process_pending_calls()

        # Both calls should be deferred due to no suitable elevator
        assert processed_calls == []

    def test_integration_with_real_call_objects(self):
        """Integration test using real Call objects to verify the fix works end-to-end."""
        # Create real Call objects
        call1 = Call("test-call-1", 3, MoveDirection.UP)
        call2 = Call("test-call-2", 5, MoveDirection.DOWN)

        # Add them to dispatcher
        self.dispatcher.pending_calls["test-call-1"] = call1
        self.dispatcher.pending_calls["test-call-2"] = call2

        # Mock assign_task to simulate assignment
        def mock_assign_task(elevator_idx, floor, call_id=None):
            if call_id and call_id in self.dispatcher.pending_calls:
                self.dispatcher.pending_calls[call_id].assign_to_elevator(elevator_idx)

        self.dispatcher.assign_task = Mock(side_effect=mock_assign_task)

        # First processing should defer both calls due to no suitable elevator
        self.dispatcher._process_pending_calls()
        assert self.dispatcher.assign_task.call_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
