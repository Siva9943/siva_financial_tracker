import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

apiClient.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('accessToken')
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

let refreshPromise = null

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error

    if (response?.status !== 401 || config._retry) {
      return Promise.reject(error)
    }

    const refreshToken = localStorage.getItem('refreshToken')
    if (!refreshToken) {
      return Promise.reject(error)
    }

    config._retry = true

    try {
      refreshPromise ??= axios
        .post(`${import.meta.env.VITE_API_URL}/auth/refresh/`, { refresh: refreshToken })
        .finally(() => {
          refreshPromise = null
        })

      const { data } = await refreshPromise
      localStorage.setItem('accessToken', data.access)
      config.headers.Authorization = `Bearer ${data.access}`
      return apiClient(config)
    } catch (refreshError) {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      return Promise.reject(refreshError)
    }
  },
)

export default apiClient
