/**
 * Listagem de usuários usando mocks.
 */

import React, { useCallback, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CButton, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppTabs from 'src/components/shared/AppTabs'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { formatPhoneBR } from 'src/utils/formatters'
import { users as usersMock } from 'src/mocks/data'

const formatDateTimeBR = (value) => {
  if (!value) return '-'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return '-'

  return `${date.toLocaleDateString('pt-BR')} às ${date.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  })}`
}

const userTabs = [
  { key: 'active', label: 'Ativos' },
  { key: 'inactive', label: 'Inativos' },
]

const UsersList = () => {
  const [activeTab, setActiveTab] = useState('active')
  const [users, setUsers] = useState(usersMock)
  const [error, setError] = useState('')
  const [isLoading] = useState(false)

  const handleInactivate = useCallback((selectedUser) => {
    setError('')

    setUsers((current) =>
      current.map((item) =>
        String(item.id) === String(selectedUser.id)
          ? {
              ...item,
              status_id: '2',
              status_name: 'inactive',
              status_display_name: 'Inativo',
              updated_at: new Date().toISOString(),
            }
          : item,
      ),
    )
  }, [])

  const handleActivate = useCallback((selectedUser) => {
    setError('')

    setUsers((current) =>
      current.map((item) =>
        String(item.id) === String(selectedUser.id)
          ? {
              ...item,
              status_id: '1',
              status_name: 'active',
              status_display_name: 'Ativo',
              updated_at: new Date().toISOString(),
            }
          : item,
      ),
    )
  }, [])

  const filteredUsers = useMemo(() => {
    return users.filter((item) => item.status_name === activeTab)
  }, [users, activeTab])

  const counts = useMemo(
    () => ({
      active: users.filter((item) => item.status_name === 'active').length,
      inactive: users.filter((item) => item.status_name === 'inactive').length,
    }),
    [users],
  )

  const columns = useMemo(
    () => [
      {
        accessorKey: 'name',
        header: 'Nome',
      },
      {
        accessorKey: 'email',
        header: 'E-mail',
      },
      {
        accessorKey: 'phone',
        header: 'Telefone',
        cell: ({ getValue }) => formatPhoneBR(getValue()) || '-',
      },
      {
        accessorKey: 'role_display_name',
        header: 'Perfil',
        cell: ({ getValue, row }) => getValue() || row.original.role_name || '-',
      },
      {
        accessorKey: 'clinic_name',
        header: 'Clínica',
        cell: ({ getValue }) => getValue() || '-',
      },
      {
        accessorKey: 'last_access_at',
        header: 'Último acesso',
        cell: ({ getValue }) => formatDateTimeBR(getValue()),
      },
      {
        id: 'actions',
        header: 'Ações',
        enableSorting: false,
        cell: ({ row }) => {
          const selectedUser = row.original
          const isInactive = selectedUser.status_name === 'inactive'

          return (
            <AppActionButtons
              itemLabel={selectedUser.name}
              viewTo={`/users/${selectedUser.id}`}
              editTo={`/users/${selectedUser.id}/edit`}
              isInactive={isInactive}
              onInactivate={() => handleInactivate(selectedUser)}
              onActivate={() => handleActivate(selectedUser)}
            />
          )
        },
      },
    ],
    [handleActivate, handleInactivate],
  )

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Controle de Acesso</div>
          <h1 className="h3 mb-0">Usuários</h1>
          <p className="text-body-secondary mb-0">
            Gerencie usuários, perfis de acesso, status e vínculo com clínicas.
          </p>
        </div>

        <CButton color="primary" size="lg" as={Link} to="/users/create">
          Cadastrar Usuário
        </CButton>
      </div>

      <CCard>
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando usuários...</p>
          ) : (
            <>
              <AppTabs
                activeTab={activeTab}
                counts={counts}
                onChange={setActiveTab}
                tabs={userTabs}
              />

              <AppTable
                data={filteredUsers}
                columns={columns}
                emptyMessage="Nenhum usuário encontrado."
              />
            </>
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default UsersList