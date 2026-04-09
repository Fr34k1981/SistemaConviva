"""
COMPONENTES DE UI PADRONIZADOS
Buttons, Cards, Headers, Inputs, etc. com Design System
"""
import streamlit as st
from src.design_system import (
    COLORS, TYPOGRAPHY, SPACING, BORDER_RADIUS, SHADOWS,
    SIZES, ICONS, GRAVIDADE_CORES, get_typography_css,
    get_button_size_css, get_shadow_css, get_gravidade_styling,
    ANIMATIONS
)


# ===== BOTÕES PADRONIZADOS =====

def render_button(label, size="md", variant="primary", icon=None, full_width=False):
    """
    Renderiza um botão padronizado
    
    Args:
        label: Texto do botão
        size: 'xs', 'sm', 'md', 'lg'
        variant: 'primary', 'secondary', 'success', 'danger', 'ghost'
        icon: Ícone a exibir
        full_width: Ocupar 100% da largura
    """
    style_map = {
        "primary": {
            "bg": COLORS["primary"],
            "text": COLORS["white"],
            "hover_bg": COLORS["primary_dark"],
        },
        "secondary": {
            "bg": COLORS["secondary"],
            "text": COLORS["white"],
            "hover_bg": COLORS["secondary_dark"],
        },
        "success": {
            "bg": COLORS["success"],
            "text": COLORS["white"],
            "hover_bg": "#059669",
        },
        "danger": {
            "bg": COLORS["danger"],
            "text": COLORS["white"],
            "hover_bg": "#dc2626",
        },
        "ghost": {
            "bg": "transparent",
            "text": COLORS["primary"],
            "hover_bg": COLORS["light"],
        },
    }
    
    style = style_map.get(variant, style_map["primary"])
    button_icon = f"{icon} " if icon else ""
    
    css = f"""
    <style>
        .btn-{variant}-{size} {{
            {get_button_size_css(f'button_{size}')}
            background-color: {style['bg']};
            color: {style['text']};
            border: none;
            border-radius: {BORDER_RADIUS['md']};
            cursor: pointer;
            font-weight: 600;
            width: {'100%' if full_width else 'auto'};
            {get_shadow_css('sm')}
            {ANIMATIONS['transition_base']}
        }}
        .btn-{variant}-{size}:hover {{
            background-color: {style['hover_bg']};
            {ANIMATIONS['hover_lift']}
        }}
    </style>
    """
    
    return f"{button_icon}{label}"


# ===== CARDS PADRONIZADOS =====

def render_card(title, content, icon=None, variant="default", size="md"):
    """
    Renderiza um card padronizado
    
    Args:
        title: Título do card
        content: Conteúdo (HTML/texto)
        icon: Ícone do card
        variant: 'default', 'info', 'success', 'warning', 'danger'
        size: 'sm', 'md', 'lg'
    """
    color_map = {
        "default": COLORS["gray_100"],
        "info": COLORS["info_light"],
        "success": COLORS["success_light"],
        "warning": COLORS["warning_light"],
        "danger": COLORS["danger_light"],
    }
    
    card_size = SIZES[f"card_{size}"]
    border_color = {
        "default": COLORS["border"],
        "info": COLORS["info"],
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "danger": COLORS["danger"],
    }.get(variant, COLORS["border"])
    
    card_icon = f"{icon} " if icon else ""
    
    card_html = f"""
    <div style="
        background-color: {color_map[variant]};
        border-left: 4px solid {border_color};
        padding: {card_size['padding']};
        border-radius: {BORDER_RADIUS['lg']};
        {get_shadow_css('md')}
        margin-bottom: {SPACING['md']};
    ">
        <h4 style="
            {get_typography_css('h4')}
            color: {COLORS['text']};
            margin: 0 0 {SPACING['sm']} 0;
        ">
            {card_icon}{title}
        </h4>
        <p style="
            {get_typography_css('body')}
            color: {COLORS['text_secondary']};
            margin: 0;
        ">
            {content}
        </p>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)


# ===== HEADERS PADRONIZADOS =====

def render_header_page(title, subtitle=None, icon=None):
    """
    Header de página padronizado
    """
    title_icon = f"{icon} " if icon else ""
    
    header_html = f"""
    <div style="
        padding: {SPACING['xl']} {SPACING['md']};
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        border-radius: {BORDER_RADIUS['lg']};
        color: white;
        margin-bottom: {SPACING['2xl']};
        {get_shadow_css('lg')}
    ">
        <h1 style="
            {get_typography_css('h1')}
            color: white;
            margin: 0 0 {SPACING['sm'] if subtitle else '0'} 0;
        ">
            {title_icon}{title}
        </h1>
        {f'<p style="color: rgba(255,255,255,0.9); margin: 0;">{subtitle}</p>' if subtitle else ''}
    </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)


