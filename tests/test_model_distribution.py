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

    def test_rejeita_artefato_com_conteudo_adulterado(self) -> None:
        (self.release / "resnet50.pt").write_bytes(b"conteudo-adulterado")
        with patch.dict(os.environ, self._ambiente(), clear=True):
            with self.assertRaises(download_models.ErroDownload):
                download_models.baixar_modelos()
        self.assertFalse((self.destino / "resnet50.pt").exists())


if __name__ == "__main__":
    unittest.main()

