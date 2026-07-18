/**
 * Verifica o layout compartilhado de cadastro e edição de exames.
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
  form,
  constants,
  backendService,
] = await Promise.all([
  read(
    'frontend/src/views/exams/ExamForm.jsx',
  ),
  read(
    'frontend/src/utils/constants.js',
  ),
  read(
    'backend/app/modules/exams/service.py',
  ),
])

assert.match(
  constants,
  /endoscopy:\s*['"]Endoscopia digestiva alta['"]/,
)

assert.match(
  constants,
  /label:\s*['"]Endoscopia digestiva alta['"]/,
)

assert.match(
  backendService,
  /"cpf": patient\.cpf/,
)

assert.match(
  backendService,
  /"birth_date": patient\.birth_date/,
)

assert.match(
  form,
  /const buildPatientOptionLabel = \(patient\) =>[\s\S]*?patient\?\.name/,
)

assert.doesNotMatch(
  form,
  /return `\$\{patientName\} — \$\{patientCpf\}`/,
)

assert.match(
  form,
  /list=['"]exam-patient-options['"]/,
)

assert.match(
  form,
  /<datalist id=['"]exam-patient-options['"]>/,
)

assert.match(
  form,
  /selectedPatientCpf/,
)

assert.match(
  form,
  /selectedPatientAge/,
)

assert.match(
  form,
  /responsibleDoctorName/,
)

assert.match(
  form,
  /<CCol md=\{6\}>\s*<div className="text-body-secondary small mb-1">\s*Clínica/,
)

assert.match(
  form,
  /Clínica[\s\S]*?<div className="fw-semibold">\s*\{selectedClinicName\}/,
)

assert.match(
  form,
  /Médico responsável[\s\S]*?<div className="fw-semibold">\s*\{responsibleDoctorName\}/,
)

assert.match(
  form,
  /<CCol md=\{8\}>[\s\S]*?Paciente[\s\S]*?<CCol md=\{2\}>[\s\S]*?CPF[\s\S]*?<CCol md=\{2\}>[\s\S]*?Idade/,
)

assert.match(
  form,
  /<CCol md=\{6\}>[\s\S]*?Título[\s\S]*?<CCol md=\{4\}>[\s\S]*?Tipo de exame[\s\S]*?<CCol md=\{2\}>[\s\S]*?Data do exame/,
)

assert.match(
  form,
  /Indicação clínica[\s\S]*?rows=\{5\}/,
)

assert.match(
  form,
  /Observações[\s\S]*?rows=\{5\}/,
)

assert.match(
  form,
  /required=\{isCreateMode\}/,
)

assert.match(
  form,
  /selectedFilePreviewUrl \|\|[\s\S]*?originalImageUrl/,
)

console.log(
  'Layout de cadastro e edição aprovado: clínica e médico estáticos, paciente com oito colunas, CPF e idade carregados, tipo/data reorganizados e textareas ampliados.',
)
