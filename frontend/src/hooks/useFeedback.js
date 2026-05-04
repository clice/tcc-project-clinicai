/**
 * Hook para acessar feedback global.
 */

import { useContext } from 'react'

import FeedbackContext from 'src/contexts/FeedbackContext'

export const useFeedback = () => {
  const context = useContext(FeedbackContext)

  if (!context) {
    throw new Error('useFeedback deve ser usado dentro de FeedbackProvider.')
  }

  return context
}
