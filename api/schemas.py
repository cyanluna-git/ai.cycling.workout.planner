"""Pydantic schemas for API request/response models."""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


# --- Fitness ---


class TrainingMetrics(BaseModel):
    """Current training metrics."""

    ctl: float = Field(..., description="Chronic Training Load (fitness)")
    atl: float = Field(..., description="Acute Training Load (fatigue)")
    tsb: float = Field(..., description="Training Stress Balance (form)")
    form_status: str = Field(..., description="Form status (Fresh/Tired/Fatigued)")


class WellnessMetrics(BaseModel):
    """Current wellness metrics."""

    readiness: str = Field(..., description="Training readiness")
    hrv: Optional[float] = Field(None, description="Heart Rate Variability")
    rhr: Optional[int] = Field(None, description="Resting Heart Rate")
    sleep_hours: Optional[float] = Field(None, description="Hours of sleep")


class AthleteProfile(BaseModel):
    """Athlete profile from Intervals.icu."""

    ftp: Optional[int] = Field(None, description="Functional Threshold Power (W)")
    max_hr: Optional[int] = Field(None, description="Maximum Heart Rate (bpm)")
    lthr: Optional[int] = Field(None, description="Lactate Threshold Heart Rate (bpm)")
    weight: Optional[float] = Field(None, description="Weight (kg)")
    w_per_kg: Optional[float] = Field(None, description="Watts per kg (FTP/weight)")


class FitnessResponse(BaseModel):
    """Response for /api/fitness endpoint."""

    training: TrainingMetrics
    wellness: WellnessMetrics
    profile: AthleteProfile


# --- Workout Generation ---


class WorkoutGenerateRequest(BaseModel):
    """Request body for workout generation."""

    target_date: Optional[str] = Field(None, description="Target date (YYYY-MM-DD)")
    duration: int = Field(60, ge=15, le=180, description="Duration in minutes")
    style: str = Field("auto", description="Training style")
    intensity: str = Field("auto", description="Intensity preference")
    notes: str = Field("", description="Additional notes")
    indoor: bool = Field(False, description="Indoor trainer mode")


class WorkoutStep(BaseModel):
    """Individual workout step."""

    duration: str = Field(..., description="Duration (e.g., '10m')")
    power: str = Field(..., description="Power target (e.g., '50%')")


class GeneratedWorkout(BaseModel):
    """Generated workout response."""

    name: str = Field(..., description="Workout name")
    workout_type: str = Field(..., description="Workout type")
    design_goal: Optional[str] = Field(None, description="Design goal or rationale")
    estimated_tss: Optional[int] = Field(None, description="Estimated TSS")
    estimated_duration_minutes: int = Field(..., description="Duration in minutes")
    workout_text: str = Field(..., description="Formatted workout text")
    warmup: List[str] = Field(default_factory=list, description="Warmup steps")
    main: List[str] = Field(default_factory=list, description="Main set steps")
    cooldown: List[str] = Field(default_factory=list, description="Cooldown steps")
    steps: Optional[List[dict]] = Field(
        default=None, description="Structured workout steps (JSON)"
    )


class WorkoutGenerateResponse(BaseModel):
    """Response for workout generation."""

    success: bool
    workout: Optional[GeneratedWorkout] = None
    error: Optional[str] = None


# --- Workout Creation ---


class WorkoutCreateRequest(BaseModel):
    """Request body for creating workout on Intervals.icu."""

    target_date: str = Field(..., description="Target date (YYYY-MM-DD)")
    name: str = Field(..., description="Workout name")
    workout_text: str = Field(..., description="Workout text")
    duration_minutes: int = Field(..., description="Duration in minutes")
    estimated_tss: Optional[int] = Field(None, description="Estimated TSS")
    design_goal: Optional[str] = Field(
        None, description="Design goal or rationale from AI"
    )
    workout_type: Optional[str] = Field(
        None, description="Workout type (e.g., SweetSpot)"
    )
    force: bool = Field(False, description="Replace existing workout")
    steps: Optional[List[dict]] = Field(
        default=None, description="Structured workout steps for API"
    )


class WorkoutCreateResponse(BaseModel):
    """Response for workout creation."""

    success: bool
    event_id: Optional[int] = None
    error: Optional[str] = None


# --- Activities ---


class Activity(BaseModel):
    """Activity summary."""

    id: str
    date: str
    name: str
    type: str
    duration_minutes: Optional[int] = None
    tss: Optional[float] = None
    distance_km: Optional[float] = None


class ActivitiesResponse(BaseModel):
    """Response for activities list."""

    activities: List[Activity]
    total: int


# --- Weekly Calendar ---


class WeeklyEvent(BaseModel):
    """A planned workout event or actual activity from Intervals.icu."""

    id: str  # Changed to str to accommodate Activity IDs (often strings)
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    name: str
    category: str = Field(..., description="Event category (WORKOUT, ACTIVITY, etc)")
    workout_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    tss: Optional[int] = None
    description: Optional[str] = None
    is_actual: bool = Field(False, description="True if this is a completed activity")
    is_indoor: bool = Field(False, description="True if indoor activity")


class WeeklyCalendarResponse(BaseModel):
    """Response for weekly calendar."""

    week_start: str
    week_end: str
    events: List[WeeklyEvent]
    planned_tss: int = 0
    actual_tss: int = 0
