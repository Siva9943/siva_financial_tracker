import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import EmptyState from '../../components/EmptyState.jsx'
import { CATEGORICAL_PALETTE, CHART_INK, capToPaletteSlots } from '../../utils/chartPalette.js'
import { formatCurrency } from '../../utils/format.js'

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { loan_name: loanName, outstanding_principal: outstanding } = payload[0].payload
  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm shadow-sm">
      <p className="font-medium text-slate-900 dark:text-slate-100">{loanName}</p>
      <p className="text-slate-500 dark:text-slate-400">{formatCurrency(outstanding)}</p>
    </div>
  )
}

export default function LoanBalanceChart({ data }) {
  const { t } = useTranslation()
  const rows = capToPaletteSlots(data ?? [], { labelKey: 'loan_name', valueKey: 'outstanding_principal' })

  if (rows.length === 0) {
    return <EmptyState title={t('dashboard.noActiveLoansTitle')} description={t('dashboard.noActiveLoansDescription')} />
  }

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('dashboard.loanBalance')}</h3>
      <ResponsiveContainer width="100%" height={Math.max(rows.length * 40, 120)}>
        <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
          <XAxis type="number" hide />
          <YAxis type="category" dataKey="loan_name" width={110} tickLine={false} axisLine={false} tick={{ fill: CHART_INK.secondary, fontSize: 12 }} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(11,11,11,0.04)' }} />
          <Bar dataKey="outstanding_principal" radius={[4, 4, 4, 4]} maxBarSize={22}>
            {rows.map((row, index) => (
              <Cell key={row.loan_name} fill={CATEGORICAL_PALETTE[index % CATEGORICAL_PALETTE.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
