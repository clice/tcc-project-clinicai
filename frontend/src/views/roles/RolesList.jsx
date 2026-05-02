/**
 * Listagem de perfis.
 *
 * Exibe os perfis cadastrados no sistema e permite acessar
 * visualização, edição e cadastro sem depender do banco.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CButton, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { roleService } from 'src/services/roleService'

import { canManageRoles } from 'src/utils/permissions'

const RolesList = () => {
  const { user } = useAuth()

  const [roles, setRoles] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const canManage = canManageRoles(user)

  const loadRoles = useCallback(async () => {
    try {
      setIsLoading(true)
      setError('')

      const data = await roleService.list()
      setRoles(data)
    } catch (err) {
      setError('Erro ao carregar os perfis.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadRoles()
  }, [loadRoles])

  const columns = useMemo(
    () => [
      { accessorKey: 'name', header: 'Nome técnico' },
      { accessorKey: 'display_name', header: 'Nome de exibição' },
      { accessorKey: 'description', header: 'Descrição' },
      {
        id: 'actions',
        header: 'Ações',
        enableSorting: false,
        cell: ({ row }) => (
          <AppActionButtons
            viewTo={`/roles/${row.original.id}`}
            editTo={`/roles/${row.original.id}/edit`}
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
          <h1 className="h3 mb-0">Perfis</h1>
          <p className="text-body-secondary mb-0">
            Gerencie os perfis de acesso usados no sistema.
          </p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButton color="primary" size="lg" as={Link} to="/roles/create">
            Cadastrar Perfil
          </CButton>
        </div>        
      </div>

      <CCard>
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando perfis...</p>
          ) : (
            <AppTable data={roles} columns={columns} emptyMessage="Nenhum perfil encontrado." />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default RolesList