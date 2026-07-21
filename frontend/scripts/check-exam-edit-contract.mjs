/** Verifica o contrato da tela unificada de exames pendentes. */

import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const projectDirectory = path.resolve(scriptDirectory, '..', '..')

const read = (relativePath) => readFile(path.join(projectDirectory, relativePath), 'utf8')

const [routes, form, list, service, router, schema, backendService] = await Promise.all([
  read('frontend/src/routes.js'),
  read('frontend/src/views/exams/ExamForm.jsx'),
  read('frontend/src/views/exams/ExamsList.jsx'),
  read('frontend/src/services/examService.js'),
  read('backend/app/modules/exams/router.py'),
  read('backend/app/modules/exams/schema.py'),
  read('backend/app/modules/exams/service.py'),
])

assert.doesNotMatch(
  routes,
  /const EditExam/,
  'O exame não deve manter componente exclusivo de edição.',
)

assert.doesNotMatch(
  routes,
  /path:\s*['"]\/exams\/:id\/edit['"]/,
  'A rota exclusiva de edição deve permanecer removida.',
)

const detailRouteMatch = routes.match(/\{\s*path:\s*['"]\/exams\/:id['"][\s\S]*?\n\s*\},/)

assert.ok(detailRouteMatch, 'A rota canônica do exame não foi encontrada.')

const detailRoute = detailRouteMatch[0]

assert.match(detailRoute, /roles:\s*\[['"]doctor['"]\]/)

assert.match(detailRoute, /permission:\s*['"]exams:read['"]/)

assert.match(
  list,
  /editTo=\{`\/exams\/\$\{exam\.id\}`\}/,
  'A edição deve abrir a rota canônica do exame.',
)

assert.match(
  list,
  /viewTo=\{[\s\S]*?!isPending \|\| !canEditExam[\s\S]*?`\/exams\/\$\{exam\.id\}`/,
  'A visualização deve ser ocultada quando o exame pendente puder ser editado.',
)

assert.match(list, /canEdit=\{canEditExam && isPending\}/)

assert.match(
  form,
  /const canEditExistingExam =[\s\S]*?PERMISSIONS\.EXAMS_UPDATE[\s\S]*?form\.status_name === ['"]pending['"]/,
  'Somente exame pendente com permissão deve ser editável.',
)

assert.match(form, /const isEditMode = canEditExistingExam/)

assert.match(form, /const isReadOnly = !isCreateMode && !isEditMode/)

assert.match(
  form,
  /const canAnalyze = canOfferAnalysis && !isDirty/,
  'A análise deve aguardar o salvamento das alterações.',
)

assert.match(form, /Salve as alterações do exame antes de executar a análise de IA\./)

assert.match(form, /await examService\.replaceFile\(id, selectedFile\)/)

assert.match(form, /setSelectedFile\(null\)[\s\S]*?setIsDirty\(false\)/)

assert.match(
  form,
  /key=\{fileInputKey\}[\s\S]*?type="file"[\s\S]*?required=\{isCreateMode\}/,
  'A imagem deve continuar obrigatória somente no cadastro.',
)

assert.match(
  form,
  /id="exam-patient-search"[\s\S]*?required/,
  'O paciente deve continuar obrigatório.',
)

assert.match(
  form,
  /value=\{form\.description\}[\s\S]*?required/,
  'A descrição deve continuar obrigatória.',
)

assert.match(
  form,
  /value=\{form\.exam_type\}[\s\S]*?required/,
  'O tipo do exame deve continuar obrigatório.',
)

assert.match(
  form,
  /isEditMode && canDownloadExamFile && originalImageUrl/,
  'A tela editável deve disponibilizar o download da imagem atual.',
)

assert.match(form, /onClick=\{handleOriginalDownload\}/)

assert.match(form, /<ExamHistoryCard/)

assert.match(router, /require_doctor_permission\(["']exams:update["']\)/)

assert.match(router, /require_doctor_permission\(["']exams:upload["']\)/)

assert.match(schema, /patient_id:\s*int \| None = Field\(default=None, gt=0\)/)

assert.match(backendService, /Apenas usuários com perfil médico[\s\S]*?podem editar exames/)

assert.match(service, /replaceFile:\s*async/)

console.log(
  'Contrato da tela unificada aprovado: rota canônica, edição pendente, campos obrigatórios, download, análise protegida e histórico preservado.',
)
