/**
 * Listagem de usuários.
 *
 * Exibe os usuários cadastrados no sistema e permite acessar
 * visualização, edição e cadastro sem depender do banco.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CButton, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppTabs from 'src/components/shared/AppTabs'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { userService } from 'src/services/userService'

import { formatCpfBR, formatDateTimeBR, formatPhoneBR } from 'src/utils/formatters'
import { canManageUsers } from 'src/utils/permissions'

const userTabs = [
  { key: 'active', label: 'Ativos' },
  { key: 'inactive', label: 'Inativos' },
]

const UsersList = () => {
  const { user } = useAuth()

  const [activeTab, setActiveTab] = useState('active')
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const canManage = canManageUsers(user)

  const loadUsers = useCallback(async () => {
    try {
      setIsLoading(true)
      setError('')

      const data = await userService.list()
      setUsers(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Erro ao carregar os usuários.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadUsers()
  }, [loadUsers])

  const handleInactivate = useCallback(
    async (selectedUser) => {
      try {
        setError('')
        await userService.inactivate(selectedUser.id)
        await loadUsers()
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Erro ao inativar o usuário.')
      }
    },
    [loadUsers],
  )

  const handleActivate = useCallback(
    async (selectedUser) => {
      try {
        setError('')
        await userService.activate(selectedUser.id)
        await loadUsers()
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Erro ao ativar o usuário.')
      }
    },
    [loadUsers],
  )

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
      { accessorKey: 'name', header: 'Nome' },
      { accessorKey: 'email', header: 'E-mail' },
      { accessorKey: 'phone', header: 'Telefone', cell: ({ getValue }) => {
  const value = getValue()
  console.log('PHONE VALUE:', value)
  return value ? formatPhoneBR(value) : '-'
} },
      { accessorKey: 'role_display_name', header: 'Perfil', cell: ({ getValue, row }) => getValue() || row.original.role_name || '-' },
      { accessorKey: 'clinic_name', header: 'Clínica', cell: ({ getValue }) => getValue() || '-' },
      { accessorKey: 'last_access_at', header: 'Último acesso', cell: ({ getValue }) => formatDateTimeBR(getValue()) },
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
              canView={canManage}
              canEdit={canManage}
              canInactivate={canManage && !isInactive}
              canActivate={canManage && isInactive}
              onInactivate={() => handleInactivate(selectedUser)}
              onActivate={() => handleActivate(selectedUser)}
            />
          )
        },
      },
    ],
    [canManage, handleActivate, handleInactivate],
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

        <div className="d-flex justify-content-center mt-4">
          <CButton color="primary" size="lg" as={Link} to="/users/create">
            Cadastrar Usuário
          </CButton>
        </div>
      </div>

      <CCard>
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando usuários...</p>
          ) : (
            <>
              <AppTabs activeTab={activeTab} counts={counts} onChange={setActiveTab} tabs={userTabs} />
              <AppTable data={filteredUsers} columns={columns} emptyMessage="Nenhum usuário encontrado." />
            </>
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default UsersList