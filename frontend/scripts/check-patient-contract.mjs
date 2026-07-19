/** Verifica o contrato CHK-08 entre frontend e backend de pacientes. */

import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const projectDirectory = path.resolve(scriptDirectory, '..', '..')
const readProjectFile = (relativePath) =>
  readFile(path.join(projectDirectory, relativePath), 'utf8')

const [router, schema, service, userService, patientService, form, list] = await Promise.all([
  readProjectFile('backend/app/modules/patients/router.py'),
  readProjectFile('backend/app/modules/patients/schema.py'),
  readProjectFile('backend/app/modules/patients/service.py'),
  readProjectFile('backend/app/modules/users/service.py'),
  readProjectFile('frontend/src/services/patientService.js'),
  readProjectFile('frontend/src/views/patients/PatientForm.jsx'),
  readProjectFile('frontend/src/views/patients/PatientsList.jsx'),
])

assert.match(router, /search: str \| None = Query\(default=None\)/)
assert.match(router, /clinic_id: int \| None = Query\(default=None\)/)
assert.match(router, /doctor_id: int \| None = Query\(default=None\)/)

assert.match(schema, /class PatientUpdate\(StrictRequestModel\)/)
assert.doesNotMatch(
  schema.split('class PatientUpdate')[1].split('class PatientResponse')[0],
  /^\s+status_id\s*:/m,
  'PatientUpdate não deve permitir alteração genérica de status',
)

assert.match(service, /def validate_patient_assignment_change/)
assert.match(service, /def patient_has_exams/)
assert.match(service, /Médicos não podem transferir o paciente/)
assert.match(service, /paciente já possui exames vinculados/)
assert.match(service, /def list_patients[\s\S]*?filter_query_by_user_scope/)
assert.match(service, /Médicos só podem filtrar os próprios pacientes/)
assert.match(service, /def activate_patient[\s\S]*?validate_clinic_is_active/)
assert.match(service, /def activate_patient[\s\S]*?validate_doctor_can_be_assigned/)
assert.match(service, /if patient\.status and patient\.status\.name == StatusName\.ACTIVE\.value/)
assert.match(service, /if patient\.status and patient\.status\.name == StatusName\.INACTIVE\.value/)

assert.match(userService, /def ensure_doctor_has_no_active_patients/)
assert.match(userService, /Reatribua ou inative esses[\s\S]*?pacientes/)

assert.match(patientService, /search: search \|\| undefined/)
assert.match(patientService, /clinic_id: clinicId \|\| undefined/)
assert.match(patientService, /doctor_id: doctorId \|\| undefined/)

assert.match(form, /if \(isCreateMode \|\| !isDoctor\)/)
assert.match(form, /status_display_name \|\| form\.status_name/)

assert.equal(
  (
    form.match(
      /<CCol xs=\{12\}>/g,
    ) || []
  ).length,
  2,
  'Dados e histórico devem ocupar toda a largura.',
)

assert.doesNotMatch(
  form,
  /lg=\{isCreateMode \|\| !hasPatientExams \? 12 : 8\}/,
)

assert.doesNotMatch(
  form,
  /<CCol lg=\{4\}>/,
)

assert.match(
  form,
  /maxHeight:\s*'420px'/,
)

assert.match(
  form,
  /overflowY:\s*'auto'/,
)

assert.match(
  form,
  /tabIndex=\{0\}/,
)

assert.match(
  form,
  /aria-label="Histórico de exames do paciente"/,
)

const patientDataPosition =
  form.indexOf(
    '<strong>Dados do Paciente</strong>',
  )

const patientHistoryPosition =
  form.indexOf(
    '<strong>Histórico de Exames</strong>',
  )

assert.ok(
  patientDataPosition >= 0 &&
    patientHistoryPosition >
      patientDataPosition,
  'O histórico deve aparecer depois dos dados do paciente.',
)
assert.match(list, /ROLES\.DOCTOR/)
assert.match(list, /ROLES\.CLINIC_STAFF/)

assert.match(
  list,
  /const showDoctorColumn = roleName !== ROLES\.DOCTOR/,
)

assert.match(
  list,
  /const showClinicColumn = roleName === ROLES\.ADMIN_MASTER/,
)

assert.match(
  list,
  /\.\.\.\(\s*showDoctorColumn\s*\?\s*\[\s*\{\s*accessorKey:\s*['"]doctor_name['"]/,
)

assert.match(
  list,
  /\.\.\.\(\s*showClinicColumn\s*\?\s*\[\s*\{\s*accessorKey:\s*['"]clinic_name['"]/,
)

assert.match(
  list,
  /\[\s*canView,\s*canEdit,\s*canChangeStatus,\s*loadPatients,\s*showClinicColumn,\s*showDoctorColumn,?\s*\]/,
)
assert.match(list, /Buscar por paciente, CPF, médico ou clínica/)

console.log(
  'Contrato de pacientes coerente: escopo, vínculos, colunas por perfil, status, filtros e histórico em largura total validados.',
)
