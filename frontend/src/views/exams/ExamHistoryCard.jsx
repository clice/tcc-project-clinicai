/** Histórico de eventos e alterações de status de um exame (RF36). */

import React, { useEffect, useRef, useState } from 'react'
import {
  CAlert,
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CSpinner,
} from '@coreui/react'

import { examService } from 'src/services/examService'
import { getErrorMessage } from 'src/utils/errors'

const actionLabels = {
  create: 'Cadastro',
  update: 'Atualização',
  cancel_exam: 'Cancelamento',
  restore_exam: 'Restauração',
  review_exam: 'Revisão médica',
  upload: 'Upload',
  download: 'Download',
  run_ai_analysis: 'Análise por IA',
  ai_analysis_failed: 'Falha da IA',
}

const statusLabels = {
  pending: 'Pendente',
  processing: 'Processando',
  awaiting_review: 'Aguardando revisão',
  completed: 'Concluído',
  completed_with_divergence: 'Concluído com divergência',
  failed: 'Falha',
  canceled: 'Cancelado',
}

const formatStatusChange = (entry) => {
  const previousStatus = entry.old_data?.status_name
  const nextStatus = entry.new_data?.status_name

  if (!previousStatus && !nextStatus) return null

  if (previousStatus && nextStatus && previousStatus !== nextStatus) {
    return `${statusLabels[previousStatus] || previousStatus} → ${statusLabels[nextStatus] || nextStatus}`
  }

  const status = nextStatus || previousStatus
  return statusLabels[status] || status
}

const ExamHistoryCard = ({
  examId,
  refreshKey = 0,
  collapsible = false,
  defaultOpen = true,
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const [entries, setEntries] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const hasLoadedOnce = useRef(false)
  const isContentOpen = !collapsible || isOpen

  useEffect(() => {
    if (!isContentOpen) return undefined

    let isCancelled = false

    const loadHistory = async () => {
      const isInitialLoad = !hasLoadedOnce.current

      try {
        if (isInitialLoad) setIsLoading(true)
        setError('')

        const history = await examService.getHistory(examId)

        if (!isCancelled) {
          setEntries(Array.isArray(history?.items) ? history.items : [])
        }
      } catch (err) {
        if (!isCancelled && isInitialLoad) {
          setError(getErrorMessage(err, 'Não foi possível carregar o histórico do exame.'))
        }
      } finally {
        if (!isCancelled) {
          hasLoadedOnce.current = true
          if (isInitialLoad) setIsLoading(false)
        }
      }
    }

    void loadHistory()

    return () => {
      isCancelled = true
    }
  }, [examId, isContentOpen, refreshKey])

  return (
    <CCard className="mt-4 mb-4">
      <CCardHeader className="d-flex justify-content-between align-items-center gap-2">
        <strong>Histórico do Exame</strong>

        {collapsible && (
          <CButton
            color="secondary"
            variant="outline"
            size="sm"
            type="button"
            aria-expanded={isOpen}
            onClick={() =>
              setIsOpen((current) => !current)
            }
          >
            {isOpen ? 'Recolher' : 'Expandir'}
          </CButton>
        )}
      </CCardHeader>

      {isContentOpen && (
        <CCardBody>
        {isLoading ? (
          <div className="d-flex align-items-center gap-2 text-body-secondary">
            <CSpinner size="sm" />
            <span>Carregando histórico...</span>
          </div>
        ) : error ? (
          <CAlert color="danger" className="mb-0">
            {error}
          </CAlert>
        ) : entries.length === 0 ? (
          <div className="text-body-secondary">Nenhum evento registrado para este exame.</div>
        ) : (
          <div className="d-grid gap-3">
            {entries.map((entry, index) => {
              const statusChange = formatStatusChange(entry)

              return (
                <div
                  key={entry.id}
                  className={index === entries.length - 1 ? '' : 'border-bottom pb-3'}
                >
                  <div className="d-flex flex-wrap align-items-center gap-2 mb-1">
                    <CBadge color="secondary">{actionLabels[entry.action] || entry.action}</CBadge>
                    {statusChange && <CBadge color="info">{statusChange}</CBadge>}
                  </div>

                  <div>{entry.description || 'Evento registrado no ciclo de vida do exame.'}</div>
                  <div className="small text-body-secondary mt-1">
                    {entry.user_name || 'Sistema'} ·{' '}
                    {new Date(entry.created_at).toLocaleString('pt-BR')}
                  </div>
                </div>
              )
            })}
          </div>
        )}
        </CCardBody>
      )}
    </CCard>
  )
}

export default ExamHistoryCard
