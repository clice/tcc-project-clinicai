/**
 * Verifica a organização da visualização e revisão de exames
 * sem alterar o formulário compartilhado de cadastro e edição.
 */

import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))

const projectDirectory = path.resolve(scriptDirectory, '..', '..')

const read = (relativePath) => readFile(path.join(projectDirectory, relativePath), 'utf8')

const [form, aiCard, summaryHeader, examService, downloadNames, history] = await Promise.all([
  read('frontend/src/views/exams/ExamForm.jsx'),
  read('frontend/src/views/exams/ExamAiResultCard.jsx'),
  read('frontend/src/views/exams/ExamSummaryHeader.jsx'),
  read('frontend/src/services/examService.js'),
  read('frontend/src/utils/examDownloadNames.js'),
  read('frontend/src/views/exams/ExamHistoryCard.jsx'),
])

const examCardStart = form.indexOf('  const examDataCard = (')

const viewContentStart = form.indexOf('  const examDataViewContent = (')

const examCard = form.slice(examCardStart, viewContentStart)

assert.ok(
  examCardStart >= 0 && viewContentStart > examCardStart,
  'O formulário cadastral deve continuar isolado.',
)

assert.match(examCard, /'Dados Cadastrais do Exame'/)

assert.match(examCard, /'Editar Dados do Exame'/)

assert.match(
  examCard,
  /<CCol lg=\{8\}>[\s\S]*?<CFormLabel htmlFor="exam-patient-search">Paciente<\/CFormLabel>/,
)

assert.match(examCard, /<CCol md=\{9\}>[\s\S]*?Paciente/)

assert.match(examCard, /<CCol md=\{3\}>[\s\S]*?CPF/)

assert.match(examCard, /<CCol md=\{6\}>[\s\S]*?Tipo de exame/)

assert.match(examCard, /<CCol md=\{3\}>[\s\S]*?Data do exame/)

assert.match(examCard, /<CCol md=\{3\}>[\s\S]*?Idade/)

assert.match(
  examCard,
  /<CFormLabel>Indicação clínica<\/CFormLabel>[\s\S]*?<CFormTextarea[\s\S]*?rows=\{2\}/,
)

assert.match(
  examCard,
  /<CFormLabel>Observações<\/CFormLabel>[\s\S]*?<CFormTextarea[\s\S]*?rows=\{2\}/,
)

assert.match(
  examCard,
  /<CCol lg=\{4\}>[\s\S]*?<CFormLabel>Imagem do exame<\/CFormLabel>/,
)

assert.match(examCard, /selectedFilePreviewUrl/)

assert.match(examCard, /required=\{isCreateMode\}/)

assert.match(form, /examService\.replaceFile\(/)

assert.match(
  form,
  /const isPendingView =[\s\S]*?\['pending', 'failed', 'canceled'\]\.includes\([\s\S]*?form\.status_name/,
)

assert.match(examCard, /Descrição/)

assert.doesNotMatch(examCard, /\bTítulo\b/)

const examViewStart = form.indexOf('  const examDataViewContent = (')

const examViewEnd = form.indexOf('  const examDataViewCard = (', examViewStart)

const examView = form.slice(examViewStart, examViewEnd)

const clinicPosition = examView.indexOf('Clínica')

const doctorPosition = examView.indexOf('Médico responsável')

const indicationPosition = examView.indexOf('Indicação clínica')

const observationsPosition = examView.indexOf('Observações')

assert.ok(
  examViewStart >= 0 &&
    examViewEnd > examViewStart &&
    clinicPosition >= 0 &&
    doctorPosition > clinicPosition &&
    indicationPosition > doctorPosition &&
    observationsPosition > indicationPosition,
  'A visualização deve apresentar clínica/médico, indicação clínica e observações nessa ordem.',
)

assert.doesNotMatch(examView, /Identificação do exame/)

assert.doesNotMatch(examView, />\s*Descrição\s*</)

assert.match(examView, /Clínica[\s\S]*?<div className="fw-semibold">\s*\{selectedClinicName\}/)

assert.match(
  examView,
  /Médico responsável[\s\S]*?<div className="fw-semibold">\s*\{selectedDoctorName\}/,
)

assert.doesNotMatch(examView, /Identificação do exame/)

assert.match(form, /<ExamSummaryHeader/)

assert.match(summaryHeader, /calculateAge/)

assert.match(summaryHeader, /examTypeLabels/)

assert.match(summaryHeader, /formatDateBR/)

assert.match(summaryHeader, /patientCpf/)

assert.match(summaryHeader, /resolvedPatientCpf/)

assert.match(summaryHeader, /\{resolvedPatientCpf\}/)

assert.match(summaryHeader, /resolvedAge/)

assert.doesNotMatch(summaryHeader, /statusColors/)

assert.doesNotMatch(summaryHeader, /<CBadge/)

assert.match(form, /statusColors\[\s*form\.status_name/)

assert.match(form, /examStatusDisplayLabels\[\s*form\.status_name/)

assert.match(
  form,
  /<div className="mb-4">\s*\{examDataViewCard\}\s*<\/div>[\s\S]*?<ExamAiResultCard[\s\S]*?<ExamHistoryCard/,
)

assert.match(form, /reviewPanel=\{reviewPanel\}/)

assert.match(form, /bg-warning-subtle/)

assert.match(form, /defaultOpen=\{false\}/)

assert.match(form, /const pendingExamCard = \(\s*<CCard className="mb-4">/)

assert.match(history, /<CCard className="mb-4">/)

assert.match(aiCard, /cilCloudDownload/)

assert.match(aiCard, /title="Baixar imagem original e mapa de atribuição"/)

assert.doesNotMatch(aiCard, />\s*Baixar imagem e mapa\s*</)

assert.match(aiCard, /onPackageDownload/)

assert.match(aiCard, /Mapa de atribuição composto/)

assert.match(aiCard, /Mapa Grad-CAM \(ResNet-50\)/)

assert.match(examService, /downloadImagePackage/)

assert.match(downloadNames, /buildExamImagesPackageDownloadName/)

assert.doesNotMatch(aiCard, /onOriginalDownload/)

assert.doesNotMatch(aiCard, /onGradcamDownload/)

assert.doesNotMatch(aiCard, />\s*Baixar imagem original\s*</)

const scalePosition = aiCard.indexOf('contributionScaleStyle')

const originalPosition = aiCard.indexOf('id="original-image-title"')

const mapPosition = aiCard.indexOf('id="attribution-image-title"')

const analysisPosition = aiCard.indexOf('id="analysis-data-title"')

assert.ok(
  scalePosition >= 0 &&
    originalPosition > scalePosition &&
    mapPosition > scalePosition &&
    analysisPosition > mapPosition,
  'A ordem deve ser escala/download, imagens e dados da análise.',
)

assert.match(form, /icon=\{cilWarning\}/)

assert.match(form, /rgba\(var\(--cui-warning-rgb\), 0\.12\)/)

assert.match(form, /completed_with_divergence[\s\S]*?border-dark/)

assert.match(form, /rgba\(var\(--cui-dark-rgb\), 0\.08\)/)

assert.match(form, /\? 'dark'[\s\S]*?: 'success'/)

console.log(
  'Layout aprovado: ações por ícone alinhadas à escala, alerta amarelo claro com atenção e divergência em tonalidade escura.',
)
