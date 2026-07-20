/** Verifica se a criação dinâmica de perfis e status continua indisponível. */

import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const projectDirectory = path.resolve(scriptDirectory, '..', '..')

const readProjectFile = (relativePath) =>
  readFile(path.join(projectDirectory, relativePath), 'utf8')

const routes = await readProjectFile('frontend/src/routes.js')

for (const catalog of [
  {
    route: 'roles',
    form: 'frontend/src/views/roles/RoleForm.jsx',
    service: 'frontend/src/services/roleService.js',
    router: 'backend/app/modules/roles/router.py',
    schema: 'backend/app/modules/roles/schema.py',
    createModel: 'RoleCreate',
  },
  {
    route: 'statuses',
    form: 'frontend/src/views/statuses/StatusForm.jsx',
    service: 'frontend/src/services/statusService.js',
    router: 'backend/app/modules/statuses/router.py',
    schema: 'backend/app/modules/statuses/schema.py',
    createModel: 'StatusCreate',
  },
]) {
  const form = await readProjectFile(catalog.form)
  const service = await readProjectFile(catalog.service)
  const backendRouter = await readProjectFile(catalog.router)
  const backendSchema = await readProjectFile(catalog.schema)

  assert.doesNotMatch(routes, new RegExp(`/${catalog.route}/create`))
  assert.doesNotMatch(form, /mode === ['"]create['"]|Service\.create/)
  assert.doesNotMatch(service, new RegExp(`api\\.post\\(['"]/${catalog.route}/`))
  assert.doesNotMatch(backendRouter, /@router\.post|create_(?:role|status)/)
  assert.doesNotMatch(backendSchema, new RegExp(`class ${catalog.createModel}`))
}

const statusList = await readProjectFile('frontend/src/views/statuses/StatusesList.jsx')
const statusForm = await readProjectFile('frontend/src/views/statuses/StatusForm.jsx')

assert.doesNotMatch(routes, /ViewStatus|path: ['"]\/statuses\/:id['"]/)
assert.match(routes, /path: ['"]\/statuses\/:id\/edit['"]/)
assert.doesNotMatch(statusList, /viewTo=|canView=/)
assert.match(statusList, /editTo=\{`\/statuses\/\$\{row\.original\.id\}\/edit`\}/)
assert.doesNotMatch(statusForm, /\bisReadOnly\b|\bisEditMode\b|mode === ['"]view['"]/)
assert.match(statusForm, /<h1 className="h3 mb-0">Editar Status<\/h1>/)
assert.match(
  statusForm,
  /<CFormLabel>Nome técnico<\/CFormLabel>[\s\S]*?<CFormInput[^>]*disabled readOnly \/>/,
)
assert.match(
  statusForm,
  /<CFormLabel>Aplicado em<\/CFormLabel>[\s\S]*?<CFormInput[^>]*disabled readOnly \/>/,
)

console.log(
  'Catálogos fechados: perfis e status não expõem criação dinâmica; Status usa edição unificada.',
)
