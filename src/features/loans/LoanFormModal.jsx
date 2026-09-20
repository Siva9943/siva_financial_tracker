import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'
import Input from '../../components/Input.jsx'
import Modal from '../../components/Modal.jsx'
import Select from '../../components/Select.jsx'
import { labelize } from '../../utils/categories.js'
import { getErrorMessage } from '../../utils/apiError.js'
import { INTEREST_METHODS, LOAN_STATUSES, LOAN_TYPES, PAYMENT_FREQUENCIES } from '../../utils/loanOptions.js'

const emptyValues = {
  loan_name: '',
  loan_type: 'PERSONAL',
  lender: '',
  original_principal: '',
  annual_interest_rate: '',
  interest_calculation_method: 'EMI_AMORTIZATION',
  emi_amount: '',
  payment_frequency: 'MONTHLY',
  start_date: new Date().toISOString().slice(0, 10),
  maturity_date: '',
  processing_fee: '0',
  late_fee: '0',
  prepayment_penalty: '0',
  status: 'ACTIVE',
  notes: '',
}

export default function LoanFormModal({ isOpen, onClose, onSubmit, editingLoan }) {
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
      reset(editingLoan ? { ...emptyValues, ...editingLoan } : emptyValues)
      setFormError('')
    }
  }, [isOpen, editingLoan, reset])

  const submit = async (values) => {
    setFormError('')
    try {
      await onSubmit(values)
      onClose()
    } catch (error) {
      setFormError(getErrorMessage(error, t('loans.errors.saveLoan')))
    }
  }

  return (
    <Modal title={editingLoan ? t('loans.editLoan') : t('loans.addLoan')} isOpen={isOpen} onClose={onClose}>
      <form className="max-h-[70vh] space-y-4 overflow-y-auto pr-1" onSubmit={handleSubmit(submit)} noValidate>
        <Input
          label={t('loans.fields.loanName')}
          error={errors.loan_name?.message}
          {...register('loan_name', { required: t('loans.validation.loanNameRequired') })}
        />

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select label={t('loans.fields.type')} {...register('loan_type', { required: true })}>
            {LOAN_TYPES.map((type) => (
              <option key={type} value={type}>
                {labelize(type)}
              </option>
            ))}
          </Select>
          <Input label={t('loans.fields.lender')} {...register('lender')} />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label={t('loans.fields.originalPrincipal')}
            type="number"
            step="0.01"
            min="0.01"
            error={errors.original_principal?.message}
            {...register('original_principal', {
              required: t('loans.validation.principalRequired'),
              min: { value: 0.01, message: t('loans.validation.mustBeGreaterThanZero') },
            })}
          />
          <Input
            label={t('loans.fields.annualInterestRate')}
            type="number"
            step="0.001"
            min="0"
            error={errors.annual_interest_rate?.message}
            {...register('annual_interest_rate', {
              required: t('loans.validation.interestRateRequired'),
              min: { value: 0, message: t('loans.validation.cannotBeNegative') },
            })}
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select label={t('loans.fields.interestMethod')} {...register('interest_calculation_method', { required: true })}>
            {INTEREST_METHODS.map((method) => (
              <option key={method} value={method}>
                {labelize(method)}
              </option>
            ))}
          </Select>
          <Select label={t('loans.fields.paymentFrequency')} {...register('payment_frequency', { required: true })}>
            {PAYMENT_FREQUENCIES.map((freq) => (
              <option key={freq} value={freq}>
                {labelize(freq)}
              </option>
            ))}
          </Select>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label={t('loans.fields.emiAmountOptional')}
            type="number"
            step="0.01"
            min="0.01"
            error={errors.emi_amount?.message}
            {...register('emi_amount', { min: { value: 0.01, message: t('loans.validation.mustBeGreaterThanZero') } })}
          />
          <Select label={t('loans.fields.status')} {...register('status', { required: true })}>
            {LOAN_STATUSES.map((s) => (
              <option key={s} value={s}>
                {labelize(s)}
              </option>
            ))}
          </Select>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label={t('loans.fields.startDate')}
            type="date"
            error={errors.start_date?.message}
            {...register('start_date', { required: t('loans.validation.startDateRequired') })}
          />
          <Input
            label={t('loans.fields.maturityDate')}
            type="date"
            error={errors.maturity_date?.message}
            {...register('maturity_date', { required: t('loans.validation.maturityDateRequired') })}
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Input label={t('loans.fields.processingFee')} type="number" step="0.01" min="0" {...register('processing_fee')} />
          <Input label={t('loans.fields.lateFee')} type="number" step="0.01" min="0" {...register('late_fee')} />
          <Input
            label={t('loans.fields.prepaymentPenalty')}
            type="number"
            step="0.01"
            min="0"
            {...register('prepayment_penalty')}
          />
        </div>

        <Input label={t('loans.fields.notesOptional')} {...register('notes')} />

        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t('loans.saving') : t('common.save')}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
