/**
 * Listagem de pacientes.
 *
 * Exibe os pacientes cadastrados no sistema e permite acessar
 * visualização, edição e cadastro sem depender do banco.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CButton, CCard, CCardBody, CFormInput, CSpinner } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppTabs from 'src/components/shared/AppTabs'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { patientService } from 'src/services/patientService'

import { calculateAge } from 'src/utils/calculators'
import { getErrorMessage } from 'src/utils/errors'
import { formatCpfBR, formatPhoneBR, formatSex } from 'src/utils/formatters'
import { getActionAccess } from 'src/utils/actionPermissions.mjs'
import { getUserRole, hasPermission, ROLES } from 'src/utils/permissions'

const patientTabs = [
  { key: 'active', label: 'Ativos' },
  { key: 'inactive', label: 'Inativos' },
]

const PatientsList = () => {
  const { user } = useAuth()
  const { showSuccess, showError } = useFeedback()

  const [activeTab, setActiveTab] = useState('active')
  const [patients, setPatients] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const roleName = getUserRole(user)
  const { canView, canCreate, canEdit, canChangeStatus } = getActionAccess(
    'patients',
    (permission) => hasPermission(user, permission),
  )

  const loadPatients = useCallback(async () => {
    try {
      setIsLoading(true)
      showError('')

      const data = await patientService.list({ includeInactive: true })
      setPatients(Array.isArray(data) ? data : [])
    } catch (err) {
      showError(getErrorMessage(err, 'Erro ao carregar pacientes.'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadPatients()
  }, [loadPatients])

  /**
   * Separa pacientes por status para alimentar as abas.
   */
  const filteredPatients = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLocaleLowerCase('pt-BR')

    return patients.filter((patient) => {
      if (patient.status_name !== activeTab) return false
      if (!normalizedSearch) return true

      return [
        patient.name,
        patient.cpf,
        patient.doctor_name,
        patient.clinic_name,
      ].some((value) => String(value || '').toLocaleLowerCase('pt-BR').includes(normalizedSearch))
    })
  }, [patients, activeTab, searchTerm])

  /**
   * Conta registros por aba.
   */
  const tabCounts = useMemo(
    () => ({
      active: patients.filter((patient) => patient.status_name === 'active').length,
      inactive: patients.filter((patient) => patient.status_name === 'inactive').length,
    }),
    [patients],
  )

  /**
   * Mudança de status do paciente.
   */
  const handleChangeStatus = async (patient) => {
    try {
      showError('')

      if (patient.status_name === 'active') {
        await patientService.inactivate(patient.id)
        showSuccess('Paciente inativado com sucesso.')
      } else {
        await patientService.activate(patient.id)
        showSuccess('Paciente ativado com sucesso.')
      }

      await loadPatients()
    } catch (err) {
      showError(err.response?.data?.detail || 'Erro ao alterar status do paciente.')
    }
  }

  const columns = useMemo(
    () => [
      { accessorKey: 'name', header: 'Paciente' },
      { accessorKey: 'cpf', header: 'CPF', cell: ({ getValue }) => formatCpfBR(getValue()) || '-' },
      {
        accessorKey: 'birth_date',
        header: 'Idade',
        cell: ({ getValue }) => calculateAge(getValue()),
      },
      { accessorKey: 'sex', header: 'Sexo', cell: ({ getValue }) => formatSex(getValue()) },
      {
        accessorKey: 'phone',
        header: 'Telefone',
        cell: ({ getValue }) => formatPhoneBR(getValue()) || '-',
      },
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
              canView={canView}
              canEdit={canEdit}
              canInactivate={canChangeStatus && !isInactive}
              canActivate={canChangeStatus && isInactive}
              onInactivate={() => handleChangeStatus(patient)}
              onActivate={() => handleChangeStatus(patient)}
            />
          )
        },
      },
    ],
    [canView, canEdit, canChangeStatus, loadPatients],
  )

  return (
    <>
      <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
        <div>
          <div className="text-body-secondary">Registros de Saúde</div>
          <h1 className="h3 mb-0">Pacientes</h1>
          <p className="text-body-secondary mb-0">
            {roleName === ROLES.DOCTOR
              ? 'Visualize somente os pacientes sob sua responsabilidade.'
              : roleName === ROLES.CLINIC_STAFF
                ? 'Visualize os pacientes vinculados à sua clínica.'
                : 'Gerencie pacientes de todas as clínicas conforme os filtros.'}
          </p>
        </div>

        {canCreate && (
          <div className="d-flex justify-content-center mt-4">
            <CButton color="primary" size="lg" as={Link} to="/patients/create">
              Cadastrar Paciente
            </CButton>
          </div>
        )}
      </div>

      <CCard>
        <CCardBody>
          {isLoading ? (
            <div className="d-flex justify-content-center py-5">
              <CSpinner />
            </div>
          ) : (
            <>
              <CFormInput
                className="mb-3"
                type="search"
                value={searchTerm}
                placeholder="Buscar por paciente, CPF, médico ou clínica"
                aria-label="Buscar pacientes"
                onChange={(event) => setSearchTerm(event.target.value)}
              />
              <AppTabs
                tabs={patientTabs}
                counts={tabCounts}
                activeTab={activeTab}
                onChange={setActiveTab}
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
