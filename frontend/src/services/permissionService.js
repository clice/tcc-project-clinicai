/**
 * Serviços do módulo Permissions.
 *
 * Centraliza as chamadas HTTP relacionadas as permissions.
 */

import api from 'src/services/api'

export const permissionService = {
  /**
   * Lista de todas as permissões cadastradas.
   */
  list: async () => {
    const response = await api.get('/permissions/')
    return response.data
  },

  /**
   * Busca uma permissão pelo ID
   */
  getById: async (id) => {
    const response = await api.get(`/permissions/${id}`)
    return response.data
  },

  /**
   * Atualiza parcialmente uma permissão existente.
   */
  update: async (id, payload) => {
    const response = await api.patch(`/permissions/${id}`, payload)
    return response.data
  },
}
