/**
 * Matriz de permissões por ação usada pelos componentes do frontend.
 *
 * A permissão responde somente se a ação pode ser oferecida. Regras de estado
 * do registro, como impedir a edição de um exame concluído, continuam sendo
 * aplicadas pelo componente em conjunto com estes resultados.
 */
export const ACTION_PERMISSIONS = Object.freeze({
  patients: Object.freeze({
    canView: 'patients:read',
    canCreate: 'patients:create',
    canEdit: 'patients:update',
    canChangeStatus: 'patients:change_status',
  }),
  clinics: Object.freeze({
    canView: 'clinics:read',
    canCreate: 'clinics:create',
    canEdit: 'clinics:update',
    canChangeStatus: 'clinics:change_status',
  }),
  users: Object.freeze({
    canView: 'users:read',
    canCreate: 'users:create',
    canEdit: 'users:update',
    canChangeStatus: 'users:change_status',
  }),
  exams: Object.freeze({
    canView: 'exams:read',
    canCreate: 'exams:create',
    canEdit: 'exams:update',
    canChangeStatus: 'exams:change_status',
    canUpload: 'exams:upload',
    canDownload: 'exams:download',
    canReview: 'exams:review',
    canAnalyze: 'ai_analysis:create',
  }),
})

export const getActionAccess = (resource, hasPermission) => {
  const permissionMap = ACTION_PERMISSIONS[resource]

  if (!permissionMap) {
    throw new Error(`Recurso sem matriz de ações: ${resource}`)
  }

  return Object.fromEntries(
    Object.entries(permissionMap).map(([action, permission]) => [
      action,
      Boolean(hasPermission(permission)),
    ]),
  )
}
