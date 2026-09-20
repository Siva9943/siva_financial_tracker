import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as transactionApi from '../api/transactionApi'
import Button from '../components/Button.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import Pagination from '../components/Pagination.jsx'
import MonthlyTrendChart from '../features/transactions/MonthlyTrendChart.jsx'
import TransactionFilters from '../features/transactions/TransactionFilters.jsx'
import TransactionFormModal from '../features/transactions/TransactionFormModal.jsx'
import TransactionTable from '../features/transactions/TransactionTable.jsx'
import { getErrorMessage } from '../utils/apiError.js'

const PAGE_SIZE = 20
const DEFAULT_FILTERS = { search: '', transaction_type: '', date_from: '', date_to: '' }

export default function Transactions() {
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
      const params = {
        page,
        ordering,
        search: filters.search || undefined,
        transaction_type: filters.transaction_type || undefined,
        date_from: filters.date_from || undefined,
        date_to: filters.date_to || undefined,
      }
      const data = await transactionApi.listTransactions(params)
      setTransactions(data.results)
      setCount(data.count)
    } catch (err) {
      setError(getErrorMessage(err, t('transactions.loadError')))
    } finally {
      setIsLoading(false)
    }
  }

  const fetchSummary = async () => {
    try {
      const data = await transactionApi.getTransactionSummary()
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
  }, [])

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
      await transactionApi.updateTransaction(editingTransaction.id, values)
    } else {
      await transactionApi.createTransaction(values)
    }
    await fetchTransactions()
  }

  const confirmDelete = async () => {
    setIsDeleting(true)
    try {
      await transactionApi.deleteTransaction(pendingDelete.id)
      setPendingDelete(null)
      await fetchTransactions()
    } catch (err) {
      setError(getErrorMessage(err, t('transactions.deleteError')))
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.transactions')}</h1>
        <Button onClick={openCreateForm}>
          <Plus className="size-4" />
          {t('transactions.addTransaction')}
        </Button>
      </div>

      <MonthlyTrendChart
        data={summary?.monthly_trend}
        mode="dual"
        title={t('transactions.monthlyTrend', { type: t('pages.transactions') })}
      />

      <TransactionFilters filters={filters} onChange={handleFiltersChange} />

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
          />
          <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
        </>
      )}

      <TransactionFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        editingTransaction={editingTransaction}
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
