import React from 'react'
import { CCard, CCardBody, CCardHeader, CCol, CProgress, CRow } from '@coreui/react'
import { CChartLine, CChartPie } from '@coreui/react-chartjs'

import { examStatusLabels } from 'src/utils/constants'
import { CHART_COLORS, DASHBOARD_STATUSES } from './dashboardData'

const DashboardCharts = ({ counts, monthlyData, concordance }) => {
  const distribution = DASHBOARD_STATUSES.filter((status) => counts[status] > 0)
  const reviewed = counts.completed + counts.completed_with_divergence
  const concordancePercent = concordance * 100

  return (
    <>
      <CRow className="mb-4">
        <CCol lg={8}>
          <CCard className="clinicai-card h-100">
            <CCardHeader className="clinicai-card-header">
              <strong>Evolução dos Exames (Últimos 6 meses)</strong>
            </CCardHeader>
            <CCardBody>
              <CChartLine
                data={{
                  labels: monthlyData.map((month) => month.label),
                  datasets: [
                    {
                      label: 'Concluídos',
                      borderColor: CHART_COLORS.completed,
                      backgroundColor: 'rgba(46, 184, 92, 0.15)',
                      data: monthlyData.map((month) => month.completed),
                      tension: 0.3,
                    },
                    {
                      label: 'Com divergência',
                      borderColor: CHART_COLORS.completed_with_divergence,
                      backgroundColor: 'rgba(79, 93, 115, 0.15)',
                      data: monthlyData.map((month) => month.divergence),
                      tension: 0.3,
                    },
                    {
                      label: 'Falhos',
                      borderColor: CHART_COLORS.failed,
                      backgroundColor: 'rgba(229, 83, 83, 0.15)',
                      data: monthlyData.map((month) => month.failed),
                      tension: 0.3,
                    },
                  ],
                }}
                options={{
                  maintainAspectRatio: false,
                  plugins: { legend: { position: 'bottom' } },
                }}
                style={{ height: '300px' }}
              />
            </CCardBody>
          </CCard>
        </CCol>

        <CCol lg={4}>
          <CCard className="clinicai-card h-100">
            <CCardHeader className="clinicai-card-header">
              <strong>Distribuição dos Exames</strong>
            </CCardHeader>
            <CCardBody>
              {distribution.length === 0 ? (
                <p className="text-body-secondary mb-0">Nenhum exame disponível.</p>
              ) : (
                <CChartPie
                  data={{
                    labels: distribution.map((status) => examStatusLabels[status]),
                    datasets: [
                      {
                        backgroundColor: distribution.map((status) => CHART_COLORS[status]),
                        data: distribution.map((status) => counts[status]),
                      },
                    ],
                  }}
                  options={{ plugins: { legend: { position: 'bottom' } } }}
                />
              )}
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <CCard className="clinicai-card mb-4">
        <CCardBody>
          <div className="d-flex justify-content-between mb-2">
            <div>
              <strong>Concordância com a Análise de IA</strong>
              <div className="text-body-secondary small">
                {reviewed} exame(s) revisado(s) e finalizado(s)
              </div>
            </div>
            <div className="fs-4 fw-semibold">{concordancePercent.toFixed(1)}%</div>
          </div>
          <CProgress className="clinicai-progress" color="primary" value={concordancePercent} />
        </CCardBody>
      </CCard>
    </>
  )
}

export default DashboardCharts
