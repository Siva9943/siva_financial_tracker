import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'
import Input from '../../components/Input.jsx'
import Modal from '../../components/Modal.jsx'
import Select from '../../components/Select.jsx'
import { EXPENSE_CATEGORIES } from '../../utils/categories.js'
import { getErrorMessage } from '../../utils/apiError.js'
import { DEFAULT_ALERT_THRESHOLDS, MONTH_NAMES } from '../../utils/budgetOptions.js'

function makeDefaults(month, year) {
  return {
    category: '',
    amount: '',
    month,
    year,
    alert_thresholds: DEFAULT_ALERT_THRESHOLDS.join(', '),
  }
}

export default function BudgetFormModal({ isOpen, onClose, onSubmit, editingBudget, month, year }) {
  const { t } = useTranslation()
  const [formError, setFormError] = useState('')
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: makeDefaults(month, year) })

  useEffect(() => {
    if (isOpen) {
      reset(
        editingBudget
          ? { ...editingBudget, alert_thresholds: editingBudget.alert_thresholds.join(', ') }
          : makeDefaults(month, year),
      )
      setFormError('')
    }
  }, [isOpen, editingBudget, month, year, reset])

  const submit = async (values) => {
    setFormError('')
    try {
      const alert_thresholds = values.alert_thresholds
        .split(',')
        .map((v) => v.trim())
        .filter(Boolean)
        .map(Number)

      await onSubmit({ ...values, alert_thresholds })
      onClose()
    } catch (error) {
      setFormError(getErrorMessage(error, t('budgets.saveError')))
    }
  }

  return (
    <Modal title={editingBudget ? t('budgets.editBudget') : t('budgets.addBudget')} isOpen={isOpen} onClose={onClose}>
      <form className="space-y-4" onSubmit={handleSubmit(submit)} noValidate>
        <div>
          <Input
            label={t('budgets.categoryLabel')}
            list="budget-category-suggestions"
            error={errors.category?.message}
            disabled={!!editingBudget}
            {...register('category', { required: t('budgets.categoryRequired') })}
          />
          <datalist id="budget-category-suggestions">
            {EXPENSE_CATEGORIES.map((category) => (
              <option key={category} value={category} />
            ))}
          </datalist>
        </div>

        <Input
          label={t('budgets.monthlyAmountLabel')}
          type="number"
          step="0.01"
          min="0.01"
          error={errors.amount?.message}
          {...register('amount', { required: t('budgets.amountRequired'), min: { value: 0.01, message: t('budgets.amountPositive') } })}
        />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select label={t('budgets.month')} disabled={!!editingBudget} {...register('month', { required: true, valueAsNumber: true })}>
            {MONTH_NAMES.map((name, index) => (
              <option key={name} value={index + 1}>
                {name}
              </option>
            ))}
          </Select>
          <Input
            label={t('budgets.year')}
            type="number"
            disabled={!!editingBudget}
            {...register('year', { required: true, valueAsNumber: true })}
          />
        </div>

        <Input
          label={t('budgets.alertThresholdsLabel')}
          error={errors.alert_thresholds?.message}
          {...register('alert_thresholds', { required: t('budgets.alertThresholdsRequired') })}
        />

        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t('budgets.saving') : t('common.save')}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
