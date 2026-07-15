# Ativos acadêmicos do `academic_demo`

Este diretório contém somente os quatro arquivos necessários para a
demonstração reproduzível do ClinicAI:

- duas imagens endoscópicas provenientes do Kvasir Dataset;
- dois mapas Grad-CAM produzidos pelo `ensemble_stacking` versão `0.1.0`.

## Origem e licença

- Dataset: Kvasir Dataset
- Distribuição utilizada: `meetnagadia/kvasir-dataset`
- Fonte: `https://www.kaggle.com/datasets/meetnagadia/kvasir-dataset`
- Licença informada pelo cliente Kaggle: `ODbL-1.0`

Os nomes originais, classes de origem, hashes, dimensões lógicas e predições
selecionadas estão registrados em `manifest.json`.

## Seleção

### Exemplo normal

- classe de origem: `normal-cecum`;
- predição do ClinicAI: `normal`;
- classe numérica: `0`;
- confiança: `0.9773`.

### Exemplo abnormal

- classe de origem: `dyed-lifted-polyps`;
- predição do ClinicAI: `abnormal`;
- classe numérica: `1`;
- confiança: `0.9903`.

## Limites de uso

Os arquivos são destinados exclusivamente à demonstração acadêmica do
ClinicAI. As predições registradas demonstram o funcionamento técnico do
modelo sobre esses ativos e não constituem diagnóstico, validação clínica ou
nova medição de desempenho científico.

O modo `bootstrap` não deve criar registros nem instalar esses ativos. Eles
serão utilizados somente quando `SEED_MODE=academic_demo`.
