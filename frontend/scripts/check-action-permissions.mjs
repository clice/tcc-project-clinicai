/**
 * Teste da matriz de autorização por ação implementada na RBAC-05.
 */

import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { ACTION_PERMISSIONS, getActionAccess } from '../src/utils/actionPermissions.mjs'

for (const [resource, actionMap] of Object.entries(ACTION_PERMISSIONS)) {
  for (const [expectedAction, singlePermission] of Object.entries(actionMap)) {
    const access = getActionAccess(resource, (permission) => permission === singlePermission)

    for (const action of Object.keys(actionMap)) {
      assert.equal(
        access[action],
        action === expectedAction,
        `${resource}.${expectedAction} liberou indevidamente ${action}`,
      )
    }
  }
}

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const frontendDirectory = path.resolve(scriptDirectory, '..')
const componentExpectations = {
  'src/views/patients/PatientsList.jsx': [
    '{canCreate &&',
    'canEdit={canEdit}',
    'canInactivate={canChangeStatus',
  ],
  'src/views/clinics/ClinicsList.jsx': [
    '{canCreate &&',
    'canEdit={canEdit}',
    'canInactivate={canChangeStatus',
  ],
  'src/views/users/UsersList.jsx': [
    '{canCreate &&',
    'canEdit={canEdit}',
    'canInactivate={canChangeStatus',
  ],
  'src/views/exams/ExamsList.jsx': [
    '{canCreate &&',
    'canView={canView}',
    'canEdit={canEdit',
    'canDownload={canDownload',
    'canCancel={canChangeStatus',
  ],
  'src/views/patients/PatientForm.jsx': [
    /hasPermission\(\s*user,\s*PERMISSIONS\.EXAMS_CREATE,?\s*\)/,
    /patient\?\.status_name\s*===\s*['"]active['"]\s*&&\s*isDoctor\s*&&\s*canCreateExam/,
  ],
  'src/views/exams/ExamForm.jsx': ['hasPermission(user, PERMISSIONS.EXAMS_REVIEW)', 'isDoctor &&'],
}

for (const [relativePath, expectedFragments] of Object.entries(componentExpectations)) {
  const source = await readFile(path.join(frontendDirectory, relativePath), 'utf8')
  assert.doesNotMatch(source, /\bcanManage\b/, `${relativePath} ainda usa canManage`)

  for (const expected of expectedFragments) {
    const matches = expected instanceof RegExp ? expected.test(source) : source.includes(expected)

    assert.ok(matches, `${relativePath} não aplica ${String(expected)}`)
  }
}

const patientList = await readFile(
  path.join(frontendDirectory, 'src/views/patients/PatientsList.jsx'),
  'utf8',
)
const routes = await readFile(path.join(frontendDirectory, 'src/routes.js'), 'utf8')
const userForm = await readFile(
  path.join(frontendDirectory, 'src/views/users/UserForm.jsx'),
  'utf8',
)

assert.doesNotMatch(
  patientList,
  /viewTo=\{`\/patients\//,
  'A lista de pacientes não deve oferecer visualização separada.',
)
assert.doesNotMatch(
  patientList,
  /canView=\{canView\}/,
  'A lista de pacientes não deve manter a ação redundante de visualização.',
)
assert.doesNotMatch(
  routes,
  /const ViewPatient|element: ViewPatient|path: '\/patients\/:id'/,
  'A rota separada de visualização de paciente deve permanecer removida.',
)
assert.match(
  userForm,
  /to=\{`\/patients\/\$\{patient\.id\}\/edit`\}/,
  'Pacientes associados ao médico devem abrir diretamente na edição.',
)

console.log('Matriz por ação válida para permissões unitárias e componentes de lista.')
