"""Workout Profile Database Service.

Provides access to pre-built workout profiles stored in SQLite DB.
Supports querying by category, duration, difficulty, and TSS range.
"""

import json
import logging
import random
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
        limit: int = 50,
        exclude_profile_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Query workout profiles by filters.

        Args:
            categories: List of category names to include (e.g., ["threshold", "vo2max"])
            target_zone: Target training zone (e.g., "Z2", "SST", "VO2max")
            duration_range: (min_minutes, max_minutes)
            tss_range: (min_tss, max_tss)
            difficulty_max: Maximum difficulty ("beginner", "intermediate", "advanced")
            limit: Maximum number of results (default: 50 for better variety)
            exclude_profile_ids: List of profile IDs to exclude (recently used)

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

        # Exclude recently used profiles
        if exclude_profile_ids:
            placeholders = ",".join(["?" for _ in exclude_profile_ids])
            query += f" AND id NOT IN ({placeholders})"
            params.extend(exclude_profile_ids)

        # Use RANDOM() for variety and avoid bias
        query += " ORDER BY RANDOM() LIMIT ?"
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

    def profile_to_frontend_steps(self, profile: Dict[str, Any], ftp: int) -> List[Dict[str, Any]]:
        """Convert profile steps to frontend WorkoutStep format (power in %FTP).
        
        This method reads raw steps from profile's steps_json and converts them
        to the frontend format while keeping power values as %FTP (not watts).
        
        Args:
            profile: Profile dictionary with steps_json
            ftp: User's FTP in watts (used for metadata, not conversion)
            
        Returns:
            List of frontend-format workout steps with power in %FTP
        """
        steps_data = profile.get("steps_json", {}).get("steps", [])
        frontend_steps = []
        
        for step in steps_data:
            step_type = step.get("type", "steady")
            
            if step_type == "warmup":
                fs = {"duration": step.get("duration_sec", 0), "warmup": True}
                if "start_power" in step and "end_power" in step:
                    fs["ramp"] = True
                    fs["power"] = {
                        "start": round(step["start_power"]),
                        "end": round(step["end_power"]),
                        "units": "%ftp"
                    }
                elif "power" in step:
                    fs["power"] = {
                        "value": round(step["power"]),
                        "units": "%ftp"
                    }
                frontend_steps.append(fs)
                
            elif step_type == "cooldown":
                fs = {"duration": step.get("duration_sec", 0), "cooldown": True}
                if "start_power" in step and "end_power" in step:
                    fs["ramp"] = True
                    fs["power"] = {
                        "start": round(step["start_power"]),
                        "end": round(step["end_power"]),
                        "units": "%ftp"
                    }
                elif "power" in step:
                    fs["power"] = {
                        "value": round(step["power"]),
                        "units": "%ftp"
                    }
                frontend_steps.append(fs)
                
            elif step_type == "intervals" and "repeat" in step:
                on_step = {
                    "duration": step.get("on_sec", 0),
                    "power": {
                        "value": round(step.get("on_power", 0)),
                        "units": "%ftp"
                    }
                }
                off_step = {
                    "duration": step.get("off_sec", 0),
                    "power": {
                        "value": round(step.get("off_power", 0)),
                        "units": "%ftp"
                    }
                }
                frontend_steps.append({
                    "repeat": step["repeat"],
                    "steps": [on_step, off_step]
                })
                
            elif step_type == "ramp":
                fs = {"duration": step.get("duration_sec", 0), "ramp": True}
                if "start_power" in step and "end_power" in step:
                    fs["power"] = {
                        "start": round(step["start_power"]),
                        "end": round(step["end_power"]),
                        "units": "%ftp"
                    }
                frontend_steps.append(fs)
                
            else:  # steady
                fs = {"duration": step.get("duration_sec", 0)}
                if "start_power" in step and "end_power" in step:
                    fs["ramp"] = True
                    fs["power"] = {
                        "start": round(step["start_power"]),
                        "end": round(step["end_power"]),
                        "units": "%ftp"
                    }
                elif "power" in step:
                    fs["power"] = {
                        "value": round(step["power"]),
                        "units": "%ftp"
                    }
                frontend_steps.append(fs)
        
        logger.info(f"Converted profile {profile['id']} to {len(frontend_steps)} frontend steps (power in %FTP)")
        return frontend_steps

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


# ---------------------------------------------------------------------------
# Shared Helper for LLM Profile Selection
# ---------------------------------------------------------------------------

# Training style to category mapping (shared constant)
STYLE_CATEGORIES = {
    "endurance": ["endurance", "recovery", "tempo"],
    "sweetspot": ["sweetspot", "endurance", "threshold", "recovery"],
    "threshold": ["threshold", "sweetspot", "vo2max", "endurance", "recovery"],
    "polarized": ["endurance", "vo2max", "recovery"],
    "vo2max": ["vo2max", "threshold", "endurance", "recovery"],
    "sprint": ["sprint", "anaerobic", "endurance", "recovery"],
    "climbing": ["climbing", "threshold", "sweetspot", "endurance", "recovery"],
    "norwegian": ["threshold", "vo2max", "endurance", "recovery"],
}


def get_max_difficulty_from_tsb(tsb: float) -> str:
    """Map TSB to maximum difficulty level.
    
    Args:
        tsb: Training Stress Balance
        
    Returns:
        Maximum difficulty: "beginner", "intermediate", or "advanced"
    """
    if tsb < -20:
        return "beginner"
    elif tsb < -10:
        return "intermediate"
    else:
        return "advanced"


def get_profile_candidates_for_llm(
    tsb: float,
    training_style: str,
    duration: int,
    duration_buffer: int = 30,
    limit: int = 50,
    exclude_profile_ids: Optional[List[int]] = None,
    db_path: str = "data/workout_profiles.db",
) -> Tuple[str, List[Dict[str, Any]]]:
    """Get profile candidates formatted for LLM selection.
    
    This is a shared helper used by both daily workout generation
    and weekly plan generation to ensure consistent candidate selection.
    
    Args:
        tsb: Training Stress Balance
        training_style: Training style ("polarized", "threshold", etc.)
        duration: Target duration in minutes
        duration_buffer: Buffer around target duration (default: 30min)
        limit: Maximum number of candidates (default: 50)
        exclude_profile_ids: List of profile IDs to exclude (recently used)
        db_path: Path to workout profiles database
        
    Returns:
        Tuple of (formatted_text_for_llm, raw_candidates_list)
    """
    # Initialize service
    profile_service = WorkoutProfileService(db_path=db_path)
    
    # Calculate max difficulty from TSB
    max_difficulty = get_max_difficulty_from_tsb(tsb)
    
    # Map training style to categories
    categories = STYLE_CATEGORIES.get(training_style, None)
    
    # Get candidates with exclusions
    candidates = profile_service.get_candidates(
        categories=categories,
        duration_range=(max(20, duration - duration_buffer), duration + duration_buffer),
        difficulty_max=max_difficulty,
        limit=limit,
        exclude_profile_ids=exclude_profile_ids,
    )
    
    if not candidates:
        return "(No profiles available - fallback to legacy module system)", []
    
    # Shuffle for additional variety (on top of RANDOM())
    random.shuffle(candidates)
    
    # Format for LLM prompt
    formatted_text = profile_service.format_candidates_for_prompt(candidates)
    
    return formatted_text, candidates
