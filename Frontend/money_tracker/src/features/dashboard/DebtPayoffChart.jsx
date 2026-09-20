import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import EmptyState from '../../components/EmptyState.jsx'
import { CATEGORICAL_PALETTE, CHART_INK } from '../../utils/chartPalette.js'
import { formatCurrency } from '../../utils/format.js'

function ChartTooltip({ active, payload, label }) {
  const { t } = useTranslation()
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm shadow-sm">
      <p className="font-medium text-slate-900 dark:text-slate-100">{t('dashboard.monthLabel', { month: label })}</p>
      <p className="text-slate-500 dark:text-slate-400">{formatCurrency(payload[0].value)}</p>
    </div>
  )
}

export default function DebtPayoffChart({ data }) {
  const { t } = useTranslation()
  const total = (data ?? []).reduce((sum, row) => sum + Number(row.total_outstanding), 0)

  if (total === 0) {
    return <EmptyState title={t('dashboard.noProjectedDebtTitle')} description={t('dashboard.noProjectedDebtDescription')} />
  }

  const rows = (data ?? []).map((row) => ({ month: row.month, total_outstanding: Number(row.total_outstanding) }))

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('dashboard.debtPayoffProjection')}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={rows} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
          <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} />
          <YAxis tickFormatter={(v) => formatCurrency(v)} tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} width={80} />
          <Tooltip content={<ChartTooltip />} />
          <Line type="monotone" dataKey="total_outstanding" stroke={CATEGORICAL_PALETTE[0]} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
