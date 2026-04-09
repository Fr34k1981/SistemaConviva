# 🎨 Guia Profissional - UI/UX Sistema Conviva

## 📋 Visão Geral

O sistema foi refatorado para manter **consistência visual profissional** em toda a aplicação através de:

1. **Arquivos de Tema** (`src/styles.py`) - Paleta de cores centralizada
2. **Componentes Reutilizáveis** (`src/components.py`) - Elementos visuais prontos
3. **CSS Profissional** (em `app.py`) - Estilos base e responsividade

---

## 🎨 Paleta de Cores

### Cores Básicas
```python
from src.styles import COLORS

COLORS['primary']       # #2563eb - Azul principal
COLORS['secondary']     # #7c3aed - Roxo (ênfase)
COLORS['success']       # #10b981 - Verde
COLORS['warning']       # #f59e0b - Laranja
COLORS['danger']        # #ef4444 - Vermelho
COLORS['light']         # #f9fafb - Fundo claro
COLORS['border']        # #e5e7eb - Bordas
```

### Cores por Gravidade
```python
from src.styles import GRAVIDADE_CORES

GRAVIDADE_CORES['Leve']         # Verde
GRAVIDADE_CORES['Média']        # Laranja
GRAVIDADE_CORES['Grave']        # Laranja escuro
GRAVIDADE_CORES['Gravíssima']   # Vermelho
```

---

## 🧩 Componentes Profissionais

### 1️⃣ Cabeçalho (`render_header`)

```python
from src.components import render_header

# Simples
render_header("Título da Página")

# Completo
render_header(
    titulo="Registrar Ocorrência",
    subtitulo="Preencha os dados abaixo",
    descricao="Este formulário permite o registro de ocorrências escolares seguindo o Protocolo 179"
)
```

**Resultado:** Cabeçalho com gradiente, tipografia profissional e espaçamento.

---

### 2️⃣ Caixas de Informação (`render_info_box`)

```python
from src.components import render_info_box

# Informação
render_info_box("Conteúdo informativo", tipo="info")

# Aviso
render_info_box("Verifique os dados antes de confirmar", tipo="warning")

# Sucesso
render_info_box("Operação realizada com sucesso", tipo="success")

# Erro
render_info_box("Ocorreu um erro ao processar", tipo="error")

# Dica
render_info_box("Dica: Use Tab para navegar entre campos", tipo="tip")
```

**Tipos disponíveis:** `info`, `warning`, `success`, `error`, `tip`

---

### 3️⃣ Badges de Gravidade (`render_gravidade_badge`)

```python
from src.components import render_gravidade_badge

render_gravidade_badge("Gravíssima")
render_gravidade_badge("Grave")
render_gravidade_badge("Média")
render_gravidade_badge("Leve")
```

**Resultado:** Badges coloridas com gradiente e borda esquerda colorida.

---

### 4️⃣ Cards de Métrica (`render_metric_card`)

```python
from src.components import render_metric_card

col1, col2, col3 = st.columns(3)
with col1:
    render_metric_card("Total de Alunos", 156)

with col2:
    render_metric_card("Ocorrências", 42, delta="↑ 5 neste mês")

with col3:
    render_metric_card("Taxa de Reincidência", "8.5%", cor="danger")
```

**Cores disponíveis:** `primary`, `secondary`, `success`, `warning`, `danger`, `info`

---

### 5️⃣ Mensagens (`render_success_message`, etc)

```python
from src.components import (
    render_success_message,
    render_error_message,
    render_warning_message
)

render_success_message("✅ Ocorrência registrada com sucesso!")
render_error_message("Erro ao salvar os dados")
render_warning_message("Verifique os dados antes de confirmar")
```

---

### 6️⃣ Separadores (`render_section_divider`)

```python
from src.components import render_section_divider

st.markdown("### Seção 1")
# Conteúdo...

render_section_divider()

st.markdown("### Seção 2")
# Conteúdo...
```

---

### 7️⃣ Linha de Dados (`render_data_row`)

```python
from src.components import render_data_row

dados = {
    "Total": 156,
    "Ativo": 142,
    "Inativo": 14
}

render_data_row(dados)
```

