import apiClient from './client'

export const listGoals = (params) => apiClient.get('/goals/', { params }).then((res) => res.data)

export const createGoal = (payload) => apiClient.post('/goals/', payload).then((res) => res.data)

export const updateGoal = (id, payload) => apiClient.patch(`/goals/${id}/`, payload).then((res) => res.data)

export const deleteGoal = (id) => apiClient.delete(`/goals/${id}/`)

export const listContributions = (id) => apiClient.get(`/goals/${id}/contributions/`).then((res) => res.data)

export const recordContribution = (id, payload) =>
  apiClient.post(`/goals/${id}/contributions/`, payload).then((res) => res.data)
