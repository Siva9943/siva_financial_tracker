// Mirrors Backend/apps/loans/models.py choices — keep in sync.

export const LOAN_TYPES = ['PERSONAL', 'HOME', 'VEHICLE', 'EDUCATION', 'CREDIT_CARD', 'BUSINESS', 'GOLD_LOAN', 'OTHER']

export const INTEREST_METHODS = [
  'DAILY_REDUCING_BALANCE',
  'MONTHLY_REDUCING_BALANCE',
  'EMI_AMORTIZATION',
  'FLAT_RATE',
]

export const PAYMENT_FREQUENCIES = ['WEEKLY', 'BIWEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY']

export const LOAN_STATUSES = ['ACTIVE', 'COMPLETED', 'OVERDUE', 'PAUSED']

export const LOAN_STATUS_STYLES = {
  ACTIVE: 'bg-green-50 text-green-700',
  COMPLETED: 'bg-slate-100 text-slate-700',
  OVERDUE: 'bg-red-50 text-red-700',
  PAUSED: 'bg-amber-50 text-amber-700',
}
