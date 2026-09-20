import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { registerSW } from 'virtual:pwa-register'

export default function PwaUpdateToast() {
  const { t } = useTranslation()
  const [needRefresh, setNeedRefresh] = useState(false)
  const updateSWRef = useRef(null)

  useEffect(() => {
    updateSWRef.current = registerSW({ onNeedRefresh: () => setNeedRefresh(true) })
  }, [])

  if (!needRefresh) return null

  return (
    <div className="fixed inset-x-4 bottom-4 z-50 mx-auto flex max-w-sm items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-lg animate-fade-in-up dark:border-slate-700 dark:bg-slate-800">
      <p className="text-sm text-slate-700 dark:text-slate-200">{t('common.updateAvailable')}</p>
      <button
        type="button"
        onClick={() => updateSWRef.current?.(true)}
        className="shrink-0 rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
      >
        {t('common.reload')}
      </button>
    </div>
  )
}
