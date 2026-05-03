"""
Constantes oficiais do sistema ClinicAI.

Centraliza nomes internos usados em regras de negócio,
permissões, roles, módulos e status.
"""

from enum import StrEnum


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
    BLOCKED = "blocked"
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


class PermissionAction(StrEnum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    CHANGE_STATUS = "change_status"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    MANAGE = "manage"
    