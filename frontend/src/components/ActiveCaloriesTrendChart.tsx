import { useTranslation } from 'react-i18next';
import {
    Area,
    AreaChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';
import type { ActiveCaloriesHistoryPoint } from '@/lib/api';

interface ActiveCaloriesTrendChartProps {
    history: ActiveCaloriesHistoryPoint[];
}

function getLoadDomain(history: ActiveCaloriesHistoryPoint[]): [number, number] {
    if (history.length === 0) return [0, 600];
    const values = history.map((point) => point.active_calories_load);
    const min = Math.min(...values, 0);
    const max = Math.max(...values, 300);
    return [Math.floor(min - 20), Math.ceil(max + 40)];
}

export function ActiveCaloriesTrendChart({ history }: ActiveCaloriesTrendChartProps) {
    const { t } = useTranslation();
    const domain = getLoadDomain(history);

    return (
        <ResponsiveContainer width="100%" height={112}>
            <AreaChart data={history} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                <defs>
                    <linearGradient id="active-calories-fill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f97316" stopOpacity={0.28} />
                        <stop offset="95%" stopColor="#f97316" stopOpacity={0.04} />
                    </linearGradient>
                </defs>
                <CartesianGrid vertical={false} strokeDasharray="3 3" strokeOpacity={0.18} />
                <XAxis
                    dataKey="date"
                    tickFormatter={(d: string) => d.slice(5)}
                    tick={{ fontSize: 10 }}
                    tickLine={false}
                    axisLine={false}
                />
                <YAxis
                    tick={{ fontSize: 10 }}
                    domain={domain}
                    ticks={[domain[0], domain[1]]}
                    width={34}
                    tickLine={false}
                    axisLine={false}
                />
                <Tooltip
                    formatter={(value) => [
                        `${Number(value).toFixed(0)} kcal`,
                        t('fitness.activeCaloriesLoad'),
                    ]}
                    labelFormatter={(label) => String(label)}
                />
                <Area
                    type="monotone"
                    dataKey="active_calories_load"
                    stroke="#f97316"
                    strokeWidth={2}
                    fill="url(#active-calories-fill)"
                    dot={false}
                    activeDot={{ r: 3 }}
                />
            </AreaChart>
        </ResponsiveContainer>
    );
}
