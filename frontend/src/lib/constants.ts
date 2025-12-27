/**
 * Application Constants
 * 
 * Centralized constants for the AI Cycling Coach frontend.
 * Keep in sync with backend src/constants.py
 */

// Workout Naming
export const WORKOUT_PREFIX = "[AICoach]";
export const AI_GENERATED_PREFIX = "AI Generated - ";

// Default Values
export const DEFAULT_FTP = 250;

// Zone Colors (matching Intervals.icu)
export const ZONE_COLORS: Record<number, string> = {
    1: "#009e80",  // Active Recovery (0-55%)
    2: "#009e00",  // Endurance (56-75%)
    3: "#ffcb0e",  // Tempo (76-90%)
    4: "#ff7f0e",  // Threshold (91-105%)
    5: "#dd0447",  // VO2 Max (106-120%)
    6: "#6633cc",  // Anaerobic (121-150%)
    7: "#504861",  // Neuromuscular (151%+)
};

export const ZONE_THRESHOLDS = [55, 75, 90, 105, 120, 150, 999];
