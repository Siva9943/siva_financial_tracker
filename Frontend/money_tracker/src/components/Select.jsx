import { forwardRef } from 'react'

const Select = forwardRef(function Select({ label, error, children, ...props }, ref) {
  return (
    <label className="block">
      {label && <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">{label}</span>}
      <select
        ref={ref}
        className={`w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:ring-2 focus:ring-brand-500 dark:bg-slate-800 dark:text-slate-100 ${
          error ? 'border-red-400 dark:border-red-500' : 'border-slate-300 dark:border-slate-600'
        }`}
        {...props}
      >
        {children}
      </select>
      {error && <span className="mt-1 block text-xs text-red-600 dark:text-red-400">{error}</span>}
    </label>
  )
})

export default Select
