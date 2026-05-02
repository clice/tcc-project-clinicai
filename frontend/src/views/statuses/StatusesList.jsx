import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CBadge, CButton, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { statusService } from 'src/services/statusService'
import { canManageStatuses } from 'src/utils/permissions'

const StatusesList = () => {
  const { user } = useAuth()

  const [statuses, setStatuses] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const canManage = canManageStatuses(user)

  const loadStatuses = useCallback(async () => {
    try {
      setIsLoading(true)
      setError('')

      const data = await statusService.list()
      setStatuses(data)
    } catch {
      setError('Erro ao carregar os status.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadStatuses()
  }, [loadStatuses])

  const columns = useMemo(
    () => [
      { accessorKey: 'name', header: 'Nome técnico' },
      { accessorKey: 'display_name', header: 'Nome de exibição' },
      { accessorKey: 'applies_to', header: 'Aplicado em' },
      { accessorKey: 'description', header: 'Descrição' },
      {
        id: 'actions',
        header: 'Ações',
        enableSorting: false,
        cell: ({ row }) => (
          <AppActionButtons
            viewTo={`/statuses/${row.original.id}`}
            editTo={`/statuses/${row.original.id}/edit`}
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
          <div className="text-body-secondary">Controle de Acesso</div>
          <h1 className="h3 mb-0">Status</h1>
          <p className="text-body-secondary mb-0">
            Gerencie os estados usados por usuários, clínicas, pacientes e exames.
          </p>
        </div>
        <CButton color="primary" size="lg" as={Link} to="/statuses/create">
          Cadastrar Status
        </CButton>
      </div>

      <CCard>
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando status...</p>
          ) : (
            <AppTable data={statuses} columns={columns} placeholder="Filtrar status" />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default StatusesList