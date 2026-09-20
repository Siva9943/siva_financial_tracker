import { useTranslation } from 'react-i18next'
import { formatCurrency, formatDate } from '../../utils/format.js'

export default function LoanSimulatorComparisonTable({ scenarios }) {
  const { t } = useTranslation()
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 text-xs uppercase text-slate-500 dark:text-slate-400">
          <tr>
            <th className="px-4 py-2">{t('loans.simulatorTable.extraPayment')}</th>
            <th className="px-4 py-2">{t('loans.simulatorTable.payoffDate')}</th>
            <th className="px-4 py-2">{t('loans.simulatorTable.monthsToPayoff')}</th>
            <th className="px-4 py-2">{t('loans.simulatorTable.monthsSaved')}</th>
            <th className="px-4 py-2">{t('loans.simulatorTable.totalInterest')}</th>
            <th className="px-4 py-2">{t('loans.simulatorTable.interestSaved')}</th>
            <th className="px-4 py-2">{t('loans.simulatorTable.totalPayment')}</th>
          </tr>
        </thead>
        <tbody>
          {scenarios.map((scenario) => (
            <tr
              key={scenario.extra_payment}
              className={`border-b border-slate-100 dark:border-slate-800 last:border-0 ${
                Number(scenario.extra_payment) === 0 ? 'bg-slate-50 dark:bg-slate-800/60' : ''
              }`}
            >
              <td className="px-4 py-2 font-medium text-slate-900 dark:text-slate-100">
                {formatCurrency(scenario.extra_payment)}
                {Number(scenario.extra_payment) === 0 && <span className="ml-1 text-xs text-slate-400 dark:text-slate-500">{t('loans.simulatorTable.current')}</span>}
              </td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatDate(scenario.payoff_date)}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{scenario.months_to_payoff}</td>
              <td className="px-4 py-2 text-green-700">{scenario.months_saved > 0 ? scenario.months_saved : '—'}</td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(scenario.total_interest)}</td>
              <td className="px-4 py-2 text-green-700">
                {Number(scenario.interest_saved) > 0 ? formatCurrency(scenario.interest_saved) : '—'}
              </td>
              <td className="px-4 py-2 text-slate-600 dark:text-slate-400">{formatCurrency(scenario.total_payment)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
