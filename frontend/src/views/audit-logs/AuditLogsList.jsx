/**
 * Listagem de logs de auditoria usando mocks.
 *
 * Exibe eventos importantes do sistema, como alterações,
 * cadastros, acessos e ações administrativas.
 */

import React, { useMemo, useState } from 'react'
import { CAlert, CBadge, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import { auditLogs as auditLogsMock } from 'src/mocks/data'

const entityLabels = {
  users: 'Usuários',
  clinics: 'Clínicas',
  patients: 'Pacientes',
  exams: 'Exames',
  roles: 'Perfis',
  permissions: 'Permissões',
  statuses: 'Status',
  auth: 'Autenticação',
}

const actionLabels = {
  'users:create': 'Cadastro de usuário',
  'users:update': 'Edição de usuário',
  'users:inactive': 'Inativação de usuário',
  'users:active': 'Ativação de usuário',

  'clinics:create': 'Cadastro de clínica',
  'clinics:update': 'Edição de clínica',
  'clinics:inactive': 'Inativação de clínica',
  'clinics:active': 'Ativação de clínica',

  'patients:create': 'Cadastro de paciente',
  'patients:update': 'Edição de paciente',
  'patients:inactive': 'Inativação de paciente',
  'patients:active': 'Ativação de paciente',

  'exams:create': 'Cadastro de exame',
  'exams:update': 'Edição de exame',
  'exams:cancel': 'Cancelamento de exame',

  'roles:create': 'Cadastro de perfil',
  'roles:update': 'Edição de perfil',

  'permissions:create': 'Cadastro de permissão',
  'permissions:update': 'Edição de permissão',

  'statuses:create': 'Cadastro de status',
  'statuses:update': 'Edição de status',

  'auth:login': 'Login',
  'auth:logout': 'Logout',
  'auth:failed_login': 'Falha de login',
}

const actionColors = {
  create: 'success',
  update: 'info',
  inactive: 'warning',
  active: 'success',
  cancel: 'danger',
  login: 'success',
  logout: 'secondary',
  failed_login: 'danger',
}

const formatDateTimeBR = (value) => {
  if (!value) return '-'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return '-'

  return `${date.toLocaleDateString('pt-BR')} às ${date.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  })}`
}

const getActionColor = (action) => {
  const actionType = action?.split(':')[1]

  return actionColors[actionType] || 'secondary'
}

const AuditLogsList = () => {
  const [auditLogs] = useState(auditLogsMock)
  const [error] = useState('')
  const [isLoading] = useState(false)

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
        accessorKey: 'clinic_name',
        header: 'Clínica',
        cell: ({ getValue }) => getValue() || '-',
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