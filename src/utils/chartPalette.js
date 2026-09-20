// Reference categorical palette (fixed order — never cycled/reassigned by rank).
// See dataviz skill references/palette.md for the validated ordering.
export const CATEGORICAL_PALETTE = [
  '#2a78d6', // blue
  '#eb6834', // orange
  '#1baf7a', // aqua
  '#eda100', // yellow
  '#e87ba4', // magenta
  '#008300', // green
  '#4a3aa7', // violet
  '#e34948', // red
]

export const CHART_INK = {
  primary: '#0b0b0b',
  secondary: '#52514e',
  muted: '#898781',
  gridline: '#e1e0d9',
}

const MAX_SLOTS = CATEGORICAL_PALETTE.length

// Caps a sorted-by-magnitude breakdown at the palette's fixed slot count,
// folding any remainder into a single "Other" bucket rather than cycling colors.
export function capToPaletteSlots(rows, { labelKey = 'category', valueKey = 'total' } = {}) {
  if (rows.length <= MAX_SLOTS) return rows

  const head = rows.slice(0, MAX_SLOTS - 1)
  const tail = rows.slice(MAX_SLOTS - 1)
  const otherTotal = tail.reduce((sum, row) => sum + Number(row[valueKey]), 0)
  const otherPercentage = tail.reduce((sum, row) => sum + (row.percentage ?? 0), 0)

  return [...head, { [labelKey]: 'Other', [valueKey]: otherTotal, percentage: otherPercentage }]
}
