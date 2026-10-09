## 📋 Descrição das Alterações

Descreva de forma clara e objetiva o que este Pull Request introduz, corrige ou aprimora.

---

## 🔗 Issue Vinculada

- Closes #
- Fixes #

---

## 🎯 Tipo de Mudança

- [ ] `feat`: Nova funcionalidade
- [ ] `fix`: Correção de bug
- [ ] `perf`: Otimização de desempenho
- [ ] `refactor`: Refatoração sem alteração de comportamento
- [ ] `docs`: Atualização de documentação / especificações
- [ ] `test`: Adição ou ajuste de testes automatizados
- [ ] `chore`: Ajustes de dependências, build ou CI

---

## 🌲 Branch de Destino

- [ ] `develop` (Para novas features e fixes cotidianos)
- [ ] `testing` (Para consolidação pré-release)
- [ ] `main` (Para releases aprovadas ou hotfixes emergenciais)
- [ ] `lts` (Para backport de patches críticos de segurança)

---

## ✅ Checklist de Qualidade (Definition of Done)

Marque todos os itens verificados antes de solicitar a revisão:

- [ ] **Issue vinculada:** O PR está atrelado a uma issue devidamente discutida e documentada.
- [ ] **Linters e Formatação:** O comando `ruff check .` foi executado e não reportou erros.
- [ ] **Testes Automatizados:** Todos os testes do `pytest` passaram localmente com código de saída 0.
- [ ] **Não-bloqueio de UI:** Nenhuma chamada demorada ao sistema operacional (`psutil`, `WMI`, disco) foi colocada na thread principal do CustomTkinter.
- [ ] **Resiliência de Sensores:** Qualquer sensor ausente retorna `SensorReading(is_available=False)` sem causar falha do aplicativo.
- [ ] **Exceções de Processos:** Chamadas a processos tratam `psutil.NoSuchProcess`, `psutil.AccessDenied` e `psutil.ZombieProcess`.
- [ ] **Privacidade e Segurança:** Nenhuma telemetria externa introduzida e nenhuma deleção de arquivo sem prévia/confirmação.
- [ ] **Documentação:** Changelog ou especificações foram atualizados caso haja alteração de comportamento.
