/**
 * Unit tests for getBlendedReadiness — Kanban #372
 */

import { describe, it, expect } from "vitest";
import { getBlendedReadiness } from "./readiness";

describe("getBlendedReadiness", () => {
    // -----------------------------------------------------------------------
    // Case 1: No wellness data — TSB-only
    // -----------------------------------------------------------------------

    it("returns formStatus with no sub-text when wellness readiness is null", () => {
        const result = getBlendedReadiness(12, "Fresh", null);
        expect(result.label).toBe("Fresh");
        expect(result.subText).toBeNull();
    });

    it("returns formStatus with no sub-text when wellness readiness is empty string", () => {
        const result = getBlendedReadiness(-5, "Fatigued", "");
        expect(result.label).toBe("Fatigued");
        expect(result.subText).toBeNull();
    });

    it("returns formStatus with no sub-text when wellness readiness is undefined", () => {
        const result = getBlendedReadiness(0, "Moderate", undefined);
        expect(result.label).toBe("Moderate");
        expect(result.subText).toBeNull();
    });

    // -----------------------------------------------------------------------
    // Case 2: Numeric blend (readinessScore is a number)
    // -----------------------------------------------------------------------

    it("blends TSB and high readiness_score into 'Good'", () => {
        // TSB=+12 -> tsbNorm = (12+30)/60*100 = 70, clamped to 70
        // readinessScore=80
        // blended = 70*0.4 + 80*0.6 = 28 + 48 = 76 -> "Good"
        const result = getBlendedReadiness(12, "Fresh", "Good", 80);
        expect(result.label).toBe("Good");
        expect(result.subText).toBe("TSB: +12 / Wellness: Good");
    });

    it("blends negative TSB and moderate readiness_score into 'Moderate'", () => {
        // TSB=-10 -> tsbNorm = (-10+30)/60*100 = 33.33
        // readinessScore=50
        // blended = 33.33*0.4 + 50*0.6 = 13.33 + 30 = 43.33 -> "Moderate"
        const result = getBlendedReadiness(-10, "Stale", "Moderate", 50);
        expect(result.label).toBe("Moderate");
        expect(result.subText).toBe("TSB: -10 / Wellness: Moderate");
    });

    it("blends very negative TSB and low readiness_score into 'Poor'", () => {
        // TSB=-25 -> tsbNorm = (-25+30)/60*100 = 8.33
        // readinessScore=20
        // blended = 8.33*0.4 + 20*0.6 = 3.33 + 12 = 15.33 -> "Poor"
        const result = getBlendedReadiness(-25, "Very Stale", "Very Fatigued", 20);
        expect(result.label).toBe("Poor");
        expect(result.subText).toBe("TSB: -25 / Wellness: Very Fatigued");
    });

    it("treats readiness_score of 0 as valid numeric (not falsy)", () => {
        // TSB=+5 -> tsbNorm = (5+30)/60*100 = 58.33
        // readinessScore=0
        // blended = 58.33*0.4 + 0*0.6 = 23.33 -> "Poor"
        const result = getBlendedReadiness(5, "Fresh", "Poor", 0);
        expect(result.label).toBe("Poor");
        expect(result.subText).toBe("TSB: +5 / Wellness: Poor");
    });

    // -----------------------------------------------------------------------
    // Case 3: Wellness text only (readinessScore is null)
    // -----------------------------------------------------------------------

    it("uses wellness text label when readiness_score is null", () => {
        const result = getBlendedReadiness(8, "Fresh", "Very Fatigued", null);
        expect(result.label).toBe("Very Fatigued");
        expect(result.subText).toBe("TSB: +8 / Wellness: Very Fatigued");
    });

    it("uses wellness text label when readiness_score is undefined", () => {
        const result = getBlendedReadiness(-3, "Stale", "Moderate", undefined);
        expect(result.label).toBe("Moderate");
        expect(result.subText).toBe("TSB: -3 / Wellness: Moderate");
    });

    // -----------------------------------------------------------------------
    // Edge: TSB sign formatting
    // -----------------------------------------------------------------------

    it("formats TSB=0 with '+' prefix in sub-text", () => {
        const result = getBlendedReadiness(0, "Neutral", "Good", 70);
        expect(result.subText).toContain("TSB: +0");
    });

    // -----------------------------------------------------------------------
    // Edge: TSB clamping
    // -----------------------------------------------------------------------

    it("clamps extreme positive TSB to 100 in normalization", () => {
        // TSB=+50 -> tsbNorm = (50+30)/60*100 = 133.33 -> clamped to 100
        // readinessScore=100
        // blended = 100*0.4 + 100*0.6 = 100 -> "Good"
        const result = getBlendedReadiness(50, "Very Fresh", "Good", 100);
        expect(result.label).toBe("Good");
    });

    it("clamps extreme negative TSB to 0 in normalization", () => {
        // TSB=-40 -> tsbNorm = (-40+30)/60*100 = -16.67 -> clamped to 0
        // readinessScore=10
        // blended = 0*0.4 + 10*0.6 = 6 -> "Poor"
        const result = getBlendedReadiness(-40, "Very Stale", "Very Fatigued", 10);
        expect(result.label).toBe("Poor");
    });

    // -----------------------------------------------------------------------
    // Edge: blendedLabel boundary values (score = 65 and score = 35 exactly)
    // -----------------------------------------------------------------------

    it("returns 'Good' when blended score is exactly 65 (lower boundary of Good)", () => {
        // We need blended = tsbNorm*0.4 + readinessScore*0.6 = 65
        // TSB=+30 -> tsbNorm=100; readinessScore = (65 - 100*0.4) / 0.6 = (65-40)/0.6 = 41.67
        // blended = 100*0.4 + 41.67*0.6 = 40 + 25 = 65 -> "Good"
        const result = getBlendedReadiness(30, "Fresh", "Moderate", 41.67);
        expect(result.label).toBe("Good");
    });

    it("returns 'Moderate' when blended score is exactly 35 (lower boundary of Moderate)", () => {
        // TSB=+30 -> tsbNorm=100; readinessScore = (35 - 100*0.4) / 0.6 = (35-40)/0.6 = -8.33
        // That's negative — use a simpler setup instead:
        // TSB=0 -> tsbNorm = (0+30)/60*100 = 50
        // readinessScore = (35 - 50*0.4) / 0.6 = (35-20)/0.6 = 25
        // blended = 50*0.4 + 25*0.6 = 20 + 15 = 35 -> "Moderate"
        const result = getBlendedReadiness(0, "Neutral", "Moderate", 25);
        expect(result.label).toBe("Moderate");
    });

    // -----------------------------------------------------------------------
    // Edge: fractional TSB is rounded in sub-text
    // -----------------------------------------------------------------------

    it("rounds fractional TSB in sub-text display", () => {
        // TSB=6.7 should show as +7 in sub-text
        const result = getBlendedReadiness(6.7, "Fresh", "Good", 80);
        expect(result.subText).toContain("TSB: +7");
    });

    it("rounds negative fractional TSB in sub-text display", () => {
        // TSB=-3.4 should show as -3 in sub-text
        const result = getBlendedReadiness(-3.4, "Stale", "Moderate", 50);
        expect(result.subText).toContain("TSB: -3");
    });

    // -----------------------------------------------------------------------
    // Edge: TSB exactly at normalization boundary values (-30 and +30)
    // -----------------------------------------------------------------------

    it("maps TSB=+30 to tsbNorm=100 (upper boundary, not clamped)", () => {
        // TSB=+30 -> tsbNorm = (30+30)/60*100 = 100 exactly, no clamping needed
        // readinessScore=100
        // blended = 100*0.4 + 100*0.6 = 100 -> "Good"
        const result = getBlendedReadiness(30, "Very Fresh", "Good", 100);
        expect(result.label).toBe("Good");
    });

    it("maps TSB=-30 to tsbNorm=0 (lower boundary, not clamped)", () => {
        // TSB=-30 -> tsbNorm = (-30+30)/60*100 = 0 exactly
        // readinessScore=10
        // blended = 0*0.4 + 10*0.6 = 6 -> "Poor"
        const result = getBlendedReadiness(-30, "Very Stale", "Very Fatigued", 10);
        expect(result.label).toBe("Poor");
    });
});
