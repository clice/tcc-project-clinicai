import React, { useEffect, useMemo, useState } from 'react'

import { CBadge, CCard, CCardBody, CCol, CProgress, CRow, CSpinner } from '@coreui/react'

import { useAuth } from 'src/hooks/useAuth'
import { useExamStatusCounts } from 'src/hooks/useExamStatusCounts'

import { clinicService } from 'src/services/clinicService'
import { patientService } from 'src/services/patientService'
import { userService } from 'src/services/userService'

import { examStatusLabels, statusColors } from 'src/utils/constants'
import { getUserRole, ROLES } from 'src/utils/permissions'

/**
 * Dashboard — RF54 (indicadores gerais), RF55 (distribuição de exames por
 * status) e RF56 (indicadores da análise de IA).
 *
 * RF57 (filtrar por período/clínica/médico/status/resultado) fica fora
 * desta primeira versão — é um recurso maior, tratado à parte depois.
 *
 * Nota sobre a tese: a Tabela 11 (Dashboard e Monitoramento) hoje só lista
 * RF54–RF57, mas a faixa é citada como "RF54–RF59" tanto no cabeçalho da
 * tabela quanto no UC12 — vale conferir se RF58/RF59 existem e faltaram na
 * tabela, ou se a faixa deveria ser "RF54–RF57".
 *
 * Escopo por perfil:
 * - Administrador Master: todos os indicadores (usuários, clínicas,
 *   pacientes, exames, distribuição por status, indicadores de IA).
 * - Médico: pacientes, exames, distribuição por status e indicadores de
 *   IA — sem contagem de usuários/clínicas (fora do escopo de gestão dele).
 * - Funcionário da Clínica: pacientes, exames e distribuição por status
 *   (indicadores agregados de volume/operação). SEM indicadores de IA —
 *   esse perfil não tem permissão de acesso a `ai_analysis` (Art. 34 do
 *   CFM), então RF56 fica de fora para ele, não só ai_analysis:read.
 */

const Dashboard = () => {
  const { user } = useAuth()
  const roleName = getUserRole(user)
  const isAdminMaster = roleName === ROLES.ADMIN_MASTER
  const isClinicStaff = roleName === ROLES.CLINIC_STAFF

  const { counts: examCounts, isLoading: isLoadingExamCounts } = useExamStatusCounts()

  const [generalCounts, setGeneralCounts] = useState({
    users: null,
    clinics: null,
    patients: null,
  })
  const [isLoadingGeneral, setIsLoadingGeneral] = useState(true)

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

  // RF56: aproveita as contagens por status já existentes (RF55) para
  // derivar os indicadores de IA, em vez de buscar a análise de cada
  // exame individualmente — falha/conclusão/divergência já são, no fundo,
  // estados do próprio fluxo de exame.
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

  const totalExams = useMemo(
    () => Object.values(examCounts).reduce((sum, value) => sum + value, 0),
    [examCounts],
  )

  const statusDistributionEntries = Object.keys(examStatusLabels).filter((status) => status !== 'pending')

  const formatPercent = (value) => `${(value * 100).toFixed(1)}%`

  const renderCount = (value, isLoading) => {
    if (isLoading) return <CSpinner size="sm" />
    return value === null ? '-' : value
  }

  return (
    <>
      <div className="mb-4">
        <div className="text-body-secondary">Visão Geral</div>
        <h1 className="h3 mb-0">Dashboard</h1>
        <p className="text-body-secondary mb-0">
          Indicadores gerais da plataforma, do fluxo de exames e das análises de IA.
        </p>
      </div>

      {/* RF54 — Indicadores gerais da plataforma */}
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
              <div className="text-body-secondary small">Exames</div>
              <div className="fs-4 fw-semibold">
                {renderCount(totalExams, isLoadingExamCounts)}
              </div>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

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
              ) : totalExams === 0 ? (
                <p className="text-body-secondary mb-0">Nenhum exame cadastrado ainda.</p>
              ) : (
                statusDistributionEntries.map((status) => {
                  const count = examCounts[status] ?? 0
                  const percent = totalExams > 0 ? (count / totalExams) * 100 : 0

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
    </>
  )
}

export default Dashboard
