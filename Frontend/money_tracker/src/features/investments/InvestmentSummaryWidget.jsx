import { ArrowRight } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import * as investmentApi from '../../api/investmentApi'
import { formatCurrency } from '../../utils/format.js'

function signedAccent(value) {
  return Number(value ?? 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
}

function formatSignedCurrency(amount) {
  const value = Number(amount ?? 0)
  const prefix = value >= 0 ? '+' : ''
  return `${prefix}${formatCurrency(value)}`
}

function formatSignedPercent(value) {
  const num = Number(value ?? 0)
  const prefix = num >= 0 ? '+' : ''
  return `${prefix}${num.toFixed(2)}%`
}

export default function InvestmentSummaryWidget() {
  const { t } = useTranslation()
  const [portfolio, setPortfolio] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    investmentApi
      .getPortfolio()
      .then((data) => {
        if (!cancelled) setPortfolio(data)
      })
      .catch(() => {
        if (!cancelled) setPortfolio(null)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (isLoading || !portfolio) return null

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('dashboard.investmentPortfolio')}</h3>

      {!portfolio.investment_count ? (
        <div className="flex flex-col items-start gap-2">
          <p className="text-sm text-slate-500 dark:text-slate-400">{t('dashboard.noInvestmentsYetPrompt')}</p>
          <Link
            to="/investments"
            className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
          >
            {t('dashboard.viewPortfolio')}
            <ArrowRight className="size-4" />
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{formatCurrency(portfolio.current_value)}</p>
          <p className="text-sm">
            <span className={`font-medium ${signedAccent(portfolio.total_return)}`}>
              {formatSignedCurrency(portfolio.total_return)}
            </span>{' '}
            <span className={signedAccent(portfolio.return_percentage)}>
              {formatSignedPercent(portfolio.return_percentage)}
            </span>
          </p>
          <Link
            to="/investments"
            className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
          >
            {t('dashboard.viewPortfolio')}
            <ArrowRight className="size-4" />
          </Link>
        </div>
      )}
    </div>
  )
}
