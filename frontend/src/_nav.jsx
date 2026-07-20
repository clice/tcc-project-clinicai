/**
 * Sidebar Navigation Configuration
 */

import React from 'react'
import CIcon from '@coreui/icons-react'
import {
  cilDescription,
  cilHospital,
  cilMedicalCross,
  cilPeople,
  cilSettings,
  cilShieldAlt,
  cilSpeedometer,
  cilUser,
} from '@coreui/icons'
import { CNavGroup, CNavItem, CNavTitle } from '@coreui/react'

import { PERMISSIONS } from 'src/utils/permissions'

const _nav = [
  {
    component: CNavItem,
    name: 'Dashboard',
    to: '/dashboard',
    icon: <CIcon icon={cilSpeedometer} customClassName="nav-icon" />,
    roles: ['admin_master', 'doctor', 'clinic_manager'],
  },

  ////////// CARE

  {
    component: CNavTitle,
    name: 'Atendimento',
    roles: ['admin_master', 'doctor', 'clinic_manager'],
  },
  {
    component: CNavItem,
    name: 'Pacientes',
    to: '/patients',
    icon: <CIcon icon={cilPeople} customClassName="nav-icon" />,
    roles: ['admin_master', 'doctor', 'clinic_manager'],
    permission: PERMISSIONS.PATIENTS_READ,
  },
  {
    component: CNavGroup,
    name: 'Exames',
    to: '/exams',
    icon: <CIcon icon={cilDescription} customClassName="nav-icon" />,
    // O Gestor da Clínica pode acompanhar somente a listagem
    // operacional e os status dos exames da própria clínica. A abertura
    // dos detalhes e dos resultados continua protegida por exams:read.
    roles: ['admin_master', 'doctor', 'clinic_manager'],
    permission: PERMISSIONS.EXAMS_LIST,
    lockedOpenRoles: ['doctor', 'clinic_manager'],
    items: [
      {
        component: CNavItem,
        name: 'Pendentes',
        to: '/exams?status=pending',
        badgeKey: 'pending',
        roles: ['admin_master', 'doctor', 'clinic_manager'],
        permission: PERMISSIONS.EXAMS_LIST,
      },
      {
        component: CNavItem,
        name: 'Revisão',
        to: '/exams?status=awaiting_review',
        badgeKey: 'awaiting_review',
        roles: ['admin_master', 'doctor', 'clinic_manager'],
        permission: PERMISSIONS.EXAMS_LIST,
      },
      {
        component: CNavItem,
        name: 'Concluídos',
        to: '/exams?status=completed',
        badgeKey: 'completed',
        roles: ['admin_master', 'doctor', 'clinic_manager'],
        permission: PERMISSIONS.EXAMS_LIST,
      },
      {
        component: CNavItem,
        name: 'Com Divergência',
        to: '/exams?status=completed_with_divergence',
        badgeKey: 'completed_with_divergence',
        roles: ['admin_master', 'doctor', 'clinic_manager'],
        permission: PERMISSIONS.EXAMS_LIST,
      },
      {
        component: CNavItem,
        name: 'Falha na IA',
        to: '/exams?status=failed',
        badgeKey: 'failed',
        roles: ['admin_master', 'doctor', 'clinic_manager'],
        permission: PERMISSIONS.EXAMS_LIST,
      },
      {
        component: CNavItem,
        name: 'Cancelados',
        to: '/exams?status=canceled',
        badgeKey: 'canceled',
        roles: ['admin_master', 'doctor', 'clinic_manager'],
        permission: PERMISSIONS.EXAMS_LIST,
      },
    ],
  },

  ////////// ADMINISTRATION

  {
    component: CNavTitle,
    name: 'Administração',
    roles: ['admin_master', 'clinic_manager'],
  },
  {
    component: CNavItem,
    name: 'Clínicas',
    to: '/clinics',
    icon: <CIcon icon={cilHospital} customClassName="nav-icon" />,
    roles: ['admin_master'],
  },
  {
    component: CNavItem,
    name: 'Usuários',
    to: '/users',
    icon: <CIcon icon={cilUser} customClassName="nav-icon" />,
    roles: ['admin_master'],
  },
  {
    component: CNavItem,
    name: 'Médicos',
    to: '/users',
    icon: <CIcon icon={cilMedicalCross} customClassName="nav-icon" />,
    roles: ['clinic_manager'],
    permission: PERMISSIONS.USERS_READ,
  },
  {
    component: CNavItem,
    name: 'Logs',
    to: '/audit-logs',
    icon: <CIcon icon={cilShieldAlt} customClassName="nav-icon" />,
    roles: ['admin_master'],
  },

  ////////// CONFIGURATIONS

  {
    component: CNavGroup,
    name: 'Configurações',
    to: '/settings',
    icon: <CIcon icon={cilSettings} customClassName="nav-icon" />,
    roles: ['admin_master'],
    items: [
      {
        component: CNavItem,
        name: 'Perfis',
        to: '/roles',
        roles: ['admin_master'],
      },
      {
        component: CNavItem,
        name: 'Permissões',
        to: '/permissions',
        roles: ['admin_master'],
      },
      {
        component: CNavItem,
        name: 'Status',
        to: '/statuses',
        roles: ['admin_master'],
      },
    ],
  },
]

export default _nav
