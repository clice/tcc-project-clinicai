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
  CLINICS_CHANGE_STATUS: 'clinics:change_status',

  // PATIENTS
  PATIENTS_CREATE: 'patients:create',
  PATIENTS_READ: 'patients:read',
  PATIENTS_UPDATE: 'patients:update',
  PATIENTS_CHANGE_STATUS: 'patients:change_status',

  // EXAMS
  EXAMS_CREATE: 'exams:create',
  EXAMS_READ: 'exams:read',
  EXAMS_UPDATE: 'exams:update',
  EXAMS_DELETE: 'exams:delete',
  EXAMS_UPLOAD_FILE: 'exams:upload_file',
  EXAMS_DOWNLOAD_FILE: 'exams:downloas_file',

  // AI ANALYSIS
  AI_ANALYSIS_CREATE: 'ai_analysis:create',
  AI_ANALYSIS_READ: 'ai_analysis:read',
  AI_ANALYSIS_UPDATE: 'ai_analysis:update',
  AI_ANALYSIS_REVIEW: 'ai_analysis:review',

  ////////// SYSTEM

  // USERS
  USERS_CREATE: 'users:create',
  USERS_READ: 'users:read',
  USERS_UPDATE: 'users:update',
  USERS_CHANGE_STATUS: 'users:change_status',

  // AUDIT LOGS
  AUDIT_LOGS_READ: 'audit_logs:read',

  ////////// CONFIGURATIONS

  // ROLES
  ROLES_CREATE: 'roles:create',
  ROLES_READ: 'roles:read',
  ROLES_UPDATE: 'roles:update',
  ROLES_DELETE: 'roles:delete',

  // PERMISSIONS
  PERMISSIONS_CREATE: 'permissions:create',
  PERMISSIONS_READ: 'permissions:read',
  PERMISSIONS_UPDATE: 'permissions:update',

  // STATUSES
  STATUSES_READ: 'statuses:read',
  STATUSES_CREATE: 'statuses:create',
  STATUSES_UPDATE: 'statuses:update',
  STATUSES_CHANGE_STATUS: 'statuses:change_status',
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
 * user.role_name
 * user.role
 * user.role.name
 */
export const getUserRole = (user) => {
  return user?.role_name || user?.role?.name || user?.role || null
}

export const getUserPermissions = (user) => {
  return user?.permissions || user?.role_permissions || []
}

/**
 * Verifica se o usuário tem permissão
 */
export const hasPermission = (user, permissionName) => {
  const roleName = getUserRole(user)

  if (isAdminMaster(roleName)) {
    return true
  }

  const permissions = getUserPermissions(user)

  return permissions.includes(permissionName)
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
  return hasAnyPermission(user, [
    PERMISSIONS.CLINICS_READ,
    PERMISSIONS.CLINICS_CREATE,
    PERMISSIONS.CLINICS_UPDATE,
    PERMISSIONS.CLINICS_CHANGE_STATUS,
  ])
}

// PATIENTS
export const canManagePatients = (user) => {
  return hasAnyPermission(user, [
    PERMISSIONS.PATIENTS_READ,
    PERMISSIONS.PATIENTS_CREATE,
    PERMISSIONS.PATIENTS_UPDATE,
    PERMISSIONS.PATIENTS_CHANGE_STATUS,
  ])
}

// EXAMS
export const canManageExams = (user) => {
  return hasAnyPermission(user, [
    PERMISSIONS.EXAMS_CREATE,
    PERMISSIONS.EXAMS_READ,
    PERMISSIONS.EXAMS_UPDATE,
    PERMISSIONS.EXAMS_DELETE,
    PERMISSIONS.EXAMS_UPLOAD_FILE,
    PERMISSIONS.EXAMS_DOWNLOAD_FILE,
  ])
}

// AI ANALYSIS
export const canManageAiAnalysis = (user) => {
  return hasAnyPermission(user, [
    PERMISSIONS.AI_ANALYSIS_CREATE,
    PERMISSIONS.AI_ANALYSIS_READ,
    PERMISSIONS.AI_ANALYSIS_UPDATE,
    PERMISSIONS.AI_ANALYSIS_REVIEW,
  ])
}

////////// SYSTEM

// USERS
export const canManageUsers = (user) => {
  return hasAnyPermission(user, [
    PERMISSIONS.USERS_READ,
    PERMISSIONS.USERS_CREATE,
    PERMISSIONS.USERS_UPDATE,
    PERMISSIONS.USERS_CHANGE_STATUS,
  ])
}

// AUDIT LOGS
export const canManageAugitLogs = (user) => {
  return hasAnyPermission(user, [
    PERMISSIONS.AUDIT_LOGS_READ,
  ])
}

////////// CONFIGURATIONS

// ROLES
export const canManageRoles = (user) => {
  return hasAnyPermission(user, [
    PERMISSIONS.ROLES_READ,
    PERMISSIONS.ROLES_CREATE,
    PERMISSIONS.ROLES_UPDATE,
    PERMISSIONS.ROLES_CHANGE_STATUS,
  ])
}

// PERMISSIONS
export const canManagePermissions = (user) => {
  return hasAnyPermission(user, [
    PERMISSIONS.PERMISSIONS_READ,
    PERMISSIONS.PERMISSIONS_CREATE,
    PERMISSIONS.PERMISSIONS_UPDATE,
  ])
}

// STATUSES
export const canManageStatuses = (user) => {
  return hasAnyPermission(user, [
    PERMISSIONS.STATUSES_READ,
    PERMISSIONS.STATUSES_CREATE,
    PERMISSIONS.STATUSES_UPDATE,
    PERMISSIONS.STATUSES_CHANGE_STATUS,
  ])
}