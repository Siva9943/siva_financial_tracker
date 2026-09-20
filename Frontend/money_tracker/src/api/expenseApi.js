import apiClient from './client'

export const listExpenses = (params) => apiClient.get('/expenses/', { params }).then((res) => res.data)

export const createExpense = (payload) => apiClient.post('/expenses/', payload).then((res) => res.data)

export const updateExpense = (id, payload) => apiClient.patch(`/expenses/${id}/`, payload).then((res) => res.data)

export const deleteExpense = (id) => apiClient.delete(`/expenses/${id}/`)

export const getExpenseSummary = (params) => apiClient.get('/expenses/summary/', { params }).then((res) => res.data)
