/**
 * Listagem de clínicas.
 *
 * Exibe as clínicas cadastradas no sistema e permite acessar
 * visualização, edição e cadastro sem depender do banco.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CAlert, CButton, CCard, CCardBody } from '@coreui/react'

import AppTable from 'src/components/shared/AppTable'
import AppTabs from 'src/components/shared/AppTabs'
import AppActionButtons from 'src/components/shared/AppActionButtons'

import { useAuth } from 'src/hooks/useAuth'
import { clinicService } from 'src/services/clinicService'

import { formatCnpjBR } from 'src/utils/formatters'
import { canManageClinics } from 'src/utils/permissions'

const clinicTabs = [
  { key: 'active', label: 'Ativas' },
  { key: 'inactive', label: 'Inativas' },
]

const ClinicsList = () => {
  const { user } = useAuth()

  const [clinics, setClinics] = useState([])
  const [activeTab, setActiveTab] = useState('active')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const canManage = canManageClinics(user)

  const loadClinics = useCallback(async () => {
    try {
      setIsLoading(true)
      setError('')

      const data = await clinicService.list({ includeInactive: true })
      setClinics(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao carregar clínicas.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadClinics()
  }, [loadClinics])

  /**
   * Separa clínicas por status para alimentar as abas.
   */
  const filteredClinics = useMemo(() => {
    return clinics.filter((clinic) => clinic.status_name === activeTab)
  }, [clinics, activeTab])

  /**
   * Conta registros por aba.
   */
  const tabCounts = useMemo(() => {
    return {
      active: clinics.filter((clinic) => clinic.status_name === 'active').length,
      inactive: clinics.filter((clinic) => clinic.status_name === 'inactive').length,
    }
  }, [clinics])

  const handleChangeStatus = async (clinic) => {
    try {
      setError('')

      if (clinic.status_name === 'active') {
        await clinicService.inactivate(clinic.id)
      } else {
        await clinicService.activate(clinic.id)
      }

      await loadClinics()
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao alterar status da clínica.')
    }
  }

  const columns = useMemo(
    () => [
      { accessorKey: 'name', header: 'Nome' },
      { accessorKey: 'cnpj', header: 'CNPJ', cell: ({ getValue }) => formatCnpjBR(getValue()) || '-' },
      { accessorKey: 'city', header: 'Cidade', cell: ({ getValue }) => getValue() || '-' },
      { accessorKey: 'state', header: 'UF', cell: ({ getValue }) => getValue() || '-' },
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
              canView={canManage}
              canEdit={canManage}
              canInactivate={canManage && !isInactive}
              canActivate={canManage && isInactive}
              onInactivate={() => handleChangeStatus(clinic)}
              onActivate={() => handleChangeStatus(clinic)}
            />
          )
        },
      },
    ],
    [canManage, loadClinics],
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

        {canManage && (
          <div className="d-flex justify-content-center mt-4">
            <CButton color="primary" size="lg" as={Link} to="/clinics/create">
              Cadastrar Clínica
            </CButton>
          </div>
        )}       
      </div>

      <CCard>
        <CCardBody>
          {error && <CAlert color="danger">{error}</CAlert>}

          <AppTabs tabs={clinicTabs} activeTab={activeTab} counts={tabCounts} onChange={setActiveTab} />

          {isLoading ? (
            <p className="text-body-secondary mb-0">Carregando clínicas...</p>
          ) : (
            <AppTable data={filteredClinics} columns={columns} emptyMessage="Nenhuma clínica encontrada." />
          )}
        </CCardBody>
      </CCard>
    </>
  )
}

export default ClinicsList