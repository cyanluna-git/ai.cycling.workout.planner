import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { WellnessMetrics } from "@/lib/api";

interface WellnessCardProps {
    wellness: WellnessMetrics;
    className?: string;
}

// Helper function to get rating color (1-5 scale, lower is better for soreness/fatigue/stress)
const getRatingColor = (value: number | null, invertScale: boolean = true) => {
    if (value === null) return "text-muted-foreground";
    if (invertScale) {
        // lower is better (soreness, fatigue, stress)
        if (value <= 2) return "text-green-500";
        if (value <= 3) return "text-yellow-500";
        return "text-red-500";
    } else {
        // higher is better (mood, motivation)
        if (value >= 4) return "text-green-500";
        if (value >= 3) return "text-yellow-500";
        return "text-red-500";
    }
};

// Helper function to get rating emoji
const getRatingEmoji = (value: number | null, invertScale: boolean = true) => {
    if (value === null) return "—";
    if (invertScale) {
        if (value <= 2) return "😊";
        if (value <= 3) return "😐";
        return "😓";
    } else {
        if (value >= 4) return "🔥";
        if (value >= 3) return "😐";
        return "😴";
    }
};

export function WellnessCard({ wellness, className }: WellnessCardProps) {
    const { t } = useTranslation();
    const hasSubjectiveData = wellness.soreness != null || wellness.fatigue != null || wellness.stress != null || wellness.mood != null || wellness.motivation != null;
    const hasHealthData = wellness.spo2 != null || wellness.systolic != null || wellness.respiration != null;
    const hasSleepData = wellness.sleep_hours != null || wellness.sleep_score != null;

    return (
        <Card className={className}>
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                    {t('wellnessCard.title')}
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Primary Metrics Row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {wellness.hrv != null && (
                        <div className="text-center p-2 bg-muted/50 rounded-lg">
                            <div className="text-xs text-muted-foreground">HRV</div>
                            <div className="text-xl font-bold text-blue-500">{wellness.hrv.toFixed(0)}</div>
                            <div className="text-[10px] text-muted-foreground">ms</div>
                        </div>
                    )}
                    {wellness.rhr != null && (
                        <div className="text-center p-2 bg-muted/50 rounded-lg">
                            <div className="text-xs text-muted-foreground">{t('wellnessCard.restingHR')}</div>
                            <div className="text-xl font-bold">{wellness.rhr}</div>
                            <div className="text-[10px] text-muted-foreground">bpm</div>
                        </div>
                    )}
                    {wellness.vo2max != null && (
                        <div className="text-center p-2 bg-muted/50 rounded-lg">
                            <div className="text-xs text-muted-foreground">VO2max</div>
                            <div className="text-xl font-bold text-emerald-500">{wellness.vo2max.toFixed(1)}</div>
                            <div className="text-[10px] text-muted-foreground">ml/kg/min</div>
                        </div>
                    )}
                    {wellness.weight != null && (
                        <div className="text-center p-2 bg-muted/50 rounded-lg">
                            <div className="text-xs text-muted-foreground">{t('wellnessCard.weight')}</div>
                            <div className="text-xl font-bold">{wellness.weight.toFixed(1)}</div>
                            <div className="text-[10px] text-muted-foreground">kg</div>
                        </div>
                    )}
                </div>

                {/* Sleep Section */}
                {hasSleepData && (
                    <div className="space-y-2">
                        <div className="text-sm font-medium flex items-center gap-1">
                            {t('wellnessCard.sleepTitle')}
                        </div>
                        <div className="flex flex-wrap gap-4">
                            {wellness.sleep_hours != null && (
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-muted-foreground">{t('wellnessCard.sleepHours')}</span>
                                    <span className={`font-bold ${wellness.sleep_hours >= 7 ? 'text-green-500' : wellness.sleep_hours >= 6 ? 'text-yellow-500' : 'text-red-500'}`}>
                                        {wellness.sleep_hours.toFixed(1)}{t('common.hours')}
                                    </span>
                                </div>
                            )}
                            {wellness.sleep_score != null && (
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-muted-foreground">{t('wellnessCard.sleepScore')}</span>
                                    <span className={`font-bold ${wellness.sleep_score >= 80 ? 'text-green-500' : wellness.sleep_score >= 60 ? 'text-yellow-500' : 'text-red-500'}`}>
                                        {wellness.sleep_score.toFixed(0)}{t("common.points")}
                                    </span>
                                </div>
                            )}
                            {wellness.sleep_quality != null && (
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-muted-foreground">{t('wellnessCard.sleepQuality')}</span>
                                    <span className="font-bold">{wellness.sleep_quality}/5</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Subjective Ratings */}
                {hasSubjectiveData && (
                    <div className="space-y-2">
                        <div className="text-sm font-medium flex items-center gap-1">
                            {t('wellnessCard.subjectiveTitle')}
                        </div>
                        <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
                            {wellness.fatigue !== null && (
                                <div className="text-center p-2 bg-muted/30 rounded">
                                    <div className="text-[10px] text-muted-foreground">{t('wellnessCard.fatigue')}</div>
                                    <div className={`font-bold ${getRatingColor(wellness.fatigue)}`}>
                                        {getRatingEmoji(wellness.fatigue)} {wellness.fatigue}/5
                                    </div>
                                </div>
                            )}
                            {wellness.soreness !== null && (
                                <div className="text-center p-2 bg-muted/30 rounded">
                                    <div className="text-[10px] text-muted-foreground">{t('wellnessCard.soreness')}</div>
                                    <div className={`font-bold ${getRatingColor(wellness.soreness)}`}>
                                        {getRatingEmoji(wellness.soreness)} {wellness.soreness}/5
                                    </div>
                                </div>
                            )}
                            {wellness.stress !== null && (
                                <div className="text-center p-2 bg-muted/30 rounded">
                                    <div className="text-[10px] text-muted-foreground">{t('wellnessCard.stress')}</div>
                                    <div className={`font-bold ${getRatingColor(wellness.stress)}`}>
                                        {getRatingEmoji(wellness.stress)} {wellness.stress}/5
                                    </div>
                                </div>
                            )}
                            {wellness.mood !== null && (
                                <div className="text-center p-2 bg-muted/30 rounded">
                                    <div className="text-[10px] text-muted-foreground">{t('wellnessCard.mood')}</div>
                                    <div className={`font-bold ${getRatingColor(wellness.mood, false)}`}>
                                        {getRatingEmoji(wellness.mood, false)} {wellness.mood}/5
                                    </div>
                                </div>
                            )}
                            {wellness.motivation !== null && (
                                <div className="text-center p-2 bg-muted/30 rounded">
                                    <div className="text-[10px] text-muted-foreground">{t('wellnessCard.motivation')}</div>
                                    <div className={`font-bold ${getRatingColor(wellness.motivation, false)}`}>
                                        {getRatingEmoji(wellness.motivation, false)} {wellness.motivation}/5
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Health Metrics */}
                {hasHealthData && (
                    <div className="space-y-2">
                        <div className="text-sm font-medium flex items-center gap-1">
                            {t('wellnessCard.healthTitle')}
                        </div>
                        <div className="flex flex-wrap gap-4">
                            {wellness.spo2 != null && (
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-muted-foreground">SpO2</span>
                                    <span className={`font-bold ${wellness.spo2 >= 95 ? 'text-green-500' : 'text-yellow-500'}`}>
                                        {wellness.spo2.toFixed(0)}%
                                    </span>
                                </div>
                            )}
                            {wellness.systolic != null && wellness.diastolic != null && (
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-muted-foreground">{t('wellnessCard.bloodPressure')}</span>
                                    <span className="font-bold">{wellness.systolic}/{wellness.diastolic}</span>
                                    <span className="text-xs text-muted-foreground">mmHg</span>
                                </div>
                            )}
                            {wellness.respiration != null && (
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-muted-foreground">{t('wellnessCard.respiration')}</span>
                                    <span className="font-bold">{wellness.respiration.toFixed(1)}</span>
                                    <span className="text-xs text-muted-foreground">{t("wellnessCard.perMinute")}</span>
                                </div>
                            )}
                            {wellness.body_fat != null && (
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-muted-foreground">{t('wellnessCard.bodyFat')}</span>
                                    <span className="font-bold">{wellness.body_fat.toFixed(1)}%</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Readiness */}
                <div className="pt-2 border-t">
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">{t('wellnessCard.readiness')}</span>
                        <span className={`font-medium ${wellness.readiness.includes("Good") ? "text-green-500" :
                            wellness.readiness.includes("Poor") ? "text-red-500" :
                                "text-yellow-500"
                            }`}>
                            {wellness.readiness}
                        </span>
                    </div>
                    {wellness.readiness_score != null && (
                        <div className="mt-1">
                            <div className="w-full bg-muted rounded-full h-2">
                                <div
                                    className={`h-2 rounded-full ${wellness.readiness_score >= 70 ? 'bg-green-500' :
                                        wellness.readiness_score >= 50 ? 'bg-yellow-500' :
                                            'bg-red-500'
                                        }`}
                                    style={{ width: `${Math.min(100, wellness.readiness_score)}%` }}
                                />
                            </div>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
