import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'
import Input from '../../components/Input.jsx'
import Modal from '../../components/Modal.jsx'
import { getErrorMessage } from '../../utils/apiError.js'

const emptyValues = { amount: '', contribution_date: new Date().toISOString().slice(0, 10), notes: '' }

export default function ContributionFormModal({ isOpen, onClose, onSubmit }) {
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
      await onSubmit(values)
      onClose()
    } catch (error) {
      setFormError(getErrorMessage(error, t('goals.contributionSaveError')))
    }
  }

  return (
    <Modal title={t('goals.recordContributionTitle')} isOpen={isOpen} onClose={onClose}>
      <form className="space-y-4" onSubmit={handleSubmit(submit)} noValidate>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label={t('goals.amountLabel')}
            type="number"
            step="0.01"
            min="0.01"
            error={errors.amount?.message}
            {...register('amount', { required: t('goals.amountRequired'), min: { value: 0.01, message: t('goals.amountPositive') } })}
          />
          <Input
            label={t('goals.dateLabel')}
            type="date"
            error={errors.contribution_date?.message}
            {...register('contribution_date', { required: t('goals.dateRequired') })}
          />
        </div>
        <Input label={t('goals.notesLabel')} {...register('notes')} />

        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t('goals.saving') : t('goals.record')}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
