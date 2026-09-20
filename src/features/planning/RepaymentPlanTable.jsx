import { useTranslation } from 'react-i18next'
import { formatCurrency, formatDate } from '../../utils/format.js'

export default function RepaymentPlanTable({ items }) {
  const { t } = useTranslation()

  if (!items || items.length === 0) return null

  return (
    <div className="max-h-96 overflow-x-auto overflow-y-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="sticky top-0 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 text-xs uppercase text-slate-500 dark:text-slate-400">
          <tr>
            <th className="px-4 py-2">{t('planning.month')}</th>
            <th className="px-4 py-2">{t('planning.loan')}</th>
            <th className="px-4 py-2">{t('planning.normalEmi')}</th>
            <th className="px-4 py-2">{t('planning.extra')}</th>
            <th className="px-4 py-2">{t('planning.principal')}</th>
            <th className="px-4 py-2">{t('planning.interest')}</th>
            <th className="px-4 py-2">{t('planning.closing')}</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={`${item.month_number}-${item.loan_name}`} className="border-b border-slate-100 dark:border-slate-800 last:border-0">
              <td className="px-4 py-2 text-slate-500 dark:text-slate-400">
                {item.month_number}
                <span className="ml-1 text-xs text-slate-400 dark:text-slate-500">{formatDate(item.month_date)}</span>
              </td>
              <td className="px-4 py-2 font-medium text-slate-900 dark:text-slate-100">{item.loan_name}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(item.normal_emi)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">
                {Number(item.extra_payment) > 0 ? formatCurrency(item.extra_payment) : '—'}
              </td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(item.principal_paid)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(item.interest_paid)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(item.closing_balance)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
