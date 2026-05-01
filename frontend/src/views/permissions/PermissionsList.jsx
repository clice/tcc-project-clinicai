/**
 * Listagem do módulo de Permissions usando mocks.
 */

import React, { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CBadge, CButton, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { permissions as permissionsMock } from 'src/mocks/data'

const moduleLabels = {
  users: 'Usuários',
  clinics: 'Clínicas',
  patients: 'Pacientes',
  exams: 'Exames',
  roles: 'Perfis',
  permissions: 'Permissões',
  statuses: 'Status',
}

const PermissionsList = () => {
  const [permissions] = useState(permissionsMock)
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
        accessorKey: 'module',
        header: 'Módulo',
        cell: ({ getValue }) => (
          <CBadge color="info">
            {moduleLabels[getValue()] || getValue()}
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
            viewTo={`/permissions/${row.original.id}`}
            editTo={`/permissions/${row.original.id}/edit`}
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
          <h1 className="h3 mb-0">Permissões</h1>
          <p className="text-body-secondary mb-0">
            Gerencie permissões técnicas usadas no controle de acesso.
          </p>
        </div>

        <CButton color="primary" size="lg" as={Link} to="/permissions/create">
          Cadastrar Permissão
        </CButton>
      </div>

      <CCard>
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando permissões...</p>
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