# Design System e Identidade Visual (Sollaris Nova)

Este guia documenta o sistema de design, a paleta técnica de cores, os componentes e os princípios de interface para o **PC Optimizer (Sollaris Nova)**.

---

## 1. Filosofia Visual

O aplicativo foi projetado para transmitir a seriedade de uma ferramenta técnica de diagnóstico de engenharia, com visual moderno, focado e funcional.

### 1.1 O que EVITAR rigorosamente:
- ❌ **Gradientes intensos ou coloridos.**
- ❌ **Efeitos de brilho e neon.**
- ❌ **Sombras exageradas e efeitos 3D falsos.**
- ❌ **Cartões excessivamente arredondados (estilo mobile infantil).**
- ❌ **Emojis como ícones estruturais primários da interface.**
- ❌ **Animações decorativas que atrasem a visualização de dados.**
- ❌ **Pontuações fictícias de saúde do PC ("Health: 98%") sem fórmula transparente.**
- ❌ **Banners promocionais ou telas de cadastro/login.**

---

## 2. Paleta de Cores Oficial

A paleta de cores combina tons de azul técnico e superfícies pretas/grafite profundas:

| Token | Código Hex | Papel no Layout |
| :--- | :--- | :--- |
| `COLOR_BG_MAIN` | `#0B0F14` | Plano de fundo principal da área de conteúdo |
| `COLOR_BG_SIDEBAR` | `#0E141C` | Fundo do menu lateral de navegação |
| `COLOR_BG_SURFACE` | `#111923` | Superfície de cartões métricos, painéis e caixas |
| `COLOR_BORDER` | `#263345` | Bordas discretas de 1px entre componentes |
| `COLOR_ACCENT_BLUE` | `#3B82F6` | Azul principal: botões primários, indicador ativo, foco |
| `COLOR_ACCENT_LIGHT`| `#60A5FA` | Azul claro: hover sutil e destaques secundários |
| `COLOR_TEXT_PRIMARY`| `#DCE6F1` | Texto primário: valores numéricos e títulos principais |
| `COLOR_TEXT_MUTED`  | `#8493A7` | Texto atenuado: rótulos, unidades (`GB`, `MB/s`, `%`), rodapé |
| `COLOR_STATUS_OK`   | `#4FBF8A` | Verde técnico: métricas normais, sensores operantes |
| `COLOR_STATUS_WARN` | `#EAB308` | Amarelo de atenção: limiares moderados de alerta |
| `COLOR_STATUS_ERROR`| `#EF4444` | Vermelho de alerta: gargalo crítico ou erro de sensor |

---

## 3. Tipografia e Escalas

- **Família Tipográfica:** `Segoe UI` (fonte nativa do Windows 10 e 11). Em caso de indisponibilidade, fallback para `sans-serif`.
- **Tamanhos e Pesos:**
  - **Título de Seção:** 20px, Bold (Segoe UI)
  - **Subtítulo / Cabeçalho de Cartão:** 13px, Semi-Bold, Texto Muted (`#8493A7`)
  - **Valor Numérico em Destaque:** 26px a 32px, Bold, Texto Primário (`#DCE6F1`)
  - **Corpo / Rótulos:** 12px a 13px, Regular, Texto Muted / Primário
  - **Legendas e Rodapé:** 11px, Regular, Texto Muted

---

## 4. Espaçamento e Geometria

- **Grid de Espaçamento Base:** múltiplos de 4px, com foco em:
  - `8px`: espaçamento interno compacto (padding entre linhas e chips)
  - `12px`: espaçamento entre elementos correlatos
  - `16px`: padding padrão de cartões e distância entre colunas
  - `24px`: espaçamento de seções principais
- **Raio de Borda (Corner Radius):**
  - Janelas e painéis: `6px` a `8px` (cantos sutis e elegantes)
  - Botões e tags: `4px` a `6px`
- **Largura de Borda:** `1px` em `COLOR_BORDER` (`#263345`).

---

## 5. Janela Principal e Layout

- **Largura Inicial Recomendada:** `1180px`
- **Altura Inicial Recomendada:** `760px`
- **Largura Mínima:** `960px`
- **Altura Mínima:** `640px`
- **Menu Lateral:** Largura fixa de `220px` com alinhamento vertical à esquerda.
- **Área de Conteúdo:** Ocupa todo o espaço restante à direita com preenchimento responsivo (`grid` ou `pack` com expansão).
