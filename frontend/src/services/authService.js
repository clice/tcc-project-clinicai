/**
 * Serviço de autenticação.
 *
 * Centraliza as chamadas HTTP relacionadas a login,
 * refresh token e usuário autenticado.
 */

import api from 'src/services/api'

export const authService = {
  /**
   * Login
   */
  async login(email, password) {
    const formData = new URLSearchParams()

    formData.append('username', email)
    formData.append('password', password)

    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    return response.data
  },

  /**
   * Refresh token
   */
  async refreshToken(refreshToken) {
    const response = await api.post('/auth/refresh', {
      refresh_token: refreshToken,
    })

    return response.data
  },

  /**
   * Logout
   */
  async logout() {
    const response = await api.post('/auth/logout')
    return response.data
  },

  /**
   * Retorna usuário atual
   */
  async getCurrentUser() {
    const response = await api.get('/auth/me')

    return response.data
  },
}
