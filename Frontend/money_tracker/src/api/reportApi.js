import apiClient from './client'

export const getReportPreview = (type, params) =>
  apiClient.get(`/reports/${type}/`, { params }).then((res) => res.data.report)

export const downloadReport = async (type, params, exportFormat) => {
  let response
  try {
    response = await apiClient.get(`/reports/${type}/`, {
      params: { ...params, export: exportFormat },
      responseType: 'blob',
    })
  } catch (error) {
    // With responseType: 'blob', an error body arrives as a Blob too — parse it back to JSON
    // so getErrorMessage() can read it the same way it does for every other request.
    if (error.response?.data instanceof Blob) {
      const text = await error.response.data.text()
      try {
        error.response.data = JSON.parse(text)
      } catch {
        // leave as-is if the body wasn't JSON
      }
    }
    throw error
  }

  const disposition = response.headers['content-disposition']
  const match = disposition && disposition.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : `report.${exportFormat}`

  const url = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
