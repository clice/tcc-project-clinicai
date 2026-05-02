/**
 * Funções utilitárias de mensagens de erro.
 */

/**
 * Mostrar a mensagem de erro.
 */
export const getErrorMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string') return detail

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(' ')
  }

  return error?.message || fallback
}