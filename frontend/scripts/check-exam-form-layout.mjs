/**
 * Verifica o layout compartilhado de cadastro e edição de exames.
 */

import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))

const projectDirectory = path.resolve(scriptDirectory, '..', '..')

const read = (relativePath) => readFile(path.join(projectDirectory, relativePath), 'utf8')

const [form, constants, backendService] = await Promise.all([
  read('frontend/src/views/exams/ExamForm.jsx'),
  read('frontend/src/utils/constants.js'),
  read('backend/app/modules/exams/service.py'),
])

assert.match(constants, /endoscopy:\s*['"]Endoscopia digestiva alta['"]/)

assert.match(constants, /label:\s*['"]Endoscopia digestiva alta['"]/)

assert.match(backendService, /"cpf": patient\.cpf/)

assert.match(backendService, /"birth_date": patient\.birth_date/)

assert.match(form, /const buildPatientOptionLabel = \(patient\) =>[\s\S]*?patient\?\.name/)

assert.doesNotMatch(form, /return `\$\{patientName\} — \$\{patientCpf\}`/)

assert.match(form, /list=['"]exam-patient-options['"]/)

assert.match(form, /<datalist id=['"]exam-patient-options['"]>/)

assert.match(form, /selectedPatientCpf/)

assert.match(form, /selectedPatientAge/)

assert.match(form, /responsibleDoctorName/)

assert.match(
  form,
  /<CCol lg=\{8\}>[\s\S]*?<CCol lg=\{4\}>[\s\S]*?Imagem do exame/,
  'Os dados devem ocupar oito colunas e a imagem quatro colunas.',
)

assert.match(
  form,
  /<CCol md=\{6\}>[\s\S]*?Clínica[\s\S]*?<CCol md=\{6\}>[\s\S]*?Médico responsável/,
  'Clínica e médico devem dividir igualmente as oito colunas de dados.',
)

assert.match(form, /Clínica[\s\S]*?<div className="fw-semibold">\s*\{selectedClinicName\}/)

assert.match(
  form,
  /Médico responsável[\s\S]*?<div className="fw-semibold">\s*\{responsibleDoctorName\}/,
)

assert.match(
  form,
  /<CCol md=\{9\}>[\s\S]*?Paciente[\s\S]*?<CCol md=\{3\}>[\s\S]*?CPF/,
  'Paciente deve ocupar nove colunas visuais e CPF três.',
)

assert.match(
  form,
  /<CCol md=\{6\}>[\s\S]*?Tipo de exame[\s\S]*?<CCol md=\{3\}>[\s\S]*?Data do exame/,
  'Tipo deve ocupar quatro colunas visuais e data duas.',
)

assert.match(
  form,
  /<CCol md=\{12\}>[\s\S]*?Descrição/,
  'Descrição deve ocupar as oito colunas da área de dados.',
)

assert.match(form, /<CCol md=\{12\}>[\s\S]*?Indicação clínica[\s\S]*?rows=\{2\}/)

assert.match(form, /<CCol md=\{12\}>[\s\S]*?Observações[\s\S]*?rows=\{2\}/)

assert.match(
  form,
  /Miniatura da imagem[\s\S]*?selectedFilePreviewUrl[\s\S]*?isEditMode && canDownloadExamFile && originalImageUrl[\s\S]*?onClick=\{handleOriginalDownload\}/,
  'O download deve aparecer abaixo da imagem na edição.',
)

assert.match(form, /required=\{isCreateMode\}/)

assert.match(form, /selectedFilePreviewUrl \|\|[\s\S]*?originalImageUrl/)

console.log(
  'Layout aprovado: dados em oito colunas, imagem em quatro, campos clínicos reorganizados, textareas com duas linhas e download abaixo da imagem.',
)
