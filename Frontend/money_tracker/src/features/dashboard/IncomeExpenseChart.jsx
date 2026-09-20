import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import EmptyState from '../../components/EmptyState.jsx'
import { CATEGORICAL_PALETTE, CHART_INK } from '../../utils/chartPalette.js'
import { formatCurrency, formatDate } from '../../utils/format.js'

function ChartTooltip({ active, payload, label }) {
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

export default function IncomeExpenseChart({ data }) {
  const { t } = useTranslation()
  if (!data || data.length === 0) {
    return <EmptyState title={t('dashboard.noIncomeOrExpensesTitle')} description={t('dashboard.noIncomeOrExpensesDescription')} />
  }

  const rows = data.map((row) => ({
    period: row.period?.slice ? row.period.slice(0, 10) : row.period,
    income: Number(row.income),
    expense: Number(row.expense),
  }))

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('dashboard.incomeVsExpense')}</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={rows} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
          <CartesianGrid vertical={false} stroke={CHART_INK.gridline} />
          <XAxis dataKey="period" tickFormatter={formatDate} tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} />
          <YAxis tickFormatter={(v) => formatCurrency(v)} tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} width={80} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(11,11,11,0.04)' }} />
          <Legend />
          <Bar dataKey="income" name={t('dashboard.income')} fill={CATEGORICAL_PALETTE[0]} radius={[4, 4, 0, 0]} />
          <Bar dataKey="expense" name={t('dashboard.expense')} fill={CATEGORICAL_PALETTE[1]} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
