"""
Unit tests for validation functions in models.py

Tests the boundary validation functionality including floor bounds,
elevator ID validation, and direction validation.
"""

import pytest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from backend.models import (
    validate_floor,
    validate_elevator_id,
    validate_direction,
    MIN_FLOOR,
    MAX_FLOOR,
    MIN_ELEVATOR_ID,
    MAX_ELEVATOR_ID,
)


class TestFloorValidation:
    """Test cases for floor boundary validation"""

    def test_system_constants(self):
        """Test that system constants match UPPAAL model specifications"""
        assert MIN_FLOOR == -1, "MIN_FLOOR should match UPPAAL model"
        assert MAX_FLOOR == 3, "MAX_FLOOR should match UPPAAL model"
        assert MIN_ELEVATOR_ID == 1, "MIN_ELEVATOR_ID should be 1"
        assert MAX_ELEVATOR_ID == 2, "MAX_ELEVATOR_ID should be 2"

    def test_valid_floors(self):
        """Test that all valid floors pass validation"""
        valid_floors = [-1, 0, 1, 2, 3]
        for floor in valid_floors:
            assert validate_floor(floor), f"Floor {floor} should be valid"

    def test_invalid_floors_below_minimum(self):
        """Test that floors below minimum are rejected"""
        invalid_floors = [-2, -10, -100]
        for floor in invalid_floors:
            assert not validate_floor(
                floor
            ), f"Floor {floor} should be invalid (below minimum)"

    def test_invalid_floors_above_maximum(self):
        """Test that floors above maximum are rejected"""
        invalid_floors = [4, 10, 100]
        for floor in invalid_floors:
            assert not validate_floor(
                floor
            ), f"Floor {floor} should be invalid (above maximum)"

    def test_boundary_conditions(self):
        """Test exact boundary conditions"""
        # Test exact boundaries
        assert validate_floor(MIN_FLOOR), "MIN_FLOOR should be valid"
        assert validate_floor(MAX_FLOOR), "MAX_FLOOR should be valid"

        # Test just outside boundaries
        assert not validate_floor(
            MIN_FLOOR - 1
        ), "One below MIN_FLOOR should be invalid"
        assert not validate_floor(
            MAX_FLOOR + 1
        ), "One above MAX_FLOOR should be invalid"

    def test_floor_validation_type_handling(self):
        """Test that floor validation handles different input types appropriately"""
        # Test with float - Python allows int/float comparison, so 1.5 is valid if in range
        assert validate_floor(1.5), "Float 1.5 should be valid (within range)"
        assert not validate_floor(10.5), "Float 10.5 should be invalid (out of range)"

        # Test with string representation - should raise TypeError
        with pytest.raises(TypeError):
            validate_floor("1")

        with pytest.raises(TypeError):
            validate_floor(None)


class TestElevatorIdValidation:
    """Test cases for elevator ID validation"""

    def test_valid_elevator_ids(self):
        """Test that valid elevator IDs pass validation"""
        valid_ids = [1, 2]
        for elevator_id in valid_ids:
            assert validate_elevator_id(
                elevator_id
            ), f"Elevator ID {elevator_id} should be valid"

    def test_invalid_elevator_ids_below_minimum(self):
        """Test that elevator IDs below minimum are rejected"""
        invalid_ids = [0, -1, -10]
        for elevator_id in invalid_ids:
            assert not validate_elevator_id(
                elevator_id
            ), f"Elevator ID {elevator_id} should be invalid (below minimum)"

    def test_invalid_elevator_ids_above_maximum(self):
        """Test that elevator IDs above maximum are rejected"""
        invalid_ids = [3, 10, 100]
        for elevator_id in invalid_ids:
            assert not validate_elevator_id(
                elevator_id
            ), f"Elevator ID {elevator_id} should be invalid (above maximum)"

    def test_elevator_id_boundary_conditions(self):
        """Test exact boundary conditions for elevator IDs"""
        # Test exact boundaries
        assert validate_elevator_id(MIN_ELEVATOR_ID), "MIN_ELEVATOR_ID should be valid"
        assert validate_elevator_id(MAX_ELEVATOR_ID), "MAX_ELEVATOR_ID should be valid"

        # Test just outside boundaries
        assert not validate_elevator_id(
            MIN_ELEVATOR_ID - 1
        ), "One below MIN_ELEVATOR_ID should be invalid"
        assert not validate_elevator_id(
            MAX_ELEVATOR_ID + 1
        ), "One above MAX_ELEVATOR_ID should be invalid"


