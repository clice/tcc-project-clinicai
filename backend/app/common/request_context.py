"""Contexto HTTP usado pelos registros automáticos de auditoria."""

from contextlib import contextmanager
from contextvars import ContextVar
from collections.abc import Iterator


_request_ip_address: ContextVar[str | None] = ContextVar(
    "request_ip_address",
    default=None,
)

_request_user_agent: ContextVar[str | None] = ContextVar(
    "request_user_agent",
    default=None,
)


@contextmanager
def bind_request_audit_context(
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> Iterator[None]:
    """Associa metadados HTTP somente durante a requisição atual."""

    ip_token = _request_ip_address.set(
        ip_address
    )
    user_agent_token = _request_user_agent.set(
        user_agent
    )

    try:
        yield
    finally:
        _request_user_agent.reset(
            user_agent_token
        )
        _request_ip_address.reset(
            ip_token
        )


def get_request_audit_context() -> tuple[
    str | None,
    str | None,
]:
    """Retorna IP e user-agent da requisição atual, quando existir."""

    return (
        _request_ip_address.get(),
        _request_user_agent.get(),
    )
