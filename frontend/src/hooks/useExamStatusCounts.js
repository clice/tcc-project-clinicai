/**
 * Hook para contagem de exames por status.
 *
 * Usado tanto pela barra lateral (badges do submenu de Exames, sempre sem
 * filtro) quanto pela listagem/dashboard de exames (que pode aplicar
 * filtros de período, clínica, médico e resultado da IA — RF57).
 *
 * Nota: hoje isso busca a lista completa de exames (já filtrada pelo
 * backend quando aplicável) e conta no cliente. Se o volume de exames
 * crescer muito, vale considerar um endpoint de agregação no backend em
 * vez de trazer a lista inteira só para contar.
 */

import { useCallback, useEffect, useState } from 'react'

import { examService } from 'src/services/examService'

const emptyCounts = {
  pending: 0,
  processing: 0,
  awaiting_review: 0,
  completed: 0,
  completed_with_divergence: 0,
  failed: 0,
  canceled: 0,
}

// Filtros aplicados no cliente (exam_date não é filtrável no backend hoje).
const applyClientSideFilters = (exams, { dateFrom, dateTo } = {}) => {
  if (!dateFrom && !dateTo) return exams

  return exams.filter((exam) => {
    if (!exam.exam_date) return false
    if (dateFrom && exam.exam_date < dateFrom) return false
    if (dateTo && exam.exam_date > dateTo) return false
    return true
  })
}

export const useExamStatusCounts = (filters = {}, enabled = true) => {
  const { clinicId, doctorId, aiPredictionClass, dateFrom, dateTo } = filters

  const [counts, setCounts] = useState(emptyCounts)
  const [isLoading, setIsLoading] = useState(enabled)

  const refresh = useCallback(async () => {
    if (!enabled) {
      // Ao perder exams:read em runtime, não mantenha contagens obtidas
      // enquanto o usuário ainda tinha acesso.
      setCounts({ ...emptyCounts })
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)

      const data = await examService.list({
        includeInactive: true,
        clinicId: clinicId || undefined,
        doctorId: doctorId || undefined,
        aiPredictionClass:
          aiPredictionClass === '' || aiPredictionClass === undefined
            ? undefined
            : Number(aiPredictionClass),
      })

      const exams = applyClientSideFilters(Array.isArray(data) ? data : [], { dateFrom, dateTo })

      const nextCounts = { ...emptyCounts }
      exams.forEach((exam) => {
        if (exam.status_name in nextCounts) {
          nextCounts[exam.status_name] += 1
        }
      })

      setCounts(nextCounts)
    } catch {
      // Falha ao contar não deve quebrar a navegação — os badges só ficam
      // zerados/desatualizados até a próxima atualização bem-sucedida.
    } finally {
      setIsLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, clinicId, doctorId, aiPredictionClass, dateFrom, dateTo])

  useEffect(() => {
    // Agenda fora do corpo síncrono do effect e cancela se as dependências
    // mudarem antes da execução (por exemplo, após refresh de permissões).
    const refreshTimer = window.setTimeout(() => {
      void refresh()
    }, 0)

    return () => window.clearTimeout(refreshTimer)
  }, [refresh])

  return { counts, isLoading, refresh }
}
