# ClinicAI Frontend

Frontend oficial do projeto **ClinicAI**, desenvolvido para oferecer uma interface moderna, responsiva e profissional para clínicas, consultórios e profissionais da saúde.

Aplicação SPA construída com **React**, baseada em arquitetura escalável e preparada para integração completa com a API do sistema.

---

## Sobre o Projeto

O frontend do ClinicAI é responsável por fornecer a experiência visual e operacional do sistema, permitindo:

- Login seguro
- Navegação protegida
- Gestão administrativa
- Cadastro de pacientes
- Gestão de clínicas
- Controle de usuários
- Futuro módulo clínico
- Integração futura com IA médica

---

## Stack Utilizada

### Core

- React
- Vite
- JavaScript
- React Router DOM
- Axios

### UI / Layout

- CoreUI React Free Admin Template
- Componentização reutilizável
- Layout responsivo
- Sidebar administrativa
- Header dinâmico

### Estado / Auth

- Context API
- Persistência de sessão
- JWT Token Integration

---

## Estrutura Atual

```txt
frontend/
├── public/
│   ├── favicon.ico
│   └── assets/
│
├── src/
│   ├── assets/
│   ├── components/
│   ├── layout/
│   ├── routes/
│   ├── services/
│   ├── views/
│   ├── context/
│   ├── App.jsx
│   └── main.jsx
│
├── package.json
├── vite.config.js
└── .env
```

---

## Funcionalidades Atuais

### Autenticação

- Tela de login
- Token JWT
- Sessão autenticada
- Logout

### Administrativo

- Dashboard inicial
- Usuários
- Clínicas
- Pacientes
- Navegação lateral

### Interface

- Tema profissional
- Responsivo
- Layout administrativo moderno

---

## Como Executar Localmente

## 1. Entrar na pasta frontend

```bash
cd frontend
```

## 2. Instalar dependências

```bash
npm install
```

## 3. Configurar .env

```env
VITE_API_URL=http://localhost:8000
```

## 4. Rodar aplicação

```bash
npm run dev
```

Se o projeto estiver usando script alternativo:

```bash
npm start
```

---

## URLs Locais

| Serviço | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Vite Dev | http://localhost:5173 |

---

## Integração com Backend

A aplicação consome a API FastAPI do projeto ClinicAI:

```txt
Frontend React
     ↓
Axios Requests
     ↓
FastAPI Backend
     ↓
PostgreSQL
```

---

## Organização por Módulos

### Views

- Dashboard
- Login
- Patients
- Clinics
- Users

### Components

- Inputs reutilizáveis
- Tabelas
- Modais
- Formulários
- Alerts

### Services

- authService
- patientService
- clinicService
- userService

---

## Identidade Visual

Projeto customizado a partir do CoreUI com branding próprio:

- Nome ClinicAI
- Sidebar personalizada
- Logo própria
- Favicon próprio
- Tema institucional

---

## Roadmap Frontend

### Em andamento

- Refino UI/UX
- Melhorias de responsividade
- Padronização visual
- Feedback visual de loading/errors

### Próximos módulos

- Prontuário eletrônico
- Agenda médica
- Upload de exames
- Dashboard analítico
- IA integrada na interface

---

## IA no Frontend (Futuro)

Telas previstas:

```txt
/ai/upload-exam
/ai/results
/ai/history
```

Funcionalidades:

- Upload imagem/vídeo
- Resultado IA em tempo real
- Heatmaps / GradCAM
- Histórico por paciente

---

## Objetivo Acadêmico

Construir uma interface moderna para demonstrar no TCC a integração entre:

- Engenharia de Software
- UX/UI
- Sistemas Web
- APIs modernas
- Inteligência Artificial aplicada à saúde

---

## Desenvolvido por

**Clice Bezerra Brito Romão**