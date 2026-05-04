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
  list: async ({
    search = '',
    clinicId = '',
    patientId = '',
    doctorId = '',
    statusId = '',
    includeInactive = true,
  } = {}) => {
    const response = await api.get('/exams/', {
      params: {
        search: search || undefined,
        clinic_id: clinicId || undefined,
        patient_id: patientId || undefined,
        doctor_id: doctorId || undefined,
        status_id: statusId || undefined,
        include_inactive: includeInactive,
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

  cancel: async (id) => {
    const response = await api.patch(`/exams/${id}/cancel`)
    return response.data
  },

  getFormOptions: async () => {
    const response = await api.get('/exams/form-options')
    return response.data
  },

  uploadFileMetadata: async (id, payload) => {
    const response = await api.post(`/exams/${id}/upload-file`, null, {
      params: {
        file_path: payload.file_path,
        file_name: payload.file_name,
        file_mime_type: payload.file_mime_type,
      },
    })

    return response.data
  },

  downloadFileMetadata: async (id) => {
    const response = await api.get(`/exams/${id}/download-file`)
    return response.data
  },
}