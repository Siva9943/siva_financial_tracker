import { useTranslation } from 'react-i18next'
import StatCard from '../../components/StatCard.jsx'
import { formatCurrency, formatDate } from '../../utils/format.js'

export default function RepaymentPlanSummary({ plan, excludedLoans }) {
  const { t } = useTranslation()

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label={t('planning.expectedPayoff')} value={formatDate(plan.expected_payoff_date)} />
        <StatCard label={t('planning.monthsRemaining')} value={plan.months_remaining} />
        <StatCard label={t('planning.totalInterest')} value={formatCurrency(plan.total_interest)} accent="text-amber-700" />
        <StatCard label={t('planning.totalPayment')} value={formatCurrency(plan.total_payment)} />
      </div>

      {plan.assumptions?.length > 0 && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('planning.assumptions')}</h3>
          <ul className="list-inside list-disc space-y-1 text-sm text-slate-600 dark:text-slate-400">
            {plan.assumptions.map((assumption) => (
              <li key={assumption}>{assumption}</li>
            ))}
          </ul>
        </div>
      )}

      {excludedLoans?.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <p className="font-medium">{t('planning.excludedFromPlan')}</p>
          <ul className="mt-1 list-inside list-disc">
            {excludedLoans.map((loan) => (
              <li key={loan.loan_id}>
                {loan.loan_name} — {loan.reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
