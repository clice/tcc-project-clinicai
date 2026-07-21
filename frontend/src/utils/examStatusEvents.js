/**
 * Notifica componentes que exibem contagens de exames por status.
 */

export const EXAM_STATUS_COUNTS_INVALIDATED_EVENT = 'clinicai:exam-status-counts-invalidated'

export const EXAM_STATUS_COUNTS_STORAGE_KEY = 'clinicai:exam-status-counts-version'

export const notifyExamStatusCountsChanged = () => {
  if (typeof window === 'undefined') return

  window.dispatchEvent(new Event(EXAM_STATUS_COUNTS_INVALIDATED_EVENT))

  try {
    window.localStorage.setItem(EXAM_STATUS_COUNTS_STORAGE_KEY, `${Date.now()}:${Math.random()}`)
  } catch {
    // A atualização da aba atual continua funcionando sem localStorage.
  }
}
