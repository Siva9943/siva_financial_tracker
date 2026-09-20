import { useTranslation } from 'react-i18next'
import * as incomeApi from '../api/incomeApi'
import TransactionTypeView from '../features/transactions/TransactionTypeView.jsx'
import { INCOME_CATEGORIES } from '../utils/categories.js'

const api = {
  list: incomeApi.listIncome,
  create: incomeApi.createIncome,
  update: incomeApi.updateIncome,
  remove: incomeApi.deleteIncome,
  summary: incomeApi.getIncomeSummary,
}

export default function Income() {
  const { t } = useTranslation()
  return (
    <TransactionTypeView
      transactionType="INCOME"
      title={t('pages.income')}
      accent="text-green-700"
      categories={INCOME_CATEGORIES}
      api={api}
      addLabel={t('transactions.addIncome')}
    />
  )
}
