import { ArrowDown, ArrowUp, Pencil, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import EmptyState from '../../components/EmptyState.jsx'
import { formatCurrency, formatDate } from '../../utils/format.js'
import { labelize } from '../../utils/categories.js'

const TYPE_STYLES = {
  INCOME: 'bg-green-50 text-green-700',
  EXPENSE: 'bg-red-50 text-red-700',
  LOAN_PAYMENT: 'bg-amber-50 text-amber-700',
  REFUND: 'bg-blue-50 text-blue-700',
  TRANSFER: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300',
}

const ALL_COLUMNS = [
  { key: 'transaction_date', labelKey: 'transactions.date' },
  { key: 'transaction_type', labelKey: 'transactions.type' },
  { key: 'category', labelKey: 'transactions.category' },
  { key: 'description', labelKey: 'transactions.description' },
  { key: 'amount', labelKey: 'transactions.amount' },
]

export default function TransactionTable({ transactions, ordering, onSortChange, onEdit, onDelete, hideType }) {
  const { t } = useTranslation()

  if (transactions.length === 0) {
    return <EmptyState title={t('transactions.noTransactionsYet')} description={t('transactions.addFirstTransaction')} />
  }

  const columns = hideType ? ALL_COLUMNS.filter((column) => column.key !== 'transaction_type') : ALL_COLUMNS
  const currentField = ordering?.replace('-', '')
  const isDescending = ordering?.startsWith('-')

  const toggleSort = (field) => {
    if (currentField === field) {
      onSortChange(isDescending ? field : `-${field}`)
    } else {
      onSortChange(`-${field}`)
    }
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 text-xs uppercase text-slate-500 dark:text-slate-400">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className="px-4 py-3">
                <button
                  type="button"
                  onClick={() => toggleSort(column.key)}
                  className="flex items-center gap-1 hover:text-slate-800"
                >
                  {t(column.labelKey)}
                  {currentField === column.key &&
                    (isDescending ? <ArrowDown className="size-3" /> : <ArrowUp className="size-3" />)}
                </button>
              </th>
            ))}
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {transactions.map((txn) => (
            <tr key={txn.id} className="border-b border-slate-100 dark:border-slate-800 last:border-0 hover:bg-slate-50 dark:bg-slate-800/60">
              <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{formatDate(txn.transaction_date)}</td>
              {!hideType && (
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-1 text-xs font-medium ${TYPE_STYLES[txn.transaction_type]}`}>
                    {labelize(txn.transaction_type)}
                  </span>
                </td>
              )}
              <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{txn.category}</td>
              <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{txn.description || '—'}</td>
              <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{formatCurrency(txn.amount)}</td>
              <td className="px-4 py-3">
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => onEdit(txn)}
                    aria-label={t('common.edit')}
                    className="text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:text-slate-300"
                  >
                    <Pencil className="size-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(txn)}
                    aria-label={t('common.delete')}
                    className="text-slate-400 dark:text-slate-500 hover:text-red-600"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
