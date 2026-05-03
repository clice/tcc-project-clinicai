"""
Constantes oficiais do sistema ClinicAI.

Centraliza nomes internos usados em regras de negócio,
permissões, roles, módulos e status.
"""

from enum import StrEnum


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    CHANGE_STATUS = "change_status"
    DELETE = "delete"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    UPLOAD_FILE = "upload_file"
    RUN_AI_ANALYSIS = "run_ai_analysis"


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
    MANAGE = "manage"


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
    PROCESSING = "processing"
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
    