import { AlarmClock, Check, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import EmptyState from '../../components/EmptyState.jsx'
import { labelize } from '../../utils/categories.js'
import { formatCurrency, formatDate } from '../../utils/format.js'

function addDays(isoDate, days) {
  const d = new Date(`${isoDate}T00:00:00`)
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

export default function ReminderList({ reminders, onSnooze, onComplete, onDelete }) {
  const { t } = useTranslation()
  if (reminders.length === 0) {
    return <EmptyState title={t('notifications.noReminders')} description={t('notifications.addReminderPrompt')} />
  }

  const today = new Date().toISOString().slice(0, 10)

  return (
    <ul className="divide-y divide-slate-100 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      {reminders.map((reminder) => {
        const isSnoozed = reminder.snoozed_until && reminder.snoozed_until > today
        const isOverdue = !isSnoozed && reminder.reminder_date < today

        return (
          <li key={reminder.id} className="flex items-center justify-between gap-3 px-4 py-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <p className="font-medium text-slate-900 dark:text-slate-100">{reminder.description}</p>
                <span className="rounded-full bg-slate-100 dark:bg-slate-700 px-2 py-0.5 text-xs text-slate-600 dark:text-slate-400">
                  {labelize(reminder.reminder_type)}
                </span>
                {reminder.recurrence !== 'NONE' && (
                  <span className="rounded-full bg-brand-50 px-2 py-0.5 text-xs text-brand-700">
                    {labelize(reminder.recurrence)}
                  </span>
                )}
              </div>
              <p className={`text-xs ${isOverdue ? 'text-red-600' : 'text-slate-500 dark:text-slate-400'}`}>
                {formatDate(reminder.reminder_date)}
                {reminder.amount && ` · ${formatCurrency(reminder.amount)}`}
                {isSnoozed && ` · ${t('notifications.snoozedUntil', { date: formatDate(reminder.snoozed_until) })}`}
                {isOverdue && ` · ${t('notifications.overdue')}`}
              </p>
            </div>
            <div className="flex shrink-0 gap-2">
              <button
                type="button"
                onClick={() => onSnooze(reminder.id, addDays(today, 7))}
                aria-label={t('notifications.snoozeOneWeek')}
                title={t('notifications.snoozeOneWeek')}
                className="text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:text-slate-300"
              >
                <AlarmClock className="size-4" />
              </button>
              <button
                type="button"
                onClick={() => onComplete(reminder.id)}
                aria-label={t('notifications.complete')}
                title={t('notifications.markComplete')}
                className="text-slate-400 dark:text-slate-500 hover:text-green-600"
              >
                <Check className="size-4" />
              </button>
              <button
                type="button"
                onClick={() => onDelete(reminder)}
                aria-label={t('common.delete')}
                title={t('common.delete')}
                className="text-slate-400 dark:text-slate-500 hover:text-red-600"
              >
                <Trash2 className="size-4" />
              </button>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
