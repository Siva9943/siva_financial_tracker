import { BarChart2, LineChart as LineChartIcon } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import * as investmentApi from '../../api/investmentApi'
import ChartViewToggle from '../../components/ChartViewToggle.jsx'
import EmptyState from '../../components/EmptyState.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import { CATEGORICAL_PALETTE, CHART_INK } from '../../utils/chartPalette.js'
import { PORTFOLIO_RANGES } from '../../utils/investmentOptions.js'
import { formatCurrency, formatDate } from '../../utils/format.js'

function ValueTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm shadow-sm">
      <p className="mb-1 font-medium text-slate-900 dark:text-slate-100">{formatDate(label)}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} style={{ color: entry.color }}>
          {entry.name}: {formatCurrency(entry.value)}
        </p>
      ))}
    </div>
  )
}

function MonthlyPnlTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const value = payload[0].value
  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm shadow-sm">
      <p className="mb-1 font-medium text-slate-900 dark:text-slate-100">{label}</p>
      <p className={value >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
        {value >= 0 ? '+' : ''}
        {formatCurrency(value)}
      </p>
    </div>
  )
}

function monthLabel(monthKey) {
  const [year, month] = monthKey.split('-')
  const date = new Date(Number(year), Number(month) - 1, 1)
  return date.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
}

export default function PortfolioPerformanceChart() {
  const { t } = useTranslation()
  const [range, setRange] = useState('1Y')
  const [view, setView] = useState('value')
  const [rows, setRows] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError('')
    investmentApi
      .getPortfolioSnapshots(range)
      .then((data) => {
        if (cancelled) return
        setRows(data?.results ?? [])
      })
      .catch(() => {
        if (!cancelled) setError(t('investments.performanceLoadError'))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [range, t])

  const chartData = rows.map((row) => ({
    snapshot_date: row.snapshot_date,
    portfolio_value: Number(row.portfolio_value),
    total_invested: Number(row.total_invested),
  }))

  const monthlyPnlData = useMemo(() => {
    const lastByMonth = new Map()
    rows.forEach((row) => {
      const monthKey = row.snapshot_date.slice(0, 7)
      lastByMonth.set(monthKey, Number(row.profit_loss))
    })
    return Array.from(lastByMonth.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([monthKey, profitLoss]) => ({ month: monthLabel(monthKey), profit_loss: profitLoss }))
  }, [rows])

  const viewOptions = [
    { key: 'value', icon: LineChartIcon, label: t('investments.performanceViewValue') },
    { key: 'monthlyPnl', icon: BarChart2, label: t('investments.performanceViewMonthlyPnl') },
  ]

  const isEmpty = view === 'value' ? chartData.length === 0 : monthlyPnlData.length === 0

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{t('investments.performanceTitle')}</h3>
        <ChartViewToggle value={view} onChange={setView} options={viewOptions} />
      </div>

      <div className="mb-3 flex flex-wrap gap-1">
        {PORTFOLIO_RANGES.map((r) => (
          <button
            key={r}
            type="button"
            onClick={() => setRange(r)}
            aria-pressed={range === r}
            className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors duration-150 ${
              range === r
                ? 'bg-brand-600 text-white dark:bg-brand-500'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600'
            }`}
          >
            {r}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      ) : isEmpty ? (
        <EmptyState
          title={t('investments.noSnapshotHistoryTitle')}
          description={t('investments.noSnapshotHistoryDescription')}
        />
      ) : view === 'value' ? (
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
            <CartesianGrid vertical={false} stroke={CHART_INK.gridline} />
            <XAxis
              dataKey="snapshot_date"
              tickFormatter={formatDate}
              tickLine={false}
              axisLine={false}
              tick={{ fill: CHART_INK.muted, fontSize: 12 }}
            />
            <YAxis
              tickFormatter={(v) => formatCurrency(v)}
              tickLine={false}
              axisLine={false}
              tick={{ fill: CHART_INK.muted, fontSize: 12 }}
              width={80}
            />
            <Tooltip content={<ValueTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="portfolio_value"
              name={t('investments.portfolioValue')}
              stroke={CATEGORICAL_PALETTE[0]}
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="total_invested"
              name={t('investments.totalInvested')}
              stroke={CATEGORICAL_PALETTE[3]}
              strokeWidth={1.5}
              strokeDasharray="4 3"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={monthlyPnlData} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
            <CartesianGrid vertical={false} stroke={CHART_INK.gridline} />
            <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} />
            <YAxis tickFormatter={(v) => formatCurrency(v)} tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} width={80} />
            <Tooltip content={<MonthlyPnlTooltip />} cursor={{ fill: 'rgba(11,11,11,0.04)' }} />
            <Bar dataKey="profit_loss" name={t('investments.monthlyPnl')} radius={[3, 3, 0, 0]}>
              {monthlyPnlData.map((row) => (
                <Cell key={row.month} fill={row.profit_loss >= 0 ? '#1baf7a' : '#e34948'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
