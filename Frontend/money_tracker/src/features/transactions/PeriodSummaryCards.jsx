import { useTranslation } from 'react-i18next'
import StatCard from '../../components/StatCard.jsx'
import { formatCurrency } from '../../utils/format.js'

const PERIODS = [
  { key: 'today', labelKey: 'transactions.periodToday' },
  { key: 'this_week', labelKey: 'transactions.periodThisWeek' },
  { key: 'this_month', labelKey: 'transactions.periodThisMonth' },
  { key: 'this_year', labelKey: 'transactions.periodThisYear' },
]

export default function PeriodSummaryCards({ totals, accent }) {
  const { t } = useTranslation()
  if (!totals) return null

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {PERIODS.map(({ key, labelKey }) => (
        <StatCard key={key} label={t(labelKey)} value={formatCurrency(totals[key] ?? 0)} accent={accent} />
      ))}
    </div>
  )
}
