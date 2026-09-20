import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'
import Input from '../../components/Input.jsx'
import Select from '../../components/Select.jsx'
import { getErrorMessage } from '../../utils/apiError.js'

const STRATEGIES = [
  { value: 'AVALANCHE', labelKey: 'planning.strategyAvalanche' },
  { value: 'SNOWBALL', labelKey: 'planning.strategySnowball' },
  { value: 'CUSTOM', labelKey: 'planning.strategyCustom' },
]

const defaultValues = {
  strategy: 'AVALANCHE',
  monthly_income: '',
  essential_expenses: '',
  emergency_savings_allocation: '0',
  extra_payment: '0',
}

export default function RepaymentPlanForm({ onSubmit }) {
  const { t } = useTranslation()
  const [formError, setFormError] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues })

  const submit = async (values) => {
    setFormError('')
    try {
      await onSubmit(values)
    } catch (error) {
      setFormError(getErrorMessage(error, t('planning.couldNotGeneratePlan')))
    }
  }

  return (
    <form className="space-y-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4" onSubmit={handleSubmit(submit)} noValidate>
      <Select label={t('planning.strategy')} {...register('strategy', { required: true })}>
        {STRATEGIES.map((s) => (
          <option key={s.value} value={s.value}>
            {t(s.labelKey)}
          </option>
        ))}
      </Select>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label={t('planning.monthlyIncome')}
          type="number"
          step="0.01"
          min="0.01"
          error={errors.monthly_income?.message}
          {...register('monthly_income', { required: t('planning.monthlyIncomeRequired') })}
        />
        <Input
          label={t('planning.essentialExpenses')}
          type="number"
          step="0.01"
          min="0"
          error={errors.essential_expenses?.message}
          {...register('essential_expenses', { required: t('planning.essentialExpensesRequired') })}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label={t('planning.emergencySavingsAllocation')}
          type="number"
          step="0.01"
          min="0"
          {...register('emergency_savings_allocation')}
        />
        <Input
          label={t('planning.extraPaymentAvailable')}
          type="number"
          step="0.01"
          min="0"
          {...register('extra_payment')}
        />
      </div>

      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <Button type="submit" disabled={isSubmitting} className="w-full">
        {isSubmitting ? t('planning.generating') : t('planning.generatePlan')}
      </Button>
    </form>
  )
}
