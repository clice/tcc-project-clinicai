/** Verifica o contrato CHK-07 entre frontend e backend de usuários. */

import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const projectDirectory = path.resolve(scriptDirectory, '..', '..')
const readProjectFile = (relativePath) =>
  readFile(path.join(projectDirectory, relativePath), 'utf8')

const [router, schema, service, form, list, userService] = await Promise.all([
  readProjectFile('backend/app/modules/users/router.py'),
  readProjectFile('backend/app/modules/users/schema.py'),
  readProjectFile('backend/app/modules/users/service.py'),
  readProjectFile('frontend/src/views/users/UserForm.jsx'),
  readProjectFile('frontend/src/views/users/UsersList.jsx'),
  readProjectFile('frontend/src/services/userService.js'),
])

assert.match(router, /payload: UserSelfUpdate[\s\S]*?update_current_user_profile/)
assert.match(router, /payload: UserAdminUpdate[\s\S]*?update_user\(/)
assert.match(router, /\/doctors", response_model=list\[UserOptionResponse\]/)

const adminUpdateBlock = schema.split('class UserAdminUpdate')[1].split('class UserSelfUpdate')[0]
const selfUpdateBlock = schema.split('class UserSelfUpdate')[1].split('UserUpdate =')[0]
const optionBlock = schema.split('class UserOptionResponse')[1]

assert.doesNotMatch(adminUpdateBlock, /^\s+status_id\s*:/m)
assert.doesNotMatch(selfUpdateBlock, /^\s+(role_id|clinic_id|status_id)\s*:/m)
assert.match(optionBlock, /^\s+id\s*:\s*int/m)
assert.match(optionBlock, /^\s+name\s*:\s*str/m)
assert.doesNotMatch(optionBlock, /^\s+(email|cpf|phone|token_version|password_hash)\s*:/m)

assert.match(service, /func\.lower\(User\.email\)/)
assert.match(service, /def validate_user_role_clinic_rules/)
assert.match(service, /def ensure_last_active_admin_is_preserved/)
assert.match(service, /security_context_changed/)
assert.match(service, /user\.token_version \+= 1/)

assert.match(form, /const buildCreatePayload[\s\S]*?status_id: Number\(form\.status_id\)/)
const updatePayloadBlock = form.split('const buildAdminUpdatePayload')[1].split('const handleSubmit')[0]
assert.doesNotMatch(updatePayloadBlock, /status_id/)
assert.match(form, /disabled=\{isReadOnly \|\| isEditMode\}/)
assert.match(list, /selectedUser\.id !== user\?\.id/)
assert.match(userService, /api\.patch\(`\/users\/\$\{id\}`/)

console.log(
  'Contrato de usuários coerente: invariantes de role/clínica, status dedicado, autoedição e exposição mínima validados.',
)
