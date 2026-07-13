import React, { useEffect, useMemo, useState } from 'react'

import {
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CFormInput,
  CFormLabel,
  CFormSelect,
  CProgress,
  CRow,
  CSpinner,
  CTable,
  CTableBody,
  CTableDataCell,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
} from '@coreui/react'

import { useAuth } from 'src/hooks/useAuth'
import { useExamStatusCounts } from 'src/hooks/useExamStatusCounts'

import { aiAnalysisService } from 'src/services/aiAnalysisService'
import { clinicService } from 'src/services/clinicService'
import { patientService } from 'src/services/patientService'
import { userService } from 'src/services/userService'

import { examStatusLabels, statusColors } from 'src/utils/constants'
import { formatDateTimeBR } from 'src/utils/formatters'
import { getUserRole, hasPermission, PERMISSIONS, ROLES } from 'src/utils/permissions'

/**
 * Dashboard — RF54 (indicadores gerais), RF55 (distribuição de exames por
 * status), RF56 (indicadores da análise de IA) e RF57 (filtro por
 * período, clínica, médico, status ou resultado).
 *
 * Nota sobre a tese: a Tabela 11 (Dashboard e Monitoramento) hoje só lista
 * RF54–RF57, mas a faixa é citada como "RF54–RF59" tanto no cabeçalho da
 * tabela quanto no UC12 — vale conferir se RF58/RF59 existem e faltaram na
 * tabela, ou se a faixa deveria ser "RF54–RF57".
 *
 * Os filtros (RF57) se aplicam às seções RF55 e RF56 — os cards de
 * indicadores gerais (RF54) permanecem como uma contagem total fixa da
 * plataforma, não como algo "filtrável" no sentido operacional do RF57.
 *
 * Visibilidade de cada filtro por perfil:
 * - Período e Status: todos os perfis.
 * - Clínica: só Administrador Master (Médico e Funcionário da Clínica já
 *   são automaticamente restritos à própria clínica/aos próprios exames
 *   pelo backend — oferecer o filtro seria redundante ou geraria erro).
 * - Médico: Administrador Master e Funcionário da Clínica (o próprio
 *   Médico já só vê os seus exames).
 * - Resultado (normal/anormal, predição da IA): Administrador Master e
 *   Médico apenas — Funcionário da Clínica não tem acesso a resultados
 *   diagnósticos (Art. 34 do CFM); o backend já rejeitaria esse filtro
 *   para esse perfil, mas nem chega a oferecer a opção na interface.
 */

const emptyFilters = {
  dateFrom: '',
  dateTo: '',
  clinicId: '',
  doctorId: '',
  status: '',
  aiPredictionClass: '',
}

