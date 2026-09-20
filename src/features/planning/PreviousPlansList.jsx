import { useTranslation } from 'react-i18next'
import EmptyState from '../../components/EmptyState.jsx'
import { formatCurrency, formatDate, formatDateTime } from '../../utils/format.js'
import { labelize } from '../../utils/categories.js'

export default function PreviousPlansList({ plans, onSelect, selectedId }) {
  const { t } = useTranslation()

  if (!plans || plans.length === 0) {
    return <EmptyState title={t('planning.noPlansYetTitle')} description={t('planning.noPlansYetDescription')} />
  }

  return (
    <ul className="divide-y divide-slate-100 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      {plans.map((plan) => (
        <li key={plan.id}>
          <button
            type="button"
            onClick={() => onSelect(plan.id)}
            className={`block w-full px-4 py-3 text-left text-sm hover:bg-slate-50 dark:bg-slate-800/60 ${
              plan.id === selectedId ? 'bg-brand-50' : ''
            }`}
          >
            <p className="font-medium text-slate-900 dark:text-slate-100">
              {labelize(plan.strategy)} &middot; {formatDateTime(plan.created_at)}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {t('planning.payoffInterest', {
                date: formatDate(plan.expected_payoff_date),
                interest: formatCurrency(plan.total_interest),
              })}
            </p>
          </button>
        </li>
      ))}
    </ul>
  )
}
