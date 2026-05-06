/**
 * Listagem de exames.
 *
 * Exibe exames vinculados a pacientes, médicos e clínicas.
 * Também apresenta status do exame, status estimado da IA e ação de download.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { 
  CAlert, 
  CBadge, 
  CButton, 
  CCard, 
  CCardBody, 
  CFormInput,
  CModal,
  CModalBody,
  CModalFooter,
  CModalHeader,
  CModalTitle,
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
import AppTabs from 'src/components/shared/AppTabs'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { examService } from 'src/services/examService'

import { examTypeLabels, statusColors, aiStatusLabels, aiStatusColors } from 'src/utils/constants'
import { getErrorMessage } from 'src/utils/errors'
import { formatDateTimeBR } from 'src/utils/formatters'
import { canManageExams } from 'src/utils/permissions'

const examTabs = [
  { key: 'processing', label: 'Processando' },
  { key: 'pending', label: 'Pendentes' },
  { key: 'completed', label: 'Concluídos' },
  { key: 'failed', label: 'Falha na IA' },
  { key: 'canceled', label: 'Cancelados' },
]

const getAiStatusFromExam = (exam) => {
  if (exam.status_name === 'processing') return 'processing'
  if (exam.status_name === 'pending') return 'completed'
  if (exam.status_name === 'completed') return 'completed'
  if (exam.status_name === 'failed') return 'failed'
  if (exam.status_name === 'canceled') return 'canceled'

  return 'not_processed'
}

const ExamsList = () => {
  const { user } = useAuth()
  const { showError, showSuccess } = useFeedback()

  const [activeTab, setActiveTab] = useState('processing')
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
    return exams.filter((exam) => exam.status_name === activeTab)
  }, [exams, activeTab])

  const tabCounts = useMemo(
    () => ({
      processing: exams.filter((exam) => exam.status_name === 'processing').length,
      pending: exams.filter((exam) => exam.status_name === 'pending').length,
      completed: exams.filter((exam) => exam.status_name === 'completed').length,
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
          <h1 className="h3 mb-0">Exames</h1>
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

      <CCard>
        <CCardBody>
          {isLoading ? (
            <div className="d-flex justify-content-center py-5">
              <CSpinner />
            </div>
          ) : (
            <>
              <AppTabs
                tabs={examTabs}
                counts={tabCounts}
                activeTab={activeTab}
                onChange={setActiveTab}
              />

              <AppTable
                data={filteredExams}
                columns={columns}
                emptyMessage="Nenhum exame encontrado."
              />
            </>
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default ExamsList