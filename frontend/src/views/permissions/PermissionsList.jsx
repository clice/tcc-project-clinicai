/**
 * Listagem de permissões.
 *
 * Exibe as permissões cadastradas no sistema e permite acessar
 * visualização, edição e cadastro sem depender do banco.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CButton, CCard, CCardBody, CSpinner } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { permissionService } from 'src/services/permissionService'

import { moduleLabels } from 'src/utils/constants'
import { getErrorMessage } from 'src/utils/errors'
import { canManagePermissions } from 'src/utils/permissions'

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
      setPermissions(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(getErrorMessage(err, 'Erro ao carregar as permissões.'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadPermissions()
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
            <div className="d-flex justify-content-center py-5">
              <CSpinner />              
            </div>
          ) : (
            <AppTable
              data={permissions}
              columns={columns}
              emptyMessage="Nenhuma permissão encontrada."
            />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default PermissionsList