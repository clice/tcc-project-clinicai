/**
 * Listagem de pacientes.
 *
 * Exibe os pacientes cadastrados no sistema e permite acessar
 * visualização, edição e cadastro sem depender do banco.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CButton, CCard, CCardBody, CSpinner } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppTabs from 'src/components/shared/AppTabs'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { patientService } from 'src/services/patientService'

import { calculateAge } from 'src/utils/calculators'
import { formatCpfBR, formatPhoneBR, formatSex } from 'src/utils/formatters'
import { canManagePatients } from 'src/utils/permissions'

const patientTabs = [
  { key: 'active', label: 'Ativos' },
  { key: 'inactive', label: 'Inativos' },
]

const getErrorMessage = (error, fallback) => {
  const detail = error.response?.data?.detail

  if (typeof detail === 'string') return detail

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(' ')
  }

  return error.message || fallback
}

const PatientsList = () => {
  const { user } = useAuth()

  const [activeTab, setActiveTab] = useState('active')
  const [patients, setPatients] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const canManage = canManagePatients(user)

  const loadPatients = useCallback(async () => {
    try {
      setIsLoading(true)
      setError('')

      const data = await patientService.list({ includeInactive: true })
      setPatients(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(getErrorMessage(err, 'Erro ao carregar os pacientes.'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadPatients()
  }, [loadPatients])

  const handleInactivate = useCallback(
    async (patient) => {
      try {
        setError('')
        await patientService.inactivate(patient.id)
        await loadPatients()
      } catch (err) {
        setError(getErrorMessage(err, 'Erro ao inativar o paciente.'))
      }
    },
    [loadPatients],
  )

  const handleActivate = useCallback(
    async (patient) => {
      try {
        setError('')
        await patientService.activate(patient.id)
        await loadPatients()
      } catch (err) {
        setError(getErrorMessage(err, 'Erro ao ativar o paciente.'))
      }
    },
    [loadPatients],
  )

  const filteredPatients = useMemo(() => {
    if (activeTab === 'all') {
      return patients
    }

    return patients.filter((patient) => patient.status_name === activeTab)
  }, [patients, activeTab])

  const counts = useMemo(
    () => ({
      active: patients.filter((patient) => patient.status_name === 'active').length,
      inactive: patients.filter((patient) => patient.status_name === 'inactive').length,
      all: patients.length,
    }),
    [patients],
  )

  const columns = useMemo(
    () => [
      { accessorKey: 'name', header: 'Paciente' },
      { accessorKey: 'cpf', header: 'CPF', cell: ({ getValue }) => formatCpfBR(getValue()) || '-' },
      { accessorKey: 'birth_date', header: 'Idade', cell: ({ getValue }) => calculateAge(getValue()) },
      { accessorKey: 'sex', header: 'Sexo', cell: ({ getValue }) => formatSex(getValue()) },
      { accessorKey: 'phone', header: 'Telefone', cell: ({ getValue }) => formatPhoneBR(getValue()) || '-' },
      { accessorKey: 'doctor_name', header: 'Médico', cell: ({ getValue }) => getValue() || '-' },
      { accessorKey: 'clinic_name', header: 'Clínica', cell: ({ getValue }) => getValue() || '-' },
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
              canView={canManage}
              canEdit={canManage}
              canInactivate={canManage && !isInactive}
              canActivate={canManage && isInactive}
              onInactivate={() => handleInactivate(patient)}
              onActivate={() => handleActivate(patient)}
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
          <div className="text-body-secondary">Registros de Saúde</div>
          <h1 className="h3 mb-0">Pacientes</h1>
          <p className="text-body-secondary mb-0">
            Gerencie pacientes vinculados às clínicas e aos médicos responsáveis.
          </p>
        </div>

        <div className="d-flex justify-content-center mt-4">
          <CButton color="primary" size="lg" as={Link} to="/patients/create">
            Cadastrar Paciente
          </CButton>
        </div>  
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
              <AppTabs activeTab={activeTab} counts={counts} onChange={setActiveTab} tabs={patientTabs} />
              <AppTable data={filteredPatients} columns={columns} emptyMessage="Nenhum paciente encontrado." />
            </>
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default PatientsList