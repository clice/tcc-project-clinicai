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
const clinicProfileCard = await readProjectFile('frontend/src/views/profile/ClinicProfileCard.jsx')

const clinicCreateBody = backendSchema.match(
  /class ClinicBase\(StrictRequestModel\):([\s\S]*?)class ClinicUpdate/,
)?.[1]
assert.ok(clinicCreateBody, 'ClinicCreate não foi localizado no schema')
assert.doesNotMatch(
  clinicCreateBody,
  /status_id/,
  'ClinicCreate não deve aceitar status definido pelo cliente',
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
const createClinicBody = backendService.match(/def create_clinic\([\s\S]*?def update_clinic\(/)?.[0]
assert.ok(createClinicBody, 'create_clinic não foi localizado no service')
assert.match(createClinicBody, /name=StatusName\.ACTIVE\.value/)
assert.match(createClinicBody, /data\["status_id"\] = active_status\.id/)
assert.doesNotMatch(createClinicBody, /payload\.status_id/)

assert.doesNotMatch(clinicForm, /statusService/)
assert.doesNotMatch(clinicForm, /form\.status_id/)
assert.doesNotMatch(clinicForm, /<CFormLabel>Status<\/CFormLabel>/)
assert.match(
  clinicForm,
  /<CCol md=\{8\}>[\s\S]*?<CFormLabel>Nome<\/CFormLabel>[\s\S]*?<CCol md=\{4\}>[\s\S]*?<CFormLabel>CNPJ<\/CFormLabel>/,
)
assert.match(
  clinicForm,
  /<CCol md=\{2\}>[\s\S]*?<CFormLabel>CEP<\/CFormLabel>[\s\S]*?<CCol md=\{8\}>[\s\S]*?<CFormLabel>Endereço<\/CFormLabel>[\s\S]*?<CCol md=\{2\}>[\s\S]*?<CFormLabel>Número<\/CFormLabel>/,
)
assert.match(
  clinicForm,
  /<CCol md=\{10\}>[\s\S]*?<CFormLabel>Complemento<\/CFormLabel>[\s\S]*?<CCol md=\{2\}>[\s\S]*?<CFormLabel>UF<\/CFormLabel>/,
)
assert.match(
  clinicForm,
  /<CCol md=\{6\}>[\s\S]*?<CFormLabel>Bairro<\/CFormLabel>[\s\S]*?<CCol md=\{6\}>[\s\S]*?<CFormLabel>Cidade<\/CFormLabel>/,
)
assert.doesNotMatch(
  clinicProfileCard,
  /status_id\s*:/,
  'Autoedição da clínica não deve enviar status_id',
)

console.log(
  'Contrato de clínicas coerente: status dedicado, perfil próprio, isolamento e efeitos auditáveis.',
)
