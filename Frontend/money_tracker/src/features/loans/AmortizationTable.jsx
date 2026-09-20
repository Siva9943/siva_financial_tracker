import { useTranslation } from 'react-i18next'
import { formatCurrency, formatDate } from '../../utils/format.js'

export default function AmortizationTable({ schedule }) {
  const { t } = useTranslation()
  if (!schedule || schedule.length === 0) return null

  return (
    <div className="max-h-96 overflow-x-auto overflow-y-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="sticky top-0 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 text-xs uppercase text-slate-500 dark:text-slate-400">
          <tr>
            <th className="px-4 py-2">{t('loans.table.number')}</th>
            <th className="px-4 py-2">{t('loans.table.date')}</th>
            <th className="px-4 py-2">{t('loans.table.opening')}</th>
            <th className="px-4 py-2">{t('loans.table.payment')}</th>
            <th className="px-4 py-2">{t('loans.table.principal')}</th>
            <th className="px-4 py-2">{t('loans.table.interest')}</th>
            <th className="px-4 py-2">{t('loans.table.closing')}</th>
          </tr>
        </thead>
        <tbody>
          {schedule.map((row) => (
            <tr key={row.period} className="border-b border-slate-100 dark:border-slate-800 last:border-0">
              <td className="px-4 py-2 text-slate-500 dark:text-slate-400">{row.period}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatDate(row.date)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(row.opening_balance)}</td>
              <td className="px-4 py-2 font-medium text-slate-900 dark:text-slate-100">{formatCurrency(row.payment)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(row.principal)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(row.interest)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(row.closing_balance)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
