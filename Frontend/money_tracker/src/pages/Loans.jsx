import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as loanApi from '../api/loanApi'
import Button from '../components/Button.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import Pagination from '../components/Pagination.jsx'
import Select from '../components/Select.jsx'
import LoanFormModal from '../features/loans/LoanFormModal.jsx'
import LoanPriorityPanel from '../features/loans/LoanPriorityPanel.jsx'
import LoanSummaryCards from '../features/loans/LoanSummaryCards.jsx'
import LoanTable from '../features/loans/LoanTable.jsx'
import LoanTypeBreakdownChart from '../features/loans/LoanTypeBreakdownChart.jsx'
import { getErrorMessage } from '../utils/apiError.js'
import { labelize } from '../utils/categories.js'
import { LOAN_STATUSES, LOAN_TYPES } from '../utils/loanOptions.js'

const PAGE_SIZE = 20

export default function Loans() {
  const { t } = useTranslation()
  const [loans, setLoans] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [summary, setSummary] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingLoan, setEditingLoan] = useState(null)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const fetchLoans = async () => {
    setIsLoading(true)
    setError('')
    try {
      const data = await loanApi.listLoans({
        page,
        status: statusFilter || undefined,
        loan_type: typeFilter || undefined,
      })
      setLoans(data.results)
      setCount(data.count)
    } catch (err) {
      setError(getErrorMessage(err, t('loans.errors.loadLoans')))
    } finally {
      setIsLoading(false)
    }
  }

  const fetchSummary = async () => {
    try {
      setSummary(await loanApi.getLoanSummary())
    } catch {
      // summary is supplementary
    }
  }

  useEffect(() => {
    fetchLoans()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter, typeFilter])

  useEffect(() => {
    fetchSummary()
  }, [])

  const refreshAll = async () => {
    await Promise.all([fetchLoans(), fetchSummary()])
  }

  const openCreateForm = () => {
    setEditingLoan(null)
    setIsFormOpen(true)
  }

  const openEditForm = (loan) => {
    setEditingLoan(loan)
    setIsFormOpen(true)
  }

  const handleFormSubmit = async (values) => {
    if (editingLoan) {
      await loanApi.updateLoan(editingLoan.id, values)
    } else {
      await loanApi.createLoan(values)
    }
    await refreshAll()
  }

  const confirmDelete = async () => {
    setIsDeleting(true)
    try {
      await loanApi.deleteLoan(pendingDelete.id)
      setPendingDelete(null)
      await refreshAll()
    } catch (err) {
      setError(getErrorMessage(err, t('loans.errors.deleteLoan')))
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.loans')}</h1>
        <Button onClick={openCreateForm}>
          <Plus className="size-4" />
          {t('loans.addLoan')}
        </Button>
      </div>

      <LoanSummaryCards summary={summary} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <LoanTypeBreakdownChart loans={loans} />
        <LoanPriorityPanel />
      </div>

      <div className="flex flex-wrap gap-3">
        <Select label={t('loans.filters.status')} value={statusFilter} onChange={(e) => { setPage(1); setStatusFilter(e.target.value) }}>
          <option value="">{t('loans.filters.allStatuses')}</option>
          {LOAN_STATUSES.map((s) => (
            <option key={s} value={s}>
              {labelize(s)}
            </option>
          ))}
        </Select>
        <Select label={t('loans.filters.type')} value={typeFilter} onChange={(e) => { setPage(1); setTypeFilter(e.target.value) }}>
          <option value="">{t('loans.filters.allTypes')}</option>
          {LOAN_TYPES.map((t) => (
            <option key={t} value={t}>
              {labelize(t)}
            </option>
          ))}
        </Select>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : (
        <>
          <LoanTable loans={loans} onEdit={openEditForm} onDelete={setPendingDelete} />
          <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
        </>
      )}

      <LoanFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        editingLoan={editingLoan}
      />

      <ConfirmDialog
        isOpen={!!pendingDelete}
        title={t('loans.deleteLoanTitle')}
        message={t('loans.deleteLoanMessage')}
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
        isConfirming={isDeleting}
      />
    </div>
  )
}
