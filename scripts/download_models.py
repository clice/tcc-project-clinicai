#!/usr/bin/env python3
"""Baixa e verifica os artefatos de IA publicados em uma GitHub Release."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ARTEFATOS_OBRIGATORIOS = {
    "resnet50.pt",
    "efficientnet_b4.pt",
    "pvt_v2_b2.pt",
    "meta_classificador.joblib",
}
TAMANHO_BLOCO = 1024 * 1024


class ErroDownload(RuntimeError):
    """Indica uma falha segura na obtenção ou validação dos modelos."""


def _sha256(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(TAMANHO_BLOCO), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def _baixar(url: str, destino: Path) -> None:
    requisicao = Request(url, headers={"User-Agent": "ClinicAI-model-downloader/1.0"})
    try:
        with urlopen(requisicao, timeout=60) as resposta, destino.open("wb") as arquivo:
            while bloco := resposta.read(TAMANHO_BLOCO):
                arquivo.write(bloco)
    except (HTTPError, URLError, TimeoutError, OSError) as erro:
        destino.unlink(missing_ok=True)
        raise ErroDownload(f"Não foi possível baixar {url}: {erro}") from erro


def _carregar_manifesto(url: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="clinicai-manifesto-") as temporario:
        caminho = Path(temporario) / "manifesto.json"
        _baixar(url, caminho)
        try:
            manifesto = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as erro:
            raise ErroDownload(f"Manifesto inválido: {erro}") from erro
    if not isinstance(manifesto, dict):
        raise ErroDownload("O manifesto precisa ser um objeto JSON.")
    return manifesto


def _validar_manifesto(manifesto: dict[str, Any], release_tag: str) -> list[dict[str, Any]]:
    if manifesto.get("schema_version") != 1:
        raise ErroDownload("Versão de esquema do manifesto não suportada.")
    if manifesto.get("release_tag") != release_tag:
        raise ErroDownload("A tag do manifesto não corresponde à release solicitada.")
    if manifesto.get("domain") != "gastrointestinal":
        raise ErroDownload("O manifesto não pertence ao domínio gastrointestinal.")
    artefatos = manifesto.get("artifacts")
    if not isinstance(artefatos, list):
        raise ErroDownload("O campo 'artifacts' do manifesto precisa ser uma lista.")
    nomes = {item.get("name") for item in artefatos if isinstance(item, dict)}
    if len(artefatos) != len(ARTEFATOS_OBRIGATORIOS) or nomes != ARTEFATOS_OBRIGATORIOS:
        faltantes = sorted(ARTEFATOS_OBRIGATORIOS - nomes)
        extras = sorted(nome for nome in nomes - ARTEFATOS_OBRIGATORIOS if isinstance(nome, str))
        raise ErroDownload(
            f"Conjunto de artefatos inválido. Faltantes: {faltantes or 'nenhum'}; "
            f"extras: {extras or 'nenhum'}."
        )
    for item in artefatos:
        nome = item.get("name")
        hash_esperado = item.get("sha256")
        tamanho = item.get("size_bytes")
        if Path(nome).name != nome:
            raise ErroDownload(f"Nome de artefato inseguro: {nome!r}.")
        if not isinstance(hash_esperado, str) or len(hash_esperado) != 64:
            raise ErroDownload(f"SHA-256 inválido para {nome}.")
        try:
            int(hash_esperado, 16)
        except ValueError as erro:
            raise ErroDownload(f"SHA-256 inválido para {nome}.") from erro
        if not isinstance(tamanho, int) or tamanho <= 0:
            raise ErroDownload(f"Tamanho inválido para {nome}.")
    return artefatos


def _arquivo_valido(caminho: Path, tamanho: int, hash_esperado: str) -> bool:
    return caminho.is_file() and caminho.stat().st_size == tamanho and _sha256(caminho) == hash_esperado


def _conteudo_manifesto(manifesto: dict[str, Any]) -> str:
    return json.dumps(manifesto, indent=2, ensure_ascii=False) + "\n"


def _atualizar_somente_manifesto(
    destino: Path,
    nome_manifesto: str,
    manifesto: dict[str, Any],
) -> None:
    caminho_temporario = destino / f".{nome_manifesto}.part"
    try:
        caminho_temporario.write_text(_conteudo_manifesto(manifesto), encoding="utf-8")
        caminho_temporario.replace(destino / nome_manifesto)
    except OSError as erro:
        caminho_temporario.unlink(missing_ok=True)
        raise ErroDownload(f"Não foi possível instalar o manifesto validado: {erro}") from erro


def _instalar_conjunto_validado(
    *,
    destino: Path,
    nome_manifesto: str,
    manifesto: dict[str, Any],
    artefatos: list[dict[str, Any]],
    base_url: str,
) -> None:
    """Prepara todos os artefatos antes de substituir o conjunto instalado."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and not destino.is_dir():
        raise ErroDownload(f"O destino dos modelos não é um diretório: {destino}")

    todos_validos = destino.is_dir() and all(
        _arquivo_valido(destino / item["name"], item["size_bytes"], item["sha256"])
        for item in artefatos
    )
    if todos_validos:
        for item in artefatos:
            print(f"[OK] {item['name']} já existe e possui o SHA-256 esperado.")
        _atualizar_somente_manifesto(destino, nome_manifesto, manifesto)
        return

    diretorio_temporario = Path(
        tempfile.mkdtemp(prefix=f".{destino.name}-staging-", dir=destino.parent)
    )
    diretorio_backup: Path | None = None
    backup: Path | None = None

    try:
        for item in artefatos:
            nome = item["name"]
            caminho_atual = destino / nome
            caminho_preparado = diretorio_temporario / nome

            if _arquivo_valido(caminho_atual, item["size_bytes"], item["sha256"]):
                shutil.copy2(caminho_atual, caminho_preparado)
                print(f"[OK] {nome} reaproveitado e verificado.")
                continue

            print(f"[DOWNLOAD] Baixando {nome}...")
            _baixar(f"{base_url}/{quote(nome, safe='')}", caminho_preparado)
            if not _arquivo_valido(caminho_preparado, item["size_bytes"], item["sha256"]):
                raise ErroDownload(f"A verificação de tamanho ou SHA-256 falhou para {nome}.")
            print(f"[VALIDADO] {nome} baixado e verificado.")

        (diretorio_temporario / nome_manifesto).write_text(
            _conteudo_manifesto(manifesto), encoding="utf-8"
        )

        diretorio_backup = Path(
            tempfile.mkdtemp(prefix=f".{destino.name}-backup-", dir=destino.parent)
        )
        backup = diretorio_backup / "versao-anterior"

        try:
            if destino.exists():
                destino.replace(backup)
            diretorio_temporario.replace(destino)
        except OSError as erro:
            if backup.exists() and not destino.exists():
                backup.replace(destino)
            raise ErroDownload(
                f"Não foi possível instalar o conjunto completo de modelos: {erro}"
            ) from erro

        print("[OK] Conjunto completo de modelos instalado de forma transacional.")
    except OSError as erro:
        raise ErroDownload(f"Não foi possível preparar os modelos: {erro}") from erro
    finally:
        if diretorio_temporario.exists():
            shutil.rmtree(diretorio_temporario, ignore_errors=True)
        if diretorio_backup is not None and diretorio_backup.exists():
            shutil.rmtree(diretorio_backup, ignore_errors=True)


