import { useTranslation } from 'react-i18next';
import {
    CartesianGrid,
    Line,
    LineChart,
    ReferenceArea,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';
import type { TrainingHistoryPoint } from '@/lib/api';
import {
    mapTrainingHistoryForCenteredChart,
    type CenteredTrainingStatePoint,
} from '@/lib/training-state-chart';

interface FitnessTrendChartProps {
    history: TrainingHistoryPoint[];
}

interface TrendTooltipProps {
    active?: boolean;
    payload?: Array<{ payload: CenteredTrainingStatePoint }>;
    label?: string;
}

const DISPLAY_DOMAIN: [number, number] = [-100, 100];
const DISPLAY_TICKS = [-80, 0, 80];

function TrendTooltipContent({ active, payload, label }: TrendTooltipProps) {
    const { t } = useTranslation();
    const point = payload?.[0]?.payload;

    if (!active || !point) return null;

    return (
        <div className="min-w-[180px] rounded-md border bg-background px-3 py-2 text-xs shadow-md">
            <div className="mb-1 font-semibold text-foreground">{label}</div>
            <div className="mb-2 text-muted-foreground">
                {t('fitness.trendStateLabel')}: <span className="font-medium text-foreground">{point.state_label}</span>
            </div>
            <div className="space-y-1 text-muted-foreground">
                <div className="flex justify-between gap-3">
                    <span>{t('fitness.trendCTL')}</span>
                    <span className="font-medium text-foreground">{point.ctl.toFixed(1)}</span>
                </div>
                <div className="flex justify-between gap-3">
                    <span>{t('fitness.trendATL')}</span>
                    <span className="font-medium text-foreground">{point.atl.toFixed(1)}</span>
                </div>
                <div className="flex justify-between gap-3">
                    <span>{t('fitness.trendTSB')}</span>
                    <span className="font-medium text-foreground">{point.tsb.toFixed(1)}</span>
                </div>
            </div>
        </div>
    );
}

export function FitnessTrendChart({ history }: FitnessTrendChartProps) {
    const { t } = useTranslation();
    const centeredHistory = mapTrainingHistoryForCenteredChart(history, {
        overload: t('fitness.trendZoneOverload'),
        optimal: t('fitness.trendZoneOptimal'),
        need_load: t('fitness.trendZoneNeedLoad'),
    });

    return (
        <div className="space-y-2">
            <ResponsiveContainer width="100%" height={220}>
                <LineChart data={centeredHistory} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
                    <ReferenceArea y1={40} y2={DISPLAY_DOMAIN[1]} fill="#ef4444" fillOpacity={0.08} />
                    <ReferenceArea y1={-20} y2={40} fill="#22c55e" fillOpacity={0.08} />
                    <ReferenceArea y1={DISPLAY_DOMAIN[0]} y2={-20} fill="#f59e0b" fillOpacity={0.08} />

                    <ReferenceLine y={40} stroke="#ef4444" strokeDasharray="4 4" strokeOpacity={0.35} />
                    <ReferenceLine y={0} stroke="#22c55e" strokeDasharray="4 4" strokeOpacity={0.45} />
                    <ReferenceLine y={-20} stroke="#f59e0b" strokeDasharray="4 4" strokeOpacity={0.35} />

                    <CartesianGrid vertical={false} strokeDasharray="3 3" strokeOpacity={0.15} />
                    <XAxis
                        dataKey="date"
                        tickFormatter={(date: string) => date.slice(5)}
                        tick={{ fontSize: 10 }}
                        tickLine={false}
                        axisLine={false}
                    />
                    <YAxis
                        domain={DISPLAY_DOMAIN}
                        ticks={DISPLAY_TICKS}
                        tick={{ fontSize: 10 }}
                        tickFormatter={(value: number) => {
                            if (value > 0) return t('fitness.trendZoneOverload');
                            if (value < 0) return t('fitness.trendZoneNeedLoad');
                            return t('fitness.trendZoneOptimal');
                        }}
                        width={64}
                        tickLine={false}
                        axisLine={false}
                    />
                    <Tooltip content={<TrendTooltipContent />} />
                    <Line
                        type="monotone"
                        dataKey="display_state"
                        stroke="#2563eb"
                        strokeWidth={2.5}
                        dot={false}
                        activeDot={{ r: 4, strokeWidth: 0 }}
                    />
                </LineChart>
            </ResponsiveContainer>

            <div className="flex flex-wrap items-center justify-center gap-2 text-[10px] text-muted-foreground">
                <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5">
                    <span className="h-2 w-2 rounded-full bg-red-500" />
                    <span>{t('fitness.trendZoneOverloadLegend')}</span>
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-green-500/10 px-2 py-0.5">
                    <span className="h-2 w-2 rounded-full bg-green-500" />
                    <span>{t('fitness.trendZoneOptimalLegend')}</span>
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5">
                    <span className="h-2 w-2 rounded-full bg-amber-500" />
                    <span>{t('fitness.trendZoneNeedLoadLegend')}</span>
                </span>
            </div>

            <p className="px-1 text-[11px] leading-relaxed text-muted-foreground">
                {t('fitness.centeredTrendHint')}
            </p>
        </div>
    );
}
