import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as goalApi from '../api/goalApi'
import Button from '../components/Button.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import EmptyState from '../components/EmptyState.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ContributionFormModal from '../features/goals/ContributionFormModal.jsx'
import GoalCard from '../features/goals/GoalCard.jsx'
import GoalFormModal from '../features/goals/GoalFormModal.jsx'
import { getErrorMessage } from '../utils/apiError.js'

export default function Goals() {
  const { t } = useTranslation()
  const [goals, setGoals] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingGoal, setEditingGoal] = useState(null)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [contributingGoal, setContributingGoal] = useState(null)

  const fetchGoals = async () => {
    setIsLoading(true)
    setError('')
    try {
      const data = await goalApi.listGoals()
      setGoals(data.results)
    } catch (err) {
      setError(getErrorMessage(err, t('goals.loadError')))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchGoals()
  }, [])

  const openCreateForm = () => {
    setEditingGoal(null)
    setIsFormOpen(true)
  }

  const openEditForm = (goal) => {
    setEditingGoal(goal)
    setIsFormOpen(true)
  }

  const handleFormSubmit = async (values) => {
    if (editingGoal) {
      await goalApi.updateGoal(editingGoal.id, values)
    } else {
      await goalApi.createGoal(values)
    }
    await fetchGoals()
  }

  const confirmDelete = async () => {
    setIsDeleting(true)
    try {
      await goalApi.deleteGoal(pendingDelete.id)
      setPendingDelete(null)
      await fetchGoals()
    } catch (err) {
      setError(getErrorMessage(err, t('goals.deleteError')))
    } finally {
      setIsDeleting(false)
    }
  }

  const handleContribute = async (values) => {
    await goalApi.recordContribution(contributingGoal.id, values)
    await fetchGoals()
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.goals')}</h1>
        <Button onClick={openCreateForm}>
          <Plus className="size-4" />
          {t('goals.addGoal')}
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : goals.length === 0 ? (
        <EmptyState title={t('goals.emptyTitle')} description={t('goals.emptyDescription')} />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {goals.map((goal) => (
            <GoalCard
              key={goal.id}
              goal={goal}
              onEdit={openEditForm}
              onDelete={setPendingDelete}
              onContribute={setContributingGoal}
            />
          ))}
        </div>
      )}

      <GoalFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        editingGoal={editingGoal}
      />

      <ContributionFormModal
        isOpen={!!contributingGoal}
        onClose={() => setContributingGoal(null)}
        onSubmit={handleContribute}
      />

      <ConfirmDialog
        isOpen={!!pendingDelete}
        title={t('goals.deleteTitle')}
        message={t('goals.deleteMessage')}
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
        isConfirming={isDeleting}
      />
    </div>
  )
}
