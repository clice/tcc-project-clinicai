# Ativos Acadêmicos do `academic_demo`

Este diretório contém os ativos versionados utilizados exclusivamente na demonstração
acadêmica reproduzível do ClinicAI.

## Composição

O conjunto versionado reúne:

- 90 imagens endoscópicas de origem pública, sendo 45 com rótulo de origem `normal` e 45 com
  rótulo de origem `abnormal`;
- 72 mapas de atribuição Grad-CAM associados aos exames que possuem análise de IA;
- `manifest.json` no esquema 2, contendo tamanhos, hashes SHA-256, vínculos, resultados e
  metadados necessários à reconstrução determinística da massa.

O manifesto de ativos contempla as três clínicas ativas da demonstração, com dez pacientes e
trinta exames em cada clínica. Cada clínica recebe 15 imagens normais e 15 anormais segundo os
rótulos de origem, totalizando 30 pacientes e 90 exames entre fevereiro e julho de 2026.

A execução completa de `academic_demo` também cria uma quarta clínica inativa e contas inativas
destinadas aos cenários de bloqueio de autenticação. Esses registros administrativos não
integram o inventário de imagens do manifesto.

## Modelo e explicabilidade

As 72 análises foram executadas pelo modelo operacional:

- modelo: `ensemble_stacking`;
- versão: `0.1.2`;
- release: `models-v0.1.2`;
- protocolo: `viana_codigo_kfold3_roi_sh_da`;
- fold operacional: `1`.

Os mapas foram produzidos pelo método
`weighted_base_gradcam_oriented_by_ensemble_stacking_v1`. A visualização combina os mapas das
três arquiteturas — ResNet-50, EfficientNet-B4 e PVTv2-B2 — com pesos derivados da evidência
local utilizada pelo meta-classificador na predição correspondente.

O mapa combinado é um recurso de explicabilidade *post hoc*. Ele não constitui localização
clinicamente validada de lesões ou justificativa causal da classificação.

## Integridade

O carregamento da massa valida:

- a versão do esquema e as quantidades declaradas pelo manifesto;
- a existência de 90 exames e 72 análises;
- a unicidade das chaves e dos caminhos;
- o tamanho e o SHA-256 de cada imagem e mapa;
- os vínculos entre clínica, profissional, paciente, exame e análise;
- a ausência de caminhos operacionais absolutos no manifesto;
- a existência de 162 ativos únicos: 90 imagens e 72 mapas.

Os ativos são copiados para o armazenamento operacional sem sobrescrever silenciosamente um
arquivo divergente já existente.

## Proveniência e uso

As imagens foram selecionadas da base pública empregada no trabalho acadêmico. A procedência,
os hashes e as informações de uso estão registrados no manifesto e nos materiais do projeto.

Pacientes, profissionais, clínicas, datas e descrições da massa são fictícios e determinísticos.
Nenhum desses registros representa atendimento real.

## Limitações

A comparação entre o rótulo de origem e a predição observada nesse subconjunto não constitui
avaliação formal do modelo, validação clínica, estimativa de desempenho científico nem
alegação diagnóstica.

O manifesto atual registra um caso de divergência entre o rótulo de origem e a predição. Essa
ocorrência integra apenas o cenário demonstrativo e não deve ser interpretada como estudo de
acurácia.

## Regeneração dos mapas

O script `scripts/regenerate_demo_gradcams.py` recria os 72 mapas em uma área de *staging*. A
classificação continua utilizando a entrada quadrada e o pré-processamento compatível com o
protocolo de treinamento.

Somente a representação visual restaura a proporção original e recorta, em conjunto, a imagem
e o mapa pela maior região endoscópica contínua. Esse procedimento remove barras escuras
residuais e metadados laterais sem alterar a entrada utilizada na classificação, a classe
predita ou a confiança.

O regenerador valida classe, confiança, dimensões, tamanho e SHA-256 antes de produzir o novo
`manifest.json`. Os ativos oficiais somente devem ser substituídos após a conferência integral
do *staging*.
