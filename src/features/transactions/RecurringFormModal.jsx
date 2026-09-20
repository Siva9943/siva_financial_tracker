import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'
import Input from '../../components/Input.jsx'
import Modal from '../../components/Modal.jsx'
import Select from '../../components/Select.jsx'
import { getErrorMessage } from '../../utils/apiError.js'

const FREQUENCIES = ['DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY']

const emptyValues = {
  amount: '',
  category: '',
  description: '',
  frequency: 'MONTHLY',
  start_date: new Date().toISOString().slice(0, 10),
  end_date: '',
}

const FREQUENCY_LABEL_KEYS = {
  DAILY: 'transactions.frequencyDaily',
  WEEKLY: 'transactions.frequencyWeekly',
  MONTHLY: 'transactions.frequencyMonthly',
  YEARLY: 'transactions.frequencyYearly',
}

export default function RecurringFormModal({ isOpen, onClose, onSubmit, editingRule, categories }) {
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
      reset(editingRule ? { ...emptyValues, ...editingRule, end_date: editingRule.end_date ?? '' } : emptyValues)
      setFormError('')
    }
  }, [isOpen, editingRule, reset])

  const submit = async (values) => {
    setFormError('')
    try {
      await onSubmit({ ...values, end_date: values.end_date || null })
      onClose()
    } catch (error) {
      setFormError(getErrorMessage(error, t('transactions.saveRecurringError')))
    }
  }

  return (
    <Modal
      title={editingRule ? t('transactions.editRecurringRule') : t('transactions.addRecurringRule')}
      isOpen={isOpen}
      onClose={onClose}
    >
      <form className="space-y-4" onSubmit={handleSubmit(submit)} noValidate>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label={t('transactions.amount')}
            type="number"
            step="0.01"
            min="0.01"
            error={errors.amount?.message}
            {...register('amount', {
              required: t('transactions.amountRequired'),
              min: { value: 0.01, message: t('transactions.mustBeGreaterThanZero') },
            })}
          />
          <div>
            <Input
              label={t('transactions.category')}
              list="recurring-category-suggestions"
              error={errors.category?.message}
              {...register('category', { required: t('transactions.categoryRequired') })}
            />
            <datalist id="recurring-category-suggestions">
              {categories.map((category) => (
                <option key={category} value={category} />
              ))}
            </datalist>
          </div>
        </div>

        <Input label={t('transactions.description')} {...register('description')} />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select label={t('transactions.frequency')} {...register('frequency', { required: true })}>
            {FREQUENCIES.map((freq) => (
              <option key={freq} value={freq}>
                {t(FREQUENCY_LABEL_KEYS[freq])}
              </option>
            ))}
          </Select>
          <Input
            label={t('transactions.startDate')}
            type="date"
            error={errors.start_date?.message}
            {...register('start_date', { required: t('transactions.startDateRequired') })}
          />
        </div>

        <Input label={t('transactions.endDateOptional')} type="date" {...register('end_date')} />

        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t('transactions.saving') : t('common.save')}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
