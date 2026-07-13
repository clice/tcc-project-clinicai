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

// ROLES

export const roleLabels = {
  admin_master: 'Administrador Master',
  clinic_staff: 'Atendente da Clínica',
  doctor: 'Médico',
}

export const roleOptions = [
  { value: 'admin_master', label: roleLabels.admin_master },
  { value: 'doctor', label: roleLabels.doctor },
  { value: 'clinic_staff', label: roleLabels.clinic_staff },
]

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

export const statusNameOptions = [
  { value: 'active', label: 'Ativo' },
  { value: 'inactive', label: 'Inativo' },
  { value: 'pending', label: 'Pendente' },
  { value: 'canceled', label: 'Cancelado' },
  { value: 'completed', label: 'Concluído' },
  { value: 'completed_with_divergence', label: 'Com Divergência' },
  { value: 'processing', label: 'Processando' },
  { value: 'awaiting_review', label: 'Aguardando Revisão' },
  { value: 'failed', label: 'Falhou' },
]

export const statusScopeOptions = [
  { value: 'user', label: 'Usuário' },
  { value: 'clinic', label: 'Clínica' },
  { value: 'patient', label: 'Paciente' },
  { value: 'exam', label: 'Exame' },
  { value: 'ai_analysis', label: 'Análise de IA' },
]

// EXAMS

export const examTypeLabels = {
  colonoscopy: 'Colonoscopia',
  endoscopy: 'Endoscopia',
}

export const examTypeOptions = [
  { value: 'endoscopy', label: 'Endoscopia' },
  { value: 'colonoscopy', label: 'Colonoscopia' },
]

// AI ANALYSIS

export const aiStatusLabels = {
  pending: 'Pendente',
  processing: 'Processando',
  completed: 'Concluída',
  failed: 'Falhou',
  canceled: 'Cancelada',
  not_processed: 'Não processado',
}

export const aiStatusColors = {
  pending: 'secondary',
  processing: 'info',
  completed: 'success',
  failed: 'danger',
  canceled: 'secondary',
  not_processed: 'secondary',
}
