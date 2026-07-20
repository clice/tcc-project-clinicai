/**
 * Listagem de perfis.
 *
 * Exibe os perfis cadastrados no sistema e permite acessar
 * visualização, edição e cadastro sem depender do banco.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { CAlert, CCard, CCardBody, CSpinner } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { roleService } from 'src/services/roleService'

import { canManageRoles } from 'src/utils/permissions'
import { getErrorMessage } from 'src/utils/errors'

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
      setRoles(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(getErrorMessage(err, 'Erro ao carregar os perfis.'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadRoles()
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
        {/* Botão "Cadastrar Perfil" removido: os 3 perfis oficiais
            (admin_master, doctor, clinic_manager) são um enum fechado no
            backend e já vêm seedados — qualquer tentativa de criação
            resultaria em duplicidade ou em um nome fora do enum. Os
            perfis existentes continuam editáveis (nome de exibição,
            descrição e matriz de permissões). */}
      </div>

      <CCard className="mb-4">
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          {isLoading ? (
            <div className="d-flex justify-content-center py-5">
              <CSpinner />              
            </div>
          ) : (
            <AppTable data={roles} columns={columns} emptyMessage="Nenhum perfil encontrado." />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default RolesList