/**
 * Rota privada.
 *
 * Permite acesso apenas para usuários autenticados.
 */

import React from 'react'
import { Navigate } from 'react-router-dom'
import { CSpinner } from '@coreui/react'
import { useAuth } from 'src/hooks/useAuth'

const PrivateRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center min-vh-100">
        <CSpinner color="success" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}

export default PrivateRoute
