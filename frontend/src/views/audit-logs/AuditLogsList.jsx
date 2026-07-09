/**
 * Listagem de logs de auditoria.
 *
 * Exibe eventos importantes do sistema, como alterações,
 * cadastros, acessos e ações administrativas.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { CAlert, CBadge, CButton, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'

import { auditLogService } from 'src/services/auditLogService'
import { getErrorMessage } from 'src/utils/errors'
import { formatDateTimeBR } from 'src/utils/formatters'

const PAGE_SIZE = 50

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
  logout: 'Logout',
  cancel_exam: 'Cancelamento de exame',
  restore_exam: 'Reprocessamento de exame',
  upload: 'Upload',
  download: 'Download',
  run_ai_analysis: 'Execução de IA',
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
  logout: 'secondary',
  cancel_exam: 'danger',
  restore_exam: 'info',
  upload: 'info',
  download: 'secondary',
  run_ai_analysis: 'primary',
}

const getActionColor = (action) => actionColors[action] || 'secondary'

const AuditLogsList = () => {
  const [auditLogs, setAuditLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const loadAuditLogs = useCallback(async (currentPage) => {
    try {
      setIsLoading(true)
      setError('')

      const data = await auditLogService.list({
        limit: PAGE_SIZE,
        offset: currentPage * PAGE_SIZE,
      })

      setAuditLogs(data.items)
      setTotal(data.total)
    } catch (err) {
      setError(getErrorMessage(err, 'Erro ao carregar logs de auditoria.'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadAuditLogs(page)
  }, [loadAuditLogs, page])

  // A ordenação já vem pronta do backend (mais recentes primeiro);
  // aqui só garantimos isso mesmo se a página atual tiver poucos itens.
  const sortedLogs = useMemo(() => {
    return [...auditLogs].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
  }, [auditLogs])

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const canGoPrevious = page > 0
  const canGoNext = page + 1 < totalPages

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
        accessorKey: 'entity_id',
        header: 'ID Registro',
        cell: ({ getValue }) => getValue() || '-',
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
            Acompanhe ações relevantes realizadas no sistema ClinicAI.
          </p>
        </div>
      </div>

      <CCard>
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

              <div className="d-flex justify-content-between align-items-center mt-3">
                <small className="text-body-secondary">
                  {total > 0
                    ? `Página ${page + 1} de ${totalPages} — ${total} registro(s) no total`
                    : 'Nenhum registro'}
                </small>

                <div className="d-flex gap-2">
                  <CButton
                    color="secondary"
                    variant="outline"
                    size="sm"
                    disabled={!canGoPrevious}
                    onClick={() => setPage((current) => Math.max(0, current - 1))}
                  >
                    Anterior
                  </CButton>

                  <CButton
                    color="secondary"
                    variant="outline"
                    size="sm"
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