# ===== SEÇÕES PADRONIZADAS =====

def render_section(title, content_placeholder=None, collapsible=False, icon=None):
    """
    Seção padronizada com título
    """
    section_icon = f"{icon} " if icon else ""
    
    section_html = f"""
    <div style="
        margin-bottom: {SPACING['2xl']};
    ">
        <h3 style="
            {get_typography_css('h3')}
            color: {COLORS['text']};
            border-bottom: 2px solid {COLORS['border']};
            padding-bottom: {SPACING['md']};
            margin: {SPACING['lg']} 0 {SPACING['md']} 0;
        ">
            {section_icon}{title}
        </h3>
    </div>
    """
    
    st.markdown(section_html, unsafe_allow_html=True)


# ===== BADGES PADRONIZADOS =====

def render_badge(text, variant="default", size="md"):
    """
    Badge/rótulo padronizado
    
    Args:
        text: Texto do badge
        variant: 'default', 'primary', 'success', 'warning', 'danger', ou gravidade
        size: 'sm', 'md', 'lg'
    """
    # Verificar se é gravidade
    if variant in GRAVIDADE_CORES:
        colors = get_gravidade_styling(variant)
        bg_color = colors["light"]
        text_color = colors["dark"]
        icon = colors["icon"]
        text = f"{icon} {text}"
    else:
        color_map = {
            "default": (COLORS["gray_200"], COLORS["text"]),
            "primary": (COLORS["primary_lighter"], COLORS["primary_dark"]),
            "success": (COLORS["success_light"], COLORS["success"]),
            "warning": (COLORS["warning_light"], COLORS["warning"]),
            "danger": (COLORS["danger_light"], COLORS["danger"]),
        }
        bg_color, text_color = color_map.get(variant, color_map["default"])
    
    size_map = {"sm": "0.75rem", "md": "0.875rem", "lg": "1rem"}
    padding_map = {"sm": "0.25rem 0.5rem", "md": "0.375rem 0.75rem", "lg": "0.5rem 1rem"}
    
    badge_html = f"""
    <span style="
        display: inline-block;
        background-color: {bg_color};
        color: {text_color};
        padding: {padding_map[size]};
        border-radius: {BORDER_RADIUS['full']};
        font-size: {size_map[size]};
        font-weight: 600;
        white-space: nowrap;
    ">
        {text}
    </span>
    """
    
    return badge_html


# ===== LABELS PADRONIZADOS =====

def render_label(text, required=False, help_text=None):
    """
    Label padronizado para inputs
    """
    label_html = f"""
    <div style="margin-bottom: {SPACING['sm']};">
        <label style="
            {get_typography_css('label')}
            color: {COLORS['text']};
            display: block;
            margin-bottom: {SPACING['xs']};
        ">
            {text}
            {' <span style="color: ' + COLORS['danger'] + '; font-weight: bold;">*</span>' if required else ''}
        </label>
        {f'<small style="color: {COLORS["text_secondary"]}; display: block; margin-bottom: {SPACING["sm"]};">{help_text}</small>' if help_text else ''}
    </div>
    """
    
    st.markdown(label_html, unsafe_allow_html=True)


# ===== MENSAGENS PADRONIZADAS =====

