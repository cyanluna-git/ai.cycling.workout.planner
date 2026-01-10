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
    exclude_barcode_workouts: bool = False  # Exclude barcode-style intervals (40/20, 30/30)


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
    required_vars = ["INTERVALS_API_KEY", "ATHLETE_ID"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    # For LLM, check for provider-specific keys
    llm_provider = os.getenv("LLM_PROVIDER", "gemini")
    llm_api_key = os.getenv("LLM_API_KEY")

    # Fallback to provider-specific keys if LLM_API_KEY not set
    if not llm_api_key:
        if llm_provider == "gemini":
            llm_api_key = os.getenv("GEMINI_API_KEY", "")
        elif llm_provider == "openai":
            llm_api_key = os.getenv("OPENAI_API_KEY", "")
        elif llm_provider == "groq":
            llm_api_key = os.getenv("GROQ_API_KEY", "")

    if not llm_api_key:
        raise ValueError(
            f"No LLM API key found. Set LLM_API_KEY or {llm_provider.upper()}_API_KEY"
        )

    return Config(
        intervals=IntervalsConfig(
            api_key=os.getenv("INTERVALS_API_KEY", ""),
            athlete_id=os.getenv("ATHLETE_ID", ""),
            base_url=os.getenv("INTERVALS_BASE_URL", "https://intervals.icu/api/v1"),
        ),
        llm=LLMConfig(
            provider=llm_provider,
            api_key=llm_api_key,
            model=os.getenv("LLM_MODEL") or os.getenv(f"{llm_provider.upper()}_MODEL", "gpt-4o"),
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
