"""
Validadores e normalizadores reutilizáveis da aplicação.

Este arquivo centraliza regras simples usadas por diferentes schemas,
como limpeza de documentos, telefones, CEP, UF e textos.
"""

import re


def only_digits(value: str | None) -> str | None:
    """
    Remove todos os caracteres que não forem números.
    """
    if value is None:
        return None

    cleaned = re.sub(r"\D", "", value)
    return cleaned or None


# Alias mantido para leitura semântica em módulos que usam "números".
only_numbers = only_digits


def normalize_required_text(value: str, error_message: str = "Campo obrigatório.") -> str:
    """
    Remove espaços extras de um campo textual obrigatório.
    """
    value = value.strip()

    if not value:
        raise ValueError(error_message)

    return value


def normalize_optional_text(value: str | None) -> str | None:
    """
    Remove espaços extras de um campo textual opcional.

    Se o valor ficar vazio após a limpeza, retorna None.
    """
    if value is None:
        return None

    value = value.strip()
    return value or None


def normalize_lower_text(value: str, error_message: str = "Campo obrigatório.") -> str:
    """
    Remove espaços extras e converte um campo textual obrigatório para lowercase.
    """
    value = normalize_required_text(value, error_message)
    return value.lower()


def normalize_optional_lower_text(
    value: str | None,
    error_message: str = "Campo obrigatório.",
) -> str | None:
    """
    Remove espaços extras e converte um campo textual opcional para lowercase.
    """
    if value is None:
        return None

    return normalize_lower_text(value, error_message)


def normalize_email(value: str) -> str:
    """
    Remove espaços extras e converte e-mail para lowercase.
    """
    return normalize_lower_text(value, "E-mail é obrigatório.")


def normalize_optional_email(value: str | None) -> str | None:
    """
    Normaliza e-mail opcional.
    """
    if value is None:
        return None

    return normalize_email(value)


def normalize_state(value: str | None) -> str | None:
    """
    Normaliza UF para uppercase e valida se possui 2 caracteres.
    """
    if value is None:
        return None

    value = value.strip().upper()

    if len(value) != 2:
        raise ValueError("UF deve conter 2 caracteres.")

    return value


def normalize_zip_code(value: str | None) -> str | None:
    """
    Remove máscara do CEP e valida se possui 8 dígitos.
    """
    cleaned = only_digits(value)

    if cleaned is not None and len(cleaned) != 8:
        raise ValueError("CEP deve conter 8 dígitos.")

    return cleaned


def normalize_phone(value: str | None) -> str | None:
    """
    Remove máscara de telefone e valida tamanho mínimo.
    """
    cleaned = only_digits(value)

    if cleaned is not None and len(cleaned) < 10:
        raise ValueError("Telefone deve conter pelo menos 10 dígitos.")

    return cleaned


def validate_password_length(value: str) -> str:
    """
    Garante que a senha não ultrapasse o limite de 72 bytes do bcrypt.

    O bcrypt ignora silenciosamente qualquer byte além do 72º — ou seja,
    duas senhas diferentes que compartilhem os primeiros 72 bytes seriam
    tratadas como idênticas. Como caracteres não-ASCII podem ocupar mais
    de 1 byte em UTF-8, validamos o tamanho em bytes, não em caracteres.
    """
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Senha não pode ultrapassar 72 bytes (bcrypt).")

    return value


def validate_birth_date(value):
    """
    Valida se a data de nascimento é plausível.

    Regras:
    - não pode estar no futuro;
    - não pode implicar idade acima de 130 anos (proteção contra erro de
      digitação, ex: ano trocado).
    """
    if value is None:
        return None

    from datetime import date as _date

    today = _date.today()

    if value > today:
        raise ValueError("Data de nascimento não pode estar no futuro.")

    max_age_days = 130 * 365
    if (today - value).days > max_age_days:
        raise ValueError("Data de nascimento inválida (idade acima de 130 anos).")

    return value


BRAZILIAN_UFS = frozenset(
    {
        "AC",
        "AL",
        "AP",
        "AM",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MT",
        "MS",
        "MG",
        "PA",
        "PB",
        "PR",
        "PE",
        "PI",
        "RJ",
        "RN",
        "RS",
        "RO",
        "RR",
        "SC",
        "SP",
        "SE",
        "TO",
    }
)


def normalize_crm_number(value: str | None) -> str | None:
    """Normaliza o número do CRM sem realizar consulta ao CFM."""

    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    if not cleaned.isdigit():
        raise ValueError("CRM deve conter somente números.")

    if len(cleaned) > 10:
        raise ValueError("CRM deve conter no máximo 10 números.")

    return cleaned


def normalize_crm_uf(value: str | None) -> str | None:
    """Normaliza e valida a unidade federativa do CRM."""

    if value is None:
        return None

    cleaned = value.strip().upper()
    if not cleaned:
        return None

    if cleaned not in BRAZILIAN_UFS:
        raise ValueError("UF do CRM inválida.")

    return cleaned


def is_valid_cpf(cpf: str | None) -> bool:
    """
    Valida CPF pelo algoritmo oficial dos dígitos verificadores.
    """
    cpf = only_digits(cpf)

    if not cpf or len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:
        return False

    first_sum = sum(int(cpf[i]) * (10 - i) for i in range(9))
    first_digit = 0 if first_sum % 11 < 2 else 11 - (first_sum % 11)

    second_sum = sum(int(cpf[i]) * (11 - i) for i in range(10))
    second_digit = 0 if second_sum % 11 < 2 else 11 - (second_sum % 11)

    return cpf[-2:] == f"{first_digit}{second_digit}"


def validate_cpf(value: str | None, required: bool = True) -> str | None:
    """
    Remove máscara e valida CPF.
    """
    cleaned = only_digits(value)

    if cleaned is None:
        if required:
            raise ValueError("CPF inválido.")
        return None

    if not is_valid_cpf(cleaned):
        raise ValueError("CPF inválido.")

    return cleaned


def normalize_cpf(value: str | None) -> str | None:
    """
    Remove máscara do CPF e valida apenas o tamanho.

    Útil para módulos que ainda não aplicam validação completa do dígito verificador.
    """
    cleaned = only_digits(value)

    if cleaned is not None and len(cleaned) != 11:
        raise ValueError("CPF deve conter 11 números.")

    return cleaned


def is_valid_cnpj(cnpj: str | None) -> bool:
    """
    Valida CNPJ pelo algoritmo oficial dos dígitos verificadores.
    """
    cnpj = only_digits(cnpj)

    if not cnpj or len(cnpj) != 14:
        return False

    if cnpj == cnpj[0] * 14:
        return False

    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    first_sum = sum(int(cnpj[i]) * first_weights[i] for i in range(12))
    first_digit = 0 if first_sum % 11 < 2 else 11 - (first_sum % 11)

    second_sum = sum(int(cnpj[i]) * second_weights[i] for i in range(13))
    second_digit = 0 if second_sum % 11 < 2 else 11 - (second_sum % 11)

    return cnpj[-2:] == f"{first_digit}{second_digit}"


def validate_cnpj(value: str | None, required: bool = True) -> str | None:
    """
    Remove máscara e valida CNPJ.
    """
    cleaned = only_digits(value)

    if cleaned is None:
        if required:
            raise ValueError("CNPJ inválido.")
        return None

    if not is_valid_cnpj(cleaned):
        raise ValueError("CNPJ inválido.")

    return cleaned
