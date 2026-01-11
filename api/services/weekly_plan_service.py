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
    "polarized": "80/20 approach - 80% easy (Z1-Z2), 20% very hard (Z5-Z6). Minimal Zone 3-4. Focus on long Z2 rides and short VO2max intervals.",
    "norwegian": "Double session threshold training. Morning: easy aerobic (30-45min Z2). Afternoon: Lactate threshold intervals (4x4, 3x8, 5x5 at 95-100% FTP). 3 threshold days per week.",
    "sweetspot": "Sweet Spot emphasis - long intervals at 88-94% FTP (2x20, 3x15, 2x30). Efficient way to build FTP with lower recovery needs than threshold.",
    "threshold": "FTP-focused training with sustained efforts at 95-105% FTP. 2x20, 3x15, or over/under workouts. High training stress.",
    "endurance": "Base building with long Z2 rides, minimal intensity. Focus on aerobic development.",
}

# Day-of-week training templates (for AI guidance)
WEEKLY_STRUCTURE_TEMPLATE = """
## Weekly Structure Guidelines by Training Style:

### POLARIZED (80/20):
- **Goal:** 80% low intensity (Z1-Z2), 20% high intensity (Z5-Z6). AVOID Zone 3-4!
- **Key Workouts:** 1-2 VO2max sessions per week, 1-2 Long Z2 rides (2hrs+)
- **CRITICAL:** Include at least ONE 2-hour Zone 2 ride, preferably TWO per week (weekend rides)
- Monday: Rest
- Tuesday: Zone 2 Endurance (60-90min)
- Wednesday: **VO2max Intervals** (4x4min at 115% FTP, full recovery) - 60min total
- Thursday: Zone 2 Easy (45-60min)
- Friday: Rest or Easy Spin (30min)
- Saturday: **LONG Zone 2** (120-180min) - ESSENTIAL for polarized training
- Sunday: **Long Zone 2** (120min minimum) - ESSENTIAL for polarized training

### NORWEGIAN (Double Session Threshold):
- **Goal:** High frequency threshold work with AM/PM split sessions
- **Key Feature:** Morning easy aerobic + Afternoon threshold intervals
- **Threshold Workouts:** 4x4min, 3x8min, 5x5min at 95-100% FTP (near lactate threshold)
- Monday: Rest
- Tuesday: **AM** Easy Z2 (30-45min) + **PM** Threshold 4x4min @95%
- Wednesday: Zone 2 Recovery (45-60min)
- Thursday: **AM** Easy Z2 (30-45min) + **PM** Threshold 3x8min @95%
- Friday: Rest or Easy Spin
- Saturday: **AM** Easy Z2 (45min) + **PM** Threshold 5x5min @95%
- Sunday: Long Zone 2 Endurance (2hrs)
⚠️ For Norwegian style: Generate TWO workouts per threshold day (AM session + PM session)

### SWEETSPOT:
- **Goal:** Maximize training effect at 88-94% FTP
- **Key Workouts:** 2x20, 3x15, 2x30 at Sweet Spot, plus long Z2 rides
- Monday: Rest
- Tuesday: **Sweet Spot 2x20min** @90% FTP - 60-75min total
- Wednesday: Zone 2 Endurance (60-75min)
- Thursday: **Sweet Spot 3x15min** with burst finishes - 60-75min total
- Friday: Rest or Easy Spin (30-45min)
- Saturday: **Long Sweet Spot** 3x20min or 2x30min - 90-120min total
- Sunday: **Long Zone 2** (120min) - Essential for aerobic base

### THRESHOLD:
- **Goal:** Build FTP with sustained threshold efforts
- **Key Workouts:** 2x20, 3x15 at 95-100% FTP, Over/Unders, long Z2 rides
- Monday: Rest
- Tuesday: **Threshold 2x20min** @100% FTP - 60-75min total
- Wednesday: Zone 2 Recovery (45-60min)
- Thursday: **Over/Under** intervals (105%/95% alternating) - 60-75min total
- Friday: Rest or Easy Spin (30-45min)
- Saturday: **Threshold 3x15min** @100% FTP - 60-75min total
- Sunday: **Long Zone 2** (120min) - Essential for recovery and aerobic base

### ENDURANCE:
- **Goal:** Aerobic base building through high volume low intensity
- **Key Workouts:** Multiple long Z2 rides (2hrs+), occasional Tempo
- **CRITICAL:** Both weekend days should be long rides (120-180min)
- Monday: Rest
- Tuesday: Zone 2 Endurance (60-75min)
- Wednesday: Zone 2 Endurance (75-90min)
- Thursday: Tempo (Zone 3) 30-45min in middle - 60-75min total
- Friday: Rest or Easy Spin (30-45min)
- Saturday: **Long Zone 2** (150-180min) - Essential for base building
- Sunday: **Long Zone 2** (120-150min) - Essential for base building
"""


