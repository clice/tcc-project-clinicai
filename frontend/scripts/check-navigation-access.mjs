/**
 * Teste estático/comportamental do filtro de navegação da RBAC.
 */

import assert from 'node:assert/strict'

import { filterNavigationByAccess } from '../src/utils/navigationAccess.mjs'

const navigation = [
  {
    name: 'Pacientes',
    roles: ['doctor', 'clinic_manager'],
    permission: 'patients:read',
  },
  {
    name: 'Exames',
    roles: ['doctor', 'clinic_manager'],
    permission: 'exams:list',
    items: [
      {
        name: 'Pendentes',
        roles: ['doctor', 'clinic_manager'],
        permission: 'exams:list',
      },
    ],
  },
]

const filterFor = (roleName, permissions) =>
  filterNavigationByAccess(navigation, {
    roleName,
    hasPermission: (permission) => permissions.includes(permission),
  })

const doctorAccess = filterFor('doctor', ['patients:read', 'exams:list', 'exams:read'])

assert.deepEqual(
  doctorAccess.map((item) => item.name),
  ['Pacientes', 'Exames'],
)

const managerListOnlyAccess = filterFor('clinic_manager', ['patients:read', 'exams:list'])

assert.deepEqual(
  managerListOnlyAccess.map((item) => item.name),
  ['Pacientes', 'Exames'],
)

assert.equal(managerListOnlyAccess[1].items[0].name, 'Pendentes')

const managerWithoutExamList = filterFor('clinic_manager', ['patients:read'])

assert.deepEqual(
  managerWithoutExamList.map((item) => item.name),
  ['Pacientes'],
)

const detailsOnlyDoesNotOpenList = filterFor('clinic_manager', ['patients:read', 'exams:read'])

assert.deepEqual(
  detailsOnlyDoesNotOpenList.map((item) => item.name),
  ['Pacientes'],
)

const clinicalNavigation = [
  {
    name: 'Cadastrar Exame',
    roles: ['doctor'],
    permission: 'exams:create',
  },
]

const doctorClinicalAccess = filterNavigationByAccess(clinicalNavigation, {
  roleName: 'doctor',
  hasPermission: (permission) => permission === 'exams:create',
})

assert.deepEqual(
  doctorClinicalAccess.map((item) => item.name),
  ['Cadastrar Exame'],
)

const adminCannotBypassDoctorRole = filterNavigationByAccess(clinicalNavigation, {
  roleName: 'admin_master',
  hasPermission: () => true,
})

assert.deepEqual(adminCannotBypassDoctorRole, [])

console.log(
  'Navegação aprovada: role e permissão são cumulativas; exams:list não concede ações clínicas.',
)
