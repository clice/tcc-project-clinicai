/**
 * Protege páginas por perfil e permissão.
 *
 * Quando uma rota declara as duas restrições, ambas precisam ser atendidas:
 * a role define o perfil autorizado e a permissão confirma a capacidade.
 */

import React from 'react'
import { Navigate } from 'react-router-dom'

import { useAuth } from 'src/hooks/useAuth'
import { getUserRole, hasPermission } from 'src/utils/permissions'

const RoleRoute = ({ children, allowedRoles = [], requiredPermission = null }) => {
  const { user } = useAuth()
  const roleName = getUserRole(user)

  const roleAllowed =
    !allowedRoles ||
    allowedRoles.length === 0 ||
    allowedRoles.includes(roleName)

  if (!roleAllowed) {
    return <Navigate to="/dashboard" replace />
  }

  if (
    requiredPermission &&
    !hasPermission(user, requiredPermission)
  ) {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

export default RoleRoute