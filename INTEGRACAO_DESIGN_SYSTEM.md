"""
GUIA DE INTEGRAÇÃO - DESIGN SYSTEM NA APLICAÇÃO
Como usar os componentes padronizados no app.py
"""

# ===== PASSO 1: IMPORTAÇÕES =====
# No topo de app.py, adicionar:
from src.design_system import (
    COLORS, TYPOGRAPHY, SPACING, ICONS, GRAVIDADE_CORES,
    SIZES, get_typography_css, get_color, get_gravidade_styling
)
from src.ui_components import (
    render_header_page, render_card, render_section, render_badge,
    render_success_message, render_error_message, render_warning_message,
    render_info_message, render_divider, render_stat_card,
    render_button, render_label, apply_global_style, render_modal_container
)

# ===== PASSO 2: APLICAR ESTILOS GLOBAIS =====
# No início da função main():
def main():
    apply_global_style()  # Aplicar CSS global
    
    st.set_page_config(
        page_title="Sistema Conviva",
        page_icon=ICONS["home"],
        layout="wide"
    )

# ===== PASSO 3: USO DOS COMPONENTES =====

# ===== HEADER DE PÁGINA =====
# Antes: st.title("Home")
# Depois:
render_header_page(
    title="Home",
    subtitle="Bem-vindo ao Sistema Conviva",
    icon=ICONS["home"]
)

# ===== SEÇÕES =====
render_section(
    title="Registro de Ocorrências",
    icon=ICONS["registro"]
)

# ===== CARDS COM INFORMAÇÕES =====
render_card(
    title="Informação Importante",
    content="Esta é uma mensagem importante para o usuário.",
    icon=ICONS["info"],
    variant="info"
)

# ===== MENSAGENS PADRONIZADAS =====
render_success_message(
    title="Ocorrência Registrada",
    message="A ocorrência foi registrada com sucesso!"
)

render_error_message(
    title="Erro ao Registrar",
    message="Houve um erro ao salvar a ocorrência. Tente novamente."
)

render_warning_message(
    title="Atenção",
    message="Verifique se todos os campos estão preenchidos corretamente."
)

render_info_message(
    title="Dica",
    message="Use as categorias de gravidade para classificar melhor as ocorrências."
)

# ===== BADGES =====
# Usar gravidade com badge:
badge_html = render_badge("Agressão Física", variant="Agressão Física")
st.markdown(badge_html, unsafe_allow_html=True)

badge_html = render_badge("Leve", variant="success")
st.markdown(badge_html, unsafe_allow_html=True)

# ===== LABELS =====
render_label("Nome do Aluno", required=True, help_text="Digite o nome completo")

# ===== TABELAS =====
render_table_header(["Data", "Aluno", "Tipo", "Status"])

# ===== CARDS DE ESTATÍSTICA =====
render_stat_card(
    label="Total de Ocorrências",
    value="324",
    change=12.5,
    icon=ICONS["stats"],
    variant="primary"
)

# ===== SEPARADORES =====
render_divider()

# ===== CORES NO MARKDOWN =====
st.markdown(f"""
<div style="color: {COLORS['primary']}; font-size: 1.2rem;">
    Texto em cor primária
</div>
""", unsafe_allow_html=True)

# ===== TIPOGRAFIA NO MARKDOWN =====
st.markdown(f"""
<h2 style="{get_typography_css('h2')}">
    Título H2 com tipografia padronizada
</h2>
""", unsafe_allow_html=True)

# ===== USANDO MENU_ITEMS =====
from src.design_system import MENU_ITEMS

menu_html = "<div style='padding: 10px;'>"
for item in MENU_ITEMS:
    menu_html += f"""
    <div style="padding: 8px; cursor: pointer; border-radius: 4px;">
        {item['icon']} {item['label']}
    </div>
    """
menu_html += "</div>"

st.sidebar.markdown(menu_html, unsafe_allow_html=True)

# ===== PADRÃO COMPLETO DE FORMULÁRIO =====

def exemplo_formulario_padronizado():
    render_header_page(
        title="Registrar Ocorrência",
        subtitle="Preencha os dados abaixo",
        icon=ICONS["registro"]
    )
    
    with st.form("form_ocorrencia"):
        # Seção de Dados Básicos
        render_section(
            title="Informações do Aluno",
            icon=ICONS["aluno"]
        )
        
        render_label("Nome do Aluno", required=True)
        aluno = st.selectbox("Selecione um aluno", ["Ana Silva", "Bruno Costa", "Carla Santos"])
        
        render_label("Turma", required=True)
        turma = st.selectbox("Selecione a turma", ["6º A", "7º A", "8º A"])
        
        render_divider()
        
        # Seção de Ocorrência
        render_section(
            title="Detalhes da Ocorrência",
            icon=ICONS["ocorrencia"]
        )
        
        render_label("Tipo de Infração", required=True)
        infracao = st.selectbox(
            "Selecione a infração",
            ["Indisciplina", "Agressão Física", "Cabulou Aula", "Bullying"]
        )
        
        render_label("Gravidade", required=True)
        gravidade = st.selectbox("Nível de gravidade", list(GRAVIDADE_CORES.keys()))
        
        # Exibir badge de gravidade
        badge_html = render_badge(gravidade, variant=gravidade)
        st.markdown(badge_html, unsafe_allow_html=True)
        
        render_label("Descrição (adicionar novas informações)", required=False)
        descricao = st.text_area("Descreva o ocorrido")
        
        render_divider()
        
        # Botões
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("✅ Confirmar", use_container_width=True):
                render_success_message(
                    "Sucesso!",
                    "Ocorrência registrada com sucesso."
                )
        
        with col2:
            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                render_info_message(
                    "Cancelado",
                    "O formulário foi limpo."
                )
        
        with col3:
            pass

