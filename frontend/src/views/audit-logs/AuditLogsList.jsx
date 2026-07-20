/**
 * Listagem e filtros dos logs de auditoria.
 */

import React, { useEffect, useMemo, useState } from 'react'
import {
  CAlert,
  CBadge,
  CButton,
  CCard,
  CCardBody,
  CCol,
  CForm,
  CFormInput,
  CFormLabel,
  CFormSelect,
  CRow,
} from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'

import { auditLogService } from 'src/services/auditLogService'
import { userService } from 'src/services/userService'
import { getErrorMessage } from 'src/utils/errors'
import { formatDateTimeBR } from 'src/utils/formatters'

const PAGE_SIZE = 50

const emptyFilters = {
  userId: '',
  entity: '',
  action: '',
  dateFrom: '',
  dateTo: '',
}

const entityLabels = {
  user: 'Usuário',
  clinic: 'Clínica',
  patient: 'Paciente',
  exam: 'Exame',
  ai_analysis: 'Análise de IA',
  role: 'Perfil',
  permission: 'Permissão',
  role_permission: 'Permissão do perfil',
  status: 'Status',
  auth: 'Autenticação',
}

const actionLabels = {
  create: 'Criação',
  update: 'Atualização',
  update_password: 'Alteração de senha',
  change_status_activate: 'Ativação',
  change_status_inactivate: 'Inativação',
  delete: 'Exclusão',
  login_success: 'Login realizado',
  login_failed: 'Falha de login',
  refresh_token: 'Refresh de token',
  logout: 'Logout',
  cancel_exam: 'Cancelamento de exame',
  restore_exam: 'Reprocessamento de exame',
  upload: 'Upload',
  download: 'Download',
  run_ai_analysis: 'Execução de IA',
  ai_analysis_failed: 'Falha na análise de IA',
  review_exam: 'Revisão médica',
}

const actionColors = {
  create: 'success',
  update: 'info',
  update_password: 'warning',
  change_status_activate: 'success',
  change_status_inactivate: 'warning',
  delete: 'danger',
  login_success: 'success',
  login_failed: 'danger',
  refresh_token: 'secondary',
  logout: 'secondary',
  cancel_exam: 'danger',
  restore_exam: 'info',
  upload: 'info',
  download: 'secondary',
  run_ai_analysis: 'primary',
  ai_analysis_failed: 'danger',
  review_exam: 'primary',
}

const getActionColor = (action) => actionColors[action] || 'secondary'

