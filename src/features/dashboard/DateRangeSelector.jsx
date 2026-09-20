import { useTranslation } from 'react-i18next'
import Select from '../../components/Select.jsx'

export default function DateRangeSelector({ range, onRangeChange, start, end, onStartChange, onEndChange }) {
  const { t } = useTranslation()
  const RANGES = [
    { value: 'CURRENT_MONTH', label: t('dashboard.currentMonth') },
    { value: 'PREVIOUS_MONTH', label: t('dashboard.previousMonth') },
    { value: 'CURRENT_YEAR', label: t('dashboard.currentYear') },
    { value: 'CUSTOM', label: t('dashboard.customRange') },
  ]

  return (
    <div className="flex flex-wrap items-end gap-3">
      <Select label={t('dashboard.dateRange')} value={range} onChange={(e) => onRangeChange(e.target.value)}>
        {RANGES.map((r) => (
          <option key={r.value} value={r.value}>
            {r.label}
          </option>
        ))}
      </Select>

      {range === 'CUSTOM' && (
        <>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">{t('dashboard.from')}</span>
            <input
              type="date"
              value={start}
              onChange={(e) => onStartChange(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">{t('dashboard.to')}</span>
            <input
              type="date"
              value={end}
              onChange={(e) => onEndChange(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500"
            />
          </label>
        </>
      )}
    </div>
  )
}
