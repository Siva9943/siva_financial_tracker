// Mirrors Backend/apps/investments/models.py choices — keep in sync.

export const INVESTMENT_TYPES = ['STOCK', 'MUTUAL_FUND', 'ETF', 'BOND', 'FIXED_DEPOSIT', 'GOLD', 'CRYPTO', 'REAL_ESTATE', 'OTHER']

export const INVESTMENT_STATUSES = ['ACTIVE', 'ON_HOLD', 'CLOSED']

export const INVESTMENT_STATUS_STYLES = {
  ACTIVE: 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  ON_HOLD: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  CLOSED: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
}

export const INVESTMENT_TRANSACTION_TYPES = ['BUY', 'SELL', 'DIVIDEND', 'BONUS', 'SPLIT', 'FEE', 'DEPOSIT', 'WITHDRAWAL']

// Types where the form should collect quantity + price (the service computes amount itself).
export const QUANTITY_PRICE_TRANSACTION_TYPES = ['BUY', 'SELL']

// Types where the form should collect quantity only (no price/amount — free shares).
export const QUANTITY_ONLY_TRANSACTION_TYPES = ['BONUS', 'SPLIT']

// Types where the form should collect amount only (no quantity/price).
export const AMOUNT_ONLY_TRANSACTION_TYPES = ['DIVIDEND', 'DEPOSIT', 'WITHDRAWAL']

// FEE collects fees/tax only — handled separately in the form.

export const PORTFOLIO_RANGES = ['1D', '1W', '1M', '3M', '6M', '1Y', '3Y', '5Y', 'ALL']

export const ANALYTICS_PERIODS = ['day', 'week', 'month', 'year']