def baixar_modelos() -> None:
    repositorio = os.environ.get("MODEL_RELEASE_REPOSITORY", "clice/tcc-project-clinicai")
    release_tag = os.environ.get("MODEL_RELEASE_TAG", "models-v0.1.0")
    nome_manifesto = os.environ.get("MODEL_RELEASE_MANIFEST", "manifesto_modelos.json")
    destino = Path(os.environ.get("MODEL_DESTINATION_DIR", "/models/gastrointestinal"))
    servidor = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    base_personalizada = os.environ.get("MODEL_RELEASE_BASE_URL")
    if repositorio.count("/") != 1:
        raise ErroDownload("MODEL_RELEASE_REPOSITORY deve usar o formato proprietario/repositorio.")
    if Path(nome_manifesto).name != nome_manifesto:
        raise ErroDownload("MODEL_RELEASE_MANIFEST deve conter somente o nome do arquivo.")
    base_url = base_personalizada or (
        f"{servidor}/{quote(repositorio, safe='/')}/releases/download/{quote(release_tag, safe='')}"
    )
    manifesto = _carregar_manifesto(f"{base_url}/{quote(nome_manifesto, safe='')}")
    artefatos = _validar_manifesto(manifesto, release_tag)
    _instalar_conjunto_validado(
        destino=destino,
        nome_manifesto=nome_manifesto,
        manifesto=manifesto,
        artefatos=artefatos,
        base_url=base_url,
    )
    print(f"Modelos da release {release_tag} prontos em {destino}.")


if __name__ == "__main__":
    try:
        baixar_modelos()
    except ErroDownload as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        raise SystemExit(1) from erro
