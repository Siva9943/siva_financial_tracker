import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'
import Input from '../../components/Input.jsx'
import Modal from '../../components/Modal.jsx'
import Select from '../../components/Select.jsx'
import { getErrorMessage } from '../../utils/apiError.js'
import { labelize } from '../../utils/categories.js'
import { INVESTMENT_STATUSES, INVESTMENT_TYPES } from '../../utils/investmentOptions.js'

const emptyValues = {
  name: '',
  symbol: '',
  investment_type: 'STOCK',
  platform: '',
  current_price: '0',
  status: 'ACTIVE',
  notes: '',
  deposit_amount: '',
  withdrawal_amount: '',
  transaction_date: new Date().toISOString().slice(0, 10),
}

export default function InvestmentFormModal({ isOpen, onClose, onSubmit, editingInvestment }) {
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
      reset(editingInvestment ? { ...emptyValues, ...editingInvestment } : emptyValues)
      setFormError('')
    }
  }, [isOpen, editingInvestment, reset])

  const submit = async (values) => {
    setFormError('')
    try {
      await onSubmit(values)
      onClose()
    } catch (error) {
      setFormError(getErrorMessage(error, t('investments.errors.saveInvestment')))
    }
  }

  return (
    <Modal title={editingInvestment ? t('investments.editInvestment') : t('investments.addInvestment')} isOpen={isOpen} onClose={onClose}>
      <form className="max-h-[70vh] space-y-4 overflow-y-auto pr-1" onSubmit={handleSubmit(submit)} noValidate>
        <Input
          label={t('investments.fields.name')}
          error={errors.name?.message}
          {...register('name', { required: t('investments.validation.nameRequired') })}
        />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input label={t('investments.fields.symbolOptional')} {...register('symbol')} />
          <Select label={t('investments.fields.type')} {...register('investment_type', { required: true })}>
            {INVESTMENT_TYPES.map((type) => (
              <option key={type} value={type}>
                {labelize(type)}
              </option>
            ))}
          </Select>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input label={t('investments.fields.platformOptional')} {...register('platform')} />
          <Input
            label={t('investments.fields.currentPrice')}
            type="number"
            step="0.01"
            min="0"
            error={errors.current_price?.message}
            {...register('current_price', { min: { value: 0, message: t('investments.validation.cannotBeNegative') } })}
          />
        </div>

        <Select label={t('investments.fields.status')} {...register('status', { required: true })}>
          {INVESTMENT_STATUSES.map((s) => (
            <option key={s} value={s}>
              {labelize(s)}
            </option>
          ))}
        </Select>

        <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-3">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            {t('investments.fields.adjustInvestedAmount')}
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Input
              label={t('investments.fields.depositAmountOptional')}
              type="number"
              step="0.01"
              min="0"
              error={errors.deposit_amount?.message}
              {...register('deposit_amount', { min: { value: 0, message: t('investments.validation.cannotBeNegative') } })}
            />
            <Input
              label={t('investments.fields.withdrawalAmountOptional')}
              type="number"
              step="0.01"
              min="0"
              error={errors.withdrawal_amount?.message}
              {...register('withdrawal_amount', { min: { value: 0, message: t('investments.validation.cannotBeNegative') } })}
            />
            <Input
              label={t('investments.fields.transactionDate')}
              type="date"
              error={errors.transaction_date?.message}
              {...register('transaction_date')}
            />
          </div>
          <p className="mt-2 text-xs text-slate-400 dark:text-slate-500">{t('investments.fields.adjustInvestedAmountHint')}</p>
        </div>

        <Input label={t('investments.fields.notesOptional')} {...register('notes')} />

        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t('investments.saving') : t('common.save')}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
