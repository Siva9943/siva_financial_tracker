import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as loanApi from '../api/loanApi'
import EmptyState from '../components/EmptyState.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import Select from '../components/Select.jsx'
import StatCard from '../components/StatCard.jsx'
import LoanSimulatorChart from '../features/loans/LoanSimulatorChart.jsx'
import LoanSimulatorComparisonTable from '../features/loans/LoanSimulatorComparisonTable.jsx'
import { getErrorMessage } from '../utils/apiError.js'
import { formatCurrency, formatDate } from '../utils/format.js'

export default function LoanSimulator() {
  const { t } = useTranslation()
  const [loans, setLoans] = useState([])
  const [loanId, setLoanId] = useState('')
  const [result, setResult] = useState(null)
  const [isLoadingLoans, setIsLoadingLoans] = useState(true)
  const [isSimulating, setIsSimulating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchLoans = async () => {
      try {
        const data = await loanApi.listLoans({ status: 'ACTIVE' })
        setLoans(data.results)
        if (data.results.length > 0) setLoanId(String(data.results[0].id))
      } catch (err) {
        setError(getErrorMessage(err, t('loans.errors.loadLoans')))
      } finally {
        setIsLoadingLoans(false)
      }
    }
    fetchLoans()
  }, [])

  useEffect(() => {
    if (!loanId) return

    const simulate = async () => {
      setIsSimulating(true)
      setError('')
      try {
        const data = await loanApi.simulateLoan({ loan_id: Number(loanId) })
        setResult(data)
      } catch (err) {
        setError(getErrorMessage(err, t('loans.errors.simulateLoan')))
        setResult(null)
      } finally {
        setIsSimulating(false)
      }
    }
    simulate()
  }, [loanId])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.loanSimulator')}</h1>

      {isLoadingLoans ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : loans.length === 0 ? (
        <EmptyState title={t('loans.simulator.noActiveLoansTitle')} description={t('loans.simulator.noActiveLoansDescription')} />
      ) : (
        <>
          <div className="max-w-xs">
            <Select label={t('loans.fields.loan')} value={loanId} onChange={(e) => setLoanId(e.target.value)}>
              {loans.map((loan) => (
                <option key={loan.id} value={loan.id}>
                  {loan.loan_name}
                </option>
              ))}
            </Select>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          {isSimulating ? (
            <div className="flex justify-center py-16">
              <LoadingSpinner />
            </div>
          ) : (
            result && (
              <>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <StatCard label={t('loans.simulator.currentEmi')} value={formatCurrency(result.baseline.emi)} />
                  <StatCard label={t('loans.simulator.currentPayoffDate')} value={formatDate(result.baseline.payoff_date)} />
                  <StatCard label={t('loans.simulator.currentTotalInterest')} value={formatCurrency(result.baseline.total_interest)} />
                  <StatCard label={t('loans.simulator.currentTotalPayment')} value={formatCurrency(result.baseline.total_payment)} />
                </div>

                <LoanSimulatorChart scenarios={result.scenarios} />
                <LoanSimulatorComparisonTable scenarios={result.scenarios} />
              </>
            )
          )}
        </>
      )}
    </div>
  )
}
