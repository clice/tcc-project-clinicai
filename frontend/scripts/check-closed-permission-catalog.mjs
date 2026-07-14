/** Verifica se a criação dinâmica de permissões continua indisponível. */

import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const projectDirectory = path.resolve(scriptDirectory, '..', '..')

const readProjectFile = (relativePath) =>
  readFile(path.join(projectDirectory, relativePath), 'utf8')

const routes = await readProjectFile('frontend/src/routes.js')
const list = await readProjectFile('frontend/src/views/permissions/PermissionsList.jsx')
const form = await readProjectFile('frontend/src/views/permissions/PermissionForm.jsx')
const service = await readProjectFile('frontend/src/services/permissionService.js')
const backendRouter = await readProjectFile('backend/app/modules/permissions/router.py')
const backendSchema = await readProjectFile('backend/app/modules/permissions/schema.py')

assert.doesNotMatch(routes, /\/permissions\/create|CreatePermission/)
assert.doesNotMatch(list, /Cadastrar Permissão|\/permissions\/create/)
assert.doesNotMatch(form, /mode === ['"]create['"]|permissionService\.create/)
assert.doesNotMatch(service, /api\.post\(['"]\/permissions\//)
assert.doesNotMatch(backendRouter, /@router\.post|create_permission/)
assert.doesNotMatch(backendSchema, /class PermissionCreate/)

console.log('Catálogo fechado: nenhuma criação dinâmica exposta no frontend ou backend.')
