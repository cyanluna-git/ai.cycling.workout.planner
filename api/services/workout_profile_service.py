"""Workout Profile Database Service.

Provides access to pre-built workout profiles stored in SQLite DB.
Supports querying by category, duration, difficulty, and TSS range.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class WorkoutProfileService:
    """Service for querying and applying workout profiles from DB."""

    def __init__(self, db_path: str = "data/workout_profiles.db"):
        """Initialize profile service.

        Args:
            db_path: Path to SQLite database (relative to project root)
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            logger.warning(f"Profile DB not found at {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_candidates(
        self,
        categories: Optional[List[str]] = None,
        target_zone: Optional[str] = None,
        duration_range: Optional[Tuple[int, int]] = None,
        tss_range: Optional[Tuple[int, int]] = None,
        difficulty_max: Optional[str] = None,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """Query workout profiles by filters.

        Args:
            categories: List of category names to include (e.g., ["threshold", "vo2max"])
            target_zone: Target training zone (e.g., "Z2", "SST", "VO2max")
            duration_range: (min_minutes, max_minutes)
            tss_range: (min_tss, max_tss)
            difficulty_max: Maximum difficulty ("beginner", "intermediate", "advanced")
            limit: Maximum number of results

        Returns:
            List of profile dictionaries
        """
        if not self.db_path.exists():
            logger.warning("Profile DB not available, returning empty candidates")
            return []

        query = "SELECT * FROM workout_profiles WHERE is_active = 1"
        params = []

        # Category filter
        if categories:
            placeholders = ",".join(["?" for _ in categories])
            query += f" AND category IN ({placeholders})"
            params.extend(categories)

        # Target zone filter
        if target_zone:
            query += " AND target_zone = ?"
            params.append(target_zone)

        # Duration range filter
        if duration_range:
            min_dur, max_dur = duration_range
            query += " AND duration_minutes BETWEEN ? AND ?"
            params.extend([min_dur, max_dur])

        # TSS range filter
        if tss_range:
            min_tss, max_tss = tss_range
            query += " AND estimated_tss BETWEEN ? AND ?"
            params.extend([min_tss, max_tss])

        # Difficulty filter (beginner < intermediate < advanced)
        if difficulty_max:
            difficulty_order = {"beginner": 0, "intermediate": 1, "advanced": 2}
            max_level = difficulty_order.get(difficulty_max, 2)
            allowed_difficulties = [k for k, v in difficulty_order.items() if v <= max_level]
            placeholders = ",".join(["?" for _ in allowed_difficulties])
            query += f" AND difficulty IN ({placeholders})"
            params.extend(allowed_difficulties)

        # Order by category and duration for better variety
        query += " ORDER BY category, duration_minutes LIMIT ?"
        params.append(limit)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            profiles = []
            for row in rows:
                profile = dict(row)
                # Parse JSON fields
                if profile.get("steps_json"):
                    profile["steps_json"] = json.loads(profile["steps_json"])
                if profile.get("coach_notes"):
                    try:
                        profile["coach_notes_parsed"] = json.loads(profile["coach_notes"])
                    except json.JSONDecodeError:
                        profile["coach_notes_parsed"] = {}
                if profile.get("tags"):
                    try:
                        profile["tags_list"] = json.loads(profile["tags"])
                    except json.JSONDecodeError:
                        profile["tags_list"] = []
                profiles.append(profile)

            logger.info(f"Found {len(profiles)} profile candidates")
            return profiles

        except Exception as e:
            logger.error(f"Error querying profiles: {e}")
            return []

    def get_profile_by_id(self, profile_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single profile by ID.

        Args:
            profile_id: Profile ID

        Returns:
            Profile dictionary or None if not found
        """
        if not self.db_path.exists():
            logger.warning("Profile DB not available")
            return None

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workout_profiles WHERE id = ? AND is_active = 1", (profile_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                logger.warning(f"Profile {profile_id} not found")
                return None

            profile = dict(row)
            # Parse JSON fields
            if profile.get("steps_json"):
                profile["steps_json"] = json.loads(profile["steps_json"])
            if profile.get("coach_notes"):
                try:
                    profile["coach_notes_parsed"] = json.loads(profile["coach_notes"])
                except json.JSONDecodeError:
                    profile["coach_notes_parsed"] = {}

            return profile

        except Exception as e:
            logger.error(f"Error fetching profile {profile_id}: {e}")
            return None

    def format_candidates_for_prompt(self, candidates: List[Dict[str, Any]]) -> str:
        """Format profile candidates for LLM prompt.

        Args:
            candidates: List of profile dictionaries

        Returns:
            Formatted string for LLM prompt
        """
        if not candidates:
            return "(No profiles available - fallback to legacy module system)"

        lines = []
        for profile in candidates:
            # Format: [ID:1] Name | Category | Duration | TSS | Difficulty
            header = (
                f"[ID:{profile['id']}] {profile['name']} | "
                f"{profile['category'].upper()} | "
                f"{profile['duration_minutes']}min | "
                f"TSS:{profile['estimated_tss']:.1f} | "
                f"{profile['difficulty'].capitalize()}"
            )
            lines.append(header)

            # Description
            if profile.get("description"):
                lines.append(f"  Description: {profile['description']}")

            # Customization options from coach_notes
            coach_notes = profile.get("coach_notes_parsed", {})
            if coach_notes:
                custom_parts = []
                for key, value in coach_notes.items():
                    if isinstance(value, list) and len(value) == 2:
                        custom_parts.append(f"{key}: {value[0]} to +{value[1]}")
                if custom_parts:
                    lines.append(f"  Customizable: {', '.join(custom_parts)}")

            lines.append("")  # Blank line between profiles

        return "\n".join(lines)

    def apply_customization(
        self, profile: Dict[str, Any], customization: Dict[str, Any], ftp: int
    ) -> Dict[str, Any]:
        """Apply customization to a profile.

        Args:
            profile: Profile dictionary
            customization: Customization dict (e.g., {"repeat_adjust": -1, "power_adjust": -5})
            ftp: User's FTP in watts

        Returns:
            Modified profile dictionary (copy)
        """
        import copy

        profile_copy = copy.deepcopy(profile)
        steps = profile_copy.get("steps_json", {}).get("steps", [])
        coach_notes = profile_copy.get("coach_notes_parsed", {})

        # Apply repeat_adjust
        if "repeat_adjust" in customization:
            allowed_range = coach_notes.get("repeat_adjust", [-2, 2])
            adjust = max(allowed_range[0], min(allowed_range[1], customization["repeat_adjust"]))
            for step in steps:
                if step.get("type") == "intervals" and "repeat" in step:
                    step["repeat"] = max(1, step["repeat"] + adjust)

        # Apply power_adjust (percentage points)
        if "power_adjust" in customization:
            allowed_range = coach_notes.get("power_adjust", [-10, 10])
            adjust = max(allowed_range[0], min(allowed_range[1], customization["power_adjust"]))
            for step in steps:
                if "on_power" in step:
                    step["on_power"] = max(50, step["on_power"] + adjust)
                if "off_power" in step:
                    step["off_power"] = max(40, step["off_power"] + adjust)
                if "start_power" in step:
                    step["start_power"] = max(40, step["start_power"] + adjust)
                if "end_power" in step:
                    step["end_power"] = max(40, step["end_power"] + adjust)
                if "power" in step:
                    step["power"] = max(50, step["power"] + adjust)

        # Apply warmup_adjust (minutes)
        if "warmup_adjust" in customization:
            allowed_range = coach_notes.get("warmup_adjust", [-5, 10])
            adjust_min = max(allowed_range[0], min(allowed_range[1], customization["warmup_adjust"]))
            adjust_sec = adjust_min * 60
            for step in steps:
                if step.get("type") == "warmup" and "duration_sec" in step:
                    step["duration_sec"] = max(300, step["duration_sec"] + adjust_sec)  # Min 5min

        # Apply cooldown_adjust (minutes)
        if "cooldown_adjust" in customization:
            allowed_range = coach_notes.get("cooldown_adjust", [-5, 10])
            adjust_min = max(allowed_range[0], min(allowed_range[1], customization["cooldown_adjust"]))
            adjust_sec = adjust_min * 60
            for step in steps:
                if step.get("type") == "cooldown" and "duration_sec" in step:
                    step["duration_sec"] = max(300, step["duration_sec"] + adjust_sec)  # Min 5min

        logger.info(f"Applied customization to profile {profile['id']}: {customization}")
        return profile_copy

    def profile_to_steps(self, profile: Dict[str, Any], ftp: int) -> List[Dict[str, Any]]:
        """Convert profile steps to workout steps with FTP applied.

        Args:
            profile: Profile dictionary
            ftp: User's FTP in watts

        Returns:
            List of workout step dictionaries ready for ZWO conversion
        """
        steps_data = profile.get("steps_json", {}).get("steps", [])
        workout_steps = []

        for step in steps_data:
            step_type = step.get("type")
            step_copy = {"type": step_type}

            # Convert %FTP to watts
            if "start_power" in step:
                step_copy["start_power"] = int(step["start_power"] * ftp / 100)
            if "end_power" in step:
                step_copy["end_power"] = int(step["end_power"] * ftp / 100)
            if "on_power" in step:
                step_copy["on_power"] = int(step["on_power"] * ftp / 100)
            if "off_power" in step:
                step_copy["off_power"] = int(step["off_power"] * ftp / 100)
            if "power" in step:
                step_copy["power"] = int(step["power"] * ftp / 100)

            # Copy duration fields
            if "duration_sec" in step:
                step_copy["duration_sec"] = step["duration_sec"]
            if "on_sec" in step:
                step_copy["on_sec"] = step["on_sec"]
            if "off_sec" in step:
                step_copy["off_sec"] = step["off_sec"]
            if "repeat" in step:
                step_copy["repeat"] = step["repeat"]

            # Copy cadence if present
            if "cadence" in step:
                step_copy["cadence"] = step["cadence"]
            if "start_cadence" in step:
                step_copy["start_cadence"] = step["start_cadence"]
            if "end_cadence" in step:
                step_copy["end_cadence"] = step["end_cadence"]

            workout_steps.append(step_copy)

        logger.info(f"Converted profile {profile['id']} to {len(workout_steps)} workout steps")
        return workout_steps
