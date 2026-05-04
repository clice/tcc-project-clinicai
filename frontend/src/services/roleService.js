/**
 * Serviços do módulo Roles.
 *
 * Centraliza as chamadas HTTP relacionadas aos roles.
 */

import api from 'src/services/api'

export const roleService = {
  /**
   * Lista todos os perfis cadastrados.
   */
  list: async () => {
    const response = await api.get('/roles/')
    return response.data
  },

  /**
   * Busca um perfil pelo ID.
   */
  getById: async (id) => {
    const response = await api.get(`/roles/${id}`)
    return response.data
  },

  /**
   * Cria um novo perfil.
   */
  create: async (payload) => {
    const response = await api.post('/roles/', payload)
    return response.data
  },

  /**
   * Atualiza parcialmente um perfil existente.
   */
  update: async (id, payload) => {
    const response = await api.patch(`/roles/${id}`, payload)
    return response.data
  },
}
