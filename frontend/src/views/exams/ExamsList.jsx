/**
 * Listagem de exames.
 *
 * Médico e Administrador Master mantêm as ações clínicas autorizadas.
 * O Funcionário da Clínica não recebe coluna de ações.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { CBadge, CButton, CCard, CCardBody, CCol, CRow, CSpinner } from '@coreui/react'

import AppActionButtons from 'src/components/shared/AppActionButtons'
import AppTable from 'src/components/shared/AppTable'

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { examService } from 'src/services/examService'

import {
  aiStatusColors,
  aiStatusLabels,
  examStatusDisplayLabels,
  examStatusLabels,
  examTypeLabels,
  statusColors,
} from 'src/utils/constants'
import {
  buildExamImagesPackageDownloadName,
  buildOriginalDownloadName,
} from 'src/utils/examDownloadNames'
import { getErrorMessage } from 'src/utils/errors'
import { formatDateBR } from 'src/utils/formatters'
import { getActionAccess } from 'src/utils/actionPermissions.mjs'
import { getUserRole, hasPermission, PERMISSIONS, ROLES } from 'src/utils/permissions'

const summaryCards = [
  {
    status: 'pending',
    color: 'info',
  },
  {
    status: 'awaiting_review',
    color: 'warning',
  },
  {
    status: 'completed',
    color: 'success',
  },
  {
    status: 'completed_with_divergence',
    color: 'dark',
  },
]

const packageDownloadStatuses = new Set([
  'awaiting_review',
  'completed',
  'completed_with_divergence',
])

const originalDownloadStatuses = new Set(['pending', 'failed', 'canceled'])

const getAiStatusFromExam = (exam) => {
  if (exam.ai_analysis_status) return exam.ai_analysis_status
  if (exam.status_name === 'processing' && exam.analysis_in_progress) return 'processing'
  if (exam.status_name === 'failed') return 'failed'

  return 'not_processed'
}

const triggerBlobDownload = (blob, fileName) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()

  window.setTimeout(() => {
    window.URL.revokeObjectURL(url)
  }, 1000)
}

const ExamsList = () => {
  const { user } = useAuth()
  const { showError, showSuccess } = useFeedback()
  const roleName = getUserRole(user)

  const canUseClinicalExamActions = roleName === ROLES.DOCTOR
  const showDoctorColumn = roleName !== ROLES.DOCTOR
  const showClinicColumn = roleName === ROLES.ADMIN_MASTER

  const canReadAiAnalysis = hasPermission(user, PERMISSIONS.AI_ANALYSIS_READ)

  const [searchParams, setSearchParams] = useSearchParams()
  const statusFilter = searchParams.get('status')

  const [exams, setExams] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  const { canView, canCreate, canEdit, canChangeStatus, canDownload } = getActionAccess(
    'exams',
    (permission) => hasPermission(user, permission),
  )

  const canEditExam = roleName === ROLES.DOCTOR && canEdit

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
    const initialLoadTimerId = window.setTimeout(() => {
      void loadExams()
    }, 0)

    return () => {
      window.clearTimeout(initialLoadTimerId)
    }
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

  const handleDownload = useCallback(
    async (exam) => {
      try {
        showError('')

        if (packageDownloadStatuses.has(exam.status_name)) {
          const blob = await examService.downloadImagePackage(exam.id)

          triggerBlobDownload(
            blob,
            buildExamImagesPackageDownloadName({
              examId: exam.id,
              patientName: exam.patient_name,
              examDate: exam.exam_date,
            }),
          )
          return
        }

        const blob = await examService.downloadFile(exam.id)

        triggerBlobDownload(
          blob,
          buildOriginalDownloadName({
            examId: exam.id,
            patientName: exam.patient_name,
            examDate: exam.exam_date,
            mimeType: blob.type,
          }),
        )
      } catch (err) {
        showError(getErrorMessage(err, 'Não foi possível baixar as imagens do exame.'))
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

  const columns = useMemo(() => {
    const result = [
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
        cell: ({ getValue }) => formatDateBR(getValue()),
      },
      {
        accessorKey: 'patient_name',
        header: 'Paciente',
        cell: ({ getValue }) => getValue() || '-',
      },
      ...(showDoctorColumn
        ? [
            {
              accessorKey: 'doctor_name',
              header: 'Médico',
              cell: ({ getValue }) => getValue() || '-',
            },
          ]
        : []),
      ...(showClinicColumn
        ? [
            {
              accessorKey: 'clinic_name',
              header: 'Clínica',
              cell: ({ getValue }) => getValue() || '-',
            },
          ]
        : []),
      {
        accessorKey: 'status_display_name',
        header: 'Status',
        cell: ({ row }) => (
          <CBadge color={statusColors[row.original.status_name] || 'secondary'}>
            {examStatusDisplayLabels[row.original.status_name] ||
              row.original.status_display_name ||
              row.original.status_name ||
              '-'}
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
    ]

    if (!canUseClinicalExamActions) {
      return result
    }

    result.push({
      id: 'actions',
      header: 'Ações',
      enableSorting: false,
      cell: ({ row }) => {
        const exam = row.original
        const isProcessing = exam.status_name === 'processing'
        const isPending = exam.status_name === 'pending'
        const isFailed = exam.status_name === 'failed'
        const isCanceled = exam.status_name === 'canceled'
        const requiresPackage = packageDownloadStatuses.has(exam.status_name)
        const allowsOriginal = originalDownloadStatuses.has(exam.status_name)

        const canDownloadCurrentStatus =
          canDownload &&
          exam.file_available &&
          (allowsOriginal || (requiresPackage && canReadAiAnalysis && exam.gradcam_available))

        return (
          <AppActionButtons
            itemLabel={exam.title}
            viewTo={`/exams/${exam.id}`}
            editTo={`/exams/${exam.id}/edit`}
            isInactive={isCanceled}
            canView={canView}
            canEdit={canEditExam && isPending}
            canUpload={false}
            canDownload={canDownloadCurrentStatus}
            downloadTitle={
              requiresPackage ? 'Baixar imagem original e Mapa Grad-CAM' : 'Baixar imagem original'
            }
            canCancel={canChangeStatus && (isProcessing || isPending)}
            canRestore={canChangeStatus && (isCanceled || isFailed)}
            canInactivate={false}
            canActivate={false}
            onDownload={() => handleDownload(exam)}
            onCancel={() => handleCancelExam(exam)}
            onRestore={() => handleRestoreExam(exam)}
          />
        )
      },
    })

    return result
  }, [
    canChangeStatus,
    canDownload,
    canEditExam,
    canReadAiAnalysis,
    canUseClinicalExamActions,
    canView,
    showClinicColumn,
    showDoctorColumn,
    handleCancelExam,
    handleDownload,
    handleRestoreExam,
  ])

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Registros de Saúde</div>
          <h1 className="h3 mb-0">
            {statusFilter ? `Exames: ${examStatusLabels[statusFilter] || statusFilter}` : 'Exames'}
          </h1>
          <p className="text-body-secondary mb-0">
            {roleName === ROLES.DOCTOR
              ? 'Gerencie seus exames, a análise por IA e a revisão médica.'
              : roleName === ROLES.CLINIC_STAFF
                ? 'Acompanhe os exames dos pacientes vinculados à sua clínica.'
                : 'Acompanhe os status dos exames cadastrados em todas as clínicas.'}
          </p>
        </div>

        {canCreate && canUseClinicalExamActions && (
          <div className="d-flex justify-content-center mt-4">
            <CButton color="primary" size="lg" as={Link} to="/exams/create">
              Cadastrar Exame
            </CButton>
          </div>
        )}
      </div>

      <CRow className="mb-4">
        {summaryCards.map(
          ({
            status,
            color,
          }) => {
            const isSelected =
              statusFilter === status

            const toggleStatus = () => {
              setSearchParams(
                isSelected
                  ? {}
                  : { status },
              )
            }

            return (
              <CCol
                sm={6}
                xl={3}
                className="mb-3 mb-xl-0"
                key={status}
              >
                <CCard
                  role="button"
                  tabIndex={0}
                  aria-pressed={
                    isSelected
                  }
                  className={
                    `h-100 ${
                      isSelected
                        ? 'shadow-sm'
                        : ''
                    }`
                  }
                  style={{
                    borderTop:
                      `4px solid var(--cui-${color})`,
                  }}
                  onClick={
                    toggleStatus
                  }
                  onKeyDown={(
                    event,
                  ) => {
                    if (
                      event.key !==
                        'Enter' &&
                      event.key !== ' '
                    ) {
                      return
                    }

                    event.preventDefault()
                    toggleStatus()
                  }}
                >
                  <CCardBody>
                    <div
                      className="small fw-bold"
                      style={{
                        color:
                          `var(--cui-${color})`,
                      }}
                    >
                      {
                        examStatusLabels[
                          status
                        ]
                      }
                    </div>

                    <div className="fs-4 fw-semibold text-body">
                      {
                        tabCounts[
                          status
                        ] ?? 0
                      }
                    </div>
                  </CCardBody>
                </CCard>
              </CCol>
            )
          },
        )}
      </CRow>

      <CCard className="mb-4">
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
