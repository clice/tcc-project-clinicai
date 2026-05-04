/**
 * Hook para acessar o contexto global de autenticação.
 */

import { useContext } from 'react'
import { AuthContext } from 'src/contexts/AuthContext'

export const useAuth = () => {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider')
  }

  return context
}

export default useAuth
