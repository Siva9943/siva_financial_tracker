import { Minus, TrendingDown, TrendingUp } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export default function AnalyticsMetricCard({ label, metric }) {
  const { t } = useTranslation()
  const { current, previous, change } = metric

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-900 dark:text-slate-100">{current !== null ? `${current}%` : '—'}</p>
      <div className="mt-1 flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
        {change === null ? (
          <span>{t('dashboard.noPriorPeriodData')}</span>
        ) : (
          <>
            {change > 0 ? (
              <TrendingUp className="size-3.5 text-slate-400 dark:text-slate-500" />
            ) : change < 0 ? (
              <TrendingDown className="size-3.5 text-slate-400 dark:text-slate-500" />
            ) : (
              <Minus className="size-3.5 text-slate-400 dark:text-slate-500" />
            )}
            <span>
              {change > 0 ? '+' : ''}
              {change} {t('dashboard.ptsVs', { previous })}
            </span>
          </>
        )}
      </div>
    </div>
  )
}
