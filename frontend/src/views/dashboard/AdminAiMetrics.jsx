import React from 'react'
import { CCard, CCardBody, CCardHeader, CCol, CRow } from '@coreui/react'

const formatPercent = (value) =>
  value === null || value === undefined ? '-' : `${(value * 100).toFixed(1)}%`

const AdminAiMetrics = ({ metrics }) => {
  if (!metrics) return null

  const items = [
    ['Análises realizadas', metrics.total_analyses ?? 0],
    ['Confiança média', formatPercent(metrics.confidence_mean)],
    [
      'Tempo médio de processamento',
      metrics.processing_time_mean_ms === null || metrics.processing_time_mean_ms === undefined
        ? '-'
        : `${Math.round(metrics.processing_time_mean_ms)} ms`,
    ],
  ]

  return (
    <CCard className="mb-4">
      <CCardHeader><strong>Indicadores técnicos da IA</strong></CCardHeader>
      <CCardBody>
        <CRow>
          {items.map(([label, value]) => (
            <CCol md={4} className="mb-3 mb-md-0" key={label}>
              <div className="text-body-secondary small">{label}</div>
              <div className="fs-4 fw-semibold">{value}</div>
            </CCol>
          ))}
        </CRow>
      </CCardBody>
    </CCard>
  )
}

export default AdminAiMetrics
