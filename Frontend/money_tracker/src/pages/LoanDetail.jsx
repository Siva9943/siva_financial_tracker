import { ArrowLeft, CreditCard, Pencil } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate, useParams } from 'react-router-dom'
import * as loanApi from '../api/loanApi'
import Button from '../components/Button.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import StatCard from '../components/StatCard.jsx'
import AmortizationTable from '../features/loans/AmortizationTable.jsx'
import LoanFormModal from '../features/loans/LoanFormModal.jsx'
import LoanPaymentFormModal from '../features/loans/LoanPaymentFormModal.jsx'
import LoanPaymentHistory from '../features/loans/LoanPaymentHistory.jsx'
import { getErrorMessage } from '../utils/apiError.js'
import { labelize } from '../utils/categories.js'
import { formatCurrency, formatDate } from '../utils/format.js'
import { LOAN_STATUS_STYLES } from '../utils/loanOptions.js'

function DetailRow({ label, value }) {
  return (
    <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 py-2 text-sm last:border-0">
      <span className="text-slate-500 dark:text-slate-400">{label}</span>
      <span className="font-medium text-slate-900 dark:text-slate-100">{value}</span>
    </div>
  )
}

export default function LoanDetail() {
  const { t } = useTranslation()
  const { id } = useParams()
  const navigate = useNavigate()
  const [loan, setLoan] = useState(null)
  const [error, setError] = useState('')
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [amortization, setAmortization] = useState(null)
  const [amortizationError, setAmortizationError] = useState('')
  const [payments, setPayments] = useState([])
  const [isPaymentFormOpen, setIsPaymentFormOpen] = useState(false)

  const fetchLoan = async () => {
    setError('')
    try {
      setLoan(await loanApi.getLoan(id))
    } catch (err) {
      setError(getErrorMessage(err, t('loans.errors.loadLoan')))
    }
  }

  const fetchAmortization = async () => {
    setAmortizationError('')
    try {
      setAmortization(await loanApi.getLoanAmortization(id))
    } catch (err) {
      setAmortizationError(getErrorMessage(err, t('loans.errors.calculateAmortization')))
    }
  }

  const fetchPayments = async () => {
    try {
      const data = await loanApi.listLoanPayments(id)
      setPayments(data.results)
    } catch {
      // payment history is supplementary
    }
  }

  useEffect(() => {
    fetchLoan()
    fetchAmortization()
    fetchPayments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const refreshAfterPayment = async () => {
    await Promise.all([fetchLoan(), fetchAmortization(), fetchPayments()])
  }

  if (error) {
    return (
      <div>
        <p className="text-sm text-red-600">{error}</p>
        <Link to="/loans" className="mt-2 inline-block text-brand-600 hover:underline">
          {t('loans.backToLoans')}
        </Link>
      </div>
    )
  }

  if (!loan) {
    return (
      <div className="flex justify-center py-16">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <button
            type="button"
            onClick={() => navigate('/loans')}
            className="mb-2 flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:text-slate-100"
          >
            <ArrowLeft className="size-4" />
            {t('loans.backToLoans')}
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{loan.loan_name}</h1>
            <span className={`rounded-full px-2 py-1 text-xs font-medium ${LOAN_STATUS_STYLES[loan.status]}`}>
              {labelize(loan.status)}
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {labelize(loan.loan_type)} {loan.lender && `· ${loan.lender}`}
          </p>
        </div>
        <div className="flex gap-2">
          {loan.status !== 'COMPLETED' && (
            <Button onClick={() => setIsPaymentFormOpen(true)}>
              <CreditCard className="size-4" />
              {t('loans.recordPayment')}
            </Button>
          )}
          <Button variant="secondary" onClick={() => setIsFormOpen(true)}>
            <Pencil className="size-4" />
            {t('common.edit')}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label={t('loans.fields.originalPrincipal')} value={formatCurrency(loan.original_principal)} />
        <StatCard label={t('loans.fields.outstanding')} value={formatCurrency(loan.outstanding_principal)} accent="text-amber-700" />
        <StatCard label={t('loans.fields.interestRate')} value={`${loan.annual_interest_rate}%`} />
        <StatCard label={t('loans.fields.emi')} value={loan.emi_amount ? formatCurrency(loan.emi_amount) : '—'} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('loans.loanDetails')}</h3>
          <DetailRow label={t('loans.fields.interestMethod')} value={labelize(loan.interest_calculation_method)} />
          <DetailRow label={t('loans.fields.paymentFrequency')} value={labelize(loan.payment_frequency)} />
          <DetailRow label={t('loans.fields.startDate')} value={formatDate(loan.start_date)} />
          <DetailRow label={t('loans.fields.maturityDate')} value={formatDate(loan.maturity_date)} />
          <DetailRow label={t('loans.fields.nextDueDate')} value={loan.next_due_date ? formatDate(loan.next_due_date) : '—'} />
        </div>

        <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('loans.fees')}</h3>
          <DetailRow label={t('loans.fields.processingFee')} value={formatCurrency(loan.processing_fee)} />
          <DetailRow label={t('loans.fields.lateFee')} value={formatCurrency(loan.late_fee)} />
          <DetailRow label={t('loans.fields.prepaymentPenalty')} value={`${loan.prepayment_penalty}%`} />
        </div>
      </div>

      {loan.notes && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('loans.notes')}</h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">{loan.notes}</p>
        </div>
      )}

      <div>
        <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('loans.paymentHistory')}</h3>
        <LoanPaymentHistory payments={payments} />
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('loans.amortizationSchedule')}</h3>
        {amortizationError && <p className="text-sm text-red-600">{amortizationError}</p>}
        {amortization && (
          <>
            <div className="mb-3 grid grid-cols-2 gap-4 sm:grid-cols-3">
              <StatCard label={t('loans.fields.tenure')} value={t('loans.tenurePayments', { count: amortization.tenure_periods })} />
              <StatCard label={t('loans.fields.totalInterest')} value={formatCurrency(amortization.total_interest)} />
              <StatCard label={t('loans.fields.totalPayment')} value={formatCurrency(amortization.total_payment)} />
            </div>
            <AmortizationTable schedule={amortization.schedule} />
          </>
        )}
      </div>

      <LoanFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={async (values) => {
          await loanApi.updateLoan(loan.id, values)
          await Promise.all([fetchLoan(), fetchAmortization()])
        }}
        editingLoan={loan}
      />

      <LoanPaymentFormModal
        isOpen={isPaymentFormOpen}
        onClose={() => setIsPaymentFormOpen(false)}
        onSubmit={async (values) => {
          await loanApi.recordLoanPayment(loan.id, values)
          await refreshAfterPayment()
        }}
      />
    </div>
  )
}
