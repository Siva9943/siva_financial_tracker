import apiClient from './client'

export const getChatHistory = () => apiClient.get('/ai/chat/').then((res) => res.data)

export const sendChatMessage = (message) => apiClient.post('/ai/chat/', { message }).then((res) => res.data)