def render_success_message(title, message):
    """Mensagem de sucesso padronizada"""
    st.markdown(f"""
    <div style="
        background-color: {COLORS['success_light']};
        border-left: 4px solid {COLORS['success']};
        padding: {SPACING['lg']};
        border-radius: {BORDER_RADIUS['md']};
        margin-bottom: {SPACING['md']};
    ">
        <strong style="color: {COLORS['success']};">✅ {title}</strong>
        <p style="color: {COLORS['text']}; margin-top: {SPACING['sm']}; margin-bottom: 0;">{message}</p>
    </div>
    """, unsafe_allow_html=True)


def render_error_message(title, message):
    """Mensagem de erro padronizada"""
    st.markdown(f"""
    <div style="
        background-color: {COLORS['danger_light']};
        border-left: 4px solid {COLORS['danger']};
        padding: {SPACING['lg']};
        border-radius: {BORDER_RADIUS['md']};
        margin-bottom: {SPACING['md']};
    ">
        <strong style="color: {COLORS['danger']};">❌ {title}</strong>
        <p style="color: {COLORS['text']}; margin-top: {SPACING['sm']}; margin-bottom: 0;">{message}</p>
    </div>
    """, unsafe_allow_html=True)


def render_warning_message(title, message):
    """Mensagem de aviso padronizada"""
    st.markdown(f"""
    <div style="
        background-color: {COLORS['warning_light']};
        border-left: 4px solid {COLORS['warning']};
        padding: {SPACING['lg']};
        border-radius: {BORDER_RADIUS['md']};
        margin-bottom: {SPACING['md']};
    ">
        <strong style="color: {COLORS['warning']};">⚠️ {title}</strong>
        <p style="color: {COLORS['text']}; margin-top: {SPACING['sm']}; margin-bottom: 0;">{message}</p>
    </div>
    """, unsafe_allow_html=True)


def render_info_message(title, message):
    """Mensagem de informação padronizada"""
    st.markdown(f"""
    <div style="
        background-color: {COLORS['info_light']};
        border-left: 4px solid {COLORS['info']};
        padding: {SPACING['lg']};
        border-radius: {BORDER_RADIUS['md']};
        margin-bottom: {SPACING['md']};
    ">
        <strong style="color: {COLORS['info']};"> ℹ️ {title}</strong>
        <p style="color: {COLORS['text']}; margin-top: {SPACING['sm']}; margin-bottom: 0;">{message}</p>
    </div>
    """, unsafe_allow_html=True)


# ===== SEPARADORES =====

def render_divider():
    """Separador visual padronizado"""
    st.markdown(f"""
    <div style="
        height: 1px;
        background: linear-gradient(to right, transparent, {COLORS['border']}, transparent);
        margin: {SPACING['xl']} 0;
    "></div>
    """, unsafe_allow_html=True)


# ===== TABELAS PADRONIZADAS =====

def render_table_header(columns):
    """
    Header de tabela padronizado
    
    Args:
        columns: Lista de nomes de colunas
    """
    header_html = "<div style='display: grid; grid-template-columns: "
    header_html += " ".join(["1fr"] * len(columns)) + "; gap: " + SPACING['md'] + "; "
    header_html += f"padding: {SPACING['md']}; background-color: {COLORS['gray_100']}; "
    header_html += f"border-radius: {BORDER_RADIUS['lg']} {BORDER_RADIUS['lg']} 0 0; "
    header_html += f"border-bottom: 2px solid {COLORS['border']}; margin-bottom: 0;'>"
    
    for col in columns:
        header_html += f"""
        <div style="{get_typography_css('label')}; color: {COLORS['text']};">
            {col}
        </div>
        """
    
    header_html += "</div>"
    st.markdown(header_html, unsafe_allow_html=True)


# ===== ESTATÍSTICAS =====

def render_stat_card(label, value, change=None, icon=None, variant="primary"):
    """
    Card de estatística padronizado
    """
    stat_icon = f"{icon} " if icon else ""
    change_color = COLORS["success"] if change and change > 0 else COLORS["danger"]
    change_text = f"{'+' if change and change > 0 else ''}{change}%" if change else ""
    
    stat_html = f"""
    <div style="
        background-color: white;
        border: 1px solid {COLORS['border']};
        border-radius: {BORDER_RADIUS['lg']};
        padding: {SPACING['lg']};
        text-align: center;
        {get_shadow_css('md')}
    ">
        <div style="
            {get_typography_css('body_sm')}
            color: {COLORS['text_secondary']};
            margin-bottom: {SPACING['sm']};
        ">
            {stat_icon}{label}
        </div>
        <div style="
            {get_typography_css('h2')}
            color: {COLORS['primary']};
            margin-bottom: {SPACING['xs']};
        ">
            {value}
        </div>
        {f'<div style="color: {change_color}; font-weight: bold;">{change_text}</div>' if change_text else ''}
    </div>
    """
    
    st.markdown(stat_html, unsafe_allow_html=True)


