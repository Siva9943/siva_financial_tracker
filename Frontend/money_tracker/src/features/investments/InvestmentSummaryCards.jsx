import { useTranslation } from 'react-i18next'
import StatCard from '../../components/StatCard.jsx'
import { formatCurrency } from '../../utils/format.js'

function signedAccent(value) {
  const num = Number(value ?? 0)
  if (num > 0) return 'text-green-600 dark:text-green-400'
  if (num < 0) return 'text-red-600 dark:text-red-400'
  return 'text-slate-900 dark:text-slate-100'
}

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

export default function InvestmentSummaryCards({ portfolio }) {
  const { t } = useTranslation()
  if (!portfolio) return null

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-3 lg:grid-cols-6">
      <StatCard label={t('investments.summary.totalInvested')} value={formatCurrency(portfolio.total_invested)} />
      <StatCard label={t('investments.summary.currentValue')} value={formatCurrency(portfolio.current_value)} />
      <StatCard
        label={t('investments.summary.totalReturn')}
        value={formatSignedCurrency(portfolio.total_return)}
        accent={signedAccent(portfolio.total_return)}
      />
      <StatCard
        label={t('investments.summary.returnPercent')}
        value={formatSignedPercent(portfolio.return_percentage)}
        accent={signedAccent(portfolio.return_percentage)}
      />
      <StatCard label={t('investments.summary.dividendIncome')} value={formatCurrency(portfolio.dividend_income)} />
      <StatCard label={t('investments.summary.numberOfInvestments')} value={portfolio.investment_count} />
    </div>
  )
}
