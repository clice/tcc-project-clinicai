/**
 *
 */

import React from 'react'

// DASHBOARD
const Dashboard = React.lazy(() => import('./views/dashboard/Dashboard'))

// PROFILE
const ProfilePage = React.lazy(() => import('./views/profile/ProfilePage'))


////////// ADMIN

// CLINICS
const ClinicsList = React.lazy(() => import('./views/clinics/ClinicsList'))
const ClinicForm = React.lazy(() => import('./views/clinics/ClinicForm'))

const CreateClinic = () =>
  React.createElement(ClinicForm, {
    mode: 'create',
  })
const EditClinic = () =>
  React.createElement(ClinicForm, {
    mode: 'edit',
  })

// PATIENTS
const PatientsList = React.lazy(() => import('./views/patients/PatientsList'))
const PatientForm = React.lazy(() => import('./views/patients/PatientForm'))

const CreatePatient = () =>
  React.createElement(PatientForm, {
    mode: 'create',
  })
const EditPatient = () =>
  React.createElement(PatientForm, {
    mode: 'edit',
  })

// EXAMS
const ExamsList = React.lazy(() => import('./views/exams/ExamsList'))
const ExamForm = React.lazy(() => import('./views/exams/ExamForm'))

const CreateExam = () =>
  React.createElement(ExamForm, {
    mode: 'create',
  })
const ViewExam = () =>
  React.createElement(ExamForm, {
    mode: 'view',
  })

////////// SYSTEM

// USER
const UsersList = React.lazy(() => import('./views/users/UsersList'))
const UserForm = React.lazy(() => import('./views/users/UserForm'))

const CreateUser = () =>
  React.createElement(UserForm, {
    mode: 'create',
  })
const EditUser = () =>
  React.createElement(UserForm, {
    mode: 'edit',
  })

// AUDIT LOGS
const AuditLogsList = React.lazy(() => import('./views/audit-logs/AuditLogsList'))

////////// CONFIGURATIONS

// ROLES
const RolesList = React.lazy(() => import('./views/roles/RolesList'))
const RoleForm = React.lazy(() => import('./views/roles/RoleForm'))

const EditRole = () => React.createElement(RoleForm)

// PERMISSIONS
const PermissionsList = React.lazy(() => import('./views/permissions/PermissionsList'))
const PermissionForm = React.lazy(() => import('./views/permissions/PermissionForm'))

const EditPermission = () => React.createElement(PermissionForm)

// STATUSES
const StatusesList = React.lazy(() => import('./views/statuses/StatusesList'))
const StatusForm = React.lazy(() => import('./views/statuses/StatusForm'))

const EditStatus = () => React.createElement(StatusForm)

export const routes = [
  {
    path: '/',
    exact: true,
    name: 'Home',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    element: Dashboard,
  },
  {
    path: '/profile',
    name: 'Meu Perfil',
    element: ProfilePage,
  },

  ////////// ADMIN

  // CLINICS
  {
    path: '/clinics',
    name: 'Clínicas',
    element: ClinicsList,
    roles: ['admin_master'],
  },
  {
    path: '/clinics/create',
    name: 'Adicionar Clínica',
    element: CreateClinic,
    roles: ['admin_master'],
  },
  {
    path: '/clinics/:id/edit',
    name: 'Editar Clínica',
    element: EditClinic,
    roles: ['admin_master'],
  },
  // PATIENTS
  // Quando uma rota declara "roles" e "permission", as duas restrições
  // são aplicadas em conjunto. A role define o perfil autorizado e a
  // permissão confirma que a capacidade continua concedida ao perfil.
  {
    path: '/patients',
    name: 'Pacientes',
    element: PatientsList,
    roles: ['admin_master', 'doctor', 'clinic_manager'],
    permission: 'patients:read',
  },
  {
    path: '/patients/create',
    name: 'Adicionar Paciente',
    element: CreatePatient,
    roles: ['admin_master', 'doctor', 'clinic_manager'],
    permission: 'patients:create',
  },
  {
    path: '/patients/:id/edit',
    name: 'Editar Paciente',
    element: EditPatient,
    roles: ['admin_master', 'doctor', 'clinic_manager'],
    permission: 'patients:update',
  },
  // EXAMS
  {
    path: '/exams',
    name: 'Exames',
    element: ExamsList,
    roles: ['admin_master', 'doctor', 'clinic_manager'],
    permission: 'exams:list',
  },
  {
    path: '/exams/create',
    name: 'Adicionar Exame',
    element: CreateExam,
    roles: ['doctor'],
    permission: 'exams:create',
  },
  {
    path: '/exams/:id',
    name: 'Detalhes do Exame',
    element: ViewExam,
    roles: ['doctor'],
    permission: 'exams:read',
  },

  /////////// SYSTEM

  // USERS
  {
    path: '/users',
    name: 'Usuários',
    element: UsersList,
    roles: ['admin_master', 'clinic_manager'],
    permission: 'users:read',
  },
  {
    path: '/users/create',
    name: 'Adicionar Usuário',
    element: CreateUser,
    roles: ['admin_master', 'clinic_manager'],
    permission: 'users:create',
  },
  {
    path: '/users/:id/edit',
    name: 'Editar Usuário',
    element: EditUser,
    roles: ['admin_master', 'clinic_manager'],
    permission: 'users:update',
  },
  // AUDIT LOGS
  {
    path: '/audit-logs',
    name: 'Logs de Auditoria',
    element: AuditLogsList,
    roles: ['admin_master'],
  },

  ////////// CONFIGURATIONS

  // ROLES
  {
    path: '/roles',
    name: 'Perfis',
    element: RolesList,
    roles: ['admin_master'],
  },
  {
    path: '/roles/:id/edit',
    name: 'Editar Perfil',
    element: EditRole,
    roles: ['admin_master'],
  },

  // PERMISSIONS
  {
    path: '/permissions',
    name: 'Permissões',
    element: PermissionsList,
    roles: ['admin_master'],
  },
  {
    path: '/permissions/:id/edit',
    name: 'Editar Permissão',
    element: EditPermission,
    roles: ['admin_master'],
  },
  // STATUSES
  {
    path: '/statuses',
    name: 'Status',
    element: StatusesList,
    roles: ['admin_master'],
  },
  {
    path: '/statuses/:id/edit',
    name: 'Editar Status',
    element: EditStatus,
    roles: ['admin_master'],
  },
]

export default routes
