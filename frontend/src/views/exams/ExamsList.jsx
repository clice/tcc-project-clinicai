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
import { getUserRole, ROLES, canManageExams } from 'src/utils/permissions'

const examTabs = [
  { key: 'pending', label: 'Pendentes' },
  { key: 'processing', label: 'Processando' },
  { key: 'completed', label: 'Concluídos' },
  { key: 'canceled', label: 'Cancelados' },
]

const getAiStatusFromExam = (exam) => {
  if (exam.status_name === 'canceled') {
    return 'canceled'
  }

  if (!exam.file_name) {
    return 'pending'
  }

  if (exam.status_name === 'processing') {
    return 'processing'
  }

  if (exam.status_name === 'completed') {
    return 'completed'
  }

  return 'processing'
}

const ExamsList = () => {
  const { user } = useAuth()
  const { showError, showSuccess } = useFeedback()

  const [activeTab, setActiveTab] = useState('pending')
  const [exams, setExams] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  const [selectedExam, setSelectedExam] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

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
      pending: exams.filter((exam) => exam.status_name === 'pending').length,
      processing: exams.filter((exam) => exam.status_name === 'processing').length,
      completed: exams.filter((exam) => exam.status_name === 'completed').length,
      canceled: exams.filter((exam) => exam.status_name === 'canceled').length,
    }),
    [exams],
  )

  const handleOpenUploadModal = useCallback((exam) => {
    setSelectedExam(exam)
    setSelectedFile(null)
    setUploadModalVisible(true)
  }, [])  

  const handleUploadFile = useCallback(async () => {
    if (!selectedExam || !selectedFile) {
      showError('Selecione um arquivo para enviar.')
      return
    }

    try {
      setIsUploading(true)
      showError('')

      await examService.uploadFile(selectedExam.id, selectedFile)

      setUploadModalVisible(false)
      setSelectedExam(null)
      setSelectedFile(null)

      await loadExams()
    } catch (err) {
      showError(err.response?.data?.detail || 'Erro ao enviar arquivo do exame.')
    } finally {
      setIsUploading(false)
    }
  }, [selectedExam, selectedFile, loadExams])

  const handleDownloadFile = useCallback(async (exam) => {
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
  }, [])  

  const handleCancelExam = async (exam) => {
    try {
      showError('')

      await examService.cancel(exam.id)
      showSuccess('Exame cancelado com sucesso.')
      await loadExams()
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao cancelar exame.'))
    }
  }

  const handleRestoreExam = useCallback(
    async (exam) => {
      try {
        showError('')

        await examService.restore(exam.id)

        await loadExams()
      } catch (err) {
        showError(err.response?.data?.detail || 'Erro ao retomar exame.')
      }
    },
    [loadExams],
  )

  const handleCloseUploadModal = useCallback(() => {
    if (isUploading) return

    setUploadModalVisible(false)
    setSelectedExam(null)
    setSelectedFile(null)
  }, [isUploading])

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
        id: 'ai_status',
        header: 'IA',
        cell: ({ row }) => {
          const aiStatus = getAiStatusFromExam(row.original)

          return (
            <CBadge color={aiStatusColors[aiStatus] || 'secondary'}>
              {aiStatusLabels[aiStatus] || '-'}
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

          const isPending = exam.status_name === 'pending'
          const isProcessing = exam.status_name === 'processing'
          const isCompleted = exam.status_name === 'completed'
          const isCanceled = exam.status_name === 'canceled'

          return (
            <AppActionButtons
              itemLabel={exam.title}
              viewTo={`/exams/${exam.id}`}
              editTo={`/exams/${exam.id}/edit`}
              isInactive={isCanceled}

              canView
              canEdit={isPending || isProcessing}
              canUpload={isPending}
              canDownload={Boolean(exam.file_name) && (isProcessing || isCompleted)}
              canCancel={isPending || isProcessing}
              canRestore={isCanceled}

              canInactivate={false}
              canActivate={false}

              onUpload={() => handleOpenUploadModal(exam)}
              onDownload={() => handleDownloadFile(exam)}
              onCancel={() => handleCancelExam(exam)}
              onRestore={() => handleRestoreExam(exam)}
            />
          )
        },
      }
    ],
    [canManage, handleCancelExam],
  )

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Registros de Saúde</div>
          <h1 className="h3 mb-0">Exames</h1>
          <p className="text-body-secondary mb-0">
            Gerencie exames, arquivos enviados e acompanhamento inicial da análise por IA.
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
              <AppTabs tabs={examTabs} counts={tabCounts} activeTab={activeTab} onChange={setActiveTab} />
              <AppTable data={filteredExams} columns={columns} emptyMessage="Nenhum exame encontrado." />
            </>
          )}

          {/* {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando exames...</p>
          ) : (
            <AppTable
              data={examsWithAi}
              columns={columns}
              emptyMessage="Nenhum exame encontrado."
            />
          )} */}
        </CCardBody>
      </CCard>

      <CModal visible={uploadModalVisible} onClose={handleCloseUploadModal}>
        <CModalHeader>
          <CModalTitle>Enviar arquivo do exame</CModalTitle>
        </CModalHeader>

        <CModalBody>
          <p className="mb-2">
            Exame: <strong>{selectedExam?.title}</strong>
          </p>

          <p className="text-body-secondary small">
            Formatos permitidos: PDF, JPG, JPEG ou PNG.
          </p>

          <CFormInput
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            disabled={isUploading}
            onChange={(event) => {
              setSelectedFile(event.target.files?.[0] || null)
            }}
          />
        </CModalBody>

        <CModalFooter>
          <CButton
            color="secondary"
            variant="outline"
            onClick={handleCloseUploadModal}
            disabled={isUploading}
          >
            Fechar
          </CButton>

          <CButton
            color="primary"
            onClick={handleUploadFile}
            disabled={isUploading || !selectedFile}
          >
            {isUploading ? 'Enviando...' : 'Enviar arquivo'}
          </CButton>
        </CModalFooter>
      </CModal>
    </>
  )
}

export default ExamsList