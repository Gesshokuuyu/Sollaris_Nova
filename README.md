# Sollaris Nova — PC Optimizer

> Aplicativo desktop em Python para monitoramento técnico, diagnóstico de gargalos e otimização segura do computador no Windows 10 e 11.

---

## 📌 Visão Geral

O **Sollaris Nova** é uma ferramenta técnica de diagnóstico e monitoramento de desempenho local. O projeto foi projetado com base em três pilares fundamentais:
1. **Medições Reais:** Informações autênticas de CPU, RAM, Armazenamento e Sensores térmicos. Zero números inventados ou pontuações universais arbitrárias.
2. **Diagnósticos Explicáveis:** Gargalos são identificados com base na persistência de múltiplas amostras, acompanhados de justificativa técnica, impacto e risco.
3. **Segurança e Transparência:** Nenhuma alteração destrutiva sem confirmação expressa e prévia. Zero telemetria remota.

---

## 📂 Navegação da Documentação e Governança

Para manter a consistência contínua do projeto, a documentação viva está estruturada em:

| Pasta / Arquivo | Descrição |
| :--- | :--- |
| [PROJECT_SPEC.md](file:///d:/GitHub/Sollaris_Nova/PROJECT_SPEC.md) | Especificação técnica mestre (Visão geral, escopo do MVP, RF-001 a RF-015, métricas e fases) |
| [docs/specs/MVP_CRITERIA.md](file:///d:/GitHub/Sollaris_Nova/docs/specs/MVP_CRITERIA.md) | Critérios de aceite e Definição de Pronto (DoD) do MVP |
| [docs/architecture/ARCHITECTURE.md](file:///d:/GitHub/Sollaris_Nova/docs/architecture/ARCHITECTURE.md) | Arquitetura em camadas desacopladas, thread de coleta em background e dataclasses imutáveis |
| [docs/standards/DESIGN_SYSTEM.md](file:///d:/GitHub/Sollaris_Nova/docs/standards/DESIGN_SYSTEM.md) | Design System (Paleta de cores `#0B0F14` / `#3B82F6`, Segoe UI, espaçamento, proibições) |
| [docs/standards/CODE_STANDARDS.md](file:///d:/GitHub/Sollaris_Nova/docs/standards/CODE_STANDARDS.md) | Padrões de código PEP 8, tipagem estática obrigatória, tratamento resiliente de erros e commits |
| [docs/changelogs/CHANGELOG.md](file:///d:/GitHub/Sollaris_Nova/docs/changelogs/CHANGELOG.md) | Histórico contínuo de alterações seguindo o padrão Keep a Changelog |
| [docs/workflow/DEVELOPMENT_AND_RELEASE_FLOW.md](file:///d:/GitHub/Sollaris_Nova/docs/workflow/DEVELOPMENT_AND_RELEASE_FLOW.md) | Fluxo Git, estratégia de branches (`main`, `lts`, `testing`, `develop`), tratamento em issues e CI/CD |
| [docs/setup/SETUP_GUIDE.md](file:///d:/GitHub/Sollaris_Nova/docs/setup/SETUP_GUIDE.md) | Guia completo de configuração de ambiente e comandos |
| [THIRD_PARTY_NOTICES.md](file:///d:/GitHub/Sollaris_Nova/THIRD_PARTY_NOTICES.md) | Atribuição de licenças de dependências de terceiros |

---

## 🏗️ Estrutura do Repositório

```
Sollaris_Nova/
├── main.py                     # Ponto de entrada (CLI e GUI)
├── run.bat / run.ps1           # Scripts de execução rápida
├── setup_env.bat / .ps1        # Scripts de setup automatizado
├── requirements.txt            # Dependências de produção
├── requirements-dev.txt        # Dependências de desenvolvimento e testes
├── PROJECT_SPEC.md             # Especificação técnica do projeto
├── README.md                   # Portal de apresentação do projeto
├── LICENSE                     # Licença MIT
├── THIRD_PARTY_NOTICES.md      # Avisos de dependências de terceiros
├── docs/                       # Documentação viva do projeto
│   ├── specs/                  # Especificações técnicas e critérios de aceite
│   ├── architecture/           # Arquitetura em camadas e concorrência
│   ├── standards/              # Design System e padrões de código
│   ├── changelogs/             # Registro formal de mudanças por versão
│   └── setup/                  # Guias de instalação e execução
├── app/                        # Camada de Interface (CustomTkinter)
│   ├── theme.py                # Tokens de cores e tipografia
│   ├── components/             # Cartões de métricas, sidebar e gráficos
│   └── pages/                  # Dashboard, Diagnóstico, Limpeza, etc.
├── core/                       # Camada de Negócio e Coleta (Headless)
│   ├── hardware.py             # Coletor de métricas de hardware e sensores
│   ├── monitor.py              # Thread assíncrona de monitoramento
│   ├── processes.py            # Coleta resiliente de processos do sistema
│   └── diagnostics.py          # Motor de detecção de gargalos
├── database/                   # Persistência local (SQLite)
├── safety/                     # Permissões, auditoria e rollback seguro
├── tests/                      # Suite de testes automatizados (pytest)
└── data/                       # Armazenamento local (.db e logs)
```

---

## 🚀 Como Executar (1 Clique / Zero-Touch)

Você **não precisa digitar comandos no terminal** nem configurar ambiente manualmente:

- **Basta dar um duplo clique em `run.bat` no Windows Explorer!**
  - O script verifica automaticamente o ambiente `.venv`.
  - Se for a primeira execução ou faltarem dependências, ele cria o ambiente com **Python 3.14** e instala tudo silenciosamente.
  - Em seguida, abre a aplicação diretamente.

- **Ou via terminal (PowerShell):**
  ```powershell
  .\run.ps1
  ```

---

## 🛠️ Diagnóstico do Ambiente e Testes (Para Desenvolvedores)
Para verificar as métricas de hardware detectadas e a integridade das bibliotecas diretamente no terminal:
```powershell
.\.venv\Scripts\python.exe main.py --check-env
```

### 4. Executar Testes Automatizados
```powershell
.\.venv\Scripts\pytest -v
```

### 5. Checar Qualidade e Padrões de Código (Ruff)
```powershell
.\.venv\Scripts\ruff check .
```

---

## 🌿 Fluxo de Branches e Tratamento de Issues

O desenvolvimento segue uma estrutura com branches permanentes e branches efêmeras de trabalho:

- **`main`**: Versão estável / produção / releases.
- **`lts`**: Versão de suporte estendido para correções críticas de segurança.
- **`testing`**: Homologação e validação pré-release.
- **`develop`**: Branch ativa de integração do desenvolvimento diário.
- **Branches de trabalho**:
  - `feature/<id>-<nome>`: Novas funcionalidades a partir de `develop`.
  - `fix/<issue-id>-<nome>`: Correções a partir de `develop`.
  - `hotfix/<versao>-<nome>`: Correções emergenciais a partir de `main`.

> **Regra Obrigatória:** Toda alteração nasce a partir de uma **Issue** no GitHub (utilizando os templates em `.github/ISSUE_TEMPLATE/`) e é integrada via **Pull Request** para a branch correta com validação contínua do GitHub Actions.

