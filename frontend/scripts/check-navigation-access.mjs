/**
 * Teste estático/comportamental do filtro de navegação da RBAC-03.
 */

import assert from 'node:assert/strict'

import { filterNavigationByAccess } from '../src/utils/navigationAccess.mjs'

const navigation = [
  {
    name: 'Pacientes',
    roles: ['doctor'],
    permission: 'patients:read',
  },
  {
    name: 'Exames',
    roles: ['doctor'],
    permission: 'exams:read',
    items: [
      {
        name: 'Processando',
        roles: ['doctor'],
        permission: 'exams:read',
      },
    ],
  },
]

const filterFor = (permissions) =>
  filterNavigationByAccess(navigation, {
    roleName: 'doctor',
    hasPermission: (permission) => permissions.includes(permission),
  })

const fullAccess = filterFor(['patients:read', 'exams:read'])
assert.deepEqual(
  fullAccess.map((item) => item.name),
  ['Pacientes', 'Exames'],
)
assert.equal(fullAccess[0].roles, undefined)
assert.equal(fullAccess[0].permission, undefined)

const withoutPatients = filterFor(['exams:read'])
assert.deepEqual(
  withoutPatients.map((item) => item.name),
  ['Exames'],
)

const withoutExams = filterFor(['patients:read'])
assert.deepEqual(
  withoutExams.map((item) => item.name),
  ['Pacientes'],
)

// Assim como no RoleRoute, uma permissão explícita tem prioridade sobre a
// lista de roles usada como fallback.
const delegatedAccess = filterNavigationByAccess(navigation, {
  roleName: 'clinic_staff',
  hasPermission: (permission) => ['patients:read', 'exams:read'].includes(permission),
})
assert.deepEqual(
  delegatedAccess.map((item) => item.name),
  ['Pacientes', 'Exames'],
)

// O grupo Exames também desaparece quando seu único filho é filtrado.
const childProtectedNavigation = [
  {
    name: 'Exames',
    roles: ['doctor'],
    items: [{ name: 'Revisão', permission: 'exams:review' }],
  },
]
assert.deepEqual(
  filterNavigationByAccess(childProtectedNavigation, {
    roleName: 'doctor',
    hasPermission: () => false,
  }),
  [],
)

console.log('Filtro de navegação válido para role, permissão e grupos vazios.')
