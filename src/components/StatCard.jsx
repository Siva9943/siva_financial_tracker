export default function StatCard({ label, value, accent = 'text-slate-900 dark:text-slate-100' }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 transition-shadow duration-150 hover:shadow-md dark:border-slate-700 dark:bg-slate-800">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${accent}`}>{value}</p>
    </div>
  )
}
