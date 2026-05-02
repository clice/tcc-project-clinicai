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

    email = payload.get("sub")

    if not email:
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
        .filter(User.email == email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
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

        user_permissions = [
            role_permission.permission.name
            for role_permission in current_user.role.role_permissions
            if role_permission.permission is not None
        ]

        if permission_name not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{permission_name}' necessária.",
            )

        return current_user

    return permission_checker