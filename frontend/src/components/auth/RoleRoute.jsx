/**
 * Componente de proteção de rota por perfil e/ou permissão.
 *
 * Ele impede que usuários sem a role/permissão necessária acessem
 * páginas restritas, mesmo digitando a URL diretamente no navegador.
 *
 * Duas formas de proteção, escolha conforme o tipo de regra (achado
 * FE-02 de revisão):
 * - `requiredPermission`: para áreas operacionais (pacientes, exames,
 *   clínicas) onde o acesso real depende da matriz de permissões da
 *   role, não do nome da role em si — se um admin remover
 *   "patients:read" do Médico, a rota passa a bloquear sozinha, sem
 *   precisar editar routes.js.
 * - `allowedRoles`: para regras clínicas não-delegáveis (ex: revisão
 *   médica) e para a área de configuração estrutural do sistema (Perfis,
 *   Permissões, Vínculos, Status), que é exclusiva do Administrador
 *   Master por decisão arquitetural, não por permissão dinâmica (ver
 *   nota em `utils/permissions.js`).
 *
 * Se `requiredPermission` for informado, ele tem prioridade — é a
 * checagem mais fiel ao que o backend realmente vai aplicar.
 */

import React from 'react'
import { Navigate } from 'react-router-dom'

import { useAuth } from 'src/hooks/useAuth'
import { getUserRole, hasPermission } from 'src/utils/permissions'

const RoleRoute = ({ children, allowedRoles = [], requiredPermission = null }) => {
  const { user } = useAuth()

  if (requiredPermission) {
    if (!hasPermission(user, requiredPermission)) {
      return <Navigate to="/dashboard" replace />
    }
    return children
  }

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