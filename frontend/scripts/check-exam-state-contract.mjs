import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const repositoryRoot = path.resolve(scriptDir, '..', '..')
const read = (relativePath) => fs.readFileSync(path.join(repositoryRoot, relativePath), 'utf8')

const constants = read('frontend/src/utils/constants.js')
const form = read('frontend/src/views/exams/ExamForm.jsx')
const patientForm = read('frontend/src/views/patients/PatientForm.jsx')
const list = read('frontend/src/views/exams/ExamsList.jsx')
const history = read('frontend/src/views/exams/ExamHistoryCard.jsx')
const aiResultCard = read('frontend/src/views/exams/ExamAiResultCard.jsx')
const summaryHeader = read('frontend/src/views/exams/ExamSummaryHeader.jsx')
const navigation = read('frontend/src/_nav.jsx')
const service = read('frontend/src/services/examService.js')
const downloadNames = read('frontend/src/utils/examDownloadNames.js')
const stateMachine = read('backend/app/modules/exams/state_machine.py')
const examService = read('backend/app/modules/exams/service.py')
const examRouter = read('backend/app/modules/exams/router.py')

const requiredStatuses = [
  'pending',
  'processing',
  'awaiting_review',
  'completed',
  'completed_with_divergence',
  'failed',
  'canceled',
]

for (const status of requiredStatuses) {
  if (!constants.includes(`${status}:`)) {
    throw new Error(`Status de exame ausente no catálogo do frontend: ${status}`)
  }
  if (!stateMachine.includes(`StatusName.${status.toUpperCase()}.value`)) {
    throw new Error(`Status de exame ausente na máquina de estados: ${status}`)
  }
}

const editableStatusesMatch = stateMachine.match(
  /EDITABLE_EXAM_STATUSES = frozenset\(([\s\S]*?)\n\)/,
)

if (
  !editableStatusesMatch ||
  !editableStatusesMatch[1].includes('StatusName.PENDING.value') ||
  editableStatusesMatch[1].includes('StatusName.FAILED.value') ||
  editableStatusesMatch[1].includes('StatusName.PROCESSING.value')
) {
  throw new Error('Somente exames pending podem ter metadados editados.')
}

const requiredActions = [
  'CREATE',
  'START_PROCESSING',
  'CANCEL',
  'RESTORE',
  'REPLACE_FILE',
  'ANALYSIS_SUCCEEDED',
  'ANALYSIS_FAILED',
  'REVIEW_CONFIRM',
  'REVIEW_DIVERGENCE',
]
for (const action of requiredActions) {
  if (!stateMachine.includes(`${action} =`)) {
    throw new Error(`Ação ausente na máquina de estados: ${action}`)
  }
}

