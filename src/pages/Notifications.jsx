import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as notificationApi from '../api/notificationApi'
import Button from '../components/Button.jsx'
import EmptyState from '../components/EmptyState.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { getErrorMessage } from '../utils/apiError.js'
import { labelize } from '../utils/categories.js'
import { formatDateTime } from '../utils/format.js'

export default function Notifications() {
  const { t } = useTranslation()
  const [notifications, setNotifications] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchNotifications = async () => {
    setIsLoading(true)
    setError('')
    try {
      const data = await notificationApi.listNotifications()
      setNotifications(data.results)
    } catch (err) {
      setError(getErrorMessage(err, t('notifications.couldNotLoadNotifications')))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchNotifications()
  }, [])

  const handleMarkRead = async (id) => {
    await notificationApi.markNotificationRead(id)
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)))
  }

  const handleMarkAllRead = async () => {
    await notificationApi.markAllNotificationsRead()
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
  }

  const hasUnread = notifications.some((n) => !n.is_read)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.notifications')}</h1>
        {hasUnread && (
          <Button variant="secondary" onClick={handleMarkAllRead}>
            {t('notifications.markAllAsRead')}
          </Button>
        )}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : notifications.length === 0 ? (
        <EmptyState title={t('notifications.noNotifications')} description={t('notifications.allCaughtUp')} />
      ) : (
        <ul className="divide-y divide-slate-100 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
          {notifications.map((notification) => (
            <li
              key={notification.id}
              className={`px-4 py-3 ${notification.is_read ? '' : 'bg-brand-50/50'}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    {!notification.is_read && <span className="size-2 rounded-full bg-brand-500" />}
                    <p className="font-medium text-slate-900 dark:text-slate-100">{notification.title}</p>
                    <span className="rounded-full bg-slate-100 dark:bg-slate-700 px-2 py-0.5 text-xs text-slate-600 dark:text-slate-400">
                      {labelize(notification.notification_type)}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{notification.message}</p>
                  <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">{formatDateTime(notification.created_at)}</p>
                </div>
                {!notification.is_read && (
                  <button
                    type="button"
                    onClick={() => handleMarkRead(notification.id)}
                    className="shrink-0 text-xs text-brand-600 hover:underline"
                  >
                    {t('notifications.markRead')}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
