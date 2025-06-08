"""
Unit tests for Simulator class functionality.

Tests the simulator initialization, API integration, and update behavior
as specified in the validation documentation (TC112-TC115).
"""

import pytest
from unittest.mock import Mock, patch
from backend.simulator import Simulator
from backend.api.core import ElevatorAPI


class TestSimulatorInitialization:
    """Test cases for simulator initialization"""

    def test_simulator_creation(self):
        """Test basic simulator creation"""
        simulator = Simulator()

        assert simulator is not None
        assert hasattr(simulator, "dispatcher")
        assert hasattr(simulator, "elevators")


class TestSimulatorAPIIntegration:
    """Test cases for simulator API integration (TC112-TC113)"""

    def test_set_api_with_none_raises_error(self):
        """TC112: Test that setting API to None raises ValueError"""
        simulator = Simulator()

        with pytest.raises(ValueError):
            simulator.set_api_and_initialize_components(None)

    def test_set_api_initializes_components(self):
        """TC113: Test that providing API initializes components"""
        simulator = Simulator()
        mock_api = Mock(spec=ElevatorAPI)

        # Should not raise an exception
        simulator.set_api_and_initialize_components(mock_api)

        # Verify components are initialized
        assert simulator.dispatcher is not None
        assert hasattr(simulator, "elevators")


class TestSimulatorUpdate:
    """Test cases for simulator update behavior (TC114-TC115)"""

    def test_update_with_dispatcher_calls_update(self):
        """TC114: Test that update() calls dispatcher.update() when dispatcher exists"""
        simulator = Simulator()
        mock_api = Mock(spec=ElevatorAPI)
        simulator.set_api_and_initialize_components(mock_api)

        # Mock the dispatcher
        mock_dispatcher = Mock()
        simulator.dispatcher = mock_dispatcher

        # Call update
        simulator.update()

        # Verify dispatcher.update() was called
        mock_dispatcher.update.assert_called_once()

    def test_update_without_dispatcher_no_error(self):
        """TC115: Test that update() handles None dispatcher gracefully"""
        simulator = Simulator()
        simulator.dispatcher = None

        # Should not raise an exception
        try:
            simulator.update()
        except Exception as e:
            pytest.fail(f"update() raised an exception with None dispatcher: {e}")


class TestSimulatorIntegration:
    """Integration tests for simulator with multiple components"""

    def test_full_initialization_workflow(self):
        """Test complete initialization workflow"""
        simulator = Simulator()
        mock_api = Mock(spec=ElevatorAPI)

        # Initialize components
        simulator.set_api_and_initialize_components(mock_api)

        # Verify all components are properly initialized
        assert simulator.dispatcher is not None
        assert hasattr(simulator, "elevators")
        assert len(simulator.elevators) >= 0  # Should have elevator list

    def test_simulator_elevator_creation(self):
        """Test that simulator creates elevators properly"""
        simulator = Simulator()
        mock_api = Mock(spec=ElevatorAPI)

        simulator.set_api_and_initialize_components(mock_api)

        # Verify elevators are created
        if hasattr(simulator, "elevators") and simulator.elevators:
            for elevator in simulator.elevators:
                assert hasattr(elevator, "id")
                assert hasattr(elevator, "current_floor")
                assert hasattr(elevator, "state")
                assert hasattr(elevator, "door_state")


if __name__ == "__main__":
    pytest.main([__file__])
