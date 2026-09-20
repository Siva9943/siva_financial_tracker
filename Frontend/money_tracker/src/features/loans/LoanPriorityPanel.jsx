import { ArrowDown, ArrowUp } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import * as loanApi from '../../api/loanApi'
import EmptyState from '../../components/EmptyState.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import Select from '../../components/Select.jsx'
import { getErrorMessage } from '../../utils/apiError.js'
import { formatCurrency } from '../../utils/format.js'

const PRIORITY_STYLES = {
  High: 'bg-red-50 text-red-700',
  Medium: 'bg-amber-50 text-amber-700',
  Low: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300',
}

const STRATEGY_VALUES = ['AVALANCHE', 'SNOWBALL', 'CUSTOM']

export default function LoanPriorityPanel() {
  const { t } = useTranslation()
  const STRATEGIES = STRATEGY_VALUES.map((value) => ({ value, label: t(`loans.priority.strategy.${value}`) }))
  const [strategy, setStrategy] = useState('AVALANCHE')
  const [results, setResults] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchPriority = async (nextStrategy = strategy) => {
    setIsLoading(true)
    setError('')
    try {
      const data = await loanApi.getLoanPriority(nextStrategy)
      setResults(data.results)
    } catch (err) {
      setError(getErrorMessage(err, t('loans.errors.loadPriority')))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchPriority()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [strategy])

  const move = async (index, direction) => {
    const targetIndex = index + direction
    if (targetIndex < 0 || targetIndex >= results.length) return

    const reordered = [...results]
    ;[reordered[index], reordered[targetIndex]] = [reordered[targetIndex], reordered[index]]
    setResults(reordered)

    try {
      await loanApi.reorderLoans(reordered.map((r) => r.loan_id))
      await fetchPriority('CUSTOM')
    } catch (err) {
      setError(getErrorMessage(err, t('loans.errors.saveOrder')))
      await fetchPriority()
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{t('loans.priority.title')}</h3>
        <Select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
          {STRATEGIES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </Select>
      </div>

      {error && <p className="mb-2 text-sm text-red-600">{error}</p>}

      {isLoading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : results.length === 0 ? (
        <EmptyState title={t('loans.priority.emptyTitle')} description={t('loans.priority.emptyDescription')} />
      ) : (
        <ul className="divide-y divide-slate-100">
          {results.map((r, index) => (
            <li key={r.loan_id} className="flex items-center gap-3 py-3">
              <span className="w-6 text-center text-sm font-semibold text-slate-400 dark:text-slate-500">{r.rank}</span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Link to={`/loans/${r.loan_id}`} className="font-medium text-slate-900 dark:text-slate-100 hover:text-brand-600">
                    {r.loan_name}
                  </Link>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${PRIORITY_STYLES[r.priority_level]}`}>
                    {r.priority_level}
                  </span>
                </div>
                <p className="whitespace-pre-line text-xs text-slate-500 dark:text-slate-400">{r.reason}</p>
              </div>
              <div className="text-right text-sm">
                <p className="font-medium text-slate-900 dark:text-slate-100">{formatCurrency(r.outstanding_principal)}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">{t('loans.priority.apr', { rate: r.annual_interest_rate })}</p>
              </div>
              {strategy === 'CUSTOM' && (
                <div className="flex flex-col">
                  <button
                    type="button"
                    onClick={() => move(index, -1)}
                    disabled={index === 0}
                    aria-label={t('loans.priority.moveUp')}
                    className="text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:text-slate-300 disabled:opacity-30"
                  >
                    <ArrowUp className="size-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => move(index, 1)}
                    disabled={index === results.length - 1}
                    aria-label={t('loans.priority.moveDown')}
                    className="text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:text-slate-300 disabled:opacity-30"
                  >
                    <ArrowDown className="size-4" />
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
