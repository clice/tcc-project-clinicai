/**
 * Funções utilitárias para transformar erros da API em mensagens seguras para o usuário.
 *
 * Importante:
 * - Mostra mensagens úteis vindas do backend quando elas são controladas pela API.
 * - Trata erros de validação do FastAPI/Pydantic.
 * - Evita exibir detalhes técnicos sensíveis como stack trace, SQL ou nomes internos de exceções.
 */

const fallbackByStatus = {
  400: 'Revise os dados enviados e tente novamente.',
  401: 'Sua sessão expirou. Faça login novamente.',
  403: 'Você não tem permissão para realizar esta ação.',
  404: 'Registro não encontrado.',
  409: 'Não foi possível concluir a ação porque há conflito com outro registro.',
  422: 'Alguns campos estão inválidos. Revise o formulário.',
  500: 'Erro interno no servidor. Tente novamente em instantes.',
}

const fieldLabels = {
  name: 'Nome técnico',
  display_name: 'Nome de exibição',
  applies_to: 'Aplicado em',
  clinic_id: 'Clínica',
  patient_id: 'Paciente',
  doctor_id: 'Médico',
  status_id: 'Status',
  exam_type: 'Tipo de exame',
  exam_date: 'Data do exame',
  title: 'Título',
  description: 'Descrição',
  clinical_indication: 'Indicação clínica',
  findings: 'Achados',
  conclusion: 'Conclusão',
}

const isUnsafeMessage = (message = '') => {
  const normalized = String(message).toLowerCase()

  return [
    'traceback',
    'sqlalchemy',
    'psycopg',
    'integrityerror',
    'programmingerror',
    'operationalerror',
    'database',
    'stack',
  ].some((term) => normalized.includes(term))
}

const getFieldLabel = (loc) => {
  if (!Array.isArray(loc)) return null

  const field = loc[loc.length - 1]
  return fieldLabels[field] || field
}

const formatValidationError = (item) => {
  const fieldName = Array.isArray(item?.loc) ? item.loc[item.loc.length - 1] : null

  if (fieldName === 'cnpj') {
    return 'Informe um CNPJ válido.'
  }

  const field = getFieldLabel(item?.loc)
  const message = String(item?.msg || 'Campo inválido.').replace(/^Value error,\s*/i, '')

  return field ? `${field}: ${message}` : message
}

export const getErrorMessage = (error, fallback = 'Ocorreu um erro inesperado.') => {
  const status = error?.response?.status
  const detail = error?.response?.data?.detail

  if (!error?.response) {
    return 'Não foi possível conectar ao servidor. Verifique se a API está em execução.'
  }

  if (Array.isArray(detail)) {
    return detail.map(formatValidationError).join(' ')
  }

  if (typeof detail === 'string' && detail.trim()) {
    return isUnsafeMessage(detail) ? fallbackByStatus[status] || fallback : detail
  }

  return fallbackByStatus[status] || fallback
}
