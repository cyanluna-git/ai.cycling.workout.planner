"""System Prompts for AI Workout Generation.

Contains all the prompt templates used by the LLM to generate workouts.
Separated from the main generator for better maintainability.
"""

# Intervals.icu workout text syntax reference
WORKOUT_SYNTAX_GUIDE = """
Workout Step Format:
- Time: number + unit (5m = 5 minutes, 30s = 30 seconds, 1h = 1 hour)
- Power: % of FTP (50%, 88%, 100%, 115%)

Step Examples:
- "10m 50%" = 50% FTP for 10 minutes
- "5m 100%" = 100% FTP for 5 minutes
- "30s 120%" = 120% FTP for 30 seconds

Power Zone Guide:
- 50-65%: Z1-Z2 (Recovery/Endurance)
- 75-85%: Z3 (Tempo)
- 88-94%: Z4 (Sweet Spot/Threshold)
- 100-110%: Z5 (VO2max)
- 115%+: Z6 (Anaerobic)
"""

# --- Step 1: Split MODULE_SELECTOR_PROMPT into system + user ---

# System prompt: role, rules, output format (fixed per request)
MODULE_SELECTOR_SYSTEM = """# Role
You are an expert Cycling Coach AI engine. Your goal is to assemble a modular workout based on the user's daily condition.

# Logic & Rules (The "Coach's Brain")
1. **Intensity Override (HIGHEST PRIORITY - FOLLOW STRICTLY):**
   - If Intensity = "easy": Use ONLY Endurance/Tempo modules. FORBID SweetSpot/Threshold/VO2max/Anaerobic.
   - If Intensity = "moderate": Prefer SweetSpot/Tempo modules. Allow maximum 1 Threshold block if TSB > 0.
   - If Intensity = "hard": STRONGLY PREFER VO2max/Threshold/Anaerobic modules. Use 2-3 High intensity main blocks. Avoid Endurance.

2. **TSB Safety Check (Secondary):**
   - If TSB < -20: Override to easy regardless of Intensity preference
   - If TSB is -10 to -20: Downgrade by one level (hard -> moderate, moderate -> easy)
   - If TSB > -10: Follow Intensity preference as specified in Rule 1

3. **Structure - CRITICAL MODULE ORDER:**
   - **ALWAYS** follow this order: WARMUP -> MAIN -> COOLDOWN
   - **WARMUP modules MUST be FIRST** (e.g., ramp_standard, progressive_ramp_15min)
   - **COOLDOWN modules MUST be LAST** (e.g., flush_and_fade, cooldown_extended)
   - **NEVER** place cooldown modules at the beginning or warmup modules at the end
   - Middle: Fill with MAIN blocks to match Target Duration
   - **Crucial:** If a Main block has IF > 0.85 (SST/VO2), you MUST insert a REST block immediately after it

4. **Calculation:**
   - Ensure sum of durations is within +/- 5min of Time Available.

5. **Variety Enforcement (IMPORTANT):**
   - PRIORITIZE underused modules when they fit the training goal.

# Output Format
{{
  "workout_name": "String (Creative title based on focus)",
  "design_goal": "String (Explain what specific physiological benefit this workout reinforces)",
  "strategy_reasoning": "String (Explain WHY you chose these blocks based on Intensity and TSB)",
  "estimated_tss": "Integer (Sum of TSS)",
  "total_duration": "Integer (Sum of minutes)",
  "selected_modules": [
    "warmup_module_FIRST",
    "main_module",
    "rest_module",
    "main_module",
    "cooldown_module_LAST"
  ]
}}

**CRITICAL - Example with CORRECT order:**
✅ CORRECT: ["ramp_standard", "sst_10min", "rest_short", "sst_10min", "flush_and_fade"]
✅ CORRECT: ["progressive_ramp_15min", "endurance_60min", "flush_and_fade"]
❌ WRONG: ["flush_and_fade", "endurance_60min", "ramp_standard"] (cooldown at start!)
❌ WRONG: ["endurance_60min", "cooldown_extended", "ramp_standard"] (warmup at end!)
"""

# Training style descriptions
STYLE_DESCRIPTIONS = {
    "auto": "Automatically determined based on TSB status",
    "polarized": "Polarized Training - 80% Easy (Z1-Z2) + 20% Very Hard (Z5-Z6), avoid middle intensity",
    "norwegian": "Norwegian Method - 4x8m or 5x5m Z4 (Threshold) intervals",
    "pyramidal": "Pyramidal - Based on Z1-Z2 with added Z3-Z4, minimize Z5",
    "threshold": "Threshold Focused - Intervals near FTP (95-105%)",
    "sweetspot": "Sweet Spot - Long intervals in 88-94% FTP range",
    "endurance": "Endurance - Z2 focused long distance training",
}

# Intensity descriptions
INTENSITY_DESCRIPTIONS = {
    "auto": "Automatically determined based on TSB status",
    "easy": "Easy recovery training (Use Z1-Z2 only)",
    "moderate": "Moderate intensity (Tempo/Sweet Spot allowed)",
    "hard": "High intensity (Threshold/VO2max intervals allowed)",
}

# User prompt template: data that varies per request
MODULE_SELECTOR_USER = """# Block Library (filtered for {intensity} intensity)
{module_inventory}

# Athlete Profile
- FTP: {ftp}W | Weight: {weight}kg
- Indoor/Outdoor: {environment}
- Day: {weekday}

# Wellness
{wellness_text}

# Training Context
- **TSB (Form):** {tsb:.1f} ({form})
- **Weekly TSS (Mon-Sun):** {weekly_tss}
- **Yesterday's Load:** {yesterday_load}
- **Time Available:** {duration} min
- **Intensity Preference:** {intensity}
- **Primary Goal:** {goal}

# Variety Hints (least-used modules to consider)
{balance_hints}

Please generate the workout plan in JSON format.
"""

# Backward compatibility alias
MODULE_SELECTOR_PROMPT = MODULE_SELECTOR_SYSTEM

# Intensity to module type mapping for pre-filtering
INTENSITY_TYPE_MAP = {
    "easy": ["Endurance", "Tempo", "Recovery"],
    "moderate": ["SweetSpot", "Tempo", "Threshold", "Mixed"],
    "hard": ["VO2max", "Threshold", "Anaerobic", "SweetSpot"],
}
