/**
 * WorkoutDetailModal - Full workout details in modal popup
 * Shows power chart, step breakdown, TSS, rationale
 */

import { Lightbulb } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { WorkoutPreview } from '@/components/WorkoutPreview';
import type { DailyWorkout, GeneratedWorkout } from '@/lib/api';

interface WorkoutDetailModalProps {
    workout: DailyWorkout | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function WorkoutDetailModal({
    workout,
    open,
    onOpenChange
}: WorkoutDetailModalProps) {
    if (!workout || !workout.planned_steps) {
        return null;
    }

    // Convert DailyWorkout to GeneratedWorkout format for WorkoutPreview
    const generatedWorkout: GeneratedWorkout = {
        name: workout.planned_name || 'Workout',
        workout_type: workout.planned_type || 'Endurance',
        estimated_tss: workout.planned_tss || null,
        estimated_duration_minutes: workout.planned_duration || 60,
        workout_text: '', // Not needed for chart display
        warmup: [],
        main: [],
        cooldown: [],
        design_goal: workout.planned_rationale,
        steps: workout.planned_steps,
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>
                        {workout.day_name} - {workout.planned_name}
                    </DialogTitle>
                </DialogHeader>

                <div className="mt-4">
                    <WorkoutPreview
                        workout={generatedWorkout}
                        onRegister={() => {}}  // No registration from weekly plan view
                        isRegistering={false}
                    />
                </div>

                {workout.planned_rationale && (
                    <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                        <h3 className="font-semibold text-sm mb-2 flex items-center gap-1.5"><Lightbulb className="h-4 w-4" /> Rationale</h3>
                        <p className="text-sm text-gray-700">
                            {workout.planned_rationale}
                        </p>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
}
