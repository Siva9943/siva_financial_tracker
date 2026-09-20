import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'
import Input from '../../components/Input.jsx'
import Modal from '../../components/Modal.jsx'
import Select from '../../components/Select.jsx'
import { getErrorMessage } from '../../utils/apiError.js'
import { labelize } from '../../utils/categories.js'
import { GOAL_PRIORITIES, GOAL_TYPES } from '../../utils/goalOptions.js'

const emptyValues = {
  name: '',
  goal_type: 'EMERGENCY_FUND',
  target_amount: '',
  target_date: '',
  monthly_contribution: '0',
  priority: 'MEDIUM',
}

export default function GoalFormModal({ isOpen, onClose, onSubmit, editingGoal }) {
  const { t } = useTranslation()
  const [formError, setFormError] = useState('')
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: emptyValues })

  useEffect(() => {
    if (isOpen) {
      reset(editingGoal ? { ...emptyValues, ...editingGoal } : emptyValues)
      setFormError('')
    }
  }, [isOpen, editingGoal, reset])

  const submit = async (values) => {
    setFormError('')
    try {
      await onSubmit(values)
      onClose()
    } catch (error) {
      setFormError(getErrorMessage(error, t('goals.saveError')))
    }
  }

  return (
    <Modal title={editingGoal ? t('goals.editGoal') : t('goals.addGoal')} isOpen={isOpen} onClose={onClose}>
      <form className="space-y-4" onSubmit={handleSubmit(submit)} noValidate>
        <Input label={t('goals.nameLabel')} error={errors.name?.message} {...register('name', { required: t('goals.nameRequired') })} />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select label={t('goals.typeLabel')} {...register('goal_type', { required: true })}>
            {GOAL_TYPES.map((type) => (
              <option key={type} value={type}>
                {t(`goals.type.${type}`, labelize(type))}
              </option>
            ))}
          </Select>
          <Select label={t('goals.priorityLabel')} {...register('priority', { required: true })}>
            {GOAL_PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {t(`goals.priority.${p}`, labelize(p))}
              </option>
            ))}
          </Select>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label={t('goals.targetAmountLabel')}
            type="number"
            step="0.01"
            min="0.01"
            error={errors.target_amount?.message}
            {...register('target_amount', { required: t('goals.targetAmountRequired'), min: { value: 0.01, message: t('goals.amountPositive') } })}
          />
          <Input
            label={t('goals.targetDateLabel')}
            type="date"
            error={errors.target_date?.message}
            {...register('target_date', { required: t('goals.targetDateRequired') })}
          />
        </div>

        <Input label={t('goals.monthlyContributionLabel')} type="number" step="0.01" min="0" {...register('monthly_contribution')} />

        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t('goals.saving') : t('common.save')}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
