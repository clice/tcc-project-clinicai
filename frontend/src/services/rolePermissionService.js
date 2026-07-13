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
   * Sincroniza as permissões de uma role, em uma única chamada
   * transacional no backend.
   *
   * Antes, isso disparava vários POST/DELETE em paralelo (Promise.all)
   * sem nenhuma transação — uma falha no meio deixava parte das
   * permissões aplicada e parte não, e como as adições aconteciam antes
   * das remoções, existia uma janela real em que a role tinha mais
   * permissões do que deveria. O backend agora calcula a diferença e
   * aplica tudo de uma vez, com rollback integral em caso de erro.
   */
  syncRolePermissions: async (roleId, selectedPermissionIds) => {
    const response = await api.put(`/role-permissions/roles/${roleId}`, {
      permission_ids: selectedPermissionIds.map((id) => Number(id)),
    })

    return {
      role_id: Number(roleId),
      permission_ids: selectedPermissionIds.map((id) => Number(id)),
      role_permissions: response.data,
    }
  },
}
