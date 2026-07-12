/**
 * Hook para contagem de exames por status.
 *
 * Usado tanto pela barra lateral (badges do submenu de Exames) quanto pela
 * listagem de exames (cards de resumo), para não duplicar a lógica de
 * contagem em dois lugares.
 *
 * Nota: hoje isso busca a lista completa de exames e conta no cliente,
 * seguindo o mesmo padrão que a listagem já usava para os badges das
 * antigas abas. Se o volume de exames crescer muito, vale considerar um
 * endpoint de agregação no backend (`GET /exams/status-counts` ou similar)
 * em vez de trazer a lista inteira só para contar.
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

export const useExamStatusCounts = () => {
  const [counts, setCounts] = useState(emptyCounts)
  const [isLoading, setIsLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      setIsLoading(true)

      const data = await examService.list({ includeInactive: true })
      const exams = Array.isArray(data) ? data : []

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
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return { counts, isLoading, refresh }
}