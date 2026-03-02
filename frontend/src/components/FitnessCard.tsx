import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Info, ChevronRight, RefreshCw } from "lucide-react";
import { getTsbIcon } from "@/lib/icon-maps";
import type { TrainingMetrics, WellnessMetrics, AthleteProfile } from "@/lib/api";
import { FitnessTrendChart } from "@/components/FitnessTrendChart";

interface FitnessCardProps {
    training: TrainingMetrics;
    wellness: WellnessMetrics;
    profile: AthleteProfile;
    onRefresh?: () => void;
    isRefreshing?: boolean;
}

export function FitnessCard({ training, wellness, profile, onRefresh, isRefreshing }: FitnessCardProps) {
    const { t } = useTranslation();
    // TSB color based on value
    const getTsbColor = (tsb: number) => {
        if (tsb > 10) return "text-green-500";
        if (tsb > 0) return "text-blue-500";
        if (tsb > -10) return "text-yellow-500";
        return "text-red-500";
    };

    const getTsbIconNode = (tsb: number) => getTsbIcon(tsb, "h-4 w-4 inline");

    const getReadinessColor = (readiness: string) => {
        if (readiness.includes("Poor")) return "text-red-500";
        if (readiness.includes("Good")) return "text-green-500";
        return "text-yellow-500";
    };

    return (
        <Card className="w-full">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        {t('fitness.title')}
                    </CardTitle>
                    {onRefresh && (
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={onRefresh}
                            disabled={isRefreshing}
                            aria-label={t('fitness.refresh')}
                        >
                            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                        </Button>
                    )}
                </div>
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
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                    {/* Left: Training Metrics */}
                    <div className="space-y-2">
                        <div className="text-xs font-medium text-muted-foreground mb-1">{t('fitness.trainingLoad')}</div>
                        <div className="flex justify-between items-baseline">
                            <span className="text-sm text-muted-foreground">
                                {t('fitness.ctlLabel')}
                            </span>
                            <span className="text-lg font-bold">{training.ctl.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between items-baseline">
                            <span className="text-sm text-muted-foreground">
                                {t('fitness.atlLabel')}
                            </span>
                            <span className="text-lg font-bold">{training.atl.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between items-baseline">
                            <span className="text-sm text-muted-foreground">
                                TSB
                            </span>
                            <span className={`text-lg font-bold ${getTsbColor(training.tsb)} flex items-center gap-1`}>
                                {getTsbIconNode(training.tsb)} {training.tsb.toFixed(1)}
                            </span>
                        </div>
                    </div>

                    {/* Right: Wellness Metrics */}
                    <div className="space-y-2">
                        <div className="text-xs font-medium text-muted-foreground mb-1">{t('fitness.wellness')}</div>
                        {wellness.hrv == null && wellness.sleep_hours == null && wellness.rhr == null ? (
                            <div className="p-3 bg-muted/30 rounded-lg flex flex-col gap-1.5">
                                <div className="flex items-start gap-1.5">
                                    <Info className="h-3.5 w-3.5 mt-0.5 shrink-0 text-muted-foreground" />
                                    <span className="text-xs text-muted-foreground leading-relaxed">{t('fitness.wearableHint')}</span>
                                </div>
                                <a
                                    href="https://intervals.icu/settings"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs text-primary underline-offset-2 hover:underline ml-5"
                                >
                                    {t('fitness.wearableHintLink')}
                                </a>
                            </div>
                        ) : null}
                        {wellness.hrv != null && (
                            <div className="flex justify-between items-baseline">
                                <span className="text-sm text-muted-foreground">HRV</span>
                                <span className="text-lg font-bold text-blue-500">{wellness.hrv.toFixed(0)} ms</span>
                            </div>
                        )}
                        {wellness.rhr != null && (
                            <div className="flex justify-between items-baseline">
                                <span className="text-sm text-muted-foreground">{t('fitness.restingHR')}</span>
                                <span className="text-lg font-bold">{wellness.rhr} bpm</span>
                            </div>
                        )}
                        {wellness.sleep_hours != null && (
                            <div className="flex justify-between items-baseline">
                                <span className="text-sm text-muted-foreground">{t('fitness.sleep')}</span>
                                <span className={`text-lg font-bold ${wellness.sleep_hours >= 7 ? 'text-green-500' : wellness.sleep_hours >= 6 ? 'text-yellow-500' : 'text-red-500'}`}>
                                    {wellness.sleep_hours.toFixed(1)}h
                                </span>
                            </div>
                        )}
                        {wellness.sleep_score != null && wellness.sleep_hours == null && (
                            <div className="flex justify-between items-baseline">
                                <span className="text-sm text-muted-foreground">{t('fitness.sleepScore')}</span>
                                <span className={`text-lg font-bold ${wellness.sleep_score >= 80 ? 'text-green-500' : wellness.sleep_score >= 60 ? 'text-yellow-500' : 'text-red-500'}`}>
                                    {wellness.sleep_score.toFixed(0)}{t("common.points")}
                                </span>
                            </div>
                        )}
                    </div>
                </div>

                {/* CTL/ATL/TSB Trend Chart */}
                {training.ctl_history && training.ctl_history.length > 0 && (
                    <div>
                        <div className="text-xs font-medium text-muted-foreground mb-2">{t('fitness.trendTitle')}</div>
                        <FitnessTrendChart history={training.ctl_history} />
                    </div>
                )}

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

                {/* NEW: Glossary Section */}
                <details className="mt-4 pt-4 border-t">
                    <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2">
                        <Info className="h-4 w-4" />
                        <span>{t('fitness.glossaryTitle')}</span>
                        <span className="text-xs">▼</span>
                    </summary>
                    <div className="mt-3 space-y-3 text-sm">
                        <div>
                            <div className="font-semibold mb-1 flex items-center gap-1"><ChevronRight className="h-3 w-3" /> {t('fitness.ctlLabel')}</div>
                            <p className="text-muted-foreground text-xs leading-relaxed">
                                {t('fitness.ctlGlossary')}
                            </p>
                        </div>
                        <div>
                            <div className="font-semibold mb-1 flex items-center gap-1"><ChevronRight className="h-3 w-3" /> {t('fitness.atlLabel')}</div>
                            <p className="text-muted-foreground text-xs leading-relaxed">
                                {t('fitness.atlGlossary')}
                            </p>
                        </div>
                        <div>
                            <div className="font-semibold mb-1 flex items-center gap-1"><ChevronRight className="h-3 w-3" /> TSB</div>
                            <p className="text-muted-foreground text-xs leading-relaxed">
                                {t('fitness.tsbGlossary')}
                            </p>
                        </div>
                        <div>
                            <div className="font-semibold mb-1 flex items-center gap-1"><ChevronRight className="h-3 w-3" /> FTP</div>
                            <p className="text-muted-foreground text-xs leading-relaxed">
                                {t('fitness.ftpGlossary')}
                            </p>
                        </div>
                        <div>
                            <div className="font-semibold mb-1 flex items-center gap-1"><ChevronRight className="h-3 w-3" /> HRV</div>
                            <p className="text-muted-foreground text-xs leading-relaxed">
                                {t('fitness.hrvGlossary')}
                            </p>
                        </div>
                    </div>
                </details>
            </CardContent>
        </Card>
    );
}
