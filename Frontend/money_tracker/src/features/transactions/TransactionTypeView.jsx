import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'
import ConfirmDialog from '../../components/ConfirmDialog.jsx'
import LoadingSpinner from '../../components/LoadingSpinner.jsx'
import Pagination from '../../components/Pagination.jsx'
import { getErrorMessage } from '../../utils/apiError.js'
import CategoryBreakdownChart from './CategoryBreakdownChart.jsx'
import MonthlyTrendChart from './MonthlyTrendChart.jsx'
import PeriodSummaryCards from './PeriodSummaryCards.jsx'
import RecurringManager from './RecurringManager.jsx'
import TransactionFilters from './TransactionFilters.jsx'
import TransactionFormModal from './TransactionFormModal.jsx'
import TransactionTable from './TransactionTable.jsx'

const PAGE_SIZE = 20
const DEFAULT_FILTERS = { search: '', date_from: '', date_to: '' }

export default function TransactionTypeView({ transactionType, title, accent, categories, api, addLabel }) {
  const { t } = useTranslation()
  const [transactions, setTransactions] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [ordering, setOrdering] = useState('-transaction_date')
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const [summary, setSummary] = useState(null)

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingTransaction, setEditingTransaction] = useState(null)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const fetchTransactions = async () => {
    setIsLoading(true)
    setError('')
    try {
      const data = await api.list({
        page,
        ordering,
        search: filters.search || undefined,
        date_from: filters.date_from || undefined,
        date_to: filters.date_to || undefined,
      })
      setTransactions(data.results)
      setCount(data.count)
    } catch (err) {
      setError(getErrorMessage(err, t('transactions.loadTypeError', { type: title.toLowerCase() })))
    } finally {
      setIsLoading(false)
    }
  }

  const fetchSummary = async () => {
    try {
      const data = await api.summary()
      setSummary(data)
    } catch {
      // summary is supplementary — a failure here shouldn't block the ledger view
    }
  }

  useEffect(() => {
    fetchTransactions()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, ordering, filters])

  useEffect(() => {
    fetchSummary()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const refreshAll = async () => {
    await Promise.all([fetchTransactions(), fetchSummary()])
  }

  const handleFiltersChange = (nextFilters) => {
    setPage(1)
    setFilters(nextFilters)
  }

  const openCreateForm = () => {
    setEditingTransaction(null)
    setIsFormOpen(true)
  }

  const openEditForm = (transaction) => {
    setEditingTransaction(transaction)
    setIsFormOpen(true)
  }

  const handleFormSubmit = async (values) => {
    if (editingTransaction) {
      await api.update(editingTransaction.id, values)
    } else {
      await api.create(values)
    }
    await refreshAll()
  }

  const confirmDelete = async () => {
    setIsDeleting(true)
    try {
      await api.remove(pendingDelete.id)
      setPendingDelete(null)
      await refreshAll()
    } catch (err) {
      setError(getErrorMessage(err, t('transactions.deleteError')))
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{title}</h1>
        <Button onClick={openCreateForm}>
          <Plus className="size-4" />
          {addLabel}
        </Button>
      </div>

      <PeriodSummaryCards totals={summary?.totals} accent={accent} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <CategoryBreakdownChart data={summary?.breakdown} title={title} />
        <RecurringManager transactionType={transactionType} categories={categories} onGenerated={refreshAll} />
        <MonthlyTrendChart
          data={summary?.monthly_trend}
          mode="single"
          title={t('transactions.monthlyTrend', { type: title })}
          className="lg:col-span-2"
        />
      </div>

      <TransactionFilters filters={filters} onChange={handleFiltersChange} hideTypeFilter />

      {error && <p className="text-sm text-red-600">{error}</p>}

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : (
        <>
          <TransactionTable
            transactions={transactions}
            ordering={ordering}
            onSortChange={setOrdering}
            onEdit={openEditForm}
            onDelete={setPendingDelete}
            hideType
          />
          <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
        </>
      )}

      <TransactionFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        editingTransaction={editingTransaction}
        lockedType={transactionType}
      />

      <ConfirmDialog
        isOpen={!!pendingDelete}
        title={t('transactions.deleteTitle')}
        message={t('transactions.deleteMessage')}
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
        isConfirming={isDeleting}
      />
    </div>
  )
}
