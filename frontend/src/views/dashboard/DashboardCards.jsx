import React from 'react'
import { Link } from 'react-router-dom'
import CIcon from '@coreui/icons-react'
import { cilDescription, cilHospital, cilPeople, cilUser } from '@coreui/icons'
import { CCard, CCardBody, CCol, CRow, CSpinner } from '@coreui/react'

import { ROLES } from 'src/utils/permissions'

const DashboardCards = ({ roleName, counts, isLoading }) => {
  const cards =
    roleName === ROLES.ADMIN_MASTER
      ? [
          {
            label: 'Usuários ativos',
            value: counts.users,
            icon: cilUser,
            to: '/users',
          },
          {
            label: 'Clínicas ativas',
            value: counts.clinics,
            icon: cilHospital,
            to: '/clinics',
          },
          {
            label: 'Pacientes ativos',
            value: counts.patients,
            icon: cilPeople,
            to: '/patients',
          },
          {
            label: 'Exames',
            value: counts.exams,
            icon: cilDescription,
            to: '/exams',
          },
        ]
      : roleName === ROLES.CLINIC_MANAGER
        ? [
            {
              label: 'Médicos ativos',
              value: counts.doctors,
              icon: cilUser,
              to: '/users',
            },
            {
              label: 'Pacientes ativos',
              value: counts.patients,
              icon: cilPeople,
              to: '/patients',
            },
            {
              label: 'Exames',
              value: counts.exams,
              icon: cilDescription,
              to: '/exams',
            },
          ]
        : [
            {
              label: 'Pacientes ativos',
              value: counts.patients,
              icon: cilPeople,
              to: '/patients',
            },
            {
              label: 'Exames',
              value: counts.exams,
              icon: cilDescription,
              to: '/exams',
            },
          ]

  return (
    <CRow className="mb-4">
      {cards.map(({ label, value, icon, to }) => (
        <CCol sm={6} xl={12 / cards.length} key={label}>
          <Link
            to={to}
            className="clinicai-summary-card-link d-block h-100 text-decoration-none"
            aria-label={`Abrir ${label.toLowerCase()}`}
          >
            <CCard className="clinicai-summary-card mb-3 h-100">
              <CCardBody className="d-flex align-items-center justify-content-between gap-3">
                <div>
                  <div className="clinicai-summary-card-label small">
                    <strong>{label}</strong>
                  </div>

                  <div className="fs-3 fw-semibold">
                    {isLoading ? <CSpinner size="sm" /> : value}
                  </div>
                </div>

                <div className="clinicai-summary-card-icon" aria-hidden="true">
                  <CIcon icon={icon} height={30} />
                </div>
              </CCardBody>
            </CCard>
          </Link>
        </CCol>
      ))}
    </CRow>
  )
}

export default DashboardCards
