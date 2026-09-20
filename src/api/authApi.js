import apiClient from './client'

export const register = (payload) => apiClient.post('/auth/register/', payload).then((res) => res.data)

export const login = (payload) => apiClient.post('/auth/login/', payload).then((res) => res.data)

export const logout = (refresh) => apiClient.post('/auth/logout/', { refresh }).then((res) => res.data)

export const getMe = () => apiClient.get('/auth/me/').then((res) => res.data)

export const updateMe = (payload) => apiClient.patch('/auth/me/', payload).then((res) => res.data)

export const changePassword = (payload) =>
  apiClient.post('/auth/change-password/', payload).then((res) => res.data)
