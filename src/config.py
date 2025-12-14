"""Configuration management for AI Cycling Coach."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class IntervalsConfig:
    """Intervals.icu API configuration."""

    api_key: str
    athlete_id: str
    base_url: str = "https://intervals.icu/api/v1"


@dataclass
class LLMConfig:
    """LLM API configuration."""

    provider: str  # openai, anthropic, gemini
    api_key: str
    model: str


@dataclass
class UserProfile:
    """User cycling profile for workout generation."""

    ftp: int  # Functional Threshold Power
    max_hr: int  # Maximum Heart Rate
    lthr: int  # Lactate Threshold Heart Rate
    training_goal: str


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""

    schedule_time: str  # HH:MM format
    log_level: str
    log_file: str


@dataclass
class Config:
    """Main configuration container."""

    intervals: IntervalsConfig
    llm: LLMConfig
    user_profile: UserProfile
    scheduler: SchedulerConfig


def load_config(env_file: Optional[str] = None) -> Config:
    """Load configuration from environment variables.

    Args:
        env_file: Optional path to .env file. If not provided, looks for .env in project root.

    Returns:
        Config object with all settings loaded.

    Raises:
        ValueError: If required environment variables are missing.
    """
    if env_file:
        load_dotenv(env_file)
    else:
        # Try to find .env in project root
        project_root = Path(__file__).parent.parent
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()  # Try default locations

    # Validate required environment variables
    required_vars = ["INTERVALS_API_KEY", "ATHLETE_ID", "LLM_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    return Config(
        intervals=IntervalsConfig(
            api_key=os.getenv("INTERVALS_API_KEY", ""),
            athlete_id=os.getenv("ATHLETE_ID", ""),
            base_url=os.getenv("INTERVALS_BASE_URL", "https://intervals.icu/api/v1"),
        ),
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            api_key=os.getenv("LLM_API_KEY", ""),
            model=os.getenv("LLM_MODEL", "gpt-4o"),
        ),
        user_profile=UserProfile(
            ftp=int(os.getenv("USER_FTP", "250")),
            max_hr=int(os.getenv("USER_MAX_HR", "185")),
            lthr=int(os.getenv("USER_LTHR", "165")),
            training_goal=os.getenv("TRAINING_GOAL", ""),
        ),
        scheduler=SchedulerConfig(
            schedule_time=os.getenv("SCHEDULE_TIME", "06:00"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "logs/ai_cycling_coach.log"),
        ),
    )


# Convenience function for quick access
def get_config() -> Config:
    """Get configuration singleton.

    Returns:
        Loaded Config object.
    """
    return load_config()
