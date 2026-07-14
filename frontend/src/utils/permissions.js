/**
 * Utilitários de permissão e perfil do usuário autenticado.
 */

export const ROLES = {
  ADMIN_MASTER: 'admin_master',
  DOCTOR: 'doctor',
  CLINIC_STAFF: 'clinic_staff',
}

/**
 * Catálogo de permissões reais do sistema — cada string aqui corresponde
 * a uma permissão de fato seedada no backend (ver `permissions/seed.py`).
 * Em módulos delegáveis, a permissão é checada por `require_permission(...)`.
 * Nos módulos estruturais Clínicas, Usuários administrativos e Auditoria,
 * a role fixa `admin_master` é a barreira autoritativa da rota; as constantes
 * administrativas são consultadas por ação na interface, enquanto a role
 * continua sendo a barreira de entrada desses módulos.
 *
 * Decisão arquitetural (achados PM-03/AU-01 de revisão): configuração
 * estrutural do sistema — Perfis, Permissões, Vínculos Perfil↔Permissão
 * e Status — é EXCLUSIVA do Administrador Master e protegida no backend
 * por perfil (`require_admin`), não por permissão granular dinâmica.
 * Não existem, portanto, permissões tipo "roles:create" ou
 * "statuses:manage" — mantê-las aqui como se existissem sugeria um
 * controle mais fino do que o sistema realmente tem, e nenhuma delas era
 * checada por rota nenhuma. Se essa área precisar de RBAC dinâmico no
 * futuro, será necessário seedar essas permissões de verdade no backend
 * e trocar as rotas de `require_admin` para `require_permission`.
 *
 * Também removidas: todas as variantes ":delete" e ":manage" — nenhuma
 * rota real do sistema as exige (a exclusão de registros, quando existe,
 * usa change_status para inativar, não delete físico).
 */
export const PERMISSIONS = {
  // USERS
  USERS_CREATE: 'users:create',
  USERS_READ: 'users:read',
  USERS_UPDATE: 'users:update',
  USERS_CHANGE_STATUS: 'users:change_status',
  USERS_READ_PROFILE: 'users:read_profile',
  USERS_UPDATE_PROFILE: 'users:update_profile',

  // CLINICS
  CLINICS_CREATE: 'clinics:create',
  CLINICS_READ: 'clinics:read',
  CLINICS_UPDATE: 'clinics:update',
  CLINICS_CHANGE_STATUS: 'clinics:change_status',
  CLINICS_READ_PROFILE: 'clinics:read_profile',
  CLINICS_UPDATE_PROFILE: 'clinics:update_profile',

  // PATIENTS
  PATIENTS_CREATE: 'patients:create',
  PATIENTS_READ: 'patients:read',
  PATIENTS_UPDATE: 'patients:update',
  PATIENTS_CHANGE_STATUS: 'patients:change_status',

  // EXAMS
  EXAMS_CREATE: 'exams:create',
  EXAMS_READ: 'exams:read',
  EXAMS_UPDATE: 'exams:update',
  EXAMS_CHANGE_STATUS: 'exams:change_status',
  EXAMS_REVIEW: 'exams:review',
  EXAMS_UPLOAD: 'exams:upload',
  EXAMS_DOWNLOAD: 'exams:download',

  // AI ANALYSIS
  AI_ANALYSIS_CREATE: 'ai_analysis:create',
  AI_ANALYSIS_READ: 'ai_analysis:read',
  AI_ANALYSIS_UPDATE: 'ai_analysis:update',

  // AUDIT LOGS
  AUDIT_LOGS_READ: 'audit_logs:read',
}

/**
 * Retorna as possibilidades de perfis do usuário.
 */
export const isAdminMaster = (roleName) => roleName === ROLES.ADMIN_MASTER
export const isDoctor = (roleName) => roleName === ROLES.DOCTOR
export const isClinicStaff = (roleName) => roleName === ROLES.CLINIC_STAFF

/**
 * Normaliza a role do usuário.
 *
 * Funciona se o backend retornar:
 * - user.role_name
 * - user.role
 * - user.role.name
 */
export const getUserRole = (user) => user?.role_name || user?.role?.name || user?.role || null

/**
 * Normaliza permissões vindas do backend.
 *
 * Aceita tanto array de strings quanto array de objetos contendo name.
 */
export const getUserPermissions = (user) => {
  const permissions = user?.permissions || user?.role_permissions || []

  return permissions
    .map((permission) => {
      if (typeof permission === 'string') return permission
      return permission?.name || permission?.permission?.name || null
    })
    .filter(Boolean)
}

/**
 * Verifica se o usuário tem permissão
 */
export const hasPermission = (user, permissionName) => {
  const roleName = getUserRole(user)

  if (isAdminMaster(roleName)) {
    return true
  }

  return getUserPermissions(user).includes(permissionName)
}

/**
 * Retorna se o usuário tem permissão de acesso ou não.
 */
export const canAccessRole = (user, allowedRoles = []) => {
  const roleName = getUserRole(user)

  if (!allowedRoles.length) {
    return true
  }

  return allowedRoles.includes(roleName)
}

/**
 * Verifica permissões específicas de acesso aos recursos do sistema.
 */
////////// ADMIN

////////// CONFIGURATIONS

// ROLES
export const canManageRoles = (user) => {
  return isAdminMaster(getUserRole(user))
}

// PERMISSIONS
export const canManagePermissions = (user) => {
  return isAdminMaster(getUserRole(user))
}

// STATUSES
export const canManageStatuses = (user) => {
  return isAdminMaster(getUserRole(user))
}
