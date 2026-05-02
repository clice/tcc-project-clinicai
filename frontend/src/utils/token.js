/**
 * Utilitário responsável por controlar autenticação
 * no armazenamento local do navegador.
 *
 * Aqui salvamos:
 * - token JWT
 * - dados do usuário logado
 */

const TOKEN_KEY = import.meta.env.VITE_TOKEN_STORAGE_KEY || 'clinicai_token'
const REFRESH_TOKEN_KEY = import.meta.env.VITE_REFRESH_STORAGE_KEY || 'clinicai_refresh_token'
const USER_KEY = import.meta.env.VITE_USER_STORAGE_KEY || 'clinicai_current_user'

/**
 * Retorna token salvo.
 */
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * Salva token JWT.
 */
export const setToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * Remove token salvo.
 */
export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY)
}

/**
 * Retorna refreshed token salvo.
 */
export const getRefreshToken = () => {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

/**
 * Salva refreshed token JWT.
 */
export const setRefreshToken = (refreshToken) => {
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
}

/**
 * Remove refreshed token salvo.
 */
export const removeRefreshToken = () => {
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

/**
 * Busca usuário salvo no navegador.
 */
export const getStoredUser = () => {
  const rawUser = localStorage.getItem(USER_KEY)

  if (!rawUser) {
    return null
  }

  try {
    return JSON.parse(rawUser)
  } catch {
    removeStoredUser()
    return null
  }
}

/**
 * Salva usuário autenticado.
 */
export const setStoredUser = (user) => {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

/**
 * Remove usuário salvo.
 */
export const removeStoredUser = () => {
  localStorage.removeItem(USER_KEY)
}

/**
 * Configura o token do usuário salvo.
 */
export const setAuthTokens = ({ accessToken, refreshToken }) => {
  setToken(accessToken)

  if (refreshToken) {
    setRefreshToken(refreshToken)
  }
}

/**
 * Limpa toda sessão local.
 * Utilizado no logout ou token inválido.
 */
export const clearAuthStorage = () => {
  removeToken()
  removeRefreshToken()
  removeStoredUser()
}
