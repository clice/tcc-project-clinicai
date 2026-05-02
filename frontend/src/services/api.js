/**
 * Cliente principal HTTP da aplicação.
 *
 * Centraliza:
 * - URL base da API
 * - envio automático do token JWT
 * - renovação automática com refresh token
 */

import axios from 'axios'
import {
  clearAuthStorage,
  getRefreshToken,
  getToken,
  setAuthTokens,
} from 'src/utils/token'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Instância única do Axios.
 */
const api = axios.create({
  baseURL: API_URL,
})

/**
 * Interceptor executado antes de cada request.
 *
 * Se existir access token salvo, adiciona Authorization Bearer.
 */
api.interceptors.request.use((config) => {
  const token = getToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

/**
 * Interceptor global de resposta.
 *
 * Se a API retornar 401:
 * - tenta renovar o access token usando refresh token
 * - repete a requisição original
 * - se falhar, limpa sessão e redireciona para login
 */
api.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status

    const isUnauthorized = status === 401
    const alreadyRetried = originalRequest?._retry
    const isRefreshRoute = originalRequest?.url?.includes('/auth/refresh')

    if (!isUnauthorized || alreadyRetried || isRefreshRoute) {
      return Promise.reject(error)
    }

    originalRequest._retry = true

    try {
      const refreshToken = getRefreshToken()

      if (!refreshToken) {
        throw new Error('Refresh token não encontrado.')
      }

      const response = await axios.post(`${API_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      })

      setAuthTokens({
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
      })

      originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`

      return api(originalRequest)
    } catch (refreshError) {
      clearAuthStorage()

      if (!window.location.hash.includes('/login')) {
        window.location.hash = '#/login'
      }

      return Promise.reject(refreshError)
    }
  },
)

export default api
