import { Pencil, PlusCircle, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { labelize } from '../../utils/categories.js'
import { formatCurrency, formatDate } from '../../utils/format.js'
import { GOAL_STATUS_STYLES } from '../../utils/goalOptions.js'

export default function GoalCard({ goal, onEdit, onDelete, onContribute }) {
  const { t } = useTranslation()
  const percentage = Math.min(100, goal.percentage_complete)
  const barColor = goal.status === 'COMPLETED' ? 'bg-green-500' : goal.is_on_track ? 'bg-brand-500' : 'bg-amber-500'

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <div className="mb-2 flex items-start justify-between">
        <div>
          <p className="font-medium text-slate-900 dark:text-slate-100">{goal.name}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{t(`goals.type.${goal.goal_type}`, labelize(goal.goal_type))}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${GOAL_STATUS_STYLES[goal.status]}`}>
            {t(`goals.status.${goal.status}`, labelize(goal.status))}
          </span>
          <button type="button" onClick={() => onEdit(goal)} aria-label={t('common.edit')} className="text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:text-slate-300">
            <Pencil className="size-4" />
          </button>
          <button type="button" onClick={() => onDelete(goal)} aria-label={t('common.delete')} className="text-slate-400 dark:text-slate-500 hover:text-red-600">
            <Trash2 className="size-4" />
          </button>
        </div>
      </div>

      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${percentage}%` }} />
      </div>
      <div className="mt-2 flex justify-between text-xs text-slate-500 dark:text-slate-400">
        <span>{formatCurrency(goal.current_amount)}</span>
        <span>{formatCurrency(goal.target_amount)}</span>
      </div>

      <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600 dark:text-slate-400">
        <div>
          <dt className="text-slate-400 dark:text-slate-500">{t('goals.remaining')}</dt>
          <dd className="font-medium">{formatCurrency(goal.remaining_amount)}</dd>
        </div>
        <div>
          <dt className="text-slate-400 dark:text-slate-500">{t('goals.targetDate')}</dt>
          <dd className="font-medium">{formatDate(goal.target_date)}</dd>
        </div>
        <div>
          <dt className="text-slate-400 dark:text-slate-500">{t('goals.neededPerMonth')}</dt>
          <dd className="font-medium">{formatCurrency(goal.required_monthly_contribution)}</dd>
        </div>
        <div>
          <dt className="text-slate-400 dark:text-slate-500">{t('goals.estCompletion')}</dt>
          <dd className={`font-medium ${goal.is_on_track ? '' : 'text-amber-600'}`}>
            {goal.estimated_completion_date ? formatDate(goal.estimated_completion_date) : '—'}
          </dd>
        </div>
      </dl>

      {goal.status === 'IN_PROGRESS' && (
        <button
          type="button"
          onClick={() => onContribute(goal)}
          className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg border border-slate-200 dark:border-slate-700 py-1.5 text-sm text-brand-600 hover:bg-brand-50"
        >
          <PlusCircle className="size-4" />
          {t('goals.addContribution')}
        </button>
      )}
    </div>
  )
}
