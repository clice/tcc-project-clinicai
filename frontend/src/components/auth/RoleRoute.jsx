/**
 * Componente de proteção de rota por perfil.
 *
 * Ele impede que usuários sem a role necessária acessem páginas restritas,
 * mesmo digitando a URL diretamente no navegador.
 */

import React from 'react'
import { Navigate } from 'react-router-dom'

import { useAuth } from 'src/hooks/useAuth'
import { getUserRole } from 'src/utils/permissions'

/**
 * Protege rota por perfil
 */
const RoleRoute = ({ children, allowedRoles = [] }) => {
  const { user } = useAuth()

  if (!allowedRoles || allowedRoles.length === 0) {
    return children
  }

  const roleName = getUserRole(user)

  if (!allowedRoles.includes(roleName)) {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

export default RoleRoute
