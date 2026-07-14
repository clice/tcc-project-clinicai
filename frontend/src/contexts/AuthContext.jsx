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

import React, { createContext, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { authService } from 'src/services/authService'
import {
  clearAuthStorage,
  getStoredUser,
  getToken,
  setAuthTokens,
  setStoredUser,
} from 'src/utils/token'
import { getUserRole } from 'src/utils/permissions'
import { ACTIVE_ACCESS_REFRESH_INTERVAL_MS, hasAccessChanged } from 'src/utils/sessionAccess.mjs'

export const AuthContext = createContext(null)

/**
 * Provider global de autenticação.
 */
export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => getToken())
  const [user, setUser] = useState(() => getStoredUser())
  const [loading, setLoading] = useState(true)
  const [accessChangeNotice, setAccessChangeNotice] = useState(null)
  const userRef = useRef(user)

  const isAuthenticated = Boolean(token)

  /**
   * Logout
   */
  const logout = useCallback(async ({ callApi = true } = {}) => {
    try {
      if (callApi && getToken()) {
        await authService.logout()
      }
    } catch {
      // Mesmo se a API falhar, a sessão local precisa ser limpa.
    } finally {
      clearAuthStorage()
      userRef.current = null
      setToken(null)
      setUser(null)
      setAccessChangeNotice(null)
    }
  }, [])

  /**
   * Atualiza usuário e armazenamento, avisando quando a matriz RBAC mudou.
   */
  const persistCurrentUser = useCallback((currentUser, { notifyOnAccessChange = false } = {}) => {
    const previousUser = userRef.current
    const accessChanged = notifyOnAccessChange && hasAccessChanged(previousUser, currentUser)

    userRef.current = currentUser
    setUser(currentUser)
    setStoredUser(currentUser)

    if (accessChanged) {
      setAccessChangeNotice({
        id: Date.now(),
        message:
          'Sua role ou suas permissões foram alteradas. Os menus, rotas e ações disponíveis já foram sincronizados.',
      })
    }

    return currentUser
  }, [])

  /**
   * Carregar usuário atual
   */
  const loadCurrentUser = useCallback(async () => {
    if (!token) {
      clearAuthStorage()
      setUser(null)
      setLoading(false)
      return
    }

    try {
      const currentUser = await authService.getCurrentUser()
      persistCurrentUser(currentUser)
    } catch {
      await logout()
    } finally {
      setLoading(false)
    }
  }, [logout, persistCurrentUser, token])

  /**
   * Recarrega os dados do usuário autenticado sem afetar o loading global.
   * Usado após a edição do próprio perfil (nome, e-mail, telefone etc.),
   * pra refletir a mudança imediatamente no cabeçalho.
   */
  const refreshUser = useCallback(
    async ({ notifyOnAccessChange = false } = {}) => {
      if (!token) return null

      const currentUser = await authService.getCurrentUser()
      return persistCurrentUser(currentUser, { notifyOnAccessChange })
    },
    [persistCurrentUser, token],
  )

  /**
   * Login
   */
  const login = useCallback(
    async (email, password) => {
      const data = await authService.login(email, password)

      setAuthTokens({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
      })

      setToken(data.access_token)

      const currentUser = await authService.getCurrentUser()

      return persistCurrentUser(currentUser)
    },
    [persistCurrentUser],
  )

  const dismissAccessChangeNotice = useCallback(() => {
    setAccessChangeNotice(null)
  }, [])

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadCurrentUser()
    }, 0)

    return () => window.clearTimeout(timeoutId)
  }, [loadCurrentUser])

  useEffect(() => {
    const handleUnauthorized = () => {
      logout({ callApi: false })
    }

    window.addEventListener('clinicai:unauthorized', handleUnauthorized)

    return () => {
      window.removeEventListener('clinicai:unauthorized', handleUnauthorized)
    }
  }, [logout])

  useEffect(() => {
    if (!token) return undefined

    let refreshInProgress = false

    const synchronizeActiveAccess = async () => {
      if (refreshInProgress || document.visibilityState === 'hidden') return

      refreshInProgress = true
      try {
        await refreshUser({ notifyOnAccessChange: true })
      } catch {
        // Falhas transitórias não apagam a sessão. Respostas 401 são tratadas
        // pelo interceptor global e disparam o evento de não autorizado.
      } finally {
        refreshInProgress = false
      }
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        void synchronizeActiveAccess()
      }
    }

    const intervalId = window.setInterval(
      synchronizeActiveAccess,
      ACTIVE_ACCESS_REFRESH_INTERVAL_MS,
    )

    window.addEventListener('focus', synchronizeActiveAccess)
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      window.clearInterval(intervalId)
      window.removeEventListener('focus', synchronizeActiveAccess)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [refreshUser, token])

  const value = useMemo(
    () => ({
      token,
      user,
      roleName: getUserRole(user),
      loading,
      isAuthenticated,
      accessChangeNotice,
      login,
      logout,
      refreshUser,
      dismissAccessChangeNotice,
    }),
    [
      token,
      user,
      loading,
      isAuthenticated,
      accessChangeNotice,
      login,
      logout,
      refreshUser,
      dismissAccessChangeNotice,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
