/**
 * Coach Loading Animation
 * 
 * Engaging multi-step loading animation for AI workout generation.
 * Shows sequential steps with fade-in effects and completion checkmarks.
 */

import { useEffect, useState, type ReactNode } from "react";
import { BarChart3, Crosshair, PenLine, CalendarDays, Zap, CircleCheck } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface Step {
  icon: ReactNode;
  text: string;
}

interface CoachLoadingAnimationProps {
  steps?: Step[];
  intervalMs?: number;
}

const DEFAULT_STEPS: Step[] = [
  { icon: <BarChart3 className="h-6 w-6" />, text: "Analyzing your training data..." },
  { icon: <Crosshair className="h-6 w-6" />, text: "Selecting optimal workout..." },
  { icon: <PenLine className="h-6 w-6" />, text: "Writing coaching notes..." },
];

export function CoachLoadingAnimation({
  steps = DEFAULT_STEPS,
  intervalMs = 1000,
}: CoachLoadingAnimationProps) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < steps.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [steps.length, intervalMs]);

  return (
    <Card className="w-full bg-muted/30">
      <CardContent className="py-8 px-4">
        <div className="flex flex-col items-center justify-center space-y-4 min-h-[160px]">
          {steps.map((step, index) => {
            const isCompleted = index < currentStep;
            const isCurrent = index === currentStep;
            const isVisible = index <= currentStep;

            return (
              <div
                key={index}
                className={`flex items-center gap-3 transition-all duration-500 ${
                  isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
                }`}
              >
                {/* Icon or Checkmark */}
                <div className="min-w-[32px] flex items-center justify-center">
                  {isCompleted ? (
                    <CircleCheck className="h-6 w-6 text-green-600" />
                  ) : (
                    <span className={isCurrent ? "animate-pulse" : ""}>
                      {step.icon}
                    </span>
                  )}
                </div>

                {/* Text */}
                <div
                  className={`text-sm sm:text-base transition-colors ${
                    isCurrent
                      ? "text-foreground font-medium"
                      : isCompleted
                      ? "text-muted-foreground"
                      : "text-muted-foreground/60"
                  }`}
                >
                  {step.text}
                </div>

                {/* Pulsing dot for current step */}
                {isCurrent && (
                  <div className="ml-2 w-2 h-2 rounded-full bg-primary animate-pulse" />
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// Weekly plan variant with different messages
export function WeeklyPlanLoadingAnimation() {
  const WEEKLY_STEPS: Step[] = [
    { icon: <BarChart3 className="h-6 w-6" />, text: "Analyzing weekly metrics..." },
    { icon: <CalendarDays className="h-6 w-6" />, text: "Planning your training week..." },
    { icon: <Zap className="h-6 w-6" />, text: "Optimizing TSS distribution..." },
    { icon: <PenLine className="h-6 w-6" />, text: "Finalizing coach recommendations..." },
  ];

  return <CoachLoadingAnimation steps={WEEKLY_STEPS} intervalMs={1000} />;
}
