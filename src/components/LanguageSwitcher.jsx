import { Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { setLanguage } from '../i18n/index.js'

const LANGUAGES = [
  { code: 'en', label: 'EN' },
  { code: 'ta', label: 'தமிழ்' },
]

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation()

  return (
    <label className="flex items-center gap-1 text-slate-500 dark:text-slate-400" aria-label={t('common.language')}>
      <Languages className="size-4" />
      <select
        value={i18n.language}
        onChange={(e) => setLanguage(e.target.value)}
        className="bg-transparent text-sm outline-none dark:bg-slate-900"
      >
        {LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code} className="dark:bg-slate-800">
            {lang.label}
          </option>
        ))}
      </select>
    </label>
  )
}
