/**
 * Utilitários de nomeclaturas das etiquetas do sistema.
 */

// ACTIONS

export const actionLabels = {
  create: 'Criar',
  read: 'Visualizar',
  update: 'Atualizar',
  delete: 'Excluir',
  change_status: 'Alterar status',
  upload: 'Upload',
  download: 'Download',
  manage: 'Gerenciar',
}

export const actionOptions = [
  { value: 'create', label: actionLabels.create },
  { value: 'read', label: actionLabels.read },
  { value: 'update', label: actionLabels.update },
  { value: 'delete', label: actionLabels.delete },
  { value: 'change_status', label: actionLabels.change_status },
  { value: 'upload', label: actionLabels.upload },
  { value: 'download', label: actionLabels.download },
  { value: 'manage', label: actionLabels.manage },
]

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

export const moduleOptions = [
  { value: 'users', label: moduleLabels.users },
  { value: 'clinics', label: moduleLabels.clinics },
  { value: 'patients', label: moduleLabels.patients },
  { value: 'exams', label: moduleLabels.exams },
  { value: 'ai_analysis', label: moduleLabels.ai_analysis },
  { value: 'audit_logs', label: moduleLabels.audit_logs },
  { value: 'roles', label: moduleLabels.roles },
  { value: 'permissions', label: moduleLabels.permissions },
  { value: 'role_permissions', label: moduleLabels.role_permissions },
  { value: 'statuses', label: moduleLabels.statuses },
]

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

export const statusNameOptions = [
  { value: 'active', label: 'Ativo' },
  { value: 'inactive', label: 'Inativo' },
  { value: 'pending', label: 'Pendente' },
  { value: 'canceled', label: 'Cancelado' },
  { value: 'completed', label: 'Concluído' },
  { value: 'completed_with_divergence', label: 'Concluído com Divergência' },
  { value: 'processing', label: 'Processando' },
  { value: 'awaiting_review', label: 'Aguardando Revisão Médica' },
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