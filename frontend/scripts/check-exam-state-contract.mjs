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
const navigation = read('frontend/src/_nav.jsx')
const service = read('frontend/src/services/examService.js')
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
  !editableStatusesMatch[1].includes('StatusName.FAILED.value') ||
  editableStatusesMatch[1].includes('StatusName.PROCESSING.value')
) {
  throw new Error('Somente exames pending/failed podem ter metadados editados.')
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
if (!list.includes('canEdit={canEdit && (isPending || isFailed)}')) {
  throw new Error('A listagem deve permitir edição somente em pending/failed.')
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
  !form.includes('if (!isAdminMaster) return') ||
  !form.includes('{isCreateMode && isAdminMaster ? (') ||
  !form.includes('doctor_id: isDoctor') ||
  !form.includes('Clínica vinculada ao usuário autenticado.') ||
  !form.includes('Médico autenticado responsável pelo exame.')
) {
  throw new Error(
    'O cadastro do exame deve fixar clínica e médico e filtrar os pacientes do médico autenticado.',
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
  !aiResultCard.includes('Baixar imagem original') ||
  form.includes('target="_blank"') ||
  form.includes('href={originalImageUrl}') ||
  aiResultCard.includes('target="_blank"') ||
  aiResultCard.includes('href={originalImageUrl}') ||
  aiResultCard.includes('href={gradcamUrl}') ||
  form.includes("<CFormInput value={form.file_name || 'Nenhum arquivo vinculado'} disabled />") ||
  form.includes("<div>{form.file_name || '-'}</div>") ||
  form.includes("<div>{form.file_mime_type || '-'}</div>")
) {
  throw new Error(
    'O detalhe deve exibir e baixar imagens sem abrir outra aba nem expor nome físico ou MIME.',
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
  !examService.includes('description="Download do mapa de atribuição da IA autorizado."') ||
  !examService.includes('"artifact_type": "ai_attribution_map"') ||
  !examService.includes('"delivery_mode": "attachment"')
) {
  throw new Error('A prévia do Grad-CAM deve ser separada do download manual auditado.')
}

if ((service.match(/download_request: Date\.now\(\)/g) || []).length !== 2) {
  throw new Error(
    'Os downloads explícitos devem impedir respostas reutilizadas do cache do navegador.',
  )
}

if (
  !form.includes('buildAttributionMapDownloadName') ||
  !form.includes('`mapa-atribuicao-exame-${examId}-`') ||
  !form.includes('mapa de atribuição da IA')
) {
  throw new Error('A revisão e o download devem usar a nomenclatura pública do mapa de atribuição.')
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

const pendingLayoutStart = form.indexOf('{isPendingView ? (')
const regularLayoutStart = form.indexOf(': !isCreateMode ? (')
const pendingLayout = form.slice(pendingLayoutStart, regularLayoutStart)
const regularLayout = form.slice(regularLayoutStart)

const reviewIndex = regularLayout.indexOf('id="revisao-medica"')
const aiResultIndex = regularLayout.indexOf('<ExamAiResultCard')
const dataCardIndex = regularLayout.indexOf('{isReadOnly ? examDataViewCard : examDataCard}')
const historyIndex = regularLayout.indexOf('<ExamHistoryCard')

if (
  pendingLayoutStart < 0 ||
  regularLayoutStart <= pendingLayoutStart ||
  !pendingLayout.includes('{pendingExamCard}') ||
  pendingLayout.includes('<ExamAiResultCard') ||
  reviewIndex < 0 ||
  aiResultIndex <= reviewIndex ||
  dataCardIndex <= aiResultIndex ||
  historyIndex <= dataCardIndex
) {
  throw new Error(
    'O pendente deve priorizar o card único; os demais detalhes mantêm revisão, IA, dados e histórico.',
  )
}

if (
  !form.includes("form.status_name === 'pending'") ||
  !form.includes('const pendingExamCard = (') ||
  !form.includes('<CCol lg={8}>') ||
  !form.includes('<CCol lg={4}>') ||
  !form.includes('Paciente') ||
  !form.includes('Data do exame') ||
  !form.includes('Tipo de exame') ||
  !form.includes('Status') ||
  !form.includes('Clínica') ||
  !form.includes('Médico responsável') ||
  !form.includes('Indicação clínica') ||
  !form.includes('Observações') ||
  !form.includes('className="g-4 align-items-start"') ||
  !form.includes("height: 'auto'") ||
  form.includes('const pendingImageLoadingStyle') ||
  form.includes("height: '360px'") ||
  form.includes('className="g-4 align-items-stretch"') ||
  form.includes('<CCol lg={4} className="d-flex">') ||
  form.includes('className="d-flex flex-column w-100"') ||
  form.includes('className="w-100 rounded border bg-body-tertiary"') ||
  form.includes('className="d-grid mt-auto"') ||
  form.includes('isExamDataOpen') ||
  !form.includes('collapsible={isReadOnly}') ||
  !form.includes('defaultOpen={!isReadOnly}') ||
  !history.includes('collapsible = false') ||
  !history.includes('defaultOpen = true') ||
  !history.includes('const isContentOpen = !collapsible || isOpen') ||
  !history.includes('aria-expanded={isOpen}') ||
  !history.includes('{isContentOpen && (') ||
  !history.includes('className="mt-4 mb-4"')
) {
  throw new Error(
    'Os dados devem usar visualização compacta e somente o histórico permanece recolhível.',
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
  !form.includes('{isCreateMode ? title : form.title || title}') ||
  !form.includes('Consulte os dados do exame e acompanhe seu fluxo de análise e revisão.') ||
  !form.includes('{selectedPatientName}') ||
  !form.includes('{formatDateBR(form.exam_date)}') ||
  !form.includes('examTypeLabels[form.exam_type]') ||
  !form.includes('statusColors[form.status_name]')
) {
  throw new Error(
    'O cabeçalho deve preservar o título e o corpo deve apresentar paciente, data, tipo e status.',
  )
}

if (
  !form.includes("import ExamAiResultCard from 'src/views/exams/ExamAiResultCard'") ||
  !form.includes('<ExamAiResultCard') ||
  !aiResultCard.includes('<strong>Resultado da IA</strong>') ||
  !aiResultCard.includes('color="info"') ||
  !aiResultCard.includes('Uso do resultado:') ||
  !aiResultCard.includes('Sobre o mapa atual:') ||
  !aiResultCard.includes('Ensemble Stacking') ||
  !aiResultCard.includes('ENSEMBLE_ATTRIBUTION_METHOD') ||
  !aiResultCard.includes('weighted_base_gradcam_oriented_by_ensemble_stacking_v1') ||
  !aiResultCard.includes('Mapa de atribuição composto') ||
  !aiResultCard.includes('Mapa Grad-CAM (ResNet-50)') ||
  !aiResultCard.includes('Grad-CAMs da ResNet-50, EfficientNet-B4 e') ||
  !/PVTv2-B2\s+para\s+a\s+classe\s+final\s+prevista/.test(aiResultCard) ||
  !aiResultCard.includes('ponderados pelas evidências locais do') ||
  !aiResultCard.includes('metaclassificador') ||
  !aiResultCard.includes('mapa legado gerado') ||
  !aiResultCard.includes('decisão completa do Ensemble') ||
  !aiResultCard.includes('Pesos locais da composição:') ||
  !aiResultCard.includes('attribution_branch_weights') ||
  !aiResultCard.includes('formatAttributionWeight') ||
  !aiResultCard.includes('risco, gravidade') ||
  !aiResultCard.includes('causalidade') ||
  !aiResultCard.includes('Status da análise') ||
  !aiResultCard.includes('Predição') ||
  !aiResultCard.includes('Confiança') ||
  !aiResultCard.includes('Modelo utilizado') ||
  !aiResultCard.includes('Versão') ||
  !aiResultCard.includes('Tempo de processamento') ||
  !aiResultCard.includes("'ClinicAI ES Gastrointestinal'") ||
  !aiResultCard.includes('model_version') ||
  !aiResultCard.includes('<hr className="my-4" />') ||
  !aiResultCard.includes('Imagem original') ||
  !aiResultCard.includes('const mapTitle = isEnsembleAttribution') ||
  !aiResultCard.includes('const mapName = isEnsembleAttribution') ||
  !aiResultCard.includes('Baixar imagem original') ||
  !aiResultCard.includes('Baixar ${mapName}') ||
  !aiResultCard.includes('Intensidade de atribuição relativa') ||
  !aiResultCard.includes('Intensidade de contribuição relativa') ||
  !aiResultCard.includes('Menor intensidade') ||
  !aiResultCard.includes('Maior intensidade') ||
  !aiResultCard.includes('linear-gradient(90deg') ||
  !aiResultCard.includes('ai_notes?.trim()') ||
  !aiResultCard.includes("height: '360px'") ||
  aiResultCard.includes('Abrir imagem original em tamanho maior') ||
  aiResultCard.includes('Abrir mapa em tamanho maior') ||
  aiResultCard.includes('target="_blank"') ||
  aiResultCard.includes('Mapa produzido pela ResNet-50, componente') ||
  aiResultCard.includes('console.log(')
) {
  throw new Error(
    'O resultado da IA deve distinguir o mapa composto do mapa legado e preservar orientação, métricas, imagens, escala e ações.',
  )
}

const contributionScaleIndex = aiResultCard.indexOf('const contributionScaleStyle')

const originalImageSectionIndex = aiResultCard.indexOf('id="original-image-title"')

const gradcamImageSectionIndex = aiResultCard.indexOf('id="gradcam-image-title"')

if (
  contributionScaleIndex < 0 ||
  originalImageSectionIndex <= contributionScaleIndex ||
  gradcamImageSectionIndex <= contributionScaleIndex ||
  !aiResultCard.includes('className="g-4 align-items-stretch"') ||
  (aiResultCard.match(/className="h-100 d-flex flex-column"/g) || []).length !== 2 ||
  (aiResultCard.match(/className="d-grid mt-auto"/g) || []).length !== 2
) {
  throw new Error(
    'A escala deve anteceder as imagens e as duas colunas devem permanecer visualmente equilibradas.',
  )
}

if (
  !form.includes('Dados Clínicos e Administrativos') ||
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

if (form.includes('console.log(')) {
  throw new Error('ExamForm ainda contém logs de depuração.')
}

console.log(
  'Contrato de exames coerente: 7 estados, transições, repetição e concorrência validados.',
)
