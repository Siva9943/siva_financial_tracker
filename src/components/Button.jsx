const VARIANTS = {
  primary: 'bg-brand-600 text-white hover:bg-brand-700 disabled:bg-brand-300 dark:disabled:bg-brand-900',
  secondary:
    'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-600 dark:hover:bg-slate-700',
}

export default function Button({ variant = 'primary', className = '', ...props }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-150 active:scale-[0.97] disabled:cursor-not-allowed disabled:active:scale-100 ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  )
}
