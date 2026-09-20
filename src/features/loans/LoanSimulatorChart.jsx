import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import { CATEGORICAL_PALETTE, CHART_INK } from '../../utils/chartPalette.js'
import { formatCurrency } from '../../utils/format.js'

function ChartTooltip({ active, payload, label, t }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm shadow-sm">
      <p className="font-medium text-slate-900 dark:text-slate-100">{t('loans.simulatorChart.extraPerMonth', { amount: formatCurrency(label) })}</p>
      <p className="text-slate-500 dark:text-slate-400">{t('loans.simulatorChart.interestSaved', { amount: formatCurrency(payload[0].value) })}</p>
    </div>
  )
}

export default function LoanSimulatorChart({ scenarios }) {
  const { t } = useTranslation()
  const data = scenarios.map((s) => ({
    extra_payment: Number(s.extra_payment),
    interest_saved: Number(s.interest_saved),
  }))

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('loans.simulatorChart.title')}</h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
          <CartesianGrid vertical={false} stroke={CHART_INK.gridline} />
          <XAxis
            dataKey="extra_payment"
            tickFormatter={(value) => formatCurrency(value)}
            tickLine={false}
            axisLine={false}
            tick={{ fill: CHART_INK.muted, fontSize: 12 }}
          />
          <YAxis
            tickFormatter={(value) => formatCurrency(value)}
            tickLine={false}
            axisLine={false}
            tick={{ fill: CHART_INK.muted, fontSize: 12 }}
            width={80}
          />
          <Tooltip content={<ChartTooltip t={t} />} cursor={{ fill: 'rgba(11,11,11,0.04)' }} />
          <Bar dataKey="interest_saved" fill={CATEGORICAL_PALETTE[0]} radius={[4, 4, 0, 0]} maxBarSize={48} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
