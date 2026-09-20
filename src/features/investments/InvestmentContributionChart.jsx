import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import * as investmentApi from '../../api/investmentApi'
import EmptyState from '../../components/EmptyState.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import { CATEGORICAL_PALETTE, CHART_INK } from '../../utils/chartPalette.js'
import { ANALYTICS_PERIODS } from '../../utils/investmentOptions.js'
import { formatCurrency, formatDate } from '../../utils/format.js'

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function formatLabel(period, value) {
  if (period === 'month' && /^\d{4}-\d{2}$/.test(value)) {
    const [year, month] = value.split('-')
    return `${MONTH_NAMES[Number(month) - 1]} ${year}`
  }
  if (period === 'year') return value
  return formatDate(value)
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm shadow-sm">
      <p className="mb-1 font-medium text-slate-900 dark:text-slate-100">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} style={{ color: entry.color }}>
          {formatCurrency(entry.value)}
        </p>
      ))}
    </div>
  )
}

export default function InvestmentContributionChart() {
  const { t } = useTranslation()
  const [period, setPeriod] = useState('month')
  const [rows, setRows] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError('')
    investmentApi
      .getContributionTrend(period)
      .then((data) => {
        if (cancelled) return
        setRows(data?.results ?? [])
      })
      .catch(() => {
        if (!cancelled) setError(t('investments.contributionLoadError'))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [period, t])

  const chartData = rows.map((row) => ({
    label: formatLabel(period, row.period),
    contribution: Number(row.contribution),
  }))
  const hasData = chartData.some((row) => row.contribution !== 0)

  const periodLabels = {
    day: t('investments.periodDay'),
    week: t('investments.periodWeek'),
    month: t('investments.periodMonth'),
    year: t('investments.periodYear'),
  }

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{t('investments.contributionTitle')}</h3>
        <div className="inline-flex items-center gap-0.5 rounded-lg border border-slate-200 bg-slate-50 p-0.5 dark:border-slate-700 dark:bg-slate-900">
          {ANALYTICS_PERIODS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setPeriod(p)}
              aria-pressed={period === p}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors duration-150 ${
                period === p
                  ? 'bg-white text-brand-600 shadow-sm dark:bg-slate-700 dark:text-brand-400'
                  : 'text-slate-400 hover:text-slate-700 dark:text-slate-500 dark:hover:text-slate-200'
              }`}
            >
              {periodLabels[p]}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      ) : !hasData ? (
        <EmptyState title={t('investments.noContributionsTitle')} description={t('investments.noContributionsDescription')} />
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
            <CartesianGrid vertical={false} stroke={CHART_INK.gridline} />
            <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} />
            <YAxis
              tickFormatter={(v) => formatCurrency(v)}
              tickLine={false}
              axisLine={false}
              tick={{ fill: CHART_INK.muted, fontSize: 12 }}
              width={80}
            />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(11,11,11,0.04)' }} />
            <Bar dataKey="contribution" fill={CATEGORICAL_PALETTE[2]} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
