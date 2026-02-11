import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TrainingMetrics, WellnessMetrics, AthleteProfile } from "@/lib/api";

interface FitnessCardProps {
    training: TrainingMetrics;
    wellness: WellnessMetrics;
    profile: AthleteProfile;
}

export function FitnessCard({ training, wellness, profile }: FitnessCardProps) {
    const { t } = useTranslation();
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

    const getReadinessColor = (readiness: string) => {
        if (readiness.includes("Poor")) return "text-red-500";
        if (readiness.includes("Good")) return "text-green-500";
        return "text-yellow-500";
    };

    return (
        <Card className="w-full">
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                    {t('fitness.title')}
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Profile Section - Compact */}
                <div className="flex flex-wrap gap-3 p-3 bg-muted/50 rounded-lg text-sm">
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
                    {profile.weight && (
                        <div className="flex items-center gap-1">
                            <span className="text-xs text-muted-foreground">{t('fitness.weight')}</span>
                            <span className="font-bold">{profile.weight}kg</span>
                        </div>
                    )}
                    {profile.vo2max && (
                        <div className="flex items-center gap-1">
                            <span className="text-xs text-muted-foreground">VO2max</span>
                            <span className="font-bold text-emerald-500">{profile.vo2max.toFixed(1)}</span>
                        </div>
                    )}
                </div>

                {/* Training Load & Wellness - Two Columns */}
                <div className="grid grid-cols-2 gap-4">
                    {/* Left: Training Metrics */}
                    <div className="space-y-2">
                        <div className="text-xs font-medium text-muted-foreground mb-1">{t('fitness.trainingLoad')}</div>
                        <div className="flex justify-between items-baseline">
                            <span className="text-sm text-muted-foreground">{t('fitness.ctlLabel')}</span>
                            <span className="text-lg font-bold">{training.ctl.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between items-baseline">
                            <span className="text-sm text-muted-foreground">{t('fitness.atlLabel')}</span>
                            <span className="text-lg font-bold">{training.atl.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between items-baseline">
                            <span className="text-sm text-muted-foreground">TSB</span>
                            <span className={`text-lg font-bold ${getTsbColor(training.tsb)}`}>
                                {getTsbEmoji(training.tsb)} {training.tsb.toFixed(1)}
                            </span>
                        </div>
                    </div>

                    {/* Right: Wellness Metrics */}
                    <div className="space-y-2">
                        <div className="text-xs font-medium text-muted-foreground mb-1">{t('fitness.wellness')}</div>
                        {wellness.hrv && (
                            <div className="flex justify-between items-baseline">
                                <span className="text-sm text-muted-foreground">HRV</span>
                                <span className="text-lg font-bold text-blue-500">{wellness.hrv.toFixed(0)} ms</span>
                            </div>
                        )}
                        {wellness.rhr && (
                            <div className="flex justify-between items-baseline">
                                <span className="text-sm text-muted-foreground">{t('fitness.restingHR')}</span>
                                <span className="text-lg font-bold">{wellness.rhr} bpm</span>
                            </div>
                        )}
                        {wellness.sleep_hours && (
                            <div className="flex justify-between items-baseline">
                                <span className="text-sm text-muted-foreground">{t('fitness.sleep')}</span>
                                <span className={`text-lg font-bold ${wellness.sleep_hours >= 7 ? 'text-green-500' : wellness.sleep_hours >= 6 ? 'text-yellow-500' : 'text-red-500'}`}>
                                    {wellness.sleep_hours.toFixed(1)}h
                                </span>
                            </div>
                        )}
                        {wellness.sleep_score && !wellness.sleep_hours && (
                            <div className="flex justify-between items-baseline">
                                <span className="text-sm text-muted-foreground">{t('fitness.sleepScore')}</span>
                                <span className={`text-lg font-bold ${wellness.sleep_score >= 80 ? 'text-green-500' : wellness.sleep_score >= 60 ? 'text-yellow-500' : 'text-red-500'}`}>
                                    {wellness.sleep_score.toFixed(0)}점
                                </span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Readiness - Single Bottom Section */}
                <div className="pt-3 border-t">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                            <span className="text-sm text-muted-foreground">{t('fitness.readiness')}</span>
                            <span className="text-xs text-muted-foreground">{training.form_status}</span>
                        </div>
                        <span className={`font-bold ${getReadinessColor(wellness.readiness)}`}>
                            {wellness.readiness}
                        </span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