WEEKLY_PLAN_PROMPT = """# Role
You are an expert Cycling Coach creating a structured 7-day training plan.

# Athlete Context
- **Training Style:** {training_style} - {training_style_description}
- **Training Focus:** {training_focus} ({focus_description})
- **Preferred Duration:** {preferred_duration} minutes per workout
- **Current CTL (Fitness):** {ctl:.1f}
- **Current ATL (Fatigue):** {atl:.1f}
- **Current TSB (Form):** {tsb:.1f} ({form_status})
- **Weekly TSS Target:** {weekly_tss_target}

# Week Planning: {week_start} to {week_end}

{weekly_structure}

# Available Workout Modules
Below is the COMPLETE library of workout modules you MUST use.
**CRITICAL:** You can ONLY use module keys from this list. Do NOT create, invent, or modify module names.
If a module you want doesn't exist, choose the closest alternative from this list.

## Module Length Categories:
- **SHORT** (<15min): Quick intervals, short blocks
- **MID** (15-45min): Standard interval sessions
- **LONG** (45-75min): Extended steady-state or long interval sets
- **VERYLONG** (75min+): Long endurance blocks (FatMax, Zone 2, Tempo)

## Building Long Workouts (120min+):
For 2-hour+ Zone 2/FatMax rides, use LONG/VERYLONG modules or combine multiple modules:
- Example 120min Z2: [ramp_standard, endurance_60min, endurance_45min, flush_and_fade]
- Example 150min Z2: [progressive_ramp_15min, endurance_60min, endurance_60min, flush_and_fade]
- Example 180min Z2: [ramp_standard, endurance_60min, endurance_60min, endurance_60min, flush_and_fade]
- Example 180min FatMax: [ramp_standard, fatmax_90min, fatmax_90min, flush_and_fade]
- Example 120min Tempo: [progressive_ramp_15min, tempo_60min, tempo_long_40min, flush_and_fade]

{module_inventory}

# Rules
1. **Structure - CRITICAL MODULE ORDER:**
   - **ALWAYS** follow this order: WARMUP modules → MAIN modules → COOLDOWN modules
   - **WARMUP modules MUST be FIRST** (e.g., ramp_standard, progressive_ramp_15min)
   - **COOLDOWN modules MUST be LAST** (e.g., flush_and_fade, cooldown_extended)
   - **NEVER** place cooldown modules at the beginning or warmup modules at the end
   - Example CORRECT order: ["ramp_standard", "endurance_60min", "flush_and_fade"]
   - Example WRONG order: ["flush_and_fade", "endurance_60min", "ramp_standard"] ❌
2. **Rest Days:** Include 1-2 complete rest days per week. For rest days, set type to "Rest" and modules to empty array.
3. **TSB Management:**
   - If TSB < -20: Prioritize recovery, reduce intensity
   - If TSB -10 to -20: Moderate volume, limit high intensity
   - If TSB > -10: Can include hard workouts
4. **Progressive Load:** Build intensity mid-week, recover on weekends or vice versa.
5. **Duration Guidelines:**
   - Weekday workouts: 45-90min (default: {preferred_duration} min)
   - Weekend long rides: 120-180min for Polarized, Endurance, Threshold styles
   - **CRITICAL for Polarized:** Must include at least ONE 2-hour Zone 2 ride, preferably TWO (Saturday + Sunday)
   - High-intensity workouts (VO2max, Threshold): 60-75min total (including warmup/cooldown)
6. **Style Emphasis:** Strongly favor workouts that match the training style.
7. **Norwegian Double Sessions:** For Norwegian style, generate TWO separate workout entries for the same day when there's AM + PM sessions. Use "session": "AM" or "session": "PM" to differentiate.
8. **TSS Calculation:** TSS = (duration_hours × IF²) × 100, where IF = average_intensity / FTP
   - Recovery (50-60% FTP): 60min = ~25 TSS
   - Endurance (65-75% FTP): 60min = ~50 TSS
   - Tempo (80-90% FTP): 60min = ~70 TSS
   - Sweet Spot (88-94% FTP): 60min = ~80 TSS
   - Threshold (95-105% FTP): 60min = ~100 TSS
   - VO2max (110-120% FTP): 30min intervals only = ~60-80 TSS total
   - NEVER exceed TSS 100 for 60min workout unless it's pure threshold
   - Long endurance rides: 120min at 70% = ~100 TSS, 180min = ~150 TSS

# Output Format
Generate a JSON array with daily plans. For Norwegian style with double sessions, you may have more than 7 entries:

```json
[
  {{
    "day_index": 0,
    "day_name": "Monday",
    "date": "2026-01-13",
    "session": "AM|PM|null",
    "workout_type": "Recovery|Endurance|Tempo|SweetSpot|Threshold|VO2max|Rest",
    "workout_name": "Creative descriptive name",
    "duration_minutes": 60,
    "estimated_tss": 45,
    "intensity": "easy|moderate|hard|rest",
    "selected_modules": ["warmup_key", "main_key", "rest_key", "main_key", "cooldown_key"],
    "rationale": "Brief explanation of why this workout on this day"

    **CRITICAL for selected_modules - ORDER MATTERS:**
    - **FIRST:** Always start with WARMUP module (ramp_standard, progressive_ramp_15min, etc.)
    - **MIDDLE:** Main workout modules (intervals, endurance blocks, etc.)
    - **LAST:** Always end with COOLDOWN module (flush_and_fade, cooldown_extended, etc.)
    - Use ONLY module keys from the inventory above
    - DO NOT invent or modify module names

    **Examples:**
    ✅ CORRECT: ["ramp_standard", "sst_2x20", "rest_5min", "sst_2x20", "flush_and_fade"]
    ✅ CORRECT: ["progressive_ramp_15min", "endurance_60min", "endurance_45min", "flush_and_fade"]
    ❌ WRONG: ["flush_and_fade", "endurance_60min", "ramp_standard"] (cooldown at start!)
    ❌ WRONG: ["endurance_60min", "cooldown_extended", "ramp_standard"] (warmup at end!)
    ❌ WRONG: ["progressive_warmup_20min", "custom_interval"] (modules don't exist)
  }},
  ...
]
```

Generate the plan now.
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
    session: Optional[str] = None  # "AM", "PM", or None for single session


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

        # Calculate weekly TSS target based on CTL and training focus
        base_tss = int(ctl * 7)  # Base estimate

        # Apply training focus multiplier
        training_focus = self.profile.get("training_focus", "maintain")
        focus_multipliers = {
            "recovery": 0.7,  # -30% for recovery week
            "maintain": 1.0,  # Keep current load
            "build": 1.1,  # +10% for building phase
        }
        multiplier = focus_multipliers.get(training_focus, 1.0)
        weekly_tss_target = int(base_tss * multiplier)

        # Get module inventory with style-aware recommendations
        from src.services.workout_modules import get_module_inventory_text

        module_inventory = get_module_inventory_text(
            exclude_barcode=exclude_barcode, training_style=training_style
        )

        # Build prompt
        focus_descriptions = {
            "recovery": "Recovery week - reduce load and intensity",
            "maintain": "Maintain current fitness level",
            "build": "Build phase - progressively increase load",
        }
        focus_description = focus_descriptions.get(training_focus, "Maintain")

        prompt = WEEKLY_PLAN_PROMPT.format(
            training_style=training_style,
            training_style_description=training_style_desc,
            training_focus=training_focus,
            focus_description=focus_description,
            preferred_duration=self.profile.get("preferred_duration", 60),
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

        # Generate with LLM (with retry on parse failure)
        max_retries = 2
        for attempt in range(max_retries):
            response = self.llm.generate(
                system_prompt=prompt,
                user_prompt="Generate the 7-day workout plan now. Output ONLY valid JSON array, no markdown or extra text.",
            )

            # Parse response
            daily_plans = self._parse_response(response, week_start)

            # Check if we got fallback plan (indicates parse failure)
            if (
                daily_plans
                and daily_plans[0].rationale != "Fallback plan - AI generation failed"
            ):
                # Successfully parsed
                break
            elif attempt < max_retries - 1:
                logger.warning(f"Parse failed on attempt {attempt + 1}, retrying...")
            else:
                logger.error(f"All {max_retries} attempts failed, using fallback plan")

        # Calculate total TSS
        total_tss = sum(dp.estimated_tss for dp in daily_plans)

        return WeeklyPlan(
            week_start=week_start,
            week_end=week_end,
            training_style=training_style,
            total_planned_tss=total_tss,
            daily_plans=daily_plans,
        )

    def _validate_and_correct_tss(
        self, workout_type: str, duration_minutes: int, estimated_tss: int
    ) -> int:
        """Validate and correct TSS based on workout type and duration.

        TSS = (duration_hours × IF²) × 100
        where IF = average_intensity / FTP
        """
        duration_hours = duration_minutes / 60.0

        # Expected IF ranges for each workout type
        if_ranges = {
            "Rest": 0.0,
            "Recovery": 0.55,  # 50-60% FTP
            "Endurance": 0.70,  # 65-75% FTP
            "Tempo": 0.85,  # 80-90% FTP
            "SweetSpot": 0.91,  # 88-94% FTP
            "Threshold": 1.0,  # 95-105% FTP
            "VO2max": 1.15,  # 110-120% FTP (but short intervals)
        }

        # Get expected IF for workout type
        expected_if = if_ranges.get(workout_type, 0.70)

        # Calculate expected TSS
        expected_tss = int(duration_hours * (expected_if**2) * 100)

        # For VO2max, cap at reasonable values (short intervals, not continuous)
        if workout_type == "VO2max":
            # VO2max workouts are typically 30-40min of intervals, not full duration
            max_tss = int(duration_hours * 80)  # Cap at ~80 TSS per hour
            expected_tss = min(expected_tss, max_tss)

        # Check if LLM-provided TSS is reasonable (within 30% of expected)
        if estimated_tss == 0 and workout_type == "Rest":
            return 0

        tolerance = 0.3
        if abs(estimated_tss - expected_tss) / max(expected_tss, 1) > tolerance:
            logger.warning(
                f"TSS mismatch for {workout_type} {duration_minutes}min: "
                f"LLM={estimated_tss}, Expected={expected_tss}. Using corrected value."
            )
            return expected_tss

        return estimated_tss

    def _clean_json_string(self, json_str: str) -> str:
        """Clean common JSON formatting issues from LLM responses.

        Args:
            json_str: Raw JSON string that may have formatting issues

        Returns:
            Cleaned JSON string
        """
        # Remove trailing commas before closing brackets/braces (common LLM error)
        # Pattern: comma followed by optional whitespace and closing bracket/brace
        cleaned = re.sub(r",\s*(\]|\})", r"\1", json_str)

        # Remove JavaScript-style comments (// and /* */)
        cleaned = re.sub(r"//.*?(?=\n|$)", "", cleaned)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)

        # Fix unquoted keys (convert key: to "key":)
        cleaned = re.sub(r"(?<=[{\[,])\s*(\w+)\s*:", r' "\1":', cleaned)

        # Remove markdown code block markers if present
        cleaned = re.sub(r"^```json\s*", "", cleaned)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        return cleaned.strip()

    def _fix_module_order(self, modules: List[str]) -> List[str]:
        """Fix module order to ensure warmup first, cooldown last.

        Args:
            modules: List of module keys from LLM

        Returns:
            Reordered list with warmup modules first, cooldown modules last
        """
        from src.services.workout_modules import get_module_category

        if not modules:
            return modules

        warmup_modules = []
        main_modules = []
        cooldown_modules = []

        for module in modules:
            category = get_module_category(module)
            if category == "Warmup":
                warmup_modules.append(module)
            elif category == "Cooldown":
                cooldown_modules.append(module)
            else:
                main_modules.append(module)

        # Check if reordering is needed
        original_order = modules
        fixed_order = warmup_modules + main_modules + cooldown_modules

        if original_order != fixed_order:
            logger.warning(
                f"🔧 AUTO-FIX module order: {original_order} → {fixed_order}"
            )

        return fixed_order

    def _parse_response(self, response: str, week_start: date) -> List[DailyPlan]:
        """Parse LLM response into DailyPlan objects.

        Args:
            response: Raw LLM response
            week_start: Monday of the week

        Returns:
            List of 7 DailyPlan objects
        """
        # Extract JSON from response
        try:
            # Try to find JSON array in response
            json_match = re.search(r"\[[\s\S]*\]", response)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response

            # First attempt: parse as-is
            try:
                plans_data = json.loads(json_str)
            except json.JSONDecodeError:
                # Second attempt: clean JSON and retry
                logger.warning("Initial JSON parse failed, attempting cleanup...")
                cleaned_json = self._clean_json_string(json_str)
                plans_data = json.loads(cleaned_json)
                logger.info("JSON cleanup successful!")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse weekly plan response: {e}")
            logger.error(f"Response was: {response[:1000]}...")
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

        # For Norwegian style, we may have more than 7 entries (AM + PM sessions)
        for plan_data in plans_data:
            day_index = plan_data.get("day_index", 0)
            if day_index >= 7:
                continue  # Safety check

            workout_date = week_start + timedelta(days=day_index)
            workout_type = plan_data.get("workout_type", "Endurance")
            duration_minutes = plan_data.get("duration_minutes", 60)
            llm_tss = plan_data.get("estimated_tss", 50)

            # Validate and correct TSS if needed
            corrected_tss = self._validate_and_correct_tss(
                workout_type, duration_minutes, llm_tss
            )

            # Validate and fix module order (warmup first, cooldown last)
            selected_modules = plan_data.get("selected_modules", [])
            if selected_modules:
                selected_modules = self._fix_module_order(selected_modules)

            daily_plans.append(
                DailyPlan(
                    day_index=day_index,
                    day_name=day_names[day_index],
                    workout_date=workout_date,
                    workout_type=workout_type,
                    workout_name=plan_data.get(
                        "workout_name", f"Day {day_index+1} Workout"
                    ),
                    duration_minutes=duration_minutes,
                    estimated_tss=corrected_tss,
                    intensity=plan_data.get("intensity", "moderate"),
                    selected_modules=selected_modules,
                    rationale=plan_data.get("rationale", ""),
                    session=plan_data.get("session"),  # AM, PM, or None
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
