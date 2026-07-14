/** Verifica o contrato frontend/backend consolidado na CHK-06. */

import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const projectDirectory = path.resolve(scriptDirectory, '..', '..')
const readProjectFile = (relativePath) =>
  readFile(path.join(projectDirectory, relativePath), 'utf8')

const backendSchema = await readProjectFile('backend/app/modules/clinics/schema.py')
const backendRouter = await readProjectFile('backend/app/modules/clinics/router.py')
const backendService = await readProjectFile('backend/app/modules/clinics/service.py')
const clinicService = await readProjectFile('frontend/src/services/clinicService.js')
const clinicForm = await readProjectFile('frontend/src/views/clinics/ClinicForm.jsx')
const profilePage = await readProjectFile('frontend/src/views/profile/ProfilePage.jsx')
const clinicProfileCard = await readProjectFile(
  'frontend/src/views/profile/ClinicProfileCard.jsx',
)

const clinicUpdateBody = backendSchema.match(
  /class ClinicUpdate\(StrictRequestModel\):([\s\S]*?)class ClinicResponse/,
)?.[1]
assert.ok(clinicUpdateBody, 'ClinicUpdate não foi localizado no schema')
assert.doesNotMatch(
  clinicUpdateBody,
  /status_id/,
  'ClinicUpdate não deve permitir alteração genérica de status',
)

assert.match(backendRouter, /@router\.patch\("\/\{clinic_id\}\/inactivate"/)
assert.match(backendRouter, /@router\.patch\("\/\{clinic_id\}\/activate"/)
assert.match(backendRouter, /@router\.get\("\/me"/)
assert.match(backendRouter, /@router\.patch\("\/me"/)
assert.match(backendRouter, /return build_clinic_response\(clinic\)/)

assert.match(backendService, /func\.lower\(Clinic\.email\)/)
assert.match(backendService, /associated_patients/)
assert.match(backendService, /associated_exams/)
assert.match(backendService, /related_records_preserved/)

assert.match(clinicService, /getMyClinic/)
assert.match(clinicService, /updateMyClinic/)
assert.match(profilePage, /ClinicProfileCard/)
assert.match(profilePage, /CLINICS_READ_PROFILE/)
assert.match(profilePage, /CLINICS_UPDATE_PROFILE/)
assert.match(clinicForm, /disabled=\{!isCreateMode\}/)
assert.match(clinicForm, /\.\.\.\(isCreateMode/)
assert.doesNotMatch(
  clinicProfileCard,
  /status_id\s*:/,
  'Autoedição da clínica não deve enviar status_id',
)

console.log(
  'Contrato de clínicas coerente: status dedicado, perfil próprio, isolamento e efeitos auditáveis.',
)