---

### 8️⃣ Grupo de Botões (`render_button_group`)

```python
from src.components import render_button_group

def acao1():
    st.write("Ação 1 executada")

def acao2():
    st.write("Ação 2 executada")

render_button_group({
    "Cancelar": lambda: st.session_state.clear(),
    "Confirmar": acao1,
    "Salvar": acao2
})
```

---

## 📝 Exemplo Completo

```python
from src.components import (
    render_header,
    render_info_box,
    render_gravidade_badge,
    render_section_divider,
    render_success_message
)

# Cabeçalho
render_header(
    titulo="Registrar Ocorrência",
    subtitulo="Preenchimento de dados",
    descricao="Complete o formulário com todas as informações necessárias"
)

# Info box
render_info_box(
    "Selecione pelo menos um aluno",
    tipo="info"
)

# Seção de seleção
st.markdown("### Dados da Ocorrência")

col1, col2 = st.columns(2)
with col1:
    aluno = st.selectbox("Aluno", ["João", "Maria", "Pedro"])
with col2:
    turma = st.selectbox("Turma", ["1º A", "2º B", "3º C"])

# Separador
render_section_divider()

# Gravidade
st.markdown("### Gravidade")
gravidade = st.radio("Selecione", ["Leve", "Média", "Grave", "Gravíssima"], horizontal=True)
render_gravidade_badge(gravidade)

# Separador
render_section_divider()

# Botão
if st.button("Salvar Ocorrência", use_container_width=True):
    render_success_message("Ocorrência registrada com sucesso!")
    st.balloons()
```

---

## 🎯 Boas Práticas

### ✅ FAÇA:

```python
# Use componentes profissionais
render_header("Título")
render_info_box("Mensagem", tipo="info")
render_gravidade_badge("Grave")

# Use cores consistentes
from src.styles import COLORS
color = COLORS['primary']

# Use espaçamento padronizado
render_section_divider()

# Agrupe elementos logicamente
with st.columns(3):
    render_metric_card("Label 1", 100)
    render_metric_card("Label 2", 200)
    render_metric_card("Label 3", 300)
```

### ❌ EVITE:

```python
# Não misture estilos velhos e novos
st.success("❌ Sucesso!")  # ❌ Antigo
render_success_message("✅ Sucesso!")  # ✅ Novo

# Não use emojis em excesso
st.title("📝📋🎯 Meu Título")  # ❌ Muitos emojis
st.title("Meu Título")  # ✅ Limpo

# Não crie cores hardcoded
st.markdown(f'<div style="color: #xyz">...')  # ❌
from src.styles import COLORS  # ✅
st.markdown(f'<div style="color: {COLORS["primary"]}>...')

# Não misture múltiplos tipos de alertas
st.info("...")
st.warning("...")
st.error("...")
st.success("...")
# Use componentes em excesso
```

---

## 🔄 Migração de Código Antigo

### Antes
```python
st.success("✅ Operação realizada com sucesso!")
st.warning("⚠️ Verifique os dados")
st.error("❌ Erro ao salvar")
```

### Depois
```python
from src.components import (
    render_success_message,
    render_warning_message,
    render_error_message
)

render_success_message("Operação realizada com sucesso")
render_warning_message("Verifique os dados")
render_error_message("Erro ao salvar")
```

---

## 🎨 Customização

### Adicionar nova cor

Edite `src/styles.py`:

```python
COLORS = {
    "primary": "#2563eb",
    # ... cores existentes ...
    "custom": "#your-hex-color"  # Nova cor
}
```

### Adicionar novo componente

Adicione função em `src/components.py`:

```python
def render_custom_component(param1: str, param2: int):
    """Descrição do componente"""
    st.markdown(f"""
    <div style="...">
        {param1} - {param2}
    </div>
    """, unsafe_allow_html=True)
```

---

## 📊 Exemplo de Página Profissional Completa

Veja o arquivo atualizado em `app.py` na seção "🏠 Início" para um exemplo da aplicação destes componentes.

---

**✨ Sistema profissional e consistente em toda a aplicação!**
