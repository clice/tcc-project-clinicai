from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("download_models", RAIZ / "scripts" / "download_models.py")
download_models = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(download_models)


class DistribuicaoModelosTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temp.name)
        self.release = self.raiz / "release"
        self.destino = self.raiz / "destino"
        self.release.mkdir()
        artefatos = []
        for nome in sorted(download_models.ARTEFATOS_OBRIGATORIOS):
            conteudo = f"conteudo-de-teste-{nome}".encode()
            (self.release / nome).write_bytes(conteudo)
            artefatos.append({
                "name": nome,
                "size_bytes": len(conteudo),
                "sha256": hashlib.sha256(conteudo).hexdigest(),
            })
        manifesto = {
            "schema_version": 1,
            "release_tag": "models-teste",
            "model_version": "teste",
            "domain": "gastrointestinal",
            "artifacts": artefatos,
        }
        (self.release / "manifesto_modelos.json").write_text(json.dumps(manifesto), encoding="utf-8")
        handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(
            *args, directory=str(self.release), **kwargs
        )
        self.servidor = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.servidor.shutdown()
        self.servidor.server_close()
        self.thread.join()
        self.temp.cleanup()

    def _ambiente(self) -> dict[str, str]:
        return {
            "MODEL_RELEASE_REPOSITORY": "clice/tcc-project-clinicai",
            "MODEL_RELEASE_TAG": "models-teste",
            "MODEL_RELEASE_MANIFEST": "manifesto_modelos.json",
            "MODEL_RELEASE_BASE_URL": f"http://127.0.0.1:{self.servidor.server_port}",
            "MODEL_DESTINATION_DIR": str(self.destino),
        }

    def test_baixa_e_verifica_todos_os_artefatos(self) -> None:
        with patch.dict(os.environ, self._ambiente(), clear=True):
            download_models.baixar_modelos()
        for nome in download_models.ARTEFATOS_OBRIGATORIOS:
            self.assertEqual((self.destino / nome).read_bytes(), (self.release / nome).read_bytes())

    def test_segunda_execucao_reaproveita_artefatos_validos(self) -> None:
        with patch.dict(os.environ, self._ambiente(), clear=True):
            download_models.baixar_modelos()

        conteudo_inicial = {
            nome: (self.destino / nome).read_bytes()
            for nome in download_models.ARTEFATOS_OBRIGATORIOS
        }
        baixar_original = download_models._baixar
        urls_baixadas: list[str] = []

        def registrar_download(url: str, destino: Path) -> None:
            urls_baixadas.append(url)
            baixar_original(url, destino)

        with patch.dict(os.environ, self._ambiente(), clear=True):
            with patch.object(download_models, "_baixar", side_effect=registrar_download):
                download_models.baixar_modelos()

        self.assertEqual(len(urls_baixadas), 1)
        self.assertTrue(urls_baixadas[0].endswith("/manifesto_modelos.json"))
        for nome, conteudo in conteudo_inicial.items():
            self.assertEqual((self.destino / nome).read_bytes(), conteudo)

    def test_rejeita_artefato_com_conteudo_adulterado(self) -> None:
        self.destino.mkdir()
        for nome in download_models.ARTEFATOS_OBRIGATORIOS:
            (self.destino / nome).write_bytes(f"versao-anterior-{nome}".encode())
        (self.destino / "manifesto_modelos.json").write_text(
            '{"release_tag": "versao-anterior"}', encoding="utf-8"
        )
        conteudo_anterior = {
            caminho.name: caminho.read_bytes()
            for caminho in self.destino.iterdir()
            if caminho.is_file()
        }

        (self.release / "resnet50.pt").write_bytes(b"conteudo-adulterado")
        with patch.dict(os.environ, self._ambiente(), clear=True):
            with self.assertRaises(download_models.ErroDownload):
                download_models.baixar_modelos()

        conteudo_depois_da_falha = {
            caminho.name: caminho.read_bytes()
            for caminho in self.destino.iterdir()
            if caminho.is_file()
        }
        self.assertEqual(conteudo_depois_da_falha, conteudo_anterior)
        self.assertFalse(any(self.destino.parent.glob(".destino-staging-*")))
        self.assertFalse(any(self.destino.parent.glob(".destino-backup-*")))


if __name__ == "__main__":
    unittest.main()
