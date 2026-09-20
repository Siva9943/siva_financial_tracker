import apiClient from './client'

export const listIncome = (params) => apiClient.get('/income/', { params }).then((res) => res.data)

export const createIncome = (payload) => apiClient.post('/income/', payload).then((res) => res.data)

export const updateIncome = (id, payload) => apiClient.patch(`/income/${id}/`, payload).then((res) => res.data)

export const deleteIncome = (id) => apiClient.delete(`/income/${id}/`)

export const getIncomeSummary = (params) => apiClient.get('/income/summary/', { params }).then((res) => res.data)
