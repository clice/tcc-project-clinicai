/**
 * Contexto global de feedback da aplicação.
 *
 * Centraliza:
 * - toasts de sucesso/erro/aviso;
 * - loading global;
 * - mensagens seguras para o usuário.
 */

import React, { createContext, useCallback, useMemo, useState } from 'react'
import {
  CSpinner,
  CToast,
  CToastBody,
  CToastClose,
  CToaster,
} from '@coreui/react'

const FeedbackContext = createContext(null)

export const FeedbackProvider = ({ children }) => {
  const [toasts, setToasts] = useState([])
  const [loadingCount, setLoadingCount] = useState(0)

  const isLoading = loadingCount > 0

  const removeToast = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const showToast = useCallback(
    ({ color = 'primary', message, title = '' }) => {
      if (!message) return

      const id = `${Date.now()}-${Math.random()}`

      setToasts((current) => [
        ...current,
        {
          id,
          color,
          message,
          title,
        },
      ])

      window.setTimeout(() => {
        removeToast(id)
      }, 5000)
    },
    [removeToast],
  )

  const showSuccess = useCallback(
    (message) => showToast({ color: 'success', message, title: 'Sucesso' }),
    [showToast],
  )

  const showError = useCallback(
    (message) => showToast({ color: 'danger', message, title: 'Erro' }),
    [showToast],
  )

  const showWarning = useCallback(
    (message) => showToast({ color: 'warning', message, title: 'Atenção' }),
    [showToast],
  )

  const startLoading = useCallback(() => {
    setLoadingCount((current) => current + 1)
  }, [])

  const stopLoading = useCallback(() => {
    setLoadingCount((current) => Math.max(0, current - 1))
  }, [])

  const value = useMemo(
    () => ({
      isLoading,
      showToast,
      showSuccess,
      showError,
      showWarning,
      startLoading,
      stopLoading,
    }),
    [isLoading, showToast, showSuccess, showError, showWarning, startLoading, stopLoading],
  )

  return (
    <FeedbackContext.Provider value={value}>
      {children}

      {isLoading && (
        <div
          className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
          style={{
            zIndex: 2000,
            backgroundColor: 'rgba(255, 255, 255, 0.45)',
            backdropFilter: 'blur(1px)',
          }}
        >
          <div className="bg-body rounded shadow-sm px-4 py-3 d-flex align-items-center gap-3">
            <CSpinner size="sm" />
            <span className="text-body-secondary">Carregando...</span>
          </div>
        </div>
      )}

      <CToaster placement="top-end" className="p-3" style={{ zIndex: 2100 }}>
        {toasts.map((toast) => (
          <CToast
            key={toast.id}
            visible
            autohide
            delay={5000}
            color={toast.color}
            className="text-white"
          >
            <div className="d-flex">
              <CToastBody>
                {toast.title && <strong className="d-block mb-1">{toast.title}</strong>}
                {toast.message}
              </CToastBody>
              <CToastClose
                className="me-2 m-auto"
                white
                onClick={() => removeToast(toast.id)}
              />
            </div>
          </CToast>
        ))}
      </CToaster>
    </FeedbackContext.Provider>
  )
}

export default FeedbackContext
