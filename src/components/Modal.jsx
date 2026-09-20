import { X } from 'lucide-react'
import { useEffect } from 'react'
import { createPortal } from 'react-dom'

export default function Modal({ title, isOpen, onClose, children }) {
  useEffect(() => {
    if (!isOpen) return undefined

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4 animate-fade-in">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-4 shadow-lg animate-scale-in sm:p-6 dark:bg-slate-800">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
          >
            <X className="size-5" />
          </button>
        </div>
        {children}
      </div>
    </div>,
    document.body,
  )
}
