/**
 * Workout Utilities
 * 
 * Shared utility functions for workout-related operations.
 */

import { WORKOUT_PREFIX, AI_GENERATED_PREFIX } from "./constants";
import i18n from "@/i18n/config";

/**
 * Clean workout name by removing common prefixes.
 * 
 * @param name - Raw workout name from API
 * @returns Cleaned workout name
 */
export function cleanWorkoutName(name: string): string {
    return name
        .replace(WORKOUT_PREFIX, "")
        .replace(AI_GENERATED_PREFIX, "")
        .trim();
}

/**
 * Format duration in minutes to a readable string.
 * 
 * @param minutes - Duration in minutes
 * @returns Formatted string like "1h 30min" or "45min"
 */
export function formatDuration(minutes: number): string {
    if (minutes < 60) {
        return `${minutes}${i18n.t("common.minutes")}`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}${i18n.t("common.hours")} ${mins}${i18n.t("common.minutes")}` : `${hours}${i18n.t("common.hours")}`;
}

/**
 * Get zone color based on power percentage.
 * 
 * @param percent - Power as percentage of FTP
 * @returns Hex color string
 */
export function getZoneColor(percent: number): string {
    if (percent <= 55) return "#009e80";      // Z1 - Recovery
    if (percent <= 75) return "#009e00";      // Z2 - Endurance
    if (percent <= 90) return "#ffcb0e";      // Z3 - Tempo
    if (percent <= 105) return "#ff7f0e";     // Z4 - Threshold
    if (percent <= 120) return "#dd0447";     // Z5 - VO2 Max
    if (percent <= 150) return "#6633cc";     // Z6 - Anaerobic
    return "#504861";                          // Z7 - Neuromuscular
}

/**
 * Get zone number based on power percentage.
 * 
 * @param percent - Power as percentage of FTP
 * @returns Zone number (1-7)
 */
export function getZoneNumber(percent: number): number {
    if (percent <= 55) return 1;
    if (percent <= 75) return 2;
    if (percent <= 90) return 3;
    if (percent <= 105) return 4;
    if (percent <= 120) return 5;
    if (percent <= 150) return 6;
    return 7;
}
