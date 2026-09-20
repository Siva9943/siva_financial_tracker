import apiClient from './client'

export const listTransactions = (params) =>
  apiClient.get('/transactions/', { params }).then((res) => res.data)

export const createTransaction = (payload) =>
  apiClient.post('/transactions/', payload).then((res) => res.data)

export const updateTransaction = (id, payload) =>
  apiClient.patch(`/transactions/${id}/`, payload).then((res) => res.data)

export const deleteTransaction = (id) => apiClient.delete(`/transactions/${id}/`)

export const getTransactionSummary = (params) =>
  apiClient.get('/transactions/summary/', { params }).then((res) => res.data)
