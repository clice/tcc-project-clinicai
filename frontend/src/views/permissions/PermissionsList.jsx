/**
 * Listagem do módulo de Permissions.
 *
 * Exibe as permissões cadastradas no sistema e permite acessar
 * visualização, edição e cadastro.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CBadge, CButton, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { permissionService } from 'src/services/permissionService'
import { canManagePermissions } from 'src/utils/permissions'

const moduleLabels = {
  users: 'Usuários',
  clinics: 'Clínicas',
  patients: 'Pacientes',
  exams: 'Exames',
  ai_analysis: 'Análises IA',
  roles: 'Perfis',
  permissions: 'Permissões',
  statuses: 'Status',
  audit_logs: 'Logs de Auditoria',
}

const PermissionsList = () => {
  const { user } = useAuth()

  const [permissions, setPermissions] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const canManage = canManagePermissions(user)

  const loadPermissions = useCallback(async () => {
    try {
      setIsLoading(true)
      setError('')

      const data = await permissionService.list()
      setPermissions(data)
    } catch (err) {
      setError('Erro ao carregar as permissões.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadPermissions()
  }, [loadPermissions])

  const columns = useMemo(
    () => [
      { accessorKey: 'name', header: 'Nome técnico' },
      { accessorKey: 'display_name', header: 'Nome de exibição' },
      { accessorKey: 'description', header: 'Descrição' },
      {
        accessorKey: 'module',
        header: 'Módulo',
        cell: ({ getValue }) => moduleLabels[getValue()] || getValue(),
      },
      {
        id: 'actions',
        header: 'Ações',
        enableSorting: false,
        cell: ({ row }) => (
          <AppActionButtons
            viewTo={`/permissions/${row.original.id}`}
            editTo={`/permissions/${row.original.id}/edit`}
            canView={canManage}
            canEdit={canManage}
          />
        ),
      },
    ],
    [canManage],
  )

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Configurações</div>
          <h1 className="h3 mb-0">Permissões</h1>
          <p className="text-body-secondary mb-0">
            Gerencie permissões técnicas usadas no controle de acesso.
          </p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButton color="primary" size="lg" as={Link} to="/permissions/create">
            Cadastrar Permissão
          </CButton>
        </div>         
      </div>

      <CCard>
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando permissões...</p>
          ) : (
            <AppTable data={permissions} columns={columns} emptyMessage="Nenhuma permissão encontrada." />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default PermissionsList