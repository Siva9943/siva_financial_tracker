import { useTranslation } from 'react-i18next'
import EmptyState from '../../components/EmptyState.jsx'
import { formatCurrency, formatDate } from '../../utils/format.js'

export default function LoanPaymentHistory({ payments }) {
  const { t } = useTranslation()
  if (!payments || payments.length === 0) {
    return <EmptyState title={t('loans.paymentHistoryEmptyTitle')} description={t('loans.paymentHistoryEmptyDescription')} />
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 text-xs uppercase text-slate-500 dark:text-slate-400">
          <tr>
            <th className="px-4 py-2">{t('loans.table.date')}</th>
            <th className="px-4 py-2">{t('loans.table.amount')}</th>
            <th className="px-4 py-2">{t('loans.table.principal')}</th>
            <th className="px-4 py-2">{t('loans.table.interest')}</th>
            <th className="px-4 py-2">{t('loans.table.lateFee')}</th>
            <th className="px-4 py-2">{t('loans.table.extra')}</th>
            <th className="px-4 py-2">{t('loans.table.balanceAfter')}</th>
          </tr>
        </thead>
        <tbody>
          {payments.map((payment) => (
            <tr key={payment.id} className="border-b border-slate-100 dark:border-slate-800 last:border-0">
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatDate(payment.payment_date)}</td>
              <td className="px-4 py-2 font-medium text-slate-900 dark:text-slate-100">{formatCurrency(payment.amount)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(payment.principal_component)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(payment.interest_component)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(payment.late_fee)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(payment.extra_payment)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(payment.remaining_principal)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
