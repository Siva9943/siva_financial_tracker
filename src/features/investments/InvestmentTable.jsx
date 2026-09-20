import { Pencil, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import EmptyState from '../../components/EmptyState.jsx'
import { labelize } from '../../utils/categories.js'
import { formatCurrency } from '../../utils/format.js'
import { INVESTMENT_STATUS_STYLES } from '../../utils/investmentOptions.js'

function formatSignedCurrency(amount) {
  const value = Number(amount ?? 0)
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${formatCurrency(value)}`
}

function formatSignedPercent(value) {
  const num = Number(value ?? 0)
  const prefix = num > 0 ? '+' : ''
  return `${prefix}${num.toFixed(2)}%`
}

function gainLossClass(value) {
  const num = Number(value ?? 0)
  if (num > 0) return 'text-green-600 dark:text-green-400'
  if (num < 0) return 'text-red-600 dark:text-red-400'
  return 'text-slate-600 dark:text-slate-400'
}

export default function InvestmentTable({ investments, onEdit, onDelete }) {
  const { t } = useTranslation()
  if (investments.length === 0) {
    return <EmptyState title={t('investments.tableEmptyTitle')} description={t('investments.tableEmptyDescription')} />
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 text-xs uppercase text-slate-500 dark:text-slate-400">
          <tr>
            <th className="px-4 py-3">{t('investments.table.investment')}</th>
            <th className="px-4 py-3">{t('investments.table.type')}</th>
            <th className="px-4 py-3">{t('investments.table.quantity')}</th>
            <th className="px-4 py-3">{t('investments.table.avgBuyPrice')}</th>
            <th className="px-4 py-3">{t('investments.table.currentPrice')}</th>
            <th className="px-4 py-3">{t('investments.table.invested')}</th>
            <th className="px-4 py-3">{t('investments.table.currentValue')}</th>
            <th className="px-4 py-3">{t('investments.table.profitLoss')}</th>
            <th className="px-4 py-3">{t('investments.table.returnPercent')}</th>
            <th className="px-4 py-3">{t('investments.table.status')}</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {investments.map((investment) => (
            <tr
              key={investment.id}
              className="border-b border-slate-100 dark:border-slate-800 last:border-0 hover:bg-slate-50 dark:bg-slate-800/60"
            >
              <td className="px-4 py-3">
                <Link to={`/investments/${investment.id}`} className="font-medium text-brand-600 hover:underline">
                  {investment.name}
                </Link>
                {investment.symbol && <p className="text-xs text-slate-500 dark:text-slate-400">{investment.symbol}</p>}
              </td>
              <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{labelize(investment.investment_type)}</td>
              <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{investment.quantity}</td>
              <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{formatCurrency(investment.average_buy_price)}</td>
              <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{formatCurrency(investment.current_price)}</td>
              <td className="px-4 py-3 text-slate-900 dark:text-slate-100">{formatCurrency(investment.total_invested)}</td>
              <td className="px-4 py-3 text-slate-900 dark:text-slate-100">{formatCurrency(investment.current_value)}</td>
              <td className={`px-4 py-3 font-medium ${gainLossClass(investment.unrealized_profit_loss)}`}>
                {formatSignedCurrency(investment.unrealized_profit_loss)}
              </td>
              <td className={`px-4 py-3 font-medium ${gainLossClass(investment.return_percentage)}`}>
                {formatSignedPercent(investment.return_percentage)}
              </td>
              <td className="px-4 py-3">
                <span className={`rounded-full px-2 py-1 text-xs font-medium ${INVESTMENT_STATUS_STYLES[investment.status]}`}>
                  {labelize(investment.status)}
                </span>
              </td>
              <td className="px-4 py-3">
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => onEdit(investment)}
                    aria-label={t('common.edit')}
                    className="text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:text-slate-300"
                  >
                    <Pencil className="size-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(investment)}
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
