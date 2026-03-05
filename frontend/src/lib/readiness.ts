/**
 * Blended readiness logic — merges TSB-based form status with wellness readiness
 * into a single, non-contradictory label.
 *
 * Kanban #372
 */

export interface BlendedReadiness {
    label: string;
    subText: string | null;
}

/**
 * Clamp a number between min and max (inclusive).
 */
function clamp(value: number, min: number, max: number): number {
    return Math.min(max, Math.max(min, value));
}

/**
 * Map a blended 0-100 score to a human-readable label.
 */
function blendedLabel(score: number): string {
    if (score >= 65) return "Good";
    if (score >= 35) return "Moderate";
    return "Poor";
}

/**
 * Produce a single blended readiness result from TSB + wellness signals.
 *
 * Rules:
 * 1. If wellness readiness is null or empty string -> TSB-only (formStatus), no sub-text
 * 2. If readinessScore is a number (including 0) -> numeric blend (TSB 40% + wellness 60%)
 * 3. If readinessScore is null but wellness text exists -> use wellness text as label
 *
 * Cases 2 & 3 include sub-text showing both sources.
 */
export function getBlendedReadiness(
    tsb: number,
    formStatus: string,
    wellnessReadiness: string | null | undefined,
    readinessScore?: number | null,
): BlendedReadiness {
    // Case 1: no wellness data
    if (wellnessReadiness == null || wellnessReadiness === "") {
        return { label: formStatus, subText: null };
    }

    const tsbSign = tsb >= 0 ? "+" : "";
    const subText = `TSB: ${tsbSign}${Math.round(tsb)} / Wellness: ${wellnessReadiness}`;

    // Case 2: numeric blend (readinessScore is a number, including 0)
    if (typeof readinessScore === "number") {
        // Normalize TSB from roughly [-30, +30] range to 0-100
        const tsbNorm = clamp((tsb + 30) / 60 * 100, 0, 100);
        const blended = tsbNorm * 0.4 + readinessScore * 0.6;
        return { label: blendedLabel(blended), subText };
    }

    // Case 3: wellness text only (readinessScore is null/undefined)
    return { label: wellnessReadiness, subText };
}
