# Ajustes recomendados na monografia — RF31, RF34 e RF36

## Inconsistência identificada

A Seção 4.3.3 já define o Funcionário da Clínica como perfil administrativo sem acesso a exames, arquivos ou resultados da IA. Entretanto, a Tabela de Casos de Uso associa o UC08 “Consultar e baixar exames” aos atores MED e FNC e o vincula a RF31, RF34 e RF36.

A implementação e a matriz padrão de RBAC adotam a política abaixo:

- **Administrador Master:** pode consultar exames e arquivos para supervisão do sistema, respeitando que não pode realizar revisão médica;
- **Médico:** pode consultar, baixar e visualizar o histórico dos exames dentro de seu escopo;
- **Funcionário da Clínica:** não recebe permissões de exames ou análise de IA na matriz padrão.

## Correção da Tabela de Casos de Uso

Substituir a linha atual do UC08 por:

| ID | Nome | Atores | Requisitos |
| --- | --- | --- | --- |
| UC08 | Consultar, baixar e acompanhar histórico de exames | ADM, MED | RF31, RF34, RF36 |

O ADM aparece por sua função de supervisão técnica e administrativa. A revisão do resultado continua exclusiva do MED no UC09.

## Redação recomendada para os requisitos

### RF31 — Consultar exames

> Permitir a listagem, busca, filtragem e visualização detalhada dos exames por usuários autorizados. O Médico acessa somente os exames permitidos por seu vínculo e escopo clínico; o Administrador Master pode consultá-los para supervisão do sistema. O Funcionário da Clínica não possui acesso ao módulo de exames na configuração padrão.

### RF34 — Baixar arquivo do exame

> Permitir o download da imagem ou dos arquivos associados ao exame somente para usuários autorizados e dentro do escopo validado pelo backend. Na configuração padrão, a operação é disponibilizada ao Médico e ao Administrador Master, não ao Funcionário da Clínica.

### RF36 — Consultar histórico do exame

> Permitir a visualização cronológica das alterações de status e dos eventos associados ao exame por usuários autorizados a consultar o próprio exame. O histórico utiliza o mesmo escopo de acesso do exame e não expõe metadados operacionais restritos, como endereço IP ou user-agent.

## Ajuste sugerido na Seção 4.3.3

A expressão “reservados exclusivamente ao médico responsável” entra em tensão com a descrição do Administrador Master na Seção 4.3.1, que acompanha o processamento dos exames. Uma redação mais fiel ao protótipo é:

> Seu escopo de atuação é deliberadamente restrito às atividades organizacionais, sem acesso aos exames, arquivos ou resultados individuais gerados pela IA. Essas informações são disponibilizadas ao médico dentro de seu escopo clínico e ao Administrador Master apenas para supervisão técnica e administrativa do sistema. A revisão clínica e a validação do resultado permanecem exclusivas do médico responsável.

## Correspondência com a implementação

| Requisito | Backend | Frontend | Perfis padrão |
| --- | --- | --- | --- |
| RF31 | `GET /exams/`, `GET /exams/{id}`, `exams:read` + escopo | Lista, filtros e detalhes | ADM e MED |
| RF34 | `GET /exams/{id}/download`, `exams:download` + escopo | Ação de download por permissão | ADM e MED |
| RF36 | `GET /exams/{id}/history`, `exams:read` + escopo | Cartão “Histórico do Exame” | ADM e MED |

Essas alterações ajustam o documento ao estado real sem ampliar a complexidade do protótipo acadêmico.
