/**
 * Contexto global de autenticação do ClinicAI.
 *
 * Responsável por:
 * - armazenar o usuário autenticado;
 * - armazenar o token JWT;
 * - realizar login;
 * - realizar logout;
 * - carregar os dados do usuário atual pela rota /auth/me.
 */

import React, { createContext, useEffect, useMemo, useState } from 'react'
import { authService } from 'src/services/authService'
import {
  clearAuthStorage,
  getStoredUser,
  getToken,
  setAuthTokens,
  setStoredUser,
} from 'src/utils/token'
import { getUserRole } from 'src/utils/permissions'

export const AuthContext = createContext(null)

/**
 * Provider global de autenticação.
 */
export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => getToken())
  const [user, setUser] = useState(() => getStoredUser())
  const [loading, setLoading] = useState(true)

  const isAuthenticated = Boolean(token)

  /**
   * Logout
   */
  const logout = async ({ callApi = true } = {}) => {
    try {
      if (callApi && getToken()) {
        await authService.logout()
      }
    } catch {
      // Mesmo se a API falhar, a sessão local precisa ser limpa.
    } finally {
      clearAuthStorage()
      setToken(null)
      setUser(null)
    }
  }

  /**
   * Carregar usuário atual
   */
  const loadCurrentUser = async () => {
    if (!token) {
      clearAuthStorage()
      setUser(null)
      setLoading(false)
      return
    }

    try {
      const currentUser = await authService.getCurrentUser()

      setUser(currentUser)
      setStoredUser(currentUser)
    } catch {
      logout()
    } finally {
      setLoading(false)
    }
  }

  /**
   * Recarrega os dados do usuário autenticado sem afetar o loading global.
   * Usado após a edição do próprio perfil (nome, e-mail, telefone etc.),
   * pra refletir a mudança imediatamente no cabeçalho.
   */
  const refreshUser = async () => {
    if (!token) return null

    const currentUser = await authService.getCurrentUser()

    setUser(currentUser)
    setStoredUser(currentUser)

    return currentUser
  }

  /**
   * Login
   */
  const login = async (email, password) => {
    const data = await authService.login(email, password)

    setAuthTokens({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
    })

    setToken(data.access_token)

    const currentUser = await authService.getCurrentUser()

    setUser(currentUser)
    setStoredUser(currentUser)

    return currentUser
  }

  useEffect(() => {
    loadCurrentUser()
  }, [token])

  useEffect(() => {
    const handleUnauthorized = () => {
      logout({ callApi: false })
    }

    window.addEventListener('clinicai:unauthorized', handleUnauthorized)

    return () => {
      window.removeEventListener('clinicai:unauthorized', handleUnauthorized)
    }
  }, [])

  const value = useMemo(
    () => ({
      token,
      user,
      roleName: getUserRole(user),
      loading,
      isAuthenticated,
      login,
      logout,
      refreshUser,
    }),
    [token, user, loading, isAuthenticated],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
