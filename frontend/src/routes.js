/**
 * 
 */

import React from 'react'

// DASHBOARD
const Dashboard = React.lazy(() => import('./views/dashboard/Dashboard'))

// COMING SOON
const ComingSoon = React.lazy(() => import('./views/coming-soon/ComingSoon'))

////////// ADMIN

// CLINICS
const ClinicsList = React.lazy(() => import('./views/clinics/ClinicsList'))
const ClinicForm = React.lazy(() => import('./views/clinics/ClinicForm'))

const CreateClinic = () => React.createElement(ClinicForm, { mode: 'create' })
const EditClinic = () => React.createElement(ClinicForm, { mode: 'edit' })
const ViewClinic = () => React.createElement(ClinicForm, { mode: 'view' })

// USER
const UsersList = React.lazy(() => import('./views/users/UsersList'))
const UserForm = React.lazy(() => import('./views/users/UserForm'))

const CreateUser = () => React.createElement(UserForm, { mode: 'create' })
const EditUser = () => React.createElement(UserForm, { mode: 'edit' })
const ViewUser = () => React.createElement(UserForm, { mode: 'view' })

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

  ////////// ADMIN

  // CLINICS
  { path: '/clinics', name: 'Clínicas', element: ClinicsList, roles: ['admin_master']},
  { path: '/clinics/create', name: 'Adicionar Clínica', element: CreateClinic, roles: ['admin_master']},
  { path: '/clinics/:id/edit', name: 'Editar Clínica', element: EditClinic, roles: ['admin_master']},
  { path: '/clinics/:id', name: 'Detalhes da Clínica', element: ViewClinic, roles: ['admin_master']},

  // USERS
  { path: '/users', name: 'Usuários', element: UsersList, roles: ['admin_master']},
  { path: '/users/create', name: 'Adicionar Usuário', element: CreateUser, roles: ['admin_master']},
  { path: '/users/:id/edit', name: 'Editar Usuário', element: EditUser, roles: ['admin_master']},
  { path: '/users/:id', name: 'Detalhes do Usuário', element: ViewUser, roles: ['admin_master']},

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

  { path: '/patients', name: 'Pacientes', element: ComingSoon },
  { path: '/exams', name: 'Exams', element: ComingSoon },
  { path: '/audit-logs', name: 'Logs', element: ComingSoon },
]

export default routes