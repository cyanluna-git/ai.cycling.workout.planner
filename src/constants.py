"""Application Constants.

Centralized constants for the AI Cycling Coach application.
This reduces magic strings and makes configuration easier to manage.
"""

# ---------------------
# Workout Naming
# ---------------------
WORKOUT_PREFIX = "[AICoach]"
WORKOUT_FALLBACK_NAME = "AI Generated Workout"

# ---------------------
# Default Values
# ---------------------
DEFAULT_FTP = 250  # Watts
DEFAULT_MAX_DURATION = 60  # Minutes
DEFAULT_WORKOUT_TYPE = "Ride"

# ---------------------
# Training Zones (% of FTP)
# ---------------------
ZONE_COLORS = {
    1: "#009e80",  # Active Recovery (0-55%)
    2: "#009e00",  # Endurance (56-75%)
    3: "#ffcb0e",  # Tempo (76-90%)
    4: "#ff7f0e",  # Threshold (91-105%)
    5: "#dd0447",  # VO2 Max (106-120%)
    6: "#6633cc",  # Anaerobic (121-150%)
    7: "#504861",  # Neuromuscular (151%+)
}

ZONE_THRESHOLDS = [55, 75, 90, 105, 120, 150, 999]

# ---------------------
# API Defaults
# ---------------------
DEFAULT_CACHE_TTL = 300  # 5 minutes
MAX_RETRY_ATTEMPTS = 3
API_TIMEOUT = 30  # seconds

# ---------------------
# LLM Configuration
# ---------------------
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 2000
