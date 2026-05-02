/**
 * Serviços do módulo Status.
 *
 * Centraliza as chamadas HTTP relacionadas aos Status.
 */

import api from 'src/services/api'

export const statusService = {
  /**
   * Lista todos os status cadastrados.
   */
  list: async () => {
    const response = await api.get('/statuses/')
    return response.data
  },

  /**
   * Busca um status pelo ID.
   */
  getById: async (id) => {
    const response = await api.get(`/statuses/${id}`)
    return response.data
  },

  /**
   * Cria um novo status.
   */
  create: async (payload) => {
    const response = await api.post('/statuses/', payload)
    return response.data
  },

  /**
   * Atualiza parcialmente um status existente.
   */
  update: async (id, payload) => {
    const response = await api.patch(`/statuses/${id}`, payload)
    return response.data
  },
}