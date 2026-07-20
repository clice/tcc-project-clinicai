/**
 * Listagem de pacientes.
 *
 * Exibe os pacientes cadastrados no sistema e permite acessar
 * visualização, edição e cadastro sem depender do banco.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CButton, CCard, CCardBody, CSpinner } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppTabs from 'src/components/shared/AppTabs'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { useFeedback } from 'src/hooks/useFeedback'

import { patientService } from 'src/services/patientService'

import { getErrorMessage } from 'src/utils/errors'
import { formatCpfBR, formatPhoneBR } from 'src/utils/formatters'
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
  const [isLoading, setIsLoading] = useState(true)

  const roleName = getUserRole(user)
  const showDoctorColumn = roleName !== ROLES.DOCTOR
  const showClinicColumn = roleName === ROLES.ADMIN_MASTER

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
  }, [showError])

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadPatients()
    }, 0)

    return () => {
      window.clearTimeout(timeoutId)
    }
  }, [loadPatients])

  /**
   * Separa pacientes por status para alimentar as abas.
   */
  const filteredPatients = useMemo(
    () => patients.filter((patient) => patient.status_name === activeTab),
    [patients, activeTab],
  )

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
  const handleChangeStatus = useCallback(
    async (patient) => {
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
    },
    [loadPatients, showError, showSuccess],
  )

  const columns = useMemo(
    () => [
      { accessorKey: 'name', header: 'Paciente' },
      { accessorKey: 'cpf', header: 'CPF', cell: ({ getValue }) => formatCpfBR(getValue()) || '-' },
      {
        accessorKey: 'phone',
        header: 'Telefone',
        cell: ({ getValue }) => formatPhoneBR(getValue()) || '-',
      },
      ...(showDoctorColumn
        ? [
            {
              accessorKey: 'doctor_name',
              header: 'Médico',
              cell: ({ getValue }) => getValue() || '-',
            },
          ]
        : []),
      ...(showClinicColumn
        ? [
            {
              accessorKey: 'clinic_name',
              header: 'Clínica',
              cell: ({ getValue }) => getValue() || '-',
            },
          ]
        : []),
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
    [canView, canEdit, canChangeStatus, handleChangeStatus, showClinicColumn, showDoctorColumn],
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
              : roleName === ROLES.CLINIC_MANAGER
                ? 'Visualize os pacientes vinculados à sua clínica.'
                : 'Gerencie pacientes de todas as clínicas conforme os filtros.'}
          </p>
        </div>

        {canCreate && (
          <div className="d-flex justify-content-center mt-4">
            <CButton
              color="primary"
              className="clinicai-btn"
              size="lg"
              as={Link}
              to="/patients/create"
            >
              Cadastrar Paciente
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
