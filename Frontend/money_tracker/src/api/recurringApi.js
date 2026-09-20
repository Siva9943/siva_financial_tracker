import apiClient from './client'

export const listRecurring = (params) =>
  apiClient.get('/recurring-transactions/', { params }).then((res) => res.data)

export const createRecurring = (payload) =>
  apiClient.post('/recurring-transactions/', payload).then((res) => res.data)

export const updateRecurring = (id, payload) =>
  apiClient.patch(`/recurring-transactions/${id}/`, payload).then((res) => res.data)

export const deleteRecurring = (id) => apiClient.delete(`/recurring-transactions/${id}/`)

export const generateDueRecurring = () =>
  apiClient.post('/recurring-transactions/generate_due/').then((res) => res.data)
