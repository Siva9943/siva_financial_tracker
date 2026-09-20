import { Bell } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import * as notificationApi from '../api/notificationApi'

export default function NotificationBell() {
  const { t } = useTranslation()
  const [count, setCount] = useState(0)

  useEffect(() => {
    let cancelled = false
    notificationApi
      .getUnreadNotificationCount()
      .then((data) => {
        if (!cancelled) setCount(data.count)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <Link
      to="/notifications"
      className="relative text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
      aria-label={t('pages.notifications')}
    >
      <Bell className="size-5" />
      {count > 0 && (
        <span className="absolute -right-1.5 -top-1.5 flex size-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-medium text-white">
          {count > 9 ? '9+' : count}
        </span>
      )}
    </Link>
  )
}
