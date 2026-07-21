/**
 * Serviços do módulo Clinics.
 *
 * Centraliza as chamadas HTTP relacionadas às clínicas.
 */

import api from 'src/services/api'

export const clinicService = {
  /**
   * Busca a clínica vinculada ao usuário autenticado.
   */
  getMyClinic: async () => {
    const response = await api.get('/clinics/me')
    return response.data
  },

  /**
   * Atualiza os dados cadastrais da própria clínica.
   * O status só pode ser alterado pelo administrador nas rotas dedicadas.
   */
  updateMyClinic: async (payload) => {
    const response = await api.patch('/clinics/me', payload)
    return response.data
  },
  /**
   * Lista todas as clínicas cadastradas.
   */
  list: async ({ search = '', includeInactive = true } = {}) => {
    const response = await api.get('/clinics/', {
      params: {
        search: search || undefined,
        include_inactive: includeInactive,
      },
    })

    return response.data
  },

  /**
   * Busca uma clínica pelo ID.
   */
  getById: async (id) => {
    const response = await api.get(`/clinics/${id}`)
    return response.data
  },

  /**
   * Cria uma nova clínica.
   */
  create: async (payload) => {
    const response = await api.post('/clinics/', payload)
    return response.data
  },

  /**
   * Atualiza parcialmente uma clínica existente.
   */
  update: async (id, payload) => {
    const response = await api.patch(`/clinics/${id}`, payload)
    return response.data
  },

  /**
   * Inativa uma clínica sem remover do banco.
   */
  inactivate: async (id) => {
    const response = await api.patch(`/clinics/${id}/inactivate`)
    return response.data
  },

  /**
   * Reativa uma clínica inativa.
   */
  activate: async (id) => {
    const response = await api.patch(`/clinics/${id}/activate`)
    return response.data
  },
}
