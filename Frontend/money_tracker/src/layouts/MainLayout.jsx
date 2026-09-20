import { LayoutDashboard, Menu, Settings as SettingsIcon } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import LanguageSwitcher from '../components/LanguageSwitcher.jsx'
import NotificationBell from '../components/NotificationBell.jsx'
import ThemeToggle from '../components/ThemeToggle.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import MegaMenuNav from '../features/layout/MegaMenuNav.jsx'
import MobileNavDrawer from '../features/layout/MobileNavDrawer.jsx'

export default function MainLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <header className="sticky top-0 z-30 flex items-center justify-between gap-4 border-b border-slate-200 bg-white px-4 py-3 sm:px-6 dark:border-slate-700 dark:bg-slate-800">
        <div className="flex min-w-0 items-center gap-6">
          <button
            type="button"
            onClick={() => setIsDrawerOpen(true)}
            aria-label={t('nav.menu')}
            className="text-slate-600 lg:hidden dark:text-slate-300"
          >
            <Menu className="size-6" />
          </button>

          <Link to="/" className="flex shrink-0 items-center gap-2">
            <LayoutDashboard className="size-5 text-brand-600 dark:text-brand-400" />
            <span className="text-lg font-semibold text-slate-900 dark:text-white">{t('app.name')}</span>
          </Link>

          <MegaMenuNav />
        </div>

        <div className="flex shrink-0 items-center gap-3 sm:gap-4">
          <div className="hidden items-center gap-3 sm:flex">
            <LanguageSwitcher />
            <ThemeToggle />
          </div>
          <NotificationBell />
          <span className="hidden text-sm text-slate-600 md:inline dark:text-slate-300">{user?.username}</span>
          <Link
            to="/settings"
            className="hidden text-slate-500 hover:text-slate-900 sm:block dark:text-slate-400 dark:hover:text-white"
            aria-label={t('nav.settings')}
          >
            <SettingsIcon className="size-5" />
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            className="hidden items-center gap-1 text-sm text-slate-500 hover:text-slate-900 sm:flex dark:text-slate-400 dark:hover:text-white"
          >
            {t('nav.logout')}
          </button>
        </div>
      </header>

      <MobileNavDrawer isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} user={user} onLogout={handleLogout} />

      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
        <Outlet />
      </main>
    </div>
  )
}
