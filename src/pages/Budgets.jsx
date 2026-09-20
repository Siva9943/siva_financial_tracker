import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as budgetApi from '../api/budgetApi'
import Button from '../components/Button.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import EmptyState from '../components/EmptyState.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import Select from '../components/Select.jsx'
import StatCard from '../components/StatCard.jsx'
import BudgetCard from '../features/budgets/BudgetCard.jsx'
import BudgetFormModal from '../features/budgets/BudgetFormModal.jsx'
import { getErrorMessage } from '../utils/apiError.js'
import { formatCurrency } from '../utils/format.js'
import { MONTH_NAMES } from '../utils/budgetOptions.js'

const today = new Date()

export default function Budgets() {
  const { t } = useTranslation()
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [year, setYear] = useState(today.getFullYear())
  const [budgets, setBudgets] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingBudget, setEditingBudget] = useState(null)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const fetchBudgets = async () => {
    setIsLoading(true)
    setError('')
    try {
      const data = await budgetApi.listBudgets({ month, year })
      setBudgets(data.results)
    } catch (err) {
      setError(getErrorMessage(err, t('budgets.loadError')))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchBudgets()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [month, year])

  const openCreateForm = () => {
    setEditingBudget(null)
    setIsFormOpen(true)
  }

  const openEditForm = (budget) => {
    setEditingBudget(budget)
    setIsFormOpen(true)
  }

  const handleFormSubmit = async (values) => {
    if (editingBudget) {
      await budgetApi.updateBudget(editingBudget.id, { amount: values.amount, alert_thresholds: values.alert_thresholds })
    } else {
      await budgetApi.createBudget(values)
    }
    await fetchBudgets()
  }

  const confirmDelete = async () => {
    setIsDeleting(true)
    try {
      await budgetApi.deleteBudget(pendingDelete.id)
      setPendingDelete(null)
      await fetchBudgets()
    } catch (err) {
      setError(getErrorMessage(err, t('budgets.deleteError')))
    } finally {
      setIsDeleting(false)
    }
  }

  const totals = budgets.reduce(
    (acc, b) => ({
      budgeted: acc.budgeted + Number(b.amount),
      spent: acc.spent + Number(b.spent),
      remaining: acc.remaining + Number(b.remaining),
    }),
    { budgeted: 0, spent: 0, remaining: 0 },
  )
  const exceededCount = budgets.filter((b) => b.status === 'EXCEEDED').length

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.budgets')}</h1>
        <Button onClick={openCreateForm}>
          <Plus className="size-4" />
          {t('budgets.addBudget')}
        </Button>
      </div>

      <div className="flex flex-wrap gap-3">
        <Select label={t('budgets.month')} value={month} onChange={(e) => setMonth(Number(e.target.value))}>
          {MONTH_NAMES.map((name, index) => (
            <option key={name} value={index + 1}>
              {name}
            </option>
          ))}
        </Select>
        <Select label={t('budgets.year')} value={year} onChange={(e) => setYear(Number(e.target.value))}>
          {[year - 1, year, year + 1].map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </Select>
      </div>

      {budgets.length > 0 && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label={t('budgets.totalBudgeted')} value={formatCurrency(totals.budgeted)} />
          <StatCard label={t('budgets.totalSpent')} value={formatCurrency(totals.spent)} accent="text-amber-700" />
          <StatCard label={t('budgets.remaining')} value={formatCurrency(totals.remaining)} />
          <StatCard label={t('budgets.exceeded')} value={exceededCount} accent={exceededCount > 0 ? 'text-red-700' : undefined} />
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : budgets.length === 0 ? (
        <EmptyState title={t('budgets.emptyTitle')} description={t('budgets.emptyDescription')} />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {budgets.map((budget) => (
            <BudgetCard key={budget.id} budget={budget} onEdit={openEditForm} onDelete={setPendingDelete} />
          ))}
        </div>
      )}

      <BudgetFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        editingBudget={editingBudget}
        month={month}
        year={year}
      />

      <ConfirmDialog
        isOpen={!!pendingDelete}
        title={t('budgets.deleteTitle')}
        message={t('budgets.deleteMessage')}
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
        isConfirming={isDeleting}
      />
    </div>
  )
}
