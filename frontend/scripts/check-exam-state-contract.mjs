import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const repositoryRoot = path.resolve(scriptDir, '..', '..')
const read = (relativePath) => fs.readFileSync(path.join(repositoryRoot, relativePath), 'utf8')

const constants = read('frontend/src/utils/constants.js')
const form = read('frontend/src/views/exams/ExamForm.jsx')
const list = read('frontend/src/views/exams/ExamsList.jsx')
const history = read('frontend/src/views/exams/ExamHistoryCard.jsx')
const navigation = read('frontend/src/_nav.jsx')
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
  throw new Error(
    'O polling deve limitar erros consecutivos e limpar o timer ao desmontar a tela.',
  )
}
if (!form.includes('navigate(`/exams/${createdExam.id}`)')) {
  throw new Error('O cadastro não redireciona para o exame recém-criado.')
}
if (
  !list.includes(
    "const summaryCardStatuses = ['pending', 'processing', 'awaiting_review', 'completed']",
  )
) {
  throw new Error('Os cards da listagem não representam o fluxo iniciado em pending.')
}
if (
  !navigation.includes("name: 'Pendentes'") ||
  !navigation.includes("to: '/exams?status=pending'") ||
  !navigation.includes("badgeKey: 'pending'")
) {
  throw new Error('A barra lateral não oferece o filtro e a contagem de exames pendentes.')
}
if (
  !history.includes("import React, { useEffect, useRef, useState } from 'react'") ||
  !history.includes('const hasLoadedOnce = useRef(false)') ||
  !history.includes('if (isInitialLoad) setIsLoading(true)')
) {
  throw new Error('O histórico não preserva a exibição durante atualizações silenciosas.')
}
if (form.includes('console.log(')) {
  throw new Error('ExamForm ainda contém logs de depuração.')
}

console.log(
  'Contrato de exames coerente: 7 estados, transições, repetição e concorrência validados.',
)
