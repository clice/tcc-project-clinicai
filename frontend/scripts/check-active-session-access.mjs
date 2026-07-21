import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

import {
  ACTIVE_ACCESS_REFRESH_INTERVAL_MS,
  getAccessSnapshot,
  hasAccessChanged,
} from '../src/utils/sessionAccess.mjs'

const readProjectFile = (relativePath) =>
  readFileSync(fileURLToPath(new URL(`../${relativePath}`, import.meta.url)), 'utf8')

const originalUser = {
  role_id: 2,
  role_name: 'doctor',
  permissions: ['exams:read', 'exams:review'],
}

assert.equal(ACTIVE_ACCESS_REFRESH_INTERVAL_MS, 60_000)
assert.deepEqual(getAccessSnapshot(originalUser).permissions, ['exams:read', 'exams:review'])
assert.equal(
  hasAccessChanged(originalUser, {
    ...originalUser,
    permissions: ['exams:review', 'exams:read'],
  }),
  false,
  'Apenas reordenar permissões não pode gerar um alerta.',
)
assert.equal(
  hasAccessChanged(originalUser, { ...originalUser, permissions: ['exams:read'] }),
  true,
  'Revogar uma permissão deve ser detectado.',
)
assert.equal(
  hasAccessChanged(originalUser, { ...originalUser, role_id: 3, role_name: 'clinic_manager' }),
  true,
  'Trocar a role deve ser detectado.',
)

const authContext = readProjectFile('src/contexts/AuthContext.jsx')
const defaultLayout = readProjectFile('src/layout/DefaultLayout.jsx')
const roleForm = readProjectFile('src/views/roles/RoleForm.jsx')

for (const requiredFragment of [
  "window.addEventListener('focus'",
  "document.addEventListener('visibilitychange'",
  'window.setInterval(',
  'notifyOnAccessChange: true',
  'authService.getCurrentUser()',
]) {
  assert.ok(
    authContext.includes(requiredFragment),
    `AuthContext deve conter o mecanismo: ${requiredFragment}`,
  )
}

assert.ok(defaultLayout.includes('<AccessUpdateAlert />'))
assert.ok(roleForm.includes('em até 60 segundos'))

console.log('Propagação de acessos para sessões ativas verificada com sucesso.')
