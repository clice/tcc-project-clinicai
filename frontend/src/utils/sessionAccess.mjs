/**
 * Utilitários para comparar o acesso recebido pela rota /auth/me.
 *
 * A ordenação impede que uma mudança apenas na ordem das permissões seja
 * interpretada como alteração real da matriz RBAC.
 */

export const ACTIVE_ACCESS_REFRESH_INTERVAL_MS = 60_000

const normalizePermissions = (permissions = []) => {
  return [...new Set(permissions.filter((permission) => typeof permission === 'string'))].sort()
}

export const getAccessSnapshot = (user) => ({
  roleId: user?.role_id ?? null,
  roleName: user?.role_name ?? user?.role?.name ?? user?.role ?? null,
  permissions: normalizePermissions(user?.permissions ?? user?.role_permissions ?? []),
})

export const hasAccessChanged = (previousUser, currentUser) => {
  if (!previousUser || !currentUser) return false

  return (
    JSON.stringify(getAccessSnapshot(previousUser)) !==
    JSON.stringify(getAccessSnapshot(currentUser))
  )
}
