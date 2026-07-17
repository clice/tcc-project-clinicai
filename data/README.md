# Dados operacionais locais do ClinicAI

Esta pasta reúne os arquivos produzidos durante a execução local
do sistema.

```text
data/
├── exams/
│   └── <clinic_id>/<patient_id>/<exam_id>/original/
├── attribution/
├── predictions/
└── temporary/
```

- `exams/`: imagens originais validadas dos exames;
- `attribution/`: mapas de atribuição produzidos pela IA;
- `predictions/`: reservado para artefatos futuros;
- `temporary/`: arquivos transitórios.

O conteúdo operacional não é versionado no Git. Somente este
README permanece rastreável.

Os ativos acadêmicos permanentes continuam em
`backend/demo_assets/`.

Os volumes antigos permanecem preservados durante a migração.
Não utilize dados clínicos reais neste protótipo acadêmico.