const AuditLogsList = () => {
  const [auditLogs, setAuditLogs] = useState([])
  const [users, setUsers] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [filters, setFilters] = useState({ ...emptyFilters })
  const [appliedFilters, setAppliedFilters] = useState({ ...emptyFilters })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let isCurrentRequest = true

    auditLogService
      .list({
        ...appliedFilters,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      })
      .then((data) => {
        if (!isCurrentRequest) return

        setAuditLogs(data.items)
        setTotal(data.total)
        setError('')
      })
      .catch((err) => {
        if (!isCurrentRequest) return

        setError(getErrorMessage(err, 'Erro ao carregar logs de auditoria.'))
      })
      .finally(() => {
        if (isCurrentRequest) {
          setIsLoading(false)
        }
      })

    return () => {
      isCurrentRequest = false
    }
  }, [appliedFilters, page])

  useEffect(() => {
    const loadUsers = async () => {
      try {
        const data = await userService.list()
        setUsers(Array.isArray(data) ? data : [])
      } catch {
        setUsers([])
      }
    }

    void loadUsers()
  }, [])

  const sortedUsers = useMemo(
    () => [...users].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')),
    [users],
  )

  const sortedLogs = useMemo(
    () =>
      [...auditLogs].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ),
    [auditLogs],
  )

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const canGoPrevious = page > 0
  const canGoNext = page + 1 < totalPages

  const handleFilterChange = (event) => {
    const { name, value } = event.target

    setFilters((current) => ({
      ...current,
      [name]: value,
    }))
  }

  const handleApplyFilters = (event) => {
    event.preventDefault()

    if (filters.dateFrom && filters.dateTo && filters.dateFrom > filters.dateTo) {
      setError('A data inicial não pode ser posterior à data final.')
      return
    }

    setError('')
    setIsLoading(true)
    setPage(0)
    setAppliedFilters({ ...filters })
  }

  const handleClearFilters = () => {
    setError('')
    setIsLoading(true)
    setFilters({ ...emptyFilters })
    setPage(0)
    setAppliedFilters({ ...emptyFilters })
  }

  const columns = useMemo(
    () => [
      {
        accessorKey: 'created_at',
        header: 'Data/Hora',
        cell: ({ getValue }) => formatDateTimeBR(getValue()),
      },
      {
        accessorKey: 'action',
        header: 'Ação',
        cell: ({ getValue }) => (
          <CBadge color={getActionColor(getValue())}>
            {actionLabels[getValue()] || getValue()}
          </CBadge>
        ),
      },
      {
        accessorKey: 'entity',
        header: 'Entidade',
        cell: ({ getValue }) => entityLabels[getValue()] || getValue() || '-',
      },
      {
        accessorKey: 'user_name',
        header: 'Usuário',
        cell: ({ getValue }) => getValue() || 'Sistema',
      },
      {
        accessorKey: 'description',
        header: 'Descrição',
        cell: ({ getValue }) => getValue() || '-',
      },
      {
        accessorKey: 'ip_address',
        header: 'IP',
        cell: ({ getValue }) => getValue() || '-',
      },
    ],
    [],
  )

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Segurança e Auditoria</div>
          <h1 className="h3 mb-0">Logs de Auditoria</h1>
          <p className="text-body-secondary mb-0">
            Acompanhe e filtre ações relevantes realizadas no sistema ClinicAI.
          </p>
        </div>
      </div>

      <CCard className="mb-4">
        <CCardBody>
          <CForm onSubmit={handleApplyFilters}>
            <CRow className="g-3 align-items-end">
              <CCol md={6} xl={3}>
                <CFormLabel htmlFor="audit-user">Usuário</CFormLabel>
                <CFormSelect
                  id="audit-user"
                  name="userId"
                  value={filters.userId}
                  onChange={handleFilterChange}
                >
                  <option value="">Todos</option>
                  {sortedUsers.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name} — {item.email}
                    </option>
                  ))}
                </CFormSelect>
              </CCol>

              <CCol md={6} xl={2}>
                <CFormLabel htmlFor="audit-entity">Entidade</CFormLabel>
                <CFormSelect
                  id="audit-entity"
                  name="entity"
                  value={filters.entity}
                  onChange={handleFilterChange}
                >
                  <option value="">Todas</option>
                  {Object.entries(entityLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </CFormSelect>
              </CCol>

              <CCol md={6} xl={3}>
                <CFormLabel htmlFor="audit-action">Ação ou evento</CFormLabel>
                <CFormSelect
                  id="audit-action"
                  name="action"
                  value={filters.action}
                  onChange={handleFilterChange}
                >
                  <option value="">Todos</option>
                  {Object.entries(actionLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </CFormSelect>
              </CCol>

              <CCol md={6} xl={2}>
                <CFormLabel htmlFor="audit-date-from">Data inicial</CFormLabel>
                <CFormInput
                  id="audit-date-from"
                  type="date"
                  name="dateFrom"
                  value={filters.dateFrom}
                  onChange={handleFilterChange}
                />
              </CCol>

              <CCol md={6} xl={2}>
                <CFormLabel htmlFor="audit-date-to">Data final</CFormLabel>
                <CFormInput
                  id="audit-date-to"
                  type="date"
                  name="dateTo"
                  value={filters.dateTo}
                  onChange={handleFilterChange}
                />
              </CCol>

              <CCol xs={12}>
                <div className="d-flex flex-wrap gap-2">
                  <CButton type="submit" color="primary">
                    Filtrar
                  </CButton>
                  <CButton
                    type="button"
                    color="secondary"
                    variant="outline"
                    onClick={handleClearFilters}
                  >
                    Limpar filtros
                  </CButton>
                </div>
              </CCol>
            </CRow>
          </CForm>
        </CCardBody>
      </CCard>

      <CCard className="mb-4">
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando logs de auditoria...</p>
          ) : (
            <>
              <AppTable
                data={sortedLogs}
                columns={columns}
                emptyMessage="Nenhum log de auditoria encontrado."
              />

              <div className="d-flex flex-column flex-sm-row justify-content-between align-items-sm-center gap-3 mt-3">
                <span className="text-body-secondary">
                  Página {page + 1} de {totalPages} — {total} registro(s)
                </span>

                <div className="d-flex gap-2">
                  <CButton
                    color="secondary"
                    variant="outline"
                    disabled={!canGoPrevious}
                    onClick={() => {
                      setIsLoading(true)
                      setPage((current) => current - 1)
                    }}
                  >
                    Anterior
                  </CButton>
                  <CButton
                    color="secondary"
                    variant="outline"
                    disabled={!canGoNext}
                    onClick={() => setPage((current) => current + 1)}
                  >
                    Próxima
                  </CButton>
                </div>
              </div>
            </>
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default AuditLogsList
