import React, { useMemo } from 'react'
import { CAlert, CSpinner } from '@coreui/react'

import { useAuth } from 'src/hooks/useAuth'
import { getUserRole, ROLES } from 'src/utils/permissions'

import AdminAiMetrics from './AdminAiMetrics'
import DashboardCards from './DashboardCards'
import DashboardCharts from './DashboardCharts'
import { buildLastSixMonths, calculateConcordance, countExamsByStatus } from './dashboardData'
import { useDashboardData } from './useDashboardData'

const Dashboard = () => {
  const { user } = useAuth()
  const roleName = getUserRole(user)
  const { exams, summary, aiMetrics, isLoading, error, isAdminMaster } = useDashboardData(roleName)

  const statusCounts = useMemo(() => countExamsByStatus(exams), [exams])
  const monthlyData = useMemo(() => buildLastSixMonths(exams), [exams])
  const concordance = useMemo(() => calculateConcordance(statusCounts), [statusCounts])

  const scopeDescription =
    roleName === ROLES.DOCTOR
      ? 'Indicadores dos seus pacientes e exames.'
      : roleName === ROLES.CLINIC_MANAGER
        ? 'Indicadores operacionais da sua clínica.'
        : 'Indicadores gerais da plataforma.'

  return (
    <>
      <div className="mb-4">
        <div className="text-body-secondary">Visão geral</div>
        <h1 className="h3 mb-0 clinicai-page-title">Dashboard</h1>
        <p className="text-body-secondary mb-0">{scopeDescription}</p>
      </div>

      {error && <CAlert color="danger">{error}</CAlert>}

      <DashboardCards roleName={roleName} counts={summary} isLoading={isLoading} />

      {isLoading ? (
        <div className="d-flex justify-content-center py-5">
          <CSpinner />
        </div>
      ) : (
        <DashboardCharts
          counts={statusCounts}
          monthlyData={monthlyData}
          concordance={concordance}
        />
      )}

      {isAdminMaster && <AdminAiMetrics metrics={aiMetrics} />}
    </>
  )
}

export default Dashboard
