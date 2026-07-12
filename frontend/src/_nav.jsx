/**
 * Sidebar Navigation Configuration
 */

import React from 'react'
import CIcon from '@coreui/icons-react'
import {
  cilFile,
  cilMedicalCross,
  cilHospital,
  cilPeople,
  cilSettings,
  cilShieldAlt,
  cilSpeedometer,
  cilUser,
} from '@coreui/icons'
import { CNavGroup, CNavItem, CNavTitle } from '@coreui/react'

const _nav = [
  {
    component: CNavItem,
    name: 'Dashboard',
    to: '/dashboard',
    icon: <CIcon icon={cilSpeedometer} customClassName="nav-icon" />,
    roles: ['admin_master', 'doctor', 'clinic_staff'],
  },

  ////////// ADMIN

  {
    component: CNavTitle,
    name: 'Administrativo',
    roles: ['admin_master', 'doctor', 'clinic_staff'],
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
    name: 'Pacientes',
    to: '/patients',
    icon: <CIcon icon={cilMedicalCross} customClassName="nav-icon" />,
    roles: ['admin_master', 'doctor', 'clinic_staff'],
  },
  {
    component: CNavGroup,
    name: 'Exames',
    to: '/exams',
    icon: <CIcon icon={cilFile} customClassName="nav-icon" />,
    roles: ['admin_master', 'doctor', 'clinic_staff'],
    items: [
      {
        component: CNavItem,
        name: 'Processando',
        to: '/exams?status=processing',
        badgeKey: 'processing',
        roles: ['admin_master', 'doctor', 'clinic_staff'],
      },
      {
        component: CNavItem,
        name: 'Revisão',
        to: '/exams?status=awaiting_review',
        badgeKey: 'awaiting_review',
        roles: ['admin_master', 'doctor', 'clinic_staff'],
      },
      {
        component: CNavItem,
        name: 'Concluídos',
        to: '/exams?status=completed',
        badgeKey: 'completed',
        roles: ['admin_master', 'doctor', 'clinic_staff'],
      },
      {
        component: CNavItem,
        name: 'Divergência',
        to: '/exams?status=completed_with_divergence',
        badgeKey: 'completed_with_divergence',
        roles: ['admin_master', 'doctor', 'clinic_staff'],
      },
      {
        component: CNavItem,
        name: 'Falha na IA',
        to: '/exams?status=failed',
        badgeKey: 'failed',
        roles: ['admin_master', 'doctor', 'clinic_staff'],
      },
      {
        component: CNavItem,
        name: 'Cancelados',
        to: '/exams?status=canceled',
        badgeKey: 'canceled',
        roles: ['admin_master', 'doctor', 'clinic_staff'],
      },
      {
        component: CNavItem,
        name: 'Pendentes',
        to: '/exams?status=pending',
        badgeKey: 'pending',
        // Reservado — hoje nenhum exame chega a esse status (upload é
        // obrigatório no cadastro). Visível só para o Administrador Master
        // enquanto isso não se tornar um estado alcançável de verdade.
        roles: ['admin_master'],
      },
    ],
  },

  ////////// SYSTEM

  {
    component: CNavTitle,
    name: 'Sistema',
    roles: ['admin_master'],
  },  
  {
    component: CNavItem,
    name: 'Usuários',
    to: '/users',
    icon: <CIcon icon={cilPeople} customClassName="nav-icon" />,
    roles: ['admin_master'],
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