/**
 * Verifica o contrato da edição de exames pendentes.
 */

import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(
  fileURLToPath(import.meta.url),
)

const projectDirectory = path.resolve(
  scriptDirectory,
  '..',
  '..',
)

const read = (relativePath) =>
  readFile(
    path.join(
      projectDirectory,
      relativePath,
    ),
    'utf8',
  )

const [
  routes,
  form,
  list,
  service,
  router,
  schema,
  backendService,
] = await Promise.all([
  read('frontend/src/routes.js'),
  read(
    'frontend/src/views/exams/ExamForm.jsx',
  ),
  read(
    'frontend/src/views/exams/ExamsList.jsx',
  ),
  read(
    'frontend/src/services/examService.js',
  ),
  read(
    'backend/app/modules/exams/router.py',
  ),
  read(
    'backend/app/modules/exams/schema.py',
  ),
  read(
    'backend/app/modules/exams/service.py',
  ),
])

const editRouteMatch = routes.match(
  /\{\s*path:\s*['"]\/exams\/:id\/edit['"][\s\S]*?\n\s*\},/,
)

assert.ok(
  editRouteMatch,
  'A rota de edição do exame não foi encontrada.',
)

const editRoute = editRouteMatch[0]

assert.match(
  editRoute,
  /roles:\s*\[['"]doctor['"]\]/,
)

assert.doesNotMatch(
  editRoute,
  /admin_master/,
)

assert.match(
  editRoute,
  /permission:\s*['"]exams:update['"]/,
)

assert.match(
  list,
  /const canEditExam = roleName === ROLES\.DOCTOR && canEdit/,
)

assert.match(
  list,
  /canEdit=\{canEditExam && isPending\}/,
)

assert.match(
  router,
  /require_doctor_permission\(["']exams:update["']\)/,
)

assert.match(
  router,
  /require_doctor_permission\(["']exams:upload["']\)/,
)

assert.match(
  schema,
  /patient_id:\s*int \| None = Field\(default=None, gt=0\)/,
)

assert.match(
  backendService,
  /Apenas usuários com perfil médico[\s\S]*?podem editar exames/,
)

assert.match(
  backendService,
  /copy_exam_file_to_storage/,
)

assert.match(
  form,
  /selectedFilePreviewUrl/,
)

assert.match(
  form,
  /await examService\.replaceFile/,
)

assert.match(
  service,
  /replaceFile:\s*async/,
)

assert.match(
  form,
  /\) : isEditMode \? \([\s\S]*?examDataCard[\s\S]*?<ExamHistoryCard[\s\S]*?defaultOpen=\{false\}/,
)

console.log(
  'Contrato da edição aprovado: somente médico, exame pendente, paciente corrigível, substituição de imagem e histórico recolhido.',
)
