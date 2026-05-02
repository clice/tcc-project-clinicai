"""
Seed do módulo de permissions.

Este arquivo cadastra as permissões iniciais usadas pelo sistema.
"""

from sqlalchemy.orm import Session

from app.modules.permissions.model import Permission


def get_or_create_permission(
    db: Session,
    name: str,
    display_name: str,
    description: str | None,
    module: str,
) -> Permission:
    """
    Busca uma permission existente ou cria uma nova.

    Evita duplicação nos seeds.
    """
    permission = db.query(Permission).filter(Permission.name == name).first()

    if permission:
        return permission

    permission = Permission(
        name=name,
        display_name=display_name,
        description=description,
        module=module,
    )

    db.add(permission)
    db.commit()
    db.refresh(permission)

    return permission


def seed_permissions(db: Session) -> dict[str, Permission]:
    """
    Cria as permissões iniciais do sistema.

    Retorna um dicionário para que outros seeds possam reutilizar
    esses registros, por exemplo no futuro seed de role_permissions.
    """

    permissions = {
        "users": {
            "users:create": {
                "display_name": "Criar Usuários",
                "description": "Permite cadastrar novos usuários no sistema.",
            },
            "users:read": {
                "display_name": "Visualizar Usuários",
                "description": "Permite visualizar usuários cadastrados.",
            },
            "users:update": {
                "display_name": "Atualizar Usuários",
                "description": "Permite editar dados de usuários.",
            },
            "users:change_status": {
                "display_name": "Alterar Status dos Usuários",
                "description": "Permite ativar, inativar ou alterar o status dos usuários.",
            },
        },
        "clinics": {
            "clinics:create": {
                "display_name": "Criar Clínicas",
                "description": "Permite cadastrar novas clínicas.",
            },
            "clinics:read": {
                "display_name": "Visualizar Clínicas",
                "description": "Permite visualizar clínicas cadastradas.",
            },
            "clinics:update": {
                "display_name": "Atualizar Clínicas",
                "description": "Permite editar dados de clínicas.",
            },
            "clinics:change_status": {
                "display_name": "Alterar Status das Clínicas",
                "description": "Permite ativar, inativar ou alterar o status das clínicas.",
            },
        },
        "roles": {
            "roles:create": {
                "display_name": "Criar Perfis de Acesso",
                "description": "Permite cadastrar novos perfis de acesso.",
            },
            "roles:read": {
                "display_name": "Visualizar Perfis de Acesso",
                "description": "Permite visualizar perfis de acesso.",
            },
            "roles:update": {
                "display_name": "Atualizar Perfis de Acesso",
                "description": "Permite editar perfis de acesso.",
            },
            "roles:delete": {
                "display_name": "Excluir Perfis de Acesso",
                "description": "Permite excluir ou arquivar perfis de acesso.",
            },
        },
        "permissions": {
            "permissions:create": {
                "display_name": "Criar Permissões",
                "description": "Permite cadastrar novas permissões do sistema.",
            },
            "permissions:read": {
                "display_name": "Visualizar Permissões",
                "description": "Permite visualizar permissões do sistema.",
            },
            "permissions:update": {
                "display_name": "Atualizar Permissões",
                "description": "Permite editar permissões do sistema.",
            },
        },
        "patients": {
            "patients:create": {
                "display_name": "Criar Pacientes",
                "description": "Permite cadastrar novos pacientes.",
            },
            "patients:read": {
                "display_name": "Visualizar Pacientes",
                "description": "Permite visualizar pacientes cadastrados.",
            },
            "patients:update": {
                "display_name": "Atualizar Pacientes",
                "description": "Permite editar dados de pacientes.",
            },
            "patients:change_status": {
                "display_name": "Alterar Status dos Pacientes",
                "description": "Permite ativar ou inativar pacientes.",
            },
        },
        "exams": {
            "exams:create": {
                "display_name": "Criar Exames",
                "description": "Permite cadastrar exames.",
            },
            "exams:read": {
                "display_name": "Visualizar Exames",
                "description": "Permite visualizar exames cadastrados.",
            },
            "exams:update": {
                "display_name": "Atualizar Exames",
                "description": "Permite editar dados de exames.",
            },
            "exams:delete": {
                "display_name": "Excluir Exames",
                "description": "Permite excluir ou arquivar exames.",
            },
            "exams:upload_file": {
                "display_name": "Enviar Arquivos de Exames",
                "description": "Permite anexar arquivos aos exames.",
            },
            "exams:download_file": {
                "display_name": "Baixar Arquivos de Exames",
                "description": "Permite baixar arquivos anexados aos exames.",
            },
        },
        "ai_analysis": {
            "ai_analysis:create": {
                "display_name": "Criar Análise por IA",
                "description": "Permite solicitar análise automatizada de exames por IA.",
            },
            "ai_analysis:read": {
                "display_name": "Visualizar Análise por IA",
                "description": "Permite visualizar resultados de análises por IA.",
            },
            "ai_analysis:update": {
                "display_name": "Atualizar Análise por IA",
                "description": "Permite atualizar metadados ou revisão da análise por IA.",
            },
            "ai_analysis:review": {
                "display_name": "Revisar Análise por IA",
                "description": "Permite registrar revisão médica sobre uma análise gerada por IA.",
            },
        },
        "audit_logs": {
            "audit_logs:read": {
                "display_name": "Visualizar Logs de Auditoria",
                "description": "Permite visualizar registros de auditoria do sistema.",
            },
        },
    }

    created_permissions: dict[str, Permission] = {}

    for module, module_permissions in permissions.items():
        for name, data in module_permissions.items():
            created_permissions[name] = get_or_create_permission(
                db=db,
                name=name,
                display_name=data["display_name"],
                description=data["description"],
                module=module,
            )

    return created_permissions
