import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { useTranslation } from 'react-i18next'
import EmptyState from '../../components/EmptyState.jsx'
import { CATEGORICAL_PALETTE } from '../../utils/chartPalette.js'
import { labelize } from '../../utils/categories.js'
import { formatCurrency } from '../../utils/format.js'

function buildBreakdown(loans) {
  const totals = new Map()
  for (const loan of loans) {
    const type = loan.loan_type
    const outstanding = Number(loan.outstanding_principal ?? 0)
    totals.set(type, (totals.get(type) ?? 0) + outstanding)
  }

  const rows = [...totals.entries()]
    .map(([type, outstanding]) => ({ type, label: labelize(type), outstanding }))
    .sort((a, b) => b.outstanding - a.outstanding)

  const grandTotal = rows.reduce((sum, row) => sum + row.outstanding, 0)

  const maxSlots = CATEGORICAL_PALETTE.length
  if (rows.length <= maxSlots) {
    return rows.map((row) => ({ ...row, percentage: grandTotal ? Math.round((row.outstanding / grandTotal) * 100) : 0 }))
  }

  const head = rows.slice(0, maxSlots - 1)
  const tail = rows.slice(maxSlots - 1)
  const otherTotal = tail.reduce((sum, row) => sum + row.outstanding, 0)
  return [...head, { type: 'OTHER', label: 'Other', outstanding: otherTotal }].map((row) => ({
    ...row,
    percentage: grandTotal ? Math.round((row.outstanding / grandTotal) * 100) : 0,
  }))
}

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { label, outstanding, percentage } = payload[0].payload
  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm shadow-sm">
      <p className="font-medium text-slate-900 dark:text-slate-100">{label}</p>
      <p className="text-slate-500 dark:text-slate-400">
        {formatCurrency(outstanding)} &middot; {percentage}%
      </p>
    </div>
  )
}

export default function LoanTypeBreakdownChart({ loans }) {
  const { t } = useTranslation()
  const rows = buildBreakdown(loans ?? [])

  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('loans.typeBreakdown.title')}</h3>
        <EmptyState title={t('loans.typeBreakdown.emptyTitle')} description={t('loans.typeBreakdown.emptyDescription')} />
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('loans.typeBreakdown.title')}</h3>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie data={rows} dataKey="outstanding" nameKey="label" innerRadius={60} outerRadius={95} paddingAngle={2}>
            {rows.map((row, index) => (
              <Cell key={row.type} fill={CATEGORICAL_PALETTE[index % CATEGORICAL_PALETTE.length]} />
            ))}
          </Pie>
          <Tooltip content={<ChartTooltip />} />
          <Legend iconSize={10} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
