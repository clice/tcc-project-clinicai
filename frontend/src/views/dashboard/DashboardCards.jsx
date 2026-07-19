import React from 'react'
import { CCard, CCardBody, CCol, CRow, CSpinner } from '@coreui/react'

import { ROLES } from 'src/utils/permissions'

const DashboardCards = ({ roleName, counts, isLoading }) => {
  const cards =
    roleName === ROLES.ADMIN_MASTER
      ? [
          ['Usuários ativos', counts.users],
          ['Clínicas ativas', counts.clinics],
          ['Pacientes ativos', counts.patients],
          ['Exames', counts.exams],
        ]
      : [
          ['Pacientes ativos', counts.patients],
          ['Exames', counts.exams],
        ]

  return (
    <CRow className="mb-4">
      {cards.map(([label, value]) => (
        <CCol sm={6} xl={12 / cards.length} key={label}>
          <CCard className="mb-3 h-100">
            <CCardBody>
              <div className="text-body-secondary small">{label}</div>
              <div className="fs-3 fw-semibold">
                {isLoading ? <CSpinner size="sm" /> : value}
              </div>
            </CCardBody>
          </CCard>
        </CCol>
      ))}
    </CRow>
  )
}

export default DashboardCards
