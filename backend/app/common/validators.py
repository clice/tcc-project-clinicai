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
