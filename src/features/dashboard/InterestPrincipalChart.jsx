import { useTranslation } from 'react-i18next'
import EmptyState from '../../components/EmptyState.jsx'
import { CATEGORICAL_PALETTE } from '../../utils/chartPalette.js'
import { formatCurrency } from '../../utils/format.js'

export default function InterestPrincipalChart({ data }) {
  const { t } = useTranslation()
  const interest = Number(data?.interest ?? 0)
  const principal = Number(data?.principal ?? 0)
  const total = interest + principal

  if (total === 0) {
    return <EmptyState title={t('dashboard.noLoanPaymentsTitle')} description={t('dashboard.noLoanPaymentsDescription')} />
  }

  const interestPct = (interest / total) * 100

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('dashboard.interestVsPrincipal')}</h3>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
        <div style={{ width: `${interestPct}%`, backgroundColor: CATEGORICAL_PALETTE[7] }} />
        <div style={{ width: `${100 - interestPct}%`, backgroundColor: CATEGORICAL_PALETTE[0] }} />
      </div>
      <div className="mt-3 flex justify-between text-sm">
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full" style={{ backgroundColor: CATEGORICAL_PALETTE[7] }} />
          {t('dashboard.interestColon', { amount: formatCurrency(interest) })}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full" style={{ backgroundColor: CATEGORICAL_PALETTE[0] }} />
          {t('dashboard.principalColon', { amount: formatCurrency(principal) })}
        </span>
      </div>
    </div>
  )
}
