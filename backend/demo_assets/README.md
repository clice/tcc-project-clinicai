# Ativos acadêmicos do `academic_demo`

Este diretório contém os ativos versionados usados exclusivamente na
demonstração acadêmica reproduzível do ClinicAI.

## Composição

- 90 imagens endoscópicas de origem pública: 45 classificadas na origem como
  normais e 45 como anormais;
- 72 mapas de atribuição Grad-CAM gerados para os exames analisados pela IA;
- `manifest.json` no esquema 2, com os hashes SHA-256, tamanhos, vínculos e
  resultados necessários à reconstrução determinística da massa.

A massa cria três clínicas, com dez pacientes e trinta exames em cada clínica.
Cada clínica recebe 15 imagens normais e 15 anormais, totalizando 30 pacientes
e 90 exames entre fevereiro e julho de 2026.

## Modelo e explicabilidade

As 72 análises foram executadas pelo modelo operacional
`ensemble_stacking` versão `0.1.1`, release `models-v0.1.1`, usando o fold
operacional 3 do protocolo `viana_codigo_kfold3_roi_sh_da`.

Os mapas de atribuição foram produzidos pelo método
`weighted_base_gradcam_oriented_by_ensemble_stacking_v1`. O manifesto mantém
somente metadados seguros e caminhos relativos aos ativos versionados.

## Integridade

O carregamento da massa valida:

- o esquema e as quantidades declaradas pelo manifesto;
- a unicidade das chaves e dos caminhos;
- o tamanho e o SHA-256 de cada imagem e mapa Grad-CAM;
- os vínculos entre clínica, profissional, paciente, exame e análise;
- a inexistência de caminhos operacionais locais no manifesto.

Os ativos são copiados para o armazenamento de exames sem sobrescrever
silenciosamente arquivos divergentes já existentes.

## Proveniência e uso

As imagens foram selecionadas da base pública usada no trabalho acadêmico e
são mantidas apenas para demonstração técnica e reprodutibilidade. Antes da
redistribuição, devem ser observados os termos e a licença da base original.

Os pacientes, profissionais, clínicas, datas e descrições da massa são
fictícios e determinísticos. Nenhum desses registros representa atendimento
real.

## Limitações

A concordância entre o rótulo de origem e a predição observada neste conjunto
selecionado não constitui avaliação formal do modelo, validação clínica,
estimativa de desempenho científico nem alegação diagnóstica. Trata-se apenas
de um subconjunto demonstrativo escolhido para exercitar os fluxos do sistema,
inclusive dois casos reais de divergência entre origem e predição.

## Regeneração dos mapas

O script `scripts/regenerate_demo_gradcams.py` recria os 72 mapas em uma
área de staging. A classificação continua usando a entrada quadrada e o
pré-processamento replicado de Viana. Somente a representação visual restaura
a proporção original e recorta, em conjunto, a imagem e o mapa pela maior
região endoscópica contínua. Dessa forma, barras escuras residuais e metadados
laterais são removidos sem alterar a entrada, a classe ou a confiança do
modelo.

O regenerador valida classe, confiança, dimensões, tamanho e SHA-256 antes
de produzir o novo `manifest.json`. Os arquivos oficiais somente devem ser
substituídos após a conferência completa do staging.
