/**
 * Listagem de statuses.
 *
 * Exibe os statuses cadastrados no sistema e permite acessar
 * visualização, edição e cadastro sem depender do banco.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { CAlert, CBadge, CCard, CCardBody, CSpinner } from '@coreui/react'

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
        {/* Botão "Cadastrar Status" removido: os pares (name, applies_to)
            válidos são uma matriz fechada (ver ALLOWED_STATUS_BY_SCOPE no
            backend) e já vêm todos seedados — criar um novo só permitiria
            duplicatas ou combinações inválidas. Os status existentes
            continuam editáveis (nome de exibição e descrição). */}
      </div>

      <CCard>
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          {isLoading ? (
            <div className="d-flex justify-content-center py-5">
              <CSpinner />              
            </div>
          ) : (
            <AppTable data={statuses} columns={columns} placeholder="Filtrar status" />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default StatusesList