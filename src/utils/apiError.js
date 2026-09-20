export function getErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  const data = error?.response?.data

  if (!data) return fallback
  if (data.message) return data.message

  if (data.errors && typeof data.errors === 'object') {
    const firstKey = Object.keys(data.errors)[0]
    const firstValue = data.errors[firstKey]
    return Array.isArray(firstValue) ? firstValue[0] : String(firstValue ?? fallback)
  }

  return fallback
}
