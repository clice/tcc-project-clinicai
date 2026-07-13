/**
 * 
 */

import React from 'react'
import AuditLogsList from './views/audit-logs/AuditLogsList'

// DASHBOARD
const Dashboard = React.lazy(() => import('./views/dashboard/Dashboard'))

// PROFILE
const ProfilePage = React.lazy(() => import('./views/profile/ProfilePage'))

// COMING SOON
const ComingSoon = React.lazy(() => import('./views/coming-soon/ComingSoon'))

////////// ADMIN

// CLINICS
const ClinicsList = React.lazy(() => import('./views/clinics/ClinicsList'))
const ClinicForm = React.lazy(() => import('./views/clinics/ClinicForm'))

const CreateClinic = () => React.createElement(ClinicForm, { mode: 'create' })
const EditClinic = () => React.createElement(ClinicForm, { mode: 'edit' })
const ViewClinic = () => React.createElement(ClinicForm, { mode: 'view' })

// PATIENTS
const PatientsList = React.lazy(() => import('./views/patients/PatientsList'))
const PatientForm = React.lazy(() => import('./views/patients/PatientForm'))

const CreatePatient = () => React.createElement(PatientForm, { mode: 'create' })
const EditPatient = () => React.createElement(PatientForm, { mode: 'edit' })
const ViewPatient = () => React.createElement(PatientForm, { mode: 'view' })

// EXAMS
const ExamsList = React.lazy(() => import('./views/exams/ExamsList'))
const ExamForm = React.lazy(() => import('./views/exams/ExamForm'))

const CreateExam = () => React.createElement(ExamForm, { mode: 'create' })
const EditExam = () => React.createElement(ExamForm, { mode: 'edit' })
const ViewExam = () => React.createElement(ExamForm, { mode: 'view' })

////////// SYSTEM

// USER
const UsersList = React.lazy(() => import('./views/users/UsersList'))
const UserForm = React.lazy(() => import('./views/users/UserForm'))

const CreateUser = () => React.createElement(UserForm, { mode: 'create' })
const EditUser = () => React.createElement(UserForm, { mode: 'edit' })
const ViewUser = () => React.createElement(UserForm, { mode: 'view' })

// AUDIT LOGS
const AugitLogsList = React.lazy(() => import('./views/audit-logs/AuditLogsList'))

////////// CONFIGURATIONS

// ROLES
const RolesList = React.lazy(() => import('./views/roles/RolesList'))
const RoleForm = React.lazy(() => import('./views/roles/RoleForm'))

const CreateRole = () => React.createElement(RoleForm, { mode: 'create' })
const EditRole = () => React.createElement(RoleForm, { mode: 'edit' })
const ViewRole = () => React.createElement(RoleForm, { mode: 'view' })

// PERMISSIONS
const PermissionsList = React.lazy(() => import('./views/permissions/PermissionsList'))
const PermissionForm = React.lazy(() => import('./views/permissions/PermissionForm'))

const CreatePermission = () => React.createElement(PermissionForm, { mode: 'create' })
const EditPermission = () => React.createElement(PermissionForm, { mode: 'edit' })
const ViewPermission = () => React.createElement(PermissionForm, { mode: 'view' })

// STATUSES
const StatusesList = React.lazy(() => import('./views/statuses/StatusesList'))
const StatusForm = React.lazy(() => import('./views/statuses/StatusForm'))

const CreateStatus = () => React.createElement(StatusForm, { mode: 'create' })
const EditStatus = () => React.createElement(StatusForm, { mode: 'edit' })
const ViewStatus = () => React.createElement(StatusForm, { mode: 'view' })

export const routes = [
  { path: '/', exact: true, name: 'Home' },
  { path: '/dashboard', name: 'Dashboard', element: Dashboard },
  { path: '/profile', name: 'Meu Perfil', element: ProfilePage },

  ////////// ADMIN

  // CLINICS
  { path: '/clinics', name: 'Clínicas', element: ClinicsList, roles: ['admin_master']},
  { path: '/clinics/create', name: 'Adicionar Clínica', element: CreateClinic, roles: ['admin_master']},
  { path: '/clinics/:id/edit', name: 'Editar Clínica', element: EditClinic, roles: ['admin_master']},
  { path: '/clinics/:id', name: 'Detalhes da Clínica', element: ViewClinic, roles: ['admin_master']},

  // PATIENTS
  { path: '/patients', name: 'Pacientes', element: PatientsList, roles: ['admin_master', 'doctor', 'clinic_staff']},
  { path: '/patients/create', name: 'Adicionar Paciente', element: CreatePatient, roles: ['admin_master', 'doctor', 'clinic_staff']},
  { path: '/patients/:id/edit', name: 'Editar Paciente', element: EditPatient, roles: ['admin_master', 'doctor', 'clinic_staff']},
  { path: '/patients/:id', name: 'Detalhes do Paciente', element: ViewPatient, roles: ['admin_master', 'doctor', 'clinic_staff']},

  // EXAMS
  { path: '/exams', name: 'Exames', element: ExamsList, roles: ['admin_master', 'doctor']},
  { path: '/exams/create', name: 'Adicionar Exame', element: CreateExam, roles: ['admin_master', 'doctor']},
  { path: '/exams/:id/edit', name: 'Editar Exame', element: EditExam, roles: ['admin_master', 'doctor']},
  { path: '/exams/:id', name: 'Detalhes do Exame', element: ViewExam, roles: ['admin_master', 'doctor']},

  /////////// SYSTEM

  // USERS
  { path: '/users', name: 'Usuários', element: UsersList, roles: ['admin_master']},
  { path: '/users/create', name: 'Adicionar Usuário', element: CreateUser, roles: ['admin_master']},
  { path: '/users/:id/edit', name: 'Editar Usuário', element: EditUser, roles: ['admin_master']},
  { path: '/users/:id', name: 'Detalhes do Usuário', element: ViewUser, roles: ['admin_master']},

  // AUDIT LOGS
  { path: '/audit-logs', name: 'Logs de Auditoria', element: AuditLogsList, roles: ['admin_master']},

  ////////// CONFIGURATIONS

  // ROLES
  { path: '/roles', name: 'Perfis', element: RolesList, roles: ['admin_master']},
  { path: '/roles/create', name: 'Adicionar Perfil', element: CreateRole, roles: ['admin_master']},
  { path: '/roles/:id/edit', name: 'Editar Perfil', element: EditRole, roles: ['admin_master']},
  { path: '/roles/:id', name: 'Detalhes do Perfil', element: ViewRole, roles: ['admin_master']},

  // PERMISSIONS
  { path: '/permissions', name: 'Permissões', element: PermissionsList, roles: ['admin_master']},
  { path: '/permissions/create', name: 'Adicionar Permissão', element: CreatePermission, roles: ['admin_master']},
  { path: '/permissions/:id/edit', name: 'Editar Permissão', element: EditPermission, roles: ['admin_master']},
  { path: '/permissions/:id', name: 'Detalhes da Permissão', element: ViewPermission, roles: ['admin_master']},

  // STATUSES
  { path: '/statuses', name: 'Status', element: StatusesList, roles: ['admin_master'] },
  { path: '/statuses/create', name: 'Adicionar Status', element: CreateStatus, roles: ['admin_master'] },
  { path: '/statuses/:id/edit', name: 'Editar Status', element: EditStatus, roles: ['admin_master'] },
  { path: '/statuses/:id', name: 'Detalhes do Status', element: ViewStatus, roles: ['admin_master'] },
]

export default routes