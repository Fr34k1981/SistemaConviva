"""
DESIGN SYSTEM - Sistema de Design Completo e Padronizado
Tipografia, paleta de cores, espaçamento, ícones, tamanhos e componentes
"""

# ===== 1. PALETA DE CORES EXPANDIDA =====
COLORS = {
    # Primária (Azul)
    "primary": "#2563eb",
    "primary_light": "#3b82f6",
    "primary_lighter": "#60a5fa",
    "primary_dark": "#1e40af",
    "primary_darker": "#1e3a8a",
    
    # Secundária (Roxo)
    "secondary": "#7c3aed",
    "secondary_light": "#a78bfa",
    "secondary_dark": "#6d28d9",
    
    # Estados
    "success": "#10b981",
    "success_light": "#d1fae5",
    "warning": "#f59e0b",
    "warning_light": "#fef08a",
    "danger": "#ef4444",
    "danger_light": "#fee2e2",
    "info": "#06b6d4",
    "info_light": "#cffafe",
    
    # Neutras
    "white": "#ffffff",
    "black": "#000000",
    "light": "#f9fafb",
    "lighter": "#f3f4f6",
    "gray_50": "#f9fafb",
    "gray_100": "#f3f4f6",
    "gray_200": "#e5e7eb",
    "gray_300": "#d1d5db",
    "gray_400": "#9ca3af",
    "gray_500": "#6b7280",
    "gray_600": "#4b5563",
    "gray_700": "#374151",
    "gray_800": "#1f2937",
    "gray_900": "#111827",
    
    # Texto
    "text": "#1f2937",
    "text_secondary": "#6b7280",
    "text_tertiary": "#9ca3af",
    "text_inverse": "#ffffff",
    
    # Bordas
    "border": "#e5e7eb",
    "border_dark": "#d1d5db",
    "border_light": "#f3f4f6",
}

# ===== 2. CORES POR GRAVIDADE (OCORRÊNCIAS) =====
GRAVIDADE_CORES = {
    "Leve": {
        "primary": "#10b981",
        "light": "#d1fae5",
        "lighter": "#a7f3d0",
        "dark": "#065f46",
        "icon": "✅",
        "badge": "#d1fae5",
        "text": "#065f46",
    },
    "Média": {
        "primary": "#f59e0b",
        "light": "#fef08a",
        "lighter": "#fde047",
        "dark": "#78350f",
        "icon": "⚠️",
        "badge": "#fef08a",
        "text": "#78350f",
    },
    "Grave": {
        "primary": "#f97316",
        "light": "#fed7aa",
        "lighter": "#fdba74",
        "dark": "#7c2d12",
        "icon": "🔴",
        "badge": "#fed7aa",
        "text": "#7c2d12",
    },
    "Gravíssima": {
        "primary": "#ef4444",
        "light": "#fecaca",
        "lighter": "#fca5a5",
        "dark": "#7f1d1d",
        "icon": "⛔",
        "badge": "#fecaca",
        "text": "#7f1d1d",
    },
}

# ===== 3. TIPOGRAFIA COMPLETA =====
TYPOGRAPHY = {
    # Font Families (usar Segoe UI ou Inter para web, ou system fonts)
    "font_primary": "'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    "font_mono": "'Courier New', Courier, monospace",
    
    # Heading Sizes
    "h1": {
        "size": "2rem",
        "weight": 700,
        "line_height": 1.2,
        "letter_spacing": "-0.5px",
    },
    "h2": {
        "size": "1.75rem",
        "weight": 700,
        "line_height": 1.3,
        "letter_spacing": "-0.25px",
    },
    "h3": {
        "size": "1.5rem",
        "weight": 700,
        "line_height": 1.3,
        "letter_spacing": "0px",
    },
    "h4": {
        "size": "1.25rem",
        "weight": 600,
        "line_height": 1.4,
        "letter_spacing": "0px",
    },
    
    # Body Sizes
    "body_lg": {
        "size": "1.125rem",
        "weight": 400,
        "line_height": 1.5,
    },
    "body": {
        "size": "1rem",
        "weight": 400,
        "line_height": 1.5,
    },
    "body_sm": {
        "size": "0.875rem",
        "weight": 400,
        "line_height": 1.5,
    },
    "body_xs": {
        "size": "0.75rem",
        "weight": 400,
        "line_height": 1.5,
    },
    
    # Labels & Captions
    "label_lg": {
        "size": "1rem",
        "weight": 600,
        "line_height": 1.4,
        "text_transform": "none",
    },
    "label": {
        "size": "0.9375rem",
        "weight": 600,
        "line_height": 1.4,
    },
    "label_sm": {
        "size": "0.8125rem",
        "weight": 600,
        "line_height": 1.4,
        "text_transform": "uppercase",
        "letter_spacing": "0.5px",
    },
    "caption": {
        "size": "0.75rem",
        "weight": 500,
        "line_height": 1.4,
        "color": COLORS["text_secondary"],
    },
}

