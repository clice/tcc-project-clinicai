/**
 * Serviços do módulo Exams.
 *
 * Centraliza as chamadas HTTP relacionadas aos exames.
 */

import api from 'src/services/api'

export const examService = {
  /**
  * Lista todos os exames cadastrados.
  */
  list: async (params = {}) => {
    const response = await api.get('/exams/', {
      params: {
        search: params.search || undefined,
        clinic_id: params.clinicId || undefined,
        patient_id: params.patientId || undefined,
        doctor_id: params.doctorId || undefined,
        status_id: params.statusId || undefined,
        include_inactive: params.includeInactive ?? true,
      },
    })

    return response.data
  },

  /**
   * Busca um exame pelo ID.
   */
  getById: async (id) => {
    const response = await api.get(`/exams/${id}`)
    return response.data
  },

  /**
   * Cria um novo exame.
   */
  create: async (payload) => {
    const response = await api.post('/exams/', payload)
    return response.data
  },

  /**
   * Atualiza parcialmente um exame existente.
   */
  update: async (id, payload) => {
    const response = await api.patch(`/exams/${id}`, payload)
    return response.data
  },

  /**
   * Atualiza status para cancelado.
   */
  cancel: async (id) => {
    const response = await api.patch(`/exams/${id}/cancel`)
    return response.data
  },

  /**
   * Atualiza status para restaurado.
   */
  restore: async (id) => {
    const response = await api.patch(`/exams/${id}/restore`)
    return response.data
  },

  /**
   * 
   */
  getFormOptions: async () => {
    const response = await api.get('/exams/form-options')
    return response.data
  },

  /**
   * Permite o upload do arquivo de exame.
   */
  uploadFile: async (id, file) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post(`/exams/${id}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    return response.data
  },

  /**
   * Permite o download do arquivo de exame.
   */
  downloadFile: async (id) => {
    const response = await api.get(`/exams/${id}/download`, {
      responseType: 'blob',
    })

    return response.data
  },
}