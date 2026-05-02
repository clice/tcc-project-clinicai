/**
 * Listagem de exames usando mocks.
 *
 * Exibe exames vinculados a pacientes, clínicas, médicos
 * e resultados simulados de análise por IA.
 */

import React, { useCallback, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CBadge, CButton, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppTabs from 'src/components/shared/AppTabs'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { exams as examsMock, aiAnalyses as aiAnalysesMock } from 'src/mocks/data'

const examTabs = [
  { key: 'processing', label: 'Processando' },
  { key: 'review_required', label: 'Revisão' },
  { key: 'approved', label: 'Aprovados' },
  { key: 'canceled', label: 'Cancelados' },
]

const examTypeLabels = {
  colonoscopy: 'Colonoscopia',
  endoscopy: 'Endoscopia',
}

const statusColors = {
  processing: 'info',
  review_required: 'warning',
  approved: 'success',
  canceled: 'danger',
}

const aiStatusLabels = {
  not_processed: 'Não processado',
  processing: 'Processando',
  completed: 'Concluída',
  failed: 'Falhou',
}

const aiStatusColors = {
  not_processed: 'secondary',
  processing: 'info',
  completed: 'success',
  failed: 'danger',
}

const formatDateBR = (value) => {
  if (!value) return '-'

  const date = new Date(`${value}T00:00:00`)

  if (Number.isNaN(date.getTime())) return '-'

  return date.toLocaleDateString('pt-BR')
}

const ExamsList = () => {
  const [activeTab, setActiveTab] = useState('processing')
  const [exams, setExams] = useState(examsMock)
  const [error, setError] = useState('')
  const [isLoading] = useState(false)

  const handleCancel = useCallback((exam) => {
    setError('')

    setExams((current) =>
      current.map((item) =>
        String(item.id) === String(exam.id)
          ? {
              ...item,
              status_id: '10',
              status_name: 'canceled',
              status_display_name: 'Cancelado',
              ai_analysis_status: 'not_processed',
              ai_summary: 'Análise não realizada devido ao cancelamento do exame.',
              updated_at: new Date().toISOString(),
            }
          : item,
      ),
    )
  }, [])

  const filteredExams = useMemo(() => {
    return exams.filter((exam) => exam.status_name === activeTab)
  }, [exams, activeTab])

  const counts = useMemo(
    () => ({
      processing: exams.filter((exam) => exam.status_name === 'processing').length,
      review_required: exams.filter((exam) => exam.status_name === 'review_required').length,
      approved: exams.filter((exam) => exam.status_name === 'approved').length,
      canceled: exams.filter((exam) => exam.status_name === 'canceled').length,
    }),
    [exams],
  )

  const examsWithAi = useMemo(() => {
    return filteredExams.map((exam) => {
      const aiAnalysis = aiAnalysesMock.find(
        (analysis) => String(analysis.exam_id) === String(exam.id),
      )

      return {
        ...exam,
        aiAnalysis,
      }
    })
  }, [filteredExams])

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
        cell: ({ getValue }) => formatDateBR(getValue()),
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
        accessorKey: 'status_name',
        header: 'Status',
        cell: ({ row }) => (
          <CBadge color={statusColors[row.original.status_name] || 'secondary'}>
            {row.original.status_display_name || row.original.status_name}
          </CBadge>
        ),
      },
      {
        accessorKey: 'ai_analysis_status',
        header: 'IA',
        cell: ({ getValue }) => (
          <CBadge color={aiStatusColors[getValue()] || 'secondary'}>
            {aiStatusLabels[getValue()] || getValue() || 'Não processado'}
          </CBadge>
        ),
      },
      {
        id: 'confidence',
        header: 'Confiança',
        cell: ({ row }) => {
          const confidence = row.original.aiAnalysis?.confidence

          if (confidence === undefined || confidence === null) return '-'

          return `${Math.round(confidence * 100)}%`
        },
      },
      {
        id: 'actions',
        header: 'Ações',
        enableSorting: false,
        cell: ({ row }) => {
          const exam = row.original
          const isCanceled = exam.status_name === 'canceled'

          return (
            <AppActionButtons
              itemLabel={exam.title}
              viewTo={`/exams/${exam.id}`}
              editTo={`/exams/${exam.id}/edit`}
              isInactive={isCanceled}
              canView
              onInactivate={() => handleCancel(exam)}
            />
          )
        },
      },
    ],
    [handleCancel],
  )

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Registros de Saúde</div>
          <h1 className="h3 mb-0">Exames</h1>
          <p className="text-body-secondary mb-0">
            Gerencie exames, arquivos enviados e resultados simulados da análise por IA.
          </p>
        </div>
        
        <CButton color="primary" size="lg" as={Link} to="/exams/create">
          Cadastrar Exame
        </CButton>
      </div>

      <CCard>
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          <AppTabs
            activeTab={activeTab}
            counts={counts}
            onChange={setActiveTab}
            tabs={examTabs}
          />

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando exames...</p>
          ) : (
            <AppTable
              data={examsWithAi}
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