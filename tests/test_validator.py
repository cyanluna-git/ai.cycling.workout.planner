"""Tests for workout validator."""

import pytest

from src.services.validator import WorkoutValidator, ValidationResult


@pytest.fixture
def validator():
    """Create test validator."""
    return WorkoutValidator(max_duration_minutes=90)


class TestWorkoutValidator:
    """Tests for WorkoutValidator class."""

    def test_validate_simple_workout(self, validator):
        """Test validating a simple workout."""
        workout_text = """
        10m 50%
        20m 75%
        10m 50%
        """

        result = validator.validate(workout_text)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_intervals(self, validator):
        """Test validating interval workout."""
        workout_text = """
        10m 50%
        5x 3m 115% 3m 50%
        10m 50%
        """

        result = validator.validate(workout_text)

        assert result.is_valid

    def test_validate_with_zones(self, validator):
        """Test validating workout with zones."""
        workout_text = """
        15m Z2
        30m Z3
        15m Z1
        """

        result = validator.validate(workout_text)

        assert result.is_valid

    def test_validate_empty_text(self, validator):
        """Test validating empty workout."""
        result = validator.validate("")

        assert not result.is_valid
        assert "empty" in result.errors[0].lower()

    def test_validate_invalid_format(self, validator):
        """Test validating invalid format."""
        workout_text = "Just ride for an hour"

        result = validator.validate(workout_text)

        assert not result.is_valid

    def test_validate_unsafe_power(self, validator):
        """Test warning for unsafe power levels."""
        # 10 minutes at 150% is not sustainable
        workout_text = "10m 150%"

        result = validator.validate(workout_text)

        # Should still be valid but with warning
        assert result.is_valid
        assert len(result.warnings) > 0

    def test_validate_with_bullets(self, validator):
        """Test cleaning bullet points."""
        workout_text = """
        - 10m 50%
        - 20m 75%
        - 10m 50%
        """

        result = validator.validate(workout_text)

        assert result.is_valid
        assert "10m 50%" in result.cleaned_text

    def test_parse_duration_seconds(self, validator):
        """Test parsing seconds."""
        result = validator._parse_duration("30", "s")
        assert result == 30

    def test_parse_duration_minutes(self, validator):
        """Test parsing minutes."""
        result = validator._parse_duration("10", "m")
        assert result == 600

    def test_parse_duration_hours(self, validator):
        """Test parsing hours."""
        result = validator._parse_duration("1", "h")
        assert result == 3600

    def test_check_power_limit_safe(self, validator):
        """Test power within safe limits."""
        # 3 minutes at 115% is safe
        result = validator._check_power_limit(180, 115)
        assert result is None

    def test_check_power_limit_unsafe(self, validator):
        """Test power exceeding safe limits."""
        # 5 minutes at 150% is not safe
        result = validator._check_power_limit(300, 150)
        assert result is not None
        assert "exceeds" in result.lower()


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_result(self):
        """Test valid result."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            cleaned_text="10m 50%",
        )

        assert result.is_valid
        assert result.cleaned_text == "10m 50%"

    def test_invalid_result(self):
        """Test invalid result."""
        result = ValidationResult(
            is_valid=False,
            errors=["Invalid format"],
            warnings=[],
            cleaned_text="",
        )

        assert not result.is_valid
        assert len(result.errors) == 1
