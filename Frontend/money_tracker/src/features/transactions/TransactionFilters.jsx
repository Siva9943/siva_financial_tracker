import { Search } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Select from '../../components/Select.jsx'
import { TRANSACTION_TYPES, labelize } from '../../utils/categories.js'

export default function TransactionFilters({ filters, onChange, hideTypeFilter }) {
  const { t } = useTranslation()
  const update = (patch) => onChange({ ...filters, ...patch })

  return (
    <div className="flex flex-wrap items-end gap-3">
      <label className="block">
        <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">{t('common.search')}</span>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
          <input
            value={filters.search}
            onChange={(event) => update({ search: event.target.value })}
            placeholder={t('transactions.searchPlaceholder')}
            className="w-64 rounded-lg border border-slate-300 py-2 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
      </label>

      {!hideTypeFilter && (
        <Select
          label={t('transactions.type')}
          value={filters.transaction_type}
          onChange={(event) => update({ transaction_type: event.target.value })}
        >
          <option value="">{t('transactions.allTypes')}</option>
          {TRANSACTION_TYPES.map((type) => (
            <option key={type} value={type}>
              {labelize(type)}
            </option>
          ))}
        </Select>
      )}

      <label className="block">
        <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">{t('transactions.from')}</span>
        <input
          type="date"
          value={filters.date_from}
          onChange={(event) => update({ date_from: event.target.value })}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500"
        />
      </label>

      <label className="block">
        <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">{t('transactions.to')}</span>
        <input
          type="date"
          value={filters.date_to}
          onChange={(event) => update({ date_to: event.target.value })}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500"
        />
      </label>
    </div>
  )
}
