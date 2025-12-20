import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TrainingMetrics, WellnessMetrics, AthleteProfile } from "@/lib/api";

interface FitnessCardProps {
    training: TrainingMetrics;
    wellness: WellnessMetrics;
    profile: AthleteProfile;
}

export function FitnessCard({ training, wellness, profile }: FitnessCardProps) {
    // TSB color based on value
    const getTsbColor = (tsb: number) => {
        if (tsb > 10) return "text-green-500";
        if (tsb > 0) return "text-blue-500";
        if (tsb > -10) return "text-yellow-500";
        return "text-red-500";
    };

    const getTsbEmoji = (tsb: number) => {
        if (tsb > 10) return "🚀";
        if (tsb > 0) return "✅";
        if (tsb > -10) return "😐";
        if (tsb > -20) return "😓";
        return "🛏️";
    };

    return (
        <Card className="w-full">
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                    📊 현재 훈련 상태
                </CardTitle>
            </CardHeader>
            <CardContent>
                {/* Profile Section */}
                <div className="flex flex-wrap gap-3 mb-4 p-3 bg-muted/50 rounded-lg">
                    {profile.ftp && (
                        <div className="flex items-center gap-1">
                            <span className="text-xs text-muted-foreground">FTP</span>
                            <span className="font-bold">{profile.ftp}W</span>
                        </div>
                    )}
                    {profile.w_per_kg && (
                        <div className="flex items-center gap-1">
                            <span className="text-xs text-muted-foreground">W/kg</span>
                            <span className="font-bold text-blue-500">{profile.w_per_kg}</span>
                        </div>
                    )}
                    {profile.max_hr && (
                        <div className="flex items-center gap-1">
                            <span className="text-xs text-muted-foreground">Max HR</span>
                            <span className="font-bold">{profile.max_hr}</span>
                        </div>
                    )}
                    {profile.lthr && (
                        <div className="flex items-center gap-1">
                            <span className="text-xs text-muted-foreground">LTHR</span>
                            <span className="font-bold">{profile.lthr}</span>
                        </div>
                    )}
                    {profile.weight && (
                        <div className="flex items-center gap-1">
                            <span className="text-xs text-muted-foreground">체중</span>
                            <span className="font-bold">{profile.weight}kg</span>
                        </div>
                    )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                    {/* Training Metrics */}
                    <div className="space-y-3">
                        <div className="flex justify-between items-baseline">
                            <span className="text-sm text-muted-foreground">CTL (체력)</span>
                            <span className="text-xl font-bold">{training.ctl.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between items-baseline">
                            <span className="text-sm text-muted-foreground">ATL (피로)</span>
                            <span className="text-xl font-bold">{training.atl.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between items-baseline">
                            <span className="text-sm text-muted-foreground">TSB (컨디션)</span>
                            <span className={`text-xl font-bold ${getTsbColor(training.tsb)}`}>
                                {getTsbEmoji(training.tsb)} {training.tsb.toFixed(1)}
                            </span>
                        </div>
                    </div>

                    {/* Wellness */}
                    <div className="space-y-3">
                        <div className="flex justify-between items-baseline">
                            <span className="text-sm text-muted-foreground">상태</span>
                            <span className="text-sm font-medium">{training.form_status}</span>
                        </div>
                        <div className="flex justify-between items-baseline">
                            <span className="text-sm text-muted-foreground">준비도</span>
                            <span className={`text-sm font-medium ${wellness.readiness.includes("Poor") ? "text-red-500" :
                                    wellness.readiness.includes("Good") ? "text-green-500" :
                                        "text-yellow-500"
                                }`}>
                                {wellness.readiness}
                            </span>
                        </div>
                        {wellness.hrv && (
                            <div className="flex justify-between items-baseline">
                                <span className="text-sm text-muted-foreground">HRV</span>
                                <span className="text-xl font-bold">{wellness.hrv}</span>
                            </div>
                        )}
                        {wellness.rhr && (
                            <div className="flex justify-between items-baseline">
                                <span className="text-sm text-muted-foreground">RHR</span>
                                <span className="text-xl font-bold">{wellness.rhr} bpm</span>
                            </div>
                        )}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

