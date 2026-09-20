import { BarChart2, CircleDot, LineChart as LineChartIcon } from 'lucide-react'
import { useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useTranslation } from 'react-i18next'
import ChartViewToggle from '../../components/ChartViewToggle.jsx'
import EmptyState from '../../components/EmptyState.jsx'
import { CATEGORICAL_PALETTE, CHART_INK } from '../../utils/chartPalette.js'

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm shadow-sm">
      {label && <p className="mb-1 font-medium text-slate-900 dark:text-slate-100">{label}</p>}
      {payload.map((entry) => (
        <p key={entry.dataKey ?? entry.name} style={{ color: entry.color ?? entry.payload?.fill }}>
          {entry.name}: {entry.value ?? '—'}%
        </p>
      ))}
    </div>
  )
}

export default function HistoricalMetricsChart({ historical }) {
  const { t } = useTranslation()
  const [view, setView] = useState('line')
  const SERIES = [
    { key: 'savings_rate', name: t('dashboard.savingsRate') },
    { key: 'debt_to_income', name: t('dashboard.debtToIncome') },
    { key: 'expense_ratio', name: t('dashboard.expenseRatio') },
    { key: 'interest_burden', name: t('dashboard.interestBurden') },
  ]

  if (!historical || historical.length === 0) {
    return <EmptyState title={t('dashboard.notEnoughHistoryTitle')} description={t('dashboard.notEnoughHistoryDescription')} />
  }

  const latest = historical[historical.length - 1]
  const radialData = SERIES.map((series, index) => ({
    name: series.name,
    value: Number(latest[series.key] ?? 0),
    fill: CATEGORICAL_PALETTE[index],
  }))

  const viewOptions = [
    { key: 'line', icon: LineChartIcon, label: t('dashboard.chartViewLine') },
    { key: 'bar', icon: BarChart2, label: t('dashboard.chartViewBar') },
    { key: 'circle', icon: CircleDot, label: t('dashboard.chartViewCircle') },
  ]

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{t('dashboard.financialRatiosOverTime')}</h3>
        <ChartViewToggle value={view} onChange={setView} options={viewOptions} />
      </div>

      {view === 'circle' ? (
        <>
          <p className="mb-2 text-xs text-slate-400 dark:text-slate-500">{t('dashboard.chartViewCircleHint', { period: latest.label })}</p>
          <ResponsiveContainer width="100%" height={280}>
            <RadialBarChart
              data={radialData}
              innerRadius="20%"
              outerRadius="100%"
              barSize={14}
              startAngle={90}
              endAngle={-270}
            >
              <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
              <PolarGrid radialLines={false} stroke={CHART_INK.gridline} />
              <RadialBar background dataKey="value" cornerRadius={8} />
              <Tooltip content={<ChartTooltip />} />
              <Legend
                iconSize={10}
                layout="vertical"
                verticalAlign="middle"
                align="right"
                formatter={(_, entry) => `${entry.payload.name}: ${entry.payload.value}%`}
              />
            </RadialBarChart>
          </ResponsiveContainer>
        </>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          {view === 'bar' ? (
            <BarChart data={historical} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
              <CartesianGrid vertical={false} stroke={CHART_INK.gridline} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} />
              <YAxis tickFormatter={(v) => `${v}%`} tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} width={50} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(11,11,11,0.04)' }} />
              <Legend />
              {SERIES.map((series, index) => (
                <Bar key={series.key} dataKey={series.key} name={series.name} fill={CATEGORICAL_PALETTE[index]} radius={[3, 3, 0, 0]} />
              ))}
            </BarChart>
          ) : (
            <LineChart data={historical} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
              <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} />
              <YAxis tickFormatter={(v) => `${v}%`} tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} width={50} />
              <Tooltip content={<ChartTooltip />} />
              <Legend />
              {SERIES.map((series, index) => (
                <Line
                  key={series.key}
                  type="monotone"
                  dataKey={series.key}
                  name={series.name}
                  stroke={CATEGORICAL_PALETTE[index]}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                />
              ))}
            </LineChart>
          )}
        </ResponsiveContainer>
      )}
    </div>
  )
}
