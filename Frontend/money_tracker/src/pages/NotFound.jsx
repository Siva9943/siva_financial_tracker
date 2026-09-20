import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function NotFound() {
  const { t } = useTranslation()
  return (
    <div className="text-center">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('notFound.title')}</h1>
      <Link to="/" className="mt-2 inline-block text-brand-600 hover:underline">
        {t('notFound.backToDashboard')}
      </Link>
    </div>
  )
}