class TestDirectionValidation:
    """Test cases for direction validation"""

    def test_valid_directions(self):
        """Test that valid directions pass validation"""
        valid_directions = ["up", "down"]
        for direction in valid_directions:
            assert validate_direction(
                direction
            ), f"Direction '{direction}' should be valid"

    def test_invalid_directions(self):
        """Test that invalid directions are rejected"""
        invalid_directions = ["left", "right", "forward", "backward", "stop"]
        for direction in invalid_directions:
            assert not validate_direction(
                direction
            ), f"Direction '{direction}' should be invalid"

    def test_direction_case_sensitivity(self):
        """Test that direction validation is case-sensitive"""
        case_variants = ["UP", "Down", "Up", "DOWN", "uP", "dOwN"]
        for direction in case_variants:
            assert not validate_direction(
                direction
            ), f"Direction '{direction}' should be invalid (case sensitive)"

    def test_direction_empty_and_none(self):
        """Test handling of empty strings and None values"""
        assert not validate_direction(""), "Empty string should be invalid"
        assert not validate_direction(None), "None should be invalid"

    def test_direction_whitespace(self):
        """Test handling of whitespace in directions"""
        whitespace_variants = [" up", "up ", " up ", "u p", "up\n", "\tup"]
        for direction in whitespace_variants:
            assert not validate_direction(
                direction
            ), f"Direction '{repr(direction)}' with whitespace should be invalid"


class TestValidationIntegration:
    """Integration tests for validation functions"""

    def test_realistic_scenarios(self):
        """Test realistic usage scenarios"""
        # Valid call to floor 2 going up with elevator 1
        assert validate_floor(2)
        assert validate_direction("up")
        assert validate_elevator_id(1)

        # Valid call to basement (floor -1) going down with elevator 2
        assert validate_floor(-1)
        assert validate_direction("down")
        assert validate_elevator_id(2)

        # Invalid scenarios
        assert not validate_floor(5)  # Floor too high
        assert not validate_direction("sideways")  # Invalid direction
        assert not validate_elevator_id(0)  # Invalid elevator ID

    def test_manual_verification_scenario(self):
        """Test the exact scenario that was manually verified"""
        # This test matches the manual verification performed:
        # python -c "from src.backend.models import validate_floor; print(validate_floor(2), validate_floor(5))"

        # Valid floor within bounds
        result_valid = validate_floor(2)
        assert (
            result_valid == True
        ), "Floor 2 should be valid (within MIN_FLOOR=-1, MAX_FLOOR=3)"

        # Invalid floor outside bounds
        result_invalid = validate_floor(5)
        assert (
            result_invalid == False
        ), "Floor 5 should be invalid (exceeds MAX_FLOOR=3)"

        # Verify the exact output matches manual test: True False
        assert (result_valid, result_invalid) == (
            True,
            False,
        ), "Manual verification should return (True, False)"

    def test_edge_case_combinations(self):
        """Test edge cases that might occur in real usage"""
        # Test minimum and maximum values together
        assert validate_floor(MIN_FLOOR) and validate_elevator_id(MIN_ELEVATOR_ID)
        assert validate_floor(MAX_FLOOR) and validate_elevator_id(MAX_ELEVATOR_ID)

        # Test invalid combinations
        assert not (
            validate_floor(MIN_FLOOR - 1) and validate_elevator_id(MIN_ELEVATOR_ID)
        )
        assert not (
            validate_floor(MAX_FLOOR + 1) and validate_elevator_id(MAX_ELEVATOR_ID + 1)
        )


if __name__ == "__main__":
    # Allow running the test file directly
    pytest.main([__file__])
