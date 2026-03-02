/**
 * FitnessTrendChart - 7-day CTL/ATL/TSB trend line chart
 *
 * TSB zone bands (standard PMC / Joe Friel terminology):
 *   > +5   : Peak Form (Race Ready)         — green band
 *  -10..+5 : Optimal Training Zone           — no fill
 * -30..-10 : Accumulated Fatigue (Overreach) — orange band
 *   < -30  : Overreached / Danger            — red band
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

// Derive Y-axis domain that fits data + zone band extremes
function getYDomain(history: TrainingHistoryPoint[]): [number, number] {
    if (history.length === 0) return [-40, 40];
    const allValues = history.flatMap(p => [p.ctl, p.atl, p.tsb]);
    const min = Math.min(...allValues, -30);
    const max = Math.max(...allValues, 10);
    const pad = 5;
    return [Math.floor(min - pad), Math.ceil(max + pad)];
}

export function FitnessTrendChart({ history }: FitnessTrendChartProps) {
    const { t } = useTranslation();
    const [yMin, yMax] = getYDomain(history);

    return (
        <ResponsiveContainer width="100%" height={200}>
            <LineChart data={history} margin={{ top: 5, right: 40, bottom: 5, left: -20 }}>

                {/* ── TSB Zone Bands (background, drawn before lines) ── */}

                {/* Peak Form / Race Ready: TSB > +5 */}
                <ReferenceArea
                    y1={5} y2={yMax}
                    fill="#22c55e" fillOpacity={0.08}
                    ifOverflow="extendDomain"
                />
                {/* Accumulated Fatigue: TSB -30 to -10 */}
                <ReferenceArea
                    y1={-30} y2={-10}
                    fill="#f97316" fillOpacity={0.10}
                    ifOverflow="extendDomain"
                />
                {/* Overreached / Danger: TSB < -30 */}
                <ReferenceArea
                    y1={yMin} y2={-30}
                    fill="#ef4444" fillOpacity={0.12}
                    ifOverflow="extendDomain"
                />

                {/* ── Zone boundary reference lines ── */}
                <ReferenceLine
                    y={5}
                    stroke="#22c55e" strokeWidth={1} strokeDasharray="3 3" strokeOpacity={0.6}
                    label={{ value: t('fitness.zonePeakForm'), position: 'right', fontSize: 9, fill: '#16a34a' }}
                />
                <ReferenceLine
                    y={-10}
                    stroke="#f97316" strokeWidth={1} strokeDasharray="3 3" strokeOpacity={0.6}
                    label={{ value: t('fitness.zoneFatigue'), position: 'right', fontSize: 9, fill: '#ea580c' }}
                />
                <ReferenceLine
                    y={-30}
                    stroke="#ef4444" strokeWidth={1} strokeDasharray="3 3" strokeOpacity={0.6}
                    label={{ value: t('fitness.zoneOverreached'), position: 'right', fontSize: 9, fill: '#dc2626' }}
                />
                {/* Zero line */}
                <ReferenceLine y={0} stroke="#94a3b8" strokeWidth={1} strokeOpacity={0.4} />

                <XAxis
                    dataKey="date"
                    tickFormatter={(d: string) => d.slice(5)}
                    tick={{ fontSize: 10 }}
                />
                <YAxis tick={{ fontSize: 10 }} domain={[yMin, yMax]} />
                <Tooltip
                    formatter={(value, name) => [
                        value != null ? Number(value).toFixed(1) : '—',
                        name ?? '',
                    ]}
                    labelFormatter={(label) => String(label)}
                />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Line
                    type="monotone"
                    dataKey="ctl"
                    name={t('fitness.trendCTL')}
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                />
                <Line
                    type="monotone"
                    dataKey="atl"
                    name={t('fitness.trendATL')}
                    stroke="#f97316"
                    strokeWidth={2}
                    dot={false}
                />
                <Line
                    type="monotone"
                    dataKey="tsb"
                    name={t('fitness.trendTSB')}
                    stroke="#22c55e"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                />
            </LineChart>
        </ResponsiveContainer>
    );
}
