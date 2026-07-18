/** Nomes públicos padronizados para os downloads de exames. */

export const normalizeExamDownloadPart = (value, fallback) => {
  const normalized = String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toLowerCase()
    .slice(0, 60)
    .replace(/-+$/g, '')

  return normalized || fallback
}

const resolveImageExtension = (mimeType) => (mimeType === 'image/png' ? 'png' : 'jpg')

const buildBaseName = ({ examId, patientName, examDate }) => {
  const patientPart = normalizeExamDownloadPart(patientName, 'paciente')
  const datePart = examDate || 'sem-data'

  return `${examId}-${patientPart}-${datePart}`
}

export const buildOriginalDownloadName = ({ examId, patientName, examDate, mimeType }) =>
  `exame-${buildBaseName({
    examId,
    patientName,
    examDate,
  })}.${resolveImageExtension(mimeType)}`

export const buildGradcamDownloadName = ({ examId, patientName, examDate, mimeType }) =>
  `mapa-grad-cam-exame-${buildBaseName({
    examId,
    patientName,
    examDate,
  })}.${resolveImageExtension(mimeType)}`

export const buildExamImagesPackageDownloadName = ({ examId, patientName, examDate }) =>
  `imagens-exame-${buildBaseName({
    examId,
    patientName,
    examDate,
  })}.zip`
