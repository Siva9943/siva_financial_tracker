import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'
import Input from '../../components/Input.jsx'
import Modal from '../../components/Modal.jsx'
import Select from '../../components/Select.jsx'
import { getErrorMessage } from '../../utils/apiError.js'
import { PAYMENT_METHODS, labelize } from '../../utils/categories.js'

const emptyValues = {
  payment_date: new Date().toISOString().slice(0, 10),
  amount: '',
  late_fee: '',
  payment_method: 'BANK_TRANSFER',
  transaction_reference: '',
  notes: '',
}

export default function LoanPaymentFormModal({ isOpen, onClose, onSubmit }) {
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
      await onSubmit({ ...values, late_fee: values.late_fee === '' ? null : values.late_fee })
      onClose()
    } catch (error) {
      setFormError(getErrorMessage(error, t('loans.errors.recordPayment')))
    }
  }

  return (
    <Modal title={t('loans.recordPayment')} isOpen={isOpen} onClose={onClose}>
      <form className="space-y-4" onSubmit={handleSubmit(submit)} noValidate>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label={t('loans.fields.paymentDate')}
            type="date"
            error={errors.payment_date?.message}
            {...register('payment_date', { required: t('loans.validation.paymentDateRequired') })}
          />
          <Input
            label={t('loans.fields.amount')}
            type="number"
            step="0.01"
            min="0.01"
            error={errors.amount?.message}
            {...register('amount', {
              required: t('loans.validation.amountRequired'),
              min: { value: 0.01, message: t('loans.validation.mustBeGreaterThanZero') },
            })}
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label={t('loans.fields.lateFeeOptional')}
            type="number"
            step="0.01"
            min="0"
            {...register('late_fee')}
          />
          <Select label={t('loans.fields.paymentMethod')} {...register('payment_method', { required: true })}>
            {PAYMENT_METHODS.map((method) => (
              <option key={method} value={method}>
                {labelize(method)}
              </option>
            ))}
          </Select>
        </div>

        <Input label={t('loans.fields.referenceOptional')} {...register('transaction_reference')} />
        <Input label={t('loans.fields.notesOptional')} {...register('notes')} />

        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t('loans.recording') : t('loans.recordPayment')}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
