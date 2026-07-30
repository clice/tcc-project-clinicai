# Dados Operacionais Locais

Esta pasta recebe os arquivos produzidos durante a execução local do sistema. Ela é montada no
container do backend como `/clinicai-data`.

## Estrutura canônica

```text
data/
└── exams/
    └── <clinic_id>/
        └── <patient_id>/
            └── <exam_id>/
                ├── original/
                │   └── <arquivo-validado>.jpg|png
                └── attribution/
                    └── <mapa-gradcam>.jpg|png
```

- `original/`: imagem original do exame, validada e persistida pelo backend;
- `attribution/`: mapa de atribuição retornado pelo serviço de IA e validado pelo backend.

Os nomes físicos são gerados pela aplicação. Os caminhos persistidos no banco são relativos à
raiz operacional, e o acesso ocorre apenas por rotas autenticadas da API.

## Segurança do armazenamento

O backend valida, entre outros pontos:

- tamanho máximo;
- formato e assinatura real de JPEG ou PNG;
- dimensões e quantidade de pixels;
- integridade estrutural básica da imagem;
- vínculo entre clínica, paciente e exame;
- resolução segura do caminho;
- ausência de travessia de diretórios e de links simbólicos;
- hash SHA-256 do mapa recebido do serviço de IA.

## Versionamento

O conteúdo operacional de `data/` não deve ser versionado no Git. Somente este README permanece
rastreável.

Os ativos permanentes da demonstração acadêmica ficam em `backend/demo_assets/`. Durante o
`academic_demo`, cópias desses ativos são instaladas na hierarquia operacional descrita acima.

Não utilize dados clínicos reais neste protótipo acadêmico.
