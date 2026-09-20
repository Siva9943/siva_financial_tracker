// Mirrors Backend/apps/transactions/categories.py — keep in sync.

export const TRANSACTION_TYPES = ['INCOME', 'EXPENSE', 'LOAN_PAYMENT', 'REFUND', 'TRANSFER']

export const PAYMENT_METHODS = ['CASH', 'BANK_TRANSFER', 'UPI', 'CARD', 'CHEQUE', 'OTHER']

export const INCOME_CATEGORIES = ['Salary', 'Freelance', 'Business', 'Investment', 'Farming', 'Other']

export const EXPENSE_CATEGORIES = [
  'Food',
  'Travel',
  'Rent',
  'Electricity',
  'Education',
  'Medical',
  'Shopping',
  'Entertainment',
  'Loan EMI',
  'Insurance',
  'Mobile',
  'Internet',
  'Groceries',
  'Other',
]

export function categoriesForType(transactionType) {
  if (transactionType === 'INCOME') return INCOME_CATEGORIES
  if (transactionType === 'EXPENSE') return EXPENSE_CATEGORIES
  return ['Other']
}

export function labelize(value) {
  return value
    .toLowerCase()
    .split('_')
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(' ')
}
