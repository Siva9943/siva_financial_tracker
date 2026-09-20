import apiClient from './client'

export const listReminders = (params) => apiClient.get('/reminders/', { params }).then((res) => res.data)

export const createReminder = (payload) => apiClient.post('/reminders/', payload).then((res) => res.data)

export const deleteReminder = (id) => apiClient.delete(`/reminders/${id}/`)

export const snoozeReminder = (id, snoozedUntil) =>
  apiClient.post(`/reminders/${id}/snooze/`, { snoozed_until: snoozedUntil }).then((res) => res.data)

export const completeReminder = (id) => apiClient.post(`/reminders/${id}/complete/`).then((res) => res.data)

export const listNotifications = (params) => apiClient.get('/notifications/', { params }).then((res) => res.data)

export const markNotificationRead = (id) => apiClient.post(`/notifications/${id}/mark_read/`).then((res) => res.data)

export const markAllNotificationsRead = () => apiClient.post('/notifications/mark_all_read/').then((res) => res.data)

export const getUnreadNotificationCount = () =>
  apiClient.get('/notifications/unread_count/').then((res) => res.data)
