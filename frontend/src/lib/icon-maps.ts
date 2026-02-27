/**
 * Shared icon mappings for consistent icon usage across components.
 * All icons are from Lucide React.
 */

import type { ReactNode } from "react";
import {
  Moon,
  Sprout,
  Bike,
  Dumbbell,
  Cookie,
  Flame,
  Zap,
  Trophy,
  CircleCheck,
  Minus,
  XCircle,
  Clock,
  Crosshair,
  Smile,
  Target,
  PersonStanding,
  Waves,
  Rocket,
  TrendingDown,
  BedDouble,
} from "lucide-react";
import { createElement } from "react";

// --- Workout Type Icons ---
export type WorkoutType =
  | "Rest"
  | "Recovery"
  | "Endurance"
  | "Tempo"
  | "SweetSpot"
  | "Threshold"
  | "VO2max";

const WORKOUT_TYPE_ICON_MAP: Record<WorkoutType, typeof Bike> = {
  Rest: Moon,
  Recovery: Sprout,
  Endurance: Bike,
  Tempo: Dumbbell,
  SweetSpot: Cookie,
  Threshold: Flame,
  VO2max: Zap,
};

export function getWorkoutTypeIcon(
  type: string,
  className: string = "h-3.5 w-3.5"
): ReactNode {
  const Icon = WORKOUT_TYPE_ICON_MAP[type as WorkoutType] || Bike;
  return createElement(Icon, { className });
}

// --- Achievement / Status Icons ---
export type AchievementStatus =
  | "exceeded"
  | "achieved"
  | "partial"
  | "missed"
  | "in_progress"
  | "no_target";

const STATUS_ICON_MAP: Record<AchievementStatus, typeof Trophy> = {
  exceeded: Trophy,
  achieved: CircleCheck,
  partial: Minus,
  missed: XCircle,
  in_progress: Clock,
  no_target: Minus,
};

export function getStatusIcon(
  status: string,
  className: string = "h-3 w-3"
): ReactNode {
  const Icon = STATUS_ICON_MAP[status as AchievementStatus] || Minus;
  return createElement(Icon, { className });
}

// --- Intensity Icons ---
export type IntensityLevel = "auto" | "easy" | "moderate" | "hard";

const INTENSITY_ICON_MAP: Record<IntensityLevel, typeof Crosshair> = {
  auto: Crosshair,
  easy: Smile,
  moderate: Dumbbell,
  hard: Flame,
};

export function getIntensityIcon(
  intensity: string,
  className: string = "h-4 w-4"
): ReactNode {
  const Icon = INTENSITY_ICON_MAP[intensity as IntensityLevel] || Target;
  return createElement(Icon, { className });
}

// --- TSB Status Icons ---
export function getTsbIcon(
  tsb: number,
  className: string = "h-4 w-4 inline"
): ReactNode {
  if (tsb > 10) return createElement(Rocket, { className });
  if (tsb > 0) return createElement(CircleCheck, { className });
  if (tsb > -10) return createElement(Minus, { className });
  if (tsb > -20) return createElement(TrendingDown, { className });
  return createElement(BedDouble, { className });
}

// --- Event Type Icons (Calendar) ---
export function getEventTypeIcon(
  event: { workout_type?: string; category: string },
  className: string = "h-3 w-3"
): ReactNode {
  const t = (event.workout_type || event.category).toLowerCase();

  if (t.includes("run") || t.includes("walk"))
    return createElement(PersonStanding, { className });
  if (t.includes("swim")) return createElement(Waves, { className });
  if (t.includes("weight") || t.includes("strength"))
    return createElement(Dumbbell, { className });
  return createElement(Bike, { className });
}
