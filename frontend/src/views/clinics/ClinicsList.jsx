/**
 * Listagem de clínicas usando mocks.
 */

import React, { useCallback, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CButton, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppTabs from 'src/components/shared/AppTabs'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { clinics as clinicsMock } from 'src/mocks/data'
import { formatCnpjBR } from 'src/utils/formatters'

const clinicTabs = [
  { key: 'active', label: 'Ativas' },
  { key: 'inactive', label: 'Inativas' },
]

const ClinicsList = () => {
  const [clinics, setClinics] = useState(clinicsMock)
  const [activeTab, setActiveTab] = useState('active')
  const [error, setError] = useState('')
  const [isLoading] = useState(false)

  const filteredClinics = useMemo(() => {
    return clinics.filter((clinic) => clinic.status_name === activeTab)
  }, [clinics, activeTab])

  const tabCounts = useMemo(() => {
    return {
      active: clinics.filter((clinic) => clinic.status_name === 'active').length,
      inactive: clinics.filter((clinic) => clinic.status_name === 'inactive').length,
    }
  }, [clinics])

  const handleChangeStatus = useCallback((clinic) => {
    setError('')

    const nextStatus =
      clinic.status_name === 'active'
        ? {
            status_id: '4',
            status_name: 'inactive',
            status_display_name: 'Inativa',
          }
        : {
            status_id: '3',
            status_name: 'active',
            status_display_name: 'Ativa',
          }

    setClinics((current) =>
      current.map((item) =>
        String(item.id) === String(clinic.id)
          ? {
              ...item,
              ...nextStatus,
              updated_at: new Date().toISOString(),
            }
          : item,
      ),
    )
  }, [])

  const columns = useMemo(
    () => [
      {
        accessorKey: 'name',
        header: 'Nome',
      },
      {
        accessorKey: 'cnpj',
        header: 'CNPJ',
        cell: ({ getValue }) => formatCnpjBR(getValue()) || '-',
      },
      {
        accessorKey: 'city',
        header: 'Cidade',
        cell: ({ getValue }) => getValue() || '-',
      },
      {
        accessorKey: 'state',
        header: 'UF',
        cell: ({ getValue }) => getValue() || '-',
      },
      {
        accessorKey: 'status_display_name',
        header: 'Status',
        cell: ({ getValue }) => getValue() || '-',
      },
      {
        id: 'actions',
        header: 'Ações',
        enableSorting: false,
        cell: ({ row }) => {
          const clinic = row.original
          const isInactive = clinic.status_name === 'inactive'

          return (
            <AppActionButtons
              itemLabel={clinic.name}
              viewTo={`/clinics/${clinic.id}`}
              editTo={`/clinics/${clinic.id}/edit`}
              isInactive={isInactive}
              onInactivate={() => handleChangeStatus(clinic)}
              onActivate={() => handleChangeStatus(clinic)}
            />
          )
        },
      },
    ],
    [handleChangeStatus],
  )

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Administração</div>
          <h1 className="h3 mb-0">Clínicas</h1>
          <p className="text-body-secondary mb-0">
            Gerencie clínicas vinculadas aos usuários, pacientes e exames.
          </p>
        </div>

        <CButton color="primary" size="lg" as={Link} to="/clinics/create">
          Cadastrar Clínica
        </CButton>
      </div>

      <CCard>
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          <AppTabs
            tabs={clinicTabs}
            activeTab={activeTab}
            counts={tabCounts}
            onChange={setActiveTab}
          />

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando clínicas...</p>
          ) : (
            <AppTable
              data={filteredClinics}
              columns={columns}
              emptyMessage="Nenhuma clínica encontrada."
            />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default ClinicsList