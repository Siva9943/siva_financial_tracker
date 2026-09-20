import { ArrowLeft, Pencil, Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate, useParams } from 'react-router-dom'
import * as investmentApi from '../api/investmentApi'
import Button from '../components/Button.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import StatCard from '../components/StatCard.jsx'
import InvestmentFormModal from '../features/investments/InvestmentFormModal.jsx'
import InvestmentTransactionFormModal from '../features/investments/InvestmentTransactionFormModal.jsx'
import InvestmentTransactionTable from '../features/investments/InvestmentTransactionTable.jsx'
import { applyInvestedAmountAdjustments, extractBaseInvestmentPayload } from '../features/investments/investmentFormHelpers.js'
import { getErrorMessage } from '../utils/apiError.js'
import { labelize } from '../utils/categories.js'
import { formatCurrency } from '../utils/format.js'
import { INVESTMENT_STATUS_STYLES } from '../utils/investmentOptions.js'

function DetailRow({ label, value }) {
  return (
    <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 py-2 text-sm last:border-0">
      <span className="text-slate-500 dark:text-slate-400">{label}</span>
      <span className="font-medium text-slate-900 dark:text-slate-100">{value}</span>
    </div>
  )
}

function signedAccent(value) {
  const num = Number(value ?? 0)
  if (num > 0) return 'text-green-600 dark:text-green-400'
  if (num < 0) return 'text-red-600 dark:text-red-400'
  return 'text-slate-900 dark:text-slate-100'
}

function formatSignedCurrency(amount) {
  const value = Number(amount ?? 0)
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${formatCurrency(value)}`
}

function formatSignedPercent(value) {
  const num = Number(value ?? 0)
  const prefix = num > 0 ? '+' : ''
  return `${prefix}${num.toFixed(2)}%`
}

const TABS = ['overview', 'transactions', 'performance', 'dividends']

export default function InvestmentDetail({ initialTab = 'overview' }) {
  const { t } = useTranslation()
  const { id } = useParams()
  const navigate = useNavigate()
  const [investment, setInvestment] = useState(null)
  const [error, setError] = useState('')
  const [transactions, setTransactions] = useState([])
  const [activeTab, setActiveTab] = useState(initialTab)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [isTransactionFormOpen, setIsTransactionFormOpen] = useState(false)

  const fetchInvestment = async () => {
    setError('')
    try {
      setInvestment(await investmentApi.getInvestment(id))
    } catch (err) {
      setError(getErrorMessage(err, t('investments.errors.loadInvestment')))
    }
  }

  const fetchTransactions = async () => {
    try {
      const data = await investmentApi.listInvestmentTransactions(id)
      setTransactions(data.results)
    } catch {
      // transaction history is supplementary
    }
  }

  useEffect(() => {
    fetchInvestment()
    fetchTransactions()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const refreshAfterTransaction = async () => {
    await Promise.all([fetchInvestment(), fetchTransactions()])
  }

  if (error) {
    return (
      <div>
        <p className="text-sm text-red-600">{error}</p>
        <Link to="/investments" className="mt-2 inline-block text-brand-600 hover:underline">
          {t('investments.backToInvestments')}
        </Link>
      </div>
    )
  }

  if (!investment) {
    return (
      <div className="flex justify-center py-16">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <button
            type="button"
            onClick={() => navigate('/investments')}
            className="mb-2 flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:text-slate-100"
          >
            <ArrowLeft className="size-4" />
            {t('investments.backToInvestments')}
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{investment.name}</h1>
            {investment.symbol && <span className="text-sm text-slate-500 dark:text-slate-400">{investment.symbol}</span>}
            <span className={`rounded-full px-2 py-1 text-xs font-medium ${INVESTMENT_STATUS_STYLES[investment.status]}`}>
              {labelize(investment.status)}
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {labelize(investment.investment_type)} {investment.platform && `· ${investment.platform}`}
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setIsTransactionFormOpen(true)}>
            <Plus className="size-4" />
            {t('investments.addTransaction')}
          </Button>
          <Button variant="secondary" onClick={() => setIsFormOpen(true)}>
            <Pencil className="size-4" />
            {t('common.edit')}
          </Button>
        </div>
      </div>

      <div className="flex gap-1 border-b border-slate-200 dark:border-slate-700">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400'
                : 'border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
            }`}
          >
            {t(`investments.tabs.${tab}`)}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label={t('investments.fields.quantity')} value={investment.quantity} />
            <StatCard label={t('investments.fields.avgBuyPrice')} value={formatCurrency(investment.average_buy_price)} />
            <StatCard label={t('investments.fields.currentPrice')} value={formatCurrency(investment.current_price)} />
            <StatCard label={t('investments.fields.currentValue')} value={formatCurrency(investment.current_value)} />
          </div>

          <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
            <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('investments.investmentDetails')}</h3>
            <DetailRow label={t('investments.fields.totalInvested')} value={formatCurrency(investment.total_invested)} />
            <DetailRow
              label={t('investments.fields.realizedPL')}
              value={<span className={signedAccent(investment.realized_profit_loss)}>{formatSignedCurrency(investment.realized_profit_loss)}</span>}
            />
            <DetailRow
              label={t('investments.fields.unrealizedPL')}
              value={<span className={signedAccent(investment.unrealized_profit_loss)}>{formatSignedCurrency(investment.unrealized_profit_loss)}</span>}
            />
            <DetailRow label={t('investments.fields.dividendIncome')} value={formatCurrency(investment.dividend_income)} />
          </div>

          {investment.notes && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
              <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('investments.notes')}</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">{investment.notes}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'transactions' && <InvestmentTransactionTable transactions={transactions} />}

      {activeTab === 'performance' && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{t('investments.tabs.performance')}</h3>
          <DetailRow label={t('investments.fields.capitalGain')} value={formatCurrency(investment.capital_gain)} />
          <DetailRow label={t('investments.fields.dividendIncome')} value={formatCurrency(investment.dividend_income)} />
          <DetailRow label={t('investments.fields.totalFees')} value={formatCurrency(investment.total_fees)} />
          <DetailRow label={t('investments.fields.totalTax')} value={formatCurrency(investment.total_tax)} />
          <DetailRow
            label={t('investments.fields.totalReturn')}
            value={<span className={signedAccent(investment.total_return)}>{formatSignedCurrency(investment.total_return)}</span>}
          />
          <DetailRow
            label={t('investments.fields.returnPercentage')}
            value={<span className={signedAccent(investment.return_percentage)}>{formatSignedPercent(investment.return_percentage)}</span>}
          />
          {investment.methodology && (
            <p className="mt-3 text-xs text-slate-400 dark:text-slate-500">
              {t('investments.methodologyLabel', { value: labelize(investment.methodology) })}
            </p>
          )}
        </div>
      )}

      {activeTab === 'dividends' && <InvestmentTransactionTable transactions={transactions} filterType="DIVIDEND" />}

      <InvestmentFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={async (values) => {
          await investmentApi.updateInvestment(investment.id, extractBaseInvestmentPayload(values))
          await applyInvestedAmountAdjustments(investmentApi, investment.id, values)
          await refreshAfterTransaction()
        }}
        editingInvestment={investment}
      />

      <InvestmentTransactionFormModal
        isOpen={isTransactionFormOpen}
        onClose={() => setIsTransactionFormOpen(false)}
        onSubmit={async (values) => {
          await investmentApi.recordInvestmentTransaction(investment.id, values)
          await refreshAfterTransaction()
        }}
      />
    </div>
  )
}