# ===== 4. ESPAÇAMENTO PADRONIZADO =====
SPACING = {
    "0": "0px",
    "xs": "0.25rem",      # 4px
    "sm": "0.5rem",       # 8px
    "md": "1rem",         # 16px
    "lg": "1.5rem",       # 24px
    "xl": "2rem",         # 32px
    "2xl": "2.5rem",      # 40px
    "3xl": "3rem",        # 48px
    "4xl": "3.5rem",      # 56px
    "5xl": "4rem",        # 64px
}

# ===== 5. RAIO DE BORDA =====
BORDER_RADIUS = {
    "none": "0px",
    "xs": "0.25rem",      # 4px (botões pequenos)
    "sm": "0.375rem",     # 6px
    "md": "0.5rem",       # 8px (padrão)
    "lg": "0.75rem",      # 12px (cards)
    "xl": "1rem",         # 16px (modais)
    "2xl": "1.5rem",      # 24px (grandes)
    "full": "9999px",     # Pills / Fully rounded
}

# ===== 6. SOMBRAS =====
SHADOWS = {
    "none": "none",
    "xs": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "sm": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
    "inner": "inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)",
}

# ===== 7. EFEITOS E ANIMAÇÕES =====
ANIMATIONS = {
    "transition_fast": "transition: all 0.15s ease-in-out;",
    "transition_base": "transition: all 0.3s ease-in-out;",
    "transition_slow": "transition: all 0.5s ease-in-out;",
    "hover_lift": "transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15);",
    "hover_scale": "transform: scale(1.02);",
}

# ===== 8. TAMANHOS DE COMPONENTES =====
SIZES = {
    # Botões
    "button_xs": {
        "padding": "0.375rem 0.75rem",  # 6-12px
        "font_size": "0.75rem",
        "height": "1.75rem",            # 28px
    },
    "button_sm": {
        "padding": "0.5rem 1rem",       # 8-16px
        "font_size": "0.875rem",
        "height": "2rem",               # 32px
    },
    "button_md": {
        "padding": "0.75rem 1.5rem",    # 12-24px
        "font_size": "1rem",
        "height": "2.5rem",             # 40px (padrão)
    },
    "button_lg": {
        "padding": "1rem 2rem",         # 16-32px
        "font_size": "1.125rem",
        "height": "3rem",               # 48px
    },
    
    # Input / Field
    "input": {
        "padding": "0.625rem 1rem",    # 10-16px
        "font_size": "1rem",
        "height": "2.5rem",             # 40px
    },
    
    # Cards
    "card_sm": {
        "padding": "1rem",
        "max_width": "300px",
    },
    "card_md": {
        "padding": "1.5rem",
        "max_width": "600px",
    },
    "card_lg": {
        "padding": "2rem",
        "max_width": "900px",
    },
    
    # Modal / Drawer
    "modal": {
        "width": "600px",
        "max_height": "90vh",
    },
    "drawer": {
        "width": "400px",
        "max_height": "100vh",
    },
    
    # Avatar
    "avatar_xs": "1.5rem",      # 24px
    "avatar_sm": "2rem",        # 32px
    "avatar_md": "2.5rem",      # 40px
    "avatar_lg": "3rem",        # 48px
    "avatar_xl": "4rem",        # 64px
    
    # Icon
    "icon_xs": "1rem",          # 16px
    "icon_sm": "1.25rem",       # 20px
    "icon_md": "1.5rem",        # 24px
    "icon_lg": "2rem",          # 32px
    "icon_xl": "3rem",          # 48px
}

# ===== 9. ÍCONES PADRONIZADOS =====
ICONS = {
    # Ações
    "add": "➕",
    "edit": "✏️",
    "delete": "🗑️",
    "save": "💾",
    "cancel": "❌",
    "close": "✕",
    "back": "←",
    "search": "🔍",
    "filter": "🔽",
    "sort": "↕️",
    "menu": "☰",
    "download": "⬇️",
    "upload": "⬆️",
    "copy": "📋",
    "share": "🔗",
    
    # Status
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ⓘ",
    "loading": "⏳",
    "check": "✓",
    "cross": "✗",
    
    # Navegação
    "home": "🏠",
    "dashboard": "📊",
    "settings": "⚙️",
    "profile": "👤",
    "logout": "🚪",
    "next": "→",
    "prev": "←",
    "up": "↑",
    "down": "↓",
    
    # Dados
    "student": "👨‍🎓",
    "teacher": "👨‍🏫",
    "calendar": "📅",
    "time": "⏰",
    "clock": "🕐",
    "file": "📄",
    "folder": "📁",
    "document": "📃",
    "printer": "🖨️",
    "pdf": "📕",
    "excel": "📗",
    
    # Comunicação
    "message": "💬",
    "email": "📧",
    "phone": "📞",
    "call": "☎️",
    "notification": "🔔",
    "bell": "🔔",
    
    # Geral
    "star": "⭐",
    "heart": "❤️",
    "flag": "🚩",
    "link": "🔗",
    "eye": "👁️",
    "eye_off": "👁️‍🗨️",
    "lock": "🔒",
    "unlock": "🔓",
    "key": "🔑",
    
    # Ocorrências (específico do sistema)
    "occurrence": "📝",
    "agression": "⛔",
    "truancy": "🏃",
    "bullying": "😤",
    "disrespect": "🗣️",
    "theft": "🚨",
    "damage": "🔨",
    "drugs": "⚠️",
    "weapon": "🚫",
}

