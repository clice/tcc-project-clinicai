# Catálogos oficiais de perfis e status

O ClinicAI trata perfis de acesso (`roles`) e status operacionais (`statuses`)
como catálogos fechados. Esses registros possuem nomes técnicos usados por
regras de autorização e de negócio; por isso, não podem ser criados ou
renomeados pela interface administrativa nem pela API pública.

## Contrato público

A API oferece somente as operações suportadas pelo produto:

| Recurso | Listagem | Consulta | Atualização parcial | Criação pública |
| --- | --- | --- | --- | --- |
| Perfis | `GET /roles/` | `GET /roles/{role_id}` | `PATCH /roles/{role_id}` | não disponível |
| Status | `GET /statuses/` | `GET /statuses/{status_id}` | `PATCH /statuses/{status_id}` | não disponível |

As atualizações aceitam apenas `display_name` e `description`. Os campos
`Role.name`, `Status.name` e `Status.applies_to` são identificadores técnicos
imutáveis. A remoção dos endpoints POST também retira da documentação OpenAPI
os schemas de criação que não pertencem ao contrato público.

## Inicialização e evolução

Na primeira instalação, `backend/app/modules/roles/seed.py` e
`backend/app/modules/statuses/seed.py` cadastram os valores oficiais. Esse
bootstrap interno não depende dos endpoints HTTP e continua disponível.

Depois que um banco entrar em uso, qualquer adição, remoção ou alteração de
identificador técnico deve ser feita por migration Alembic versionada. A
migration precisa preservar integridade referencial, definir `upgrade` e
`downgrade`, e ser acompanhada por testes. Alterações meramente descritivas
podem ser feitas pelas telas administrativas e ficam registradas na auditoria.

## Verificação antes da implantação

- Executar `pytest` no backend, incluindo
  `test_closed_configuration_catalogs.py`.
- Executar `npm run check:configuration-catalogs` no frontend.
- Abrir `/openapi.json` ou `/docs` e confirmar a ausência de `POST /roles/` e
  `POST /statuses/`.
- Confirmar que a primeira inicialização ainda cadastra os perfis e status
  oficiais pelos seeds.

Essa separação mantém o contrato da API coerente com o produto e impede que
clientes externos criem identificadores que o restante do sistema não conhece.
