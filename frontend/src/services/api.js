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

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error)
      return
    }

    promise.resolve(token)
  })

  failedQueue = []
}

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

    if (!error.response) {
      return Promise.reject(error)
    }

    const status = error.response.status

    const isAuthRoute =
      originalRequest?.url?.includes('/auth/login') ||
      originalRequest?.url?.includes('/auth/refresh') ||
      originalRequest?.url?.includes('/auth/logout')

    if (isAuthRoute) {
      return Promise.reject(error)
    }

    if (status !== 401 || originalRequest?._retry) {
      return Promise.reject(error)
    }

    const refreshToken = getRefreshToken()

    if (!refreshToken) {
      clearAuthStorage()
      window.dispatchEvent(new Event('clinicai:unauthorized'))
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      })
        .then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
        .catch((err) => Promise.reject(err))
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      const response = await axios.post(`${API_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      })

      const accessToken = response.data?.access_token
      const newRefreshToken = response.data?.refresh_token || refreshToken

      if (!accessToken) {
        throw new Error('Token de acesso não retornado.')
      }

      setAuthTokens({
        accessToken,
        refreshToken: newRefreshToken,
      })

      processQueue(null, accessToken)

      originalRequest.headers.Authorization = `Bearer ${accessToken}`

      return api(originalRequest)
    } catch (refreshError) {
      processQueue(refreshError, null)
      clearAuthStorage()
      window.dispatchEvent(new Event('clinicai:unauthorized'))

      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)

export default api

