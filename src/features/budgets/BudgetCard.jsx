import { Pencil, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { formatCurrency } from '../../utils/format.js'
import { BUDGET_STATUS_STYLES } from '../../utils/budgetOptions.js'

export default function BudgetCard({ budget, onEdit, onDelete }) {
  const { t } = useTranslation()
  const styles = BUDGET_STATUS_STYLES[budget.status]
  const barWidth = Math.min(100, budget.percentage_used)

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <div className="mb-2 flex items-start justify-between">
        <div>
          <p className="font-medium text-slate-900 dark:text-slate-100">{budget.category}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {t('budgets.spentOfAmount', { spent: formatCurrency(budget.spent), amount: formatCurrency(budget.amount) })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles.badge}`}>
            {t(`budgets.status.${budget.status}`, budget.status)}
          </span>
          <button type="button" onClick={() => onEdit(budget)} aria-label={t('common.edit')} className="text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:text-slate-300">
            <Pencil className="size-4" />
          </button>
          <button type="button" onClick={() => onDelete(budget)} aria-label={t('common.delete')} className="text-slate-400 dark:text-slate-500 hover:text-red-600">
            <Trash2 className="size-4" />
          </button>
        </div>
      </div>

      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
        <div className={`h-full rounded-full ${styles.bar}`} style={{ width: `${barWidth}%` }} />
      </div>

      <div className="mt-2 flex justify-between text-xs text-slate-500 dark:text-slate-400">
        <span>{t('budgets.percentUsed', { percent: budget.percentage_used })}</span>
        <span>{t('budgets.amountRemaining', { amount: formatCurrency(budget.remaining) })}</span>
      </div>
    </div>
  )
}
