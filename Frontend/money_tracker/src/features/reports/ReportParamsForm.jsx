import { useTranslation } from 'react-i18next'
import Input from '../../components/Input.jsx'
import Select from '../../components/Select.jsx'
import { MONTH_NAMES } from '../../utils/budgetOptions.js'

const today = new Date()

export default function ReportParamsForm({ paramKeys, params, onChange }) {
  const { t } = useTranslation()
  const update = (patch) => onChange({ ...params, ...patch })

  if (paramKeys.length === 0) return null

  return (
    <div className="flex flex-wrap gap-3">
      {paramKeys.includes('month') && (
        <Select label={t('reports.month')} value={params.month ?? today.getMonth() + 1} onChange={(e) => update({ month: Number(e.target.value) })}>
          {MONTH_NAMES.map((name, index) => (
            <option key={name} value={index + 1}>
              {name}
            </option>
          ))}
        </Select>
      )}
      {paramKeys.includes('year') && (
        <Select
          label={t('reports.year')}
          value={params.year ?? today.getFullYear()}
          onChange={(e) => update({ year: Number(e.target.value) })}
        >
          {[today.getFullYear() - 1, today.getFullYear(), today.getFullYear() + 1].map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </Select>
      )}
      {paramKeys.includes('start') && (
        <Input label={t('reports.from')} type="date" value={params.start ?? ''} onChange={(e) => update({ start: e.target.value })} />
      )}
      {paramKeys.includes('end') && (
        <Input label={t('reports.to')} type="date" value={params.end ?? ''} onChange={(e) => update({ end: e.target.value })} />
      )}
    </div>
  )
}
