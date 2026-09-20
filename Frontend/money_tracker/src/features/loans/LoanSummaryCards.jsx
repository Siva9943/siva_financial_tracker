import { useTranslation } from 'react-i18next'
import StatCard from '../../components/StatCard.jsx'
import { formatCurrency, formatDate } from '../../utils/format.js'

export default function LoanSummaryCards({ summary }) {
  const { t } = useTranslation()
  if (!summary) return null

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-3 lg:grid-cols-6">
      <StatCard label={t('loans.summary.totalPrincipal')} value={formatCurrency(summary.total_original_principal)} />
      <StatCard label={t('loans.fields.outstanding')} value={formatCurrency(summary.total_outstanding_principal)} accent="text-amber-700" />
      <StatCard label={t('loans.summary.activeLoans')} value={summary.active_loan_count} />
      <StatCard label={t('loans.summary.completed')} value={summary.completed_loan_count} />
      <StatCard label={t('loans.summary.monthlyDebtPayment')} value={formatCurrency(summary.monthly_debt_payment)} />
      <StatCard label={t('loans.summary.nextDue')} value={summary.next_due_date ? formatDate(summary.next_due_date) : '—'} />
    </div>
  )
}
