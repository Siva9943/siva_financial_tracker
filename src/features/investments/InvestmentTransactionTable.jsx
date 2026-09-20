import { useTranslation } from 'react-i18next'
import EmptyState from '../../components/EmptyState.jsx'
import { labelize } from '../../utils/categories.js'
import { formatCurrency, formatDate } from '../../utils/format.js'

const TRANSACTION_TYPE_STYLES = {
  BUY: 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  SELL: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  DIVIDEND: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  BONUS: 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  SPLIT: 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  FEE: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  DEPOSIT: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
  WITHDRAWAL: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
}

function formatOrDash(value, formatter = (v) => v) {
  if (value === null || value === undefined || value === '') return '—'
  return formatter(value)
}

export default function InvestmentTransactionTable({ transactions, filterType }) {
  const { t } = useTranslation()
  const rows = filterType ? transactions.filter((tx) => tx.transaction_type === filterType) : transactions

  if (!rows || rows.length === 0) {
    return (
      <EmptyState
        title={t('investments.transactionsEmptyTitle')}
        description={t('investments.transactionsEmptyDescription')}
      />
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 text-xs uppercase text-slate-500 dark:text-slate-400">
          <tr>
            <th className="px-4 py-2">{t('investments.table.date')}</th>
            <th className="px-4 py-2">{t('investments.table.type')}</th>
            <th className="px-4 py-2">{t('investments.table.quantity')}</th>
            <th className="px-4 py-2">{t('investments.table.price')}</th>
            <th className="px-4 py-2">{t('investments.table.amount')}</th>
            <th className="px-4 py-2">{t('investments.table.fees')}</th>
            <th className="px-4 py-2">{t('investments.table.tax')}</th>
            <th className="px-4 py-2">{t('investments.table.reference')}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((tx) => (
            <tr key={tx.id} className="border-b border-slate-100 dark:border-slate-800 last:border-0">
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatDate(tx.transaction_date)}</td>
              <td className="px-4 py-2">
                <span className={`rounded-full px-2 py-1 text-xs font-medium ${TRANSACTION_TYPE_STYLES[tx.transaction_type] ?? ''}`}>
                  {labelize(tx.transaction_type)}
                </span>
              </td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatOrDash(tx.quantity)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatOrDash(tx.price, formatCurrency)}</td>
              <td className="px-4 py-2 font-medium text-slate-900 dark:text-slate-100">{formatOrDash(tx.amount, formatCurrency)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatOrDash(tx.fees, formatCurrency)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatOrDash(tx.tax, formatCurrency)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatOrDash(tx.reference)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
