/**
 * Listagem de logs de auditoria.
 *
 * Exibe eventos importantes do sistema, como alterações,
 * cadastros, acessos e ações administrativas.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { CAlert, CBadge, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'

import { auditLogService } from 'src/services/auditLogService'
import { getErrorMessage } from 'src/utils/errors'
import { formatDateTimeBR } from 'src/utils/formatters'

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
  upload: 'info',
  download: 'secondary',
  run_ai_analysis: 'primary',
}

const getActionColor = (action) => actionColors[action] || 'secondary'

const AuditLogsList = () => {
  const [auditLogs, setAuditLogs] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const loadAuditLogs = useCallback(async () => {
    try {
      setIsLoading(true)
      setError('')

      const data = await auditLogService.list()
      setAuditLogs(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Erro ao carregar logs de auditoria.'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadAuditLogs()
  }, [loadAuditLogs])

  const sortedLogs = useMemo(() => {
    return [...auditLogs].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
  }, [auditLogs])

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
            <AppTable
              data={sortedLogs}
              columns={columns}
              emptyMessage="Nenhum log de auditoria encontrado."
            />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default AuditLogsList