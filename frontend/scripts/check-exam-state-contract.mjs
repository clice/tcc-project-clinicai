import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const repositoryRoot = path.resolve(scriptDir, '..', '..')
const read = (relativePath) =>
  fs.readFileSync(path.join(repositoryRoot, relativePath), 'utf8')

const constants = read('frontend/src/utils/constants.js')
const form = read('frontend/src/views/exams/ExamForm.jsx')
const list = read('frontend/src/views/exams/ExamsList.jsx')
const service = read('frontend/src/services/examService.js')
const stateMachine = read('backend/app/modules/exams/state_machine.py')
const examService = read('backend/app/modules/exams/service.py')

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

if (!service.includes("api.post(`/exams/${id}/analyze`)")) {
  throw new Error('O frontend não expõe o disparo protegido da análise de IA.')
}
if (!form.includes("form.status_name === 'processing'") || !form.includes('analysis_in_progress')) {
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
if (!examService.includes('claim_exam_for_analysis') || !examService.includes('get_exam_model_for_update')) {
  throw new Error('O backend não contém proteção explícita de concorrência.')
}
if (form.includes('console.log(')) {
  throw new Error('ExamForm ainda contém logs de depuração.')
}

console.log('Contrato de exames coerente: 7 estados, transições, repetição e concorrência validados.')
