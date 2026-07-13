"""
Seed do módulo de role_permissions.

Este arquivo cria os vínculos iniciais entre perfis de acesso
e permissões do sistema.
"""

from sqlalchemy.orm import Session

from app.modules.permissions.model import Permission
from app.modules.roles.model import Role
from app.modules.role_permissions.model import RolePermission


def apply_permissions_to_role(
    db: Session,
    role: Role,
    permissions: dict[str, Permission],
    permission_names: list[str],
) -> None:
    """
    Reconcilia os vínculos de uma role com a matriz oficial de permissões:
    adiciona os que estão faltando E remove os que existem no banco mas
    não estão mais na lista atual.

    Antes, esta função só adicionava (get_or_create), nunca removia — se
    uma versão anterior do seed concedeu uma permissão a uma role e a
    versão atual a retirou da lista, rodar o seed de novo num banco já
    inicializado NÃO revogava o vínculo antigo. Isso já aconteceu de
    verdade neste projeto: o Funcionário da Clínica chegou a ter
    exams:read/ai_analysis:read concedidos, removidos manualmente depois
    — um reseed num banco desatualizado reintroduziria esse acesso.

    Permissões oficiais ausentes do catálogo de `permissions` (ainda não
    seedadas) fazem a função levantar erro, em vez de ignorar
    silenciosamente — um nome errado na matriz deve ser percebido agora,
    não silenciar um vínculo que a role deveria ter.
    """
    permissoes_desejadas: dict[str, Permission] = {}
    for permission_name in permission_names:
        permission = permissions.get(permission_name)
        if not permission:
            raise ValueError(
                f"Permissão '{permission_name}' referenciada para a role "
                f"'{role.name}' não existe no catálogo de permissions seedadas. "
                "Corrija o nome na matriz ou adicione a permissão ao seed de permissions."
            )
        permissoes_desejadas[permission_name] = permission

    vinculos_atuais = (
        db.query(RolePermission).filter(RolePermission.role_id == role.id).all()
    )
    permission_id_by_id = {p.id: p for p in permissions.values()}
    ids_atuais = {rp.permission_id for rp in vinculos_atuais}
    ids_desejados = {p.id for p in permissoes_desejadas.values()}

    # Remove vínculos que existem no banco mas não estão mais na matriz.
    ids_para_remover = ids_atuais - ids_desejados
    if ids_para_remover:
        db.query(RolePermission).filter(
            RolePermission.role_id == role.id,
            RolePermission.permission_id.in_(ids_para_remover),
        ).delete(synchronize_session=False)

    # Adiciona vínculos que estão na matriz mas ainda não existem no banco.
    ids_para_adicionar = ids_desejados - ids_atuais
    for permission_id in ids_para_adicionar:
        db.add(RolePermission(role_id=role.id, permission_id=permission_id))


def seed_role_permissions(
    db: Session,
    roles: dict[str, Role],
    permissions: dict[str, Permission],
) -> None:
    """
    Cria os vínculos iniciais entre roles e permissions.
    """

    # Admin
    admin_master_permissions = list(permissions.keys())

    # Doctor
    doctor_permissions = [
        "users:read_profile",
        "users:update_profile",

        "clinics:read_profile",
        "clinics:update_profile",
        
        "patients:create",
        "patients:read",
        "patients:update",
        "patients:change_status",

        "exams:create",
        "exams:read",
        "exams:update",
        "exams:upload",
        "exams:download",
        "exams:change_status",
        "exams:review",

        "ai_analysis:create",
        "ai_analysis:read",
        "ai_analysis:update",
        "ai_analysis:download",
    ]

    # Clinic_staff
    clinic_staff_permissions = [
        "users:read_profile",
        "users:update_profile",

        "clinics:read_profile",
        "clinics:update_profile",
        
        "patients:create",
        "patients:read",
        "patients:update",
        "patients:change_status",
    ]

    role_permission_map = {
        "admin_master": admin_master_permissions,
        "doctor": doctor_permissions,
        "clinic_staff": clinic_staff_permissions,
    }

    for role_name, permission_names in role_permission_map.items():
        role = roles.get(role_name)

        if not role:
            continue

        apply_permissions_to_role(
            db=db,
            role=role,
            permissions=permissions,
            permission_names=permission_names,
        )

    # Commit único no final: a reconciliação (remover + adicionar) de
    # todas as roles acontece na mesma transação — uma falha no meio não
    # deixa metade das roles com privilégios revogados e a outra metade
    # ainda com os antigos.
    db.commit()
    