if (!service.includes('api.post(`/exams/${id}/analyze`)')) {
  throw new Error('O frontend não expõe o disparo protegido da análise de IA.')
}
if (!form.includes("form.status_name === 'pending'") || !form.includes('analysis_in_progress')) {
  throw new Error('A interface não bloqueia repetição visual da análise em andamento.')
}
if (!form.includes("form.status_name === 'awaiting_review'")) {
  throw new Error('A revisão médica não está condicionada a awaiting_review.')
}
if (!list.includes('canCancel={canChangeStatus && (isProcessing || isPending)}')) {
  throw new Error('A ação de cancelar não reflete pending/processing.')
}
if (!list.includes('canRestore={canChangeStatus && (isCanceled || isFailed)}')) {
  throw new Error('A ação de restaurar não reflete canceled/failed.')
}
if (!list.includes('canEdit={canEditExam && isPending}')) {
  throw new Error(
    'A listagem deve permitir edição somente ao médico e em pending.',
  )
}
if (!list.includes('examStatusDisplayLabels[row.original.status_name]')) {
  throw new Error('A listagem não utiliza o catálogo padronizado de status em português.')
}
if (
  !examService.includes('claim_exam_for_analysis') ||
  !examService.includes('get_exam_model_for_update')
) {
  throw new Error('O backend não contém proteção explícita de concorrência.')
}
if (
  !form.includes('const maxConsecutivePollingErrors = 5') ||
  !form.includes('consecutiveErrors += 1') ||
  !form.includes('consecutiveErrors < maxConsecutivePollingErrors') ||
  !form.includes('window.clearTimeout(timerId)')
) {
  throw new Error('O polling deve limitar erros consecutivos e limpar o timer ao desmontar a tela.')
}
if (!form.includes('navigate(`/exams/${createdExam.id}`)')) {
  throw new Error('O cadastro não redireciona para o exame recém-criado.')
}
if (
  !patientForm.includes("patient?.status_name === 'active'") ||
  !patientForm.includes('to={`/exams/create?patient=${id}`}') ||
  !patientForm.includes('Cadastrar Exame')
) {
  throw new Error(
    'O paciente ativo não oferece corretamente o cadastro de exame pela rota existente.',
  )
}
if (
  !form.includes('useSearchParams') ||
  !form.includes("const requestedPatientId = searchParams.get('patient')") ||
  !form.includes('const canPreselectRequestedPatient = Boolean(') ||
  !form.includes("clinic.status_name === 'active'") ||
  !form.includes("doctor.status_name === 'active'") ||
  !form.includes('patient_id: canPreselectRequestedPatient') ||
  !form.includes('doctor_id: canPreselectRequestedPatient')
) {
  throw new Error(
    'O cadastro de exame não valida e pré-seleciona paciente, clínica e médico a partir da URL.',
  )
}
if (
  !form.includes('const authenticatedDoctorId = useMemo(() => {') ||
  !form.includes('String(patient.doctor_id) ===') ||
  !form.includes('authenticatedDoctorId') ||
  !form.includes('const defaultClinicId =') ||
  !form.includes('const defaultDoctorId =') ||
  !form.includes(': defaultClinicId,') ||
  !form.includes(': defaultDoctorId,') ||
  !form.includes('clinic_id:') ||
  !form.includes('patient?.clinic_id') ||
  !form.includes('doctor_id:') ||
  !form.includes('patient.doctor_id') ||
  !form.includes('responsibleDoctorName') ||
  !form.includes('selectedClinicName')
) {
  throw new Error(
    'O cadastro do exame deve preencher clínica e médico a partir do usuário e do paciente selecionado.',
  )
}

if (
  !patientForm.includes('if (isCreateMode || !patient) return payload') ||
  !patientForm.includes('const originalPayload = {') ||
  !patientForm.includes('Object.fromEntries(') ||
  !patientForm.includes('value !== originalPayload[field]') ||
  !patientForm.includes('Object.keys(payload).length === 0') ||
  !patientForm.includes('setPatient(updatedPatient)')
) {
  throw new Error('A edição do paciente deve enviar somente os campos efetivamente alterados.')
}

if (
  !list.includes("const summaryCardStatuses = ['pending', 'awaiting_review', 'completed']") ||
  list.includes("const summaryCardStatuses = ['pending', 'processing'") ||
  !list.includes('<CCol sm={6} xl={4} key={status}>')
) {
  throw new Error('Os cards devem mostrar somente pendentes, aguardando revisão e concluídos.')
}
if (
  !navigation.includes("name: 'Pendentes'") ||
  !navigation.includes("to: '/exams?status=pending'") ||
  !navigation.includes("badgeKey: 'pending'") ||
  navigation.includes("name: 'Processando'") ||
  navigation.includes("to: '/exams?status=processing'") ||
  navigation.includes("badgeKey: 'processing'")
) {
  throw new Error(
    'A barra lateral deve mostrar pendentes, mas não expor processing como seção permanente.',
  )
}
if (
  !list.includes("exam.status_name === 'processing' && exam.analysis_in_progress") ||
  !list.includes("const isProcessing = exam.status_name === 'processing'") ||
  !list.includes('canCancel={canChangeStatus && (isProcessing || isPending)}') ||
  !stateMachine.includes('StatusName.PROCESSING.value')
) {
  throw new Error(
    'Processing deve permanecer no fluxo interno, na sinalização da análise e nas regras operacionais.',
  )
}