# ===== MODAL / DRAWER STYLE =====

def render_modal_container(title, content):
    """Estilo de modal padronizado"""
    modal_html = f"""
    <div style="
        background-color: white;
        border-radius: {BORDER_RADIUS['xl']};
        {get_shadow_css('2xl')}
        margin: {SPACING['2xl']} auto;
        max-width: 600px;
        overflow: hidden;
    ">
        <div style="
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
            padding: {SPACING['lg']};
            color: white;
        ">
            <h2 style="
                {get_typography_css('h2')}
                color: white;
                margin: 0;
            ">
                {title}
            </h2>
        </div>
        <div style="padding: {SPACING['2xl']};">
            {content}
        </div>
    </div>
    """
    
    st.markdown(modal_html, unsafe_allow_html=True)


# ===== ESTILO GLOBAL DO APP =====

def apply_global_style():
    """Aplica estilos globais ao Streamlit"""
    st.markdown(f"""
    <style>
        /* Fontes */
        * {{
            font-family: {TYPOGRAPHY['font_primary']};
        }}
        
        /* Scrollbar customizada */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: {COLORS['gray_100']};
        }}
        ::-webkit-scrollbar-thumb {{
            background: {COLORS['gray_400']};
            border-radius: {BORDER_RADIUS['full']};
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {COLORS['gray_500']};
        }}
        
        /* Headings */
        h1, h2, h3, h4, h5, h6 {{
            color: {COLORS['text']};
            font-weight: 700;
        }}
        
        /* Links */
        a {{
            color: {COLORS['primary']};
            text-decoration: none;
            transition: all 0.2s ease;
        }}
        a:hover {{
            color: {COLORS['primary_dark']};
            text-decoration: underline;
        }}
        
        /* Botões do Streamlit */
        .stButton > button {{
            width: 100%;
            padding: {SPACING['md']} {SPACING['lg']};
            border: none;
            border-radius: {BORDER_RADIUS['md']};
            font-weight: 600;
            {get_shadow_css('md')}
            {ANIMATIONS['transition_base']}
        }}
        
        .stButton > button:hover {{
            {ANIMATIONS['hover_lift']}
        }}
        
        /* Inputs do Streamlit */
        .stTextInput input, .stTextArea textarea, .stSelectbox select {{
            border: 1px solid {COLORS['border']} !important;
            border-radius: {BORDER_RADIUS['md']} !important;
            padding: {SPACING['md']} !important;
            font-size: 1rem !important;
        }}
        
        .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {{
            border-color: {COLORS['primary']} !important;
            box-shadow: 0 0 0 3px {COLORS['primary']}20 !important;
        }}
        
        /* Checkbox e Radio */
        input[type="checkbox"], input[type="radio"] {{
            accent-color: {COLORS['primary']};
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] button {{
            border-radius: {BORDER_RADIUS['md']} {BORDER_RADIUS['md']} 0 0;
            font-weight: 600;
        }}
        
        /* Expander */
        .streamlit-expanderHeader {{
            font-weight: 600;
            border-radius: {BORDER_RADIUS['md']};
        }}
        
        /* Código */
        code {{
            background-color: {COLORS['gray_100']};
            padding: 2px 6px;
            border-radius: {BORDER_RADIUS['xs']};
            font-family: {TYPOGRAPHY['font_mono']};
        }}
        
        pre {{
            background-color: {COLORS['gray_900']};
            color: {COLORS['white']};
            border-radius: {BORDER_RADIUS['lg']};
            padding: {SPACING['lg']};
        }}
    </style>
    """, unsafe_allow_html=True)
