/**
 * WeeklyProgressRing — SVG circular progress ring
 *
 * Renders a ring with stroke-dasharray/stroke-dashoffset.
 * Visually clamped at 100%; text shows actual value/max.
 * CSS transition: stroke-dashoffset 700ms ease-out.
 */

import { useState, useEffect, useRef } from "react";

interface WeeklyProgressRingProps {
    value: number;
    max: number;
    size?: number;
    strokeWidth?: number;
    color: string;
    label?: string;
}

export function WeeklyProgressRing({
    value,
    max,
    size = 64,
    strokeWidth = 5,
    color,
    label,
}: WeeklyProgressRingProps) {
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;

    const percentage = max > 0 ? Math.min((value / max) * 100, 100) : 0;
    const targetOffset = circumference - (percentage / 100) * circumference;

    // Mount animation: start fully undrawn, then animate to target
    const [animatedOffset, setAnimatedOffset] = useState<number>(circumference);
    const prevCircumference = useRef(circumference);

    useEffect(() => {
        // When circumference changes (size/strokeWidth change), reset without animation
        if (prevCircumference.current !== circumference) {
            prevCircumference.current = circumference;
        }
        const timer = setTimeout(() => {
            setAnimatedOffset(targetOffset);
        }, 50);
        return () => clearTimeout(timer);
    }, [targetOffset, circumference]);

    const displayOffset = animatedOffset;

    return (
        <div className="flex flex-col items-center gap-1">
            <div className="relative" style={{ width: size, height: size }}>
                <svg
                    width={size}
                    height={size}
                    className="transform -rotate-90"
                >
                    {/* Background circle */}
                    <circle
                        cx={size / 2}
                        cy={size / 2}
                        r={radius}
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={strokeWidth}
                        className="text-muted/30"
                    />
                    {/* Progress circle */}
                    <circle
                        cx={size / 2}
                        cy={size / 2}
                        r={radius}
                        fill="none"
                        stroke={color}
                        strokeWidth={strokeWidth}
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={displayOffset}
                        style={{ transition: "stroke-dashoffset 700ms ease-out" }}
                    />
                </svg>
                {/* Center text */}
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-[10px] font-semibold leading-none text-foreground">
                        {Math.round(max > 0 ? (value / max) * 100 : 0)}%
                    </span>
                </div>
            </div>
            {label && (
                <span className="text-[10px] text-muted-foreground leading-tight text-center">
                    {label}
                </span>
            )}
        </div>
    );
}
