# 📌 ClinicAI — Sistema Web Inteligente para Clínicas com IA Aplicada a Exames Endoscópicos

> _Projeto de Trabalho de Conclusão de Curso (TCC) voltado ao desenvolvimento de um sistema web para gestão clínica com integração futura de Inteligência Artificial para análise de exames gastrointestinais._

---

## 🧠 Objetivo Geral

Desenvolver um sistema web para clínicas e profissionais da saúde, integrando gestão administrativa com uma base tecnológica preparada para análise automatizada de exames endoscópicos utilizando técnicas de Inteligência Artificial.

---

## 🎯 Objetivos Específicos

- **Desenvolver Backend Robusto:** Criar uma API REST utilizando FastAPI com arquitetura modular e escalável.
- **Implementar Autenticação Segura:** Utilizar JWT para controle de acesso e segurança da aplicação.
- **Gerenciar Estrutura Administrativa:** Implementar controle de usuários, clínicas, pacientes, perfis e permissões.
- **Organizar Dados Clínicos:** Estruturar o sistema para suportar prontuários e exames médicos.
- **Preparar Integração com IA:** Criar base para upload e análise futura de imagens e vídeos endoscópicos.
- **Aplicar Boas Práticas de Engenharia de Software:** Utilizar separação de camadas, Docker, migrations e organização modular.

---

## 📈 Status Atual do Projeto

- **Status geral:** Em desenvolvimento  
- **Fase atual:** Finalização da base administrativa e preparação do módulo clínico  
- **Próxima etapa:** Implementação do módulo de exames e integração inicial com IA  

---

## 👩‍💻 Autoria

| Nome | Função | Contato |
|------|--------|---------|
| Luana Batista da Cruz | Orientadora | luana.batista@ufca.edu.br |
| Clice Bezerra Brito Romão | Autora | clice.romao@aluno.ufca.edu.br |

---

## 🧪 Tecnologias Utilizadas

### 🔧 Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic
- JWT Authentication

### 💻 Frontend

- React
- CoreUI React Free Admin Template
- Vite
- React Router
- Axios
- Context API

### 🧠 Inteligência Artificial (planejada)

- TensorFlow / PyTorch
- OpenCV
- Scikit-learn

### ⚙️ Infraestrutura

- Docker
- Docker Compose

---

## 🏗️ Arquitetura do Sistema

```text
Frontend (React)
        ↓
API REST (FastAPI)
        ↓
PostgreSQL
        ↓
(Módulo futuro de IA)
```

---

## 📁 Estrutura do Projeto

    tcc-project-clinicai/
    ├── backend/        -> API FastAPI e lógica de negócio
    ├── frontend/       -> Interface web React
    ├── docs/           -> Documentação técnica (arquitetura, banco, roadmap)
    ├── docker-compose.yml
    └── README.md

---

## ⚙️ Como Executar o Projeto

### 1. Clonar repositório

```bash
git clone https://github.com/clice/tcc-project-clinicai.git
cd tcc-project-clinicai
```

### 2. Configurar ambiente

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 3. Subir containers

```bash
docker compose up --build -d
```

---

## 🌐 Acesso Local

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| Documentação Backend API | http://localhost:8000/docs |
| Documentação IA API | http://localhost:8001/docs |

---

## 🧩 Módulos do Sistema

### ✔ Implementados

- Autenticação (JWT)
- Usuários
- Clínicas
- Pacientes
- Roles (Perfis)
- Permissões
- Status

### 🔄 Em desenvolvimento

- Validações avançadas
- Controle de acesso refinado
- Melhorias de interface

### 🚧 Planejados

- Prontuário eletrônico
- Exames
- Upload de imagens/vídeos
- Dashboard clínico
- Integração com IA

---

## 🧠 Inteligência Artificial no Projeto

O diferencial do ClinicAI é a integração com visão computacional para exames médicos.

### Aplicações previstas

- Classificação de imagens endoscópicas
- Detecção de anomalias
- Apoio à decisão clínica

### Técnicas previstas

- CNN (Redes Convolucionais)
- Transfer Learning
- Vision Transformers (opcional)
- Explainable AI (GradCAM)

### Métricas

- Accuracy
- Precision
- Recall
- F1-Score
- IoU (caso haja segmentação)

---

## 📊 Roadmap do Projeto

### Curto prazo

- Finalizar backend administrativo
- Revisar segurança e permissões
- Refinar frontend

### Médio prazo

- Implementar módulo de exames
- Criar upload de arquivos
- Estruturar prontuário

### Longo prazo

- Integrar Inteligência Artificial
- Implementar análise automática de exames
- Preparar deploy
- Finalizar documentação acadêmica

---

## 📚 Contribuição Acadêmica

O projeto contribui com:

- Aplicação de Engenharia de Software em sistemas reais
- Integração entre sistemas web e Inteligência Artificial
- Estruturação de dados clínicos
- Base para pesquisa em diagnóstico assistido por IA

---

## 📄 Observações

Este projeto está em desenvolvimento contínuo como parte do Trabalho de Conclusão de Curso e será evoluído progressivamente até sua versão final.

---

## 📄 Licença

Projeto acadêmico desenvolvido para fins educacionais.