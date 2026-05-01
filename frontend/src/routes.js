/**
 * 
 */

import React from 'react'

// DASHBOARD
const Dashboard = React.lazy(() => import('./views/dashboard/Dashboard'))

// COMING SOON
const ComingSoon = React.lazy(() => import('./views/coming-soon/ComingSoon'))

export const routes = [
  { path: '/', exact: true, name: 'Home' },
  { path: '/dashboard', name: 'Dashboard', element: Dashboard },

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