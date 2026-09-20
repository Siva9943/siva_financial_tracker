import { useTranslation } from 'react-i18next'
import StatCard from '../../components/StatCard.jsx'
import { formatCurrency } from '../../utils/format.js'

export default function DashboardCards({ cards }) {
  const { t } = useTranslation()
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <StatCard label={t('dashboard.totalIncome')} value={formatCurrency(cards.total_income)} accent="text-green-700" />
      <StatCard label={t('dashboard.totalExpenses')} value={formatCurrency(cards.total_expenses)} accent="text-red-700" />
      <StatCard label={t('dashboard.savings')} value={formatCurrency(cards.savings)} />
      <StatCard label={t('dashboard.availableBalance')} value={formatCurrency(cards.available_balance)} />
      <StatCard label={t('dashboard.totalDebt')} value={formatCurrency(cards.total_debt)} />
      <StatCard label={t('dashboard.outstandingPrincipal')} value={formatCurrency(cards.outstanding_principal)} accent="text-amber-700" />
      <StatCard label={t('dashboard.interestPaid')} value={formatCurrency(cards.interest_paid)} />
      <StatCard label={t('dashboard.monthlyEmi')} value={formatCurrency(cards.monthly_emi)} />
    </div>
  )
}
