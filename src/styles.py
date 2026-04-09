"""
Configurações de tema e estilos visuais profissionais
"""

# ===== PALETA DE CORES =====
COLORS = {
    "primary": "#2563eb",
    "primary_light": "#3b82f6",
    "primary_dark": "#1e40af",
    "secondary": "#7c3aed",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#3b82f6",
    "light": "#f9fafb",
    "gray": "#6b7280",
    "dark": "#1f2937",
    "border": "#e5e7eb",
    "text": "#1f2937",
    "text_secondary": "#6b7280",
}

# ===== CORES POR GRAVIDADE =====
GRAVIDADE_CORES = {
    "Leve": {
        "primary": "#10b981",
        "light": "#d1fae5",
        "lighter": "#a7f3d0",
        "dark": "#065f46",
    },
    "Média": {
        "primary": "#f59e0b",
        "light": "#fef08a",
        "lighter": "#fde047",
        "dark": "#78350f",
    },
    "Grave": {
        "primary": "#f97316",
        "light": "#fed7aa",
        "lighter": "#fdba74",
        "dark": "#7c2d12",
    },
    "Gravíssima": {
        "primary": "#ef4444",
        "light": "#fecaca",
        "lighter": "#fca5a5",
        "dark": "#7f1d1d",
    },
}

# ===== TIPOGRAFIA =====
TYPOGRAPHY = {
    "title": "font-size: 2rem; font-weight: 700; letter-spacing: -0.5px;",
    "subtitle": "font-size: 1.5rem; font-weight: 700;",
    "section": "font-size: 1.25rem; font-weight: 600;",
    "body": "font-size: 1rem; font-weight: 400;",
    "small": "font-size: 0.875rem; font-weight: 400;",
    "label": "font-size: 0.9375rem; font-weight: 600;",
}

# ===== ESPAÇAMENTO =====
SPACING = {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.25rem",
    "xl": "1.5rem",
    "2xl": "2rem",
    "3xl": "2.5rem",
}

# ===== SOMBRAS =====
SHADOWS = {
    "sm": "0 2px 8px rgba(0, 0, 0, 0.06)",
    "md": "0 4px 12px rgba(0, 0, 0, 0.1)",
    "lg": "0 8px 20px rgba(0, 0, 235, 0.15)",
    "xl": "0 12px 28px rgba(37, 99, 235, 0.25)",
}

# ===== RAIO DE BORDA =====
BORDER_RADIUS = {
    "sm": "6px",
    "md": "10px",
    "lg": "12px",
    "full": "20px",
}

# ===== FUNÇÃO PARA GERAR CARD COM GRAVIDADE =====
def get_gravidade_style(gravidade: str) -> dict:
    """
    Retorna um dicionário com cores para a gravidade especificada
    
    Args:
        gravidade: Uma das chaves em GRAVIDADE_CORES
    
    Returns:
        Dicionário com as cores correspondentes
    """
    return GRAVIDADE_CORES.get(
        gravidade,
        GRAVIDADE_CORES["Leve"]  # Default
    )


# ===== FUNÇÃO PARA CRIAR BADGE DE STATUS =====
def create_status_badge_html(texto: str, status: str) -> str:
    """
    Cria HTML de uma badge de status profissional
    
    Args:
        texto: Texto a exibir
        status: Tipo de status (success, warning, danger, info)
    
    Returns:
        String HTML para a badge
    """
    colors_map = {
        "success": ("#dcfce7", "#047857"),
        "warning": ("#fef3c7", "#92400e"),
        "danger": ("#fee2e2", "#991b1b"),
        "info": ("#dbeafe", "#1e40af"),
    }
    
    bg_color, text_color = colors_map.get(status, colors_map["info"])
    
    return f"""
    <span style="
        background-color: {bg_color};
        color: {text_color};
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
    ">
        {texto}
    </span>
    """


# ===== FUNÇÃO PARA CRIAR CARD DE INFRAÇÃO COM GRAVIDADE =====
def create_gravidade_card_html(titulo: str, conteudo: str, gravidade: str) -> str:
    """
    Cria um card HTML com estilo baseado na gravidade
    
    Args:
        titulo: Título do card
        conteudo: Conteúdo HTML do card
        gravidade: Nível de gravidade (Leve, Média, Grave, Gravíssima)
    
    Returns:
        String HTML para o card
    """
    cores = get_gravidade_style(gravidade)
    
    return f"""
    <div style="
        background: linear-gradient(135deg, {cores['light']} 0%, {cores['lighter']} 100%);
        border-left: 4px solid {cores['primary']};
        border-radius: 10px;
        padding: 1.25rem;
        margin: 1rem 0;
        color: {cores['dark']};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    ">
        <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.75rem;">
            {titulo}
        </div>
        <div style="font-size: 0.95rem; line-height: 1.6;">
            {conteudo}
        </div>
    </div>
    """


# ===== FUNÇÃO PARA CRIAR CONTAINER INFO =====
def create_info_container_html(titulo: str, conteudo: str, icon: str = "ℹ️", tipo: str = "info") -> str:
    """
    Cria um container de informação profissional
    
    Args:
        titulo: Título do container
        conteudo: Conteúdo HTML
        icon: Emoji ou símbolo (padrão: ℹ️)
        tipo: Tipo (info, warning, success, error)
    
    Returns:
        String HTML para o container
    """
    color_map = {
        "info": "#2563eb",
        "warning": "#f59e0b",
        "success": "#10b981",
        "error": "#ef4444",
    }
    
    cor = color_map.get(tipo, color_map["info"])
    
    return f"""
    <div style="
        background: white;
        border: 1px solid {cor}20;
        border-left: 4px solid {cor};
        border-radius: 10px;
        padding: 1.25rem;
        margin: 1.25rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.75rem;
            color: {cor};
        ">
            <span style="font-size: 1.5rem;">{icon}</span>
            <span style="font-weight: 600; font-size: 1rem;">{titulo}</span>
        </div>
        <div style="color: #4b5563; font-size: 0.95rem; line-height: 1.6;">
            {conteudo}
        </div>
    </div>
    """
