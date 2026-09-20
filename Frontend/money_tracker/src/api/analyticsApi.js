import apiClient from './client'

export const getDashboard = (params) => apiClient.get('/dashboard/', { params }).then((res) => res.data)

export const getAnalytics = (params) => apiClient.get('/analytics/', { params }).then((res) => res.data)
