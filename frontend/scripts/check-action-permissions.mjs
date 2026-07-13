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
    'canView={canView}',
    'canEdit={canEdit}',
    'canInactivate={canChangeStatus',
  ],
  'src/views/clinics/ClinicsList.jsx': [
    '{canCreate &&',
    'canView={canView}',
    'canEdit={canEdit}',
    'canInactivate={canChangeStatus',
  ],
  'src/views/users/UsersList.jsx': [
    '{canCreate &&',
    'canView={canView}',
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
    'hasPermission(user, PERMISSIONS.EXAMS_CREATE)',
    'patient && canCreateExam',
  ],
  'src/views/exams/ExamForm.jsx': ['hasPermission(user, PERMISSIONS.EXAMS_REVIEW)', 'isDoctor &&'],
}

for (const [relativePath, expectedFragments] of Object.entries(componentExpectations)) {
  const source = await readFile(path.join(frontendDirectory, relativePath), 'utf8')
  assert.doesNotMatch(source, /\bcanManage\b/, `${relativePath} ainda usa canManage`)

  for (const fragment of expectedFragments) {
    assert.ok(source.includes(fragment), `${relativePath} não aplica ${fragment}`)
  }
}

console.log('Matriz por ação válida para permissões unitárias e componentes de lista.')
