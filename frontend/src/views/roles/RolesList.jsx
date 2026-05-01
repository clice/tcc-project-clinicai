/**
 * Listagem de Roles usando mocks.
 *
 * Exibe os perfis cadastrados no sistema e permite acessar
 * visualização, edição e cadastro sem depender do banco.
 */

import React, { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CBadge, CButton, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { roles as rolesMock } from 'src/mocks/data'

const RolesList = () => {
  const [roles] = useState(rolesMock)
  const [error] = useState('')
  const [isLoading] = useState(false)

  const columns = useMemo(
    () => [
      {
        accessorKey: 'name',
        header: 'Nome técnico',
      },
      {
        accessorKey: 'display_name',
        header: 'Nome de exibição',
      },
      {
        accessorKey: 'description',
        header: 'Descrição',
        cell: ({ row }) => row.original.description || '-',
      },
      {
        accessorKey: 'permissionsCount',
        header: 'Permissões',
        cell: ({ row }) => (
          <CBadge color="info">
            {row.original.permissionsCount ?? 0}
          </CBadge>
        ),
      },
      {
        accessorKey: 'updated_at',
        header: 'Atualizado em',
      },
      {
        id: 'actions',
        header: 'Ações',
        enableSorting: false,
        cell: ({ row }) => (
          <AppActionButtons
            viewTo={`/roles/${row.original.id}`}
            editTo={`/roles/${row.original.id}/edit`}
          />
        ),
      },
    ],
    [],
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

        <CButton color="primary" size="lg" as={Link} to="/roles/create">
          Cadastrar Perfil
        </CButton>
      </div>

      <CCard>
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando perfis...</p>
          ) : (
            <AppTable
              data={roles}
              columns={columns}
              emptyMessage="Nenhum perfil encontrado."
            />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default RolesList