export default function EmptyState({ title, description }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-16 text-center dark:border-slate-700">
      <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{title}</p>
      {description && <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>}
    </div>
  )
}
