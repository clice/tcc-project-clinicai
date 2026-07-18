/**
 * Listagem de usuários.
 *
 * Exibe os usuários cadastrados no sistema e permite acessar
 * visualização, edição e cadastro.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CBadge, CButton, CCard, CCardBody, CSpinner } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppTabs from 'src/components/shared/AppTabs'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { userService } from 'src/services/userService'

import { formatCpfBR, formatDateTimeBR } from 'src/utils/formatters'
import { getErrorMessage } from 'src/utils/errors'
import { getActionAccess } from 'src/utils/actionPermissions.mjs'
import { hasPermission } from 'src/utils/permissions'

const userTabs = [
  { key: 'active', label: 'Ativos' },
  { key: 'inactive', label: 'Inativos' },
]

const roleBadgeColors = {
  admin_master: 'danger',
  doctor: 'primary',
  clinic_staff: 'info',
}

const UsersList = () => {
  const { user } = useAuth()
  const { showSuccess, showError } = useFeedback()

  const [activeTab, setActiveTab] = useState('active')
  const [users, setUsers] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  const { canView, canCreate, canEdit, canChangeStatus } = getActionAccess('users', (permission) =>
    hasPermission(user, permission),
  )

  const loadUsers = useCallback(async () => {
    try {
      setIsLoading(true)
      showError('')

      const data = await userService.list()
      setUsers(Array.isArray(data) ? data : [])
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao carregar os usuários.'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadUsers()
  }, [loadUsers])

  /**
   * Separa usuários por status para alimentar as abas.
   */
  const filteredUsers = useMemo(() => {
    return users.filter((item) => item.status_name === activeTab)
  }, [users, activeTab])

  /**
   * Conta registros por aba.
   */
  const tabCounts = useMemo(
    () => ({
      active: users.filter((item) => item.status_name === 'active').length,
      inactive: users.filter((item) => item.status_name === 'inactive').length,
    }),
    [users],
  )

  /**
   * Mudança de status do usuário.
   */
  const handleChangeStatus = async (user) => {
    try {
      showError('')

      if (user.status_name === 'active') {
        await userService.inactivate(user.id)
        showSuccess('Usuário inativado com sucesso.')
      } else {
        await userService.activate(user.id)
        showSuccess('Usuário ativado com sucesso.')
      }

      await loadUsers()
    } catch (err) {
      showError(err.response?.data?.detail || 'Erro ao alterar status do usuário.')
    }
  }

  const columns = useMemo(
    () => [
      { accessorKey: 'name', header: 'Nome' },
      { accessorKey: 'email', header: 'E-mail' },
      {
        accessorKey: 'cpf',
        header: 'CPF',
        cell: ({ getValue }) => {
          const value = getValue()
          return value ? formatCpfBR(value) : '-'
        },
      },
      {
        accessorKey: 'role_display_name',
        header: 'Perfil',
        cell: ({ getValue, row }) => {
          const label = getValue() || row.original.role_name || '-'
          const roleName = row.original.role_name

          return <CBadge color={roleBadgeColors[roleName] || 'secondary'}>{label}</CBadge>
        },
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
              canView={canView}
              canEdit={canEdit}
              canInactivate={canChangeStatus && !isInactive && selectedUser.id !== user?.id}
              canActivate={canChangeStatus && isInactive}
              onInactivate={() => handleChangeStatus(selectedUser)}
              onActivate={() => handleChangeStatus(selectedUser)}
            />
          )
        },
      },
    ],
    [canView, canEdit, canChangeStatus, loadUsers, user?.id],
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

        {canCreate && (
          <div className="d-flex justify-content-center mt-4">
            <CButton color="primary" size="lg" as={Link} to="/users/create">
              Cadastrar Usuário
            </CButton>
          </div>
        )}
      </div>

      <CCard className="mb-4">
        <CCardBody>
          {isLoading ? (
            <div className="d-flex justify-content-center py-5">
              <CSpinner />
            </div>
          ) : (
            <>
              <AppTabs
                tabs={userTabs}
                counts={tabCounts}
                activeTab={activeTab}
                onChange={setActiveTab}
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