# ===== 10. MENU PADRONIZADO =====
MENU_ITEMS = {
    "home": {"icon": "🏠", "label": "Início", "order": 0},
    "register_student": {"icon": "👨‍🎓", "label": "Registrar Aluno", "order": 1},
    "register_teacher": {"icon": "👨‍🏫", "label": "Registrar Professor", "order": 2},
    "register_responsible": {"icon": "👥", "label": "Registrar Responsável", "order": 3},
    "register_occurrence": {"icon": "📝", "label": "Registrar Ocorrência", "order": 4},
    "query_occurrence": {"icon": "🔍", "label": "Consultar Ocorrência", "order": 5},
    "report": {"icon": "📊", "label": "Relatórios", "order": 6},
    "communication": {"icon": "📄", "label": "Comunicado aos Pais", "order": 7},
    "elective": {"icon": "🎓", "label": "Eletivas", "order": 8},
    "backup": {"icon": "💾", "label": "Backups", "order": 9},
    "settings": {"icon": "⚙️", "label": "Configurações", "order": 10},
}

# ===== 11. BREAKPOINTS (RESPONSIVIDADE) =====
BREAKPOINTS = {
    "xs": 0,        # Extra small (mobile)
    "sm": 640,      # Small (mobile landscape)
    "md": 768,      # Medium (tablet)
    "lg": 1024,     # Large (desktop)
    "xl": 1280,     # Extra large (wide desktop)
    "2xl": 1536,    # 2X large (very wide)
}

# ===== 12. Z-INDEX COORDENADO =====
Z_INDEX = {
    "hide": -1,
    "auto": 0,
    "dropdown": 1000,
    "sticky": 1020,
    "fixed": 1030,
    "modal_backdrop": 1040,
    "modal": 1050,
    "popover": 1060,
    "tooltip": 1070,
    "notification": 1080,
    "absolute_max": 9999,
}

# ===== 13. TRANSIÇÕES DE TEMPO =====
DURATIONS = {
    "instant": "0ms",
    "fastest": "75ms",
    "faster": "100ms",
    "fast": "150ms",
    "normal": "200ms",
    "slow": "300ms",
    "slower": "500ms",
    "slowest": "1s",
}

# ===== 14. SISTEMA DE GRID =====
GRID = {
    "gutter": "1.5rem",      # 24px (espaço entre colunas)
    "columns": 12,
    "max_width": "1280px",   # 1280px (container max)
}

# ===== FUNÇÕES DE HELPER =====

def get_typography_css(style_name):
    """Retorna CSS para um estilo de tipografia"""
    if style_name not in TYPOGRAPHY:
        return ""
    
    styles = TYPOGRAPHY[style_name]
    if isinstance(styles, dict):
        css = f"font-size: {styles.get('size', '1rem')};"
        css += f"font-weight: {styles.get('weight', 400)};"
        css += f"line-height: {styles.get('line_height', 1.5)};"
        if 'letter_spacing' in styles:
            css += f"letter-spacing: {styles['letter_spacing']};"
        return css
    return styles

def get_color(color_name):
    """Retorna cor por nome"""
    return COLORS.get(color_name, COLORS["text"])

def get_gravidade_styling(gravidade):
    """Retorna estilo completo para uma gravidade"""
    return GRAVIDADE_CORES.get(gravidade, GRAVIDADE_CORES["Leve"])

def get_shadow_css(shadow_name):
    """Retorna propriedade box-shadow"""
    shadow = SHADOWS.get(shadow_name, SHADOWS["md"])
    return f"box-shadow: {shadow};" if shadow != "none" else "box-shadow: none;"

def get_button_size_css(size_name):
    """Retorna CSS para tamanho de botão"""
    if size_name not in SIZES:
        size_name = "button_md"
    
    size = SIZES[size_name]
    css = f"padding: {size['padding']};"
    css += f"font-size: {size['font_size']};"
    css += f"min-height: {size['height']};"
    return css
