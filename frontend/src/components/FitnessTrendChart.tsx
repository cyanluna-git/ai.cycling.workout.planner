/**
 * FitnessTrendChart - 7-day CTL/ATL/TSB trend line chart
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
} from 'recharts';
import type { TrainingHistoryPoint } from '@/lib/api';

interface FitnessTrendChartProps {
    history: TrainingHistoryPoint[];
}

export function FitnessTrendChart({ history }: FitnessTrendChartProps) {
    const { t } = useTranslation();

    return (
        <ResponsiveContainer width="100%" height={180}>
            <LineChart data={history} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
                <XAxis
                    dataKey="date"
                    tickFormatter={(d: string) => d.slice(5)}
                    tick={{ fontSize: 10 }}
                />
                <YAxis tick={{ fontSize: 10 }} />
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
