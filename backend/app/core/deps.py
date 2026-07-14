"""
Dependências globais de autenticação e autorização.

Este arquivo centraliza funções reutilizáveis para:
- obter o usuário autenticado a partir do token JWT;
- restringir rotas para administradores;
- validar permissões específicas por perfil de acesso.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload

from app.common.constants import RoleName
from app.core.database import get_db
from app.core.security import decode_access_token
from app.modules.role_permissions.model import RolePermission
from app.modules.roles.model import Role
from app.modules.users.model import User


# Define o endpoint usado pelo Swagger/OpenAPI para obter o token de autenticação.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Retorna o usuário autenticado com base no token JWT enviado na requisição.
    O token deve conter o campo 'sub', que neste projeto representa o e-mail
    do usuário autenticado.
    """
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )

    user_id = payload.get("sub")
    token_version = payload.get("token_version")

    if not user_id or token_version is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
        )

    user = (
        db.query(User)
        .options(
            joinedload(User.role)
            .joinedload(Role.role_permissions)
            .joinedload(RolePermission.permission),
            joinedload(User.status),
            joinedload(User.clinic),
        )
        .filter(User.id == int(user_id))
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
        )

    if user.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada. Faça login novamente.",
        )

    if not user.status or user.status.name != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo ou bloqueado.",
        )

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Permite acesso apenas para usuários com perfil admin_master.
    """
    if current_user.role is None or current_user.role.name != "admin_master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )

    return current_user


def get_user_permission_names(current_user: User) -> set[str]:
    """Retorna as permissões válidas vinculadas à role do usuário."""

    if current_user.role is None:
        return set()

    return {
        role_permission.permission.name
        for role_permission in current_user.role.role_permissions
        if role_permission.permission is not None
    }


def require_permission(permission_name: str):
    def permission_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """
        Cria uma dependência para validar se o usuário possui uma permissão específica.

        O admin_master possui acesso total.
        """
        if current_user.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário sem perfil de acesso.",
            )

        if current_user.role.name == "admin_master":
            return current_user

        user_permissions = get_user_permission_names(current_user)

        if permission_name not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{permission_name}' necessária.",
            )

        return current_user

    return permission_checker


def require_doctor_permission(permission_name: str):
    """Exige simultaneamente perfil médico e uma permissão explícita.

    Esta dependência não aplica o bypass de ``admin_master`` usado nas ações
    administrativas. Revisão clínica é uma atribuição profissional não
    delegável e exige que o usuário tenha role ``doctor`` de fato.
    """

    def doctor_permission_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if (
            current_user.role is None
            or current_user.role.name != RoleName.DOCTOR.value
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas usuários com perfil médico podem revisar exames.",
            )

        if permission_name not in get_user_permission_names(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{permission_name}' necessária.",
            )

        return current_user

    # Metadados simples permitem que testes de regressão inspecionem a regra
    # registrada na rota sem depender do nome interno da função closure.
    doctor_permission_checker.required_role_name = RoleName.DOCTOR.value
    doctor_permission_checker.required_permission_name = permission_name

    return doctor_permission_checker
