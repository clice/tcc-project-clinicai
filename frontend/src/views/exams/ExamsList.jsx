/**
 * Listagem de exames.
 *
 * Exibe exames vinculados a pacientes, médicos e clínicas.
 * Também apresenta status do exame, status estimado da IA e ação de download.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { 
  CAlert, 
  CBadge, 
  CButton, 
  CCard, 
  CCardBody, 
  CCol,
  CFormInput,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
  CRow,
  CSpinner,
} from '@coreui/react'
import CIcon from '@coreui/icons-react'
import {
  cilCloudUpload,
  cilFolderOpen,
  cilUser,
  cilPencil,
  cilReload,
} from '@coreui/icons'

import AppTable from 'src/components/shared/AppTable'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { examService } from 'src/services/examService'

import { examTypeLabels, statusColors, examStatusLabels, aiStatusLabels, aiStatusColors } from 'src/utils/constants'
import { getErrorMessage } from 'src/utils/errors'
import { formatDateTimeBR } from 'src/utils/formatters'
import { canManageExams } from 'src/utils/permissions'

// Os três estados mais relevantes do dia a dia — os cards de resumo focam
// neles; os demais (falha, cancelado, pendente) ficam só no submenu
// lateral, disponíveis mas sem disputar espaço visual no topo da página.
const summaryCardStatuses = ['processing', 'awaiting_review', 'completed']

const getAiStatusFromExam = (exam) => {
  if (exam.status_name === 'processing') return 'processing'
  if (exam.status_name === 'awaiting_review') return 'completed'
  if (exam.status_name === 'completed') return 'completed'
  if (exam.status_name === 'completed_with_divergence') return 'completed'
  if (exam.status_name === 'failed') return 'failed'
  if (exam.status_name === 'canceled') return 'canceled'

  return 'not_processed'
}

const ExamsList = () => {
  const { user } = useAuth()
  const { showError, showSuccess } = useFeedback()

  const [searchParams, setSearchParams] = useSearchParams()
  // Sem ?status= na URL = visão geral (todos os exames), útil quando se
  // clica em "Exames" no topo do submenu, sem escolher um status específico.
  const statusFilter = searchParams.get('status')

  const [exams, setExams] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  const canManage = canManageExams(user)

  const loadExams = useCallback(async () => {
    try {
      setIsLoading(true)
      showError('')

      const data = await examService.list({
        includeInactive: true,
      })

      setExams(Array.isArray(data) ? data : [])
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao carregar exames.'))
    } finally {
      setIsLoading(false)
    }
  }, [showError])

  useEffect(() => {
    void loadExams()
  }, [loadExams])

  const filteredExams = useMemo(() => {
    if (!statusFilter) return exams
    return exams.filter((exam) => exam.status_name === statusFilter)
  }, [exams, statusFilter])

  const tabCounts = useMemo(
    () => ({
      processing: exams.filter((exam) => exam.status_name === 'processing').length,
      awaiting_review: exams.filter((exam) => exam.status_name === 'awaiting_review').length,
      completed: exams.filter((exam) => exam.status_name === 'completed').length,
      completed_with_divergence: exams.filter(
        (exam) => exam.status_name === 'completed_with_divergence',
      ).length,
      pending: exams.filter((exam) => exam.status_name === 'pending').length,
      failed: exams.filter((exam) => exam.status_name === 'failed').length,
      canceled: exams.filter((exam) => exam.status_name === 'canceled').length,
    }),
    [exams],
  )

  const handleDownloadFile = useCallback(
    async (exam) => {
      try {
        showError('')

        const blob = await examService.downloadFile(exam.id)

        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')

        link.href = url
        link.download = exam.file_name || `exame-${exam.id}`
        document.body.appendChild(link)
        link.click()

        link.remove()
        window.URL.revokeObjectURL(url)
      } catch {
        showError('Erro ao baixar arquivo do exame.')
      }
    },
    [showError],
  )

  const handleCancelExam = useCallback(
    async (exam) => {
      try {
        showError('')

        await examService.cancel(exam.id)

        showSuccess('Exame cancelado com sucesso.')
        await loadExams()
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao cancelar exame.'))
      }
    },
    [loadExams, showError, showSuccess],
  )

  const handleRestoreExam = useCallback(
    async (exam) => {
      try {
        showError('')

        await examService.restore(exam.id)

        showSuccess('Exame retomado com sucesso.')
        await loadExams()
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao retomar exame.'))
      }
    },
    [loadExams, showError, showSuccess],
  )

  const columns = useMemo(
    () => [
      {
        accessorKey: 'title',
        header: 'Exame',
      },
      {
        accessorKey: 'exam_type',
        header: 'Tipo',
        cell: ({ getValue }) => examTypeLabels[getValue()] || getValue() || '-',
      },
      {
        accessorKey: 'exam_date',
        header: 'Data',
        cell: ({ getValue }) => formatDateTimeBR(getValue()),
      },
      {
        accessorKey: 'patient_name',
        header: 'Paciente',
        cell: ({ getValue }) => getValue() || '-',
      },
      {
        accessorKey: 'doctor_name',
        header: 'Médico',
        cell: ({ getValue }) => getValue() || '-',
      },
      {
        accessorKey: 'status_display_name',
        header: 'Status',
        cell: ({ row, getValue }) => (
          <CBadge color={statusColors[row.original.status_name] || 'secondary'}>
            {getValue() || row.original.status_name || '-'}
          </CBadge>
        ),
      },
      {
        id: 'ai_status',
        header: 'IA',
        cell: ({ row }) => {
          const aiStatus = getAiStatusFromExam(row.original)

          return (
            <CBadge color={aiStatusColors[aiStatus] || 'secondary'}>
              {aiStatusLabels[aiStatus] || aiStatus}
            </CBadge>
          )
        },
      },
      {
        id: 'actions',
        header: 'Ações',
        enableSorting: false,
        cell: ({ row }) => {
          const exam = row.original

          const isProcessing = exam.status_name === 'processing'
          const isPending = exam.status_name === 'pending'
          const isCompleted = exam.status_name === 'completed'
          const isFailed = exam.status_name === 'failed'
          const isCanceled = exam.status_name === 'canceled'

          return (
            <AppActionButtons
              itemLabel={exam.title}
              viewTo={`/exams/${exam.id}`}
              editTo={`/exams/${exam.id}/edit`}
              isInactive={isCanceled}
              canView
              canEdit={canManage && (isProcessing || isPending)}
              canUpload={false}
              canDownload={Boolean(exam.file_name)}
              canCancel={canManage && (isProcessing || isPending || isFailed)}
              canRestore={canManage && isCanceled}
              canInactivate={false}
              canActivate={false}
              onDownload={() => handleDownloadFile(exam)}
              onCancel={() => handleCancelExam(exam)}
              onRestore={() => handleRestoreExam(exam)}
            />
          )
        },
      },
    ],
    [canManage, handleCancelExam, handleDownloadFile, handleRestoreExam],
  )

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Registros de Saúde</div>
          <h1 className="h3 mb-0">
            {statusFilter ? `Exames: ${examStatusLabels[statusFilter] || statusFilter}` : 'Exames'}
          </h1>
          <p className="text-body-secondary mb-0">
            Gerencie exames, análise por IA e revisão médica.
          </p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButton color="primary" size="lg" as={Link} to="/exams/create">
            Cadastrar Exame
          </CButton>
        </div>
      </div>

      <CRow className="mb-4">
        {summaryCardStatuses.map((status) => (
          <CCol sm={4} key={status}>
            <CCard
              role="button"
              className={statusFilter === status ? 'border-primary' : ''}
              onClick={() => setSearchParams(status === statusFilter ? {} : { status })}
            >
              <CCardBody>
                <div className="text-body-secondary small">{examStatusLabels[status]}</div>
                <div className="fs-4 fw-semibold">{tabCounts[status] ?? 0}</div>
              </CCardBody>
            </CCard>
          </CCol>
        ))}
      </CRow>

      <CCard>
        <CCardBody>
          {isLoading ? (
            <div className="d-flex justify-content-center py-5">
              <CSpinner />
            </div>
          ) : (
            <AppTable
              data={filteredExams}
              columns={columns}
              emptyMessage="Nenhum exame encontrado."
            />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default ExamsList
