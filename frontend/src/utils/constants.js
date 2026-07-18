/**
 * Utilitários de nomeclaturas das etiquetas do sistema.
 */

// MODULES

export const moduleLabels = {
  users: 'Usuários',
  clinics: 'Clínicas',
  patients: 'Pacientes',
  exams: 'Exames',
  ai_analysis: 'Análises IA',
  audit_logs: 'Logs de Auditoria',
  roles: 'Perfis',
  permissions: 'Permissões',
  role_permissions: 'Permissões por Perfil',
  statuses: 'Status',
}

// STATUS

export const statusColors = {
  pending: 'secondary',
  processing: 'info',
  awaiting_review: 'warning',
  completed: 'success',
  completed_with_divergence: 'dark',
  canceled: 'secondary',
  failed: 'danger',
}

// Rótulos em português dos status de exame — plural, porque são usados
// como título de card/lista ("Concluídos", "Cancelados"). Compartilhado
// entre ExamsList.jsx e Dashboard.jsx para não duplicar a mesma lista.
export const examStatusLabels = {
  pending: 'Pendentes',
  processing: 'Processando',
  awaiting_review: 'Aguardando Revisão',
  completed: 'Concluídos',
  completed_with_divergence: 'Com Divergência',
  failed: 'Falha na IA',
  canceled: 'Cancelados',
}

export const examStatusDisplayLabels = {
  pending: 'Pendente',
  processing: 'Processando',
  awaiting_review: 'Aguardando revisão',
  completed: 'Concluído',
  completed_with_divergence: 'Concluído com divergência',
  failed: 'Falha na IA',
  canceled: 'Cancelado',
}

// EXAMS

export const examTypeLabels = {
  colonoscopy: 'Colonoscopia',
  endoscopy: 'Endoscopia digestiva alta',
}

export const examTypeOptions = [
  {
    value: 'endoscopy',
    label: 'Endoscopia digestiva alta',
  },
  {
    value: 'colonoscopy',
    label: 'Colonoscopia',
  },
]

// AI ANALYSIS

export const aiStatusLabels = {
  pending: 'Pendente',
  processing: 'Processando',
  completed: 'Concluída',
  failed: 'Falhou',
  canceled: 'Cancelada',
  not_processed: 'Não processada',
}

export const predictionLabels = {
  normal: 'Normal',
  abnormal: 'Anormal',
}

export const aiStatusColors = {
  pending: 'secondary',
  processing: 'info',
  completed: 'success',
  failed: 'danger',
  canceled: 'secondary',
  not_processed: 'secondary',
}
