You are an expert cycling coach.
Available Modules:
--- WARMUP MODULES ---
- [ramp_extended] Extended Warmup (15 min)
- [ramp_short] Quick Ramp (5 min)
- [ramp_standard] Standard Ramp (10 min)

--- MAIN SEGMENTS ---
- [attack_block] Attack Simulation (8 min, Mixed)
- [ciabatta_3x9] Ciabatta 3x9 (27 min, VO2max)
- [ciabatta_light] Ciabatta Light 40/20 (20 min, VO2max)
- [endurance_20min] Endurance 20min (20 min, Endurance)
- [hour_of_power] Hour of Power (30 min, Threshold)
- [ironman_spikes] Ironman Spikes (35 min, Endurance)
- [mesoburst_hiit] MesoBurst HIIT (15 min, VO2max)
- [micro_30_15] 30/15 Micro Intervals (10 min, VO2max)
- [micro_40_20] 40/20 Micro Intervals (10 min, VO2max)
- [over_under_3rep] Over/Under x3 (12 min, Threshold)
- [sst_10min] Sweet Spot 10min (10 min, SweetSpot)
- [sst_with_bumps] SST with Surges (12 min, SweetSpot)
- [tempo_15min] Tempo 15min (15 min, Endurance)
- [threshold_2x8] 2x8min Threshold (20 min, Threshold)
- [vo2_3x3] 3x3min VO2max (15 min, VO2max)
- [xert_over_under] Xert Over/Under (12 min, Threshold)

--- REST SEGMENTS ---
- [rest_active] Active Recovery (5 min)
- [rest_medium] Medium Rest (4 min)
- [rest_short] Short Rest (2 min)

--- COOLDOWN MODULES ---
- [flush_and_fade] Flush and Fade (15 min)
- [ramp_short] Quick Cooldown (5 min)
- [ramp_standard] Standard Cooldown (10 min)

User Profile:
- TSB: -12.5 (Fatigued)
- Target Duration: 90 min
- Goal: Endurance with some intensity

Task: Create a workout by selecting a sequence of module keys.
Rules:
1. Must start with a WARMUP module.
2. Must end with a COOLDOWN module.
3. Total duration must be within +/- 5 mins of target.
4. Select MAIN segments suitable for the user's form (TSB).
5. Include REST segments between hard main segments (VO2max, Threshold).
   - Use 'rest_short' (2m) or 'rest_medium' (4m).
   - Endurance/Steady blocks might not need rest intervals.

Output JSON:
{
  "workout_name": "Creative Name",
  "rationale": "Brief explanation",
  "selected_modules": ["key1", "key2", "rest_key", "key3", "cooldown_key"]
}
