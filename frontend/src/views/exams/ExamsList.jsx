/**
 * Listagem de exames.
 *
 * Somente o Médico recebe ações clínicas.
 * Médico e Gestor da Clínica podem imprimir exames finalizados.
 * Administrador Master recebe somente acesso operacional à listagem.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { CAlert, CBadge, CButton, CCard, CCardBody, CCol, CRow, CSpinner } from '@coreui/react'
import { cilDescription } from '@coreui/icons'

import AppActionButtons from 'src/components/shared/AppActionButtons'
import AppTable from 'src/components/shared/AppTable'

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { examService } from 'src/services/examService'

import {
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
    color: 'completed',
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

const printableExamStatuses = new Set([
  'completed',
  'completed_with_divergence',
])

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

  const canPrintExams =
    roleName === ROLES.DOCTOR ||
    roleName === ROLES.CLINIC_MANAGER

  const hasOperationalExamAccess =
    roleName === ROLES.ADMIN_MASTER || roleName === ROLES.CLINIC_MANAGER
  const showDoctorColumn = roleName !== ROLES.DOCTOR
  const showClinicColumn = roleName === ROLES.ADMIN_MASTER

  const canReadAiAnalysis = hasPermission(user, PERMISSIONS.AI_ANALYSIS_READ)

  const [searchParams, setSearchParams] = useSearchParams()
  const statusFilter = searchParams.get('status')

  const managerCanSeeActions =
    roleName === ROLES.CLINIC_MANAGER &&
    printableExamStatuses.has(statusFilter)

  const canShowActionsColumn =
    canUseClinicalExamActions || managerCanSeeActions

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
        showSuccess('Exame restaurado com sucesso.')
        await loadExams()
      } catch (err) {
        showError(getErrorMessage(err, 'Erro ao restaurar exame.'))
      }
    },
    [loadExams, showError, showSuccess],
  )

  const handlePrintReport = useCallback(
    async (exam) => {
      try {
        const blob =
          await examService.downloadPrintReport(exam.id)

        triggerBlobDownload(
          blob,
          `relatorio-exame-${exam.id}.pdf`,
        )
      } catch (error) {
        showError(
          getErrorMessage(
            error,
            'Não foi possível gerar o relatório PDF.',
          ),
        )
      }
    },
    [showError],
  )

  const columns = useMemo(() => {
    const result = [
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
      {
        accessorKey: 'exam_type',
        header: 'Tipo',
        cell: ({ getValue }) => examTypeLabels[getValue()] || getValue() || '-',
      },
      {
        accessorKey: 'description',
        header: 'Descrição',
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
      ...(!statusFilter
        ? [
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
          ]
        : []),
    ]

    if (!canShowActionsColumn) {
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

        const canPrintCurrentStatus =
          canPrintExams &&
          printableExamStatuses.has(exam.status_name)

        return (
          <AppActionButtons
            itemLabel={exam.description}
            viewTo={!isPending || !canEditExam ? `/exams/${exam.id}` : null}
            viewTitle={statusFilter === 'awaiting_review' ? 'Revisar' : 'Visualizar'}
            viewColor={
              statusFilter === 'awaiting_review'
                ? 'warning'
                : statusFilter === 'pending'
                  ? 'info'
                  : statusFilter === 'failed'
                    ? 'danger'
                    : statusFilter === 'completed'
                      ? 'success'
                      : statusFilter === 'completed_with_divergence'
                        ? 'dark'
                        : 'secondary'
            }
            viewIcon={cilDescription}
            viewIconClassName={
              ['completed', 'failed'].includes(statusFilter) ? 'text-white' : undefined
            }
            editTo={`/exams/${exam.id}`}
            editColor={isPending ? 'info' : 'primary'}
            editIcon={isPending ? cilDescription : undefined}
            isInactive={isCanceled}
            canView={canView}
            canEdit={canEditExam && isPending}
            canUpload={false}
            downloadTitle={
              requiresPackage ? 'Baixar imagem original e Mapa Grad-CAM' : 'Baixar imagem original'
            }
            canDownload={canDownloadCurrentStatus}
            printTitle="Baixar relatório em PDF"
            canPrint={canPrintCurrentStatus}
            onPrint={() => handlePrintReport(exam)}
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
    canPrintExams,
    canShowActionsColumn,
    canView,
    showClinicColumn,
    showDoctorColumn,
    statusFilter,
    handleCancelExam,
    handleDownload,
    handlePrintReport,
    handleRestoreExam,
  ])

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Registros de Saúde</div>
          <h1 className="h3 mb-0 clinicai-page-title">
            {statusFilter ? `Exames: ${examStatusLabels[statusFilter] || statusFilter}` : 'Exames'}
          </h1>
          <p className="text-body-secondary mb-0">
            {roleName === ROLES.DOCTOR
              ? 'Gerencie seus exames, a análise por IA e a revisão médica.'
              : roleName === ROLES.CLINIC_MANAGER
                ? 'Acompanhe os exames dos pacientes vinculados à sua clínica.'
                : 'Acompanhe os status dos exames cadastrados em todas as clínicas.'}
          </p>
        </div>

        {canCreate && canUseClinicalExamActions && (
          <div className="d-flex justify-content-center mt-4">
            <CButton
              color="primary"
              className="clinicai-btn"
              size="lg"
              as={Link}
              to="/exams/create"
            >
              Cadastrar Exame
            </CButton>
          </div>
        )}
      </div>

      <CRow className="mb-4">
        {summaryCards.map(({ status, color }) => {
          const isSelected = statusFilter === status

          const toggleStatus = () => {
            setSearchParams(isSelected ? {} : { status })
          }

          return (
            <CCol sm={6} xl={3} className="mb-3 mb-xl-0" key={status}>
              <CCard
                role="button"
                tabIndex={0}
                aria-pressed={isSelected}
                className={`h-100 ${isSelected ? 'shadow-sm' : ''}`}
                style={{
                  borderTop: `4px solid var(--cui-${color})`,
                }}
                onClick={toggleStatus}
                onKeyDown={(event) => {
                  if (event.key !== 'Enter' && event.key !== ' ') {
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
                      color: `var(--cui-${color})`,
                    }}
                  >
                    {examStatusLabels[status]}
                  </div>

                  <div className="fs-4 fw-semibold text-body">{tabCounts[status] ?? 0}</div>
                </CCardBody>
              </CCard>
            </CCol>
          )
        })}
      </CRow>

      {hasOperationalExamAccess && (
        <CAlert color="info" className="mb-4">
          Este perfil possui acesso exclusivamente operacional à listagem de exames. Informações
          clínicas, imagens, resultados da análise por IA e ações médicas permanecem restritos aos
          médicos responsáveis.
        </CAlert>
      )}

      <CCard className="clinicai-card mb-4">
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
