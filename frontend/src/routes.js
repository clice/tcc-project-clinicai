/**
 * 
 */

import React from 'react'

// DASHBOARD
const Dashboard = React.lazy(() => import('./views/dashboard/Dashboard'))

// COMING SOON
const ComingSoon = React.lazy(() => import('./views/coming-soon/ComingSoon'))

////////// CONFIGURATIONS

// STATUSES
const StatusesList = React.lazy(() => import('./views/statuses/StatusesList'))
const StatusForm = React.lazy(() => import('./views/statuses/StatusForm'))

const CreateStatus = () => React.createElement(StatusForm, { mode: 'create' })
const EditStatus = () => React.createElement(StatusForm, { mode: 'edit' })
const ViewStatus = () => React.createElement(StatusForm, { mode: 'view' })

export const routes = [
  { path: '/', exact: true, name: 'Home' },
  { path: '/dashboard', name: 'Dashboard', element: Dashboard },

  ////////// CONFIGURATIONS

  // STATUSES
  { path: '/statuses', name: 'Status', element: StatusesList, roles: ['admin_master'] },
  { path: '/statuses/create', name: 'Adicionar Status', element: CreateStatus, roles: ['admin_master'] },
  { path: '/statuses/:id/edit', name: 'Editar Status', element: EditStatus, roles: ['admin_master'] },
  { path: '/statuses/:id', name: 'Detalhes do Status', element: ViewStatus, roles: ['admin_master'] },

  { path: '/users', name: 'Usuários', element: ComingSoon },
  { path: '/clinics', name: 'Clínicas', element: ComingSoon },
  { path: '/patients', name: 'Pacientes', element: ComingSoon },
  { path: '/exams', name: 'Exams', element: ComingSoon },
  { path: '/roles', name: 'Perfis', element: ComingSoon },
  { path: '/permissions', name: 'Permissões', element: ComingSoon },
  { path: '/statuses', name: 'Status', element: ComingSoon },
  { path: '/audit-logs', name: 'Logs', element: ComingSoon },
]

export default routes