import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { CATEGORICAL_PALETTE, CHART_INK } from '../../utils/chartPalette.js'
import { formatCurrency } from '../../utils/format.js'

function pivotByMonth(items) {
  const loanNames = [...new Set(items.map((item) => item.loan_name))]
  const byMonth = new Map()

  for (const item of items) {
    const row = byMonth.get(item.month_number) ?? { month_number: item.month_number }
    row[item.loan_name] = Number(item.closing_balance)
    byMonth.set(item.month_number, row)
  }

  return { rows: [...byMonth.values()].sort((a, b) => a.month_number - b.month_number), loanNames }
}

function ChartTooltip({ active, payload, label, t }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm shadow-sm">
      <p className="mb-1 font-medium text-slate-900 dark:text-slate-100">{t('planning.monthWithNumber', { month: label })}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} style={{ color: entry.color }}>
          {entry.dataKey}: {formatCurrency(entry.value)}
        </p>
      ))}
    </div>
  )
}

export default function RepaymentPlanChart({ items }) {
  const { t } = useTranslation()
  const { rows, loanNames } = useMemo(() => pivotByMonth(items), [items])

  if (rows.length === 0) return null

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('planning.debtPayoffProjection')}</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={rows} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
          <XAxis
            dataKey="month_number"
            tickLine={false}
            axisLine={false}
            tick={{ fill: CHART_INK.muted, fontSize: 12 }}
            label={{ value: t('planning.month'), position: 'insideBottom', offset: -2, fill: CHART_INK.muted, fontSize: 12 }}
          />
          <YAxis tickLine={false} axisLine={false} tick={{ fill: CHART_INK.muted, fontSize: 12 }} width={70} />
          <Tooltip content={<ChartTooltip t={t} />} />
          {loanNames.length > 1 && <Legend />}
          {loanNames.map((name, index) => (
            <Line
              key={name}
              type="monotone"
              dataKey={name}
              stroke={CATEGORICAL_PALETTE[index % CATEGORICAL_PALETTE.length]}
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
