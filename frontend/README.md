# ClinicAI Frontend

Interface web do ClinicAI, desenvolvida em React para operar os módulos administrativos e o
fluxo acadêmico de exames integrado à API principal.

## Finalidade

O frontend apresenta os recursos do sistema e adapta menus, rotas e ações ao papel e às
permissões do usuário.

O backend continua sendo a fonte autoritativa de segurança. A ausência ou presença de um botão
na interface não concede nem substitui autorização da API.

## Escopo implementado

- autenticação com *access token* e *refresh token*;
- renovação da sessão e encerramento de acesso;
- edição do perfil e troca de senha;
- dashboard com cards de resumo e navegação para as listagens correspondentes;
- gestão de usuários, clínicas, pacientes, perfis, permissões e status;
- consulta de registros de auditoria pelo perfil autorizado;
- cadastro, listagem e detalhamento de exames;
- upload e download autenticado de imagens;
- envio do exame ao serviço de IA;
- acompanhamento dos estados do processamento;
- visualização da classe, da confiança e do mapa Grad-CAM pelo médico autorizado;
- exibição do rótulo da IA nas listagens médicas em estados compatíveis;
- revisão médica com confirmação ou divergência;
- cancelamento e restauração conforme as permissões;
- geração do relatório final em PDF nos fluxos autorizados;
- feedback visual padronizado para sucesso, erro e confirmação.

## Perfis na interface

### Administrador Master

Acessa os módulos estruturais e administrativos previstos, como clínicas, usuários, perfis,
permissões, status e auditoria.

O papel não utiliza o privilégio administrativo para acessar resultados clínicos da IA ou a
tela detalhada de revisão médica.

### Gestor de clínica

Opera usuários e pacientes da própria clínica e visualiza a listagem operacional de exames.

O gestor não recebe o resultado da IA na listagem nem acessa a tela clínica detalhada. Pode
gerar o relatório PDF de exame concluído da própria clínica quando a autorização específica do
backend for atendida.

### Médico

Opera pacientes e exames sob sua responsabilidade, consulta o resultado da IA, visualiza o
Grad-CAM, realiza a revisão e gera o relatório final nos estados permitidos.

## Tecnologias

- React 19;
- JavaScript;
- Vite;
- React Router com `HashRouter`;
- Axios;
- CoreUI React;
- Context API;
- Redux e React Redux;
- Chart.js;
- ESLint.

O Redux é utilizado principalmente para o estado global de exibição da barra lateral. A
autenticação e as mensagens de feedback são mantidas em `AuthContext` e `FeedbackContext`.

## Organização

```text
frontend/
├── public/                  # favicon e arquivos públicos
├── src/
│   ├── assets/              # identidade visual e recursos estáticos
│   ├── components/
│   │   ├── auth/            # proteção de rotas
│   │   ├── layout/          # cabeçalho, sidebar, conteúdo e rodapé
│   │   ├── navigation/      # navegação e breadcrumbs
│   │   └── shared/          # tabelas, ações, abas e componentes reutilizáveis
│   ├── contexts/            # autenticação e feedback
│   ├── hooks/               # hooks reutilizáveis
│   ├── layout/              # composição do layout autenticado
│   ├── services/            # comunicação com a API
│   ├── utils/               # permissões, tokens, status e constantes
│   ├── views/               # telas dos módulos
│   ├── App.jsx              # providers e roteamento principal
│   ├── routes.js            # catálogo de rotas protegidas
│   └── store.js             # estado global da interface
├── .env.example
├── package.json
├── vite.config.js
└── README.md
```

## Roteamento e autorização visual

`App.jsx` utiliza:

- `AuthProvider`;
- `FeedbackProvider`;
- `HashRouter`;
- `PublicRoute` para o login;
- `PrivateRoute` para a área autenticada.

O catálogo `routes.js` associa rotas a papéis e, quando necessário, a permissões. Quando uma
rota declara ambos, as restrições são aplicadas em conjunto.

Mesmo que uma sessão mantenha temporariamente uma rota visível, o backend recusa a operação
quando a permissão foi removida.

## Configuração local

A execução integrada é recomendada:

```bash
cp frontend/.env.example frontend/.env
docker compose up --build -d frontend
```

O frontend fica disponível em:

```text
http://localhost:3000
```

Para executar diretamente:

```bash
cd frontend
cp .env.example .env
npm ci
npm start
```

A variável principal de integração é:

```dotenv
VITE_API_URL=http://localhost:8000
```

Não armazene segredos em variáveis `VITE_*`, pois elas são incorporadas ao código entregue ao
navegador.

## Sessão e atualização de permissões

O contexto de autenticação consulta `/auth/me` para atualizar o usuário e suas permissões,
inclusive:

- ao recuperar o foco;
- ao voltar a ficar visível;
- periodicamente durante a sessão.

As chaves de armazenamento local são configuradas no `.env`. O uso atual é adequado à
demonstração acadêmica, mas uma implantação pública exigiria revisão específica do modelo de
ameaças e da proteção contra XSS.

## Identidade visual

A interface foi adaptada a partir do CoreUI com:

- marca e logotipo do ClinicAI;
- favicon próprio;
- tema claro institucional;
- componentes compartilhados;
- tabelas e ações padronizadas;
- estados de foco e navegação por teclado nos elementos interativos atualizados.

## Verificação

```bash
docker compose run --rm --no-deps frontend npm run lint
docker compose run --rm --no-deps frontend npm run build
```

O primeiro comando executa o ESLint. O segundo gera o pacote de produção com Vite.

## Integração

```text
Frontend React
      ↓
Backend FastAPI
      ├── PostgreSQL
      └── Serviço de IA
```

As requisições autenticadas são centralizadas nos serviços do frontend. Resultados clínicos,
imagens e mapas não são publicados como arquivos estáticos.

## Limites do protótipo

O frontend demonstra o escopo definido para o TCC e não implementa prontuário eletrônico
completo, agenda médica, faturamento ou uso clínico em produção.

A conclusão técnica não equivale a validação clínica, certificação de segurança ou avaliação
formal de usabilidade com profissionais e pacientes.

## Autoria

Desenvolvido por **Clice Bezerra Brito Romão** como parte do ClinicAI.
