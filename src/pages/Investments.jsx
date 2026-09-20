import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import * as investmentApi from '../api/investmentApi'
import Button from '../components/Button.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import Pagination from '../components/Pagination.jsx'
import Select from '../components/Select.jsx'
import DividendHistoryList from '../features/investments/DividendHistoryList.jsx'
import InvestmentContributionChart from '../features/investments/InvestmentContributionChart.jsx'
import InvestmentFormModal from '../features/investments/InvestmentFormModal.jsx'
import InvestmentSummaryCards from '../features/investments/InvestmentSummaryCards.jsx'
import InvestmentTable from '../features/investments/InvestmentTable.jsx'
import { applyInvestedAmountAdjustments, extractBaseInvestmentPayload } from '../features/investments/investmentFormHelpers.js'
import PortfolioAllocationChart from '../features/investments/PortfolioAllocationChart.jsx'
import PortfolioPerformanceChart from '../features/investments/PortfolioPerformanceChart.jsx'
import { getErrorMessage } from '../utils/apiError.js'
import { labelize } from '../utils/categories.js'
import { INVESTMENT_STATUSES, INVESTMENT_TYPES } from '../utils/investmentOptions.js'

const PAGE_SIZE = 20

export default function Investments() {
  const { t } = useTranslation()
  const [investments, setInvestments] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [portfolio, setPortfolio] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingInvestment, setEditingInvestment] = useState(null)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const fetchInvestments = async () => {
    setIsLoading(true)
    setError('')
    try {
      const data = await investmentApi.listInvestments({
        page,
        status: statusFilter || undefined,
        investment_type: typeFilter || undefined,
      })
      setInvestments(data.results)
      setCount(data.count)
    } catch (err) {
      setError(getErrorMessage(err, t('investments.errors.loadInvestments')))
    } finally {
      setIsLoading(false)
    }
  }

  const fetchPortfolio = async () => {
    try {
      setPortfolio(await investmentApi.getPortfolio())
    } catch {
      // portfolio summary is supplementary
    }
  }

  useEffect(() => {
    fetchInvestments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter, typeFilter])

  useEffect(() => {
    fetchPortfolio()
  }, [])

  const refreshAll = async () => {
    await Promise.all([fetchInvestments(), fetchPortfolio()])
  }

  const openCreateForm = () => {
    setEditingInvestment(null)
    setIsFormOpen(true)
  }

  const openEditForm = (investment) => {
    setEditingInvestment(investment)
    setIsFormOpen(true)
  }

  const handleFormSubmit = async (values) => {
    const basePayload = extractBaseInvestmentPayload(values)
    let investmentId = editingInvestment?.id
    if (editingInvestment) {
      await investmentApi.updateInvestment(editingInvestment.id, basePayload)
    } else {
      const created = await investmentApi.createInvestment(basePayload)
      investmentId = created.id
    }
    await applyInvestedAmountAdjustments(investmentApi, investmentId, values)
    await refreshAll()
  }

  const confirmDelete = async () => {
    setIsDeleting(true)
    try {
      await investmentApi.deleteInvestment(pendingDelete.id)
      setPendingDelete(null)
      await refreshAll()
    } catch (err) {
      setError(getErrorMessage(err, t('investments.errors.deleteInvestment')))
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.investments')}</h1>
        <Button onClick={openCreateForm}>
          <Plus className="size-4" />
          {t('investments.addInvestment')}
        </Button>
      </div>

      <InvestmentSummaryCards portfolio={portfolio} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <PortfolioAllocationChart />
        <PortfolioPerformanceChart />
        <InvestmentContributionChart />
        <DividendHistoryList />
      </div>

      <div className="flex flex-wrap gap-3">
        <Select
          label={t('investments.filters.status')}
          value={statusFilter}
          onChange={(e) => {
            setPage(1)
            setStatusFilter(e.target.value)
          }}
        >
          <option value="">{t('investments.filters.allStatuses')}</option>
          {INVESTMENT_STATUSES.map((s) => (
            <option key={s} value={s}>
              {labelize(s)}
            </option>
          ))}
        </Select>
        <Select
          label={t('investments.filters.type')}
          value={typeFilter}
          onChange={(e) => {
            setPage(1)
            setTypeFilter(e.target.value)
          }}
        >
          <option value="">{t('investments.filters.allTypes')}</option>
          {INVESTMENT_TYPES.map((type) => (
            <option key={type} value={type}>
              {labelize(type)}
            </option>
          ))}
        </Select>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : (
        <>
          <InvestmentTable investments={investments} onEdit={openEditForm} onDelete={setPendingDelete} />
          <Pagination page={page} pageSize={PAGE_SIZE} count={count} onPageChange={setPage} />
        </>
      )}

      <InvestmentFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        editingInvestment={editingInvestment}
      />

      <ConfirmDialog
        isOpen={!!pendingDelete}
        title={t('investments.deleteInvestmentTitle')}
        message={t('investments.deleteInvestmentMessage')}
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
        isConfirming={isDeleting}
      />
    </div>
  )
}
