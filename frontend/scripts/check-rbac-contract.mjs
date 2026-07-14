/** Compara permissões de rotas, menus e ações com o contrato do backend. */

import assert from 'node:assert/strict'
import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const projectDirectory = path.resolve(scriptDirectory, '..', '..')

const readProjectFile = (relativePath) =>
  readFile(path.join(projectDirectory, relativePath), 'utf8')

const permissionsSource = await readProjectFile('frontend/src/utils/permissions.js')
const routesSource = await readProjectFile('frontend/src/routes.js')
const navigationSource = await readProjectFile('frontend/src/_nav.jsx')
const actionsSource = await readProjectFile('frontend/src/utils/actionPermissions.mjs')
const routerDirectory = path.join(projectDirectory, 'backend', 'app', 'modules')

const permissionCatalog = new Map(
  [...permissionsSource.matchAll(/^\s*([A-Z][A-Z0-9_]*):\s*'([^']+)'/gm)].map(
    ([, constantName, permissionName]) => [constantName, permissionName],
  ),
)

let backendSource = ''
for (const entry of await readdir(routerDirectory, { withFileTypes: true })) {
  if (!entry.isDirectory()) continue
  const routerPath = path.join(routerDirectory, entry.name, 'router.py')
  try {
    backendSource += await readFile(routerPath, 'utf8')
  } catch (error) {
    if (error.code !== 'ENOENT') throw error
  }
}

const backendPermissions = new Set(
  [...backendSource.matchAll(/require_(?:doctor_)?permission\("([a-z_]+:[a-z_]+)"\)/g)].map(
    (match) => match[1],
  ),
)
const routePermissions = new Set(
  [...routesSource.matchAll(/permission:\s*'([^']+)'/g)].map((match) => match[1]),
)
const navigationConstants = new Set(
  [...navigationSource.matchAll(/permission:\s*PERMISSIONS\.([A-Z][A-Z0-9_]*)/g)].map(
    (match) => match[1],
  ),
)
const navigationPermissions = new Set(
  [...navigationConstants].map((constantName) => {
    assert.ok(
      permissionCatalog.has(constantName),
      `Menu usa PERMISSIONS.${constantName} inexistente.`,
    )
    return permissionCatalog.get(constantName)
  }),
)
const actionPermissions = new Set(
  [...actionsSource.matchAll(/:\s*'([a-z_]+:[a-z_]+)'/g)].map((match) => match[1]),
)

for (const permission of [...routePermissions, ...navigationPermissions]) {
  assert.ok(
    backendPermissions.has(permission),
    `Frontend oferece ${permission}, mas nenhuma rota backend a exige.`,
  )
}

// Clínicas e usuários administrativos possuem botões por ação, mas sua
// barreira autoritativa é a role admin_master em todo o router.
const adminOnlyActions = new Set([
  'clinics:create',
  'clinics:read',
  'clinics:update',
  'clinics:change_status',
  'users:create',
  'users:read',
  'users:update',
  'users:change_status',
])
const clinicsRouter = await readProjectFile('backend/app/modules/clinics/router.py')
const usersRouter = await readProjectFile('backend/app/modules/users/router.py')
assert.match(clinicsRouter, /Depends\(require_admin\)/)
assert.match(usersRouter, /Depends\(require_admin\)/)

for (const permission of actionPermissions) {
  assert.ok(
    backendPermissions.has(permission) || adminOnlyActions.has(permission),
    `Botão usa ${permission} sem proteção equivalente no backend.`,
  )
}

assert.match(actionsSource, /canReview:\s*'exams:review'/)
assert.match(backendSource, /require_doctor_permission\("exams:review"\)/)

console.log(
  `Contrato RBAC coerente: ${routePermissions.size} permissões de rota, ` +
    `${navigationPermissions.size} de menu e ${actionPermissions.size} de ação validadas.`,
)
