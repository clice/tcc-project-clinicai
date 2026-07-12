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
    