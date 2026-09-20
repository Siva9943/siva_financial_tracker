import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as notificationApi from '../api/notificationApi'
import Button from '../components/Button.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ReminderFormModal from '../features/notifications/ReminderFormModal.jsx'
import ReminderList from '../features/notifications/ReminderList.jsx'
import { getErrorMessage } from '../utils/apiError.js'

export default function Reminders() {
  const { t } = useTranslation()
  const [reminders, setReminders] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const fetchReminders = async () => {
    setIsLoading(true)
    setError('')
    try {
      const data = await notificationApi.listReminders({ is_completed: false })
      setReminders(data.results)
    } catch (err) {
      setError(getErrorMessage(err, t('notifications.couldNotLoadReminders')))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchReminders()
  }, [])

  const handleCreate = async (values) => {
    await notificationApi.createReminder(values)
    await fetchReminders()
  }

  const handleSnooze = async (id, snoozedUntil) => {
    try {
      await notificationApi.snoozeReminder(id, snoozedUntil)
      await fetchReminders()
    } catch (err) {
      setError(getErrorMessage(err, t('notifications.couldNotSnoozeReminder')))
    }
  }

  const handleComplete = async (id) => {
    try {
      await notificationApi.completeReminder(id)
      await fetchReminders()
    } catch (err) {
      setError(getErrorMessage(err, t('notifications.couldNotCompleteReminder')))
    }
  }

  const confirmDelete = async () => {
    setIsDeleting(true)
    try {
      await notificationApi.deleteReminder(pendingDelete.id)
      setPendingDelete(null)
      await fetchReminders()
    } catch (err) {
      setError(getErrorMessage(err, t('notifications.couldNotDeleteReminder')))
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.reminders')}</h1>
        <Button onClick={() => setIsFormOpen(true)}>
          <Plus className="size-4" />
          {t('notifications.addReminder')}
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : (
        <ReminderList
          reminders={reminders}
          onSnooze={handleSnooze}
          onComplete={handleComplete}
          onDelete={setPendingDelete}
        />
      )}

      <ReminderFormModal isOpen={isFormOpen} onClose={() => setIsFormOpen(false)} onSubmit={handleCreate} />

      <ConfirmDialog
        isOpen={!!pendingDelete}
        title={t('notifications.deleteReminderTitle')}
        message={t('notifications.deleteReminderMessage')}
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
        isConfirming={isDeleting}
      />
    </div>
  )
}
