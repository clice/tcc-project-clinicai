/**
 * Serviços do módulo Exams.
 *
 * Centraliza as chamadas HTTP relacionadas aos exames.
 */

import api from 'src/services/api'

const buildExamFormData = (payload) => {
  const formData = new FormData()

  formData.append('clinic_id', payload.clinic_id)
  formData.append('patient_id', payload.patient_id)

  if (payload.doctor_id) {
    formData.append('doctor_id', payload.doctor_id)
  }

  formData.append('exam_type', payload.exam_type)

  if (payload.exam_date) {
    formData.append('exam_date', payload.exam_date)
  }

  formData.append('title', payload.title)

  if (payload.description) {
    formData.append('description', payload.description)
  }

  if (payload.clinical_indication) {
    formData.append('clinical_indication', payload.clinical_indication)
  }

  formData.append('file', payload.file)

  return formData
}

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
    const formData = buildExamFormData(payload)

    const response = await api.post('/exams/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

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
   * Atualiza status para reprocessamento.
   */
  reprocess: async (id) => {
    const response = await api.patch(`/exams/${id}/restore`)
    return response.data
  },

  /**
   * Atualiza status para restaurar.
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
   * Permite o download do arquivo de exame.
   */
  downloadFile: async (id) => {
    const response = await api.get(`/exams/${id}/download`, {
      responseType: 'blob',
    })

    return response.data
  },

  /**
   * Permite fazer o download dos arquivos.
   */
  downloadAiFile: async (id) => {
    const response = await api.get(`/exams/${id}/ai-file/download`, {
      responseType: 'blob',
    })

    return response.data
  },
}