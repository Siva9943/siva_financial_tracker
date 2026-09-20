export default function ChartViewToggle({ value, onChange, options }) {
  return (
    <div className="inline-flex items-center gap-0.5 rounded-lg border border-slate-200 bg-slate-50 p-0.5 dark:border-slate-700 dark:bg-slate-900">
      {options.map((option) => {
        const Icon = option.icon
        const isActive = option.key === value
        return (
          <button
            key={option.key}
            type="button"
            onClick={() => onChange(option.key)}
            aria-label={option.label}
            aria-pressed={isActive}
            title={option.label}
            className={`flex size-7 items-center justify-center rounded-md transition-colors duration-150 ${
              isActive
                ? 'bg-white text-brand-600 shadow-sm dark:bg-slate-700 dark:text-brand-400'
                : 'text-slate-400 hover:text-slate-700 dark:text-slate-500 dark:hover:text-slate-200'
            }`}
          >
            <Icon className="size-4" />
          </button>
        )
      })}
    </div>
  )
}
