"""
Componentes visuais profissionais reutilizáveis
"""
import streamlit as st
from src.styles import (
    COLORS, GRAVIDADE_CORES, create_gravidade_card_html,
    create_info_container_html, create_status_badge_html
)


def render_header(titulo: str, subtitulo: str = "", descricao: str = ""):
    """Renderiza um cabeçalho profissional"""
    if descricao:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
            padding: 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 2rem;
        ">
            <h1 style="margin: 0; font-size: 2rem; font-weight: 700;">{titulo}</h1>
            {f'<p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.95;">{subtitulo}</p>' if subtitulo else ''}
            {f'<p style="margin: 1rem 0 0 0; font-size: 0.95rem; opacity: 0.85; line-height: 1.6;">{descricao}</p>' if descricao else ''}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.title(titulo)
        if subtitulo:
            st.markdown(f"*{subtitulo}*")


def render_info_box(texto: str, tipo: str = "info", icon: str = None):
    """Renderiza uma caixa de informação profissional"""
    icon_map = {
        "info": "ℹ️",
        "warning": "⚠️",
        "success": "✅",
        "error": "❌",
        "tip": "💡"
    }
    
    icon = icon or icon_map.get(tipo, "ℹ️")
    
    tipo_title_map = {
        "info": "Informação",
        "warning": "Aviso",
        "success": "Sucesso",
        "error": "Erro",
        "tip": "Dica"
    }
    
    st.markdown(
        create_info_container_html(
            titulo=tipo_title_map.get(tipo, "Informação"),
            conteudo=texto,
            icon=icon,
            tipo=tipo
        ),
        unsafe_allow_html=True
    )


def render_gravidade_badge(gravidade: str):
    """Renderiza uma badge de gravidade colorida"""
    cores = GRAVIDADE_CORES.get(gravidade, GRAVIDADE_CORES["Leve"])
    
    st.markdown(f"""
    <span style="
        background: linear-gradient(135deg, {cores['light']} 0%, {cores['lighter']} 100%);
        color: {cores['dark']};
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        border-left: 3px solid {cores['primary']};
        display: inline-block;
    ">
        {gravidade}
    </span>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, valor: str | int, delta: str = None, cor: str = "primary"):
    """Renderiza um card de métrica profissional"""
    cor_hex = COLORS.get(cor, COLORS["primary"])
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {cor_hex} 0%, {COLORS['primary_light']} 100%);
        padding: 1.75rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.15);
    ">
        <div style="font-size: 2.75rem; font-weight: 700; margin-bottom: 0.5rem;">
            {valor}
        </div>
        <div style="font-size: 1rem; opacity: 0.95; font-weight: 500;">
            {label}
        </div>
        {f'<div style="font-size: 0.85rem; opacity: 0.85; margin-top: 0.5rem;">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)


def render_data_row(dados: dict, cols: list = None):
    """
    Renderiza uma linha de dados profissional
    
    dados: Dict com as colunas e valores
    cols: Lista de colunas a exibir (None = todas)
    """
    if cols is None:
        cols = list(dados.keys())
    
    col_objs = st.columns(len(cols))
    
    for idx, col_name in enumerate(cols):
        with col_objs[idx]:
            valor = dados.get(col_name, "N/A")
            st.markdown(f"""
            <div style="
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 1rem;
                text-align: center;
            ">
                <div style="
                    font-size: 0.9rem;
                    color: {COLORS['text_secondary']};
                    font-weight: 500;
                    margin-bottom: 0.5rem;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                ">
                    {col_name}
                </div>
                <div style="
                    font-size: 1.5rem;
                    color: {COLORS['primary']};
                    font-weight: 700;
                ">
                    {valor}
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_section_divider(margin: str = "1.5rem"):
    """Renderiza um divisor visual entre seções"""
    st.markdown(f"""
    <div style="
        height: 1px;
        background: linear-gradient(90deg, transparent, {COLORS['border']}, transparent);
        margin: {margin} 0;
    "></div>
    """, unsafe_allow_html=True)


def render_success_message(mensagem: str):
    """Renderiza uma mensagem de sucesso profissional"""
    st.markdown(f"""
    <div class="success-box">
        ✅ {mensagem}
    </div>
    """, unsafe_allow_html=True)


def render_error_message(mensagem: str):
    """Renderiza uma mensagem de erro profissional"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border: 1px solid {COLORS['danger']};
        border-left: 4px solid {COLORS['danger']};
        border-radius: 10px;
        padding: 1.25rem;
        margin: 1.25rem 0;
        color: #7f1d1d;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
    ">
        ❌ {mensagem}
    </div>
    """, unsafe_allow_html=True)


def render_warning_message(mensagem: str):
    """Renderiza uma mensagem de aviso profissional"""
    st.markdown(f"""
    <div class="protocolo-info">
        ⚠️ {mensagem}
    </div>
    """, unsafe_allow_html=True)


def render_button_group(botoes: dict):
    """
    Renderiza um grupo de botões lado a lado
    
    botoes: Dict com {label: callback}
    """
    cols = st.columns(len(botoes))
    for idx, (label, callback) in enumerate(botoes.items()):
        with cols[idx]:
            if st.button(label, use_container_width=True):
                callback()


def render_stats_row(stats: dict):
    """
    Renderiza uma linha de estatísticas
    
    stats: Dict com {label: valor}
    """
    cols = st.columns(len(stats))
    for idx, (label, valor) in enumerate(stats.items()):
        with cols[idx]:
            st.metric(label, valor)


def apply_professional_style():
    """Aplica estilos profissionais gerais ao Streamlit"""
    st.markdown("""
    <style>
    /* Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    ::-webkit-scrollbar-thumb {
        background: #2563eb;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #1e40af;
    }
    </style>
    """, unsafe_allow_html=True)
