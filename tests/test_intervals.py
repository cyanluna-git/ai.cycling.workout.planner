"""Tests for Intervals.icu API client."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date

from src.clients.intervals import IntervalsClient, IntervalsAPIError
from src.config import IntervalsConfig


@pytest.fixture
def config():
    """Create test configuration."""
    return IntervalsConfig(
        api_key="test_api_key",
        athlete_id="i12345",
        base_url="https://intervals.icu/api/v1",
    )


@pytest.fixture
def client(config):
    """Create test client."""
    return IntervalsClient(config)


class TestIntervalsClient:
    """Tests for IntervalsClient class."""

    def test_init(self, client, config):
        """Test client initialization."""
        assert client.config == config
        assert client.base_url == "https://intervals.icu/api/v1"

    def test_format_date_string(self, client):
        """Test date formatting with string input."""
        result = client._format_date("2024-12-15")
        assert result == "2024-12-15"

    def test_format_date_object(self, client):
        """Test date formatting with date object."""
        d = date(2024, 12, 15)
        result = client._format_date(d)
        assert result == "2024-12-15"

    @patch("src.clients.intervals.requests.Session")
    def test_get_activities(self, mock_session_class, config):
        """Test getting activities."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "name": "Morning Ride", "icu_training_load": 75},
            {"id": 2, "name": "Evening Ride", "icu_training_load": 50},
        ]
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = IntervalsClient(config)
        client.session = mock_session

        activities = client.get_activities("2024-12-01", "2024-12-15")

        assert len(activities) == 2
        assert activities[0]["name"] == "Morning Ride"

    @patch("src.clients.intervals.requests.Session")
    def test_get_wellness(self, mock_session_class, config):
        """Test getting wellness data."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "2024-12-15", "hrv": 55, "restingHR": 52, "sleepSecs": 28800},
        ]
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = IntervalsClient(config)
        client.session = mock_session

        wellness = client.get_wellness("2024-12-08", "2024-12-15")

        assert len(wellness) == 1
        assert wellness[0]["hrv"] == 55

    @patch("src.clients.intervals.requests.Session")
    def test_create_workout(self, mock_session_class, config):
        """Test creating a workout."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123,
            "name": "AI Generated - VO2 Max",
            "category": "WORKOUT",
        }
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = IntervalsClient(config)
        client.session = mock_session

        result = client.create_workout(
            target_date="2024-12-15",
            name="AI Generated - VO2 Max",
            description="10m 50%\n5x 3m 115% 3m 50%\n10m 50%",
            moving_time=3600,
        )

        assert result["id"] == 123
        assert result["category"] == "WORKOUT"


class TestIntervalsAPIError:
    """Tests for IntervalsAPIError exception."""

    def test_error_with_status_code(self):
        """Test error with status code."""
        error = IntervalsAPIError("Not found", status_code=404)

        assert str(error) == "Not found"
        assert error.status_code == 404

    def test_error_with_response(self):
        """Test error with response data."""
        response = {"error": "Invalid request"}
        error = IntervalsAPIError("Bad request", status_code=400, response=response)

        assert error.response == response
