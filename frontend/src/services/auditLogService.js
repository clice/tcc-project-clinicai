/**
 * Serviços do módulo de Audit Logs.
 *
 * Centraliza as chamadas HTTP relacionadas aos logs de auditoria.
 * A criação dos logs acontece automaticamente no backend.
 */

import api from 'src/services/api'

export const auditLogService = {
  /**
   * Lista logs cadastrados, paginado.
   * Retorna { items, total, limit, offset }.
   */
  list: async ({
    clinicId = '',
    userId = '',
    entity = '',
    action = '',
    limit = 50,
    offset = 0,
  } = {}) => {
    const response = await api.get('/audit-logs/', {
      params: {
        clinic_id: clinicId || undefined,
        user_id: userId || undefined,
        entity: entity || undefined,
        action: action || undefined,
        limit,
        offset,
      },
    })

    const data = response.data

    if (Array.isArray(data)) {
      // Compatibilidade defensiva, caso a API antiga (sem paginação) responda.
      return { items: data, total: data.length, limit, offset }
    }

    return {
      items: Array.isArray(data?.items) ? data.items : [],
      total: data?.total ?? 0,
      limit: data?.limit ?? limit,
      offset: data?.offset ?? offset,
    }
  },
}
