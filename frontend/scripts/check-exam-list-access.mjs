/**
 * Garante a separação entre listagem operacional e detalhes clínicos.
 */

import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))

const projectDirectory = path.resolve(scriptDirectory, '..', '..')

const read = (relativePath) => readFile(path.join(projectDirectory, relativePath), 'utf8')

const [
  permissions,
  routes,
  navigation,
  sidebar,
  examsList,
  backendRouter,
  backendSchema,
  backendService,
  roleSeed,
] = await Promise.all([
  read('frontend/src/utils/permissions.js'),
  read('frontend/src/routes.js'),
  read('frontend/src/_nav.jsx'),
  read('frontend/src/components/layout/AppSidebar.jsx'),
  read('frontend/src/views/exams/ExamsList.jsx'),
  read('backend/app/modules/exams/router.py'),
  read('backend/app/modules/exams/schema.py'),
  read('backend/app/modules/exams/service.py'),
  read('backend/app/modules/role_permissions/seed.py'),
])

const roleRoute = await read('frontend/src/components/auth/RoleRoute.jsx')

assert.match(permissions, /EXAMS_LIST:\s*'exams:list'/)

const listRoute = routes.match(/\{\s*path:\s*'\/exams',[\s\S]*?\n\s*\},/)

assert.ok(listRoute, 'Rota da listagem não encontrada.')

assert.match(listRoute[0], /clinic_manager/)

assert.match(listRoute[0], /permission:\s*'exams:list'/)

const createRoute = routes.match(/\{\s*path:\s*'\/exams\/create',[\s\S]*?\n\s*\},/)

assert.ok(createRoute, 'Rota de criação não encontrada.')

assert.match(createRoute[0], /roles:\s*\['doctor'\]/)

assert.doesNotMatch(createRoute[0], /admin_master|clinic_manager/)

const detailRoute = routes.match(/\{\s*path:\s*'\/exams\/:id',[\s\S]*?\n\s*\},/)

assert.ok(detailRoute, 'Rota de detalhes não encontrada.')

assert.match(detailRoute[0], /roles:\s*\['doctor'\]/)

assert.doesNotMatch(detailRoute[0], /admin_master|clinic_manager/)

assert.match(detailRoute[0], /permission:\s*'exams:read'/)

assert.match(navigation, /name:\s*'Exames'[\s\S]*?permission:\s*PERMISSIONS\.EXAMS_LIST/)

assert.match(sidebar, /hasPermission\(user, PERMISSIONS\.EXAMS_LIST\)/)

assert.doesNotMatch(sidebar, /useExamStatusCounts\(\{\}, canReadExams\)/)

assert.match(examsList, /const canUseClinicalExamActions = roleName === ROLES\.DOCTOR/)

assert.match(examsList, /const showDoctorColumn = roleName !== ROLES\.DOCTOR/)

assert.match(examsList, /const showClinicColumn = roleName === ROLES\.ADMIN_MASTER/)

assert.match(
  examsList,
  /\.\.\.\(\s*showDoctorColumn\s*\?\s*\[\s*\{\s*accessorKey:\s*['"]doctor_name['"]/,
)

assert.match(
  examsList,
  /\.\.\.\(\s*showClinicColumn\s*\?\s*\[\s*\{\s*accessorKey:\s*['"]clinic_name['"]/,
)

assert.match(examsList, /if \(!canUseClinicalExamActions\) \{\s*return result/)

assert.match(examsList, /canCreate && canUseClinicalExamActions/)

assert.match(backendRouter, /@router\.get\([\s\S]*?"\/"[\s\S]*?require_permission\("exams:list"\)/)

assert.match(
  backendRouter,
  /@router\.get\("\/\{exam_id\}"[\s\S]*?require_doctor_permission\("exams:read"\)/,
)

assert.match(
  backendRouter,
  /@router\.get\("\/\{exam_id\}\/history"[\s\S]*?require_doctor_permission\("exams:read"\)/,
)

const listSchema = backendSchema
  .split('class ExamListItemResponse')[1]
  .split('class ExamResponse')[0]

assert.match(listSchema, /clinic_name:\s*str \| None = None/)

assert.match(
  listSchema,
  /description:\s*str/,
  'A listagem resumida deve expor a descrição operacional do exame.',
)

for (const forbiddenField of [
  'observations:',
  'clinical_indication:',
  'findings:',
  'conclusion:',
  'ai_prediction_label:',
  'ai_prediction_class:',
  'patient_cpf:',
  'file_name:',
]) {
  assert.doesNotMatch(
    listSchema,
    new RegExp(forbiddenField),
    `A listagem resumida expõe ${forbiddenField}`,
  )
}

assert.match(
  backendService,
  /elif role_name == RoleName\.CLINIC_MANAGER\.value:[\s\S]*?Exam\.clinic_id == current_user\.clinic_id/,
)

assert.match(backendService, /Gestor da clínica não tem permissão para filtrar por resultado da IA/)

assert.match(roleRoute, /const roleAllowed =/)

assert.match(roleRoute, /if \(!roleAllowed\)/)

assert.match(roleRoute, /requiredPermission &&[\s\S]*!hasPermission\(user, requiredPermission\)/)

assert.match(backendService, /return \[[\s\S]*?build_exam_list_response\(exam\) for exam in exams/)

const managerPermissions = roleSeed.split('CLINIC_MANAGER_PERMISSIONS = [')[1].split(']')[0]

assert.match(managerPermissions, /"exams:list"/)

for (const forbiddenPermission of [
  'exams:read',
  'exams:create',
  'exams:update',
  'exams:download',
  'exams:review',
  'ai_analysis:read',
]) {
  assert.doesNotMatch(
    managerPermissions,
    new RegExp(`"${forbiddenPermission}"`),
    `Gestor recebeu indevidamente ${forbiddenPermission}`,
  )
}

assert.match(
  examsList,
  /const hasOperationalExamAccess =[\s\S]*?ROLES\.ADMIN_MASTER[\s\S]*?ROLES\.CLINIC_MANAGER/,
)

assert.match(
  examsList,
  /hasOperationalExamAccess && \([\s\S]*?acesso exclusivamente operacional à listagem de exames[\s\S]*?restritos aos[\s\S]*?médicos responsáveis/,
)

console.log(
  'Acesso de exames aprovado: Médico recebe ações clínicas; Gestor e Administrador recebem somente a listagem operacional.',
)
