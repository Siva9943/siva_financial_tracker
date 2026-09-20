import { Send } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import Button from '../../components/Button.jsx'

export default function ChatInput({ onSend, isSending }) {
  const { t } = useTranslation()
  const [value, setValue] = useState('')

  const submit = (event) => {
    event.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || isSending) return
    onSend(trimmed)
    setValue('')
  }

  return (
    <form onSubmit={submit} className="flex gap-2 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-3">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={t('ai.chatInputPlaceholder')}
        disabled={isSending}
        className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-50 dark:bg-slate-800/60"
      />
      <Button type="submit" disabled={isSending || !value.trim()}>
        <Send className="size-4" />
        {t('ai.send')}
      </Button>
    </form>
  )
}
