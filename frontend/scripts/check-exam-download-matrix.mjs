import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(scriptDir, '..', '..')
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), 'utf8')

const list = read('frontend/src/views/exams/ExamsList.jsx')
const card = read('frontend/src/views/exams/ExamAiResultCard.jsx')
const form = read('frontend/src/views/exams/ExamForm.jsx')
const names = read('frontend/src/utils/examDownloadNames.js')
const service = read('frontend/src/services/examService.js')
const buttons = read('frontend/src/components/shared/AppActionButtons.jsx')
const backendState = read('backend/app/modules/exams/state_machine.py')
const backendRouter = read('backend/app/modules/exams/router.py')
const backendService = read('backend/app/modules/exams/service.py')

const requiredListFragments = [
  'const packageDownloadStatuses = new Set([',
  "'awaiting_review'",
  "'completed'",
  "'completed_with_divergence'",
  "const originalDownloadStatuses = new Set(['pending', 'failed', 'canceled'])",
  'exam.file_available',
  'exam.gradcam_available',
  'downloadImagePackage(exam.id)',
  'canEdit={canEditExam && isPending}',
  'canRestore={canChangeStatus && (isCanceled || isFailed)}',
  'canCancel={canChangeStatus && (isProcessing || isPending)}',
  'canUseClinicalExamActions',
  'roleName === ROLES.DOCTOR',
  'roleName === ROLES.ADMIN_MASTER',
  'if (!canUseClinicalExamActions)',
  'Baixar imagem original e Mapa Grad-CAM',
  'Baixar imagem original',
]

for (const fragment of requiredListFragments) {
  if (!list.includes(fragment)) {
    throw new Error(`Fragmento ausente na matriz da lista: ${fragment}`)
  }
}

if (list.includes('canEdit={canEdit && (isPending || isFailed)}')) {
  throw new Error('Falha da IA ainda está editável na listagem.')
}

if (
  !names.includes('mapa-grad-cam-exame-') ||
  !names.includes('imagens-exame-') ||
  !service.includes('`/exams/${id}/images/download`') ||
  !buttons.includes('downloadTitle')
) {
  throw new Error('Nomes, serviço ZIP ou tooltip não estão padronizados.')
}

if (
  !card.includes(
    "'Mapa de atribuição composto'",
  ) ||
  !card.includes(
    "'Mapa Grad-CAM (ResNet-50)'",
  ) ||
  !card.includes('onPackageDownload') ||
  !card.includes('cilCloudDownload') ||
  !card.includes('cilPrint') ||
  !card.includes(
    'title="Baixar imagem original e mapa de atribuição"',
  ) ||
  card.includes('Baixar imagem e mapa') ||
  card.includes('onOriginalDownload') ||
  card.includes('onGradcamDownload') ||
  !form.includes(
    'buildExamImagesPackageDownloadName',
  ) ||
  !form.includes(
    'downloadImagePackage',
  )
) {
  throw new Error(
    'O detalhe deve distinguir o mapa composto do legado e disponibilizar somente o pacote conjunto.',
  )
}

const editableSection = backendState
  .split('EDITABLE_EXAM_STATUSES', 2)[1]
  .split('def get_transition_target', 1)[0]

if (
  !editableSection.includes('StatusName.PENDING.value') ||
  editableSection.includes('StatusName.FAILED.value') ||
  backendState.includes('(StatusName.FAILED.value, ExamTransitionAction.REPLACE_FILE)')
) {
  throw new Error('O backend ainda permite edição ou substituição após falha.')
}

if (
  !backendRouter.includes('@router.get("/{exam_id}/images/download")') ||
  !backendService.includes('def download_exam_images_package(') ||
  !backendService.includes('mapa-grad-cam-exame-') ||
  !backendService.includes('imagens-exame-')
) {
  throw new Error('Contrato do pacote ZIP não está completo no backend.')
}

console.log('Matriz de ações, downloads e Mapa Grad-CAM validada.')
