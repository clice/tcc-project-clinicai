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
assert.doesNotMatch(
  form,
  /<CFormLabel>Status<\/CFormLabel>/,
  'O status do paciente deve ser alterado somente pela listagem.',
)

assert.equal(
  (form.match(/<CCol xs=\{12\}>/g) || []).length,
  2,
  'Dados e histórico devem ocupar toda a largura.',
)

assert.doesNotMatch(form, /lg=\{isCreateMode \|\| !hasPatientExams \? 12 : 8\}/)

assert.doesNotMatch(form, /<CCol lg=\{4\}>/)

assert.match(form, /maxHeight:\s*'420px'/)

assert.match(form, /overflowY:\s*'auto'/)

assert.match(form, /tabIndex=\{0\}/)

assert.match(form, /aria-label="Histórico de exames do paciente"/)

assert.match(form, /PERMISSIONS\.EXAMS_LIST/)
assert.match(form, /const canListExams/)
assert.match(form, /Histórico de Exames \(\{patientExams\.length\}\)/)
assert.match(form, /\{isDoctor && canReadExams && \([\s\S]*?to=\{`\/exams\/\$\{exam\.id\}`\}/)

const patientDataPosition = form.indexOf('<strong>Dados do Paciente</strong>')

const patientHistoryPosition = form.indexOf('<strong>Histórico de Exames (')

assert.ok(
  patientDataPosition >= 0 && patientHistoryPosition > patientDataPosition,
  'O histórico deve aparecer depois dos dados do paciente.',
)
assert.match(list, /ROLES\.DOCTOR/)
assert.match(list, /ROLES\.CLINIC_MANAGER/)

assert.match(list, /const showDoctorColumn = roleName !== ROLES\.DOCTOR/)

assert.match(list, /const showClinicColumn = roleName === ROLES\.ADMIN_MASTER/)

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
  /\[\s*canEdit,\s*canChangeStatus,\s*handleChangeStatus,\s*showClinicColumn,\s*showDoctorColumn,?\s*\]/,
)
assert.doesNotMatch(
  list,
  /type="search"/,
  'A listagem de pacientes não deve exibir o campo de busca removido.',
)

assert.match(
  form,
  /<CCol key=\{exam\.id\} xs=\{12\} md=\{6\} lg=\{4\}>/,
  'O histórico deve exibir três cards por linha em telas grandes.',
)

assert.match(
  form,
  /\{isDoctor && canReadExams && \(/,
  'Somente o médico pode receber a ação de abrir o exame no histórico.',
)

assert.doesNotMatch(
  form,
  /\{canReadExams && \(/,
  'A permissão isolada de leitura não deve expor a ação clínica.',
)

assert.match(
  form,
  /\{patient\?\.status_name === 'active' && isDoctor && canCreateExam && \(/,
  'Somente médicos podem receber a ação de cadastrar exame pelo paciente.',
)

assert.doesNotMatch(
  form,
  /\{patient\?\.status_name === 'active' && canCreateExam && \(/,
  'A permissão isolada de criação não deve expor a ação ao administrador.',
)

assert.doesNotMatch(form, /mode === 'view'/)
assert.match(form, /const isReadOnly = isArchiveMode/)
assert.match(
  form,
  /Esta tela permite alterar os dados do paciente\./,
  'A edição deve informar que o salvamento altera os dados.',
)
assert.doesNotMatch(list, /viewTo=\{`\/patients\//)
assert.doesNotMatch(list, /canView=\{canView\}/)

console.log(
  'Contrato de pacientes coerente: escopo, vínculos, status e histórico contado com acesso não clínico do gestor validados.',
)
