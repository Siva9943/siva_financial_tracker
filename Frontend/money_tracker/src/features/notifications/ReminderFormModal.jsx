import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'
import Input from '../../components/Input.jsx'
import Modal from '../../components/Modal.jsx'
import Select from '../../components/Select.jsx'
import { labelize } from '../../utils/categories.js'
import { getErrorMessage } from '../../utils/apiError.js'
import { RECURRENCES, REMINDER_TYPES } from '../../utils/reminderOptions.js'

const emptyValues = {
  reminder_type: 'CUSTOM',
  description: '',
  amount: '',
  reminder_date: new Date().toISOString().slice(0, 10),
  recurrence: 'NONE',
}

export default function ReminderFormModal({ isOpen, onClose, onSubmit }) {
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
      reset(emptyValues)
      setFormError('')
    }
  }, [isOpen, reset])

  const submit = async (values) => {
    setFormError('')
    try {
      await onSubmit({ ...values, amount: values.amount || null })
      onClose()
    } catch (error) {
      setFormError(getErrorMessage(error, t('notifications.couldNotSaveReminder')))
    }
  }

  return (
    <Modal title={t('notifications.addReminder')} isOpen={isOpen} onClose={onClose}>
      <form className="space-y-4" onSubmit={handleSubmit(submit)} noValidate>
        <Select label={t('notifications.type')} {...register('reminder_type', { required: true })}>
          {REMINDER_TYPES.map((type) => (
            <option key={type} value={type}>
              {labelize(type)}
            </option>
          ))}
        </Select>

        <Input
          label={t('notifications.description')}
          error={errors.description?.message}
          {...register('description', { required: t('notifications.descriptionRequired') })}
        />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input label={t('notifications.amountOptional')} type="number" step="0.01" min="0.01" {...register('amount')} />
          <Input
            label={t('notifications.reminderDate')}
            type="date"
            error={errors.reminder_date?.message}
            {...register('reminder_date', { required: t('notifications.reminderDateRequired') })}
          />
        </div>

        <Select label={t('notifications.recurrence')} {...register('recurrence', { required: true })}>
          {RECURRENCES.map((r) => (
            <option key={r} value={r}>
              {labelize(r)}
            </option>
          ))}
        </Select>

        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t('notifications.saving') : t('common.save')}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
