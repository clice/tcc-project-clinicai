"""
Pacote de domínios clínicos do ClinicAI.

Cada arquivo neste pacote representa um domínio de exame (gastrointestinal,
e futuramente outros como tomografia de cabeça ou mamografia) e registra
seus próprios modelos. Importar este pacote (feito uma vez, em
`app.main`, na subida do serviço) executa todos os módulos abaixo e
popula o registro central (`app.inference.registry`).

Para adicionar um domínio novo, ver `README.md` nesta pasta.
"""

from app.inference.domains import gastrointestinal  # noqa: F401

# Novo domínio? Importe o módulo aqui também, do mesmo jeito:
# from app.inference.domains import head_ct  # noqa: F401
# from app.inference.domains import mammography  # noqa: F401
