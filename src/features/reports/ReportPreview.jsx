import { useTranslation } from 'react-i18next'

export default function ReportPreview({ report }) {
  const { t } = useTranslation()
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{report.title}</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">{t('reports.generatedAt', { date: report.generated_at })}</p>
      </div>

      {report.sections.map((section) => (
        <div key={section.heading} className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
          <h3 className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 px-4 py-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
            {section.heading}
          </h3>
          {section.rows.length === 0 ? (
            <p className="px-4 py-3 text-sm text-slate-400 dark:text-slate-500">{t('reports.noData')}</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-500 dark:text-slate-400">
                <tr>
                  {section.columns.map((column) => (
                    <th key={column} className="px-4 py-2">
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {section.rows.map((row, index) => (
                  <tr key={index} className="border-t border-slate-100 dark:border-slate-800">
                    {row.map((cell, cellIndex) => (
                      <td key={cellIndex} className="px-4 py-2 text-slate-600 dark:text-slate-400">
                        {cell === null || cell === undefined ? '—' : String(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}
    </div>
  )
}
