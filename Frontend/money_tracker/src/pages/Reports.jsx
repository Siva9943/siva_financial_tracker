import { Download, Eye } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as reportApi from '../api/reportApi'
import Button from '../components/Button.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import Select from '../components/Select.jsx'
import ReportParamsForm from '../features/reports/ReportParamsForm.jsx'
import ReportPreview from '../features/reports/ReportPreview.jsx'
import { getErrorMessage } from '../utils/apiError.js'
import { EXPORT_FORMATS, REPORT_TYPES } from '../utils/reportOptions.js'

export default function Reports() {
  const { t } = useTranslation()
  const [reportType, setReportType] = useState('monthly')
  const [params, setParams] = useState({})
  const [report, setReport] = useState(null)
  const [isLoadingPreview, setIsLoadingPreview] = useState(false)
  const [downloadingFormat, setDownloadingFormat] = useState('')
  const [error, setError] = useState('')

  const selectedType = REPORT_TYPES.find((rt) => rt.value === reportType)

  const handleTypeChange = (value) => {
    setReportType(value)
    setParams({})
    setReport(null)
    setError('')
  }

  const handlePreview = async () => {
    setIsLoadingPreview(true)
    setError('')
    try {
      const data = await reportApi.getReportPreview(reportType, params)
      setReport(data)
    } catch (err) {
      setError(getErrorMessage(err, t('reports.previewError')))
      setReport(null)
    } finally {
      setIsLoadingPreview(false)
    }
  }

  const handleDownload = async (exportFormat) => {
    setDownloadingFormat(exportFormat)
    setError('')
    try {
      await reportApi.downloadReport(reportType, params, exportFormat)
    } catch (err) {
      setError(getErrorMessage(err, t('reports.downloadError')))
    } finally {
      setDownloadingFormat('')
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.reports')}</h1>

      <div className="space-y-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <Select label={t('reports.reportLabel')} value={reportType} onChange={(e) => handleTypeChange(e.target.value)}>
            {REPORT_TYPES.map((rt) => (
              <option key={rt.value} value={rt.value}>
                {t(`reports.type.${rt.value}`)}
              </option>
            ))}
          </Select>
          <ReportParamsForm paramKeys={selectedType.params} params={params} onChange={setParams} />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button variant="secondary" onClick={handlePreview} disabled={isLoadingPreview}>
            <Eye className="size-4" />
            {isLoadingPreview ? t('common.loading') : t('reports.preview')}
          </Button>
          {EXPORT_FORMATS.map((f) => (
            <Button key={f.value} variant="secondary" onClick={() => handleDownload(f.value)} disabled={!!downloadingFormat}>
              <Download className="size-4" />
              {downloadingFormat === f.value ? t('reports.downloading') : t(`reports.format.${f.value}`)}
            </Button>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {isLoadingPreview ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : (
        report && <ReportPreview report={report} />
      )}
    </div>
  )
}
