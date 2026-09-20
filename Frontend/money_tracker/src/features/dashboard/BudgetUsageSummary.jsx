import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import EmptyState from '../../components/EmptyState.jsx'
import { formatCurrency } from '../../utils/format.js'

export default function BudgetUsageSummary({ usage }) {
  const { t } = useTranslation()
  const budgeted = Number(usage?.total_budgeted ?? 0)
  const spent = Number(usage?.total_spent ?? 0)

  if (budgeted === 0) {
    return <EmptyState title={t('dashboard.noBudgetsSetTitle')} description={t('dashboard.noBudgetsSetDescription')} />
  }

  const percentage = Math.min(100, (spent / budgeted) * 100)
  const barColor = percentage >= 100 ? 'bg-red-500' : percentage >= 50 ? 'bg-amber-500' : 'bg-brand-500'

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{t('dashboard.budgetUsage')}</h3>
        <Link to="/budgets" className="text-xs text-brand-600 hover:underline">
          {t('dashboard.viewAll')}
        </Link>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${percentage}%` }} />
      </div>
      <div className="mt-2 flex justify-between text-xs text-slate-500 dark:text-slate-400">
        <span>{t('dashboard.spentAmount', { amount: formatCurrency(spent) })}</span>
        <span>{t('dashboard.budgetedAmount', { amount: formatCurrency(budgeted) })}</span>
      </div>
    </div>
  )
}
