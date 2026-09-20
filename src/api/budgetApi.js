import apiClient from './client'

export const listBudgets = (params) => apiClient.get('/budgets/', { params }).then((res) => res.data)

export const createBudget = (payload) => apiClient.post('/budgets/', payload).then((res) => res.data)

export const updateBudget = (id, payload) => apiClient.patch(`/budgets/${id}/`, payload).then((res) => res.data)

export const deleteBudget = (id) => apiClient.delete(`/budgets/${id}/`)
