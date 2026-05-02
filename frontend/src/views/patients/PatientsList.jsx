/**
 * Listagem de pacientes usando mocks.
 */

import React, { useCallback, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CButton, CCard, CCardBody, CSpinner } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppTabs from 'src/components/shared/AppTabs'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { formatCpfBR, formatPhoneBR } from 'src/utils/formatters'
import { patients as patientsMock } from 'src/mocks/data'

const patientTabs = [
  { key: 'active', label: 'Ativos' },
  { key: 'inactive', label: 'Inativos' },
]

const calculateAge = (birthDate) => {
  if (!birthDate) return '-'

  const date = new Date(birthDate)

  if (Number.isNaN(date.getTime())) return '-'

  const today = new Date()
  let age = today.getFullYear() - date.getFullYear()
  const monthDifference = today.getMonth() - date.getMonth()

  if (
    monthDifference < 0 ||
    (monthDifference === 0 && today.getDate() < date.getDate())
  ) {
    age -= 1
  }

  return age
}

const formatSex = (value) => {
  const labels = {
    female: 'Feminino',
    male: 'Masculino',
    other: 'Outro',
  }

  return labels[value] || '-'
}

const PatientsList = () => {
  const [activeTab, setActiveTab] = useState('active')
  const [patients, setPatients] = useState(patientsMock)
  const [error, setError] = useState('')
  const [isLoading] = useState(false)

  const handleInactivate = useCallback((patient) => {
    setError('')

    setPatients((current) =>
      current.map((item) =>
        String(item.id) === String(patient.id)
          ? {
              ...item,
              status_id: '6',
              status_name: 'inactive',
              status_display_name: 'Inativo',
              updated_at: new Date().toISOString(),
            }
          : item,
      ),
    )
  }, [])

  const handleActivate = useCallback((patient) => {
    setError('')

    setPatients((current) =>
      current.map((item) =>
        String(item.id) === String(patient.id)
          ? {
              ...item,
              status_id: '5',
              status_name: 'active',
              status_display_name: 'Ativo',
              updated_at: new Date().toISOString(),
            }
          : item,
      ),
    )
  }, [])

  const filteredPatients = useMemo(() => {
    return patients.filter((patient) => patient.status_name === activeTab)
  }, [patients, activeTab])

  const counts = useMemo(
    () => ({
      active: patients.filter((patient) => patient.status_name === 'active').length,
      inactive: patients.filter((patient) => patient.status_name === 'inactive').length,
    }),
    [patients],
  )

  const columns = useMemo(
    () => [
      {
        accessorKey: 'name',
        header: 'Paciente',
      },
      {
        accessorKey: 'cpf',
        header: 'CPF',
        cell: ({ getValue }) => formatCpfBR(getValue()) || '-',
      },
      {
        accessorKey: 'birth_date',
        header: 'Idade',
        cell: ({ getValue }) => calculateAge(getValue()),
      },
      {
        accessorKey: 'sex',
        header: 'Sexo',
        cell: ({ getValue }) => formatSex(getValue()),
      },
      {
        accessorKey: 'phone',
        header: 'Telefone',
        cell: ({ getValue }) => formatPhoneBR(getValue()) || '-',
      },
      {
        accessorKey: 'doctor_name',
        header: 'Médico',
        cell: ({ getValue }) => getValue() || '-',
      },
      {
        accessorKey: 'clinic_name',
        header: 'Clínica',
        cell: ({ getValue }) => getValue() || '-',
      },
      {
        id: 'actions',
        header: 'Ações',
        enableSorting: false,
        cell: ({ row }) => {
          const patient = row.original
          const isInactive = patient.status_name === 'inactive'

          return (
            <AppActionButtons
              itemLabel={patient.name}
              viewTo={`/patients/${patient.id}`}
              editTo={`/patients/${patient.id}/edit`}
              isInactive={isInactive}
              onInactivate={() => handleInactivate(patient)}
              onActivate={() => handleActivate(patient)}
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
          <div className="text-body-secondary">Registros de Saúde</div>
          <h1 className="h3 mb-0">Pacientes</h1>
          <p className="text-body-secondary mb-0">
            Gerencie pacientes vinculados às clínicas e aos médicos responsáveis.
          </p>
        </div>

        <CButton color="primary" size="lg" as={Link} to="/patients/create">
          Cadastrar Paciente
        </CButton>
      </div>

      <CCard>
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          {isLoading ? (
            <div className="d-flex justify-content-center py-5">
              <CSpinner />
            </div>
          ) : (
            <>
              <AppTabs
                activeTab={activeTab}
                counts={counts}
                onChange={setActiveTab}
                tabs={patientTabs}
              />

              <AppTable
                data={filteredPatients}
                columns={columns}
                emptyMessage="Nenhum paciente encontrado."
              />
            </>
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default PatientsList