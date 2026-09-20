import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as analyticsApi from '../api/analyticsApi'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import AnalyticsMetricCard from '../features/dashboard/AnalyticsMetricCard.jsx'
import BudgetUsageSummary from '../features/dashboard/BudgetUsageSummary.jsx'
import DashboardCards from '../features/dashboard/DashboardCards.jsx'
import DateRangeSelector from '../features/dashboard/DateRangeSelector.jsx'
import DebtPayoffChart from '../features/dashboard/DebtPayoffChart.jsx'
import HistoricalMetricsChart from '../features/dashboard/HistoricalMetricsChart.jsx'
import IncomeExpenseChart from '../features/dashboard/IncomeExpenseChart.jsx'
import InterestPrincipalChart from '../features/dashboard/InterestPrincipalChart.jsx'
import LoanBalanceChart from '../features/dashboard/LoanBalanceChart.jsx'
import InvestmentSummaryWidget from '../features/investments/InvestmentSummaryWidget.jsx'
import CategoryBreakdownChart from '../features/transactions/CategoryBreakdownChart.jsx'
import { getErrorMessage } from '../utils/apiError.js'

export default function Dashboard() {
  const { t } = useTranslation()
  const METRIC_LABELS = {
    savings_rate: t('dashboard.savingsRate'),
    debt_to_income: t('dashboard.debtToIncome'),
    expense_ratio: t('dashboard.expenseRatio'),
    interest_burden: t('dashboard.interestBurden'),
  }
  const [range, setRange] = useState('CURRENT_MONTH')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [dashboard, setDashboard] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (range === 'CUSTOM' && (!start || !end)) return

    const fetchData = async () => {
      setIsLoading(true)
      setError('')
      try {
        const params = range === 'CUSTOM' ? { range, start, end } : { range }
        const [dashboardData, analyticsData] = await Promise.all([
          analyticsApi.getDashboard(params),
          analyticsApi.getAnalytics(params),
        ])
        setDashboard(dashboardData)
        setAnalytics(analyticsData)
      } catch (err) {
        setError(getErrorMessage(err, t('dashboard.loadError')))
      } finally {
        setIsLoading(false)
      }
    }
    fetchData()
  }, [range, start, end])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.dashboard')}</h1>
        <DateRangeSelector
          range={range}
          onRangeChange={setRange}
          start={start}
          end={end}
          onStartChange={setStart}
          onEndChange={setEnd}
        />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {isLoading || !dashboard || !analytics ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : (
        <>
          <DashboardCards cards={dashboard.cards} />

          <InvestmentSummaryWidget />

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {Object.entries(analytics.metrics).map(([key, metric]) => (
              <AnalyticsMetricCard key={key} label={METRIC_LABELS[key]} metric={metric} />
            ))}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <IncomeExpenseChart data={dashboard.charts.income_vs_expense} />
            <CategoryBreakdownChart data={dashboard.charts.expense_by_category} title={t('dashboard.expenses')} />
            <LoanBalanceChart data={dashboard.charts.loan_balance} />
            <InterestPrincipalChart data={dashboard.charts.interest_vs_principal} />
            <BudgetUsageSummary usage={dashboard.charts.budget_usage} />
            <DebtPayoffChart data={dashboard.charts.debt_payoff_projection} />
          </div>

          <HistoricalMetricsChart historical={analytics.historical} />
        </>
      )}
    </div>
  )
}
