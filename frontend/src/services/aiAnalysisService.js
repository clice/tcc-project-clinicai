/**
 * Serviços do módulo AI Analysis.
 *
 * Centraliza as chamadas HTTP relacionadas às análises de IA vinculadas aos exames.
 */

import api from 'src/services/api'

export const aiAnalysisService = {
  /**
   * Busca a análise de IA vinculada a um exame.
   *
   * Retorna null (em vez de lançar) quando o exame ainda não possui análise
   * vinculada (404) — esse é um estado normal (exame em processamento),
   * não um erro a ser exibido para o usuário.
   */
  getByExamId: async (examId) => {
    try {
      const response = await api.get(`/ai-analyses/exam/${examId}`)
      return response.data
    } catch (err) {
      if (err?.response?.status === 404) {
        return null
      }

      throw err
    }
  },

  /**
   * Métricas agregadas de governança/infraestrutura do módulo de IA —
   * exclusivas do Administrador Master. A rota já é protegida no backend
   * por `require_admin`; qualquer outro perfil recebe 403.
   */
  getMetrics: async () => {
    const response = await api.get('/ai-analyses/metrics')
    return response.data
  },
}
