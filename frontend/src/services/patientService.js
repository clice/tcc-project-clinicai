/**
 * Serviços do módulo Patients.
 *
 * Centraliza as chamadas HTTP relacionadas aos pacientes.
 */

import api from 'src/services/api'

export const patientService = {
  /**
   * Lista pacientes.
   */
  list: async ({ includeInactive = true } = {}) => {
    const response = await api.get('/patients/', {
      params: {
        include_inactive: includeInactive,
      },
    })

    return response.data
  },

  /**
   * Busca um paciente pelo ID.
   */
  getById: async (id) => {
    const response = await api.get(`/patients/${id}`)
    return response.data
  },

  /**
   * Cria um novo paciente.
   */
  create: async (payload) => {
    const response = await api.post('/patients/', payload)
    return response.data
  },

  /**
   * Atualiza parcialmente um paciente existente.
   */
  update: async (id, payload) => {
    const response = await api.patch(`/patients/${id}`, payload)
    return response.data
  },

  /**
   * Inativa um paciente.
   */
  inactivate: async (id) => {
    const response = await api.patch(`/patients/${id}/inactivate`)
    return response.data
  },

  /**
   * Ativa um paciente.
   */
  activate: async (id) => {
    const response = await api.patch(`/patients/${id}/activate`)
    return response.data
  },
}