const Dashboard = () => {
  const { user } = useAuth()
  const roleName = getUserRole(user)
  const isAdminMaster = roleName === ROLES.ADMIN_MASTER
  const isClinicStaff = roleName === ROLES.CLINIC_STAFF
  const canReadExams = hasPermission(user, PERMISSIONS.EXAMS_READ)

  const [filters, setFilters] = useState(emptyFilters)

  const { counts: examCounts, isLoading: isLoadingExamCounts } = useExamStatusCounts(
    filters,
    canReadExams,
  )

  const [generalCounts, setGeneralCounts] = useState({
    users: null,
    clinics: null,
    patients: null,
    exams: null,
  })
  const [isLoadingGeneral, setIsLoadingGeneral] = useState(true)

  const [clinicOptions, setClinicOptions] = useState([])
  const [doctorOptions, setDoctorOptions] = useState([])

  const [aiMetrics, setAiMetrics] = useState(null)
  const [isLoadingAiMetrics, setIsLoadingAiMetrics] = useState(true)

  // Métricas de governança/infraestrutura de IA — exclusivas do Admin
  // Master. A rota já é protegida no backend (require_admin); aqui só
  // evitamos a chamada desnecessária para os outros perfis.
  useEffect(() => {
    if (!isAdminMaster) {
      setIsLoadingAiMetrics(false)
      return
    }

    const loadAiMetrics = async () => {
      try {
        setIsLoadingAiMetrics(true)
        const data = await aiAnalysisService.getMetrics()
        setAiMetrics(data)
      } catch {
        setAiMetrics(null)
      } finally {
        setIsLoadingAiMetrics(false)
      }
    }

    void loadAiMetrics()
  }, [isAdminMaster])

  // Indicadores gerais (RF54) — contagem fixa da plataforma, sem filtro.
  useEffect(() => {
    const loadGeneralCounts = async () => {
      try {
        setIsLoadingGeneral(true)

        const patients = await patientService.list({ includeInactive: true })

        const next = {
          patients: Array.isArray(patients) ? patients.length : null,
          users: null,
          clinics: null,
        }

        if (isAdminMaster) {
          const [clinics, users] = await Promise.all([
            clinicService.list({ includeInactive: true }),
            userService.list({}),
          ])
          next.clinics = Array.isArray(clinics) ? clinics.length : null
          next.users = Array.isArray(users) ? users.length : null
          setClinicOptions(Array.isArray(clinics) ? clinics : [])
        }

        setGeneralCounts(next)
      } catch {
        // Indicador degrada para '-' em vez de travar a tela do dashboard.
      } finally {
        setIsLoadingGeneral(false)
      }
    }

    void loadGeneralCounts()
  }, [isAdminMaster])

  // Opções de médico para o filtro (RF57) — só carregadas para os perfis
  // que efetivamente enxergam esse filtro (Admin Master e Funcionário).
  useEffect(() => {
    if (!isAdminMaster && !isClinicStaff) return

    const loadDoctors = async () => {
      try {
        const doctors = await userService.list({ role: 'doctor' })
        setDoctorOptions(Array.isArray(doctors) ? doctors : [])
      } catch {
        setDoctorOptions([])
      }
    }

    void loadDoctors()
  }, [isAdminMaster, isClinicStaff])

  // RF56: aproveita as contagens por status já filtradas (RF55) para
  // derivar os indicadores de IA, em vez de buscar a análise de cada
  // exame individualmente.
  const aiIndicators = useMemo(() => {
    const totalProcessedByAi =
      examCounts.awaiting_review +
      examCounts.completed +
      examCounts.completed_with_divergence +
      examCounts.failed

    const totalConcluded = examCounts.completed + examCounts.completed_with_divergence
    const divergenceRate = totalConcluded > 0 ? examCounts.completed_with_divergence / totalConcluded : 0

    return {
      totalProcessed: totalProcessedByAi,
      failed: examCounts.failed,
      divergenceRate,
    }
  }, [examCounts])

  const totalFilteredExams = useMemo(
    () => Object.values(examCounts).reduce((sum, value) => sum + value, 0),
    [examCounts],
  )

  const statusDistributionEntries = Object.keys(examStatusLabels).filter((status) => status !== 'pending')

  const formatPercent = (value) => `${(value * 100).toFixed(1)}%`

  const renderCount = (value, isLoading) => {
    if (isLoading) return <CSpinner size="sm" />
    return value === null ? '-' : value
  }

  const handleFilterChange = (field) => (event) => {
    setFilters((prev) => ({ ...prev, [field]: event.target.value }))
  }

  const hasActiveFilters = Object.values(filters).some((value) => value !== '')

  return (
    <>
      <div className="mb-4">
        <div className="text-body-secondary">Visão Geral</div>
        <h1 className="h3 mb-0">Dashboard</h1>
        <p className="text-body-secondary mb-0">
          Indicadores gerais da plataforma, do fluxo de exames e das análises de IA.
        </p>
      </div>

      {/* RF54 — Indicadores gerais da plataforma (sem filtro) */}
      <CRow className="mb-4">
        {isAdminMaster && (
          <>
            <CCol sm={6} lg={3}>
              <CCard className="mb-3">
                <CCardBody>
                  <div className="text-body-secondary small">Usuários</div>
                  <div className="fs-4 fw-semibold">
                    {renderCount(generalCounts.users, isLoadingGeneral)}
                  </div>
                </CCardBody>
              </CCard>
            </CCol>
            <CCol sm={6} lg={3}>
              <CCard className="mb-3">
                <CCardBody>
                  <div className="text-body-secondary small">Clínicas</div>
                  <div className="fs-4 fw-semibold">
                    {renderCount(generalCounts.clinics, isLoadingGeneral)}
                  </div>
                </CCardBody>
              </CCard>
            </CCol>
          </>
        )}
        <CCol sm={6} lg={3}>
          <CCard className="mb-3">
            <CCardBody>
              <div className="text-body-secondary small">Pacientes</div>
              <div className="fs-4 fw-semibold">
                {renderCount(generalCounts.patients, isLoadingGeneral)}
              </div>
            </CCardBody>
          </CCard>
        </CCol>
        <CCol sm={6} lg={3}>
          <CCard className="mb-3">
            <CCardBody>
              <div className="text-body-secondary small">
                Exames {hasActiveFilters ? '(filtrados)' : ''}
              </div>
              <div className="fs-4 fw-semibold">
                {renderCount(totalFilteredExams, isLoadingExamCounts)}
              </div>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      {/* RF57 — Filtros, aplicados às seções abaixo (RF55 e RF56) */}
      <CCard className="mb-4">
        <CCardBody>
          <h2 className="h6 mb-3">Filtrar Indicadores</h2>
          <CRow className="g-3 align-items-end">
            <CCol sm={6} lg={2}>
              <CFormLabel htmlFor="dateFrom">Período — de</CFormLabel>
              <CFormInput
                type="date"
                id="dateFrom"
                value={filters.dateFrom}
                onChange={handleFilterChange('dateFrom')}
              />
            </CCol>
            <CCol sm={6} lg={2}>
              <CFormLabel htmlFor="dateTo">Período — até</CFormLabel>
              <CFormInput
                type="date"
                id="dateTo"
                value={filters.dateTo}
                onChange={handleFilterChange('dateTo')}
              />
            </CCol>

            {isAdminMaster && (
              <CCol sm={6} lg={2}>
                <CFormLabel htmlFor="clinicFilter">Clínica</CFormLabel>
                <CFormSelect
                  id="clinicFilter"
                  value={filters.clinicId}
                  onChange={handleFilterChange('clinicId')}
                >
                  <option value="">Todas</option>
                  {clinicOptions.map((clinic) => (
                    <option key={clinic.id} value={clinic.id}>
                      {clinic.name}
                    </option>
                  ))}
                </CFormSelect>
              </CCol>
            )}

            {(isAdminMaster || isClinicStaff) && (
              <CCol sm={6} lg={2}>
                <CFormLabel htmlFor="doctorFilter">Médico</CFormLabel>
                <CFormSelect
                  id="doctorFilter"
                  value={filters.doctorId}
                  onChange={handleFilterChange('doctorId')}
                >
                  <option value="">Todos</option>
                  {doctorOptions.map((doctor) => (
                    <option key={doctor.id} value={doctor.id}>
                      {doctor.name}
                    </option>
                  ))}
                </CFormSelect>
              </CCol>
            )}

            <CCol sm={6} lg={2}>
              <CFormLabel htmlFor="statusFilter">Status</CFormLabel>
              <CFormSelect
                id="statusFilter"
                value={filters.status}
                onChange={handleFilterChange('status')}
              >
                <option value="">Todos</option>
                {Object.keys(examStatusLabels).map((status) => (
                  <option key={status} value={status}>
                    {examStatusLabels[status]}
                  </option>
                ))}
              </CFormSelect>
            </CCol>

            {!isClinicStaff && (
              <CCol sm={6} lg={2}>
                <CFormLabel htmlFor="resultFilter">Resultado (IA)</CFormLabel>
                <CFormSelect
                  id="resultFilter"
                  value={filters.aiPredictionClass}
                  onChange={handleFilterChange('aiPredictionClass')}
                >
                  <option value="">Todos</option>
                  <option value="0">Normal</option>
                  <option value="1">Anormal</option>
                </CFormSelect>
              </CCol>
            )}

            <CCol sm={6} lg={2}>
              <CButton
                color="secondary"
                variant="outline"
                disabled={!hasActiveFilters}
                onClick={() => setFilters(emptyFilters)}
              >
                Limpar filtros
              </CButton>
            </CCol>
          </CRow>
        </CCardBody>
      </CCard>

      {/* RF55 — Distribuição de exames por status */}
      <CRow className="mb-4">
        <CCol xs={12}>
          <CCard>
            <CCardBody>
              <h2 className="h6 mb-3">Exames por Status</h2>

              {isLoadingExamCounts ? (
                <div className="d-flex justify-content-center py-4">
                  <CSpinner />
                </div>
              ) : totalFilteredExams === 0 ? (
                <p className="text-body-secondary mb-0">
                  Nenhum exame encontrado para os filtros selecionados.
                </p>
              ) : (
                statusDistributionEntries
                  .filter((status) => !filters.status || filters.status === status)
                  .map((status) => {
                    const count = examCounts[status] ?? 0
                    const percent = totalFilteredExams > 0 ? (count / totalFilteredExams) * 100 : 0

                    return (
                      <div key={status} className="mb-3">
                        <div className="d-flex justify-content-between mb-1">
                          <span>
                            <CBadge color={statusColors[status]} className="me-2">
                              &nbsp;
                            </CBadge>
                            {examStatusLabels[status]}
                          </span>
                          <span className="text-body-secondary">{count}</span>
                        </div>
                        <CProgress thin color={statusColors[status]} value={percent} />
                      </div>
                    )
                  })
              )}
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      {/* RF56 — Indicadores da análise de IA (fora do escopo do Funcionário
          da Clínica, que não tem permissão de acesso a ai_analysis). */}
      {!isClinicStaff && (
        <CRow className="mb-4">
          <CCol sm={4}>
            <CCard className="mb-3">
              <CCardBody>
                <div className="text-body-secondary small">Exames processados pela IA</div>
                <div className="fs-4 fw-semibold">
                  {renderCount(aiIndicators.totalProcessed, isLoadingExamCounts)}
                </div>
              </CCardBody>
            </CCard>
          </CCol>
          <CCol sm={4}>
            <CCard className="mb-3">
              <CCardBody>
                <div className="text-body-secondary small">Falhas de processamento</div>
                <div className="fs-4 fw-semibold">
                  {renderCount(aiIndicators.failed, isLoadingExamCounts)}
                </div>
              </CCardBody>
            </CCard>
          </CCol>
          <CCol sm={4}>
            <CCard className="mb-3">
              <CCardBody>
                <div className="text-body-secondary small">Taxa de divergência médica</div>
                <div className="fs-4 fw-semibold">
                  {isLoadingExamCounts ? (
                    <CSpinner size="sm" />
                  ) : (
                    formatPercent(aiIndicators.divergenceRate)
                  )}
                </div>
                <div className="text-body-secondary small">
                  Proporção de exames concluídos em que o médico identificou divergência em
                  relação à classificação automatizada.
                </div>
              </CCardBody>
            </CCard>
          </CCol>
        </CRow>
      )}

      {isAdminMaster && (
        <CCard className="mb-4 border-info">
          <CCardHeader className="bg-info-subtle">
            <strong>Métricas de IA (Administrador Master)</strong>
          </CCardHeader>

          <CCardBody>
            {isLoadingAiMetrics ? (
              <div className="d-flex justify-content-center py-4">
                <CSpinner />
              </div>
            ) : !aiMetrics ? (
              <p className="text-body-secondary mb-0">
                Não foi possível carregar as métricas de IA no momento.
              </p>
            ) : (
              <>
                <CRow className="mb-4">
                  <CCol sm={4}>
                    <div className="text-body-secondary small">Total de análises realizadas</div>
                    <div className="fs-4 fw-semibold">{aiMetrics.total_analyses}</div>
                  </CCol>
                  <CCol sm={4}>
                    <div className="text-body-secondary small">Confiança média</div>
                    <div className="fs-4 fw-semibold">
                      {aiMetrics.confidence_mean !== null
                        ? `${(aiMetrics.confidence_mean * 100).toFixed(1)}%`
                        : '-'}
                    </div>
                    <div className="text-body-secondary small">
                      Mín. {aiMetrics.confidence_min !== null ? `${(aiMetrics.confidence_min * 100).toFixed(1)}%` : '-'}
                      {' · '}
                      Máx. {aiMetrics.confidence_max !== null ? `${(aiMetrics.confidence_max * 100).toFixed(1)}%` : '-'}
                    </div>
                  </CCol>
                  <CCol sm={4}>
                    <div className="text-body-secondary small">Tempo médio de processamento</div>
                    <div className="fs-4 fw-semibold">
                      {aiMetrics.processing_time_mean_ms !== null
                        ? `${Math.round(aiMetrics.processing_time_mean_ms)} ms`
                        : '-'}
                    </div>
                  </CCol>
                </CRow>

                <h2 className="h6 mb-3">Uso por Modelo</h2>
                {aiMetrics.by_model.length === 0 ? (
                  <p className="text-body-secondary">Nenhuma análise registrada ainda.</p>
                ) : (
                  <CTable small responsive className="mb-4">
                    <CTableHead>
                      <CTableRow>
                        <CTableHeaderCell>Modelo</CTableHeaderCell>
                        <CTableHeaderCell>Versão</CTableHeaderCell>
                        <CTableHeaderCell>Análises</CTableHeaderCell>
                      </CTableRow>
                    </CTableHead>
                    <CTableBody>
                      {aiMetrics.by_model.map((row) => (
                        <CTableRow key={`${row.model_name}-${row.model_version}`}>
                          <CTableDataCell>{row.model_name}</CTableDataCell>
                          <CTableDataCell>{row.model_version}</CTableDataCell>
                          <CTableDataCell>{row.count}</CTableDataCell>
                        </CTableRow>
                      ))}
                    </CTableBody>
                  </CTable>
                )}

                <h2 className="h6 mb-3">Distribuição de Confiança</h2>
                <div className="mb-4">
                  {Object.entries(aiMetrics.confidence_distribution).map(([faixa, count]) => {
                    const percent =
                      aiMetrics.total_analyses > 0 ? (count / aiMetrics.total_analyses) * 100 : 0
                    return (
                      <div key={faixa} className="mb-2">
                        <div className="d-flex justify-content-between mb-1">
                          <span className="small">{faixa}</span>
                          <span className="text-body-secondary small">{count}</span>
                        </div>
                        <CProgress thin value={percent} />
                      </div>
                    )
                  })}
                </div>

                <h2 className="h6 mb-3">Falhas Recentes</h2>
                {aiMetrics.recent_failures.length === 0 ? (
                  <p className="text-body-secondary mb-0">Nenhuma falha registrada.</p>
                ) : (
                  <CTable small responsive>
                    <CTableHead>
                      <CTableRow>
                        <CTableHeaderCell>Exame</CTableHeaderCell>
                        <CTableHeaderCell>Descrição</CTableHeaderCell>
                        <CTableHeaderCell>Quando</CTableHeaderCell>
                      </CTableRow>
                    </CTableHead>
                    <CTableBody>
                      {aiMetrics.recent_failures.map((failure, index) => (
                        <CTableRow key={`${failure.exam_id}-${index}`}>
                          <CTableDataCell>#{failure.exam_id ?? '-'}</CTableDataCell>
                          <CTableDataCell>{failure.description ?? '-'}</CTableDataCell>
                          <CTableDataCell>
                            {failure.created_at ? formatDateTimeBR(failure.created_at) : '-'}
                          </CTableDataCell>
                        </CTableRow>
                      ))}
                    </CTableBody>
                  </CTable>
                )}
              </>
            )}
          </CCardBody>
        </CCard>
      )}
    </>
  )
}

export default Dashboard
