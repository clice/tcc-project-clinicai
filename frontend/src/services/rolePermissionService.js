/**
 * Serviços da tabela role_permissions.
 *
 * Centraliza as chamadas HTTP relacionadas as role_permissions.
 */

import api from 'src/services/api'

export const rolePermissionService = {
  /**
   * Lista todos os vínculos entre roles e permissions.
   */
  list: async () => {
    const response = await api.get('/role-permissions/')
    return response.data
  },

  /**
   * Lista apenas os vínculos de uma role específica.
   */
  listByRole: async (roleId) => {
    const rolePermissions = await rolePermissionService.list()

    return rolePermissions.filter((item) => Number(item.role_id) === Number(roleId))
  },

  /**
   * Cria um vínculo entre role e permission.
   */
  create: async (roleId, permissionId) => {
    const response = await api.post('/role-permissions/', {
      role_id: Number(roleId),
      permission_id: Number(permissionId),
    })

    return response.data
  },

  /**
   * Remove um vínculo pelo ID da tabela role_permissions.
   */
  remove: async (rolePermissionId) => {
    const response = await api.delete(`/role-permissions/${rolePermissionId}`)
    return response.data
  },

  /**
   * Sincroniza as permissões de uma role.
   */
  syncRolePermissions: async (roleId, selectedPermissionIds) => {
    const currentLinks = await rolePermissionService.listByRole(roleId)

    const currentPermissionIds = currentLinks.map((item) => Number(item.permission_id))
    const selectedIds = selectedPermissionIds.map((id) => Number(id))

    const permissionIdsToAdd = selectedIds.filter((id) => !currentPermissionIds.includes(id))

    const linksToRemove = currentLinks.filter(
      (link) => !selectedIds.includes(Number(link.permission_id)),
    )

    await Promise.all(
      permissionIdsToAdd.map((permissionId) =>
        rolePermissionService.create(roleId, permissionId),
      ),
    )

    await Promise.all(
      linksToRemove.map((link) => rolePermissionService.remove(link.id)),
    )

    return {
      role_id: Number(roleId),
      permission_ids: selectedIds,
    }
  },
}