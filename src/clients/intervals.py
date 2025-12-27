"""Intervals.icu API Client.

This module provides a Python client for interacting with the Intervals.icu API.
It handles authentication, rate limiting, and provides methods for common operations.
"""

import logging
import time
from datetime import date, datetime, timedelta
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import IntervalsConfig

logger = logging.getLogger(__name__)


class IntervalsAPIError(Exception):
    """Exception raised for Intervals.icu API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[dict] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class IntervalsClient:
    """Client for Intervals.icu API.

    This client handles authentication using Basic Auth and provides methods
    for fetching activities, wellness data, and creating workouts.

    Example:
        >>> from src.config import load_config
        >>> config = load_config()
        >>> client = IntervalsClient(config.intervals)
        >>> activities = client.get_activities(oldest="2024-01-01", newest="2024-01-31")
    """

    def __init__(self, config: IntervalsConfig):
        """Initialize the Intervals.icu client.

        Args:
            config: IntervalsConfig with api_key, athlete_id, and base_url.
        """
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic.

        Returns:
            Configured requests Session.
        """
        session = requests.Session()

        # Set up basic auth (username: "API_KEY", password: actual API key)
        session.auth = ("API_KEY", self.config.api_key)

        # Set default headers
        session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        # Configure retry strategy for rate limiting
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
            backoff_factor=1,  # 1s, 2s, 4s between retries
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> Any:
        """Make an API request with error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint path.
            params: Optional query parameters.
            json_data: Optional JSON body data.

        Returns:
            Parsed JSON response.

        Raises:
            IntervalsAPIError: If the API request fails.
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=30,
            )

            # Handle rate limiting with exponential backoff
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self._make_request(method, endpoint, params, json_data)

            response.raise_for_status()

            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return None

            return response.json()

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error: {e}"
            try:
                error_response = e.response.json() if e.response else None
            except Exception:
                error_response = None

            logger.error(f"API request failed: {error_msg}")
            raise IntervalsAPIError(
                error_msg,
                status_code=e.response.status_code if e.response else None,
                response=error_response,
            )
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {e}"
            logger.error(f"API request failed: {error_msg}")
            raise IntervalsAPIError(error_msg)

    def _format_date(self, d: date | str) -> str:
        """Format a date for API requests.

        Args:
            d: Date object or string in YYYY-MM-DD format.

        Returns:
            Date string in YYYY-MM-DD format.
        """
        if isinstance(d, date):
            return d.strftime("%Y-%m-%d")
        return d

    # ---------------------
    # Athlete Profile
    # ---------------------

    def get_athlete_profile(self) -> dict:
        """Fetch the athlete profile.

        Returns:
            Athlete profile data including FTP, weight, etc.
        """
        endpoint = f"/athlete/{self.config.athlete_id}"
        return self._make_request("GET", endpoint)

    # ---------------------
    # Activities
    # ---------------------

    def get_activities(
        self,
        oldest: date | str,
        newest: date | str,
    ) -> list[dict]:
        """Fetch activities within a date range.

        Args:
            oldest: Start date (inclusive).
            newest: End date (inclusive).

        Returns:
            List of activity objects.
        """
        endpoint = f"/athlete/{self.config.athlete_id}/activities"
        params = {
            "oldest": self._format_date(oldest),
            "newest": self._format_date(newest),
        }
        return self._make_request("GET", endpoint, params=params) or []

    def get_recent_activities(self, days: int = 42) -> list[dict]:
        """Get activities from the last N days.

        Args:
            days: Number of days to look back (default: 42 for 6 weeks).

        Returns:
            List of activity objects.
        """
        newest = date.today()
        oldest = newest - timedelta(days=days)
        return self.get_activities(oldest, newest)

    # ---------------------
    # Wellness
    # ---------------------

    def get_wellness(
        self,
        oldest: date | str,
        newest: date | str,
    ) -> list[dict]:
        """Fetch wellness data within a date range.

        Args:
            oldest: Start date (inclusive).
            newest: End date (inclusive).

        Returns:
            List of wellness objects with HRV, RHR, sleep data.
        """
        endpoint = f"/athlete/{self.config.athlete_id}/wellness"
        params = {
            "oldest": self._format_date(oldest),
            "newest": self._format_date(newest),
        }
        return self._make_request("GET", endpoint, params=params) or []

    def get_recent_wellness(self, days: int = 7) -> list[dict]:
        """Get wellness data from the last N days.

        Args:
            days: Number of days to look back (default: 7).

        Returns:
            List of wellness objects.
        """
        newest = date.today()
        oldest = newest - timedelta(days=days)
        return self.get_wellness(oldest, newest)

    # ---------------------
    # Events / Workouts
    # ---------------------

    def get_events(
        self,
        oldest: date | str,
        newest: date | str,
        calendar_id: Optional[int] = None,
    ) -> list[dict]:
        """Fetch calendar events within a date range.

        Args:
            oldest: Start date (inclusive).
            newest: End date (inclusive).
            calendar_id: Optional calendar ID to filter events.

        Returns:
            List of event objects.
        """
        endpoint = f"/athlete/{self.config.athlete_id}/events"
        params = {
            "oldest": self._format_date(oldest),
            "newest": self._format_date(newest),
        }
        if calendar_id is not None:
            params["calendar_id"] = calendar_id

        return self._make_request("GET", endpoint, params=params) or []

    def get_event(self, event_id: int) -> dict:
        """Fetch a single event by ID.

        Args:
            event_id: The event ID.

        Returns:
            Event object.
        """
        endpoint = f"/athlete/{self.config.athlete_id}/events/{event_id}"
        return self._make_request("GET", endpoint)

    def create_workout(
        self,
        target_date: date | str,
        name: str,
        description: str,
        moving_time: int,
        workout_type: str = "Ride",
        training_load: Optional[int] = None,
        steps: Optional[list] = None,
    ) -> dict:
        """Create a workout event on the calendar.

        The description should contain Intervals.icu workout text format
        for the workout to be parsed as a structured workout.

        Args:
            target_date: Date for the workout (YYYY-MM-DD).
            name: Workout name.
            description: Workout description including structured workout text.
            moving_time: Expected duration in seconds.
            workout_type: Activity type (default: "Ride").
            training_load: Optional planned TSS.
            steps: Optional list of structured steps (JSON). Preferable to description.

        Returns:
            Created event object.

        Example:
            >>> client.create_workout(
            ...     target_date="2024-12-15",
            ...     name="AI Generated - VO2 Max Intervals",
            ...     description="- 15m 50%\\n- 5x 3m 115% 3m 50%\\n- 15m 50%",
            ...     moving_time=3600,
            ... )
        """
        endpoint = f"/athlete/{self.config.athlete_id}/events"

        # Format date for API (must end with T00:00:00)
        date_str = self._format_date(target_date)

        payload = {
            "start_date_local": f"{date_str}T00:00:00",
            "category": "WORKOUT",
            "name": name,
            "description": description,
            "type": workout_type,
            "moving_time": moving_time,
        }

        if training_load is not None:
            payload["icu_training_load"] = training_load

        if steps is not None:
            # Convert steps to ZWO format and send as file
            # Intervals.icu API accepts ZWO via file_contents_base64
            from src.services.zwo_converter import ZWOConverter

            converter = ZWOConverter(workout_name=name)
            zwo_base64 = converter.convert_to_base64(steps)

            payload["file_contents_base64"] = zwo_base64
            payload["filename"] = "workout.zwo"

            # Dump ZWO for debugging (local development only)
            import os

            if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
                try:
                    zwo_xml = converter.convert(steps)
                    with open("uploaded_workout.zwo", "w") as f:
                        f.write(zwo_xml)
                    logger.info("Dumped ZWO to uploaded_workout.zwo")
                except Exception as e:
                    logger.error(f"Failed to dump ZWO: {e}")

        # Debug: Dump payload to file (local development only)
        import os

        if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
            try:
                import json

                debug_payload = {
                    k: v for k, v in payload.items() if k != "file_contents_base64"
                }
                if "file_contents_base64" in payload:
                    debug_payload["file_contents_base64"] = (
                        f"<{len(payload['file_contents_base64'])} chars>"
                    )
                with open("uploaded_workout.json", "w") as f:
                    json.dump(debug_payload, f, indent=2)
                logger.info("Dumped upload payload to uploaded_workout.json")
            except Exception as e:
                logger.error(f"Failed to dump payload: {e}")

        logger.info(
            f"Creating workout: {name} on {date_str} (ZWO format: {bool(steps)})"
        )
        return self._make_request("POST", endpoint, json_data=payload)

    def update_workout(self, event_id: int, **kwargs) -> dict:
        """Update an existing workout event.

        Args:
            event_id: The event ID to update.
            **kwargs: Fields to update (name, description, moving_time, etc.).

        Returns:
            Updated event object.
        """
        endpoint = f"/athlete/{self.config.athlete_id}/events/{event_id}"
        return self._make_request("PUT", endpoint, json_data=kwargs)

    def delete_event(self, event_id: int) -> None:
        """Delete an event from the calendar.

        Args:
            event_id: The event ID to delete.
        """
        endpoint = f"/athlete/{self.config.athlete_id}/events/{event_id}"
        self._make_request("DELETE", endpoint)
        logger.info(f"Deleted event: {event_id}")

    # ---------------------
    # Utility Methods
    # ---------------------

    def check_workout_exists(self, target_date: date | str) -> Optional[dict]:
        """Check if a workout already exists for the given date.

        Args:
            target_date: Date to check.

        Returns:
            Existing workout event if found, None otherwise.
        """
        events = self.get_events(target_date, target_date)

        for event in events:
            if event.get("category") == "WORKOUT":
                return event

        return None
