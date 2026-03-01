import axios from 'axios'
import { initData } from '@telegram-apps/sdk-vue'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor — attach Telegram initData as auth header
apiClient.interceptors.request.use(
  (config) => {
    try {
      const raw = initData.raw()
      if (raw) {
        config.headers['Authorization'] = `tma ${raw}`
      }
    } catch {
      // initData not available in dev without mock
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Response interceptor — centralized error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('Auth failed — initData expired or invalid')
    }
    if (error.response?.status >= 500) {
      console.error('Server error:', error.response?.data)
    }
    return Promise.reject(error)
  },
)

export default apiClient
