import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as investmentApi from '../../api/investmentApi'
import EmptyState from '../../components/EmptyState.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import { formatCurrency, formatDate } from '../../utils/format.js'

export default function DividendHistoryList({ investmentId }) {
  const { t } = useTranslation()
  const [rows, setRows] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError('')
    investmentApi
      .listDividends()
      .then((data) => {
        if (cancelled) return
        const results = data?.results ?? []
        setRows(investmentId ? results.filter((row) => row.investment_id === investmentId) : results)
      })
      .catch(() => {
        if (!cancelled) setError(t('investments.dividendLoadError'))
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [investmentId, t])

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('investments.dividendHistoryTitle')}</h3>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      ) : rows.length === 0 ? (
        <EmptyState title={t('investments.noDividendsTitle')} description={t('investments.noDividendsDescription')} />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700 text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                <th className="py-2 pr-4 font-medium">{t('investments.date')}</th>
                {!investmentId && <th className="py-2 pr-4 font-medium">{t('investments.investmentName')}</th>}
                <th className="py-2 pr-4 font-medium">{t('investments.amount')}</th>
                <th className="py-2 pr-4 font-medium">{t('investments.reference')}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b border-slate-100 last:border-0 dark:border-slate-700/60">
                  <td className="py-2 pr-4 text-slate-700 dark:text-slate-300">{formatDate(row.transaction_date)}</td>
                  {!investmentId && (
                    <td className="py-2 pr-4 text-slate-700 dark:text-slate-300">{row.investment_name}</td>
                  )}
                  <td className="py-2 pr-4 font-medium text-slate-900 dark:text-slate-100">{formatCurrency(row.amount)}</td>
                  <td className="py-2 pr-4 text-slate-500 dark:text-slate-400">{row.reference || row.notes || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
