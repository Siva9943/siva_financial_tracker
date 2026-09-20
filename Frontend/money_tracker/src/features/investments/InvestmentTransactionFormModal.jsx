import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'
import Input from '../../components/Input.jsx'
import Modal from '../../components/Modal.jsx'
import Select from '../../components/Select.jsx'
import { getErrorMessage } from '../../utils/apiError.js'
import { labelize } from '../../utils/categories.js'
import {
  AMOUNT_ONLY_TRANSACTION_TYPES,
  INVESTMENT_TRANSACTION_TYPES,
  QUANTITY_ONLY_TRANSACTION_TYPES,
  QUANTITY_PRICE_TRANSACTION_TYPES,
} from '../../utils/investmentOptions.js'

const today = () => new Date().toISOString().slice(0, 10)

const emptyValues = {
  transaction_type: 'BUY',
  transaction_date: today(),
  quantity: '',
  price: '',
  amount: '',
  fees: '',
  tax: '',
  reference: '',
  notes: '',
}

function buildPayload(values) {
  const type = values.transaction_type
  const payload = {
    transaction_type: type,
    transaction_date: values.transaction_date,
  }

  if (QUANTITY_PRICE_TRANSACTION_TYPES.includes(type)) {
    payload.quantity = values.quantity
    payload.price = values.price
  } else if (QUANTITY_ONLY_TRANSACTION_TYPES.includes(type)) {
    payload.quantity = values.quantity
  } else if (AMOUNT_ONLY_TRANSACTION_TYPES.includes(type)) {
    payload.amount = values.amount
  }

  if (QUANTITY_PRICE_TRANSACTION_TYPES.includes(type) || type === 'FEE') {
    if (values.fees !== '') payload.fees = values.fees
    if (values.tax !== '') payload.tax = values.tax
  }

  if (values.reference) payload.reference = values.reference
  if (values.notes) payload.notes = values.notes

  return payload
}

export default function InvestmentTransactionFormModal({ isOpen, onClose, onSubmit }) {
  const { t } = useTranslation()
  const [formError, setFormError] = useState('')
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: emptyValues })

  const transactionType = watch('transaction_type')
  const showQuantityAndPrice = QUANTITY_PRICE_TRANSACTION_TYPES.includes(transactionType)
  const showQuantityOnly = QUANTITY_ONLY_TRANSACTION_TYPES.includes(transactionType)
  const showAmountOnly = AMOUNT_ONLY_TRANSACTION_TYPES.includes(transactionType)
  const showFeesAndTax = showQuantityAndPrice || transactionType === 'FEE'

  useEffect(() => {
    if (isOpen) {
      reset(emptyValues)
      setFormError('')
    }
  }, [isOpen, reset])

  const submit = async (values) => {
    setFormError('')
    try {
      await onSubmit(buildPayload(values))
      onClose()
    } catch (error) {
      setFormError(getErrorMessage(error, t('investments.errors.recordTransaction')))
    }
  }

  return (
    <Modal title={t('investments.addTransaction')} isOpen={isOpen} onClose={onClose}>
      <form className="max-h-[70vh] space-y-4 overflow-y-auto pr-1" onSubmit={handleSubmit(submit)} noValidate>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select label={t('investments.fields.transactionType')} {...register('transaction_type', { required: true })}>
            {INVESTMENT_TRANSACTION_TYPES.map((type) => (
              <option key={type} value={type}>
                {labelize(type)}
              </option>
            ))}
          </Select>
          <Input
            label={t('investments.fields.transactionDate')}
            type="date"
            max={today()}
            error={errors.transaction_date?.message}
            {...register('transaction_date', { required: t('investments.validation.transactionDateRequired') })}
          />
        </div>

        {showQuantityAndPrice && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input
              label={t('investments.fields.quantity')}
              type="number"
              step="0.0001"
              min="0.0001"
              error={errors.quantity?.message}
              {...register('quantity', {
                required: t('investments.validation.quantityRequired'),
                min: { value: 0.0001, message: t('investments.validation.mustBeGreaterThanZero') },
              })}
            />
            <Input
              label={t('investments.fields.price')}
              type="number"
              step="0.01"
              min="0.01"
              error={errors.price?.message}
              {...register('price', {
                required: t('investments.validation.priceRequired'),
                min: { value: 0.01, message: t('investments.validation.mustBeGreaterThanZero') },
              })}
            />
          </div>
        )}

        {showQuantityOnly && (
          <Input
            label={t('investments.fields.quantity')}
            type="number"
            step="0.0001"
            min="0.0001"
            error={errors.quantity?.message}
            {...register('quantity', {
              required: t('investments.validation.quantityRequired'),
              min: { value: 0.0001, message: t('investments.validation.mustBeGreaterThanZero') },
            })}
          />
        )}

        {showAmountOnly && (
          <Input
            label={t('investments.fields.amount')}
            type="number"
            step="0.01"
            min="0.01"
            error={errors.amount?.message}
            {...register('amount', {
              required: t('investments.validation.amountRequired'),
              min: { value: 0.01, message: t('investments.validation.mustBeGreaterThanZero') },
            })}
          />
        )}

        {showFeesAndTax && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input label={t('investments.fields.feesOptional')} type="number" step="0.01" min="0" {...register('fees')} />
            <Input label={t('investments.fields.taxOptional')} type="number" step="0.01" min="0" {...register('tax')} />
          </div>
        )}

        <Input label={t('investments.fields.referenceOptional')} {...register('reference')} />
        <Input label={t('investments.fields.notesOptional')} {...register('notes')} />

        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t('investments.recording') : t('investments.addTransaction')}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
