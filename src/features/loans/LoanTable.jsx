import { Pencil, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import EmptyState from '../../components/EmptyState.jsx'
import { labelize } from '../../utils/categories.js'
import { formatCurrency, formatDate } from '../../utils/format.js'
import { LOAN_STATUS_STYLES } from '../../utils/loanOptions.js'

export default function LoanTable({ loans, onEdit, onDelete }) {
  const { t } = useTranslation()
  if (loans.length === 0) {
    return <EmptyState title={t('loans.tableEmptyTitle')} description={t('loans.tableEmptyDescription')} />
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 text-xs uppercase text-slate-500 dark:text-slate-400">
          <tr>
            <th className="px-4 py-3">{t('loans.table.name')}</th>
            <th className="px-4 py-3">{t('loans.table.type')}</th>
            <th className="px-4 py-3">{t('loans.table.outstanding')}</th>
            <th className="px-4 py-3">{t('loans.table.rate')}</th>
            <th className="px-4 py-3">{t('loans.table.nextDue')}</th>
            <th className="px-4 py-3">{t('loans.table.status')}</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {loans.map((loan) => (
            <tr key={loan.id} className="border-b border-slate-100 dark:border-slate-800 last:border-0 hover:bg-slate-50 dark:bg-slate-800/60">
              <td className="px-4 py-3">
                <Link to={`/loans/${loan.id}`} className="font-medium text-brand-600 hover:underline">
                  {loan.loan_name}
                </Link>
                <p className="text-xs text-slate-500 dark:text-slate-400">{loan.lender}</p>
              </td>
              <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{labelize(loan.loan_type)}</td>
              <td className="px-4 py-3 text-slate-900 dark:text-slate-100">
                {formatCurrency(loan.outstanding_principal)}
                <span className="text-xs text-slate-400 dark:text-slate-500"> / {formatCurrency(loan.original_principal)}</span>
              </td>
              <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{loan.annual_interest_rate}%</td>
              <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{loan.next_due_date ? formatDate(loan.next_due_date) : '—'}</td>
              <td className="px-4 py-3">
                <span className={`rounded-full px-2 py-1 text-xs font-medium ${LOAN_STATUS_STYLES[loan.status]}`}>
                  {labelize(loan.status)}
                </span>
              </td>
              <td className="px-4 py-3">
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => onEdit(loan)}
                    aria-label={t('common.edit')}
                    className="text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:text-slate-300"
                  >
                    <Pencil className="size-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(loan)}
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
