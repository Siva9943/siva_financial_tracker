import { useEffect, useState } from 'react'
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { useTranslation } from 'react-i18next'
import * as investmentApi from '../../api/investmentApi'
import EmptyState from '../../components/EmptyState.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import { CATEGORICAL_PALETTE } from '../../utils/chartPalette.js'
import { labelize } from '../../utils/categories.js'
import { formatCurrency } from '../../utils/format.js'

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { name, current_value: currentValue, percentage } = payload[0].payload
  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm shadow-sm">
      <p className="font-medium text-slate-900 dark:text-slate-100">{name}</p>
      <p className="text-slate-500 dark:text-slate-400">
        {formatCurrency(currentValue)} &middot; {percentage}%
      </p>
    </div>
  )
}

export default function PortfolioAllocationChart() {
  const { t } = useTranslation()
  const [groupBy, setGroupBy] = useState('type')
  const [rows, setRows] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError('')
    investmentApi
      .getAllocation(groupBy)
      .then((data) => {
        if (cancelled) return
        setRows(data?.results ?? [])
      })
      .catch(() => {
        if (!cancelled) setError(t('investments.allocationLoadError'))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [groupBy, t])

  const chartData = rows.map((row) => ({
    ...row,
    name: groupBy === 'type' ? labelize(row.label) : row.label,
    current_value: Number(row.current_value),
  }))

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{t('investments.allocationTitle')}</h3>
        <div className="inline-flex items-center gap-0.5 rounded-lg border border-slate-200 bg-slate-50 p-0.5 dark:border-slate-700 dark:bg-slate-900">
          {['type', 'platform'].map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setGroupBy(key)}
              aria-pressed={groupBy === key}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors duration-150 ${
                groupBy === key
                  ? 'bg-white text-brand-600 shadow-sm dark:bg-slate-700 dark:text-brand-400'
                  : 'text-slate-400 hover:text-slate-700 dark:text-slate-500 dark:hover:text-slate-200'
              }`}
            >
              {key === 'type' ? t('investments.groupByType') : t('investments.groupByPlatform')}
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
      ) : chartData.length === 0 ? (
        <EmptyState title={t('investments.noAllocationTitle')} description={t('investments.noAllocationDescription')} />
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie data={chartData} dataKey="current_value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={2}>
              {chartData.map((row, index) => (
                <Cell key={row.name} fill={CATEGORICAL_PALETTE[index % CATEGORICAL_PALETTE.length]} />
              ))}
            </Pie>
            <Tooltip content={<ChartTooltip />} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
