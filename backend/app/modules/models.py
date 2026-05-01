"""
Registro central dos models do sistema.

Este arquivo importa todos os models da aplicação para que o Alembic
consiga detectar as tabelas durante o autogenerate das migrations.
"""

from app.modules.statuses.model import Status
from app.modules.roles.model import Role
from app.modules.permissions.model import Permission
from app.modules.role_permissions.model import RolePermission
from app.modules.clinics.model import Clinic
from app.modules.users.model import User
from app.modules.patients.model import Patient
from app.modules.exams.model import Exam
from app.modules.ai_analysis.model import AIAnalysis
from app.modules.audit_logs.model import AuditLog
