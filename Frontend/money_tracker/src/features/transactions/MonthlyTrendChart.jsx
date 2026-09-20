import { BarChart2, LineChart as LineChartIcon } from 'lucide-react'
import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import ChartViewToggle from '../../components/ChartViewToggle.jsx'
import EmptyState from '../../components/EmptyState.jsx'
import { CATEGORICAL_PALETTE, CHART_INK } from '../../utils/chartPalette.js'
import { formatCurrency } from '../../utils/format.js'

function formatMonthLabel(month) {
  if (!month) return ''
  const [year, monthNum] = month.split('-')
  const date = new Date(Number(year), Number(monthNum) - 1, 1)
  return date.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm shadow-sm">
      <p className="mb-1 font-medium text-slate-900 dark:text-slate-100">{formatMonthLabel(label)}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} style={{ color: entry.color }}>
          {entry.name}: {formatCurrency(entry.value)}
        </p>
      ))}
    </div>
  )
}

export default function MonthlyTrendChart({ data, mode = 'single', title, className = '' }) {
  const { t } = useTranslation()
  const [view, setView] = useState('line')

  const rows = (data ?? []).map((row) => ({
    month: row.month,
    total: Number(row.total ?? 0),
    income: Number(row.income ?? 0),
    expense: Number(row.expense ?? 0),
  }))

  const hasData =
    rows.length > 0 &&
    rows.some((row) => (mode === 'dual' ? row.income !== 0 || row.expense !== 0 : row.total !== 0))

  const viewOptions = [
    { key: 'line', icon: LineChartIcon, label: t('dashboard.chartViewLine') },
    { key: 'bar', icon: BarChart2, label: t('dashboard.chartViewBar') },
  ]

  return (
    <div className={`rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 ${className}`}>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</h3>
        {hasData && <ChartViewToggle value={view} onChange={setView} options={viewOptions} />}
      </div>

      {!hasData ? (
        <EmptyState
          title={t('transactions.noTrendDataTitle')}
          description={t('transactions.noTrendDataDescription')}
        />
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          {view === 'bar' ? (
            <BarChart data={rows} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
              <CartesianGrid vertical={false} stroke={CHART_INK.gridline} />
              <XAxis dataKey="month" tickFormatter={formatMonthLabel} tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} />
              <YAxis tickFormatter={(v) => formatCurrency(v)} tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} width={80} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(11,11,11,0.04)' }} />
              {mode === 'dual' && <Legend />}
              {mode === 'dual' ? (
                <>
                  <Bar dataKey="income" name={t('dashboard.income')} fill={CATEGORICAL_PALETTE[0]} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="expense" name={t('dashboard.expense')} fill={CATEGORICAL_PALETTE[1]} radius={[4, 4, 0, 0]} />
                </>
              ) : (
                <Bar dataKey="total" name={title} fill={CATEGORICAL_PALETTE[0]} radius={[4, 4, 0, 0]} />
              )}
            </BarChart>
          ) : (
            <LineChart data={rows} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
              <CartesianGrid vertical={false} stroke={CHART_INK.gridline} />
              <XAxis dataKey="month" tickFormatter={formatMonthLabel} tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} />
              <YAxis tickFormatter={(v) => formatCurrency(v)} tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} width={80} />
              <Tooltip content={<ChartTooltip />} />
              {mode === 'dual' && <Legend />}
              {mode === 'dual' ? (
                <>
                  <Line type="monotone" dataKey="income" name={t('dashboard.income')} stroke={CATEGORICAL_PALETTE[0]} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="expense" name={t('dashboard.expense')} stroke={CATEGORICAL_PALETTE[1]} strokeWidth={2} dot={false} />
                </>
              ) : (
                <Line type="monotone" dataKey="total" name={title} stroke={CATEGORICAL_PALETTE[0]} strokeWidth={2} dot={false} />
              )}
            </LineChart>
          )}
        </ResponsiveContainer>
      )}
    </div>
  )
}
