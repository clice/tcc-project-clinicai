import React from 'react'
import { CCard, CCardBody, CCardHeader, CCol, CRow } from '@coreui/react'

const formatPercent = (value) =>
  value === null || value === undefined ? '-' : `${(value * 100).toFixed(1)}%`

const formatMilliseconds = (value) =>
  value === null || value === undefined ? '-' : `${Math.round(value)} ms`

const AdminAiMetrics = ({ metrics }) => {
  if (!metrics) return null

  const reviewedCount = metrics.reviewed_analyses_count ?? 0

  const items = [
    ['Exames analisados', metrics.total_analyses ?? 0],
    ['Confiança média', formatPercent(metrics.confidence_mean)],
    ['Tempo médio de processamento', formatMilliseconds(metrics.processing_time_mean_ms)],
    ['Exames revisados', reviewedCount],
    [
      'Falsos positivos',
      `${metrics.false_positive_count ?? 0} de ${reviewedCount} revisados`,
    ],
    [
      'Falsos negativos',
      `${metrics.false_negative_count ?? 0} de ${reviewedCount} revisados`,
    ],
  ]

  return (
    <CCard className="mb-4">
      <CCardHeader>
        <strong>Indicadores Técnicos da IA</strong>
      </CCardHeader>

      <CCardBody>
        <CRow className="g-3">
          {items.map(([label, value]) => (
            <CCol md={4} key={label}>
              <div className="text-body-secondary small">{label}</div>
              <div className="fs-4 fw-semibold">{value}</div>
            </CCol>
          ))}
        </CRow>

        <div className="border-top pt-3 mt-4 small text-body-secondary">
          <div>
            <strong>Falso positivo:</strong> a IA indicou anormalidade, mas o médico
            discordou dessa classificação.
          </div>

          <div>
            <strong>Falso negativo:</strong> a IA indicou normalidade, mas o médico
            discordou dessa classificação.
          </div>

          <div className="mt-2">
            A confiança e o tempo médio consideram todas as análises executadas.
            Falsos positivos e falsos negativos consideram apenas exames revisados.
            Os resultados correspondem à massa acadêmica demonstrativa e não
            representam validação clínica do sistema.
          </div>
        </div>
      </CCardBody>
    </CCard>
  )
}

export default AdminAiMetrics
