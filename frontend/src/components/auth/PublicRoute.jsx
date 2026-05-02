/**
 * Rota pública.
 *
 * Usada para páginas como login.
 * Se o usuário já estiver autenticado, redireciona para o dashboard.
 */

import React from 'react'
import { Navigate } from 'react-router-dom'
import { CSpinner } from '@coreui/react'
import { useAuth } from 'src/hooks/useAuth'

const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center min-vh-100">
        <CSpinner color="success" />
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

export default PublicRoute
