import { Pencil, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as recurringApi from '../../api/recurringApi'
import Button from '../../components/Button.jsx'
import ConfirmDialog from '../../components/ConfirmDialog.jsx'
import EmptyState from '../../components/EmptyState.jsx'
import { formatCurrency, formatDate } from '../../utils/format.js'
import { getErrorMessage } from '../../utils/apiError.js'
import RecurringFormModal from './RecurringFormModal.jsx'

const FREQUENCY_LABEL_KEYS = {
  DAILY: 'transactions.frequencyDaily',
  WEEKLY: 'transactions.frequencyWeekly',
  MONTHLY: 'transactions.frequencyMonthly',
  YEARLY: 'transactions.frequencyYearly',
}

export default function RecurringManager({ transactionType, categories, onGenerated }) {
  const { t } = useTranslation()
  const [rules, setRules] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRule, setEditingRule] = useState(null)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const fetchRules = async () => {
    setIsLoading(true)
    setError('')
    try {
      const data = await recurringApi.listRecurring({ transaction_type: transactionType })
      setRules(data.results)
    } catch (err) {
      setError(getErrorMessage(err, t('transactions.loadRecurringError')))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchRules()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [transactionType])

  const handleSubmit = async (values) => {
    const payload = { ...values, transaction_type: transactionType }
    if (editingRule) {
      await recurringApi.updateRecurring(editingRule.id, payload)
    } else {
      await recurringApi.createRecurring(payload)
    }
    await fetchRules()
  }

  const confirmDelete = async () => {
    try {
      await recurringApi.deleteRecurring(pendingDelete.id)
      setPendingDelete(null)
      await fetchRules()
    } catch (err) {
      setError(getErrorMessage(err, t('transactions.deleteRecurringError')))
    }
  }

  const runDueNow = async () => {
    setIsGenerating(true)
    setError('')
    try {
      const result = await recurringApi.generateDueRecurring()
      await fetchRules()
      onGenerated?.(result)
    } catch (err) {
      setError(getErrorMessage(err, t('transactions.generateDueError')))
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{t('transactions.recurring')}</h3>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={runDueNow} disabled={isGenerating}>
            <RefreshCw className={`size-4 ${isGenerating ? 'animate-spin' : ''}`} />
            {t('transactions.runDueNow')}
          </Button>
          <Button
            onClick={() => {
              setEditingRule(null)
              setIsFormOpen(true)
            }}
          >
            <Plus className="size-4" />
            {t('common.add')}
          </Button>
        </div>
      </div>

      {error && <p className="mb-2 text-sm text-red-600">{error}</p>}

      {!isLoading && rules.length === 0 && (
        <EmptyState title={t('transactions.noRecurringRules')} description={t('transactions.automateRepeating')} />
      )}

      {rules.length > 0 && (
        <ul className="divide-y divide-slate-100">
          {rules.map((rule) => (
            <li key={rule.id} className="flex items-center justify-between py-2 text-sm">
              <div>
                <p className="font-medium text-slate-900 dark:text-slate-100">
                  {rule.category} &middot; {formatCurrency(rule.amount)}
                </p>
                <p className="text-slate-500 dark:text-slate-400">
                  {t(FREQUENCY_LABEL_KEYS[rule.frequency])} &middot; {t('transactions.next', { date: formatDate(rule.next_run_date) })}
                  {!rule.is_active && ` · ${t('transactions.inactive')}`}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setEditingRule(rule)
                    setIsFormOpen(true)
                  }}
                  aria-label={t('common.edit')}
                  className="text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:text-slate-300"
                >
                  <Pencil className="size-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setPendingDelete(rule)}
                  aria-label={t('common.delete')}
                  className="text-slate-400 dark:text-slate-500 hover:text-red-600"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <RecurringFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleSubmit}
        editingRule={editingRule}
        categories={categories}
      />

      <ConfirmDialog
        isOpen={!!pendingDelete}
        title={t('transactions.deleteRecurringTitle')}
        message={t('transactions.deleteRecurringMessage')}
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
      />
    </div>
  )
}
