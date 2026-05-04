/**
 * Utilitários de permissão e perfil do usuário autenticado.
 */

export const ROLES = {
  ADMIN_MASTER: 'admin_master',
  DOCTOR: 'doctor',
  CLINIC_STAFF: 'clinic_staff',
}

export const PERMISSIONS = {
  ////////// ADMIN

  // CLINICS
  CLINICS_CREATE: 'clinics:create',
  CLINICS_READ: 'clinics:read',
  CLINICS_UPDATE: 'clinics:update',
  CLINICS_DELETE: 'clinics:delete',
  CLINICS_CHANGE_STATUS: 'clinics:change_status',
  CLINICS_MANAGE: 'clinics:manage',

  // PATIENTS
  PATIENTS_CREATE: 'patients:create',
  PATIENTS_READ: 'patients:read',
  PATIENTS_UPDATE: 'patients:update',
  PATIENTS_DELETE: 'patients:delete',
  PATIENTS_CHANGE_STATUS: 'patients:change_status',
  PATIENTS_MANAGE: 'patients:manage',

  // EXAMS
  EXAMS_CREATE: 'exams:create',
  EXAMS_READ: 'exams:read',
  EXAMS_UPDATE: 'exams:update',
  EXAMS_DELETE: 'exams:delete',
  EXAMS_CHANGE_STATUS: 'exams:change_status',
  EXAMS_UPLOAD: 'exams:upload',
  EXAMS_DOWNLOAD: 'exams:download',
  EXAMS_MANAGE: 'exams:manage',

  // AI ANALYSIS
  AI_ANALYSIS_CREATE: 'ai_analysis:create',
  AI_ANALYSIS_READ: 'ai_analysis:read',
  AI_ANALYSIS_UPDATE: 'ai_analysis:update',
  AI_ANALYSIS_DELETE: 'ai_analysis:delete',
  AI_ANALYSIS_MANAGE: 'ai_analysis:manage',

  ////////// SYSTEM

  // USERS
  USERS_CREATE: 'users:create',
  USERS_READ: 'users:read',
  USERS_UPDATE: 'users:update',
  USERS_DELETE: 'users:delete',
  USERS_CHANGE_STATUS: 'users:change_status',
  USERS_MANAGE: 'users:manage',

  // AUDIT LOGS
  AUDIT_LOGS_READ: 'audit_logs:read',
  AUDIT_LOGS_MANAGE: 'audit_logs:manage',

  ////////// CONFIGURATIONS

  // ROLES
  ROLES_CREATE: 'roles:create',
  ROLES_READ: 'roles:read',
  ROLES_UPDATE: 'roles:update',
  ROLES_DELETE: 'roles:delete',
  ROLES_MANAGE: 'roles:manage',

  // PERMISSIONS
  PERMISSIONS_CREATE: 'permissions:create',
  PERMISSIONS_READ: 'permissions:read',
  PERMISSIONS_UPDATE: 'permissions:update',
  PERMISSIONS_DELETE: 'permissions:delete',
  PERMISSIONS_MANAGE: 'permissions:manage',

  // ROLE PERMISSIONS
  ROLE_PERMISSIONS_CREATE: 'role_permissions:create',
  ROLE_PERMISSIONS_READ: 'role_permissions:read',
  ROLE_PERMISSIONS_UPDATE: 'role_permissions:update',
  ROLE_PERMISSIONS_DELETE: 'role_permissions:delete',
  ROLE_PERMISSIONS_MANAGE: 'role_permissions:manage',

  // STATUSES
  STATUSES_READ: 'statuses:read',
  STATUSES_CREATE: 'statuses:create',
  STATUSES_UPDATE: 'statuses:update',
  STATUSES_DELETE: 'statuses:delete',
  STATUSES_CHANGE_STATUS: 'statuses:change_status',
  STATUSES_MANAGE: 'statuses:manage',
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
 * Verifica qualquer permissão do usuário
 */
export const hasAnyPermission = (user, permissionNames = []) => {
  const roleName = getUserRole(user)

  if (isAdminMaster(roleName)) {
    return true
  }

  return permissionNames.some((permissionName) => hasPermission(user, permissionName))
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

// CLINICS
export const canManageClinics = (user) => {
  hasAnyPermission(user, [
    PERMISSIONS.CLINICS_READ,
    PERMISSIONS.CLINICS_CREATE,
    PERMISSIONS.CLINICS_UPDATE,
    PERMISSIONS.CLINICS_CHANGE_STATUS,
    PERMISSIONS.CLINICS_MANAGE,
  ])
}

// PATIENTS
export const canManagePatients = (user) => {
  hasAnyPermission(user, [
    PERMISSIONS.PATIENTS_READ,
    PERMISSIONS.PATIENTS_CREATE,
    PERMISSIONS.PATIENTS_UPDATE,
    PERMISSIONS.PATIENTS_CHANGE_STATUS,
    PERMISSIONS.PATIENTS_MANAGE,
  ])
}

// EXAMS
export const canManageExams = (user) => {
  hasAnyPermission(user, [
    PERMISSIONS.EXAMS_READ,
    PERMISSIONS.EXAMS_CREATE,
    PERMISSIONS.EXAMS_UPDATE,
    PERMISSIONS.EXAMS_DELETE,
    PERMISSIONS.EXAMS_CHANGE_STATUS,
    PERMISSIONS.EXAMS_UPLOAD,
    PERMISSIONS.EXAMS_DOWNLOAD,
    PERMISSIONS.EXAMS_MANAGE,
  ])
}

// AI ANALYSIS
export const canManageAiAnalysis = (user) => {
  hasAnyPermission(user, [
    PERMISSIONS.AI_ANALYSIS_READ,
    PERMISSIONS.AI_ANALYSIS_CREATE,
    PERMISSIONS.AI_ANALYSIS_UPDATE,
    PERMISSIONS.AI_ANALYSIS_MANAGE,
  ])
}

////////// SYSTEM

// USERS
export const canManageUsers = (user) => {
  hasAnyPermission(user, [
    PERMISSIONS.USERS_READ,
    PERMISSIONS.USERS_CREATE,
    PERMISSIONS.USERS_UPDATE,
    PERMISSIONS.USERS_CHANGE_STATUS,
    PERMISSIONS.USERS_MANAGE,
  ])
}

// AUDIT LOGS
export const canManageAuditLogs = (user) => {
  hasAnyPermission(user, [
    PERMISSIONS.AUDIT_LOGS_READ, 
    PERMISSIONS.AUDIT_LOGS_MANAGE
  ])
}

export const canManageAugitLogs = canManageAuditLogs

////////// CONFIGURATIONS

// ROLES
export const canManageRoles = (user) => {
  hasAnyPermission(user, [
    PERMISSIONS.ROLES_READ,
    PERMISSIONS.ROLES_CREATE,
    PERMISSIONS.ROLES_UPDATE,
    PERMISSIONS.ROLES_DELETE,
    PERMISSIONS.ROLES_MANAGE,
  ])
}

// PERMISSIONS
export const canManagePermissions = (user) => {
  hasAnyPermission(user, [
    PERMISSIONS.PERMISSIONS_READ,
    PERMISSIONS.PERMISSIONS_CREATE,
    PERMISSIONS.PERMISSIONS_UPDATE,
    PERMISSIONS.PERMISSIONS_DELETE,
    PERMISSIONS.PERMISSIONS_MANAGE,
  ])
}

// STATUSES
export const canManageStatuses = (user) => {
  hasAnyPermission(user, [
    PERMISSIONS.STATUSES_READ,
    PERMISSIONS.STATUSES_CREATE,
    PERMISSIONS.STATUSES_UPDATE,
    PERMISSIONS.STATUSES_CHANGE_STATUS,
    PERMISSIONS.STATUSES_MANAGE,
  ])
}