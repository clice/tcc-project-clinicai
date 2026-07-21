/**
 * Hook para contagem de exames por status.
 *
 * Atualiza ao montar, mudar filtros, concluir mutações de exames, retornar
 * para a aba e a cada 30 segundos enquanto a página estiver visível.
 */

import { useCallback, useEffect, useState } from 'react'

import { examService } from 'src/services/examService'
import {
  EXAM_STATUS_COUNTS_INVALIDATED_EVENT,
  EXAM_STATUS_COUNTS_STORAGE_KEY,
} from 'src/utils/examStatusEvents'

const REFRESH_INTERVAL_MS = 30_000

const emptyCounts = {
  pending: 0,
  processing: 0,
  awaiting_review: 0,
  completed: 0,
  completed_with_divergence: 0,
  failed: 0,
  canceled: 0,
}

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

  const refresh = useCallback(
    async ({ silent = false } = {}) => {
      if (!enabled) {
        setCounts({ ...emptyCounts })
        setIsLoading(false)
        return
      }

      try {
        if (!silent) setIsLoading(true)

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
        // Preserva a última contagem válida.
      } finally {
        if (!silent) setIsLoading(false)
      }
    },
    [enabled, clinicId, doctorId, aiPredictionClass, dateFrom, dateTo],
  )

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refresh()
    }, 0)

    return () => window.clearTimeout(timer)
  }, [refresh])

  useEffect(() => {
    if (!enabled) return undefined

    const refreshSilently = () => {
      void refresh({ silent: true })
    }

    const handleStorage = (event) => {
      if (event.key === EXAM_STATUS_COUNTS_STORAGE_KEY) {
        refreshSilently()
      }
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        refreshSilently()
      }
    }

    window.addEventListener(EXAM_STATUS_COUNTS_INVALIDATED_EVENT, refreshSilently)
    window.addEventListener('storage', handleStorage)
    window.addEventListener('focus', refreshSilently)
    document.addEventListener('visibilitychange', handleVisibilityChange)

    const intervalId = window.setInterval(() => {
      if (document.visibilityState === 'visible') {
        refreshSilently()
      }
    }, REFRESH_INTERVAL_MS)

    return () => {
      window.removeEventListener(EXAM_STATUS_COUNTS_INVALIDATED_EVENT, refreshSilently)
      window.removeEventListener('storage', handleStorage)
      window.removeEventListener('focus', refreshSilently)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.clearInterval(intervalId)
    }
  }, [enabled, refresh])

  return { counts, isLoading, refresh }
}