if (
  !history.includes("import React, { useEffect, useRef, useState } from 'react'") ||
  !history.includes('const hasLoadedOnce = useRef(false)') ||
  !history.includes('if (isInitialLoad) setIsLoading(true)')
) {
  throw new Error('O histórico não preserva a exibição durante atualizações silenciosas.')
}
if (
  !form.includes('const [originalImageUrl, setOriginalImageUrl]') ||
  !form.includes('const handleOriginalDownload = async () =>') ||
  !service.includes('previewFile: async (id) =>') ||
  !form.includes('const blob = await examService.previewFile(id)') ||
  !form.includes('const blob = await examService.downloadFile(id)') ||
  !form.includes('buildOriginalDownloadName({') ||
  !form.includes('alt="Imagem original do exame"') ||
  !form.includes('Baixar imagem do exame') ||
  !aiResultCard.includes('alt="Imagem original do exame"') ||
  />\s*Baixar imagem original\s*</.test(aiResultCard) ||
  aiResultCard.includes('onOriginalDownload') ||
  aiResultCard.includes('target="_blank"') ||
  aiResultCard.includes('href={originalImageUrl}') ||
  aiResultCard.includes('href={gradcamUrl}') ||
  form.includes('target="_blank"') ||
  form.includes('href={originalImageUrl}') ||
  form.includes("<CFormInput value={form.file_name || 'Nenhum arquivo vinculado'} disabled />") ||
  form.includes("<div>{form.file_name || '-'}</div>") ||
  form.includes("<div>{form.file_mime_type || '-'}</div>")
) {
  throw new Error(
    'O pendente deve manter o download individual da imagem; a análise deve exibir as imagens sem downloads separados.',
  )
}

if (
  !examRouter.includes('@router.get("/{exam_id}/preview")') ||
  !examRouter.includes('return preview_exam_file(') ||
  !examService.includes('def preview_exam_file(') ||
  !examService.includes('def build_exam_download_filename(') ||
  !examService.includes('content_disposition_type="inline"') ||
  !examService.includes('content_disposition_type="attachment"')
) {
  throw new Error('A prévia automática deve ser separada do download manual auditado.')
}

if (
  !service.includes('previewAiFile: async (id) =>') ||
  !service.includes('`/exams/${id}/ai-file/preview`') ||
  !service.includes('downloadAiFile: async (id) =>') ||
  !examRouter.includes('@router.get("/{exam_id}/ai-file/preview")') ||
  !examRouter.includes('return preview_exam_ai_file(') ||
  !examRouter.includes('@router.get("/{exam_id}/ai-file/download")') ||
  !examService.includes('def get_authorized_gradcam_file(') ||
  !examService.includes('def preview_exam_ai_file(') ||
  !examService.includes('def build_gradcam_download_filename(') ||
  !examService.includes('description="Download do Mapa Grad-CAM autorizado."') ||
  !examService.includes('"artifact_type": "ai_attribution_map"') ||
  !examService.includes('"delivery_mode": "attachment"')
) {
  throw new Error('A prévia do Grad-CAM deve ser separada do download manual auditado.')
}

if ((service.match(/download_request: Date\.now\(\)/g) || []).length !== 3) {
  throw new Error(
    'Os downloads explícitos devem impedir respostas reutilizadas do cache do navegador.',
  )
}

if (
  !form.includes('buildExamImagesPackageDownloadName') ||
  form.includes('buildGradcamDownloadName') ||
  !downloadNames.includes('mapa-grad-cam-exame-') ||
  !downloadNames.includes('imagens-exame-') ||
  !service.includes('downloadImagePackage') ||
  !service.includes('`/exams/${id}/images/download`') ||
  !form.includes('await examService.downloadImagePackage(') ||
  !form.includes('const handlePackageDownload = async () =>')
) {
  throw new Error(
    'A revisão deve baixar a imagem original e o mapa em um único pacote ZIP.',
  )
}

