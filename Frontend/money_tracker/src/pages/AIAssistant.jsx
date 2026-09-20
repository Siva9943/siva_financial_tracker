import { Bot } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as aiApi from '../api/aiApi'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import ChatInput from '../features/ai/ChatInput.jsx'
import ChatMessageBubble from '../features/ai/ChatMessageBubble.jsx'
import { getErrorMessage } from '../utils/apiError.js'

export default function AIAssistant() {
  const { t } = useTranslation()
  const SUGGESTIONS = [
    t('ai.suggestionSpending'),
    t('ai.suggestionActiveLoans'),
    t('ai.suggestionHighestInterest'),
    t('ai.suggestionUpcomingPayments'),
    t('ai.suggestionBudgetStatus'),
  ]
  const [messages, setMessages] = useState([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState('')
  const scrollRef = useRef(null)
  const pendingIdRef = useRef(0)

  const fetchHistory = async () => {
    setIsLoadingHistory(true)
    try {
      const data = await aiApi.getChatHistory()
      setMessages(data.results)
    } catch (err) {
      setError(getErrorMessage(err, t('ai.historyLoadError')))
    } finally {
      setIsLoadingHistory(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isSending])

  const handleSend = async (text) => {
    setError('')
    pendingIdRef.current += 1
    const optimisticUserMessage = {
      id: `pending-${pendingIdRef.current}`,
      role: 'USER',
      content: text,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, optimisticUserMessage])
    setIsSending(true)
    try {
      const data = await aiApi.sendChatMessage(text)
      setMessages((prev) => [...prev.filter((m) => m.id !== optimisticUserMessage.id), data.user_message, data.assistant_message])
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== optimisticUserMessage.id))
      setError(getErrorMessage(err, t('ai.sendError')))
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60">
      <div className="border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3">
        <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{t('pages.aiAssistant')}</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400">{t('ai.disclaimer')}</p>
      </div>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
        {isLoadingHistory ? (
          <div className="flex justify-center py-16">
            <LoadingSpinner />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <Bot className="mb-3 size-10 text-slate-300" />
            <p className="text-sm text-slate-500 dark:text-slate-400">{t('ai.emptyStatePrompt')}</p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((question) => (
                <button
                  key={question}
                  type="button"
                  onClick={() => handleSend(question)}
                  className="rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:bg-slate-700"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => <ChatMessageBubble key={message.id} message={message} />)
        )}

        {isSending && (
          <div className="flex items-center gap-2 pl-11 text-sm text-slate-400 dark:text-slate-500">
            <LoadingSpinner className="size-4" />
            {t('ai.thinking')}
          </div>
        )}
      </div>

      {error && <p className="px-4 py-1 text-sm text-red-600">{error}</p>}

      <ChatInput onSend={handleSend} isSending={isSending} />
    </div>
  )
}
