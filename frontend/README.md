# ClinicAI Frontend

Interface web do ClinicAI, desenvolvida em React para operar os recursos administrativos e o fluxo acadêmico de exames integrado à API principal.

## Escopo implementado

- autenticação com tokens de acesso e atualização;
- atualização da sessão e encerramento de acesso;
- dashboard acadêmico;
- gestão de usuários, clínicas, pacientes, perfis, permissões e status;
- consulta de logs de auditoria;
- cadastro, listagem, detalhamento e download de exames;
- envio de exames para análise da IA;
- acompanhamento dos estados de processamento;
- visualização do resultado, da confiança e do mapa Grad-CAM;
- revisão médica, confirmação ou registro de divergência;
- cancelamento e restauração conforme as permissões do usuário;
- controle de menus, rotas e ações conforme RBAC e escopo institucional;
- edição do perfil e troca de senha.

O frontend melhora a experiência de navegação, mas não é a fonte autoritativa de segurança. Todas as operações protegidas também são autorizadas pelo backend.

## Tecnologias

- React e JavaScript;
- Vite;
- React Router;
- Axios;
- Context API;
- CoreUI React.

## Organização

```text
frontend/
├── public/               # arquivos públicos
├── src/
│   ├── assets/           # identidade visual
│   ├── components/       # componentes reutilizáveis
│   ├── context/          # autenticação e estado compartilhado
│   ├── layout/           # estrutura visual autenticada
│   ├── routes/           # rotas e proteção de acesso
│   ├── services/         # comunicação com a API
│   └── views/            # telas dos módulos
├── package.json
├── vite.config.js
└── README.md
```

## Configuração local

A execução integrada por Docker Compose é a forma recomendada. A partir da raiz do repositório:

```bash
cp frontend/.env.example frontend/.env
docker compose up --build -d frontend
```

O frontend fica disponível em <http://localhost:3000>.

Para executar diretamente com Node.js:

```bash
cd frontend
npm ci
cp .env.example .env
npm start
```

O arquivo `.env` deve definir a URL da API conforme o exemplo versionado. Não grave credenciais ou segredos nesse arquivo; variáveis `VITE_*` são incorporadas ao código entregue ao navegador.

## Verificação

```bash
docker compose run --rm --no-deps frontend npm run lint
docker compose run --rm --no-deps frontend npm run build
```

O primeiro comando executa a análise estática com ESLint. O segundo gera o pacote de produção com Vite.

## Integração

```text
Frontend React
      ↓
API FastAPI principal
      ↓
PostgreSQL e serviço de IA
```

As requisições autenticadas são centralizadas nos serviços do frontend. Alterações de permissão são refletidas pela atualização de `/auth/me`; mesmo antes da atualização visual, o backend recusa ações fora do escopo.

## Identidade visual

A interface foi adaptada a partir do CoreUI com marca, logotipo, favicon, tema institucional e componentes próprios do ClinicAI.

## Limites do protótipo

O frontend demonstra o escopo definido para o TCC e não implementa um prontuário eletrônico completo, agenda médica, faturamento ou uso clínico em produção. Sua conclusão técnica não equivale a validação clínica, certificação de segurança ou avaliação formal de usabilidade.

## Autoria

Desenvolvido por **Clice Bezerra Brito Romão**.
