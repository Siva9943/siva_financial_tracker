import { LayoutDashboard } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export default function LoadingScreen() {
  const { t } = useTranslation()

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 dark:bg-slate-900">
      <div className="relative flex size-16 items-center justify-center">
        <span className="absolute inset-0 animate-spin-slow rounded-full border-2 border-brand-200 border-t-brand-600 dark:border-brand-900 dark:border-t-brand-400" />
        <LayoutDashboard className="size-7 text-brand-600 dark:text-brand-400" />
      </div>
      <div className="animate-fade-in text-center">
        <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{t('app.name')}</p>
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{t('common.loading')}</p>
      </div>
    </div>
  )
}
