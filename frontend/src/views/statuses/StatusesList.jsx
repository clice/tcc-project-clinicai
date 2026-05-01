import React, { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CBadge, CButton, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { statuses as statusesMock } from 'src/mocks/data'

const appliesToLabels = {
  users: 'Usuários',
  clinics: 'Clínicas',
  patients: 'Pacientes',
  exams: 'Exames',
}

const StatusesList = () => {
  const [statuses] = useState(statusesMock)
  const [error] = useState('')
  const [isLoading] = useState(false)

  const columns = useMemo(
    () => [
      {
        accessorKey: 'name',
        header: 'Nome Técnico',
      },
      {
        accessorKey: 'display_name',
        header: 'Nome de Exibição',
      },
      {
        accessorKey: 'applies_to',
        header: 'Aplicado em',
        cell: ({ row }) => (
          <CBadge color="info" className="text-uppercase">
            {appliesToLabels[row.original.applies_to] || row.original.applies_to}
          </CBadge>
        ),
      },
      {
        accessorKey: 'description',
        header: 'Descrição',
        cell: ({ row }) => row.original.description || '-',
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
            viewTo={`/statuses/${row.original.id}`}
            editTo={`/statuses/${row.original.id}/edit`}
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
          <div className="text-body-secondary">Controle de Acesso</div>
          <h1 className="h3 mb-0">Status do Sistema</h1>
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
            <AppTable
              data={statuses}
              columns={columns}
              placeholder="Filtrar status"
            />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default StatusesList