/**
 * Serviços do módulo Exams.
 *
 * Centraliza as chamadas HTTP relacionadas aos exames.
 */

import api from 'src/services/api'
import { notifyExamStatusCountsChanged } from 'src/utils/examStatusEvents'

const executeExamMutation = async (requestPromise) => {
  try {
    const response = await requestPromise
    return response.data
  } finally {
    notifyExamStatusCountsChanged()
  }
}

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

  formData.append('description', payload.description)

  if (payload.observations) {
    formData.append('observations', payload.observations)
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
        ai_prediction_class:
          params.aiPredictionClass === undefined ? undefined : params.aiPredictionClass,
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
   * Busca os dados autorizados do relatório de impressão.
   */
  getPrintReport: async (id) => {
    const response = await api.get(
      `/exams/${id}/print-report`,
    )

    return response.data
  },

  /**
   * Carrega a imagem original usada no relatório.
   */
  previewPrintOriginalImage: async (id) => {
    const response = await api.get(
      `/exams/${id}/print-report/original-image`,
      {
        responseType: 'blob',
      },
    )

    return response.data
  },

  /**
   * Carrega o Mapa Grad-CAM usado no relatório.
   */
  previewPrintGradcam: async (id) => {
    const response = await api.get(
      `/exams/${id}/print-report/gradcam`,
      {
        responseType: 'blob',
      },
    )

    return response.data
  },

  /**
   * Consulta os eventos e alterações de status do exame (RF36).
   */
  getHistory: async (id) => {
    const response = await api.get(`/exams/${id}/history`)
    return response.data
  },

  /**
   * Cria um novo exame.
   */
  create: async (payload) => {
    const formData = buildExamFormData(payload)

    return executeExamMutation(
      api.post('/exams/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }),
    )
  },

  /**
   * Atualiza parcialmente um exame existente.
   */
  update: async (id, payload) => {
    return executeExamMutation(api.patch(`/exams/${id}`, payload))
  },

  /**
   * Substitui a imagem de um exame pendente.
   */
  replaceFile: async (id, file) => {
    const formData = new FormData()
    formData.append('file', file)

    return executeExamMutation(
      api.post(`/exams/${id}/replace-file`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }),
    )
  },

  /**
   * Atualiza status para cancelado.
   */
  cancel: async (id) => {
    return executeExamMutation(api.patch(`/exams/${id}/cancel`))
  },

  /**
   * Atualiza status para reprocessamento.
   */
  reprocess: async (id) => {
    return executeExamMutation(api.patch(`/exams/${id}/restore`))
  },

  /**
   * Atualiza status para restaurar.
   */
  restore: async (id) => {
    return executeExamMutation(api.patch(`/exams/${id}/restore`))
  },

  /**
   * Dispara a análise de IA. O backend garante claim atômico e idempotência.
   */
  analyze: async (id) => {
    return executeExamMutation(api.post(`/exams/${id}/analyze`))
  },

  /**
   * Registra a revisão médica do resultado da análise de IA.
   *
   * O exame precisa estar em 'awaiting_review'. has_discrepancy=false conclui
   * confirmando a análise da IA (status final 'completed'); has_discrepancy=true
   * conclui sinalizando divergência (status final 'completed_with_divergence').
   * Em ambos os casos o exame é encerrado — não é possível reprocessar a
   * partir daqui (RN10).
   */
  review: async (id, payload) => {
    return executeExamMutation(api.patch(`/exams/${id}/review`, payload))
  },

  /**
   *
   */
  getFormOptions: async () => {
    const response = await api.get('/exams/form-options')
    return response.data
  },

  /**
   * Carrega a imagem original para visualização autenticada.
   */
  previewFile: async (id) => {
    const response = await api.get(`/exams/${id}/preview`, {
      responseType: 'blob',
    })

    return response.data
  },

  /**
   * Permite o download explícito do arquivo de exame.
   */
  downloadFile: async (id) => {
    const response = await api.get(`/exams/${id}/download`, {
      responseType: 'blob',
      params: {
        download_request: Date.now(),
      },
    })

    return response.data
  },

  /**
   * Baixa a imagem original e o Mapa Grad-CAM em um arquivo ZIP.
   */
  downloadImagePackage: async (id) => {
    const response = await api.get(`/exams/${id}/images/download`, {
      responseType: 'blob',
      params: {
        download_request: Date.now(),
      },
    })

    return response.data
  },

  /**
   * Carrega o mapa Grad-CAM para visualização autenticada.
   */
  previewAiFile: async (id) => {
    const response = await api.get(`/exams/${id}/ai-file/preview`, {
      responseType: 'blob',
    })

    return response.data
  },

  /**
   * Gera e baixa o relatório PDF de um exame finalizado.
   */
  downloadPrintReport: async (id) => {
    const response = await api.get(
      `/exams/${id}/print-report.pdf`,
      {
        responseType: 'blob',
        params: {
          download_request: Date.now(),
        },
      },
    )

    return response.data
  },

  /**
   * Baixa explicitamente o mapa Grad-CAM.
   */
  downloadAiFile: async (id) => {
    const response = await api.get(`/exams/${id}/ai-file/download`, {
      responseType: 'blob',
      params: {
        download_request: Date.now(),
      },
    })

    return response.data
  },
}