const patientHistoryGuardPattern =
  /\{!isCreateMode && hasPatientExams && \(\s*<CCol lg=\{4\}>[\s\S]*?<strong>Histórico de Exames<\/strong>[\s\S]*?<\/CCol>\s*\)\}/

if (
  !patientForm.includes('<CCol lg={isCreateMode || !hasPatientExams ? 12 : 8}>') ||
  !patientHistoryGuardPattern.test(patientForm)
) {
  throw new Error('O histórico só deve aparecer quando o paciente possuir exames.')
}

if (
  !patientForm.includes("import { examService } from 'src/services/examService'") ||
  !patientForm.includes('const [patientExams, setPatientExams]') ||
  !patientForm.includes('const hasPatientExams = patientExams.length > 0') ||
  !patientForm.includes('const canReadExams = hasPermission(') ||
  !patientForm.includes('const data = await examService.list({') ||
  !patientForm.includes('patientId: id') ||
  !patientForm.includes('includeInactive: true') ||
  !patientForm.includes('patientExams.map((exam) =>') ||
  !patientForm.includes('examStatusDisplayLabels[') ||
  !patientForm.includes('examTypeLabels[exam.exam_type]') ||
  !patientForm.includes('formatDateBR(exam.exam_date)') ||
  !patientForm.includes('to={`/exams/${exam.id}`}') ||
  !patientForm.includes('Abrir exame') ||
  !patientForm.includes('{!isCreateMode && hasPatientExams && (') ||
  patientForm.includes('Nenhum exame registrado para este paciente.') ||
  patientForm.includes('Área preparada para o módulo Exams.')
) {
  throw new Error('O paciente existente deve exibir seu histórico real de exames.')
}

if (
  !form.includes(
    "['pending', 'failed', 'canceled'].includes(",
  ) ||
  !form.includes(
    'const isPendingView =',
  )
) {
  throw new Error(
    'Pendentes, exames com falha e cancelados devem usar a visualização simplificada.',
  )
}

const pendingLayoutStart =
  form.indexOf('{isPendingView ? (')

const editLayoutStart =
  form.indexOf(') : isEditMode ? (')

const regularLayoutStart =
  form.indexOf(') : !isCreateMode ? (')

const createLayoutStart =
  form.indexOf(
    ') : (\n        <CRow className="g-4">',
    regularLayoutStart,
  )

const pendingLayout =
  form.slice(
    pendingLayoutStart,
    editLayoutStart,
  )

const editLayout =
  form.slice(
    editLayoutStart,
    regularLayoutStart,
  )

const regularLayout =
  form.slice(
    regularLayoutStart,
    createLayoutStart,
  )

const dataCardIndex =
  regularLayout.indexOf(
    '{examDataViewCard}',
  )

const aiResultIndex =
  regularLayout.indexOf(
    '<ExamAiResultCard',
  )

const historyIndex =
  regularLayout.indexOf(
    '<ExamHistoryCard',
  )

if (
  pendingLayoutStart < 0 ||
  editLayoutStart <= pendingLayoutStart ||
  regularLayoutStart <= editLayoutStart ||
  createLayoutStart <= regularLayoutStart ||
  !pendingLayout.includes('{pendingExamCard}') ||
  pendingLayout.includes('<ExamAiResultCard') ||
  !editLayout.includes('{examDataCard}') ||
  editLayout.includes('<ExamAiResultCard') ||
  dataCardIndex < 0 ||
  aiResultIndex <= dataCardIndex ||
  historyIndex <= aiResultIndex ||
  !regularLayout.includes(
    'reviewPanel={reviewPanel}',
  )
) {
  throw new Error(
    'Pendentes, exames com falha e cancelados devem usar o card simplificado; a edição e a revisão permanecem separadas.',
  )
}

