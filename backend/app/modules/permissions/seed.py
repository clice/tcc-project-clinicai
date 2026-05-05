"""
Seed do módulo de permissions.

Este arquivo cadastra apenas as permissões oficiais definidas em constants.py.
"""

from sqlalchemy.orm import Session

from app.common.constants import PermissionAction, SystemModule
from app.modules.permissions.model import Permission


def build_permission_name(
    module: SystemModule,
    action: PermissionAction,
) -> str:
    return f"{module.value}:{action.value}"


def get_or_create_permission(
    db: Session,
    module: SystemModule,
    action: PermissionAction,
    display_name: str,
    description: str | None = None,
) -> Permission:
    name = build_permission_name(module, action)

    permission = db.query(Permission).filter(Permission.name == name).first()

    if permission:
        return permission

    permission = Permission(
        name=name,
        display_name=display_name,
        description=description,
        module=module.value,
    )

    db.add(permission)
    db.commit()
    db.refresh(permission)

    return permission


def seed_permissions(db: Session) -> dict[str, Permission]:
    permissions_config = [
        # Users
        (SystemModule.USERS, PermissionAction.CREATE, "Criar Usuários", "Permite cadastrar novos usuários no sistema."),
        (SystemModule.USERS, PermissionAction.READ, "Visualizar Usuários", "Permite visualizar usuários cadastrados."),
        (SystemModule.USERS, PermissionAction.UPDATE, "Atualizar Usuários", "Permite editar dados de usuários."),
        (SystemModule.USERS, PermissionAction.CHANGE_STATUS, "Alterar Status dos Usuários", "Permite ativar, inativar ou bloquear usuários."),

        # Clinics
        (SystemModule.CLINICS, PermissionAction.CREATE, "Criar Clínicas", "Permite cadastrar novas clínicas."),
        (SystemModule.CLINICS, PermissionAction.READ, "Visualizar Clínicas", "Permite visualizar clínicas cadastradas."),
        (SystemModule.CLINICS, PermissionAction.UPDATE, "Atualizar Clínicas", "Permite editar dados de clínicas."),
        (SystemModule.CLINICS, PermissionAction.CHANGE_STATUS, "Alterar Status das Clínicas", "Permite ativar, inativar ou bloquear clínicas."),

        # Roles
        (SystemModule.ROLES, PermissionAction.CREATE, "Criar Perfis de Acesso", "Permite cadastrar novos perfis de acesso."),
        (SystemModule.ROLES, PermissionAction.READ, "Visualizar Perfis de Acesso", "Permite visualizar perfis de acesso."),
        (SystemModule.ROLES, PermissionAction.UPDATE, "Atualizar Perfis de Acesso", "Permite editar perfis de acesso."),
        (SystemModule.ROLES, PermissionAction.DELETE, "Excluir Perfis de Acesso", "Permite excluir perfis de acesso."),

        # Permissions
        (SystemModule.PERMISSIONS, PermissionAction.CREATE, "Criar Permissões", "Permite cadastrar novas permissões do sistema."),
        (SystemModule.PERMISSIONS, PermissionAction.READ, "Visualizar Permissões", "Permite visualizar permissões do sistema."),
        (SystemModule.PERMISSIONS, PermissionAction.UPDATE, "Atualizar Permissões", "Permite editar permissões do sistema."),

        # Role Permissions
        (SystemModule.ROLE_PERMISSIONS, PermissionAction.CREATE, "Vincular Permissões", "Permite vincular permissões a perfis."),
        (SystemModule.ROLE_PERMISSIONS, PermissionAction.READ, "Visualizar Permissões por Perfil", "Permite visualizar vínculos entre perfis e permissões."),
        (SystemModule.ROLE_PERMISSIONS, PermissionAction.UPDATE, "Atualizar Permissões por Perfil", "Permite atualizar vínculos entre perfis e permissões."),
        (SystemModule.ROLE_PERMISSIONS, PermissionAction.DELETE, "Remover Permissões por Perfil", "Permite remover permissões de perfis."),

        # Statuses
        (SystemModule.STATUSES, PermissionAction.CREATE, "Criar Status", "Permite cadastrar status do sistema."),
        (SystemModule.STATUSES, PermissionAction.READ, "Visualizar Status", "Permite visualizar status do sistema."),
        (SystemModule.STATUSES, PermissionAction.UPDATE, "Atualizar Status", "Permite editar status do sistema."),

        # Patients
        (SystemModule.PATIENTS, PermissionAction.CREATE, "Criar Pacientes", "Permite cadastrar novos pacientes."),
        (SystemModule.PATIENTS, PermissionAction.READ, "Visualizar Pacientes", "Permite visualizar pacientes cadastrados."),
        (SystemModule.PATIENTS, PermissionAction.UPDATE, "Atualizar Pacientes", "Permite editar dados de pacientes."),
        (SystemModule.PATIENTS, PermissionAction.CHANGE_STATUS, "Alterar Status dos Pacientes", "Permite ativar ou inativar pacientes."),

        # Exams
        (SystemModule.EXAMS, PermissionAction.CREATE, "Criar Exames", "Permite cadastrar exames."),
        (SystemModule.EXAMS, PermissionAction.READ, "Visualizar Exames", "Permite visualizar exames cadastrados."),
        (SystemModule.EXAMS, PermissionAction.UPDATE, "Atualizar Exames", "Permite editar dados de exames."),
        (SystemModule.EXAMS, PermissionAction.DELETE, "Excluir Exames", "Permite excluir exames."),
        (SystemModule.EXAMS, PermissionAction.CHANGE_STATUS, "Alterar Status dos Exames", "Permite cancelar, concluir ou alterar status de exames."),
        (SystemModule.EXAMS, PermissionAction.UPLOAD, "Upload de Exames", "Permite fazer o upload dos exames."),
        (SystemModule.EXAMS, PermissionAction.DOWNLOAD, "Baixar Exames", "Permite baixar os exames."),

        # AI Analysis
        (SystemModule.AI_ANALYSIS, PermissionAction.CREATE, "Criar Análise por IA", "Permite solicitar análise automatizada de exames por IA."),
        (SystemModule.AI_ANALYSIS, PermissionAction.READ, "Visualizar Análise por IA", "Permite visualizar resultados de análises por IA."),
        (SystemModule.AI_ANALYSIS, PermissionAction.UPDATE, "Atualizar Análise por IA", "Permite atualizar ou revisar análise por IA."),
        (SystemModule.AI_ANALYSIS, PermissionAction.DOWNLOAD, "Baixar Análise por IA", "Permite baixar a análise por IA."),

        # Audit Logs
        (SystemModule.AUDIT_LOGS, PermissionAction.READ, "Visualizar Logs de Auditoria", "Permite visualizar registros de auditoria do sistema."),
    ]

    created_permissions: dict[str, Permission] = {}

    for module, action, display_name, description in permissions_config:
        permission = get_or_create_permission(
            db=db,
            module=module,
            action=action,
            display_name=display_name,
            description=description,
        )

        created_permissions[permission.name] = permission

    return created_permissions
