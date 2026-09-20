import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'
import Input from '../../components/Input.jsx'
import Modal from '../../components/Modal.jsx'
import Select from '../../components/Select.jsx'
import { categoriesForType, PAYMENT_METHODS, TRANSACTION_TYPES, labelize } from '../../utils/categories.js'
import { getErrorMessage } from '../../utils/apiError.js'

const today = () => new Date().toISOString().slice(0, 10)

const emptyValues = {
  transaction_type: 'EXPENSE',
  amount: '',
  category: '',
  description: '',
  transaction_date: today(),
  payment_method: 'CASH',
  reference: '',
}

export default function TransactionFormModal({ isOpen, onClose, onSubmit, editingTransaction, lockedType }) {
  const { t } = useTranslation()
  const [formError, setFormError] = useState('')
  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: { ...emptyValues, transaction_type: lockedType ?? emptyValues.transaction_type } })

  const transactionType = watch('transaction_type')

  useEffect(() => {
    if (isOpen) {
      const base = { ...emptyValues, transaction_type: lockedType ?? emptyValues.transaction_type }
      reset(editingTransaction ? { ...base, ...editingTransaction } : base)
      setFormError('')
    }
  }, [isOpen, editingTransaction, lockedType, reset])

  const submit = async (values) => {
    setFormError('')
    try {
      await onSubmit({ ...values, amount: String(values.amount) })
      onClose()
    } catch (error) {
      setFormError(getErrorMessage(error, t('transactions.saveError')))
    }
  }

  return (
    <Modal
      title={editingTransaction ? t('transactions.editTransaction') : t('transactions.addTransaction')}
      isOpen={isOpen}
      onClose={onClose}
    >
      <form className="space-y-4" onSubmit={handleSubmit(submit)} noValidate>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {lockedType ? (
            <input type="hidden" {...register('transaction_type')} />
          ) : (
            <Select label={t('transactions.type')} {...register('transaction_type', { required: true })}>
              {TRANSACTION_TYPES.map((type) => (
                <option key={type} value={type}>
                  {labelize(type)}
                </option>
              ))}
            </Select>
          )}
          <Input
            label={t('transactions.amount')}
            type="number"
            step="0.01"
            min="0.01"
            className={lockedType ? 'col-span-2' : ''}
            error={errors.amount?.message}
            {...register('amount', {
              required: t('transactions.amountRequired'),
              min: { value: 0.01, message: t('transactions.amountMin') },
            })}
          />
        </div>

        <div>
          <Input
            label={t('transactions.category')}
            list="category-suggestions"
            error={errors.category?.message}
            {...register('category', { required: t('transactions.categoryRequired') })}
          />
          <datalist id="category-suggestions">
            {categoriesForType(transactionType).map((category) => (
              <option key={category} value={category} />
            ))}
          </datalist>
        </div>

        <Input label={t('transactions.description')} {...register('description')} />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label={t('transactions.date')}
            type="date"
            error={errors.transaction_date?.message}
            {...register('transaction_date', { required: t('transactions.dateRequired') })}
          />
          <Select label={t('transactions.paymentMethod')} {...register('payment_method', { required: true })}>
            {PAYMENT_METHODS.map((method) => (
              <option key={method} value={method}>
                {labelize(method)}
              </option>
            ))}
          </Select>
        </div>

        <Input label={t('transactions.referenceOptional')} {...register('reference')} />

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
