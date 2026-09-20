const currencyFormatters = new Map()

export function formatCurrency(amount, currency = 'INR') {
  if (!currencyFormatters.has(currency)) {
    currencyFormatters.set(
      currency,
      new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 2 }),
    )
  }
  return currencyFormatters.get(currency).format(Number(amount))
}

export function formatDate(isoDate) {
  if (!isoDate) return ''
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export function formatDateTime(isoDateTime) {
  if (!isoDateTime) return ''
  return new Date(isoDateTime).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}
