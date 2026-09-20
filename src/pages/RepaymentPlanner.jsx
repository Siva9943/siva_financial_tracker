import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as planningApi from '../api/planningApi'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import PreviousPlansList from '../features/planning/PreviousPlansList.jsx'
import RepaymentPlanChart from '../features/planning/RepaymentPlanChart.jsx'
import RepaymentPlanForm from '../features/planning/RepaymentPlanForm.jsx'
import RepaymentPlanSummary from '../features/planning/RepaymentPlanSummary.jsx'
import RepaymentPlanTable from '../features/planning/RepaymentPlanTable.jsx'
import { getErrorMessage } from '../utils/apiError.js'

export default function RepaymentPlanner() {
  const { t } = useTranslation()
  const [plans, setPlans] = useState([])
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [excludedLoans, setExcludedLoans] = useState([])
  const [isLoadingPlan, setIsLoadingPlan] = useState(false)
  const [error, setError] = useState('')

  const fetchPlans = async () => {
    try {
      const data = await planningApi.listRepaymentPlans()
      setPlans(data.results)
    } catch {
      // history list is supplementary
    }
  }

  useEffect(() => {
    fetchPlans()
  }, [])

  const selectPlan = async (id) => {
    setIsLoadingPlan(true)
    setError('')
    setExcludedLoans([])
    try {
      const plan = await planningApi.getRepaymentPlan(id)
      setSelectedPlan(plan)
    } catch (err) {
      setError(getErrorMessage(err, t('planning.couldNotLoadPlan')))
    } finally {
      setIsLoadingPlan(false)
    }
  }

  const handleGenerate = async (values) => {
    setError('')
    const response = await planningApi.generateRepaymentPlan(values)
    setSelectedPlan(response.plan)
    setExcludedLoans(response.excluded_loans)
    await fetchPlans()
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.repaymentPlanner')}</h1>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-1">
          <RepaymentPlanForm onSubmit={handleGenerate} />
          <div>
            <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('planning.previousPlans')}</h3>
            <PreviousPlansList plans={plans} onSelect={selectPlan} selectedId={selectedPlan?.id} />
          </div>
        </div>

        <div className="space-y-6 lg:col-span-2">
          {error && <p className="text-sm text-red-600">{error}</p>}

          {isLoadingPlan ? (
            <div className="flex justify-center py-16">
              <LoadingSpinner />
            </div>
          ) : selectedPlan ? (
            <>
              <RepaymentPlanSummary plan={selectedPlan} excludedLoans={excludedLoans} />
              <RepaymentPlanChart items={selectedPlan.items} />
              <RepaymentPlanTable items={selectedPlan.items} />
            </>
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {t('planning.emptyStateHint')}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