if (
  !form.includes('const examDataViewContent = (') ||
  !form.includes('const pendingExamCard = (') ||
  form.includes('isExamDataOpen') ||
  !form.includes('<ExamHistoryCard') ||
  !form.includes('defaultOpen={false}') ||
  !history.includes('collapsible = false') ||
  !history.includes('defaultOpen = true') ||
  !history.includes('const isContentOpen = !collapsible || isOpen') ||
  !history.includes('aria-expanded={isOpen}') ||
  !history.includes('{isContentOpen && (')
) {
  throw new Error(
    'As telas devem manter os dados visíveis e somente o histórico recolhível.',
  )
}

if (
  !form.includes('const examListFilterStatuses = new Set([') ||
  !form.includes("'processing',") ||
  !form.includes('? `/exams?status=${form.status_name}`') ||
  !form.includes('to={examListPath}')
) {
  throw new Error('O botão Voltar deve retornar à listagem filtrada pelo status atual do exame.')
}

if (
  !form.includes('form.title || title') ||
  !form.includes('Consulte os dados do exame e acompanhe seu fluxo de análise e revisão.') ||
  !form.includes("import ExamSummaryHeader from 'src/views/exams/ExamSummaryHeader'") ||
  !form.includes('<ExamSummaryHeader') ||
  !form.includes('patientCpf={selectedPatientCpf}') ||
  !form.includes('patientBirthDate={') ||
  !form.includes('statusColors[') ||
  !form.includes('form.status_name') ||
  !form.includes('examStatusDisplayLabels[') ||
  !summaryHeader.includes('patientCpf') ||
  !summaryHeader.includes('resolvedPatientCpf') ||
  !summaryHeader.includes('{resolvedPatientCpf}') ||
  !summaryHeader.includes('calculateAge') ||
  !summaryHeader.includes('examTypeLabels') ||
  !summaryHeader.includes('formatDateBR') ||
  summaryHeader.includes('statusColors') ||
  summaryHeader.includes('<CBadge')
) {
  throw new Error(
    'O título da página deve exibir o status; o card deve resumir paciente, CPF, idade, tipo e data.',
  )
}

