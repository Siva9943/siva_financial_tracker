import apiClient from './client'

export const listInvestments = (params) => apiClient.get('/investments/', { params }).then((res) => res.data)

export const getInvestment = (id) => apiClient.get(`/investments/${id}/`).then((res) => res.data)

export const createInvestment = (payload) => apiClient.post('/investments/', payload).then((res) => res.data)

export const updateInvestment = (id, payload) => apiClient.patch(`/investments/${id}/`, payload).then((res) => res.data)

export const deleteInvestment = (id) => apiClient.delete(`/investments/${id}/`)

export const listInvestmentTransactions = (id, params) =>
  apiClient.get(`/investments/${id}/transactions/`, { params }).then((res) => res.data)

export const recordInvestmentTransaction = (id, payload) =>
  apiClient.post(`/investments/${id}/transactions/`, payload).then((res) => res.data)

export const getInvestmentPerformance = (id) => apiClient.get(`/investments/${id}/performance/`).then((res) => res.data)

export const getPortfolio = () => apiClient.get('/investments/portfolio/').then((res) => res.data)

export const getAllocation = (groupBy = 'type') =>
  apiClient.get('/investments/allocation/', { params: { group_by: groupBy } }).then((res) => res.data)

export const getInvestmentAnalytics = (period) =>
  apiClient.get('/investments/analytics/', { params: { period } }).then((res) => res.data)

export const getContributionTrend = (period) =>
  apiClient.get('/investments/contributions/', { params: { period } }).then((res) => res.data)

export const getPortfolioSnapshots = (range = 'ALL') =>
  apiClient.get('/investments/snapshots/', { params: { range } }).then((res) => res.data)

export const listDividends = () => apiClient.get('/investments/dividends/').then((res) => res.data)
