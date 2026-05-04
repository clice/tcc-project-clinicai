/**
 * Serviços do módulo de Audit Logs.
 *
 * Centraliza as chamadas HTTP relacionadas aos logs de auditoria.
 * A criação dos logs acontece automaticamente no backend.
 */

import api from 'src/services/api'

export const auditLogService = {
  /**
   * Lista todos logs cadastrados.
   */
  list: async ({ clinicId = '', userId = '', entity = '', action = '' } = {}) => {
    const response = await api.get('/audit-logs/', {
      params: {
        clinic_id: clinicId || undefined,
        user_id: userId || undefined,
        entity: entity || undefined,
        action: action || undefined,
      },
    })

    return Array.isArray(response.data) ? response.data : []
  },
}
