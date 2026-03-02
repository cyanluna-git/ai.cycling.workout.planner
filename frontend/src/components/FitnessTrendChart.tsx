/**
 * FitnessTrendChart - 7-day CTL/ATL/TSB trend line chart
 *
 * PMC-standard dual-axis layout (TrainingPeaks / Intervals.icu convention):
 *   Left Y-axis  → CTL + ATL (training load / fitness & fatigue)
 *   Right Y-axis → TSB only  (form / freshness)
 *
 * TSB zone bands (Joe Friel / standard PMC colour coding):
 *   > +5   : Peak Form        — green
 *  -10..+5 : Optimal Training  — blue
 * -30..-10 : Accumulated Fatigue — orange
 *   < -30  : Overreached       — red
 *
 * Zone names are shown in a compact legend strip below the chart.
 */

import { useTranslation } from 'react-i18next';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    Legend,
    ReferenceLine,
    ReferenceArea,
} from 'recharts';
import type { TrainingHistoryPoint } from '@/lib/api';

interface FitnessTrendChartProps {
    history: TrainingHistoryPoint[];
}

function getLoadDomain(history: TrainingHistoryPoint[]): [number, number] {
    if (history.length === 0) return [0, 80];
    const vals = history.flatMap(p => [p.ctl, p.atl]);
    const min = Math.min(...vals, 0);
    const max = Math.max(...vals, 50);
    return [Math.floor(min - 2), Math.ceil(max + 8)];
}

function getTsbDomain(history: TrainingHistoryPoint[]): [number, number] {
    if (history.length === 0) return [-40, 20];
    const vals = history.map(p => p.tsb);
    const min = Math.min(...vals, -35);
    const max = Math.max(...vals, 10);
    return [Math.floor(min - 3), Math.ceil(max + 5)];
}

export function FitnessTrendChart({ history }: FitnessTrendChartProps) {
    const { t } = useTranslation();
    const loadDomain = getLoadDomain(history);
    const tsbDomain = getTsbDomain(history);
    const [tsbMin, tsbMax] = tsbDomain;

    return (
        <div className="space-y-1">
            <ResponsiveContainer width="100%" height={220}>
                <LineChart data={history} margin={{ top: 5, right: 10, bottom: 5, left: 5 }}>

                    {/* ── TSB Zone Bands (background, behind lines) ── */}
                    <ReferenceArea yAxisId="tsb" y1={5}     y2={tsbMax} fill="#22c55e" fillOpacity={0.09} ifOverflow="extendDomain" />
                    <ReferenceArea yAxisId="tsb" y1={-10}   y2={5}      fill="#3b82f6" fillOpacity={0.06} ifOverflow="extendDomain" />
                    <ReferenceArea yAxisId="tsb" y1={-30}   y2={-10}    fill="#f97316" fillOpacity={0.10} ifOverflow="extendDomain" />
                    <ReferenceArea yAxisId="tsb" y1={tsbMin} y2={-30}   fill="#ef4444" fillOpacity={0.12} ifOverflow="extendDomain" />

                    {/* ── Zone boundary reference lines ── */}
                    <ReferenceLine yAxisId="tsb" y={5}   stroke="#22c55e" strokeWidth={1} strokeDasharray="3 3" strokeOpacity={0.4} />
                    <ReferenceLine yAxisId="tsb" y={-10} stroke="#f97316" strokeWidth={1} strokeDasharray="3 3" strokeOpacity={0.4} />
                    <ReferenceLine yAxisId="tsb" y={-30} stroke="#ef4444" strokeWidth={1} strokeDasharray="3 3" strokeOpacity={0.4} />
                    <ReferenceLine yAxisId="tsb" y={0}   stroke="#94a3b8" strokeWidth={1} strokeOpacity={0.4} />

                    <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} tick={{ fontSize: 10 }} />
                    <YAxis
                        yAxisId="load" orientation="left"
                        tick={{ fontSize: 10 }}
                        domain={loadDomain} ticks={[loadDomain[0], loadDomain[1]]}
                        width={30}
                    />
                    <YAxis
                        yAxisId="tsb" orientation="right"
                        tick={{ fontSize: 10, fill: '#22c55e' }}
                        domain={tsbDomain} ticks={[tsbDomain[0], tsbDomain[1]]}
                        width={30}
                    />
                    <Tooltip
                        formatter={(value, name) => [
                            value != null ? Number(value).toFixed(1) : '—',
                            name ?? '',
                        ]}
                        labelFormatter={(label) => String(label)}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                    <Line yAxisId="load" type="monotone" dataKey="ctl"
                        name={t('fitness.trendCTL')} stroke="#3b82f6" strokeWidth={2} dot={false} />
                    <Line yAxisId="load" type="monotone" dataKey="atl"
                        name={t('fitness.trendATL')} stroke="#f97316" strokeWidth={2} dot={false} />
                    <Line yAxisId="tsb" type="monotone" dataKey="tsb"
                        name={t('fitness.trendTSB')} stroke="#22c55e" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                </LineChart>
            </ResponsiveContainer>

            {/* ── TSB Zone Legend ── */}
            <div className="flex flex-wrap justify-center gap-x-3 gap-y-0.5 px-2 text-[10px] text-muted-foreground">
                <span className="flex items-center gap-1">
                    <span className="inline-block w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: '#22c55e', opacity: 0.6 }} />
                    <span>{t('fitness.zonePeakForm')}</span>
                    <span className="opacity-50">TSB &gt; +5</span>
                </span>
                <span className="flex items-center gap-1">
                    <span className="inline-block w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: '#3b82f6', opacity: 0.5 }} />
                    <span>{t('fitness.zoneOptimal')}</span>
                    <span className="opacity-50">-10 ~ +5</span>
                </span>
                <span className="flex items-center gap-1">
                    <span className="inline-block w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: '#f97316', opacity: 0.6 }} />
                    <span>{t('fitness.zoneFatigue')}</span>
                    <span className="opacity-50">-30 ~ -10</span>
                </span>
                <span className="flex items-center gap-1">
                    <span className="inline-block w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: '#ef4444', opacity: 0.6 }} />
                    <span>{t('fitness.zoneOverreached')}</span>
                    <span className="opacity-50">TSB &lt; -30</span>
                </span>
            </div>
        </div>
    );
}
