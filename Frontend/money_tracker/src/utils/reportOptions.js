export const REPORT_TYPES = [
  { value: 'monthly', label: 'Monthly Financial Report', params: ['month', 'year'] },
  { value: 'yearly', label: 'Yearly Financial Report', params: ['year'] },
  { value: 'loan', label: 'Loan Report', params: [] },
  { value: 'expense', label: 'Expense Report', params: ['start', 'end'] },
  { value: 'budget', label: 'Budget Report', params: ['month', 'year'] },
  { value: 'repayment', label: 'Repayment Report', params: [] },
  { value: 'investment', label: 'Investment Report', params: [] },
  { value: 'portfolio_performance', label: 'Portfolio Performance Report', params: [] },
  { value: 'dividend', label: 'Dividend Report', params: ['start', 'end'] },
  { value: 'investment_transaction', label: 'Investment Transaction Report', params: ['start', 'end'] },
]

export const EXPORT_FORMATS = [
  { value: 'csv', label: 'CSV' },
  { value: 'xlsx', label: 'Excel' },
  { value: 'pdf', label: 'PDF' },
]
