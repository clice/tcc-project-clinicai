#!/usr/bin/env python3
"""Validação estática do CHK-02.

Confirma que os manifests, locks e Dockerfiles usados nas três imagens são
portáveis e reproduzíveis no ambiente Linux do projeto.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REQ_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)(?:\[(?P<extras>[^\]]+)\])?==(?P<version>[^\s\\;]+)"
)
EXACT_FROM_RE = re.compile(
    r"^FROM\s+(?P<image>[^\s:@]+):(?P<tag>[^\s@]+)@sha256:(?P<digest>[0-9a-f]{64})\s*$",
    re.MULTILINE,
)
ALLOWED_NPM_HOSTS = {"registry.npmjs.org"}
FORBIDDEN_HOST_MARKERS = (
    "internal",
    "artifactory",
    "openai.org",
    "localhost",
    "127.0.0.1",
)


def canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_direct_requirements(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    errors: list[str] = []

    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-", "--")):
            errors.append(f"{path}:{number}: opção não permitida no manifest: {line}")
            continue

        match = REQ_RE.fullmatch(line)
        if not match:
            errors.append(f"{path}:{number}: use versão exata com '==': {line}")
            continue

        name = canonical_name(match.group("name"))
        version = match.group("version")
        previous = result.get(name)
        if previous and previous != version:
            errors.append(
                f"{path}:{number}: versões conflitantes para {name}: {previous} e {version}"
            )
        result[name] = version

    if errors:
        raise ValueError("\n".join(errors))
    return result


def parse_hashed_lock(path: Path) -> tuple[dict[str, str], list[str]]:
    """Lê um lock pip-tools/uv e exige hash em toda dependência fixada."""
    packages: dict[str, str] = {}
    errors: list[str] = []
    current_name: str | None = None
    current_line = 0
    current_has_hash = False

    def finish_current() -> None:
        nonlocal current_name, current_line, current_has_hash
        if current_name is not None and not current_has_hash:
            errors.append(
                f"{path}:{current_line}: {current_name} não possui hash no lock"
            )
        current_name = None
        current_line = 0
        current_has_hash = False

    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        match = REQ_RE.match(stripped)
        if match:
            finish_current()
            name = canonical_name(match.group("name"))
            version = match.group("version")
            previous = packages.get(name)
            if previous and previous != version:
                errors.append(
                    f"{path}:{number}: versões conflitantes para {name}: {previous} e {version}"
                )
            packages[name] = version
            current_name = name
            current_line = number
            current_has_hash = "--hash=sha256:" in stripped
            continue

        if stripped.startswith("--hash=sha256:"):
            if current_name is None:
                errors.append(f"{path}:{number}: hash sem pacote associado")
            else:
                current_has_hash = True
            continue

        # Linhas de continuação só podem conter hashes ou comentários.
        if current_name is not None and stripped == "\\":
            continue
        errors.append(f"{path}:{number}: linha não reconhecida no lock: {stripped}")

    finish_current()
    return packages, errors


def validate_pinned_base(dockerfile: Path, expected_image: str) -> list[str]:
    errors: list[str] = []
    text = dockerfile.read_text(encoding="utf-8")
    match = EXACT_FROM_RE.search(text)
    if not match:
        return [
            f"{dockerfile.relative_to(ROOT)} deve usar FROM com tag exata e digest sha256"
        ]
    if match.group("image") != expected_image:
        errors.append(
            f"{dockerfile.relative_to(ROOT)} usa {match.group('image')}, esperado {expected_image}"
        )
    return errors


def validate_python_component(component: str) -> list[str]:
    errors: list[str] = []
    folder = ROOT / component
    source = folder / "requirements.txt"
    lock = folder / "requirements.lock.txt"
    dockerfile = folder / "Dockerfile"

    for path in (source, lock, dockerfile):
        if not path.is_file():
            errors.append(f"arquivo obrigatório ausente: {path.relative_to(ROOT)}")
    if errors:
        return errors

    try:
        direct = parse_direct_requirements(source)
    except ValueError as exc:
        errors.extend(str(exc).splitlines())
        return errors

    locked, lock_errors = parse_hashed_lock(lock)
    errors.extend(lock_errors)

    for name, version in sorted(direct.items()):
        locked_version = locked.get(name)
        if locked_version is None:
            errors.append(f"{component}: {name} não aparece em requirements.lock.txt")
        elif locked_version != version:
            errors.append(
                f"{component}: {name} está em {version} no requirements.txt, "
                f"mas em {locked_version} no lock"
            )

    docker_text = dockerfile.read_text(encoding="utf-8")
    for fragment in ("requirements.lock.txt", "--require-hashes", "PIP_VERSION="):
        if fragment not in docker_text:
            errors.append(f"{component}/Dockerfile não contém {fragment!r}")

    errors.extend(validate_pinned_base(dockerfile, "python"))
    return errors


def validate_frontend() -> list[str]:
    errors: list[str] = []
    folder = ROOT / "frontend"
    package_json = folder / "package.json"
    package_lock = folder / "package-lock.json"
    npmrc = folder / ".npmrc"
    dockerfile = folder / "Dockerfile"

    for path in (package_json, package_lock, npmrc, dockerfile):
        if not path.is_file():
            errors.append(f"arquivo obrigatório ausente: {path.relative_to(ROOT)}")
    if errors:
        return errors

    package = json.loads(package_json.read_text(encoding="utf-8"))
    lock = json.loads(package_lock.read_text(encoding="utf-8"))

    if lock.get("lockfileVersion") != 3:
        errors.append("frontend/package-lock.json deve usar lockfileVersion 3")

    root_package = lock.get("packages", {}).get("", {})
    for section in ("dependencies", "devDependencies"):
        expected = package.get(section, {})
        locked = root_package.get(section, {})
        if expected != locked:
            errors.append(
                f"frontend/package-lock.json não corresponde ao package.json em {section}"
            )

    packages = lock.get("packages", {})
    for package_path, metadata in packages.items():
        if not package_path or metadata.get("link"):
            continue

        resolved = metadata.get("resolved")
        integrity = metadata.get("integrity")
        if not resolved:
            errors.append(f"frontend/package-lock.json: {package_path} sem resolved")
            continue
        if not integrity or not integrity.startswith("sha512-"):
            errors.append(f"frontend/package-lock.json: {package_path} sem integrity sha512")

        parsed = urlparse(resolved)
        host = (parsed.hostname or "").lower()
        if any(marker in host for marker in FORBIDDEN_HOST_MARKERS):
            errors.append(
                f"frontend/package-lock.json contém registry interno/não portátil: {host}"
            )
        elif host not in ALLOWED_NPM_HOSTS:
            errors.append(
                f"frontend/package-lock.json usa host não autorizado: {host or resolved}"
            )

    npmrc_text = npmrc.read_text(encoding="utf-8")
    if "registry=https://registry.npmjs.org/" not in npmrc_text:
        errors.append("frontend/.npmrc deve fixar o registry público do npm")

    docker_text = dockerfile.read_text(encoding="utf-8")
    if "npm ci" not in docker_text:
        errors.append("frontend/Dockerfile deve usar npm ci")
    if re.search(r"RUN\s+npm\s+install(?:\s|$)", docker_text):
        errors.append("frontend/Dockerfile ainda contém RUN npm install")
    if ".npmrc" not in docker_text:
        errors.append("frontend/Dockerfile deve copiar .npmrc antes do npm ci")

    errors.extend(validate_pinned_base(dockerfile, "node"))
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(validate_frontend())
    errors.extend(validate_python_component("backend"))
    errors.extend(validate_python_component("ai"))

    if errors:
        print("CHK-02: falha na validação dos locks:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("CHK-02: manifests, locks e Dockerfiles estão coerentes.")
    print("- Frontend: registry público + package-lock v3 + npm ci")
    print("- Backend: versões exatas + hashes + imagem-base fixada")
    print("- IA: versões exatas + hashes + imagem-base fixada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