# ===== EXEMPLO DE PÁGINA COM ESTATÍSTICAS =====

def exemplo_dashboard():
    apply_global_style()
    
    render_header_page(
        title="Dashboard",
        subtitle="Visão geral da aplicação",
        icon=ICONS["stats"]
    )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_stat_card(
            label="Alunos Cadastrados",
            value="456",
            change=5.2,
            icon=ICONS["aluno"]
        )
    
    with col2:
        render_stat_card(
            label="Ocorrências Mês",
            value="89",
            change=-3.1,
            icon=ICONS["ocorrencia"]
        )
    
    with col3:
        render_stat_card(
            label="Professores",
            value="32",
            change=0,
            icon=ICONS["professor"]
        )
    
    with col4:
        render_stat_card(
            label="Turmas",
            value="24",
            change=1.5,
            icon=ICONS["turma"]
        )
    
    render_divider()
    
    render_section(
        title="Ocorrências Recentes",
        icon=ICONS["ocorrencia"]
    )
    
    # Exemplo de tabela
    render_table_header(["Data", "Aluno", "Tipo", "Gravidade"])

# ===== CORES SEMÂNTICAS =====
"""
Use as cores semânticas ao invés de cores hardcoded:

COLORS["primary"]              # Cor principal (azul)
COLORS["secondary"]            # Cor secundária (roxo)
COLORS["success"]              # Sucesso (verde)
COLORS["danger"]               # Perigo/Erro (vermelho)
COLORS["warning"]              # Aviso (laranja)
COLORS["info"]                 # Informação (azul-claro)

COLORS["text"]                 # Texto principal (cinza escuro)
COLORS["text_secondary"]       # Texto secundário (cinza médio)
COLORS["text_light"]           # Texto leve (cinza claro)

COLORS["gray_100"] a COLORS["gray_900"]  # Escala de cinzas

COLORS["white"]                # Branco
COLORS["border"]               # Cor de borda padrão
"""

# ===== GRAVIDADE COM CORES E ÍCONES =====
"""
Use GRAVIDADE_CORES para categorias de gravidade:

Cada item em GRAVIDADE_CORES tem:
- icon: Ícone Unicode
- label: Rótulo legível
- primary: Cor principal
- light: Cor clara (para fundo)
- dark: Cor escura (para texto)

Exemplo:
gravidade = "Agressão Física"
styling = get_gravidade_styling(gravidade)
# Retorna: {
#   "icon": "🔴",
#   "label": "Agressão Física",
#   "primary": "#dc2626",
#   "light": "#fee2e2",
#   "dark": "#991b1b"
# }
"""

# ===== ESPAÇAMENTO CONSISTENTE =====
"""
Use SPACING para margens e paddings:

SPACING["0"]     # 0px
SPACING["xs"]    # 4px
SPACING["sm"]    # 8px
SPACING["md"]    # 12px
SPACING["lg"]    # 16px
SPACING["xl"]    # 24px
SPACING["2xl"]   # 32px
SPACING["3xl"]   # 48px
SPACING["4xl"]   # 64px

Exemplo:
st.markdown(f'<div style="padding: {SPACING["lg"]};"> ... </div>')
"""

# ===== TAMANHOS DE COMPONENTES =====
"""
Use SIZES para componentes:

SIZES["button_xs"]      # Botão extra pequeno
SIZES["button_sm"]      # Botão pequeno
SIZES["button_md"]      # Botão médio
SIZES["button_lg"]      # Botão grande

SIZES["card_sm"]        # Card pequeno
SIZES["card_md"]        # Card médio
SIZES["card_lg"]        # Card grande

Cada item tem: width, height, padding, font_size
"""

# ===== TIPOGRAFIA =====
"""
Use TYPOGRAPHY para todas as fontes e tamanhos:

Headings:
- h1, h2, h3, h4

Body text:
- body_lg (grande)
- body_md (médio)
- body_sm (pequeno)
- body_xs (extra pequeno)

Labels:
- label_md (label médio)
- label_sm (label pequeno)

Caption:
- caption

Exemplo:
st.markdown(f'<h2 style="{get_typography_css("h2")}">Título</h2>')
"""

# ===== ÍCONES DISPONÍVEIS =====
"""
Use ICONS para ícones padronizados:

Navegação:
- home, menu, settings, search, back, close, more

Ações:
- create, edit, delete, send, save, export, import, download, upload,
  add, remove, filter, sort, expand, collapse, refresh

Status:
- success, error, warning, info, loading, check, cross

Dados:
- user, users, aluno, professor, turma, calendar, clock, chart

Comunicação:
- message, email, phone, notification, comment

Outros:
- stats, files, folder, document, lock, unlock, eye, eye_off

Exemplo:
st.markdown(f"{ICONS['home']} Home")
"""

print("=" * 60)
print("GUIA DE INTEGRAÇÃO COMPLETO")
print("=" * 60)
print("Veja acima exemplos de como usar todos os componentes")
print("Copie e adapte para sua aplicação")
