# Validação estrita dos payloads da API

O backend do ClinicAI rejeita campos que não estejam declarados nos schemas de
entrada. A regra foi adotada no RBAC-08 para impedir que um cliente envie um
campo imutável ou incorreto e receba uma resposta de sucesso apesar de o valor
ter sido silenciosamente ignorado.

## Implementação

O modelo `app.common.schemas.StrictRequestModel` configura o Pydantic com
`extra="forbid"`. Todos os modelos utilizados como corpo de requisição herdam
desse modelo, incluindo operações de criação, atualização parcial,
sincronização de permissões, troca de senha, refresh token e revisão médica.

Os schemas de resposta continuam herdando diretamente de `BaseModel`, pois a
regra tem como objetivo validar dados recebidos pela API.

## Contrato de erro

Um campo desconhecido produz HTTP 422 antes da execução da regra de negócio. O
erro identifica o corpo da requisição, o nome do campo e o tipo
`extra_forbidden`. Exemplo simplificado:

```json
{
  "detail": [
    {
      "type": "extra_forbidden",
      "loc": ["body", "module"],
      "msg": "Extra inputs are not permitted"
    }
  ]
}
```

Assim, enviar `module` para `PermissionUpdate`, `name` para `RoleUpdate` ou
`StatusUpdate`, ou `role_id` para `RolePermissionSyncRequest` não é aceito.

## Regra para novos endpoints

Todo novo schema usado como corpo JSON deve herdar de `StrictRequestModel`,
diretamente ou por meio de outro modelo de entrada. O teste
`backend/tests/test_strict_request_schemas.py` mantém o inventário dos modelos
atuais, valida a configuração, verifica os campos imutáveis do RBAC-08 e testa
o retorno HTTP 422 do FastAPI.
