import { useTranslation } from 'react-i18next'
import * as expenseApi from '../api/expenseApi'
import TransactionTypeView from '../features/transactions/TransactionTypeView.jsx'
import { EXPENSE_CATEGORIES } from '../utils/categories.js'

const api = {
  list: expenseApi.listExpenses,
  create: expenseApi.createExpense,
  update: expenseApi.updateExpense,
  remove: expenseApi.deleteExpense,
  summary: expenseApi.getExpenseSummary,
}

export default function Expenses() {
  const { t } = useTranslation()
  return (
    <TransactionTypeView
      transactionType="EXPENSE"
      title={t('pages.expenses')}
      accent="text-red-700"
      categories={EXPENSE_CATEGORIES}
      api={api}
      addLabel={t('transactions.addExpense')}
    />
  )
}
