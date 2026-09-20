import { LogOut, Settings as SettingsIcon, X } from 'lucide-react'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { NavLink } from 'react-router-dom'
import LanguageSwitcher from '../../components/LanguageSwitcher.jsx'
import ThemeToggle from '../../components/ThemeToggle.jsx'
import { NAV_GROUPS } from '../../config/navigation.js'

export default function MobileNavDrawer({ isOpen, onClose, user, onLogout }) {
  const { t } = useTranslation()

  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  if (!isOpen) return null

  const linkClass = ({ isActive }) =>
    `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium ${
      isActive
        ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300'
        : 'text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800'
    }`

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <div className="absolute inset-0 bg-slate-900/40 animate-fade-in" onClick={onClose} aria-hidden="true" />
      <div className="absolute inset-y-0 left-0 flex w-80 max-w-[85vw] flex-col bg-white shadow-xl animate-slide-in-left dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-4 dark:border-slate-700">
          <span className="text-lg font-semibold text-slate-900 dark:text-white">{t('app.name')}</span>
          <button type="button" onClick={onClose} aria-label={t('nav.close')} className="text-slate-500 dark:text-slate-400">
            <X className="size-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-4 overflow-y-auto px-3 py-4">
          {NAV_GROUPS.map((entry) => {
            if (entry.type === 'link') {
              const Icon = entry.icon
              return (
                <NavLink key={entry.to} to={entry.to} end={entry.end} className={linkClass} onClick={onClose}>
                  <Icon className="size-4" />
                  {t(entry.labelKey)}
                </NavLink>
              )
            }
            return (
              <div key={entry.key}>
                <p className="px-3 pb-1 text-xs font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500">
                  {t(entry.labelKey)}
                </p>
                <div className="space-y-0.5">
                  {entry.items.map((item) => {
                    const ItemIcon = item.icon
                    return (
                      <NavLink key={item.to} to={item.to} className={linkClass} onClick={onClose}>
                        <ItemIcon className="size-4" />
                        {t(item.labelKey)}
                      </NavLink>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </nav>

        <div className="space-y-3 border-t border-slate-200 px-4 py-4 dark:border-slate-700">
          <div className="flex items-center justify-between">
            <LanguageSwitcher />
            <ThemeToggle />
          </div>
          <p className="truncate text-sm text-slate-500 dark:text-slate-400">{user?.username}</p>
          <NavLink to="/settings" onClick={onClose} className={linkClass}>
            <SettingsIcon className="size-4" />
            {t('nav.settings')}
          </NavLink>
          <button
            type="button"
            onClick={onLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <LogOut className="size-4" />
            {t('nav.logout')}
          </button>
        </div>
      </div>
    </div>
  )
}
