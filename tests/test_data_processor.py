"""Tests for data processor."""

import pytest
from datetime import date

from src.services.data_processor import DataProcessor, TrainingMetrics, WellnessMetrics


@pytest.fixture
def processor():
    """Create test processor."""
    return DataProcessor()


class TestTrainingMetrics:
    """Tests for TrainingMetrics dataclass."""

    def test_form_status_very_fatigued(self):
        """Test very fatigued status."""
        metrics = TrainingMetrics(ctl=80, atl=105, tsb=-25)
        assert metrics.form_status == "Very Fatigued"

    def test_form_status_tired(self):
        """Test tired status."""
        metrics = TrainingMetrics(ctl=70, atl=85, tsb=-15)
        assert metrics.form_status == "Tired"

    def test_form_status_neutral(self):
        """Test neutral status."""
        metrics = TrainingMetrics(ctl=65, atl=70, tsb=-5)
        assert metrics.form_status == "Neutral"

    def test_form_status_fresh(self):
        """Test fresh status."""
        metrics = TrainingMetrics(ctl=60, atl=55, tsb=5)
        assert metrics.form_status == "Fresh"

    def test_form_status_very_fresh(self):
        """Test very fresh status."""
        metrics = TrainingMetrics(ctl=50, atl=35, tsb=15)
        assert metrics.form_status == "Very Fresh"


class TestDataProcessor:
    """Tests for DataProcessor class."""

    def test_calculate_metrics_empty(self, processor):
        """Test with empty activities."""
        metrics = processor.calculate_training_metrics([])

        assert metrics.ctl == 0
        assert metrics.atl == 0
        assert metrics.tsb == 0

    def test_calculate_metrics_with_icu_values(self, processor):
        """Test using pre-calculated Intervals.icu values."""
        activities = [
            {
                "id": 1,
                "start_date_local": "2024-12-15",
                "icu_ctl": 65.5,
                "icu_atl": 72.3,
            },
            {
                "id": 2,
                "start_date_local": "2024-12-14",
                "icu_ctl": 64.0,
                "icu_atl": 70.0,
            },
        ]

        metrics = processor.calculate_training_metrics(activities)

        assert metrics.ctl == 65.5
        assert metrics.atl == 72.3
        assert metrics.tsb == pytest.approx(-6.8, abs=0.1)

    def test_analyze_wellness_empty(self, processor):
        """Test with empty wellness data."""
        result = processor.analyze_wellness([])

        assert result.hrv is None
        assert result.rhr is None
        assert result.sleep_hours is None
        assert result.readiness == "Unknown"

    def test_analyze_wellness_with_data(self, processor):
        """Test wellness analysis."""
        wellness = [
            {
                "id": "2024-12-15",
                "hrv": 55,
                "restingHR": 52,
                "sleepSecs": 28800,  # 8 hours
                "soreness": 2,
                "fatigue": 2,
            },
        ]

        result = processor.analyze_wellness(wellness)

        assert result.hrv == 55
        assert result.rhr == 52
        assert result.sleep_hours == 8.0
        assert "Good" in result.readiness

    def test_check_existing_workout_found(self, processor):
        """Test finding existing workout."""
        events = [
            {
                "id": 123,
                "start_date_local": "2024-12-15T00:00:00",
                "category": "WORKOUT",
                "name": "Morning Ride",
            },
            {
                "id": 124,
                "start_date_local": "2024-12-16T00:00:00",
                "category": "WORKOUT",
                "name": "Evening Ride",
            },
        ]

        result = processor.check_existing_workout(events, date(2024, 12, 15))

        assert result is not None
        assert result["id"] == 123

    def test_check_existing_workout_not_found(self, processor):
        """Test when no workout exists."""
        events = [
            {
                "id": 123,
                "start_date_local": "2024-12-14T00:00:00",
                "category": "WORKOUT",
                "name": "Morning Ride",
            },
        ]

        result = processor.check_existing_workout(events, date(2024, 12, 15))

        assert result is None
