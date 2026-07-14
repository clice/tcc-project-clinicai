"""
Constantes oficiais do sistema ClinicAI.

Centraliza nomes internos usados em regras de negócio,
permissões, roles, módulos e status.
"""

from enum import StrEnum


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    UPDATE_PASSWORD = "update_password"
    CHANGE_STATUS_ACTIVATE = "change_status_activate"
    CHANGE_STATUS_INACTIVATE = "change_status_inactivate"
    DELETE = "delete"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    REFRESH_TOKEN = "refresh_token"
    LOGOUT = "logout"
    CANCEL_EXAM = "cancel_exam"
    RESTORE_EXAM = "restore_exam"
    REVIEW_EXAM = "review_exam"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    RUN_AI_ANALYSIS = "run_ai_analysis"
    AI_ANALYSIS_FAILED = "ai_analysis_failed"


class AuditEntity(StrEnum):
    USER = "user"
    CLINIC = "clinic"
    PATIENT = "patient"
    EXAM = "exam"
    AI_ANALYSIS = "ai_analysis"
    ROLE = "role"
    PERMISSION = "permission"
    ROLE_PERMISSION = "role_permission"
    STATUS = "status"
    AUTH = "auth"


class PermissionAction(StrEnum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    CHANGE_STATUS = "change_status"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    REVIEW = "review"
    READ_PROFILE = "read_profile"
    UPDATE_PROFILE = "update_profile"


class RoleName(StrEnum):
    ADMIN_MASTER = "admin_master"
    CLINIC_STAFF = "clinic_staff"
    DOCTOR = "doctor"


class StatusScope(StrEnum):
    USER = "user"
    CLINIC = "clinic"
    PATIENT = "patient"
    EXAM = "exam"
    AI_ANALYSIS = "ai_analysis"


class StatusName(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    CANCELED = "canceled"
    COMPLETED = "completed"
    COMPLETED_WITH_DIVERGENCE = "completed_with_divergence"
    PROCESSING = "processing"
    AWAITING_REVIEW = "awaiting_review"
    FAILED = "failed"


# Matriz oficial e fechada de pares (name, applies_to) válidos. Sem essa
# validação, o schema aceitava name e applies_to como enums independentes
# — permitindo combinações sem sentido como completed/user ou active/exam,
# que quebram a máquina de estados descrita na monografia (ex: um usuário
# com status "completed" nunca autenticaria, já que get_current_user só
# aceita active/user). Usada tanto na validação do schema (StatusBase)
# quanto pode ser reaproveitada pelo frontend para filtrar as opções após
# a escolha do escopo.
ALLOWED_STATUS_BY_SCOPE: dict[str, set[str]] = {
    StatusScope.USER.value: {StatusName.ACTIVE.value, StatusName.INACTIVE.value},
    StatusScope.CLINIC.value: {StatusName.ACTIVE.value, StatusName.INACTIVE.value},
    StatusScope.PATIENT.value: {StatusName.ACTIVE.value, StatusName.INACTIVE.value},
    StatusScope.EXAM.value: {
        StatusName.PENDING.value,
        StatusName.PROCESSING.value,
        StatusName.AWAITING_REVIEW.value,
        StatusName.COMPLETED.value,
        StatusName.COMPLETED_WITH_DIVERGENCE.value,
        StatusName.CANCELED.value,
        StatusName.FAILED.value,
    },
    StatusScope.AI_ANALYSIS.value: {
        StatusName.PENDING.value,
        StatusName.PROCESSING.value,
        StatusName.COMPLETED.value,
        StatusName.FAILED.value,
    },
}


class SystemModule(StrEnum):
    USERS = "users"
    CLINICS = "clinics"
    PATIENTS = "patients"
    EXAMS = "exams"
    AI_ANALYSIS = "ai_analysis"
    AUDIT_LOGS = "audit_logs"
    ROLES = "roles"
    PERMISSIONS = "permissions"
    ROLE_PERMISSIONS = "role_permissions"
    STATUSES = "statuses"
    