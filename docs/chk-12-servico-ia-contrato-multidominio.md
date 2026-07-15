# CHK-12 — Serviço de IA e contrato multi-domínio

**Perfil:** protótipo acadêmico e demonstrativo
**Base de aplicação:** CHK-11 já aplicada
**Domínio operacional atual:** gastrointestinal

## Resultado executivo

A checagem identificou que o serviço já possuía registro por domínio e aceitava
`exam_type`, mas o backend não enviava esse campo. Além disso, tipos ausentes ou
desconhecidos caíam silenciosamente no domínio gastrointestinal, `/health`
respondia `ok` sem confirmar os pesos, `/models` listava apenas nomes registrados
e os quatro artefatos eram carregados de forma preguiçosa somente na primeira
predição.

A CHK-12 transforma esse comportamento em um contrato explícito:

1. `exam_type` é obrigatório no multipart de `/predict`;
2. `endoscopy` e `colonoscopy` resolvem explicitamente para
   `gastrointestinal`;
3. tipo desconhecido retorna HTTP 422, sem fallback silencioso;
4. a inicialização carrega ResNet-50, EfficientNet-B4, PVTv2-B2 e o
   meta-classificador;
5. `/health` só retorna HTTP 200 quando os quatro artefatos estão carregados;
6. `/models` expõe domínio, tipos aceitos, classes, versão, dispositivo e estado
   dos artefatos;
7. a versão do modelo vem de `manifesto_modelos.json`;
8. o backend envia `exam_type`, diferencia timeout de indisponibilidade e valida
   o JSON devolvido;
9. o resultado persistido usa diretamente classe, confiança, modelo, versão e
   Grad-CAM validados pelo contrato.

## Contrato de `/health`

Quando pronto, o endpoint retorna HTTP 200 com:

```json
{
  "status": "ok",
  "ready": true,
  "device": {"type": "cpu"},
  "artifact_summary": {"expected": 4, "loaded": 4},
  "domains": {
    "gastrointestinal": {
      "active_model": "ensemble_stacking",
      "loaded": true
    }
  }
}
```

Se manifesto, peso ou meta-classificador estiver ausente/incompatível, o serviço
permanece consultável, mas `/health` retorna HTTP 503 e informa `error`.
`/predict` também retorna HTTP 503 enquanto o runtime não estiver pronto.

## Contrato de `/models`

O catálogo passa a informar, por domínio:

- modelo ativo e modelos registrados;
- tipos de exame aceitos;
- mapa de classes;
- versão lida do manifesto;
- quatro artefatos esperados, existência e estado de carregamento;
- dispositivo CPU/GPU selecionado.

Para gastrointestinal, o contrato esperado é:

| Item | Valor |
| --- | --- |
| Tipos | `endoscopy`, `colonoscopy` |
| Domínio | `gastrointestinal` |
| Modelo ativo | `ensemble_stacking` |
| Classes | `0=normal`, `1=abnormal` |
| Artefatos | `resnet50.pt`, `efficientnet_b4.pt`, `pvt_v2_b2.pt`, `meta_classificador.joblib` |
| Versão | `model_version` de `manifesto_modelos.json` |
| Grad-CAM | ResNet-50 gastrointestinal |

## Contrato de `/predict`

Entrada multipart obrigatória:

```text
file=<JPEG ou PNG>
exam_type=colonoscopy
```

Resposta mínima validada:

```json
{
  "exam_type": "colonoscopy",
  "exam_domain": "gastrointestinal",
  "prediction_class": 1,
  "label": "abnormal",
  "confidence": 0.9342,
  "model_name": "ensemble_stacking",
  "model_version": "0.1.0",
  "gradcam_available": true,
  "gradcam_path": "/app/storage/gradcam/...jpg",
  "device": "cpu"
}
```

A imagem vazia, corrompida, não JPEG/PNG ou acima do limite retorna 4xx. O
serviço valida o conteúdo real com Pillow antes de chamar os modelos.

## Cliente backend

`request_prediction()` agora envia:

```python
data={"exam_type": normalized_exam_type}
files={"file": (filename, image_bytes, content_type)}
```

Também valida:

- presença dos campos obrigatórios;
- correspondência entre `exam_type` solicitado e devolvido;
- `endoscopy/colonoscopy -> gastrointestinal`;
- classe inteira;
- confiança entre zero e um;
- modelo e versão não vazios;
- consistência entre `gradcam_available` e `gradcam_path`.

Falhas são classificadas como timeout, indisponibilidade ou erro de
resposta/contrato. O fluxo do exame continua marcando a análise como falha e
registrando auditoria quando a chamada externa não pode ser concluída.

## Persistência

O serviço de exames utiliza os valores validados para construir
`AIAnalysisCreate`:

- `prediction_label`;
- `prediction_class`;
- `confidence`;
- `model_name`;
- `model_version`;
- `gradcam_path`;
- `processing_time_ms`;
- resposta bruta para rastreabilidade interna.

A criação da análise, a transição do exame e seus logs continuam na mesma
transação, conforme CHK-11.

## CPU e GPU

O dispositivo é selecionado por `torch.cuda.is_available()`. O mesmo código
funciona em CPU ou GPU; `/health`, `/models` e `/predict` informam o dispositivo
usado. A suíte testa a decisão CPU/GPU sem exigir uma placa física e a validação
HTTP real confirma o dispositivo do ambiente executado.

## Testes

### Serviço de IA

`ai/tests/test_service_contract.py` cobre:

- tipo explícito e domínio gastrointestinal;
- rejeição de tipo ausente/desconhecido;
- seleção CPU/GPU;
- carregamento dos três modelos e meta-classificador;
- manifesto e quatro artefatos;
- imagem inválida;
- classes por domínio;
- modelo, versão, confiança e Grad-CAM;
- contratos de `/health` e `/models`.

### Backend

`backend/tests/test_ai_service_contract.py` cobre:

- envio de `exam_type` no multipart;
- timeout;
- conexão recusada/indisponibilidade;
- domínio divergente;
- Grad-CAM inconsistente;
- persistência de classe, confiança, modelo, versão e caminho do Grad-CAM.

### Validação HTTP real

O script `scripts/verify_chk12_ai_contract.sh`:

1. confirma os cinco arquivos locais — manifesto e quatro artefatos;
2. executa testes unitários do serviço e do backend;
3. sobe o container `ai`;
4. aguarda `/health` confirmar `4/4` artefatos carregados;
5. valida `/models`;
6. envia imagem inválida e tipo desconhecido;
7. executa inferência gastrointestinal real;
8. confirma modelo, versão, confiança e arquivo Grad-CAM;
9. roda a suíte completa do backend e build do frontend.

## Critério de conclusão

A CHK-12 é concluída quando o script termina com:

```text
[CHK-12] Validação concluída com sucesso.
```

Nesse ponto, um exame gastrointestinal escolhe explicitamente o domínio
`gastrointestinal`, usa o `ensemble_stacking` e persiste versão, modelo,
confiança, classe e Grad-CAM.
