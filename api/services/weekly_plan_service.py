"""Weekly Workout Plan Generation Service.

Generates 7-day workout plans based on user's training style,
current fitness metrics, and training goals.
"""

import json
import logging
import re
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Training style descriptions for AI prompt
TRAINING_STYLE_DESCRIPTIONS = {
    "auto": "Automatically balance based on TSB and training phase",
    "polarized": "80/20 approach - 80% easy (Z1-Z2), 20% very hard (Z5-Z6), minimize middle zones",
    "norwegian": "Threshold-focused with 4x8 or 5x5 minute intervals at FTP",
    "sweetspot": "Sweet Spot emphasis - long intervals at 88-94% FTP for efficient gains",
    "threshold": "FTP-focused training with sustained efforts at 95-105% FTP",
    "endurance": "Base building with long Z2 rides, minimal intensity",
}

# Day-of-week training templates (for AI guidance)
WEEKLY_STRUCTURE_TEMPLATE = """
Standard weekly structure based on training style:

POLARIZED (80/20):
- Monday: Rest or Easy Spin (Recovery)
- Tuesday: Zone 2 Endurance (60-90min)
- Wednesday: HIGH INTENSITY - VO2max intervals
- Thursday: Zone 2 Endurance (60-90min)
- Friday: Rest or Easy Spin
- Saturday: HIGH INTENSITY + Long Ride
- Sunday: Long Zone 2 Endurance

NORWEGIAN / THRESHOLD:
- Monday: Rest or Easy Spin
- Tuesday: Threshold intervals (4x8 or 5x5)
- Wednesday: Zone 2 Endurance
- Thursday: Threshold intervals (3x10 or 2x20)
- Friday: Rest or Easy Spin
- Saturday: Mixed intensity long ride
- Sunday: Long Zone 2 Endurance

SWEETSPOT:
- Monday: Rest or Easy Spin
- Tuesday: Sweet Spot 2x20 or 3x15
- Wednesday: Zone 2 Endurance
- Thursday: Sweet Spot with bursts
- Friday: Rest or Easy Spin
- Saturday: Long Sweet Spot (3x20 or 2x30)
- Sunday: Long Zone 2 Endurance

ENDURANCE:
- Monday: Rest
- Tuesday: Zone 2 Endurance (60min)
- Wednesday: Zone 2 Endurance (75min)
- Thursday: Tempo (Zone 3) 30-45min
- Friday: Rest or Easy Spin
- Saturday: Long Zone 2 (2-3hrs)
- Sunday: Long Zone 2 (2-3hrs)
"""


WEEKLY_PLAN_PROMPT = """# Role
You are an expert Cycling Coach creating a structured 7-day training plan.

# Athlete Context
- **Training Style:** {training_style} - {training_style_description}
- **Preferred Duration:** {preferred_duration} minutes per workout
- **Training Goal:** {training_goal}
- **Current CTL (Fitness):** {ctl:.1f}
- **Current ATL (Fatigue):** {atl:.1f}
- **Current TSB (Form):** {tsb:.1f} ({form_status})
- **Weekly TSS Target:** {weekly_tss_target}

# Week Planning: {week_start} to {week_end}

{weekly_structure}

# Available Workout Modules
Below is the library of workout modules you can use:

{module_inventory}

# Rules
1. **Structure:** Always include warmup → main → cooldown for each workout day.
2. **Rest Days:** Include 1-2 complete rest days per week. For rest days, set type to "Rest" and modules to empty array.
3. **TSB Management:** 
   - If TSB < -20: Prioritize recovery, reduce intensity
   - If TSB -10 to -20: Moderate volume, limit high intensity
   - If TSB > -10: Can include hard workouts
4. **Progressive Load:** Build intensity mid-week, recover on weekends or vice versa.
5. **Duration:** Each workout should be close to the preferred duration ({preferred_duration} min).
6. **Variety:** Use different modules throughout the week.

# Output Format
Generate a JSON array with exactly 7 daily plans:

```json
[
  {{
    "day_index": 0,
    "day_name": "Monday",
    "date": "2026-01-13",
    "workout_type": "Recovery|Endurance|Tempo|SweetSpot|Threshold|VO2max|Rest",
    "workout_name": "Creative descriptive name",
    "duration_minutes": 60,
    "estimated_tss": 45,
    "intensity": "easy|moderate|hard|rest",
    "selected_modules": ["warmup_key", "main_key", "rest_key", "main_key", "cooldown_key"],
    "rationale": "Brief explanation of why this workout on this day"
  }},
  ...
]
```

Generate the 7-day plan now.
"""