if (
  !/export const statusColors = \{[\s\S]*?pending: 'info'/.test(
    constants,
  )
) {
  throw new Error(
    'O status pendente deve usar a cor info.',
  )
}

if (
  !form.includes("import ExamAiResultCard from 'src/views/exams/ExamAiResultCard'") ||
  !form.includes('<ExamAiResultCard') ||
  !aiResultCard.includes('Análise Automatizada e Revisão Médica') ||
  !aiResultCard.includes('Uso do resultado:') ||
  !aiResultCard.includes('Sobre o mapa:') ||
  !aiResultCard.includes('Ensemble Stacking') ||
  !aiResultCard.includes('ENSEMBLE_ATTRIBUTION_METHOD') ||
  !aiResultCard.includes('weighted_base_gradcam_oriented_by_ensemble_stacking_v1') ||
  !aiResultCard.includes("'Mapa de atribuição composto'") ||
  !aiResultCard.includes("'Mapa Grad-CAM (ResNet-50)'") ||
  !aiResultCard.includes('ResNet-50') ||
  !aiResultCard.includes('EfficientNet-B4') ||
  !aiResultCard.includes('PVTv2-B2') ||
  !aiResultCard.includes('metaclassificador') ||
  !aiResultCard.includes('Pesos locais da') ||
  !aiResultCard.includes('attribution_branch_weights') ||
  !aiResultCard.includes('formatAttributionWeight') ||
  !aiResultCard.includes('risco') ||
  !aiResultCard.includes('gravidade') ||
  !aiResultCard.includes('causalidade') ||
  !aiResultCard.includes('Status da análise') ||
  !aiResultCard.includes('Predição') ||
  !aiResultCard.includes('Confiança') ||
  !aiResultCard.includes('Modelo utilizado') ||
  !aiResultCard.includes('Versão') ||
  !aiResultCard.includes('Tempo de processamento') ||
  !aiResultCard.includes("'ClinicAI ES Gastrointestinal'") ||
  !aiResultCard.includes('model_version') ||
  !aiResultCard.includes('Imagem original') ||
  !aiResultCard.includes('cilCloudDownload') ||
  !aiResultCard.includes('cilPrint') ||
  !aiResultCard.includes('onPackageDownload') ||
  !aiResultCard.includes('title="Baixar imagem original e mapa de atribuição"') ||
  !aiResultCard.includes('title="Impressão do exame ainda não disponível"') ||
  aiResultCard.includes('Baixar imagem e mapa') ||
  !aiResultCard.includes('Intensidade de atribuição') ||
  !aiResultCard.includes('Menor intensidade') ||
  !aiResultCard.includes('Maior intensidade') ||
  !aiResultCard.includes('linear-gradient(90deg') ||
  !aiResultCard.includes('ai_notes?.trim()') ||
  !aiResultCard.includes("height: '360px'") ||
  aiResultCard.includes('onOriginalDownload') ||
  aiResultCard.includes('onGradcamDownload') ||
  />\s*Baixar imagem original\s*</.test(aiResultCard) ||
  aiResultCard.includes('Baixar ${mapName}') ||
  aiResultCard.includes('target="_blank"') ||
  aiResultCard.includes('console.log(')
) {
  throw new Error(
    'O resultado automatizado deve exibir download conjunto, imagens antes dos dados e terminologia adequada do mapa.',
  )
}

const contributionScaleIndex =
  aiResultCard.indexOf(
    'const contributionScaleStyle',
  )

const originalImageSectionIndex =
  aiResultCard.indexOf(
    'id="original-image-title"',
  )

const attributionImageSectionIndex =
  aiResultCard.indexOf(
    'id="attribution-image-title"',
  )

const analysisDataSectionIndex =
  aiResultCard.indexOf(
    'id="analysis-data-title"',
  )

if (
  contributionScaleIndex < 0 ||
  originalImageSectionIndex <=
    contributionScaleIndex ||
  attributionImageSectionIndex <=
    contributionScaleIndex ||
  analysisDataSectionIndex <=
    attributionImageSectionIndex ||
  !aiResultCard.includes(
    'className="g-4 align-items-stretch"',
  ) ||
  (
    aiResultCard.match(
      /className="h-100 d-flex flex-column"/g,
    ) || []
  ).length !== 2 ||
  aiResultCard.includes(
    'className="d-grid mt-auto"',
  )
) {
  throw new Error(
    'A escala e o download devem anteceder as imagens; os dados devem aparecer abaixo.',
  )
}

if (
  !form.includes("'Dados Cadastrais do Exame'") ||
  !form.includes("'Editar Dados do Exame'") ||
  !form.includes('Observações') ||
  !form.includes('Achados da revisão médica *') ||
  !form.includes('Conclusão médica *')
) {
  throw new Error(
    'Os dados do cadastro e da revisão médica devem permanecer semanticamente separados.',
  )
}

if (
  form.includes('<strong>Arquivo</strong>') ||
  form.includes('<div className="text-body-secondary small">Resumo</div>') ||
  form.includes("<div>{aiAnalysis.ai_notes || '-'}</div>")
) {
  throw new Error('A tela ainda contém a organização lateral ou textos artificiais antigos.')
}

if (
  !form.includes("import { cilWarning } from '@coreui/icons'") ||
  !form.includes('icon={cilWarning}') ||
  !form.includes(
    "'rgba(var(--cui-warning-rgb), 0.12)'",
  ) ||
  !form.includes(
    "'rgba(var(--cui-warning-rgb), 0.35)'",
  )
) {
  throw new Error(
    'O alerta da revisão deve usar tonalidade amarela clara e ícone de atenção.',
  )
}

if (
  !form.includes(
    "? 'border-dark'",
  ) ||
  !form.includes(
    "'rgba(var(--cui-dark-rgb), 0.08)'",
  ) ||
  !form.includes(
    "? 'dark'",
  )
) {
  throw new Error(
    'A revisão concluída com divergência deve usar borda, fundo e badge escuros.',
  )
}

if (form.includes('console.log(')) {
  throw new Error('ExamForm ainda contém logs de depuração.')
}

console.log(
  'Contrato de exames coerente: 7 estados, transições, repetição e concorrência validados.',
)