@dataclass
class DailyPlan:
    """Single day's workout plan."""

    day_index: int
    day_name: str
    workout_date: date
    workout_type: str
    workout_name: str
    duration_minutes: int
    estimated_tss: int
    intensity: str
    selected_modules: List[str]
    rationale: str


@dataclass
class WeeklyPlan:
    """Complete weekly plan."""

    week_start: date
    week_end: date
    training_style: str
    total_planned_tss: int
    daily_plans: List[DailyPlan]


class WeeklyPlanGenerator:
    """Generates weekly workout plans using AI."""

    def __init__(self, llm_client, user_profile: dict):
        """Initialize generator.

        Args:
            llm_client: LLM client for generation
            user_profile: User settings dict
        """
        self.llm = llm_client
        self.profile = user_profile

    def generate_weekly_plan(
        self,
        ctl: float,
        atl: float,
        tsb: float,
        form_status: str,
        week_start: Optional[date] = None,
        exclude_barcode: bool = False,
    ) -> WeeklyPlan:
        """Generate a complete 7-day workout plan.

        Args:
            ctl: Current Chronic Training Load
            atl: Current Acute Training Load
            tsb: Current Training Stress Balance
            form_status: Form status string (Fresh, Tired, etc.)
            week_start: Monday of the target week (default: next Monday)
            exclude_barcode: Whether to exclude barcode workouts

        Returns:
            WeeklyPlan with 7 daily plans
        """
        # Calculate week dates
        if week_start is None:
            today = date.today()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7  # Next Monday if today is Monday
            week_start = today + timedelta(days=days_until_monday)

        week_end = week_start + timedelta(days=6)

        # Get training style from profile
        training_style = self.profile.get("training_style", "auto")
        training_style_desc = TRAINING_STYLE_DESCRIPTIONS.get(
            training_style, TRAINING_STYLE_DESCRIPTIONS["auto"]
        )

        # Calculate weekly TSS target based on CTL
        weekly_tss_target = int(ctl * 7)  # Rough estimate

        # Get module inventory
        from src.services.workout_modules import get_module_inventory_text

        module_inventory = get_module_inventory_text(exclude_barcode=exclude_barcode)

        # Build prompt
        prompt = WEEKLY_PLAN_PROMPT.format(
            training_style=training_style,
            training_style_description=training_style_desc,
            preferred_duration=self.profile.get("preferred_duration", 60),
            training_goal=self.profile.get("training_goal", "General Fitness"),
            ctl=ctl,
            atl=atl,
            tsb=tsb,
            form_status=form_status,
            weekly_tss_target=weekly_tss_target,
            week_start=week_start.strftime("%Y-%m-%d"),
            week_end=week_end.strftime("%Y-%m-%d"),
            weekly_structure=WEEKLY_STRUCTURE_TEMPLATE,
            module_inventory=module_inventory,
        )

        logger.info(f"Generating weekly plan for {week_start} to {week_end}")

        # Generate with LLM
        response = self.llm.generate(
            system_prompt=prompt, user_prompt="Generate the 7-day workout plan now."
        )

        # Parse response
        daily_plans = self._parse_response(response, week_start)

        # Calculate total TSS
        total_tss = sum(dp.estimated_tss for dp in daily_plans)

        return WeeklyPlan(
            week_start=week_start,
            week_end=week_end,
            training_style=training_style,
            total_planned_tss=total_tss,
            daily_plans=daily_plans,
        )

    def _parse_response(self, response: str, week_start: date) -> List[DailyPlan]:
        """Parse LLM response into DailyPlan objects.

        Args:
            response: Raw LLM response
            week_start: Monday of the week

        Returns:
            List of 7 DailyPlan objects
        """
        if not response:
            logger.warning("Empty response from LLM, using fallback")
            return self._generate_fallback_plan(week_start)

        # Extract JSON from response
        try:
            # Try to find JSON array in response
            json_match = re.search(r"\[[\s\S]*\]", response)
            if json_match:
                json_str = json_match.group(0)
                plans_data = json.loads(json_str)
            else:
                plans_data = json.loads(response)

            if not isinstance(plans_data, list):
                logger.warning(
                    f"Parsed JSON is {type(plans_data)}, expected list. Using fallback."
                )
                return self._generate_fallback_plan(week_start)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse weekly plan response: {e}")
            logger.debug(f"Response was: {response[:500]}...")
            # Return default plan
            return self._generate_fallback_plan(week_start)

        # Convert to DailyPlan objects
        daily_plans = []
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        for i, plan_data in enumerate(plans_data[:7]):  # Limit to 7 days
            workout_date = week_start + timedelta(days=i)

            daily_plans.append(
                DailyPlan(
                    day_index=i,
                    day_name=day_names[i],
                    workout_date=workout_date,
                    workout_type=plan_data.get("workout_type", "Endurance"),
                    workout_name=plan_data.get("workout_name", f"Day {i+1} Workout"),
                    duration_minutes=plan_data.get("duration_minutes", 60),
                    estimated_tss=plan_data.get("estimated_tss", 50),
                    intensity=plan_data.get("intensity", "moderate"),
                    selected_modules=plan_data.get("selected_modules", []),
                    rationale=plan_data.get("rationale", ""),
                )
            )

        # Ensure we have exactly 7 days
        while len(daily_plans) < 7:
            i = len(daily_plans)
            workout_date = week_start + timedelta(days=i)
            daily_plans.append(
                DailyPlan(
                    day_index=i,
                    day_name=day_names[i],
                    workout_date=workout_date,
                    workout_type="Rest",
                    workout_name="Rest Day",
                    duration_minutes=0,
                    estimated_tss=0,
                    intensity="rest",
                    selected_modules=[],
                    rationale="Rest day to recover",
                )
            )

        return daily_plans

    def _generate_fallback_plan(self, week_start: date) -> List[DailyPlan]:
        """Generate a simple fallback plan if AI fails.

        Args:
            week_start: Monday of the week

        Returns:
            List of 7 basic DailyPlan objects
        """
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        fallback_types = [
            "Rest",
            "Endurance",
            "SweetSpot",
            "Endurance",
            "Rest",
            "Threshold",
            "Endurance",
        ]
        fallback_tss = [0, 50, 65, 50, 0, 75, 60]

        daily_plans = []
        for i in range(7):
            workout_date = week_start + timedelta(days=i)
            is_rest = fallback_types[i] == "Rest"

            daily_plans.append(
                DailyPlan(
                    day_index=i,
                    day_name=day_names[i],
                    workout_date=workout_date,
                    workout_type=fallback_types[i],
                    workout_name=(
                        "Rest Day" if is_rest else f"{fallback_types[i]} Session"
                    ),
                    duration_minutes=0 if is_rest else 60,
                    estimated_tss=fallback_tss[i],
                    intensity="rest" if is_rest else "moderate",
                    selected_modules=(
                        []
                        if is_rest
                        else ["ramp_standard", "endurance_20min", "flush_and_fade"]
                    ),
                    rationale="Fallback plan - AI generation failed",
                )
            )

        return daily_plans
