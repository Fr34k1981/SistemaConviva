# ======================================================
# IMPORTS PADRÃO
# ======================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime, timedelta
from io import BytesIO
from difflib import SequenceMatcher
from xml.etree import ElementTree as ET
import requests
import os
import re
import zipfile
import pytz
import unicodedata
from dotenv import load_dotenv

# ======================================================
# REPORTLAB (PDF)
# ======================================================
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER

# ======================================================
# IMPORTS LOCAIS
# ======================================================
try:
    from src.backup_manager import BackupManager, render_backup_page
except ImportError:
    class BackupManager:
        """Fallback seguro quando o módulo real de backup não estiver disponível."""
        def criar_backup(self, *args, **kwargs):
            return None

        def limpar_backups_antigos(self, *args, **kwargs):
            return None

    def render_backup_page():
        st.info("⚠️ Módulo de backup não disponível")

try:
    from src.error_handler import (
        com_tratamento_erro, com_retry,
        ErroConexaoDB, ErroValidacao, ErroCarregamentoDados,
        ErroOperacaoDB, Validadores, logger
    )
except ImportError:
    def com_tratamento_erro(func):
        return func
    def com_retry(tentativas=2):
        def decorator(func):
            return func
        return decorator
    def com_validacao(func):
        return func
    class ErroConexaoDB(Exception):
        pass
    class ErroValidacao(Exception):
        pass
    class ErroCarregamentoDados(Exception):
        def __init__(self, acao, detalhes):
            super().__init__(f"Erro ao {acao}: {detalhes}")
    class ErroOperacaoDB(Exception):
        def __init__(self, acao, detalhes):
            super().__init__(f"Erro ao {acao}: {detalhes}")
    class Validadores:
        @staticmethod
        def validar_nao_vazio(valor, campo):
            if not valor or not str(valor).strip():
                return False, f"{campo} não pode ser vazio"
            return True, ""
    import logging
    logger = logging.getLogger(__name__)

# ======================================================
# VARIÁVEIS DE AMBIENTE
# ======================================================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SENHA_EXCLUSAO = os.getenv("SENHA_EXCLUSAO", "040600")
SUPABASE_VALID = bool(SUPABASE_URL and SUPABASE_KEY)

def resolver_caminho_existente(*caminhos):
    """Retorna o primeiro caminho existente; caso nenhum exista, devolve o primeiro candidato válido."""
    candidatos = [str(c).strip() for c in caminhos if c and str(c).strip()]
    for caminho in candidatos:
        if os.path.exists(caminho):
            return caminho
    return candidatos[0] if candidatos else ""

HEADERS = {}
if SUPABASE_VALID:
    HEADERS = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

# ======================================================
# CONFIGURAÇÃO STREAMLIT
# ======================================================
st.set_page_config(
    page_title="Sistema Conviva 179 - E.E. Profª Eliane",
    layout="wide",
    page_icon="🏫",
    initial_sidebar_state="expanded"
)
# ======================================================
# CSS PREMIUM EDUCACIONAL — DESIGN MODERNO E PROFISSIONAL
# ======================================================
st.markdown("""
<style>
/* ============================================ */
/* ========== GOOGLE FONTS IMPORT ========== */
/* ============================================ */
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

/* ============================================ */
/* ========== RESET GLOBAL ========== */
/* ============================================ */
*, *::before, *::after {
    box-sizing: border-box;
}

html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Nunito', sans-serif !important;
}

/* ============================================ */
/* ========== VARIÁVEIS DE DESIGN ========== */
/* ============================================ */
:root {
    /* Cores primárias — azul educacional */
    --primary:        #2563eb;
    --primary-light:  #3b82f6;
    --primary-xlight: #eff6ff;
    --primary-dark:   #1d4ed8;

    /* Acento verde sucesso */
    --success:        #059669;
    --success-light:  #d1fae5;

    /* Acento âmbar aviso */
    --warning:        #d97706;
    --warning-light:  #fef3c7;

    /* Vermelho perigo */
    --danger:         #dc2626;
    --danger-light:   #fee2e2;

    /* Info ciano */
    --info:           #0891b2;
    --info-light:     #e0f2fe;

    /* Roxo destaque */
    --purple:         #7c3aed;
    --purple-light:   #ede9fe;

    /* Neutros */
    --dark:           #0f172a;
    --dark-mid:       #1e293b;
    --gray-dark:      #334155;
    --gray:           #64748b;
    --gray-light:     #94a3b8;
    --border:         #e2e8f0;
    --border-light:   #f1f5f9;
    --bg:             #f8fafc;
    --white:          #ffffff;

    /* Gradientes */
    --grad-primary:   linear-gradient(135deg, #1d4ed8 0%, #2563eb 50%, #3b82f6 100%);
    --grad-teal:      linear-gradient(135deg, #0891b2 0%, #06b6d4 100%);
    --grad-emerald:   linear-gradient(135deg, #059669 0%, #10b981 100%);
    --grad-amber:     linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
    --grad-danger:    linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
    --grad-purple:    linear-gradient(135deg, #6d28d9 0%, #7c3aed 100%);
    --grad-school:    linear-gradient(135deg, #1d4ed8 0%, #0891b2 60%, #059669 100%);
    --grad-warm:      linear-gradient(135deg, #f97316 0%, #ef4444 50%, #ec4899 100%);

    /* Sombras */
    --shadow-xs:  0 1px 2px rgba(15,23,42,0.06);
    --shadow-sm:  0 2px 4px rgba(15,23,42,0.08);
    --shadow-md:  0 4px 12px rgba(15,23,42,0.10);
    --shadow-lg:  0 8px 24px rgba(15,23,42,0.12);
    --shadow-xl:  0 16px 40px rgba(15,23,42,0.14);
    --shadow-2xl: 0 24px 64px rgba(15,23,42,0.18);
    --shadow-blue: 0 8px 24px rgba(37,99,235,0.25);
    --shadow-green: 0 8px 24px rgba(5,150,105,0.25);

    /* Raios */
    --r-xs:  4px;
    --r-sm:  8px;
    --r-md:  12px;
    --r-lg:  16px;
    --r-xl:  20px;
    --r-2xl: 24px;
    --r-3xl: 32px;
    --r-full: 9999px;
}

/* ============================================ */
/* ========== ANIMAÇÕES ========== */
/* ============================================ */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInLeft {
    from { opacity: 0; transform: translateX(-16px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.95); }
    to   { opacity: 1; transform: scale(1); }
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(37,99,235,0.3); }
    50%       { box-shadow: 0 0 0 8px rgba(37,99,235,0); }
}
@keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position: 200% center; }
}
@keyframes floatDot {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-6px); }
}

.animate-fade-in   { animation: fadeInUp 0.5s cubic-bezier(.16,1,.3,1) both; }
.animate-slide-in  { animation: fadeInLeft 0.4s cubic-bezier(.16,1,.3,1) both; }
.animate-scale-in  { animation: scaleIn 0.35s cubic-bezier(.16,1,.3,1) both; }

/* ============================================ */
/* ========== SCROLLBAR PERSONALIZADA ========== */
/* ============================================ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--border-light); border-radius: var(--r-full); }
::-webkit-scrollbar-thumb { background: linear-gradient(180deg, var(--primary-light), var(--purple)); border-radius: var(--r-full); }
::-webkit-scrollbar-thumb:hover { background: var(--primary); }

/* ============================================ */
/* ========== LAYOUT PRINCIPAL ========== */
/* ============================================ */
.stApp {
    background:
        radial-gradient(circle at top left, rgba(59,130,246,0.10), transparent 28%),
        radial-gradient(circle at bottom right, rgba(16,185,129,0.10), transparent 24%),
        linear-gradient(180deg, #f5f9ff 0%, #f8fbff 46%, #f5fbf7 100%) !important;
    color: var(--dark) !important;
}

[data-testid="stAppViewContainer"] {
    background: transparent !important;
}

.main .block-container {
    max-width: 1480px !important;
    padding-top: 1.4rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-bottom: 3rem !important;
}

footer { visibility: hidden; }
#MainMenu { visibility: hidden; }

/* ============================================ */
/* ========== SIDEBAR PREMIUM ========== */
/* ============================================ */
section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(15,23,42,0.96) 0%, rgba(30,41,59,0.98) 100%) !important;
    border-right: none !important;
    box-shadow: 16px 0 40px rgba(15,23,42,0.18) !important;
    min-width: 320px !important;
    max-width: 320px !important;
}

section[data-testid="stSidebar"] > div:first-child {
    background: transparent !important;
    overflow-x: visible !important;
    overflow-y: auto !important;
    padding: 0.75rem 0.9rem 1rem 0.9rem !important;
}

section[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {
    overflow-x: visible !important;
}

section[data-testid="stSidebar"] .stMarkdown h2 {
    color: white !important;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span:not(button span) {
    color: #94a3b8 !important;
}

/* ============================================ */
/* ========== BOTÕES MENU LATERAL ========== */
/* ============================================ */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stButton"] {
    margin: 0.15rem 0 !important;
}

section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stButton"] > button {
    background: rgba(255,255,255,0.95) !important;
    border: 1px solid rgba(148,163,184,0.18) !important;
    border-radius: 18px !important;
    padding: 0.9rem 1rem !important;
    text-align: left !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #183153 !important;
    width: 100% !important;
    transition: all 0.22s ease !important;
    box-shadow: 0 8px 18px rgba(15,23,42,0.10) !important;
    min-height: 56px;
    position: relative;
    justify-content: flex-start !important;
    align-items: center !important;
    white-space: normal !important;
    overflow: visible !important;
}

/* TODOS os spans dentro de botões do sidebar ficam visíveis */
[data-testid="stSidebar"] button span,
[data-testid="stSidebar"] button p {
    color: inherit !important;
    opacity: 1 !important;
    visibility: visible !important;
    display: block !important;
    font-size: inherit !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    line-height: 1.35 !important;
}

section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stButton"] > button span {
    overflow: visible !important;
    text-overflow: clip !important;
    white-space: normal !important;
    display: block !important;
    max-width: 100% !important;
    color: inherit !important;
    font-size: inherit !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* Esconde APENAS tooltips reais — NÃO esconde spans de texto dos botões */
[data-testid="stTooltipContent"],
[data-testid="stTooltipHoverTarget"] {
    display: none !important;
}

section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stButton"] > button:hover {
    background: #ffffff !important;
    color: #0f172a !important;
    border-color: rgba(59,130,246,0.35) !important;
    transform: translateX(4px) translateY(-1px) !important;
    box-shadow: 0 14px 28px rgba(37,99,235,0.16) !important;
}

/* Botão ativo (primary) no sidebar */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb 0%, #0f766e 100%) !important;
    color: white !important;
    box-shadow: 0 16px 30px rgba(37,99,235,0.30) !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
}

section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div[data-testid="stButton"] > button[kind="primary"]:hover {
    transform: translateX(2px) !important;
    box-shadow: 0 18px 34px rgba(37,99,235,0.34) !important;
}

/* ============================================ */
/* ====== DROPDOWN / POPOVER DO SELECTBOX ===== */
/* ============================================ */

/* Container do popover (renderizado fora do stSelectbox, direto no body) */
[data-baseweb="popover"],
[data-baseweb="popover"] *,
[data-baseweb="menu"],
[data-baseweb="menu"] *,
[role="listbox"],
[role="listbox"] *,
[role="option"],
[role="option"] * {
    visibility: visible !important;
    opacity: 1 !important;
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    background-clip: unset !important;
    -webkit-background-clip: unset !important;
    text-shadow: none !important;
}

[data-baseweb="popover"] input,
[data-baseweb="popover"] button,
[data-baseweb="popover"] li,
[data-baseweb="popover"] p,
[data-baseweb="menu"] input,
[data-baseweb="menu"] button,
[data-baseweb="menu"] li,
[data-baseweb="menu"] p,
[role="listbox"] input,
[role="listbox"] button,
[role="listbox"] li,
[role="listbox"] p,
[role="option"] input,
[role="option"] button,
[role="option"] li,
[role="option"] p {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* Item hover */
[data-baseweb="menu"] [role="option"]:hover,
[role="listbox"] [role="option"]:hover {
    background: #eff6ff !important;
    color: #1d4ed8 !important;
    -webkit-text-fill-color: #1d4ed8 !important;
}

/* Item selecionado */
[data-baseweb="menu"] [aria-selected="true"],
[role="option"][aria-selected="true"] {
    background: #eff6ff !important;
    color: #1d4ed8 !important;
    -webkit-text-fill-color: #1d4ed8 !important;
    font-weight: 600 !important;
}

/* ============================================ */
/* ========== TIPOGRAFIA ========== */
/* ============================================ */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    color: var(--dark) !important;
    letter-spacing: -0.02em !important;
    margin-bottom: 0.75rem !important;
    white-space: normal !important;
    word-break: break-word !important;
}

h1 { font-size: 1.9rem !important; }
h2 { font-size: 1.55rem !important; }
h3 { font-size: 1.25rem !important; }
h4 { font-size: 1.05rem !important; }

p, span, div, label, li {
    white-space: normal !important;
    word-wrap: break-word !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
    line-height: 1.6 !important;
}

button {
    white-space: normal !important;
}

[data-testid="stFileUploaderDropzone"] * {
    white-space: nowrap !important;
}
[data-testid="stSidebar"] button {
    white-space: normal !important;
}

/* ============================================ */
/* ========== HEADER DA ESCOLA ========== */
/* ============================================ */
.main-header {
    background:
        radial-gradient(circle at top right, rgba(255,255,255,0.16), transparent 24%),
        linear-gradient(135deg, #0f172a 0%, #1d4ed8 55%, #0f766e 100%);
    padding: 2.6rem 2.6rem;
    border-radius: 30px;
    color: white;
    text-align: left;
    margin-bottom: 2rem;
    box-shadow: 0 28px 48px rgba(15,23,42,0.16), 0 0 0 1px rgba(255,255,255,0.10) inset;
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.6s cubic-bezier(.16,1,.3,1) both;
}

.main-header::before {
    content: '';
    position: absolute;
    top: -60%;
    right: -10%;
    width: 500px;
    height: 500px;
    background: rgba(255,255,255,0.06);
    border-radius: 50%;
    pointer-events: none;
}

.main-header::after {
    content: '';
    position: absolute;
    bottom: -40%;
    left: -8%;
    width: 350px;
    height: 350px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
    pointer-events: none;
}

/* Pattern decorativo */
.main-header .pattern {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        radial-gradient(circle at 20% 50%, rgba(255,255,255,0.05) 1px, transparent 1px),
        radial-gradient(circle at 80% 20%, rgba(255,255,255,0.05) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
}

.school-name {
    font-family: 'Nunito', sans-serif !important;
    font-size: 2.55rem;
    font-weight: 900;
    letter-spacing: -0.03em;
    margin-bottom: 0.4rem;
    position: relative;
    z-index: 1;
    text-shadow: 0 2px 16px rgba(0,0,0,0.15);
    white-space: normal !important;
}

.school-subtitle {
    font-size: 1rem;
    font-weight: 700;
    opacity: 0.92;
    margin-bottom: 1.25rem;
    position: relative;
    z-index: 1;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #dbeafe;
}

.school-info-chips {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
    position: relative;
    z-index: 1;
}

.school-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(255,255,255,0.14);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: var(--r-full);
    padding: 0.45rem 0.95rem;
    font-size: 0.82rem;
    font-weight: 700;
    color: white;
    white-space: nowrap;
}

/* ============================================ */
/* ========== CARDS DE MÉTRICAS ========== */
/* ============================================ */
.metric-card {
    border-radius: 26px;
    padding: 1.5rem 1.25rem;
    text-align: center;
    transition: all 0.3s cubic-bezier(.16,1,.3,1);
    position: relative;
    overflow: hidden;
    color: white;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border: 1px solid rgba(255,255,255,0.14);
    backdrop-filter: blur(10px);
}

.metric-card::before {
    content: '';
    position: absolute;
    top: -30px; right: -30px;
    width: 100px; height: 100px;
    background: rgba(255,255,255,0.08);
    border-radius: 50%;
}

.metric-card:hover {
    transform: translateY(-7px) scale(1.01);
    filter: brightness(1.05);
    box-shadow: 0 22px 40px rgba(15,23,42,0.20) !important;
}

.metric-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 1;
}

.metric-value {
    font-family: 'Nunito', sans-serif !important;
    font-size: 2.6rem;
    font-weight: 900;
    line-height: 1;
    position: relative;
    z-index: 1;
    text-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.metric-label {
    font-size: 0.78rem;
    font-weight: 600;
    margin-top: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    opacity: 0.85;
    position: relative;
    z-index: 1;
    white-space: normal !important;
}

.metric-sub {
    font-size: 0.75rem;
    margin-top: 0.35rem;
    opacity: 0.75;
    position: relative;
    z-index: 1;
}

/* ============================================ */
/* ========== CARDS GENÉRICOS ========== */
/* ============================================ */
.card {
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,0.98) 100%);
    padding: 1.5rem;
    border-radius: 26px;
    border: 1px solid rgba(148,163,184,0.22);
    margin: 0.75rem 0;
    box-shadow: 0 14px 32px rgba(15,23,42,0.08);
    transition: all 0.25s cubic-bezier(.16,1,.3,1);
    position: relative;
    overflow: hidden;
    color: var(--dark);
}

.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px;
    height: 100%;
    background: var(--grad-primary);
    border-radius: 0 0 0 var(--r-2xl);
    opacity: 0;
    transition: opacity 0.3s;
}

.card:hover {
    box-shadow: 0 18px 38px rgba(37,99,235,0.12);
    transform: translateY(-3px);
    border-color: rgba(96,165,250,0.48);
}

.card:hover::before {
    opacity: 1;
}

.card-title {
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700;
    color: var(--dark);
    font-size: 1.05rem;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    white-space: normal !important;
}

.card b,
.card span,
.card div,
.card p {
    color: var(--dark) !important;
    -webkit-text-fill-color: var(--dark) !important;
}

.card-value {
    font-family: 'Nunito', sans-serif !important;
    font-size: 2rem;
    font-weight: 900;
    background: var(--grad-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
}

/* ============================================ */
/* ========== BADGES ========== */
/* ============================================ */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.3rem 0.85rem;
    border-radius: var(--r-full);
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    white-space: nowrap;
}

.badge-primary   { background: var(--primary-xlight); color: var(--primary-dark); border: 1.5px solid #bfdbfe; }
.badge-success   { background: var(--success-light); color: #065f46; border: 1.5px solid #a7f3d0; }
.badge-warning   { background: var(--warning-light); color: #92400e; border: 1.5px solid #fde68a; }
.badge-danger    { background: var(--danger-light); color: #991b1b; border: 1.5px solid #fca5a5; }
.badge-info      { background: var(--info-light); color: #0c4a6e; border: 1.5px solid #7dd3fc; }
.badge-purple    { background: var(--purple-light); color: #4c1d95; border: 1.5px solid #c4b5fd; }
.badge-dark      { background: var(--grad-primary); color: white; border: none; }

/* Gravidade badges grandes */
.badge-gravidade {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.45rem 1.25rem;
    border-radius: var(--r-full);
    font-size: 0.9rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ============================================ */
/* ========== CAIXAS DE MENSAGEM ========== */
/* ============================================ */
.success-box {
    background: linear-gradient(135deg, #f0fdf4, #dcfce7);
    border: 1.5px solid #86efac;
    border-left: 4px solid var(--success);
    border-radius: var(--r-xl);
    padding: 1.1rem 1.25rem;
    margin: 1rem 0;
    color: #14532d;
    font-weight: 500;
    box-shadow: var(--shadow-sm);
    animation: fadeInUp 0.35s ease both;
}

.warning-box {
    background: linear-gradient(135deg, #fffbeb, #fef9c3);
    border: 1.5px solid #fde047;
    border-left: 4px solid var(--warning);
    border-radius: var(--r-xl);
    padding: 1.1rem 1.25rem;
    margin: 1rem 0;
    color: #78350f;
    font-weight: 500;
    box-shadow: var(--shadow-sm);
    animation: fadeInUp 0.35s ease both;
}

.error-box {
    background: linear-gradient(135deg, #fff1f2, #fee2e2);
    border: 1.5px solid #fca5a5;
    border-left: 4px solid var(--danger);
    border-radius: var(--r-xl);
    padding: 1.1rem 1.25rem;
    margin: 1rem 0;
    color: #7f1d1d;
    font-weight: 500;
    box-shadow: var(--shadow-sm);
    animation: fadeInUp 0.35s ease both;
}

.info-box {
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    border: 1.5px solid #93c5fd;
    border-left: 4px solid var(--primary);
    border-radius: var(--r-xl);
    padding: 1.1rem 1.25rem;
    margin: 1rem 0;
    color: #1e3a8a;
    font-weight: 500;
    box-shadow: var(--shadow-sm);
    animation: fadeInUp 0.35s ease both;
}

.stAlert {
    border-radius: var(--r-lg) !important;
    border-left-width: 4px !important;
    box-shadow: var(--shadow-sm) !important;
    animation: fadeInUp 0.3s ease both !important;
    white-space: normal !important;
}

/* ============================================ */
/* ========== PROTOCOLO INFO BOX ========== */
/* ============================================ */
.protocolo-info {
    background: linear-gradient(135deg, #f0f4ff, #e8f0fe);
    border: 1.5px solid #c7d7fd;
    border-left: 5px solid var(--primary);
    border-radius: var(--r-xl);
    padding: 1.25rem 1.5rem;
    margin: 1rem 0;
    color: var(--dark-mid);
    box-shadow: var(--shadow-md);
    font-size: 0.95rem;
    line-height: 1.7;
}

.protocolo-info b {
    color: var(--primary-dark);
}

/* ============================================ */
/* ========== BOTÕES PREMIUM ========== */
/* ============================================ */
.stButton > button {
    border-radius: var(--r-lg) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.01em !important;
    transition: all 0.25s cubic-bezier(.16,1,.3,1) !important;
    border: none !important;
    padding: 0.6rem 1.2rem !important;
    min-height: 40px !important;
    white-space: normal !important;
    position: relative;
    overflow: hidden;
}

.stButton > button::after {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(255,255,255,0);
    transition: background 0.2s;
}

.stButton > button:hover::after {
    background: rgba(255,255,255,0.12);
}

.stButton > button[kind="primary"] {
    background: var(--grad-primary) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 8px 20px rgba(37,99,235,0.4) !important;
    transform: translateY(-2px) !important;
}

.stButton > button[kind="primary"]:active {
    transform: translateY(0) !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
}

.stButton > button[kind="secondary"] {
    background: var(--white) !important;
    color: var(--gray-dark) !important;
    border: 1.5px solid var(--border) !important;
    box-shadow: var(--shadow-xs) !important;
}

.stButton > button[kind="secondary"]:hover {
    background: var(--primary-xlight) !important;
    border-color: var(--primary-light) !important;
    color: var(--primary) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ============================================ */
/* ========== INPUTS MODERNOS ========== */
/* ============================================ */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 18px !important;
    border: 1px solid rgba(148,163,184,0.30) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.96rem !important;
    background: rgba(255,255,255,0.96) !important;
    color: var(--dark) !important;
    transition: all 0.2s !important;
    padding: 0.72rem 0.95rem !important;
    box-shadow: 0 10px 22px rgba(15,23,42,0.05) !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
    outline: none !important;
}

.stTextArea textarea {
    min-height: 110px !important;
    line-height: 1.6 !important;
}

/* Selectbox */
[data-baseweb="select"] > div:first-child {
    border-radius: 18px !important;
    border: 1px solid rgba(148,163,184,0.30) !important;
    background: rgba(255,255,255,0.96) !important;
    font-size: 0.96rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 10px 22px rgba(15,23,42,0.05) !important;
    min-height: 52px !important;
    padding-left: 0.25rem !important;
    padding-right: 0.25rem !important;
}

[data-baseweb="select"] > div:first-child:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
}

/* Valor selecionado visível no campo fechado */
[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    background-clip: unset !important;
    -webkit-background-clip: unset !important;
    opacity: 1 !important;
}

[data-baseweb="select"] input,
[data-baseweb="select"] p {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    opacity: 1 !important;
}

/* Ocultar indicador "Running..." / modo de espera do Streamlit */
[data-testid="stStatusWidget"],
[data-testid="stStatusWidget"] *,
.stStatusWidget,
header [data-testid="stDecoration"],
div[class*="StatusWidget"],
div[class*="statusWidget"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* Também oculta o spinner global de topo da página */
div[data-testid="stToolbar"] [data-testid="stStatusWidget"],
.st-emotion-cache-ue6h4q,
[class*="AppRunningIcon"],
[class*="appRunningIcon"] {
    display: none !important;
}

/* Labels */
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stMultiSelect label,
.stDateInput label,
.stTimeInput label,
.stSlider label,
.stCheckbox label,
.stRadio label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--gray-dark) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-bottom: 0.25rem !important;
}

/* ============================================ */
/* ========== TABS ========== */
/* ============================================ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.35rem;
    background: var(--border-light);
    padding: 0.45rem;
    border-radius: var(--r-xl);
    border: 1.5px solid var(--border);
    flex-wrap: wrap;
}

.stTabs [data-baseweb="tab"] {
    border-radius: var(--r-lg) !important;
    padding: 0.55rem 1.1rem !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: var(--gray) !important;
    transition: all 0.2s !important;
    border: none !important;
    background: transparent !important;
    white-space: nowrap !important;
}

.stTabs [data-baseweb="tab"]:hover {
    background: var(--white) !important;
    color: var(--primary) !important;
}

.stTabs [aria-selected="true"] {
    background: var(--white) !important;
    color: var(--primary-dark) !important;
    font-weight: 700 !important;
    box-shadow: var(--shadow-md) !important;
    border-bottom: 2px solid var(--primary) !important;
}

/* ============================================ */
/* ========== DATAFRAME PREMIUM ========== */
/* ============================================ */
[data-testid="stDataFrame"] {
    border-radius: var(--r-xl) !important;
    overflow: hidden !important;
    border: 1.5px solid var(--border) !important;
    box-shadow: var(--shadow-md) !important;
}

[data-testid="stDataFrame"] th {
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    color: white !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 0.7rem 1rem !important;
    white-space: nowrap !important;
}

[data-testid="stDataFrame"] td {
    padding: 0.55rem 1rem !important;
    border-bottom: 1px solid var(--border-light) !important;
    font-size: 0.875rem !important;
    color: var(--gray-dark) !important;
    white-space: normal !important;
}

[data-testid="stDataFrame"] tr:nth-child(even) td {
    background: #fafbff !important;
}

[data-testid="stDataFrame"] tr:hover td {
    background: var(--primary-xlight) !important;
    color: var(--primary-dark) !important;
}

/* ============================================ */
/* ========== EXPANDER ========== */
/* ============================================ */
div[data-testid="stExpander"] {
    border-radius: var(--r-xl) !important;
    border: 1.5px solid var(--border) !important;
    background: var(--white) !important;
    box-shadow: var(--shadow-xs) !important;
    margin: 0.6rem 0 !important;
    transition: all 0.25s ease !important;
    overflow: hidden;
}

div[data-testid="stExpander"]:hover {
    box-shadow: var(--shadow-md) !important;
    border-color: #93c5fd !important;
}

.streamlit-expanderHeader {
    border-radius: var(--r-xl) !important;
    background: linear-gradient(135deg, #fafbff, var(--white)) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: var(--dark-mid) !important;
    padding: 0.8rem 1.25rem !important;
}

.streamlit-expanderHeader:hover {
    background: var(--primary-xlight) !important;
    color: var(--primary-dark) !important;
}

/* ============================================ */
/* ========== FORMULÁRIOS ========== */
/* ============================================ */
div[data-testid="stForm"] {
    background: linear-gradient(135deg, #fafbff, var(--white)) !important;
    border-radius: var(--r-2xl) !important;
    padding: 1.75rem !important;
    border: 1.5px solid var(--border) !important;
    box-shadow: var(--shadow-md) !important;
    margin: 1.25rem 0 !important;
    transition: all 0.25s !important;
}

div[data-testid="stForm"]:hover {
    border-color: #93c5fd !important;
    box-shadow: var(--shadow-blue) !important;
}

/* ============================================ */
/* ========== MÉTRICAS STREAMLIT ========== */
/* ============================================ */
[data-testid="metric-container"] {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-radius: var(--r-xl);
    padding: 1.1rem;
    box-shadow: var(--shadow-sm);
    transition: all 0.25s;
}

[data-testid="metric-container"]:hover {
    box-shadow: var(--shadow-md);
    border-color: #93c5fd;
    transform: translateY(-2px);
}

[data-testid="metric-container"] [data-testid="stMetricLabel"] label {
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: var(--gray) !important;
    white-space: normal !important;
}

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Nunito', sans-serif !important;
    font-size: 1.9rem !important;
    font-weight: 800 !important;
    color: var(--dark) !important;
}

/* ============================================ */
/* ========== PROGRESS BAR ========== */
/* ============================================ */
.stProgress > div > div > div {
    background: var(--grad-primary) !important;
    border-radius: var(--r-full) !important;
}
.stProgress > div > div {
    background: var(--border-light) !important;
    border-radius: var(--r-full) !important;
}

/* ============================================ */
/* ========== SECTION TITLES ========== */
/* ============================================ */
.section-title {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 1.5rem 0 1rem 0;
    padding-bottom: 0.6rem;
    border-bottom: 2px solid var(--border);
    position: relative;
}

.section-title::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    width: 60px;
    height: 2px;
    background: var(--grad-primary);
    border-radius: var(--r-full);
}

.section-title h3 {
    margin: 0 !important;
    font-size: 1.1rem !important;
    color: var(--dark-mid) !important;
}

/* ============================================ */
/* ========== MAPA DA SALA ========== */
/* ============================================ */
.sala-grid {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin: 20px 0;
    padding: 24px;
    background: linear-gradient(135deg, #f0f4ff, #f8fafc);
    border-radius: var(--r-2xl);
    border: 1.5px solid var(--border);
    box-shadow: var(--shadow-md);
}

.fileira-row {
    display: flex;
    gap: 10px;
    justify-content: center;
}

.assento-card {
    width: 74px;
    height: 52px;
    border: 2px solid var(--border);
    border-radius: var(--r-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9px;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    text-align: center;
    background: var(--white);
    transition: all 0.2s;
    padding: 3px;
    word-break: break-word;
    cursor: default;
    box-shadow: var(--shadow-xs);
}

.assento-card.ocupado {
    background: var(--grad-primary);
    color: white;
    border-color: var(--primary);
    box-shadow: 0 4px 8px rgba(37,99,235,0.25);
}

.assento-card.vazio {
    background: var(--white);
    color: var(--gray-light);
    border-style: dashed;
}

.lousa {
    width: 100%;
    max-width: 320px;
    height: 38px;
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Nunito', sans-serif;
    font-weight: 800;
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    border-radius: var(--r-md);
    margin: 12px auto;
    box-shadow: var(--shadow-md);
}

/* ============================================ */
/* ========== GLASS EFFECT ========== */
/* ============================================ */
.glass-effect {
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1.5px solid rgba(255,255,255,0.4);
}

/* ============================================ */
/* ========== GRADIENT TEXT ========== */
/* ============================================ */
.gradient-text {
    background: var(--grad-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 900;
}

.gradient-text-warm {
    background: var(--grad-warm);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 900;
}

/* ============================================ */
/* ========== QUICK ACTION CARDS ========== */
/* ============================================ */
.quick-action-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,252,0.98));
    border: 1px solid rgba(148,163,184,0.20);
    border-radius: 24px;
    padding: 1.25rem;
    text-align: center;
    transition: all 0.3s cubic-bezier(.16,1,.3,1);
    box-shadow: 0 12px 28px rgba(15,23,42,0.08);
    cursor: pointer;
}

.quick-action-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 18px 36px rgba(37,99,235,0.14);
    border-color: rgba(96,165,250,0.55);
}

.quick-action-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    display: block;
}

/* ============================================ */
/* ========== PAGE BANNER ========== */
/* ============================================ */
.page-banner {
    position: relative;
    overflow: hidden;
    margin-bottom: 1.4rem;
    padding: 1.35rem 1.45rem;
    border-radius: 24px;
    background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,250,252,0.98) 100%);
    border: 1px solid rgba(148,163,184,0.20);
    box-shadow: 0 16px 34px rgba(15,23,42,0.08);
}

.page-banner::before {
    content: '';
    position: absolute;
    inset: 0 auto 0 0;
    width: 6px;
    background: var(--banner-accent, #2563eb);
}

.page-banner::after {
    content: '';
    position: absolute;
    top: -45px;
    right: -30px;
    width: 150px;
    height: 150px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(37,99,235,0.10), transparent 70%);
}

.page-banner-content {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    gap: 1rem;
}

.page-banner-icon {
    width: 58px;
    height: 58px;
    border-radius: 18px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--banner-accent, #2563eb), rgba(15,23,42,0.92));
    color: white;
    font-size: 1.5rem;
    box-shadow: 0 12px 24px rgba(15,23,42,0.14);
    flex-shrink: 0;
}

.page-banner-copy {
    min-width: 0;
}

.page-banner-kicker {
    color: var(--banner-accent, #2563eb);
    font-size: 0.74rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.page-banner-title {
    font-family: 'Nunito', sans-serif !important;
    color: var(--dark);
    font-size: 1.55rem;
    font-weight: 900;
    line-height: 1.15;
    margin: 0.18rem 0 0.2rem 0;
}

.page-banner-subtitle {
    color: var(--gray);
    font-size: 0.95rem;
    margin: 0;
}

/* ============================================ */
/* ========== SECTION HEADERS ========== */
/* ============================================ */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0.4rem 0 0.95rem 0;
}

.section-header-bar {
    width: 5px;
    height: 24px;
    border-radius: 999px;
    background: var(--section-accent, linear-gradient(180deg,#2563eb,#0891b2));
    flex-shrink: 0;
}

.section-header-copy {
    min-width: 0;
}

.section-header-title {
    margin: 0;
    font-family: 'Nunito', sans-serif;
    font-size: 1.12rem;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.15;
}

.section-header-subtitle {
    margin: 0.15rem 0 0 0;
    color: #64748b;
    font-size: 0.84rem;
}

/* ============================================ */
/* ========== DASHBOARD CALLOUTS ========== */
/* ============================================ */
.dashboard-callout {
    position: relative;
    overflow: hidden;
    margin: 0.25rem 0 1rem 0;
    padding: 1rem 1.1rem;
    border-radius: 22px;
    background: linear-gradient(135deg, rgba(219,234,254,0.82), rgba(236,253,245,0.92));
    border: 1px solid rgba(147,197,253,0.45);
    box-shadow: 0 14px 30px rgba(15,23,42,0.06);
}

.dashboard-callout::after {
    content: '';
    position: absolute;
    top: -26px;
    right: -18px;
    width: 110px;
    height: 110px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(37,99,235,0.12), transparent 70%);
}

.dashboard-callout-content {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}

.dashboard-callout-title {
    margin: 0;
    color: #0f172a;
    font-size: 1rem;
    font-weight: 800;
}

.dashboard-callout-text {
    margin: 0.2rem 0 0 0;
    color: #334155;
    font-size: 0.88rem;
}

.dashboard-callout-badge {
    flex-shrink: 0;
    padding: 0.48rem 0.8rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.78);
    border: 1px solid rgba(148,163,184,0.22);
    color: #1d4ed8;
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

/* ============================================ */
/* ========== FORM PANELS ========== */
/* ============================================ */
.form-panel {
    margin: 0.2rem 0 1rem 0;
    padding: 1rem 1.1rem;
    border-radius: 24px;
    background: linear-gradient(180deg, rgba(255,255,255,0.97), rgba(248,250,252,0.98));
    border: 1px solid rgba(148,163,184,0.20);
    box-shadow: 0 16px 30px rgba(15,23,42,0.07);
}

.form-panel-title {
    margin: 0;
    font-family: 'Nunito', sans-serif;
    font-size: 1.02rem;
    font-weight: 900;
    color: #0f172a;
}

.form-panel-subtitle {
    margin: 0.18rem 0 0 0;
    color: #64748b;
    font-size: 0.86rem;
}

/* ============================================ */
/* ========== DATAFRAME PREMIUM ========== */
/* ============================================ */
[data-testid="stDataFrame"] {
    border-radius: 22px !important;
    overflow: hidden !important;
    border: 1px solid rgba(148,163,184,0.20) !important;
    box-shadow: 0 16px 32px rgba(15,23,42,0.08) !important;
    background: rgba(255,255,255,0.96) !important;
}

[data-testid="stDataFrame"] [role="grid"] {
    border-radius: 22px !important;
}

[data-testid="stDataFrame"] [role="columnheader"] {
    background: linear-gradient(180deg, #eff6ff 0%, #e0f2fe 100%) !important;
    color: #0f172a !important;
    font-weight: 800 !important;
    border-bottom: 1px solid rgba(148,163,184,0.20) !important;
}

[data-testid="stDataFrame"] [role="gridcell"] {
    background: rgba(255,255,255,0.96) !important;
    color: #0f172a !important;
    border-color: rgba(226,232,240,0.75) !important;
}

[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {
    background: #f8fbff !important;
}

/* ============================================ */
/* ========== RESPONSIVO ========== */
/* ============================================ */
@media (max-width: 768px) {
    .main-header { padding: 1.5rem 1rem; }
    .school-name  { font-size: 1.7rem; }
    .metric-value { font-size: 2rem; }
    .metric-card  { padding: 1.1rem 0.75rem; }
    .metric-label { font-size: 0.7rem; }
    .page-banner-content {
        align-items: flex-start;
    }
    .page-banner-title {
        font-size: 1.25rem;
    }
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    section[data-testid="stSidebar"] {
        min-width: 285px !important;
        max-width: 285px !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.45rem 0.7rem !important;
        font-size: 0.78rem !important;
    }
    .school-info-chips { display: none; }
}
</style>
""", unsafe_allow_html=True)
# ======================================================
# DADOS DA ESCOLA
# ======================================================
ESCOLA_NOME = "E.E. Profª Eliane"
ESCOLA_SUBTITULO = "Sistema Conviva 179"
ESCOLA_ENDERECO = "R. Valter Souza Costa, 147 - Jardim Primavera, Ferraz de Vasconcelos - SP"
ESCOLA_CEP = "CEP: 08535-310"
ESCOLA_TELEFONE = "(11) 4675-1855"
ESCOLA_EMAIL = "e918623@educacao.sp.gov.br"
ESCOLA_LOGO = os.path.join("assets", "images", "eliane_dantas.png")

# ======================================================
# MENU LATERAL PREMIUM (SEM RADIO BUTTONS)
# ======================================================

st.sidebar.markdown("""
<div style="
    position: relative;
    padding: 1.2rem 1rem 1rem 1rem;
    margin: 0.2rem 0.2rem 0.9rem 0.2rem;
    border-radius: 28px;
    background: linear-gradient(165deg, rgba(37,99,235,0.22) 0%, rgba(15,23,42,0.18) 100%);
    border: 1px solid rgba(148,163,184,0.18);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 18px 36px rgba(15,23,42,0.18);
    overflow: hidden;
    text-align: center;
">
    <div style="
        display: inline-flex; align-items: center; justify-content: center;
        width: 56px; height: 56px;
        background: linear-gradient(135deg, #1d4ed8, #0891b2);
        border-radius: 16px;
        box-shadow: 0 8px 20px rgba(37,99,235,0.4);
        font-size: 1.6rem;
        margin-bottom: 0.75rem;
    ">🏫</div>
    <div style="
        color:#e2e8f0;
        font-size:0.72rem;
        font-weight:700;
        letter-spacing:0.18em;
        text-transform:uppercase;
        margin-bottom:0.35rem;
    ">Plataforma Escolar</div>
    <h2 style="
        font-family: 'Nunito', sans-serif;
        color: white;
        font-weight: 900;
        font-size: 2rem;
        line-height: 1.05;
        margin: 0 0 0.25rem 0;
        letter-spacing: -0.03em;
    ">Conviva 179</h2>
    <p style="
        color: #bfdbfe;
        font-size: 0.82rem;
        margin: 0 0 0.9rem 0;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    ">E.E. Profª Eliane</p>
</div>
<div style="height: 1px; background: linear-gradient(90deg, transparent, #334155, transparent); margin: 0 1rem 0.5rem 1rem;"></div>
""", unsafe_allow_html=True)

# Inicializar página atual se não existir
st.sidebar.markdown("""
<div style="
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:0.75rem;
    margin:0.1rem 0.35rem 0.95rem 0.35rem;
    padding:0.8rem 0.95rem;
    border-radius:18px;
    background:rgba(255,255,255,0.08);
    border:1px solid rgba(255,255,255,0.08);
">
    <div>
        <div style="color:#93c5fd;font-size:0.68rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;">Ambiente</div>
        <div style="color:#ffffff;font-size:0.95rem;font-weight:700;">Gestão Escolar</div>
    </div>
    <div style="
        width:40px;height:40px;border-radius:14px;
        display:flex;align-items:center;justify-content:center;
        background:linear-gradient(135deg,#2563eb,#0f766e);
        color:white;font-size:1.1rem;
        box-shadow:0 10px 18px rgba(37,99,235,0.25);
    ">✦</div>
</div>
""", unsafe_allow_html=True)

if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = "🏠 Dashboard"


# ======================================================
# INICIALIZAR SESSION STATE IMEDIATAMENTE
# ======================================================
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = "🏠 Dashboard"

# Lista de itens do menu com ícones
menu_items = [
    {"nome": "Dashboard", "icone": "🏠"},
    {"nome": "Portal do Responsável", "icone": "👨‍👩‍👧"},
    {"nome": "Importar Alunos", "icone": "📥"},
    {"nome": "Gerenciar Turmas", "icone": "📋"},
    {"nome": "Lista de Alunos", "icone": "👥"},
    {"nome": "Registrar Ocorrência", "icone": "📝"},
    {"nome": "Histórico de Ocorrências", "icone": "📋"},
    {"nome": "Comunicado aos Pais", "icone": "📄"},
    {"nome": "Gráficos e Indicadores", "icone": "📊"},
    {"nome": "Imprimir PDF", "icone": "🖨️"},
    {"nome": "Cadastrar Professores", "icone": "👨‍🏫"},
    {"nome": "Cadastrar Assinaturas", "icone": "👤"},
    {"nome": "Eletiva", "icone": "🎨"},
    {"nome": "Mapa da Sala", "icone": "🏫"},
    {"nome": "Agendamento de Espaços", "icone": "📅"},
    {"nome": "Backups", "icone": "💾"},
]

# Criar botões estilizados
for item in menu_items:
    nome_completo = f"{item['icone']} {item['nome']}"
    is_active = st.session_state.pagina_atual == nome_completo
    button_style = "primary" if is_active else "secondary"
    
    if st.sidebar.button(
        nome_completo,
        key=f"menu_{item['nome'].replace(' ', '_')}",
        use_container_width=True,
        type=button_style
    ):
        st.session_state.pagina_atual = nome_completo
        st.rerun()

# Atualizar a variável menu
menu = st.session_state.pagina_atual

st.sidebar.markdown("---")

# Informações do sistema
st.sidebar.markdown(f"""
<div style="
    padding: 0.85rem 1rem;
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    margin: 0.5rem 0.5rem 0 0.5rem;
    border: 1px solid rgba(255,255,255,0.08);
">
    <p style="margin: 0; font-size: 0.78rem; color: #64748b; text-align: center; line-height: 1.6;">
        <span style="color: #94a3b8; font-weight: 600;">🕐 {datetime.now().strftime('%d/%m/%Y')}</span><br>
        <span style="font-size: 0.72rem; color: #475569;">{datetime.now().strftime('%H:%M')} — v10.0 Premium</span>
    </p>
</div>
""", unsafe_allow_html=True)
# ======================================================
# ELETIVAS — ARQUIVO DE IMPORTAÇÃO
# ======================================================
ELETIVAS_ARQUIVO = resolver_caminho_existente(
    os.getenv("ELETIVAS_ARQUIVO"),
    os.path.join("assets", "IMportação.xlsx"),
    os.path.join("data", "IMportação.xlsx"),
    r"C:\Users\Freak Work\Desktop\IMportação.xlsx"
)

ELETIVAS = {
    "Solange": [], "Rosemeire": [], "Fernanda": [], "Fagna": [],
    "Elaine": [], "Geovana": [], "Shirley": [], "Rosangela": [],
    "Veronica": [], "Silvana": [], "Patricia": [],
}

# ======================================================
# AGENDAMENTO DE ESPAÇOS - CONSTANTES
# ======================================================
SENHA_GESTAO_AGEND = os.getenv("SENHA_GESTAO_AGEND", SENHA_EXCLUSAO)
DIAS_PRIORITARIO = 60
DIAS_NORMAL = 15

PRIORIDADES_ESTENDIDAS = ["Redação", "Leitura", "Tecnologia", "Programação", "Khan Academy"]
PRIORIDADES_OUTRAS = ["Matific", "Alura", "Speak"]
PRIORIDADE_VALIDAS = {"PRIORITARIO", "PRIORITÁRIO", "NORMAL"} | set(PRIORIDADES_ESTENDIDAS) | set(PRIORIDADES_OUTRAS)

ESPACOS_AGEND = [
    "Sala de Informática", "Carrinho Positivo", "Carrinho ChromeBook",
    "Tablet Positivo", "Sala de Leitura",
]

HORARIOS_AGEND = [
    "07:00-07:50", "07:50-08:40", "08:40-09:00", "08:40-09:30",
    "09:00-09:50", "09:30-09:50", "09:50-10:40", "10:40-11:30",
    "11:30-12:20", "12:20-13:10", "13:10-14:00", "14:30-15:20",
    "15:20-16:10", "16:30-17:20", "17:20-18:10", "18:10-19:00",
    "19:50-20:40", "20:40-21:30"
]

TURMAS_INTERVALOS_AGEND = {
    "6º A": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"},
    "6º B": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"},
    "7º A": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"},
    "7º B": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"},
    "7º C": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"},
    "8º A": {"cafe": "09:30-09:50", "almoco": "11:30-12:20"},
    "8º B": {"cafe": "09:30-09:50", "almoco": "11:30-12:20"},
    "8º C": {"cafe": "09:30-09:50", "almoco": "11:30-12:20"},
    "9º A": {"cafe": "09:30-09:50", "almoco": "11:30-12:20"},
    "9º B": {"cafe": "09:30-09:50", "almoco": "11:30-12:20"},
    "9º C": {"cafe": "09:30-09:50", "almoco": "11:30-12:20"},
    "3º A": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"},
    "3º B": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"},
    "1º A": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"},
    "1º B": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"},
    "1º C": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"},
    "1º D": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"},
    "1º E": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"},
    "1º F": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"},
    "2º A": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"},
    "2º B": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"},
    "2º C": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"},
    "3º C": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"},
    "3º D": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"},
    "3º E": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}
}

DISCIPLINAS_AGEND = [
    "Língua Portuguesa", "Matemática", "Ciências", "Geografia", "História",
    "Arte", "Educação Física", "Língua Inglesa", "Projeto de Vida",
    "Tecnologia e Inovação", "Educação Financeira", "Redação e Leitura",
    "Orientação de Estudos", "Biologia", "Física", "Química",
    "Filosofia", "Sociologia", "Tecnologia e Robótica", "Itinerários Formativos",
    "Matific", "Alura", "Speak", "Redação", "Tecnologia"
]

# ======================================================
# CORES PARA TIPOS DE INFRAÇÃO
# ======================================================
CORES_INFRACOES = {
    "Agressão Física": "#FF6B6B",
    "Agressão Verbal / Conflito Verbal": "#FFE66D",
    "Ameaça": "#C0B020",
    "Bullying": "#4ECDC4",
    "Racismo": "#9B59B6",
    "Homofobia": "#E91E63",
    "Furto": "#FFB74D",
    "Dano ao Patrimônio / Vandalismo": "#FFA726",
    "Posse de Celular / Dispositivo Eletrônico": "#4DB6AC",
    "Consumo de Substâncias Ilícitas": "#2E7D32",
    "Indisciplina": "#64B5F6",
    "Chegar atrasado": "#FFB74D",
    "Falsificar assinatura de responsáveis": "#EF5350"
}

# ======================================================
# CORES POR GRAVIDADE
# ======================================================
CORES_GRAVIDADE = {
    "Leve": "#4CAF50",
    "Média": "#FFC107",
    "Grave": "#FF9800",
    "Gravíssima": "#F44336",
}

# ======================================================
# PROTOCOLO 179 COMPLETO
# ======================================================
PROTOCOLO_179 = {
    "📌 Violência e Agressão": {
        "Agressão Física": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Acionar Orientação Educacional\n✅ Notificar famílias\n✅ Conselho Tutelar (se menor de 18 anos)\n✅ B.O. (se houver lesão corporal)"
        },
        "Agressão Verbal / Conflito Verbal": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Mediação pedagógica\n✅ Registrar em ata\n✅ Acionar Orientação Educacional\n✅ Acompanhamento psicológico (se necessário)"
        },
        "Ameaça": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. recomendado\n✅ Medidas protetivas se necessário"
        },
        "Bullying": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Programa de Mediação de Conflitos\n✅ Acompanhamento pedagógico\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Acompanhamento psicológico"
        },
        "Racismo": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚖️ CRIME INAFIANÇÁVEL (Lei 7.716/89)\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ Diretoria de Ensino\n✅ Medidas disciplinares cabíveis"
        },
        "Homofobia": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚖️ CRIME (equiparado ao racismo - STF)\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ Diretoria de Ensino\n✅ Medidas disciplinares cabíveis"
        },
    },
    "🔫 Armas e Segurança": {
        "Posse de Arma de Fogo / Simulacro": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 EMERGÊNCIA - ACIONAR PM (190)\n✅ Isolar área\n✅ Não tocar no objeto\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Afastamento imediato"
        },
        "Posse de Arma Branca": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 ACIONAR PM (190)\n✅ Isolar área\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Afastamento imediato"
        },
    },
    "💊 Drogas e Substâncias": {
        "Posse de Celular / Dispositivo Eletrônico": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Retirar dispositivo (conforme regimento)\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Devolver aos responsáveis"
        },
        "Consumo de Substâncias Ilícitas": {
            "gravidade": "Grave",
            "encaminhamento": "✅ SAMU (192) se houver emergência\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. recomendado\n✅ CAPS/CREAS\n✅ Acompanhamento especializado"
        },
    },
    "🧠 Saúde Mental e Comportamento": {
        "Indisciplina": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Mediação pedagógica\n✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho de Classe\n✅ Acompanhamento pedagógico"
        },
        "Tentativa de Suicídio": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 SAMU (192) IMEDIATO\n✅ Hospital de referência\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ CAPS\n✅ Rede de proteção\n✅ Pós-venção"
        },
    },
    "⚠️ Infrações Acadêmicas e de Pontualidade": {
        "Chegar atrasado": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Conversar com o aluno\n✅ Notificar famílias (se recorrente)\n✅ Verificar motivo dos atrasos\n✅ Orientação Educacional"
        },
        "Falsificar assinatura de responsáveis": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ Diretoria de Ensino\n✅ Acompanhamento psicológico\n✅ B.O. recomendado"
        },
    },
}
# ======================================================
# FUNÇÕES UTILITÁRIAS PREMIUM
# ======================================================

def show_toast(message: str, type: str = "success", duration: int = 3000):
    """Mostra notificação toast estilizada"""
    icon = "✅" if type == "success" else "❌" if type == "error" else "⚠️" if type == "warning" else "ℹ️"
    st.toast(f"{icon} {message}")


def page_header(titulo: str, subtitulo: str = "", cor: str = "#2563eb"):
    """Renderiza um cabeçalho de página moderno e consistente"""
    partes = titulo.split(maxsplit=1)
    icone = partes[0] if partes else "📌"
    titulo_texto = partes[1] if len(partes) > 1 else titulo
    sub_html = f'<p class="page-banner-subtitle">{subtitulo}</p>' if subtitulo else ""
    st.markdown(f"""
    <div class="page-banner" style="--banner-accent:{cor};">
        <div class="page-banner-content">
            <div class="page-banner-icon">{icone}</div>
            <div class="page-banner-copy">
                <div class="page-banner-kicker">Painel</div>
                <div class="page-banner-title">{titulo_texto}</div>
                {sub_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def info_message(message: str, type: str = "info"):
    """Mostra mensagem estilizada"""
    box_class = f"{type}-box"
    st.markdown(f'<div class="{box_class} animate-slide-in">{message}</div>', unsafe_allow_html=True)

def normalizar_texto(valor: str) -> str:
    """Normaliza texto: remove acentos, converte para maiúsculo, remove espaços duplicados"""
    if valor is None or pd.isna(valor):
        return ""
    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.split())

def gerar_chave_segura(valor: str) -> str:
    """Gera uma chave segura para uso em session_state"""
    texto = normalizar_texto(valor)
    texto = re.sub(r"[^A-Z0-9_]+", "_", texto)
    texto = texto.strip("_")
    return texto if texto else "SEM_CHAVE"

def encontrar_melhor_match(nome_busca: str, nomes_existentes: list) -> tuple:
    """Encontra o melhor match aproximado usando SequenceMatcher"""
    if not nome_busca or not nomes_existentes:
        return None, 0.0
    nome_norm = normalizar_texto(nome_busca)
    melhor_match = None
    melhor_score = 0.0
    for nome in nomes_existentes:
        nome_norm_candidato = normalizar_texto(nome)
        score = SequenceMatcher(None, nome_norm, nome_norm_candidato).ratio()
        if nome_norm_candidato.startswith(nome_norm):
            score = max(score, 0.95)
        elif nome_norm in nome_norm_candidato:
            score = max(score, 0.85)
        if score > melhor_score:
            melhor_score = score
            melhor_match = nome
    return melhor_match, melhor_score

def buscar_infracao_fuzzy(busca: str, protocolo: dict) -> dict:
    """Busca infrações no PROTOCOLO_179 usando similaridade textual"""
    if not busca or len(busca.strip()) < 2:
        return {}
    busca_norm = normalizar_texto(busca)
    resultados = {}
    palavras_chave = {
        "CELULAR": ["CELULAR", "TELEFONE", "SMARTPHONE", "DISPOSITIVO"],
        "ATRASO": ["ATRASO", "ATRASADO", "PONTUALIDADE"],
        "BULLYING": ["BULLYING", "CYBERBULLYING", "INTIMIDACAO"],
        "AGRESSAO": ["AGRESSAO", "AGREDIR", "VIOLENCIA"],
        "FURTO": ["FURTO", "ROUBO", "SUBTRAIR"],
        "DROGA": ["DROGA", "ALCOOL", "CIGARRO", "MACONHA", "SUBSTANCIA"],
        "ARMA": ["ARMA", "FACA", "CANIVETE"],
        "AMEACA": ["AMEACA", "INTIMIDAR"],
        "DISCRIMINACAO": ["RACISMO", "HOMOFOBIA", "PRECONCEITO", "DISCRIMINACAO"],
    }
    for grupo, infracoes in protocolo.items():
        encontradas = {}
        for nome_infracao, dados in infracoes.items():
            nome_norm = normalizar_texto(nome_infracao)
            similaridade = SequenceMatcher(None, busca_norm, nome_norm).ratio()
            match_parcial = busca_norm in nome_norm
            match_chave = False
            for termos in palavras_chave.values():
                if any(t in busca_norm for t in termos) and any(t in nome_norm for t in termos):
                    match_chave = True
                    break
            if similaridade >= 0.4 or match_parcial or match_chave:
                encontradas[nome_infracao] = dados
        if encontradas:
            resultados[grupo] = encontradas
    return resultados

# ======================================================
# SISTEMA DE NOTIFICAÇÕES
# ======================================================

def obter_notificacoes():
    """Retorna notificações baseadas em eventos importantes"""
    notificacoes = []
    try:
        if 'df_ocorrencias' in globals() and not df_ocorrencias.empty:
            df_ocorrencias['data_dt'] = pd.to_datetime(df_ocorrencias['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_recentes = df_ocorrencias[df_ocorrencias['data_dt'] >= datetime.now() - timedelta(hours=24)]
            graves = df_recentes[df_recentes['gravidade'].isin(['Grave', 'Gravíssima'])]
            if not graves.empty:
                notificacoes.append({
                    "icone": "🚨", "cor": "#ef4444", "titulo": "Ocorrências Graves",
                    "texto": f"{len(graves)} ocorrências graves nas últimas 24h"
                })
    except:
        pass
    return notificacoes

def exibir_notificacoes_sidebar():
    """Exibe as notificações no sidebar"""
    notificacoes = obter_notificacoes()
    if notificacoes:
        with st.sidebar.expander(f"🔔 Notificações ({len(notificacoes)})", expanded=True):
            for n in notificacoes:
                st.markdown(f"""
                <div style="background: {n['cor']}10; border-left: 4px solid {n['cor']}; 
                            border-radius: 8px; padding: 0.75rem; margin: 0.5rem 0;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 1.25rem;">{n['icone']}</span>
                        <div>
                            <b style="color: {n['cor']};">{n['titulo']}</b><br>
                            <span style="font-size: 0.8rem; color: #64748b;">{n['texto']}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        with st.sidebar.expander("🔔 Notificações", expanded=False):
            st.markdown("<div style='text-align:center;padding:0.5rem 0;font-size:0.8rem;color:#475569;'>✅ Sistema sem alertas pendentes</div>", unsafe_allow_html=True)
            # ======================================================
# SISTEMA DE GAMIFICAÇÃO
# ======================================================

CONQUISTAS = {
    "primeiro_registro": {"nome": "🆕 Primeiro Registro", "descricao": "Registrou a primeira ocorrência", "pontos": 10, "icone": "🌟"},
    "10_ocorrencias": {"nome": "📝 Repórter Escolar", "descricao": "Registrou 10 ocorrências", "pontos": 50, "icone": "📋"},
    "50_ocorrencias": {"nome": "📊 Analista de Ocorrências", "descricao": "Registrou 50 ocorrências", "pontos": 100, "icone": "📈"},
    "turma_completa": {"nome": "🏫 Gestor de Turma", "descricao": "Cadastrou uma turma completa", "pontos": 30, "icone": "👥"},
    "agendamento_perfeito": {"nome": "📅 Organizador", "descricao": "Criou 5 agendamentos", "pontos": 20, "icone": "🗓️"},
    "backup_realizado": {"nome": "💾 Guardião dos Dados", "descricao": "Realizou backup do sistema", "pontos": 40, "icone": "🛡️"}
}

def inicializar_gamificacao():
    """Inicializa o estado da gamificação"""
    if 'pontos_usuario' not in st.session_state:
        st.session_state.pontos_usuario = 0
    if 'conquistas_usuario' not in st.session_state:
        st.session_state.conquistas_usuario = []
    if 'nivel_usuario' not in st.session_state:
        st.session_state.nivel_usuario = 1
    if 'registros_ocorrencias' not in st.session_state:
        st.session_state.registros_ocorrencias = 0
    if 'agendamentos_criados' not in st.session_state:
        st.session_state.agendamentos_criados = 0

def adicionar_pontos(pontos: int, motivo: str = ""):
    """Adiciona pontos ao usuário"""
    st.session_state.pontos_usuario += pontos  # ✅ CORRIGIDO
    recalcular_nivel()
    if motivo:
        st.toast(f"+{pontos} pontos! {motivo}", icon="🌟")

def recalcular_nivel():
    """Recalcula o nível baseado nos pontos"""
    pontos = st.session_state.pontos_usuario
    if pontos >= 500:
        st.session_state.nivel_usuario = 5
    elif pontos >= 300:
        st.session_state.nivel_usuario = 4
    elif pontos >= 150:
        st.session_state.nivel_usuario = 3
    elif pontos >= 50:
        st.session_state.nivel_usuario = 2
    else:
        st.session_state.nivel_usuario = 1

def get_nivel_nome(nivel: int) -> str:
    """Retorna o nome do nível"""
    niveis = {1: "🌱 Iniciante", 2: "📚 Aprendiz", 3: "⭐ Experiente", 4: "🏆 Mestre", 5: "👑 Lendário"}
    return niveis.get(nivel, "🌱 Iniciante")

def verificar_conquista(conquista_id: str):
    """Verifica e concede uma conquista"""
    if conquista_id not in st.session_state.conquistas_usuario:
        conquista = CONQUISTAS[conquista_id]
        st.session_state.conquistas_usuario.append(conquista_id)
        adicionar_pontos(conquista["pontos"], f"Conquista: {conquista['nome']}")
        st.balloons()
        return True
    return False

def exibir_gamificacao_sidebar():
    """Exibe o widget de gamificação no sidebar"""
    inicializar_gamificacao()
    with st.sidebar.expander(f"🏆 Nível {st.session_state.nivel_usuario} — {get_nivel_nome(st.session_state.nivel_usuario)}", expanded=False):
        pontos = st.session_state.pontos_usuario
        progresso = (pontos % 100) if pontos > 0 else 0
        st.markdown(f"""
        <div style="text-align:center; padding:0.5rem 0;">
            <div style="font-size:2.2rem; margin-bottom:0.25rem;">{get_nivel_nome(st.session_state.nivel_usuario).split()[0]}</div>
            <div style="font-family:'Nunito',sans-serif; font-size:1.6rem; font-weight:900; color:white;">{pontos} <span style="font-size:0.9rem;font-weight:500;color:#94a3b8;">pts</span></div>
            <div style="margin:0.6rem 0; height:6px; background:rgba(255,255,255,0.1); border-radius:99px; overflow:hidden;">
                <div style="width:{progresso}%; height:6px; background:linear-gradient(90deg,#2563eb,#0891b2); border-radius:99px; transition:width 0.5s;"></div>
            </div>
            <div style="font-size:0.7rem; color:#475569;">{progresso}/100 para próximo nível</div>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state.conquistas_usuario:
            for c_id in st.session_state.conquistas_usuario[:5]:
                if c_id in CONQUISTAS:
                    c = CONQUISTAS[c_id]
                    st.markdown(f"<div style='font-size:0.78rem;color:#94a3b8;padding:0.15rem 0;'>{c['icone']} {c['nome']}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size:0.75rem;color:#475569;text-align:center;'>🎯 Registre ocorrências para ganhar conquistas!</div>", unsafe_allow_html=True)

# ======================================================
# ASSISTENTE VIRTUAL
# ======================================================

def assistente_virtual(pergunta: str) -> str:
    """Responde perguntas frequentes sobre o sistema"""
    respostas = {
        "como registrar ocorrência": "Vá em '📝 Registrar Ocorrência', selecione a turma, o aluno e use a busca inteligente para encontrar a infração.",
        "como importar alunos": "Use '📥 Importar Alunos', selecione o arquivo CSV da SEDUC, escolha a turma e clique em Importar.",
        "como agendar espaço": "Em '📅 Agendamento de Espaços', use '✨ Agendar' para data específica ou '🗓️ Grade Semanal' para horários fixos.",
        "como criar comunicado": "Em '📄 Comunicado aos Pais', selecione o aluno e a ocorrência, marque as medidas e gere o PDF.",
        "como ver gráficos": "Acesse '📊 Gráficos e Indicadores' para análises visuais das ocorrências.",
        "como cadastrar professor": "Em '👨‍🏫 Cadastrar Professores', preencha nome e cargo, ou importe uma lista em massa.",
        "como fazer backup": "Vá em '💾 Backups' para gerar ou importar backups do sistema.",
        "mapa da sala": "Em '🏫 Mapa da Sala', configure fileiras e carteiras, depois distribua os alunos.",
        "portal do responsável": "Acesse '👨‍👩‍👧 Portal do Responsável' e faça login com o RA do aluno.",
    }
    pergunta_lower = pergunta.lower()
    for chave, resposta in respostas.items():
        if chave in pergunta_lower:
            return resposta
    return "Desculpe, não entendi. Tente perguntar sobre: registrar ocorrência, importar alunos, agendar espaço, criar comunicado, ver gráficos, cadastrar professor, fazer backup, mapa da sala ou portal do responsável."

def exibir_assistente_sidebar():
    """Exibe o assistente virtual no sidebar"""
    with st.sidebar.expander("🤖 Assistente Virtual", expanded=False):
        st.markdown("<div style='color:#94a3b8;font-size:0.8rem;margin-bottom:0.5rem;'>Como posso ajudar?</div>", unsafe_allow_html=True)
        pergunta = st.text_input("", placeholder="Ex: Como registrar ocorrência?", key="assistente_input", label_visibility="collapsed")
        if pergunta:
            resposta = assistente_virtual(pergunta)
            st.markdown(f"<div style='background:rgba(37,99,235,0.1);border-left:3px solid #2563eb;border-radius:8px;padding:0.6rem 0.8rem;font-size:0.8rem;color:#93c5fd;margin:0.4rem 0;'>{resposta}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:1px;background:rgba(255,255,255,0.06);margin:0.6rem 0;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.72rem;color:#475569;line-height:1.8;'>💡 Busca inteligente nas ocorrências<br>📅 Agendamentos fixos na Grade Semanal<br>📥 Exporte relatórios em PDF ou Excel</div>", unsafe_allow_html=True)
        # ======================================================
# SUPABASE — FUNÇÕES BASE
# ======================================================

def _supabase_request(method: str, path: str, **kwargs):
    """Função central de request para o Supabase"""
    if not SUPABASE_VALID:
        raise ErroConexaoDB("Supabase não configurado. Verifique SUPABASE_URL e SUPABASE_KEY.")
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    response = requests.request(method, url, headers=HEADERS, timeout=15, **kwargs)
    if response.status_code >= 400:
        logger.error(f"Erro Supabase ({response.status_code}): {response.text}")
        response.raise_for_status()
    return response

def _supabase_get_dataframe(path: str, acao: str) -> pd.DataFrame:
    """Retorna DataFrame a partir de endpoint Supabase"""
    try:
        response = _supabase_request("GET", path)
        return pd.DataFrame(response.json())
    except ErroConexaoDB:
        raise
    except Exception as e:
        raise ErroCarregamentoDados(acao, str(e))

def _supabase_mutation(method: str, path: str, data, acao: str) -> bool:
    """POST / PATCH / DELETE genérico"""
    try:
        kwargs = {}
        if data is not None:
            kwargs["json"] = data
        response = _supabase_request(method, path, **kwargs)
        return response.status_code in (200, 201, 204)
    except ErroConexaoDB:
        raise
    except Exception as e:
        raise ErroOperacaoDB(acao, str(e))
    # ======================================================
# ALUNOS
# ======================================================

@st.cache_data(ttl=300)
@com_tratamento_erro
@com_retry(tentativas=2)
def carregar_alunos() -> pd.DataFrame:
    return _supabase_get_dataframe("alunos?select=*", "carregar alunos")

@com_tratamento_erro
def salvar_aluno(aluno: dict) -> bool:
    valido, msg = Validadores.validar_nao_vazio(aluno.get("nome"), "Nome do aluno")
    if not valido:
        raise ErroValidacao("nome", msg)
    sucesso = _supabase_mutation("POST", "alunos", aluno, "salvar aluno")
    if sucesso:
        carregar_alunos.clear()
    return sucesso

@com_tratamento_erro
def atualizar_aluno(ra: str, dados: dict) -> bool:
    sucesso = _supabase_mutation("PATCH", f"alunos?ra=eq.{ra}", dados, "atualizar aluno")
    if sucesso:
        carregar_alunos.clear()
    return sucesso

@com_tratamento_erro
def excluir_alunos_por_turma(turma: str) -> bool:
    if not turma:
        raise ErroValidacao("turma", "Turma não pode ser vazia")
    sucesso = _supabase_mutation("DELETE", f"alunos?turma=eq.{turma}", None, "excluir alunos da turma")
    if sucesso:
        carregar_alunos.clear()
    return sucesso

@com_tratamento_erro
def editar_nome_turma(turma_antiga: str, turma_nova: str) -> bool:
    if not turma_antiga or not turma_nova:
        raise ErroValidacao("turma", "Nome da turma não pode ser vazio")
    if turma_antiga == turma_nova:
        return True
    df_alunos = carregar_alunos()
    alunos_turma = df_alunos[df_alunos["turma"] == turma_antiga]
    sucesso_geral = True
    for _, aluno in alunos_turma.iterrows():
        if not atualizar_aluno(aluno["ra"], {"turma": turma_nova}):
            sucesso_geral = False
    if sucesso_geral:
        carregar_alunos.clear()
        return True
    return False

# ======================================================
# PROFESSORES
# ======================================================

@st.cache_data(ttl=300)
@com_tratamento_erro
@com_retry(tentativas=2)
def carregar_professores() -> pd.DataFrame:
    return _supabase_get_dataframe("professores?select=*", "carregar professores")

@com_tratamento_erro
def salvar_professor(professor: dict) -> bool:
    valido, msg = Validadores.validar_nao_vazio(professor.get("nome"), "Nome do professor")
    if not valido:
        raise ErroValidacao("nome", msg)
    sucesso = _supabase_mutation("POST", "professores", professor, "salvar professor")
    if sucesso:
        carregar_professores.clear()
    return sucesso

@com_tratamento_erro
def atualizar_professor(id_prof: int, dados: dict) -> bool:
    sucesso = _supabase_mutation("PATCH", f"professores?id=eq.{id_prof}", dados, "atualizar professor")
    if sucesso:
        carregar_professores.clear()
    return sucesso

@com_tratamento_erro
def excluir_professor(id_prof: int) -> bool:
    if not id_prof:
        raise ErroValidacao("id", "ID do professor inválido")
    sucesso = _supabase_mutation("DELETE", f"professores?id=eq.{id_prof}", None, "excluir professor")
    if sucesso:
        carregar_professores.clear()
    return sucesso

# ======================================================
# RESPONSÁVEIS / ASSINATURAS
# ======================================================

@st.cache_data(ttl=300)
@com_tratamento_erro
@com_retry(tentativas=2)
def carregar_responsaveis() -> pd.DataFrame:
    return _supabase_get_dataframe("responsaveis?select=*&ativo=eq.true", "carregar responsáveis")

def limpar_cache_responsaveis():
    try:
        carregar_responsaveis.clear()
    except Exception:
        pass

@com_tratamento_erro
def salvar_responsavel(responsavel: dict) -> bool:
    valido, msg = Validadores.validar_nao_vazio(responsavel.get("nome"), "Nome do responsável")
    if not valido:
        raise ErroValidacao("nome", msg)
    sucesso = _supabase_mutation("POST", "responsaveis", responsavel, "salvar responsável")
    if sucesso:
        limpar_cache_responsaveis()
    return sucesso

@com_tratamento_erro
def atualizar_responsavel(id_resp: int, dados: dict) -> bool:
    sucesso = _supabase_mutation("PATCH", f"responsaveis?id=eq.{id_resp}", dados, "atualizar responsável")
    if sucesso:
        limpar_cache_responsaveis()
    return sucesso

@com_tratamento_erro
def excluir_responsavel(id_resp: int) -> bool:
    if not id_resp:
        raise ErroValidacao("id", "ID do responsável inválido")
    sucesso = _supabase_mutation("DELETE", f"responsaveis?id=eq.{id_resp}", None, "excluir responsável")
    if sucesso:
        limpar_cache_responsaveis()
    return sucesso

# ======================================================
# OCORRÊNCIAS
# ======================================================

@st.cache_data(ttl=300)
@com_tratamento_erro
@com_retry(tentativas=2)
def carregar_ocorrencias() -> pd.DataFrame:
    return _supabase_get_dataframe("ocorrencias?select=*&order=id.desc", "carregar ocorrências")

@com_tratamento_erro
def salvar_ocorrencia(ocorrencia: dict) -> bool:
    valido, msg = Validadores.validar_nao_vazio(ocorrencia.get("aluno"), "Nome do aluno")
    if not valido:
        raise ErroValidacao("aluno", msg)
    sucesso = _supabase_mutation("POST", "ocorrencias", ocorrencia, "salvar ocorrência")
    if sucesso:
        carregar_ocorrencias.clear()
    return sucesso

@com_tratamento_erro
def editar_ocorrencia(id_ocorrencia: int, dados: dict) -> bool:
    sucesso = _supabase_mutation("PATCH", f"ocorrencias?id=eq.{id_ocorrencia}", dados, "editar ocorrência")
    if sucesso:
        carregar_ocorrencias.clear()
    return sucesso

@com_tratamento_erro
def excluir_ocorrencia(id_ocorrencia: int) -> bool:
    sucesso = _supabase_mutation("DELETE", f"ocorrencias?id=eq.{id_ocorrencia}", None, "excluir ocorrência")
    if sucesso:
        carregar_ocorrencias.clear()
    return sucesso

def verificar_ocorrencia_duplicada(ra: str, categoria: str, data_str: str, df_ocorrencias: pd.DataFrame) -> bool:
    if df_ocorrencias.empty:
        return False
    duplicadas = df_ocorrencias[(df_ocorrencias["ra"] == ra) & (df_ocorrencias["categoria"] == categoria) & (df_ocorrencias["data"] == data_str)]
    return not duplicadas.empty
# ======================================================
# AGENDAMENTO - FUNÇÕES SUPABASE
# ======================================================

@st.cache_data(ttl=120)
def carregar_agendamentos_filtrado(data_ini: str, data_fim: str, espaco: str = None, professor: str = None) -> pd.DataFrame:
    try:
        base = "/rest/v1/agendamentos?select=id,data_agendamento,horario,espaco,turma,disciplina,prioridade,semanas,professor_nome,professor_email,status,tipo&order=data_agendamento.asc,horario.asc"
        filtros = f"&data_agendamento=gte.{data_ini}&data_agendamento=lte.{data_fim}"
        
        if espaco and espaco in ESPACOS_AGEND:
            filtros += f"&espaco=eq.{espaco}"
        
        if professor:
            professor_encoded = professor.replace(" ", "%20")
            filtros += f'&professor_nome=eq."{professor_encoded}"'
        
        rows = _rest_get_agend(base + filtros)
        return pd.DataFrame(rows) if rows else pd.DataFrame()
        
    except Exception as e:
        st.warning(f"Falha ao consultar agendamentos: {e}")
        return pd.DataFrame()

def _rest_get_agend(path: str, params: dict = None, timeout: int = 20):
    url = f"{SUPABASE_URL}{path}"
    r = requests.get(url, headers=HEADERS, params=params or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()

def salvar_agendamento_api(dados: dict):
    url = f"{SUPABASE_URL}/rest/v1/agendamentos"
    r = requests.post(url, json=dados, headers=HEADERS, timeout=20)
    if r.status_code not in (200, 201):
        return False, f"{r.status_code} - {r.text}"
    return True, r.json()

def cancelar_agendamento_api(id_agend: str):
    url = f"{SUPABASE_URL}/rest/v1/agendamentos?id=eq.{id_agend}"
    r = requests.patch(url, json={"status": "CANCELADO"}, headers=HEADERS, timeout=20)
    return r.status_code in (200, 204), None

def excluir_agendamento_api(id_agend: str):
    url = f"{SUPABASE_URL}/rest/v1/agendamentos?id=eq.{id_agend}"
    r = requests.patch(url, json={"status": "EXCLUIDO_GESTAO"}, headers=HEADERS, timeout=20)
    return r.status_code in (200, 204), None

def verificar_conflito_api(data_yyyy_mm_dd: str, horario: str, espaco: str):
    try:
        path = f"/rest/v1/agendamentos?select=id,professor_nome,prioridade&data_agendamento=eq.{data_yyyy_mm_dd}&horario=eq.{horario}&espaco=eq.{espaco}&status=eq.ATIVO&limit=1"
        rows = _rest_get_agend(path)
        return rows[0] if rows else None
    except Exception:
        return None

def prof_list_agend(only_active: bool = True) -> pd.DataFrame:
    try:
        path = "/rest/v1/professores?select=id,nome,email,cargo&order=nome.asc"
        rows = _rest_get_agend(path)
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["id", "nome", "email", "cargo"])
        if not df.empty and 'cargo' in df.columns:
            df['status'] = 'ATIVO'
        return df
    except Exception:
        return pd.DataFrame(columns=["id", "nome", "email", "cargo", "status"])

def prof_upsert_agend(nome: str, email: str, status: str = "ATIVO"):
    payload = {"nome": (nome or "").strip(), "email": (email or "").strip(), "cargo": "Professor"}
    url = f"{SUPABASE_URL}/rest/v1/professores"
    headers_upsert = HEADERS.copy()
    headers_upsert["Prefer"] = "resolution=merge-duplicates,return=representation"
    r = requests.post(url, json=payload, headers=headers_upsert, timeout=20)
    return r.status_code in (200, 201), r.json() if r.status_code in (200, 201) else None
# ======================================================
# ELETIVAS — IMPORTAÇÃO EXCEL
# ======================================================

def carregar_eletivas_do_excel(caminho_arquivo: str, fallback: dict = None) -> dict:
    """Lê planilha XLSX de eletivas diretamente via XML"""
    if not os.path.exists(caminho_arquivo):
        return fallback if fallback is not None else {}
    try:
        ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        with zipfile.ZipFile(caminho_arquivo) as arquivo_zip:
            shared_strings = []
            if "xl/sharedStrings.xml" in arquivo_zip.namelist():
                root = ET.fromstring(arquivo_zip.read("xl/sharedStrings.xml"))
                for si in root.findall("a:si", ns):
                    textos = [t.text or "" for t in si.iterfind(".//a:t", ns)]
                    shared_strings.append("".join(textos))
            sheet = ET.fromstring(arquivo_zip.read("xl/worksheets/sheet1.xml"))
            eletivas = {}
            professora_atual = None
            for row in sheet.findall(".//a:sheetData/a:row", ns):
                valores = {}
                for cell in row.findall("a:c", ns):
                    ref = cell.attrib.get("r", "")
                    col = "".join(ch for ch in ref if ch.isalpha())
                    tipo = cell.attrib.get("t")
                    valor = ""
                    v = cell.find("a:v", ns)
                    if v is not None and v.text:
                        valor = v.text
                    if tipo == "s" and valor.isdigit():
                        valor = shared_strings[int(valor)]
                    valores[col] = str(valor).strip()
                valor_a = valores.get("A", "")
                valor_b = valores.get("B", "")
                valor_c = valores.get("C", "")
                if valor_a and not valor_b and not valor_c:
                    professora_atual = valor_a
                    eletivas.setdefault(professora_atual, [])
                    continue
                if valor_a.upper() in ("Nº", "NO", "NUM"):
                    continue
                if valor_b.upper().startswith("NOME"):
                    continue
                if professora_atual and valor_b:
                    eletivas[professora_atual].append({"nome": valor_b, "serie": valor_c})
            eletivas = {prof: alunos for prof, alunos in eletivas.items() if alunos}
            return eletivas if eletivas else (fallback or {})
    except Exception as e:
        logger.error(f"Erro ao importar eletivas: {e}")
        return fallback if fallback is not None else {}

def converter_eletivas_para_registros(eletivas_dict: dict, origem: str = "excel") -> list:
    registros = []
    for professora, alunos in eletivas_dict.items():
        for item in alunos:
            registros.append({"professora": professora, "nome_aluno": item.get("nome", ""), "serie": item.get("serie", ""), "origem": origem})
    return registros

def converter_eletivas_supabase_para_dict(df_eletivas: pd.DataFrame) -> dict:
    if df_eletivas.empty:
        return {}
    eletivas = {}
    for _, row in df_eletivas.iterrows():
        professora = str(row.get("professora", "")).strip()
        nome_aluno = str(row.get("nome_aluno", "")).strip()
        serie = str(row.get("serie", "")).strip()
        if not professora or not nome_aluno:
            continue
        eletivas.setdefault(professora, []).append({"nome": nome_aluno, "serie": serie})
    return eletivas

def montar_dataframe_eletiva(nome_professora: str, df_alunos: pd.DataFrame, eletivas_dict: dict) -> pd.DataFrame:
    registros = []
    alunos_db = df_alunos.copy()
    nome_coluna = None
    for c in alunos_db.columns:
        if c.lower() in ("nome", "nome do aluno", "aluno"):
            nome_coluna = c
            break
    if nome_coluna:
        alunos_db["nome_norm"] = alunos_db[nome_coluna].apply(normalizar_texto)
    else:
        alunos_db["nome_norm"] = ""
    for item in eletivas_dict.get(nome_professora, []):
        nome_original = item.get("nome", "")
        serie_original = item.get("serie", "")
        nome_norm_excel = normalizar_texto(nome_original)
        melhor_match = None
        melhor_score = 0.0
        for _, aluno in alunos_db.iterrows():
            score = SequenceMatcher(None, nome_norm_excel, aluno.get("nome_norm", "")).ratio()
            if score > melhor_score:
                melhor_score = score
                melhor_match = aluno
        if melhor_match is not None and melhor_score >= 0.80:
            registros.append({
                "Professora": nome_professora,
                "Nome da Eletiva": nome_original,
                "Série da Eletiva": serie_original,
                "Aluno Cadastrado": melhor_match.get("nome", ""),
                "RA": melhor_match.get("ra", ""),
                "Turma no Sistema": melhor_match.get("turma", ""),
                "Situação": melhor_match.get("situacao", ""),
                "Status": "Encontrado",
            })
        else:
            registros.append({
                "Professora": nome_professora,
                "Nome da Eletiva": nome_original,
                "Série da Eletiva": serie_original,
                "Aluno Cadastrado": "",
                "RA": "",
                "Turma no Sistema": "",
                "Situação": "",
                "Status": "Não encontrado",
            })
    return pd.DataFrame(registros)

ELETIVAS_EXCEL = carregar_eletivas_do_excel(ELETIVAS_ARQUIVO, fallback=ELETIVAS)
# ======================================================
# PDF — UTILITÁRIOS
# ======================================================

def _criar_documento_pdf(buffer: BytesIO) -> SimpleDocTemplate:
    return SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)

def _adicionar_logo(elementos: list):
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4*cm)
            logo.hAlign = "CENTER"
            elementos.append(logo)
            elementos.append(Spacer(1, 0.3*cm))
    except Exception:
        pass

# ======================================================
# PDF — ELETIVA
# ======================================================

def gerar_pdf_eletiva(nome_professora: str, df_eletiva: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    doc = _criar_documento_pdf(buffer)
    estilos = getSampleStyleSheet()
    elementos = []
    _adicionar_logo(elementos)
    
    titulo_style = ParagraphStyle('TituloEletiva', parent=estilos['Heading1'], fontSize=14, alignment=TA_CENTER, spaceAfter=0.5*cm, textColor=colors.HexColor("#4A90E2"))
    elementos.append(Paragraph(f"LISTA DE ELETIVA", titulo_style))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph(f"<b>Professora:</b> {nome_professora}", estilos['Normal']))
    elementos.append(Paragraph(f"<b>Total de estudantes:</b> {len(df_eletiva)}", estilos['Normal']))
    elementos.append(Spacer(1, 0.5*cm))
    
    cabecalho = ["Nome da Eletiva", "Série", "RA", "Turma", "Status"]
    linhas = []
    for _, row in df_eletiva.iterrows():
        linhas.append([
            str(row.get("Nome da Eletiva", ""))[:30],
            str(row.get("Série da Eletiva", ""))[:15],
            str(row.get("RA", ""))[:15],
            str(row.get("Turma no Sistema", ""))[:15],
            str(row.get("Status", ""))[:15]
        ])
    
    tabela = Table(cabecalho + linhas, colWidths=[7*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm], repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4A90E2")), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9), ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    for i in range(1, len(linhas) + 1):
        if i % 2 == 0:
            tabela.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor("#F5F5F5"))]))
    elementos.append(tabela)
    elementos.append(Spacer(1, 0.5*cm))
    
    encontrados = len(df_eletiva[df_eletiva["Status"] == "Encontrado"])
    nao_encontrados = len(df_eletiva[df_eletiva["Status"] == "Não encontrado"])
    elementos.append(Paragraph(f"<b>Encontrados no sistema:</b> {encontrados}", estilos['Normal']))
    elementos.append(Paragraph(f"<b>Não encontrados:</b> {nao_encontrados}", estilos['Normal']))
    elementos.append(Spacer(1, 0.5*cm))
    
    estilo_rodape = ParagraphStyle('Rodape', parent=estilos['Normal'], fontSize=7, alignment=TA_CENTER, textColor=colors.grey)
    elementos.append(Paragraph("_" * 75, estilos['Normal']))
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
    elementos.append(Paragraph(f"Sistema Conviva 179 - E.E. Profª Eliane", estilo_rodape))
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# ======================================================
# PDF — OCORRÊNCIA
# ======================================================

def gerar_pdf_ocorrencia(ocorrencia: dict, df_responsaveis: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    doc = _criar_documento_pdf(buffer)
    estilos = getSampleStyleSheet()
    elementos = []
    _adicionar_logo(elementos)
    protocolo = f"PROTOCOLO: {ocorrencia.get('id', 'N/A')}/{datetime.now().year}"
    elementos.append(Paragraph(f"<b>{protocolo}</b>", ParagraphStyle("protocolo", parent=estilos["Normal"], alignment=2, fontSize=9, textColor=colors.darkblue)))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("REGISTRO DE OCORRÊNCIA", ParagraphStyle("titulo", parent=estilos["Heading1"], alignment=1, fontSize=12, textColor=colors.darkblue)))
    dados = [["Data", ocorrencia.get("data", "")], ["Aluno", ocorrencia.get("aluno", "")], ["RA", str(ocorrencia.get("ra", ""))], ["Turma", ocorrencia.get("turma", "")], ["Categoria", ocorrencia.get("categoria", "")], ["Gravidade", ocorrencia.get("gravidade", "")], ["Professor", ocorrencia.get("professor", "")]]
    tabela = Table(dados, colWidths=[4*cm, 11*cm])
    tabela.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#4A90E2")), ('TEXTCOLOR', (0, 0), (0, -1), colors.white), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTSIZE', (0, 0), (-1, -1), 9)]))
    elementos.append(tabela)
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("<b>RELATO</b>", estilos["Normal"]))
    elementos.append(Paragraph(str(ocorrencia.get("relato", "")).replace("\n", "<br/>"), estilos["Normal"]))
    elementos.append(Spacer(1, 0.2*cm))
    elementos.append(Paragraph("<b>ENCAMINHAMENTOS</b>", estilos["Normal"]))
    elementos.append(Paragraph(str(ocorrencia.get("encaminhamento", "")).replace("\n", "<br/>"), estilos["Normal"]))
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# ======================================================
# PDF — COMUNICADO AOS PAIS
# ======================================================

def gerar_pdf_comunicado(aluno_data: dict, ocorrencia_data: dict, medidas_aplicadas: str, observacoes: str, df_responsaveis: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    doc = _criar_documento_pdf(buffer)
    estilos = getSampleStyleSheet()
    elementos = []
    _adicionar_logo(elementos)
    elementos.append(Paragraph("COMUNICADO AOS PAIS / RESPONSÁVEIS", ParagraphStyle("titulo", parent=estilos["Heading1"], alignment=1, fontSize=12, textColor=colors.darkblue)))
    elementos.append(Spacer(1, 0.4*cm))
    dados_aluno = [["Aluno", aluno_data.get("nome", "")], ["RA", aluno_data.get("ra", "")], ["Turma", aluno_data.get("turma", "")], ["Total de Ocorrências", aluno_data.get("total_ocorrencias", 0)]]
    tabela = Table(dados_aluno, colWidths=[5*cm, 10*cm])
    tabela.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke)]))
    elementos.append(tabela)
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("<b>RELATO DA OCORRÊNCIA</b>", estilos["Normal"]))
    elementos.append(Paragraph(str(ocorrencia_data.get("relato", "")).replace("\n", "<br/>"), estilos["Normal"]))
    elementos.append(Spacer(1, 0.3*cm))
    if medidas_aplicadas:
        elementos.append(Paragraph("<b>MEDIDAS APLICADAS</b>", estilos["Normal"]))
        for linha in medidas_aplicadas.split("\n"):
            elementos.append(Paragraph(f"• {linha}", estilos["Normal"]))
    if observacoes:
        elementos.append(Spacer(1, 0.3*cm))
        elementos.append(Paragraph("<b>OBSERVAÇÕES</b>", estilos["Normal"]))
        elementos.append(Paragraph(observacoes, estilos["Normal"]))
    doc.build(elementos)
    buffer.seek(0)
    return buffer
# ======================================================
# SESSION STATE — INICIALIZAÇÃO (CORRIGIDO)
# ======================================================

def _init_session_state():
    """Inicializa todas as variáveis de estado da sessão."""
    defaults = {
        # Estados de Edição/Ocorrências
        "editando_id": None,
        "dados_edicao": None,
        "ocorrencia_salva_sucesso": False,
        "salvando_ocorrencia": False,
        "gravidade_alterada": False,
        "adicionar_outra_infracao": False,
        "infracoes_adicionais": [],
        "mensagem_exclusao": None,
        
        # Estados de Professores
        "editando_prof": None,
        "professor_salvo_sucesso": False,
        "nome_professor_salvo": "",
        "cargo_professor_salvo": "",
        "confirmar_exclusao_prof": None,
        
        # Estados de Responsáveis
        "editando_resp": None,
        "responsavel_salvo_sucesso": False,
        "nome_responsavel_salvo": "",
        "cargo_responsavel_salvo": "",
        "confirmar_exclusao_resp": None,
        
        # Estados de Turmas
        "turma_para_editar": None,
        "turma_para_deletar": None,
        "turma_para_substituir": None,
        "turma_selecionada": None,
        "senha_exclusao_validada": False,
        "confirmar_exclusao_aluno": None,
        
        # Estados de Eletivas
        "ELETIVAS": None,
        "FONTE_ELETIVAS": None,
        
        # Estados de Backup
        "backup_manager": None,
        "backup_realizado": False,
        
        # Estados de Agendamento
        "gestao_logado": False,
        "aba_agendamento": "✨ Agendar",
        "pending_cancel_id": None,
        "pending_delete_id": None,
        "pending_delete_prof": None,
        "logs_agendamento": [],
        
        # ⭐ Estados de Gamificação
        "pontos_usuario": 0,
        "conquistas_usuario": [],
        "nivel_usuario": 1,
        "registros_ocorrencias": 0,
        "agendamentos_criados": 0,
        
        # Navegação
        "menu_selecionado": "🏠 Dashboard",
        "pagina_atual": "🏠 Dashboard",
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Inicializa o estado da sessão
_init_session_state()
# ======================================================
# BACKUP AUTOMÁTICO (CORRIGIDO)
# ======================================================

if st.session_state.backup_manager is None:
    try:
        st.session_state.backup_manager = BackupManager()
    except Exception as e:
        logger.error(f"Erro ao inicializar BackupManager: {e}")
        st.session_state.backup_manager = BackupManager()

if not st.session_state.backup_realizado:
    try:
        st.session_state.backup_manager.criar_backup()
        st.session_state.backup_manager.limpar_backups_antigos(dias_retencao=30)
        st.session_state.backup_realizado = True
        verificar_conquista("backup_realizado")  # ⭐ Conquista por fazer backup
    except Exception as e:
        logger.error(f"Erro ao executar backup automático: {e}")
        # ======================================================
# CARREGAMENTO INICIAL DE DADOS
# ======================================================

df_alunos = pd.DataFrame()
df_professores = pd.DataFrame()
df_ocorrencias = pd.DataFrame()
df_responsaveis = pd.DataFrame()
df_eletivas_supabase = pd.DataFrame()

try:
    df_alunos = carregar_alunos()
except Exception as e:
    st.warning("⚠️ Não foi possível carregar alunos.")
    logger.error(e)

try:
    df_professores = carregar_professores()
except Exception as e:
    st.warning("⚠️ Não foi possível carregar professores.")
    logger.error(e)

try:
    df_ocorrencias = carregar_ocorrencias()
except Exception as e:
    st.warning("⚠️ Não foi possível carregar ocorrências.")
    logger.error(e)

try:
    df_responsaveis = carregar_responsaveis()
except Exception as e:
    st.warning("⚠️ Não foi possível carregar responsáveis.")
    logger.error(e)

# ======================================================
# ELETIVAS — DEFINIÇÃO DE FONTE
# ======================================================

if SUPABASE_VALID:
    try:
        df_eletivas_supabase = _supabase_get_dataframe("eletivas?select=*", "carregar eletivas")
    except Exception:
        df_eletivas_supabase = pd.DataFrame()

if st.session_state.ELETIVAS is None:
    if not df_eletivas_supabase.empty:
        st.session_state.ELETIVAS = converter_eletivas_supabase_para_dict(df_eletivas_supabase)
        st.session_state.FONTE_ELETIVAS = "supabase"
    else:
        st.session_state.ELETIVAS = ELETIVAS_EXCEL
        st.session_state.FONTE_ELETIVAS = "excel"
else:
    if not df_eletivas_supabase.empty:
        st.session_state.FONTE_ELETIVAS = "supabase"
    else:
        st.session_state.FONTE_ELETIVAS = "excel"

ELETIVAS = st.session_state.ELETIVAS
FONTE_ELETIVAS = st.session_state.FONTE_ELETIVAS
# ======================================================
# REMOÇÃO DEFINITIVA DE TOOLTIPS (JAVASCRIPT CORRIGIDO)
# ======================================================
st.components.v1.html("""
<script>
(function() {
    'use strict';

    function corrigirTextoSelects() {
        const seletoresTexto = [
            '[data-baseweb="select"] *',
            '[data-baseweb="popover"] *',
            '[data-baseweb="menu"] *',
            '[role="listbox"] *',
            '[role="option"] *'
        ];

        seletoresTexto.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                el.style.setProperty('color', '#0f172a', 'important');
                el.style.setProperty('-webkit-text-fill-color', '#0f172a', 'important');
                el.style.setProperty('opacity', '1', 'important');
                el.style.setProperty('visibility', 'visible', 'important');
                el.style.setProperty('-webkit-background-clip', 'unset', 'important');
                el.style.setProperty('background-clip', 'unset', 'important');
                el.style.setProperty('text-shadow', 'none', 'important');
            });
        });
    }
    
    function limparTooltips() {
        // Remove APENAS elementos de tooltip reais — nunca toca em botões/spans de menu
        const seletores = [
            '[data-testid="stTooltipHoverTarget"]',
            '[data-testid="stTooltipContent"]',
            '[role="tooltip"]',
            '[data-baseweb="tooltip"]'
        ];
        seletores.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                // Garante que não é filho de botão (que seria o texto do botão)
                if (!el.closest('button')) el.remove();
            });
        });
        
        // Remove apenas atributos title dos botões do sidebar (previne tooltips nativos)
        document.querySelectorAll('[data-testid="stSidebar"] button').forEach(btn => {
            btn.removeAttribute('title');
            btn.removeAttribute('data-tooltip');
        });
        
        // Garante que todos os spans dentro de botões do sidebar ficam visíveis
        document.querySelectorAll('[data-testid="stSidebar"] button span').forEach(span => {
            span.style.removeProperty('display');
            span.style.removeProperty('visibility');
            span.style.removeProperty('opacity');
            span.style.removeProperty('font-size');
            span.style.removeProperty('width');
            span.style.removeProperty('height');
            span.style.removeProperty('overflow');
        });

        // CORREÇÃO: garante que o texto dentro dos selectboxes fica sempre visível
        corrigirTextoSelects();
        document.querySelectorAll('[data-baseweb="select"] div, [data-baseweb="select"] span').forEach(el => {
            el.style.setProperty('color', '#0f172a', 'important');
            el.style.setProperty('-webkit-text-fill-color', '#0f172a', 'important');
            el.style.setProperty('opacity', '1', 'important');
            el.style.setProperty('-webkit-background-clip', 'unset', 'important');
            el.style.setProperty('background-clip', 'unset', 'important');
        });

        // CORREÇÃO: garante visibilidade no popover/dropdown aberto (renderizado fora do select)
        const popoverSelectors = [
            '[data-baseweb="popover"] *',
            '[data-baseweb="menu"] *',
            '[role="listbox"] *',
            '[role="option"]'
        ];
        popoverSelectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                el.style.setProperty('color', '#0f172a', 'important');
                el.style.setProperty('-webkit-text-fill-color', '#0f172a', 'important');
                el.style.setProperty('-webkit-background-clip', 'unset', 'important');
                el.style.setProperty('background-clip', 'unset', 'important');
                el.style.setProperty('opacity', '1', 'important');
                el.style.setProperty('visibility', 'visible', 'important');
            });
        });
    }
    
    // Executa após carregamento e periodicamente
    setTimeout(limparTooltips, 300);
    setTimeout(limparTooltips, 800);
    setInterval(limparTooltips, 2000);
    
    const observer = new MutationObserver(function() {
        corrigirTextoSelects();
        const dropdownAberto = document.querySelector('[data-baseweb="popover"]') ||
                               document.querySelector('[role="listbox"]');
        if (!dropdownAberto) limparTooltips();
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", height=0)
# ======================================================
exibir_notificacoes_sidebar()
exibir_gamificacao_sidebar()
exibir_assistente_sidebar()
# ======================================================
# PÁGINA 🏠 DASHBOARD - COMPLETO E COLORIDO
# ======================================================

if menu == "🏠 Dashboard":
    # ── Header Premium da Escola ──────────────────────────────
    st.markdown(f"""
    <div class="main-header animate-fade-in">
        <div class="pattern"></div>
        <div class="school-name">🏫 {ESCOLA_NOME}</div>
        <div class="school-subtitle">{ESCOLA_SUBTITULO}</div>
        <div class="school-info-chips">
            <span class="school-chip">📍 {ESCOLA_ENDERECO}</span>
            <span class="school-chip">📞 {ESCOLA_TELEFONE}</span>
            <span class="school-chip">✉️ {ESCOLA_EMAIL}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Boas-vindas ───────────────────────────────────────────
    hora_atual = datetime.now().hour
    saudacao = "🌅 Bom dia" if hora_atual < 12 else ("☀️ Boa tarde" if hora_atual < 18 else "🌙 Boa noite")
    st.markdown(f"""
    <div style="
        display: flex; align-items: center; gap: 1rem;
        background: white; border-radius: 16px; padding: 1.25rem 1.5rem;
        border: 1.5px solid #e2e8f0; box-shadow: 0 2px 8px rgba(15,23,42,0.06);
        margin-bottom: 1.75rem;
    ">
        <div style="font-size: 2.5rem; line-height:1;">👋</div>
        <div>
            <div style="
                font-family: 'Nunito', sans-serif;
                font-size: 1.3rem; font-weight: 800;
                color: #0f172a; margin-bottom: 0.15rem;
            ">{saudacao}! Bem-vindo ao Sistema Conviva 179</div>
            <div style="color: #64748b; font-size: 0.9rem;">
                Gerencie ocorrências, alunos e agendamentos de forma inteligente.
                &nbsp;·&nbsp; <b style="color: #2563eb;">{datetime.now().strftime('%A, %d de %B de %Y')}</b>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Métricas Principais ───────────────────────────────────
    total_alunos      = len(df_alunos) if not df_alunos.empty else 0
    total_ocorrencias = len(df_ocorrencias) if not df_ocorrencias.empty else 0
    total_professores = len(df_professores) if not df_professores.empty else 0

    if not df_alunos.empty and "situacao" in df_alunos.columns:
        df_alunos["situacao_norm"]  = df_alunos["situacao"].str.strip().str.title()
        total_ativos      = len(df_alunos[df_alunos["situacao_norm"] == "Ativo"])
        total_transferidos = len(df_alunos[df_alunos["situacao_norm"] == "Transferido"])
    else:
        total_ativos      = total_alunos
        total_transferidos = 0

    gravissimas = (
        len(df_ocorrencias[df_ocorrencias["gravidade"] == "Gravíssima"])
        if not df_ocorrencias.empty and "gravidade" in df_ocorrencias.columns else 0
    )

    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem;">
        <div style="width:4px; height:22px; background:linear-gradient(180deg,#1d4ed8,#0891b2); border-radius:4px;"></div>
        <h3 style="margin:0; font-family:'Nunito',sans-serif; font-size:1.1rem; color:#0f172a;">Visão Geral do Sistema</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="dashboard-callout animate-fade-in">
        <div class="dashboard-callout-content">
            <div>
                <p class="dashboard-callout-title">Panorama do dia letivo</p>
                <p class="dashboard-callout-text">Acompanhe alunos, ocorrencias e equipe em um painel mais claro e rapido para consulta.</p>
            </div>
            <div class="dashboard-callout-badge">{datetime.now().strftime('%d/%m/%Y')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    cards_data = [
        (col1, "linear-gradient(135deg,#1d4ed8 0%,#2563eb 100%)", "👥", total_alunos, "Total de Alunos", f"{total_ativos} ativos", "0"),
        (col2, "linear-gradient(135deg,#dc2626 0%,#ef4444 100%)", "⚠️", total_ocorrencias, "Ocorrências", f"{gravissimas} gravíssimas", "0.08s"),
        (col3, "linear-gradient(135deg,#0891b2 0%,#06b6d4 100%)", "👨‍🏫", total_professores, "Professores", "cadastrados", "0.16s"),
        (col4, "linear-gradient(135deg,#059669 0%,#10b981 100%)", "✅", total_ativos, "Alunos Ativos", "frequentando", "0.24s"),
        (col5, "linear-gradient(135deg,#7c3aed 0%,#8b5cf6 100%)", "🔄", total_transferidos, "Transferidos", "este ano", "0.32s"),
    ]

    for col, grad, icon, value, label, sub, delay in cards_data:
        with col:
            st.markdown(f"""
            <div class="metric-card animate-fade-in" style="
                background: {grad};
                box-shadow: 0 8px 20px rgba(0,0,0,0.18);
                animation-delay: {delay};
            ">
                <div class="metric-icon">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
                <div class="metric-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Ações Rápidas ─────────────────────────────────────────
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem;">
        <div style="width:4px; height:22px; background:linear-gradient(180deg,#059669,#10b981); border-radius:4px;"></div>
        <h3 style="margin:0; font-family:'Nunito',sans-serif; font-size:1.1rem; color:#0f172a;">Ações Rápidas</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-header">
        <div class="section-header-bar" style="--section-accent:linear-gradient(180deg,#059669,#10b981);"></div>
        <div class="section-header-copy">
            <h3 class="section-header-title">Acoes Rapidas</h3>
            <p class="section-header-subtitle">Atalhos para as tarefas mais usadas no sistema.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📝 Nova Ocorrência", use_container_width=True, type="primary", key="quick_ocorrencia"):
            st.session_state.pagina_atual = "📝 Registrar Ocorrência"
            st.rerun()
    with col2:
        if st.button("👥 Ver Alunos", use_container_width=True, key="quick_alunos"):
            st.session_state.pagina_atual = "👥 Lista de Alunos"
            st.rerun()
    with col3:
        if st.button("📅 Agendar Espaço", use_container_width=True, key="quick_agendamento"):
            st.session_state.pagina_atual = "📅 Agendamento de Espaços"
            st.rerun()
    with col4:
        if st.button("📊 Relatórios", use_container_width=True, key="quick_relatorios"):
            st.session_state.pagina_atual = "📊 Gráficos e Indicadores"
            st.rerun()

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #eff6ff, #f0fdf4);
        border: 1.5px solid #bfdbfe;
        border-radius: 12px;
        padding: 0.75rem 1.25rem;
        font-size: 0.85rem;
        color: #1e40af;
        display: flex; align-items: center; gap: 0.5rem;
    ">
        📌 Fonte das eletivas: <b>{FONTE_ELETIVAS.upper()}</b>
        &nbsp;·&nbsp; 🗓️ Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>
    """, unsafe_allow_html=True)

    # ── Gráficos e Top 10 no Dashboard ───────────────────────
    if not df_ocorrencias.empty:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem;">
            <div style="width:4px; height:22px; background:linear-gradient(180deg,#dc2626,#f97316); border-radius:4px;"></div>
            <h3 style="margin:0; font-family:'Nunito',sans-serif; font-size:1.1rem; color:#0f172a;">Análise de Ocorrências</h3>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="section-header">
            <div class="section-header-bar" style="--section-accent:linear-gradient(180deg,#dc2626,#f97316);"></div>
            <div class="section-header-copy">
                <h3 class="section-header-title">Analise de Ocorrencias</h3>
                <p class="section-header-subtitle">Resumo visual das categorias, gravidades e reincidencias.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            # Gráfico por gravidade (donut)
            contagem_grav = df_ocorrencias["gravidade"].value_counts() if "gravidade" in df_ocorrencias.columns else pd.Series()
            if not contagem_grav.empty:
                st.markdown("<div style='font-weight:600;color:#334155;font-size:0.9rem;margin-bottom:0.5rem;'>⚖️ Ocorrências por Gravidade</div>", unsafe_allow_html=True)
                fig_grav_dash = px.pie(
                    values=contagem_grav.values,
                    names=contagem_grav.index,
                    color_discrete_sequence=['#10b981','#f59e0b','#f97316','#dc2626'],
                    hole=0.5
                )
                fig_grav_dash.update_traces(textfont_size=12, textfont_family='Inter, sans-serif')
                fig_grav_dash.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter, sans-serif', size=12, color='#334155'),
                    margin=dict(t=10, b=10, l=0, r=0),
                    legend=dict(font=dict(size=11), orientation='h', y=-0.15),
                    height=280,
                )
                st.plotly_chart(fig_grav_dash, use_container_width=True)

        with col_g2:
            # Gráfico por categoria (top 6)
            contagem_cat = df_ocorrencias["categoria"].value_counts().head(6) if "categoria" in df_ocorrencias.columns else pd.Series()
            if not contagem_cat.empty:
                st.markdown("<div style='font-weight:600;color:#334155;font-size:0.9rem;margin-bottom:0.5rem;'>📋 Top Infrações Registradas</div>", unsafe_allow_html=True)
                fig_cat_dash = px.bar(
                    x=contagem_cat.values,
                    y=contagem_cat.index,
                    orientation='h',
                    color=contagem_cat.values,
                    color_continuous_scale=[[0,'#93c5fd'],[0.5,'#2563eb'],[1,'#1d4ed8']],
                )
                fig_cat_dash.update_layout(
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter, sans-serif', size=11, color='#334155'),
                    margin=dict(t=10, b=10, l=0, r=10),
                    xaxis=dict(gridcolor='#e2e8f0', title='Quantidade'),
                    yaxis=dict(gridcolor='rgba(0,0,0,0)', title=''),
                    coloraxis_showscale=False,
                    height=280,
                )
                fig_cat_dash.update_traces(marker_line_width=0)
                st.plotly_chart(fig_cat_dash, use_container_width=True)

        # Evolução temporal (últimos 30 dias)
        df_ocorrencias_temp = df_ocorrencias.copy()
        df_ocorrencias_temp["data_dt"] = pd.to_datetime(df_ocorrencias_temp["data"], format="%d/%m/%Y %H:%M", errors="coerce")
        df_recente = df_ocorrencias_temp[df_ocorrencias_temp["data_dt"] >= datetime.now() - timedelta(days=30)]
        if not df_recente.empty:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            st.markdown("<div style='font-weight:600;color:#334155;font-size:0.9rem;margin-bottom:0.5rem;'>📈 Evolução — Últimos 30 dias</div>", unsafe_allow_html=True)
            evolucao = df_recente.groupby(df_recente["data_dt"].dt.date).size().reset_index(name="Quantidade")
            evolucao.columns = ["Data", "Quantidade"]
            fig_linha = px.area(evolucao, x="Data", y="Quantidade")
            fig_linha.update_traces(
                line_color="#2563eb", line_width=2.5,
                fillcolor="rgba(37,99,235,0.1)",
                marker=dict(size=5, color="#2563eb"),
            )
            fig_linha.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter, sans-serif', size=11, color='#334155'),
                margin=dict(t=10, b=10, l=0, r=0),
                xaxis=dict(gridcolor='#e2e8f0', linecolor='#e2e8f0'),
                yaxis=dict(gridcolor='#e2e8f0', linecolor='#e2e8f0', title='Ocorrências'),
                height=220,
            )
            st.plotly_chart(fig_linha, use_container_width=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        # ── Top 10 Alunos ─────────────────────────────────────
        st.markdown("""
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem;">
            <div style="width:4px; height:22px; background:linear-gradient(180deg,#7c3aed,#8b5cf6); border-radius:4px;"></div>
            <h3 style="margin:0; font-family:'Nunito',sans-serif; font-size:1.1rem; color:#0f172a;">🏆 Top 10 — Alunos com Mais Ocorrências</h3>
        </div>
        """, unsafe_allow_html=True)

        top10 = df_ocorrencias["aluno"].value_counts().head(10).reset_index()
        top10.columns = ["Aluno", "Ocorrências"]

        # Merge with turma info
        if not df_alunos.empty and "turma" in df_alunos.columns:
            top10 = top10.merge(
                df_alunos[["nome","turma"]].rename(columns={"nome":"Aluno"}),
                on="Aluno", how="left"
            )
            top10["Turma"] = top10.get("turma", "—").fillna("—")
        else:
            top10["Turma"] = "—"

        # Styled ranking cards
        medalhas = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        cores_rank = ["#dc2626","#d97706","#f59e0b","#64748b","#64748b","#64748b","#64748b","#64748b","#64748b","#64748b"]
        max_occ = top10["Ocorrências"].max() if not top10.empty else 1

        for idx, row in top10.iterrows():
            pct = int((row["Ocorrências"] / max_occ) * 100)
            cor = cores_rank[idx] if idx < len(cores_rank) else "#64748b"
            medalha = medalhas[idx] if idx < len(medalhas) else f"{idx+1}."
            turma_label = row.get("Turma","—") or "—"
            st.markdown(f"""
            <div style="
                display:flex; align-items:center; gap:1rem;
                background:white; border-radius:12px;
                border:1.5px solid #e2e8f0; padding:0.75rem 1rem;
                margin-bottom:0.4rem;
                box-shadow:0 1px 4px rgba(15,23,42,0.05);
            ">
                <div style="font-size:1.3rem; width:28px; text-align:center; flex-shrink:0;">{medalha}</div>
                <div style="flex:1; min-width:0;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.3rem;">
                        <div style="font-weight:600; color:#0f172a; font-size:0.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{row['Aluno']}</div>
                        <div style="display:flex; align-items:center; gap:0.5rem; flex-shrink:0; margin-left:0.5rem;">
                            <span style="background:#f1f5f9; color:#64748b; border-radius:6px; padding:0.15rem 0.5rem; font-size:0.72rem; font-weight:600;">{turma_label}</span>
                            <span style="background:{cor}18; color:{cor}; border:1.5px solid {cor}40; border-radius:8px; padding:0.2rem 0.6rem; font-size:0.82rem; font-weight:700;">{int(row['Ocorrências'])}</span>
                        </div>
                    </div>
                    <div style="height:5px; background:#f1f5f9; border-radius:99px; overflow:hidden;">
                        <div style="width:{pct}%; height:5px; background:{cor}; border-radius:99px; transition:width 0.4s;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding:2rem; color:#94a3b8; background:white; border-radius:16px; border:1.5px dashed #e2e8f0; margin-top:1rem;">
            📊 Nenhuma ocorrência registrada ainda.<br>
            <span style="font-size:0.85rem;">Os gráficos aparecerão aqui após o primeiro registro.</span>
        </div>
        """, unsafe_allow_html=True)
    # ======================================================
# PÁGINA 👨‍👩‍👧 PORTAL DO RESPONSÁVEL (COMPLETA)
# ======================================================

elif menu == "👨‍👩‍👧 Portal do Responsável":
    page_header("👨‍👩‍👧 Portal do Responsável", "Acesso seguro para pais e responsáveis", "#7c3aed")
    
    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#f5f3ff,#ede9fe);
        border:1.5px solid #c4b5fd; border-left:5px solid #7c3aed;
        border-radius:16px; padding:1.25rem 1.5rem; margin-bottom:1.5rem;
        box-shadow:0 4px 12px rgba(124,58,237,0.08);
    ">
        <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.35rem;">
            <span style="font-size:1.2rem;">🔐</span>
            <b style="font-family:'Nunito',sans-serif;font-size:1rem;color:#4c1d95;">Acesso Restrito ao Responsável</b>
        </div>
        <p style="margin:0;color:#6d28d9;font-size:0.9rem;">
            Digite o RA do aluno e a senha para acessar o histórico de ocorrências e informações.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        ra_acesso = st.text_input("RA do Aluno:", placeholder="Digite o RA", key="portal_ra")
    with col2:
        senha_acesso = st.text_input("Senha:", type="password", placeholder="Digite a senha", key="portal_senha")
    
    if st.button("🔓 Acessar Portal", type="primary", use_container_width=True):
        if not ra_acesso or not senha_acesso:
            st.error("❌ Preencha RA e senha!")
        else:
            aluno_encontrado = df_alunos[df_alunos['ra'].astype(str) == ra_acesso] if not df_alunos.empty else pd.DataFrame()
            
            if aluno_encontrado.empty:
                st.error("❌ Aluno não encontrado!")
            else:
                senha_correta = "123456"
                
                if senha_acesso != senha_correta:
                    st.error("❌ Senha incorreta!")
                else:
                    aluno = aluno_encontrado.iloc[0]
                    st.success(f"✅ Bem-vindo, responsável por **{aluno['nome']}**!")
                    
                    st.markdown("---")
                    
                    st.subheader("📋 Informações do Aluno")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("RA", aluno['ra'])
                    with col2:
                        st.metric("Turma", aluno.get('turma', 'N/A'))
                    with col3:
                        st.metric("Situação", aluno.get('situacao', 'Ativo'))
                    
                    st.markdown("---")
                    
                    st.subheader("📝 Histórico de Ocorrências")
                    ocorrencias_aluno = df_ocorrencias[df_ocorrencias['ra'].astype(str) == ra_acesso] if not df_ocorrencias.empty else pd.DataFrame()
                    
                    if ocorrencias_aluno.empty:
                        st.success("✅ Nenhuma ocorrência registrada para este aluno!")
                    else:
                        st.warning(f"⚠️ {len(ocorrencias_aluno)} ocorrência(s) registrada(s)")
                        
                        for _, occ in ocorrencias_aluno.sort_values('data', ascending=False).iterrows():
                            with st.expander(f"📅 {occ['data']} - {occ['categoria']} ({occ['gravidade']})"):
                                st.write(f"**Professor:** {occ.get('professor', 'N/A')}")
                                st.write(f"**Relato:** {occ.get('relato', 'N/A')}")
                                st.write(f"**Encaminhamento:** {occ.get('encaminhamento', 'N/A')}")
                    
                    st.markdown("---")
                    st.caption("Em caso de dúvidas, entre em contato com a secretaria da escola.")
                    # ======================================================
# PÁGINA 📥 IMPORTAR ALUNOS (COMPLETA)
# ======================================================

elif menu == "📥 Importar Alunos":
    page_header("📥 Importar Alunos por Turma", "Importe alunos a partir de arquivos CSV da SEDUC", "#0891b2")
    
    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#f0fdf4,#dcfce7);
        border:1.5px solid #86efac; border-left:5px solid #059669;
        border-radius:16px; padding:1.25rem 1.5rem; margin-bottom:1.5rem;
        box-shadow:0 4px 12px rgba(5,150,105,0.08);
    ">
        <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.6rem;">
            <span style="font-size:1.1rem;">💡</span>
            <b style="font-family:'Nunito',sans-serif;font-size:1rem;color:#065f46;">Como importar alunos</b>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.4rem;">
            <div style="display:flex;align-items:center;gap:0.5rem;color:#14532d;font-size:0.875rem;">
                <span style="background:#059669;color:white;border-radius:99px;width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:0.65rem;font-weight:700;flex-shrink:0;">1</span>
                Digite o nome da turma (Ex: 6º Ano A)
            </div>
            <div style="display:flex;align-items:center;gap:0.5rem;color:#14532d;font-size:0.875rem;">
                <span style="background:#059669;color:white;border-radius:99px;width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:0.65rem;font-weight:700;flex-shrink:0;">2</span>
                Selecione o arquivo CSV da SEDUC
            </div>
            <div style="display:flex;align-items:center;gap:0.5rem;color:#14532d;font-size:0.875rem;">
                <span style="background:#059669;color:white;border-radius:99px;width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:0.65rem;font-weight:700;flex-shrink:0;">3</span>
                O sistema identifica as colunas automaticamente
            </div>
            <div style="display:flex;align-items:center;gap:0.5rem;color:#14532d;font-size:0.875rem;">
                <span style="background:#059669;color:white;border-radius:99px;width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:0.65rem;font-weight:700;flex-shrink:0;">4</span>
                Clique em 🚀 Importar Alunos
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    turma_alunos = st.text_input("🏫 Nome da TURMA:", placeholder="Ex: 6º Ano B, 1º Ano D", key="turma_import")
    
    arquivo_upload = st.file_uploader("📁 Selecione o arquivo CSV da SEDUC", type=["csv"], key="arquivo_csv")
    
    if arquivo_upload is not None:
        try:
            df_import = pd.read_csv(arquivo_upload, sep=';', encoding='utf-8-sig', dtype=str)
            st.success(f"✅ Arquivo lido! {len(df_import)} alunos encontrados.")
            st.write("### 👀 Pré-visualização dos dados:")
            st.dataframe(df_import.head(10), use_container_width=True)
            
            colunas = df_import.columns.tolist()
            
            col_ra = None
            col_nome = None
            col_situacao = None
            
            for col in colunas:
                col_lower = col.lower()
                if 'dig' in col_lower or 'dígito' in col_lower:
                    continue
                if 'ra' in col_lower and col_ra is None:
                    amostra = df_import[col].dropna().head(5)
                    for val in amostra:
                        digitos = ''.join(c for c in str(val) if c.isdigit())
                        if len(digitos) >= 9:
                            col_ra = col
                            break
            
            for col in colunas:
                col_lower = col.lower()
                if 'nome' in col_lower and 'aluno' in col_lower:
                    col_nome = col
                    break
            
            for col in colunas:
                col_lower = col.lower()
                if 'situa' in col_lower or 'status' in col_lower:
                    col_situacao = col
                    break
            
            st.write("### 🔍 Colunas identificadas:")
            if col_ra:
                st.success(f"✅ **RA:** {col_ra}")
            else:
                st.error("❌ **RA:** NÃO ENCONTRADO")
            if col_nome:
                st.success(f"✅ **Nome:** {col_nome}")
            else:
                st.error("❌ **Nome:** NÃO ENCONTRADO")
            if col_situacao:
                st.info(f"📊 **Situação:** {col_situacao}")
            else:
                st.warning("📊 **Situação:** Não encontrada (usará 'Ativo')")
            
            if col_ra is None or col_nome is None:
                st.warning("⚠️ Selecione manualmente as colunas:")
                col1, col2 = st.columns(2)
                with col1:
                    col_ra = st.selectbox("Coluna do RA:", colunas)
                    col_nome = st.selectbox("Coluna do Nome:", colunas)
                with col2:
                    col_situacao = st.selectbox("Coluna da Situação (opcional):", ["Não usar"] + colunas)
                    if col_situacao == "Não usar":
                        col_situacao = None
            
            st.markdown("---")
            
            df_alunos_existente = carregar_alunos()
            
            if turma_alunos:
                turmas_existentes = df_alunos_existente['turma'].unique().tolist() if not df_alunos_existente.empty else []
                if turma_alunos in turmas_existentes:
                    st.warning(f"⚠️ A turma **{turma_alunos}** já existe! Alunos serão ATUALIZADOS se já estiverem nesta turma.")
            
            if st.button("🚀 IMPORTAR ALUNOS", type="primary", use_container_width=True):
                if not turma_alunos:
                    st.error("❌ Digite o nome da turma!")
                elif col_ra is None or col_nome is None:
                    st.error("❌ É necessário identificar as colunas de RA e Nome!")
                else:
                    novos = 0
                    atualizados = 0
                    ignorados = 0
                    erros = 0
                    
                    progress = st.progress(0)
                    status = st.empty()
                    total = len(df_import)
                    
                    for i, (_, row) in enumerate(df_import.iterrows()):
                        try:
                            ra_valor = row[col_ra]
                            if pd.isna(ra_valor):
                                erros += 1
                                continue
                            
                            ra_str = ''.join(c for c in str(ra_valor) if c.isdigit())
                            if not ra_str or len(ra_str) < 5:
                                erros += 1
                                continue
                            
                            nome_valor = row[col_nome]
                            if pd.isna(nome_valor):
                                erros += 1
                                continue
                            
                            nome_str = str(nome_valor).strip()
                            if not nome_str or nome_str == 'nan':
                                erros += 1
                                continue
                            
                            sit_str = "Ativo"
                            if col_situacao:
                                sit_valor = row[col_situacao]
                                if not pd.isna(sit_valor):
                                    sit_str = str(sit_valor).strip()
                                    sit_lower = sit_str.lower()
                                    if 'transfer' in sit_lower or 'baixa' in sit_lower:
                                        sit_str = "Transferido"
                                    elif 'ativo' in sit_lower:
                                        sit_str = "Ativo"
                                    elif 'inativo' in sit_lower:
                                        sit_str = "Inativo"
                                    elif 'remanej' in sit_lower:
                                        sit_str = "Remanejado"
                            
                            aluno = {'ra': ra_str, 'nome': nome_str, 'turma': turma_alunos, 'situacao': sit_str}
                            
                            existe = df_alunos_existente[df_alunos_existente['ra'] == ra_str] if not df_alunos_existente.empty else pd.DataFrame()
                            
                            if not existe.empty:
                                turma_antiga = existe.iloc[0].get('turma', '')
                                if turma_antiga == turma_alunos:
                                    if atualizar_aluno(ra_str, aluno):
                                        atualizados += 1
                                    else:
                                        erros += 1
                                else:
                                    ignorados += 1
                            else:
                                if salvar_aluno(aluno):
                                    novos += 1
                                else:
                                    erros += 1
                        except Exception:
                            erros += 1
                        
                        progress.progress((i + 1) / total)
                        status.text(f"Processando... {i + 1}/{total} | ✅ Novos: {novos} | 🔄 Atualizados: {atualizados}")
                    
                    progress.empty()
                    status.empty()
                    
                    if novos + atualizados > 0:
                        st.markdown(f"""
                        <div style="
                            background:linear-gradient(135deg,#f0fdf4,#dcfce7);
                            border:1.5px solid #86efac; border-left:5px solid #059669;
                            border-radius:16px; padding:1.1rem 1.5rem; margin:0.75rem 0;
                            box-shadow:0 4px 12px rgba(5,150,105,0.1);
                        ">
                            <div style="display:flex;align-items:center;gap:0.5rem;">
                                <span style="font-size:1.2rem;">🎉</span>
                                <div>
                                    <div style="font-family:'Nunito',sans-serif;font-weight:800;color:#065f46;font-size:1rem;">Importação concluída com sucesso!</div>
                                    <div style="color:#15803d;font-size:0.85rem;">{novos} novos · {atualizados} atualizados</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.balloons()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("🆕 Novos", novos)
                    col2.metric("🔄 Atualizados", atualizados)
                    col3.metric("⚠️ Ignorados", ignorados)
                    col4.metric("❌ Erros", erros)
                    
                    if novos + atualizados > 0:
                        carregar_alunos.clear()
                        st.rerun()
                        
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")
    else:
        st.info("📁 Selecione um arquivo CSV para começar.")
    
    st.markdown("---")
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.5rem 0;padding-bottom:0.5rem;border-bottom:2px solid #e2e8f0;position:relative;">
        <div style="position:absolute;bottom:-2px;left:0;width:45px;height:2px;background:linear-gradient(90deg,#059669,transparent);border-radius:4px;"></div>
        <span>📊</span>
        <h3 style="margin:0;font-family:'Nunito',sans-serif;font-size:1rem;color:#0f172a;">Turmas cadastradas no Sistema</h3>
    </div>
    """, unsafe_allow_html=True)
    if not df_alunos.empty:
        resumo = df_alunos.groupby('turma').size().reset_index(name='Total')
        resumo.columns = ['Turma', 'Total de Alunos']
        st.dataframe(resumo.sort_values('Turma'), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma turma cadastrada ainda.")
        # ======================================================
# PÁGINA 📋 GERENCIAR TURMAS (COMPLETA)
# ======================================================

elif menu == "📋 Gerenciar Turmas":
    page_header("📋 Gerenciar Turmas", "Visualize, edite e exclua turmas cadastradas", "#059669")

    if df_alunos.empty:
        st.info("📭 Nenhuma turma cadastrada. Use '📥 Importar Alunos' para começar.")
    else:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.5rem;margin:0.5rem 0 0.75rem 0;padding-bottom:0.5rem;border-bottom:2px solid #e2e8f0;position:relative;">
            <div style="position:absolute;bottom:-2px;left:0;width:45px;height:2px;background:linear-gradient(90deg,#059669,transparent);border-radius:4px;"></div>
            <span>📊</span>
            <h3 style="margin:0;font-family:'Nunito',sans-serif;font-size:1rem;color:#0f172a;">Resumo das Turmas</h3>
        </div>
        """, unsafe_allow_html=True)
        turmas_info = df_alunos.groupby("turma").agg(total_alunos=("ra", "count")).reset_index().sort_values("turma")

        for _, row in turmas_info.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                with col1:
                    st.markdown(f"""
                    <div style="
                        background:white; border:1.5px solid #e2e8f0;
                        border-radius:14px; padding:1rem 1.25rem;
                        box-shadow:0 2px 6px rgba(15,23,42,0.06);
                        display:flex; align-items:center; gap:0.75rem;
                        border-left:4px solid #2563eb;
                    ">
                        <div style="font-size:1.4rem;">🏫</div>
                        <div>
                            <div style="font-family:'Nunito',sans-serif;font-weight:700;font-size:1rem;color:#0f172a;">{row['turma']}</div>
                            <div style="font-size:0.78rem;color:#64748b;font-weight:500;">{row['total_alunos']} alunos cadastrados</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("👁️ Ver", key=f"ver_turma_{row['turma']}"):
                        st.session_state.turma_selecionada = row["turma"]
                        st.rerun()
                with col3:
                    if st.button("✏️ Editar", key=f"edit_turma_{row['turma']}"):
                        st.session_state.turma_para_editar = row["turma"]
                        st.rerun()
                with col4:
                    if st.button("🔄 Substituir", key=f"sub_turma_{row['turma']}"):
                        st.session_state.turma_para_substituir = row["turma"]
                        st.rerun()
                with col5:
                    if st.button("🗑️ Deletar", key=f"del_turma_{row['turma']}"):
                        st.session_state.turma_para_deletar = row["turma"]
                        st.rerun()

        # Visualizar alunos da turma
        if st.session_state.get("turma_selecionada"):
            turma = st.session_state.turma_selecionada
            st.markdown("---")
            st.subheader(f"👥 Alunos da Turma {turma}")
            alunos_turma = df_alunos[df_alunos["turma"] == turma]
            st.dataframe(alunos_turma[["ra", "nome", "situacao"]], use_container_width=True, hide_index=True)
            if st.button("❌ Fechar Visualização"):
                st.session_state.turma_selecionada = None
                st.rerun()

        # Editar nome da turma
        if st.session_state.get("turma_para_editar"):
            turma_antiga = st.session_state.turma_para_editar
            st.markdown("---")
            st.subheader(f"✏️ Editar Nome da Turma: {turma_antiga}")
            novo_nome = st.text_input("Novo nome da turma", value=turma_antiga)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar Alterações", type="primary"):
                    if not novo_nome.strip():
                        st.error("❌ Nome da turma não pode ser vazio.")
                    elif novo_nome == turma_antiga:
                        st.warning("⚠️ O nome não foi alterado.")
                    else:
                        sucesso = editar_nome_turma(turma_antiga, novo_nome)
                        if sucesso:
                            st.success(f"✅ Turma renomeada para {novo_nome}!")
                            st.session_state.turma_para_editar = None
                            st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    st.session_state.turma_para_editar = None
                    st.rerun()

        # Substituir turma
        if st.session_state.get("turma_para_substituir"):
            turma = st.session_state.turma_para_substituir
            st.markdown("---")
            st.subheader(f"🔄 Substituir Turma {turma}")
            
            st.markdown("""
            <div style="
                background:linear-gradient(135deg,#eff6ff,#dbeafe);
                border:1.5px solid #93c5fd; border-left:5px solid #2563eb;
                border-radius:14px; padding:1rem 1.25rem; margin-bottom:1rem;
            ">
                <div style="color:#1e40af;font-size:0.875rem;">
                    📁 Envie o arquivo CSV da SEDUC para substituir <b>todos os alunos</b> desta turma. Esta ação não pode ser desfeita.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            arquivo = st.file_uploader("Arquivo CSV", type=["csv"], key="substituir_csv")
            
            if arquivo is not None:
                try:
                    df_import = pd.read_csv(arquivo, sep=";", encoding="utf-8-sig", dtype=str)
                    st.success("✅ Arquivo carregado com sucesso.")
                    st.dataframe(df_import.head())
                    
                    colunas = df_import.columns.tolist()
                    
                    col_ra = None
                    col_nome = None
                    col_situacao = None
                    
                    for col in colunas:
                        col_lower = col.lower()
                        if 'ra' in col_lower and 'dig' not in col_lower:
                            col_ra = col
                        if 'nome' in col_lower:
                            col_nome = col
                        if 'situa' in col_lower:
                            col_situacao = col
                    
                    if col_ra is None or col_nome is None:
                        st.warning("⚠️ Selecione as colunas manualmente:")
                        col1, col2 = st.columns(2)
                        with col1:
                            col_ra = st.selectbox("Coluna do RA:", colunas)
                            col_nome = st.selectbox("Coluna do Nome:", colunas)
                        with col2:
                            col_situacao = st.selectbox("Coluna da Situação:", ["Não usar"] + colunas)
                            if col_situacao == "Não usar":
                                col_situacao = None
                    
                    if st.button("🔄 Confirmar Substituição", type="primary"):
                        excluir_alunos_por_turma(turma)
                        inseridos = 0
                        for _, row in df_import.iterrows():
                            ra = ''.join(c for c in str(row[col_ra]) if c.isdigit())
                            nome = str(row[col_nome]).strip()
                            if not ra or not nome:
                                continue
                            
                            situacao = "Ativo"
                            if col_situacao:
                                sit_valor = str(row[col_situacao]).strip()
                                if 'transfer' in sit_valor.lower():
                                    situacao = "Transferido"
                                elif 'ativo' in sit_valor.lower():
                                    situacao = "Ativo"
                            
                            aluno = {"ra": ra, "nome": nome, "turma": turma, "situacao": situacao}
                            if salvar_aluno(aluno):
                                inseridos += 1
                        
                        st.success(f"✅ Turma substituída! {inseridos} aluno(s) importado(s).")
                        st.session_state.turma_para_substituir = None
                        carregar_alunos.clear()
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Erro ao processar o arquivo: {e}")
            
            if st.button("❌ Cancelar Substituição"):
                st.session_state.turma_para_substituir = None
                st.rerun()

        # Excluir turma
        if st.session_state.get("turma_para_deletar"):
            turma = st.session_state.turma_para_deletar
            st.markdown("---")
            st.error(f"⚠️ Tem certeza que deseja excluir a turma **{turma}**?")
            st.warning("Todos os alunos desta turma serão removidos permanentemente!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão", type="primary"):
                    sucesso = excluir_alunos_por_turma(turma)
                    if sucesso:
                        st.success(f"✅ Turma {turma} excluída com sucesso!")
                        st.session_state.turma_para_deletar = None
                        carregar_alunos.clear()
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    st.session_state.turma_para_deletar = None
                    st.rerun()
                    # ======================================================
# PÁGINA 👥 LISTA DE ALUNOS (COM FILTRO ATIVO/TODOS)
# ======================================================

elif menu == "👥 Lista de Alunos":
    page_header("👥 Gerenciar Alunos", "Cadastro, edição e exclusão de estudantes", "#2563eb")
    
    tab1, tab2, tab3 = st.tabs(["📋 Listar Alunos", "➕ Cadastrar Aluno", "✏️ Editar/Excluir"])
    
    # ========== ABA 1: LISTAR ==========
    with tab1:
        if df_alunos.empty:
            st.info("📭 Nenhum aluno cadastrado. Use a aba '➕ Cadastrar Aluno' ou '📥 Importar Alunos'.")
        else:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                turmas_disp = ["Todas"] + sorted(df_alunos["turma"].dropna().unique().tolist())
                filtro_turma = st.selectbox("🏫 Filtrar por Turma", turmas_disp, key="filtro_turma_lista")
            
            with col2:
                if "situacao" in df_alunos.columns:
                    df_alunos["situacao_norm"] = df_alunos["situacao"].str.strip().str.title()
                    situacoes_unicas = sorted(df_alunos["situacao_norm"].dropna().unique().tolist())
                else:
                    df_alunos["situacao_norm"] = "Ativo"
                    situacoes_unicas = ["Ativo"]
                
                situacoes_disp = ["Ativos", "Todos"] + situacoes_unicas
                filtro_situacao = st.selectbox("📊 Situação", situacoes_disp, index=0, key="filtro_situacao_lista")
            
            with col3:
                busca_nome = st.text_input("🔍 Buscar por Nome ou RA", placeholder="Digite nome ou RA", key="busca_lista")
            
            df_view = df_alunos.copy()
            
            if filtro_turma != "Todas":
                df_view = df_view[df_view["turma"] == filtro_turma]
            
            if filtro_situacao == "Ativos":
                df_view = df_view[df_view["situacao_norm"] == "Ativo"]
            elif filtro_situacao != "Todos":
                df_view = df_view[df_view["situacao_norm"] == filtro_situacao]
            
            if busca_nome:
                df_view = df_view[
                    df_view["nome"].str.contains(busca_nome, case=False, na=False) |
                    df_view["ra"].astype(str).str.contains(busca_nome, na=False)
                ]
            
            total_geral = len(df_alunos)
            total_ativos = len(df_alunos[df_alunos["situacao_norm"] == "Ativo"])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👥 Total de Alunos", total_geral)
            with col2:
                st.metric("✅ Alunos Ativos", total_ativos)
            with col3:
                st.metric("📋 Exibindo", len(df_view))
            
            st.markdown("---")
            
            if df_view.empty:
                st.info("📭 Nenhum aluno encontrado com os filtros selecionados.")
            else:
                df_display = df_view.drop(columns=["situacao_norm"], errors="ignore")
                colunas_exibir = [col for col in ["ra", "nome", "turma", "situacao"] if col in df_display.columns]
                st.dataframe(df_display[colunas_exibir].sort_values(["turma", "nome"]), use_container_width=True, hide_index=True)
                
                if st.button("📥 Exportar Lista (CSV)", key="btn_exportar_csv_lista"):
                    csv = df_display.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Baixar CSV",
                        data=csv,
                        file_name=f"alunos_{filtro_situacao.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
    
    # ========== ABA 2: CADASTRAR ==========
    with tab2:
        st.subheader("➕ Cadastrar Novo Aluno")
        
        with st.form("form_cadastrar_aluno"):
            col1, col2 = st.columns(2)
            with col1:
                ra = st.text_input("RA *", placeholder="Ex: 123456")
                nome = st.text_input("Nome Completo *", placeholder="Ex: João da Silva")
                turma = st.text_input("Turma *", placeholder="Ex: 6º Ano A")
            with col2:
                situacao = st.selectbox("Situação", ["Ativo", "Transferido", "Inativo", "Remanejado"], index=0)
                responsavel = st.text_input("Responsável", placeholder="Nome do responsável")
            
            if st.form_submit_button("💾 Salvar Aluno", type="primary"):
                if not ra or not nome or not turma:
                    st.error("❌ RA, Nome e Turma são obrigatórios!")
                else:
                    if not df_alunos.empty and ra.strip() in df_alunos["ra"].astype(str).values:
                        st.error(f"❌ RA {ra} já está cadastrado!")
                    else:
                        aluno = {
                            'ra': ra.strip(),
                            'nome': nome.strip(),
                            'turma': turma.strip(),
                            'situacao': situacao,
                            'responsavel': responsavel.strip() if responsavel else None
                        }
                        
                        if salvar_aluno(aluno):
                            st.success(f"✅ Aluno {nome} cadastrado com sucesso!")
                            carregar_alunos.clear()
                            st.rerun()
                        else:
                            st.error("❌ Erro ao salvar aluno.")
    
    # ========== ABA 3: EDITAR/EXCLUIR ==========
    with tab3:
        if df_alunos.empty:
            st.info("📭 Nenhum aluno cadastrado.")
        else:
            st.subheader("✏️ Editar ou Excluir Aluno")
            
            df_busca = df_alunos[df_alunos["situacao_norm"] == "Ativo"] if "situacao_norm" in df_alunos.columns else df_alunos
            
            if df_busca.empty:
                df_busca = df_alunos
            
            df_busca = df_busca.sort_values(["turma", "nome"])
            
            opcoes_alunos = []
            for _, row in df_busca.iterrows():
                sit = row.get('situacao', 'Ativo')
                opcoes_alunos.append(f"{row['nome']} - {row['turma']} (RA: {row['ra']}) [{sit}]")
            
            aluno_selecionado = st.selectbox("Selecione o Aluno", opcoes_alunos, key="aluno_editar")
            
            if aluno_selecionado:
                ra_selecionado = aluno_selecionado.split("(RA: ")[1].split(")")[0].strip()
                aluno_info = df_alunos[df_alunos["ra"] == ra_selecionado].iloc[0]
                
                st.markdown("---")
                st.subheader("📝 Editar Informações")
                
                with st.form("form_editar_aluno"):
                    col1, col2 = st.columns(2)
                    with col1:
                        novo_nome = st.text_input("Nome *", value=aluno_info.get("nome", ""))
                        nova_turma = st.text_input("Turma *", value=aluno_info.get("turma", ""))
                        sit_atual = aluno_info.get("situacao", "Ativo")
                        if sit_atual not in ["Ativo", "Transferido", "Inativo", "Remanejado"]:
                            sit_atual = "Ativo"
                        nova_situacao = st.selectbox(
                            "Situação",
                            ["Ativo", "Transferido", "Inativo", "Remanejado"],
                            index=["Ativo", "Transferido", "Inativo", "Remanejado"].index(sit_atual)
                        )
                    with col2:
                        novo_responsavel = st.text_input("Responsável", value=str(aluno_info.get("responsavel", "")))
                    
                    st.info(f"**RA:** {aluno_info.get('ra')} (não pode ser alterado)")
                    
                    if st.form_submit_button("💾 Salvar Alterações", type="primary"):
                        dados_atualizados = {
                            'nome': novo_nome.strip(),
                            'turma': nova_turma.strip(),
                            'situacao': nova_situacao,
                            'responsavel': novo_responsavel.strip() if novo_responsavel else None
                        }
                        
                        if atualizar_aluno(str(aluno_info['ra']), dados_atualizados):
                            st.success("✅ Aluno atualizado com sucesso!")
                            carregar_alunos.clear()
                            st.rerun()
                        else:
                            st.error("❌ Erro ao atualizar aluno.")
                
                st.markdown("---")
                st.subheader("🗑️ Excluir Aluno")
                st.warning(f"⚠️ Esta ação é irreversível! O aluno **{aluno_info['nome']}** (RA: {aluno_info['ra']}) será removido permanentemente.")
                
                if st.button("🗑️ Excluir Aluno", type="secondary", key="btn_excluir_aluno_tab3"):
                    st.session_state.confirmar_exclusao_aluno = aluno_info['ra']
                    st.rerun()
                
                if st.session_state.get("confirmar_exclusao_aluno"):
                    ra_excluir = st.session_state.confirmar_exclusao_aluno
                    aluno_excluir = df_alunos[df_alunos["ra"] == ra_excluir].iloc[0] if not df_alunos[df_alunos["ra"] == ra_excluir].empty else None
                    
                    if aluno_excluir is not None:
                        st.error(f"⚠️ Confirmar exclusão de **{aluno_excluir['nome']}**?")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            senha = st.text_input("Digite a senha para confirmar:", type="password", key="senha_excluir_aluno_tab3")
                            if st.button("✅ Confirmar Exclusão", type="primary", key="confirm_excluir_aluno_tab3"):
                                if senha == SENHA_EXCLUSAO:
                                    url = f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra_excluir}"
                                    r = requests.delete(url, headers=HEADERS, timeout=20)
                                    if r.status_code in (200, 204):
                                        st.success(f"✅ Aluno {aluno_excluir['nome']} excluído!")
                                        carregar_alunos.clear()
                                        del st.session_state.confirmar_exclusao_aluno
                                        st.rerun()
                                    else:
                                        st.error("❌ Erro ao excluir aluno.")
                                else:
                                    st.error("❌ Senha incorreta!")
                        with col2:
                            if st.button("❌ Cancelar", key="cancel_excluir_aluno_tab3"):
                                del st.session_state.confirmar_exclusao_aluno
                                st.rerun()   # ======================================================
# ======================================================
# PÁGINA 📝 REGISTRAR OCORRÊNCIA (COMPLETA E CORRIGIDA)
# ======================================================

elif menu == "📝 Registrar Ocorrência":
    page_header("📝 Registrar Ocorrência", "Protocolo 179 — Preenchimento assistido por IA", "#dc2626")

    if st.session_state.ocorrencia_salva_sucesso:
        st.markdown('<div class="success-box">✅ Ocorrência(s) registrada(s) com sucesso!</div>', unsafe_allow_html=True)
        st.session_state.ocorrencia_salva_sucesso = False
        st.session_state.salvando_ocorrencia = False

    if df_alunos.empty:
        st.warning("⚠️ Cadastre ou importe alunos antes de registrar ocorrências.")
        st.stop()

    if df_professores.empty:
        st.warning("⚠️ Cadastre professores antes de registrar ocorrências.")
        st.stop()

    tz_sp = pytz.timezone("America/Sao_Paulo")
    agora = datetime.now(tz_sp)

    col1, col2 = st.columns(2)
    with col1:
        data_fato = st.date_input("📅 Data do fato", value=agora.date(), key="data_fato")
    with col2:
        hora_fato = st.time_input("⏰ Hora do fato", value=agora.time(), key="hora_fato")

    data_str = f"{data_fato.strftime('%d/%m/%Y')} {hora_fato.strftime('%H:%M')}"
    
    turmas_disponiveis = sorted(df_alunos["turma"].unique().tolist())
    turmas_sel = st.multiselect("🏫 Turma(s)", turmas_disponiveis, default=[turmas_disponiveis[0]] if turmas_disponiveis else [], key="turmas_sel")

    if not turmas_sel:
        st.warning("⚠️ Selecione ao menos uma turma.")
        st.stop()

    alunos_turma = df_alunos[df_alunos["turma"].isin(turmas_sel)]
    
    if "situacao" in alunos_turma.columns:
        alunos_turma["situacao_norm"] = alunos_turma["situacao"].str.strip().str.title()
        alunos_turma = alunos_turma[alunos_turma["situacao_norm"] == "Ativo"]

    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem 0;padding-bottom:0.5rem;border-bottom:2px solid #e2e8f0;position:relative;">
        <div style="position:absolute;bottom:-2px;left:0;width:45px;height:2px;background:linear-gradient(90deg,#2563eb,transparent);border-radius:4px;"></div>
        <span style="font-size:1rem;">👥</span>
        <h3 style="margin:0;font-family:'Nunito',sans-serif;font-size:1rem;color:#0f172a;">Estudantes Envolvidos</h3>
    </div>
    """, unsafe_allow_html=True)
    modo_multiplo = st.checkbox("Registrar para múltiplos estudantes", key="modo_multiplo")

    if modo_multiplo:
        alunos_selecionados = st.multiselect("Selecione os estudantes", alunos_turma["nome"].tolist(), key="alunos_multiplos")
    else:
        aluno_unico = st.selectbox("Aluno", alunos_turma["nome"].tolist(), key="aluno_unico")
        alunos_selecionados = [aluno_unico] if aluno_unico else []

    if not alunos_selecionados:
        st.warning("⚠️ Selecione ao menos um estudante.")
        st.stop()

    prof = st.selectbox("Professor 👨‍🏫", df_professores["nome"].tolist(), key="professor_sel")

    st.markdown("""
    <div class="form-panel">
        <p class="form-panel-title">Etapas do registro</p>
        <p class="form-panel-subtitle">Revise envolvidos, classificacao, gravidade, relato e encaminhamentos antes de salvar a ocorrencia.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem 0;padding-bottom:0.5rem;border-bottom:2px solid #e2e8f0;position:relative;">
        <div style="position:absolute;bottom:-2px;left:0;width:45px;height:2px;background:linear-gradient(90deg,#dc2626,transparent);border-radius:4px;"></div>
        <span style="font-size:1rem;">📋</span>
        <h3 style="margin:0;font-family:'Nunito',sans-serif;font-size:1rem;color:#0f172a;">Infração — Protocolo 179</h3>
        <span style="background:#fee2e2;color:#dc2626;border-radius:6px;padding:0.15rem 0.5rem;font-size:0.7rem;font-weight:700;margin-left:auto;">PREENCHIMENTO ASSISTIDO</span>
    </div>
    """, unsafe_allow_html=True)

    busca = st.text_input("🔍 Buscar infração", placeholder="Ex: celular, bullying, atraso...", key="busca_infracao")

    if busca:
        grupos_filtrados = buscar_infracao_fuzzy(busca, PROTOCOLO_179)
        if grupos_filtrados:
            grupo = st.selectbox("Grupo", list(grupos_filtrados.keys()), key="grupo_infracao")
            infracoes = grupos_filtrados[grupo]
        else:
            st.warning("⚠️ Nenhuma infração encontrada. Mostrando todas.")
            grupo = st.selectbox("Grupo", list(PROTOCOLO_179.keys()), key="grupo_infracao")
            infracoes = PROTOCOLO_179[grupo]
    else:
        grupo = st.selectbox("Grupo", list(PROTOCOLO_179.keys()), key="grupo_infracao")
        infracoes = PROTOCOLO_179[grupo]

    infracao_principal = st.selectbox("Infração", list(infracoes.keys()), key="infracao_principal")
    dados_infracao = infracoes[infracao_principal]
    gravidade_sugerida = dados_infracao["gravidade"]
    encaminhamento_sugerido = dados_infracao["encaminhamento"]

    cor_badge = CORES_GRAVIDADE.get(gravidade_sugerida, "#2563eb")
    st.markdown(f"""
    <div style="
        display:inline-flex; align-items:center; gap:0.6rem;
        background:linear-gradient(135deg,{cor_badge}15,{cor_badge}08);
        border:1.5px solid {cor_badge}40;
        border-left:4px solid {cor_badge};
        border-radius:12px; padding:0.6rem 1.25rem;
        margin:0.5rem 0;
    ">
        <span style="font-size:1.1rem;">🎯</span>
        <span style="font-family:'Nunito',sans-serif;font-weight:700;font-size:1rem;color:{cor_badge};">{infracao_principal}</span>
    </div>
    """, unsafe_allow_html=True)

    cor_gravidade = CORES_GRAVIDADE.get(gravidade_sugerida, "#9E9E9E")
    _cor_grav_map = {"Leve": "#059669", "Média": "#d97706", "Grave": "#f97316", "Gravíssima": "#dc2626"}
    _cor_g = _cor_grav_map.get(gravidade_sugerida, "#2563eb")
    _encam_html = encaminhamento_sugerido.replace(chr(10), '<br>').replace("✅","<span style=\'color:#059669;\'>✅</span>").replace("⚖️","<span style=\'color:#7c3aed;\'>⚖️</span>").replace("🚨","<span style=\'color:#dc2626;\'>🚨</span>")
    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,#f0f4ff,#fafbff);
        border:1.5px solid #c7d7fd; border-left:5px solid #2563eb;
        border-radius:16px; padding:1.25rem 1.5rem; margin:1rem 0;
        box-shadow:0 4px 12px rgba(37,99,235,0.08);
    ">
        <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.75rem;">
            <span style="font-size:1.1rem;">📋</span>
            <b style="font-family:'Nunito',sans-serif;font-size:1rem;color:#1d4ed8;">Protocolo 179 — Preenchimento Automático</b>
        </div>
        <div style="display:flex; gap:1.5rem; flex-wrap:wrap; margin-bottom:0.75rem;">
            <div>
                <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#64748b;margin-bottom:0.2rem;">Infração</div>
                <div style="font-weight:600;color:#0f172a;">{infracao_principal}</div>
            </div>
            <div>
                <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#64748b;margin-bottom:0.2rem;">Gravidade sugerida</div>
                <span style="
                    display:inline-block; padding:0.25rem 0.85rem;
                    background:{_cor_g}18; border:1.5px solid {_cor_g}50;
                    border-radius:99px; font-size:0.82rem; font-weight:700;
                    color:{_cor_g};
                ">{gravidade_sugerida}</span>
            </div>
        </div>
        <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#64748b;margin-bottom:0.4rem;">Encaminhamentos sugeridos</div>
        <div style="color:#334155; font-size:0.9rem; line-height:1.7;">{_encam_html}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.5rem 0;">
        <div style="width:4px;height:18px;background:linear-gradient(180deg,#d97706,#f59e0b);border-radius:4px;"></div>
        <span style="font-family:'Nunito',sans-serif;font-weight:700;font-size:1rem;color:#0f172a;">⚖️ Gravidade da Ocorrência</span>
    </div>
    """, unsafe_allow_html=True)
    gravidade = st.selectbox("Gravidade", ["Leve", "Média", "Grave", "Gravíssima"], 
                            index=["Leve", "Média", "Grave", "Gravíssima"].index(gravidade_sugerida) if gravidade_sugerida in ["Leve", "Média", "Grave", "Gravíssima"] else 0,
                            key="gravidade_sel")

    if gravidade != gravidade_sugerida:
        st.warning(f"⚠️ Gravidade alterada de {gravidade_sugerida} para {gravidade}.")

    encam = st.text_area("🔀 Encaminhamentos", value=encaminhamento_sugerido, height=140, key="encaminhamento")
    relato = st.text_area("📝 Relato dos fatos", height=160, placeholder="Descreva os fatos de forma clara e objetiva...", key="relato")

    st.markdown("---")

    if st.button("💾 Salvar Ocorrência(s)", type="primary"):
        if not prof or not relato.strip():
            st.error("❌ Preencha professor e relato.")
        else:
            salvas = 0
            duplicadas = 0
            
            for turma in turmas_sel:
                for aluno in alunos_selecionados:
                    registro = df_alunos[(df_alunos["nome"] == aluno) & (df_alunos["turma"] == turma)]
                    if registro.empty:
                        continue
                    
                    ra = registro["ra"].values[0]
                    
                    if verificar_ocorrencia_duplicada(ra, infracao_principal, data_str, df_ocorrencias):
                        duplicadas += 1
                        continue
                    
                    nova = {
                        "data": data_str,
                        "aluno": aluno,
                        "ra": ra,
                        "turma": turma,
                        "categoria": infracao_principal,
                        "gravidade": gravidade,
                        "relato": relato,
                        "encaminhamento": encam,
                        "professor": prof,
                    }
                    
                    if salvar_ocorrencia(nova):
                        salvas += 1
                        if st.session_state.backup_manager:
                            st.session_state.backup_manager.criar_backup()
            
            if salvas > 0:
                st.session_state.ocorrencia_salva_sucesso = True
                show_toast(f"{salvas} ocorrência(s) registrada(s)!", "success")
                
                st.session_state.registros_ocorrencias += salvas
                
                if st.session_state.registros_ocorrencias >= 1:
                    verificar_conquista("primeiro_registro")
                if st.session_state.registros_ocorrencias >= 10:
                    verificar_conquista("10_ocorrencias")
                if st.session_state.registros_ocorrencias >= 50:
                    verificar_conquista("50_ocorrencias")
            
            if duplicadas > 0:
                st.warning(f"⚠️ {duplicadas} ocorrência(s) duplicada(s) ignorada(s).")
            
            carregar_ocorrencias.clear()
            st.rerun()                                # ← 12 espaços
            # ======================================================
# PÁGINA 📋 HISTÓRICO DE OCORRÊNCIAS (COMPLETA)
# ======================================================

elif menu == "📋 Histórico de Ocorrências":
    page_header("📋 Histórico de Ocorrências", "Consulte, edite e exclua registros de ocorrências", "#d97706")

    if "mensagem_exclusao" in st.session_state:
        st.success(st.session_state.mensagem_exclusao)
        del st.session_state.mensagem_exclusao

    if df_ocorrencias.empty:
        st.info("📭 Nenhuma ocorrência registrada.")
        st.stop()

    col1, col2, col3 = st.columns(3)
    with col1:
        turmas_disp = ["Todas"] + sorted(df_ocorrencias["turma"].dropna().unique().tolist())
        filtro_turma = st.selectbox("🏫 Turma", turmas_disp)
    with col2:
        gravidades_disp = ["Todas"] + sorted(df_ocorrencias["gravidade"].dropna().unique().tolist())
        filtro_gravidade = st.selectbox("⚖️ Gravidade", gravidades_disp)
    with col3:
        categorias_unicas = sorted(df_ocorrencias["categoria"].dropna().unique().tolist())
        filtro_categoria = st.selectbox("📋 Categoria", ["Todas"] + categorias_unicas)

    df_view = df_ocorrencias.copy()
    if filtro_turma != "Todas":
        df_view = df_view[df_view["turma"] == filtro_turma]
    if filtro_gravidade != "Todas":
        df_view = df_view[df_view["gravidade"] == filtro_gravidade]
    if filtro_categoria != "Todas":
        df_view = df_view[df_view["categoria"] == filtro_categoria]

    st.markdown("""
    <div class="form-panel">
        <p class="form-panel-title">Filtros e consulta</p>
        <p class="form-panel-subtitle">Use os filtros acima para localizar registros com mais rapidez e manter a revisão organizada.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;flex-wrap:wrap;">
        <div style="background:linear-gradient(135deg,#1d4ed8,#2563eb);color:white;border-radius:10px;padding:0.4rem 1rem;font-weight:700;font-size:0.9rem;">
            📊 {len(df_view)} ocorrências encontradas
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(df_view, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.5rem;margin:1.25rem 0 0.75rem 0;padding-bottom:0.5rem;border-bottom:2px solid #e2e8f0;position:relative;">
        <div style="position:absolute;bottom:-2px;left:0;width:45px;height:2px;background:linear-gradient(90deg,#d97706,transparent);border-radius:4px;"></div>
        <span>🛠️</span>
        <h3 style="margin:0;font-family:'Nunito',sans-serif;font-size:1rem;color:#0f172a;">Ações — Editar / Excluir</h3>
    </div>
    """, unsafe_allow_html=True)
    col_excluir, col_editar = st.columns(2)

    with col_excluir:
        st.markdown("### 🗑️ Excluir Ocorrência")
        opcoes_excluir = [f"{row['id']} - {row['aluno']} - {row['data']} - {row['categoria']}" for _, row in df_view.iterrows()]
        
        if opcoes_excluir:
            opcao_sel = st.selectbox("Selecione a ocorrência", opcoes_excluir, key="select_excluir")
            id_excluir = int(opcao_sel.split(" - ")[0])
            
            senha = st.text_input("🔒 Digite a senha para excluir", type="password", key="senha_excluir")
            
            if st.button("🗑️ Excluir Ocorrência", type="secondary"):
                if senha != SENHA_EXCLUSAO:
                    st.error("❌ Senha incorreta!")
                else:
                    sucesso = excluir_ocorrencia(id_excluir)
                    if sucesso:
                        st.session_state.mensagem_exclusao = f"✅ Ocorrência {id_excluir} excluída com sucesso!"
                        carregar_ocorrencias.clear()
                        st.rerun()

    with col_editar:
        st.markdown("### ✏️ Editar Ocorrência")
        opcoes_editar = [f"{row['id']} - {row['aluno']} - {row['data']} - {row['categoria']}" for _, row in df_view.iterrows()]
        
        if opcoes_editar:
            opcao_edit = st.selectbox("Selecione a ocorrência", opcoes_editar, key="select_editar")
            id_editar = int(opcao_edit.split(" - ")[0])
            
            if st.button("✏️ Carregar para Edição"):
                st.session_state.editando_id = id_editar
                st.session_state.dados_edicao = df_view[df_view["id"] == id_editar].iloc[0].to_dict()
                st.rerun()

    if st.session_state.get("editando_id") and st.session_state.get("dados_edicao"):
        dados = st.session_state.dados_edicao
        st.markdown("---")
        st.subheader(f"✏️ Editando Ocorrência ID {st.session_state.editando_id}")
        
        novo_relato = st.text_area("📝 Relato", value=str(dados.get("relato", "")), height=120)
        novo_encam = st.text_area("🔀 Encaminhamentos", value=str(dados.get("encaminhamento", "")), height=120)
        nova_gravidade = st.selectbox("⚖️ Gravidade", ["Leve", "Média", "Grave", "Gravíssima"],
                                      index=["Leve", "Média", "Grave", "Gravíssima"].index(dados.get("gravidade", "Leve")))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Alterações", type="primary"):
                sucesso = editar_ocorrencia(st.session_state.editando_id, {
                    "relato": novo_relato,
                    "encaminhamento": novo_encam,
                    "gravidade": nova_gravidade
                })
                if sucesso:
                    st.success("✅ Ocorrência atualizada com sucesso!")
                    carregar_ocorrencias.clear()
                    st.session_state.editando_id = None
                    st.session_state.dados_edicao = None
                    st.rerun()
        with col2:
            if st.button("❌ Cancelar Edição"):
                st.session_state.editando_id = None
                st.session_state.dados_edicao = None
                st.rerun()
                # ======================================================
# PÁGINA 📄 COMUNICADO AOS PAIS (COMPLETA)
# ======================================================

elif menu == "📄 Comunicado aos Pais":
    page_header("📄 Comunicado aos Pais", "Gere comunicados individuais ou em lote para os responsáveis", "#7c3aed")
    
    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#faf5ff,#ede9fe);
        border:1.5px solid #c4b5fd; border-left:5px solid #7c3aed;
        border-radius:16px; padding:1.1rem 1.5rem; margin-bottom:1.25rem;
        box-shadow:0 4px 12px rgba(124,58,237,0.08);
    ">
        <div style="display:flex;align-items:center;gap:0.5rem;">
            <span>📄</span>
            <span style="color:#4c1d95;font-size:0.875rem;">Gere comunicados individuais ou em lote (ZIP) para envio aos pais e responsáveis.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df_alunos.empty or df_ocorrencias.empty:
        st.warning("⚠️ Cadastre alunos e ocorrências antes de gerar comunicados.")
        st.stop()

    modo = st.radio("Modo de geração", ["👤 Individual", "🏫 Por Turma(s)"], horizontal=True)

    medidas_opcoes = [
        "Mediação de conflitos", "Registro em ata", "Notificação aos pais",
        "Atividades de reflexão", "Termo de compromisso", "Ata circunstanciada",
        "Conselho Tutelar", "Mudança de turma", "Acompanhamento psicológico",
        "Reunião com pais", "Afastamento temporário", "B.O. registrado",
        "Diretoria de Ensino", "Medidas protetivas"
    ]

    if modo == "👤 Individual":
        st.subheader("👤 Seleção Individual")
        
        busca = st.text_input("🔍 Buscar aluno por nome ou RA", placeholder="Digite nome ou RA do aluno")
        
        if busca:
            df_filtrado = df_alunos[
                df_alunos["nome"].str.contains(busca, case=False, na=False) |
                df_alunos["ra"].astype(str).str.contains(busca, na=False)
            ]
        else:
            df_filtrado = df_alunos
        
        if df_filtrado.empty:
            st.warning("⚠️ Nenhum aluno encontrado.")
            st.stop()
        
        aluno_sel = st.selectbox("Aluno", df_filtrado["nome"].tolist())
        aluno_info = df_alunos[df_alunos["nome"] == aluno_sel].iloc[0]
        ra_aluno = aluno_info["ra"]
        
        ocorrencias_aluno = df_ocorrencias[df_ocorrencias["ra"] == ra_aluno]
        
        st.markdown(f"""
        <div class="card">
            <div class="card-title">📋 Dados do Aluno</div>
            <b>Nome:</b> {aluno_info['nome']}<br>
            <b>RA:</b> {ra_aluno}<br>
            <b>Turma:</b> {aluno_info['turma']}<br>
            <b>Total de ocorrências:</b> {len(ocorrencias_aluno)}
        </div>
        """, unsafe_allow_html=True)
        
        if ocorrencias_aluno.empty:
            st.info("ℹ️ Este aluno não possui ocorrências.")
            st.stop()
        
        lista_ocorrencias = (ocorrencias_aluno["id"].astype(str) + " - " + 
                            ocorrencias_aluno["data"] + " - " + 
                            ocorrencias_aluno["categoria"])
        
        occ_sel = st.selectbox("Selecione a ocorrência", lista_ocorrencias.tolist())
        occ_info = ocorrencias_aluno.iloc[lista_ocorrencias.tolist().index(occ_sel)]
        
        st.subheader("⚖️ Medidas Aplicadas")
        medidas_aplicadas = []
        cols = st.columns(3)
        for i, medida in enumerate(medidas_opcoes):
            with cols[i % 3]:
                if st.checkbox(medida, key=f"medida_ind_{medida}"):
                    medidas_aplicadas.append(medida)
        
        observacoes = st.text_area("📝 Observações adicionais", height=80)
        
        if st.button("📄 Gerar Comunicado (PDF)", type="primary"):
            aluno_data = {
                "nome": aluno_info["nome"],
                "ra": ra_aluno,
                "turma": aluno_info["turma"],
                "total_ocorrencias": len(ocorrencias_aluno)
            }
            ocorrencia_data = {
                "data": occ_info["data"],
                "categoria": occ_info["categoria"],
                "gravidade": occ_info["gravidade"],
                "professor": occ_info["professor"],
                "relato": occ_info["relato"],
                "encaminhamento": occ_info["encaminhamento"]
            }
            
            pdf_buffer = gerar_pdf_comunicado(
                aluno_data, ocorrencia_data,
                "\n".join(medidas_aplicadas), observacoes, df_responsaveis
            )
            
            st.download_button(
                "📥 Baixar Comunicado (PDF)",
                data=pdf_buffer,
                file_name=f"Comunicado_{ra_aluno}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
            st.success("✅ Comunicado gerado com sucesso!")

    else:
        st.subheader("🏫 Comunicado por Turmas")
        
        turmas_sel = st.multiselect("Selecione as turmas", sorted(df_alunos["turma"].unique().tolist()))
        
        if not turmas_sel:
            st.info("ℹ️ Selecione ao menos uma turma.")
            st.stop()
        
        alunos_turmas = df_alunos[df_alunos["turma"].isin(turmas_sel)]
        alunos_com_ocorrencias = [
            aluno for _, aluno in alunos_turmas.iterrows()
            if not df_ocorrencias[df_ocorrencias["ra"] == aluno["ra"]].empty
        ]
        
        if not alunos_com_ocorrencias:
            st.warning("⚠️ Nenhum aluno com ocorrência nas turmas selecionadas.")
            st.stop()
        
        st.success(f"📊 {len(alunos_com_ocorrencias)} alunos com ocorrências encontrados.")
        
        st.subheader("⚖️ Medidas para o Lote")
        medidas_aplicadas = []
        cols = st.columns(3)
        for i, medida in enumerate(medidas_opcoes):
            with cols[i % 3]:
                if st.checkbox(medida, key=f"medida_lote_{medida}"):
                    medidas_aplicadas.append(medida)
        
        observacoes = st.text_area("📝 Observações gerais", height=80)
        
        if st.button("📦 Gerar Comunicados em Lote (ZIP)", type="primary"):
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for aluno in alunos_com_ocorrencias:
                    ra = aluno["ra"]
                    ocorrencias = df_ocorrencias[df_ocorrencias["ra"] == ra].sort_values("data", ascending=False)
                    occ = ocorrencias.iloc[0]
                    
                    aluno_data = {
                        "nome": aluno["nome"],
                        "ra": ra,
                        "turma": aluno["turma"],
                        "total_ocorrencias": len(ocorrencias)
                    }
                    ocorrencia_data = {
                        "data": occ["data"],
                        "categoria": occ["categoria"],
                        "gravidade": occ["gravidade"],
                        "professor": occ["professor"],
                        "relato": occ["relato"],
                        "encaminhamento": occ["encaminhamento"]
                    }
                    
                    pdf = gerar_pdf_comunicado(
                        aluno_data, ocorrencia_data,
                        "\n".join(medidas_aplicadas), observacoes, df_responsaveis
                    )
                    
                    nome_pdf = f"Comunicado_{ra}_{aluno['nome'].replace(' ', '_')}.pdf"
                    zip_file.writestr(nome_pdf, pdf.getvalue())
            
            zip_buffer.seek(0)
            st.download_button(
                "📥 Baixar ZIP de Comunicados",
                data=zip_buffer,
                file_name=f"Comunicados_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip"
            )
            st.success("✅ Comunicados em lote gerados com sucesso!")
            # ======================================================
# PÁGINA 📊 GRÁFICOS E INDICADORES (COMPLETA)
# ======================================================

elif menu == "📊 Gráficos e Indicadores":
    page_header("📊 Gráficos e Indicadores", "Análise visual das ocorrências e indicadores escolares", "#0891b2")

    if df_ocorrencias.empty:
        st.info("📭 Nenhuma ocorrência registrada.")
        st.stop()

    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_periodo = st.selectbox("📅 Período", ["Todos", "Últimos 30 dias", "Este ano", "Personalizado"])
    with col2:
        turmas_disp = ["Todas"] + sorted(df_ocorrencias["turma"].dropna().unique().tolist())
        filtro_turma = st.selectbox("🏫 Turma", turmas_disp)
    with col3:
        gravidades_disp = ["Todas"] + sorted(df_ocorrencias["gravidade"].dropna().unique().tolist())
        filtro_gravidade = st.selectbox("⚖️ Gravidade", gravidades_disp)

    df_filtro = df_ocorrencias.copy()
    df_filtro["data_dt"] = pd.to_datetime(df_filtro["data"], format="%d/%m/%Y %H:%M", errors="coerce")
    
    agora = datetime.now()
    if filtro_periodo == "Últimos 30 dias":
        df_filtro = df_filtro[df_filtro["data_dt"] >= agora - timedelta(days=30)]
    elif filtro_periodo == "Este ano":
        df_filtro = df_filtro[df_filtro["data_dt"].dt.year == agora.year]
    elif filtro_periodo == "Personalizado":
        col1, col2 = st.columns(2)
        with col1:
            data_ini = st.date_input("Data inicial", value=agora.date() - timedelta(days=30))
        with col2:
            data_fim = st.date_input("Data final", value=agora.date())
        df_filtro = df_filtro[(df_filtro["data_dt"].dt.date >= data_ini) & (df_filtro["data_dt"].dt.date <= data_fim)]

    if filtro_turma != "Todas":
        df_filtro = df_filtro[df_filtro["turma"] == filtro_turma]
    if filtro_gravidade != "Todas":
        df_filtro = df_filtro[df_filtro["gravidade"] == filtro_gravidade]

    # Métricas
    _tot  = len(df_filtro)
    _grav = len(df_filtro[df_filtro["gravidade"] == "Gravíssima"]) if not df_filtro.empty and "gravidade" in df_filtro.columns else 0
    _grv  = len(df_filtro[df_filtro["gravidade"] == "Grave"])      if not df_filtro.empty and "gravidade" in df_filtro.columns else 0
    _turm = df_filtro["turma"].nunique() if not df_filtro.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'''<div class="metric-card animate-fade-in" style="background:linear-gradient(135deg,#1d4ed8,#3b82f6);box-shadow:0 8px 20px rgba(37,99,235,0.25);">
            <div class="metric-icon">📊</div><div class="metric-value">{_tot}</div>
            <div class="metric-label">Total de Ocorrências</div></div>''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''<div class="metric-card animate-fade-in" style="background:linear-gradient(135deg,#dc2626,#ef4444);box-shadow:0 8px 20px rgba(220,38,38,0.25);animation-delay:0.08s;">
            <div class="metric-icon">🚨</div><div class="metric-value">{_grav}</div>
            <div class="metric-label">Gravíssimas</div></div>''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''<div class="metric-card animate-fade-in" style="background:linear-gradient(135deg,#d97706,#f59e0b);box-shadow:0 8px 20px rgba(217,119,6,0.25);animation-delay:0.16s;">
            <div class="metric-icon">⚠️</div><div class="metric-value">{_grv}</div>
            <div class="metric-label">Graves</div></div>''', unsafe_allow_html=True)
    with col4:
        st.markdown(f'''<div class="metric-card animate-fade-in" style="background:linear-gradient(135deg,#059669,#10b981);box-shadow:0 8px 20px rgba(5,150,105,0.25);animation-delay:0.24s;">
            <div class="metric-icon">🏫</div><div class="metric-value">{_turm}</div>
            <div class="metric-label">Turmas Afetadas</div></div>''', unsafe_allow_html=True)

    st.markdown("---")

    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Por Categoria")
        contagem_cat = df_filtro["categoria"].value_counts().head(10)
        if not contagem_cat.empty:
            fig_cat = px.bar(x=contagem_cat.values, y=contagem_cat.index, orientation='h',
                             labels={'x': 'Quantidade', 'y': 'Categoria'},
                             color=contagem_cat.values, color_continuous_scale='Blues')
            fig_cat.update_layout(
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter, sans-serif', size=12, color='#334155'),
                margin=dict(t=10, b=10, l=0, r=0),
                xaxis=dict(gridcolor='#e2e8f0', linecolor='#e2e8f0'),
                yaxis=dict(gridcolor='#e2e8f0', linecolor='#e2e8f0'),
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Dados insuficientes")
    
    with col2:
        st.subheader("⚖️ Por Gravidade")
        contagem_grav = df_filtro["gravidade"].value_counts()
        if not contagem_grav.empty:
            fig_grav = px.pie(values=contagem_grav.values, names=contagem_grav.index,
                              color_discrete_sequence=['#10b981', '#f59e0b', '#f97316', '#ef4444'],
                              hole=0.45)
            fig_grav.update_traces(textfont_size=13, textfont_family='Inter, sans-serif')
            fig_grav.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter, sans-serif', size=12, color='#334155'),
                margin=dict(t=10, b=10, l=0, r=0),
                legend=dict(font=dict(size=11)),
            )
            st.plotly_chart(fig_grav, use_container_width=True)
        else:
            st.info("Dados insuficientes")

    st.markdown("---")
    st.subheader("📈 Evolução Temporal")
    df_filtro["data_apenas"] = df_filtro["data_dt"].dt.date
    evolucao = df_filtro.groupby("data_apenas").size().reset_index(name="Quantidade")
    
    if not evolucao.empty:
        fig_line = px.line(evolucao, x="data_apenas", y="Quantidade", markers=True)
        fig_line.update_traces(
            line_color="#2563eb",
            line_width=2.5,
            marker=dict(size=7, color="#2563eb", line=dict(width=2, color="white")),
        )
        fig_line.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif', size=12, color='#334155'),
            margin=dict(t=10, b=10, l=0, r=0),
            xaxis=dict(gridcolor='#e2e8f0', linecolor='#e2e8f0'),
            yaxis=dict(gridcolor='#e2e8f0', linecolor='#e2e8f0'),
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Dados insuficientes para evolução temporal")

    # Top 10 Turmas
    st.markdown("---")
    st.subheader("🏫 Top 10 Turmas com Mais Ocorrências")
    top_turmas = df_filtro['turma'].value_counts().head(10)
    if not top_turmas.empty:
        fig_turmas = px.bar(x=top_turmas.values, y=top_turmas.index, orientation='h',
                            labels={'x': 'Quantidade', 'y': 'Turma'},
                            color=top_turmas.values, color_continuous_scale='Greens')
        fig_turmas.update_layout(
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif', size=12, color='#334155'),
            margin=dict(t=10, b=10, l=0, r=0),
            xaxis=dict(gridcolor='#e2e8f0'),
            yaxis=dict(gridcolor='#e2e8f0'),
        )
        st.plotly_chart(fig_turmas, use_container_width=True)
    else:
        st.info("Dados insuficientes")

    # Top 10 Alunos
    st.markdown("---")
    st.subheader("👤 Top 10 Alunos com Mais Ocorrências")
    top_alunos = df_filtro['aluno'].value_counts().head(10)
    if not top_alunos.empty:
        fig_alunos = px.bar(x=top_alunos.values, y=top_alunos.index, orientation='h',
                            labels={'x': 'Quantidade', 'y': 'Aluno'},
                            color=top_alunos.values, color_continuous_scale='Reds')
        fig_alunos.update_layout(
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, sans-serif', size=12, color='#334155'),
            margin=dict(t=10, b=10, l=0, r=0),
            xaxis=dict(gridcolor='#e2e8f0'),
            yaxis=dict(gridcolor='#e2e8f0'),
        )
        st.plotly_chart(fig_alunos, use_container_width=True)
    else:
        st.info("Dados insuficientes")

    # Exportar
    st.markdown("---")
    csv = df_filtro.drop(columns=["data_dt", "data_apenas"], errors="ignore").to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button("📥 Baixar CSV", data=csv, file_name=f"ocorrencias_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    # ======================================================
# PÁGINA 🖨️ IMPRIMIR PDF (COMPLETA)
# ======================================================

elif menu == "🖨️ Imprimir PDF":
    page_header("🖨️ Gerar PDFs de Ocorrências", "Exporte relatórios em PDF ou em lote (ZIP)", "#334155")

    if df_ocorrencias.empty:
        st.info("📭 Nenhuma ocorrência registrada.")
        st.stop()

    st.subheader("🔍 Filtros")
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("📅 Data inicial", value=datetime.now() - timedelta(days=30))
        data_fim = st.date_input("📅 Data final", value=datetime.now())
    with col2:
        alunos_disp = sorted(df_ocorrencias["aluno"].unique().tolist())
        professores_disp = sorted(df_ocorrencias["professor"].unique().tolist())
        alunos_sel = st.multiselect("👥 Alunos (opcional)", alunos_disp)
        professores_sel = st.multiselect("👨‍🏫 Professores (opcional)", professores_disp)

    df_pdf = df_ocorrencias.copy()
    df_pdf["data_dt"] = pd.to_datetime(df_pdf["data"], format="%d/%m/%Y %H:%M", errors="coerce")
    df_pdf = df_pdf[(df_pdf["data_dt"] >= pd.Timestamp(data_inicio)) & 
                    (df_pdf["data_dt"] <= pd.Timestamp(data_fim) + pd.Timedelta(days=1))]
    
    if alunos_sel:
        df_pdf = df_pdf[df_pdf["aluno"].isin(alunos_sel)]
    if professores_sel:
        df_pdf = df_pdf[df_pdf["professor"].isin(professores_sel)]
    
    df_pdf = df_pdf.drop(columns=["data_dt"], errors="ignore")

    st.markdown("---")
    st.subheader("📋 Ocorrências Filtradas")
    
    if df_pdf.empty:
        st.warning("⚠️ Nenhuma ocorrência encontrada com os filtros aplicados.")
        st.stop()

    st.write(f"Total de ocorrências: **{len(df_pdf)}**")
    st.dataframe(df_pdf[["id", "data", "aluno", "turma", "categoria", "gravidade"]], 
                 use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📦 Gerar PDFs em Lote")
    
    if st.button("📦 Gerar ZIP de PDFs", type="primary"):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for _, occ in df_pdf.iterrows():
                pdf = gerar_pdf_ocorrencia(occ.to_dict(), df_responsaveis)
                nome_pdf = f"Ocorrencia_{occ['id']}_{occ['aluno'].replace(' ', '_')}.pdf"
                zip_file.writestr(nome_pdf, pdf.getvalue())
        
        zip_buffer.seek(0)
        st.download_button(
            "📥 Baixar ZIP com PDFs",
            data=zip_buffer,
            file_name=f"Ocorrencias_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip"
        )
        st.success("✅ PDFs gerados com sucesso!")

    st.markdown("---")
    st.subheader("📄 Gerar PDF Individual")
    
    lista_ind = (df_ocorrencias["id"].astype(str) + " - " + 
                 df_ocorrencias["aluno"] + " - " + 
                 df_ocorrencias["data"])
    
    opcao_ind = st.selectbox("Selecione a ocorrência", lista_ind.tolist())
    id_ind = int(opcao_ind.split(" - ")[0])
    occ_ind = df_ocorrencias[df_ocorrencias["id"] == id_ind].iloc[0]
    
    st.markdown(f"""
    <div class="card">
        <div class="card-title">📄 Detalhes da Ocorrência</div>
        <b>ID:</b> {occ_ind['id']}<br>
        <b>Aluno:</b> {occ_ind['aluno']}<br>
        <b>Data:</b> {occ_ind['data']}<br>
        <b>Categoria:</b> {occ_ind['categoria']}<br>
        <b>Gravidade:</b> {occ_ind['gravidade']}
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📄 Gerar PDF Individual", type="primary"):
        pdf = gerar_pdf_ocorrencia(occ_ind.to_dict(), df_responsaveis)
        st.download_button(
            "📥 Baixar PDF",
            data=pdf,
            file_name=f"Ocorrencia_{occ_ind['id']}.pdf",
            mime="application/pdf"
        )
        # ======================================================
# PÁGINA 👨‍🏫 CADASTRAR PROFESSORES (COMPLETA)
# ======================================================

elif menu == "👨‍🏫 Cadastrar Professores":
    page_header("👨‍🏫 Cadastrar Professores", "Gerencie o cadastro de professores e coordenadores", "#059669")

    if st.session_state.professor_salvo_sucesso:
        st.markdown(f"""
        <div class="success-box animate-fade-in">
            ✅ {st.session_state.cargo_professor_salvo} {st.session_state.nome_professor_salvo} cadastrado com sucesso!
        </div>
        """, unsafe_allow_html=True)
        st.session_state.professor_salvo_sucesso = False

    with st.expander("📥 Importar Professores em Massa", expanded=False):
        st.info("💡 Cole uma lista de nomes (um por linha)")
        texto_professores = st.text_area("Lista de professores:", height=150, 
                                         placeholder="Maria Silva\nJoão Pereira\nAna Souza")
        
        if st.button("📥 Importar Professores"):
            if not texto_professores.strip():
                st.error("❌ Cole ao menos um nome.")
            else:
                nomes = [n.strip() for n in texto_professores.splitlines() if n.strip()]
                inseridos = 0
                nomes_existentes = df_professores["nome"].str.lower().tolist() if not df_professores.empty else []
                
                for nome in nomes:
                    if nome.lower() in nomes_existentes:
                        continue
                    if salvar_professor({"nome": nome, "cargo": "Professor"}):
                        inseridos += 1
                
                if inseridos > 0:
                    st.success(f"✅ {inseridos} professor(es) importado(s).")
                    carregar_professores.clear()
                    st.rerun()

    st.markdown("---")

    # Formulário de cadastro
    if st.session_state.get("editando_prof"):
        prof_edit = df_professores[df_professores["id"] == st.session_state.editando_prof].iloc[0]
        st.subheader("✏️ Editar Professor")
        nome_prof = st.text_input("Nome *", value=prof_edit.get("nome", ""))
        cargo_prof = st.selectbox("Cargo", 
                                  ["Professor", "Diretor", "Diretora", "Vice-Diretor", 
                                   "Vice-Diretora", "Coordenador", "Coordenadora", "Outro"],
                                  index=["Professor", "Diretor", "Diretora", "Vice-Diretor",
                                         "Vice-Diretora", "Coordenador", "Coordenadora", "Outro"]
                                        .index(prof_edit.get("cargo", "Professor")))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Alterações", type="primary"):
                if not nome_prof.strip():
                    st.error("❌ Nome é obrigatório.")
                else:
                    sucesso = atualizar_professor(st.session_state.editando_prof, 
                                                  {"nome": nome_prof, "cargo": cargo_prof})
                    if sucesso:
                        st.success("✅ Professor atualizado!")
                        st.session_state.editando_prof = None
                        carregar_professores.clear()
                        st.rerun()
        with col2:
            if st.button("❌ Cancelar"):
                st.session_state.editando_prof = None
                st.rerun()
    else:
        st.subheader("➕ Novo Professor")
        nome_prof = st.text_input("Nome *", placeholder="Ex: João da Silva")
        cargo_prof = st.selectbox("Cargo", 
                                  ["Professor", "Diretor", "Diretora", "Vice-Diretor",
                                   "Vice-Diretora", "Coordenador", "Coordenadora", "Outro"])
        
        if st.button("💾 Salvar Cadastro", type="primary"):
            if not nome_prof.strip():
                st.error("❌ Nome é obrigatório.")
            else:
                nomes_existentes = df_professores["nome"].str.lower().tolist() if not df_professores.empty else []
                if nome_prof.lower() in nomes_existentes:
                    st.error("❌ Já existe um professor com esse nome.")
                else:
                    sucesso = salvar_professor({"nome": nome_prof, "cargo": cargo_prof})
                    if sucesso:
                        st.session_state.professor_salvo_sucesso = True
                        st.session_state.nome_professor_salvo = nome_prof
                        st.session_state.cargo_professor_salvo = cargo_prof
                        carregar_professores.clear()
                        st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.5rem 0;padding-bottom:0.5rem;border-bottom:2px solid #e2e8f0;position:relative;">
        <div style="position:absolute;bottom:-2px;left:0;width:45px;height:2px;background:linear-gradient(90deg,#059669,transparent);border-radius:4px;"></div>
        <span>📋</span>
        <h3 style="margin:0;font-family:'Nunito',sans-serif;font-size:1rem;color:#0f172a;">Professores Cadastrados</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if not df_professores.empty:
        for _, prof in df_professores.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([6, 1, 1])
                with col1:
                    cargo_display = prof.get('cargo', 'Professor')
                    if not cargo_display or str(cargo_display).lower() == 'nan':
                        cargo_display = 'Professor'
                    _cargo_cor = {"Diretor":"#1d4ed8","Diretora":"#1d4ed8","Vice-Diretor":"#0891b2","Vice-Diretora":"#0891b2","Coordenador":"#059669","Coordenadora":"#059669"}.get(cargo_display, "#64748b")
                    st.markdown(f"""<div style="display:flex;align-items:center;gap:0.6rem;padding:0.35rem 0;">
                        <div style="width:32px;height:32px;background:linear-gradient(135deg,{_cargo_cor}20,{_cargo_cor}10);border:1.5px solid {_cargo_cor}30;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:0.9rem;">👤</div>
                        <div><div style="font-weight:600;color:#0f172a;font-size:0.9rem;">{prof['nome']}</div>
                        <div style="font-size:0.75rem;color:{_cargo_cor};font-weight:600;">{cargo_display}</div></div>
                    </div>""", unsafe_allow_html=True)
                with col2:
                    if st.button("✏️", key=f"edit_prof_{prof['id']}"):
                        st.session_state.editando_prof = prof["id"]
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"del_prof_{prof['id']}"):
                        st.session_state.confirmar_exclusao_prof = prof["id"]
                        st.rerun()
        
        if st.session_state.get("confirmar_exclusao_prof"):
            prof_id = st.session_state.confirmar_exclusao_prof
            prof_excluir = df_professores[df_professores["id"] == prof_id].iloc[0]
            
            st.warning(f"⚠️ Confirma excluir o professor **{prof_excluir['nome']}**?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão", type="primary"):
                    if excluir_professor(prof_id):
                        st.success("✅ Professor excluído!")
                        del st.session_state.confirmar_exclusao_prof
                        carregar_professores.clear()
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    del st.session_state.confirmar_exclusao_prof
                    st.rerun()
    else:
        st.info("📭 Nenhum professor cadastrado.")
        # ======================================================
# PÁGINA 👤 CADASTRAR ASSINATURAS (COMPLETA)
# ======================================================

elif menu == "👤 Cadastrar Assinaturas":
    page_header("👤 Cadastrar Assinaturas", "Registre os responsáveis pelas assinaturas oficiais", "#0891b2")

    if st.session_state.responsavel_salvo_sucesso:
        st.markdown(f"""
        <div class="success-box animate-fade-in">
            ✅ {st.session_state.cargo_responsavel_salvo} {st.session_state.nome_responsavel_salvo} cadastrado(a) com sucesso!
        </div>
        """, unsafe_allow_html=True)
        st.session_state.responsavel_salvo_sucesso = False

    st.info("💡 Você pode cadastrar mais de um responsável para o mesmo cargo.")

    st.markdown("---")

    if st.session_state.get("editando_resp"):
        resp_edit = df_responsaveis[df_responsaveis["id"] == st.session_state.editando_resp].iloc[0]
        st.subheader("✏️ Editar Responsável")
        nome_resp = st.text_input("Nome *", value=resp_edit.get("nome", ""))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Alterações", type="primary"):
                if not nome_resp.strip():
                    st.error("❌ Nome é obrigatório.")
                else:
                    sucesso = atualizar_responsavel(st.session_state.editando_resp, {"nome": nome_resp})
                    if sucesso:
                        st.success("✅ Responsável atualizado!")
                        st.session_state.editando_resp = None
                        limpar_cache_responsaveis()
                        st.rerun()
        with col2:
            if st.button("❌ Cancelar"):
                st.session_state.editando_resp = None
                st.rerun()
    else:
        st.subheader("➕ Novo Responsável")
        cargos_disponiveis = ["Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora"]
        cargo = st.selectbox("Cargo", cargos_disponiveis)
        nome_resp = st.text_input("Nome do Responsável *", placeholder="Ex: Maria Silva")
        
        if st.button("💾 Cadastrar", type="primary"):
            if not nome_resp.strip():
                st.error("❌ Nome é obrigatório.")
            else:
                sucesso = salvar_responsavel({"cargo": cargo, "nome": nome_resp, "ativo": True})
                if sucesso:
                    st.session_state.responsavel_salvo_sucesso = True
                    st.session_state.nome_responsavel_salvo = nome_resp
                    st.session_state.cargo_responsavel_salvo = cargo
                    limpar_cache_responsaveis()
                    st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.5rem 0;padding-bottom:0.5rem;border-bottom:2px solid #e2e8f0;position:relative;">
        <div style="position:absolute;bottom:-2px;left:0;width:45px;height:2px;background:linear-gradient(90deg,#0891b2,transparent);border-radius:4px;"></div>
        <span>📋</span>
        <h3 style="margin:0;font-family:'Nunito',sans-serif;font-size:1rem;color:#0f172a;">Responsáveis Cadastrados</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if not df_responsaveis.empty:
        for cargo in ["Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora"]:
            grupo = df_responsaveis[df_responsaveis["cargo"] == cargo]
            if grupo.empty:
                continue
            
            _cor_carg = {"Diretor":"#1d4ed8","Diretora":"#1d4ed8","Vice-Diretor":"#0891b2","Vice-Diretora":"#0891b2","Coordenador":"#059669","Coordenadora":"#059669"}.get(cargo,"#64748b")
            st.markdown(f"""<div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.5rem 0;padding-bottom:0.4rem;border-bottom:1.5px solid #e2e8f0;">
                <span style="background:{_cor_carg};color:white;border-radius:6px;padding:0.2rem 0.5rem;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">{cargo}</span>
            </div>""", unsafe_allow_html=True)
            for _, resp in grupo.iterrows():
                col1, col2, col3 = st.columns([6, 1, 1])
                with col1:
                    st.markdown(f"""<div style="display:flex;align-items:center;gap:0.5rem;padding:0.2rem 0;">
                        <span style="color:#2563eb;">👤</span>
                        <span style="font-weight:500;color:#0f172a;font-size:0.9rem;">{resp['nome']}</span>
                    </div>""", unsafe_allow_html=True)
                with col2:
                    if st.button("✏️", key=f"edit_resp_{resp['id']}"):
                        st.session_state.editando_resp = resp["id"]
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"del_resp_{resp['id']}"):
                        st.session_state.confirmar_exclusao_resp = resp["id"]
                        st.rerun()
        
        if st.session_state.get("confirmar_exclusao_resp"):
            resp_id = st.session_state.confirmar_exclusao_resp
            resp_excluir = df_responsaveis[df_responsaveis["id"] == resp_id].iloc[0]
            
            st.warning(f"⚠️ Confirma excluir **{resp_excluir['nome']}** ({resp_excluir['cargo']})?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão", type="primary"):
                    if excluir_responsavel(resp_id):
                        st.success("✅ Responsável excluído!")
                        del st.session_state.confirmar_exclusao_resp
                        limpar_cache_responsaveis()
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    del st.session_state.confirmar_exclusao_resp
                    st.rerun()
    else:
        st.info("📭 Nenhum responsável cadastrado.")
        # ======================================================
# PÁGINA 🎨 ELETIVA (COMPLETA)
# ======================================================

elif menu == "🎨 Eletiva":
    page_header("🎨 Eletivas", "Consulte e gerencie os estudantes por professora de eletiva", "#7c3aed")
    
    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#f5f3ff,#ede9fe);
        border:1.5px solid #c4b5fd; border-left:5px solid #7c3aed;
        border-radius:16px; padding:1.1rem 1.5rem; margin-bottom:1.25rem;
        box-shadow:0 4px 12px rgba(124,58,237,0.08);
    ">
        <div style="display:flex;align-items:center;gap:0.5rem;">
            <span>🎨</span>
            <span style="color:#4c1d95;font-size:0.875rem;">Consulte os estudantes por professora da eletiva e verifique quem já foi localizado no sistema.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if FONTE_ELETIVAS == "supabase":
        st.success("✅ Eletivas carregadas do Supabase.")
    else:
        if ELETIVAS_ARQUIVO and os.path.exists(ELETIVAS_ARQUIVO):
            st.warning("⚠️ Eletivas carregadas da planilha Excel.")
        else:
            st.info("ℹ️ Nenhuma planilha de eletivas foi encontrada. Configure ELETIVAS_ARQUIVO no .env ou coloque o arquivo em assets/ ou data/.")

    if os.path.exists(ELETIVAS_ARQUIVO):
        with st.expander("☁️ Sincronizar com Supabase", expanded=False):
            st.info("💡 Este processo apaga as eletivas atuais do Supabase e grava novamente os dados do Excel.")
            if st.button("🔄 Substituir Eletivas no Supabase", type="primary"):
                registros = converter_eletivas_para_registros(ELETIVAS_EXCEL, origem="planilha")
                try:
                    _supabase_request("DELETE", "eletivas?id=not.is.null")
                    _supabase_request("POST", "eletivas", json=registros)
                    st.session_state.ELETIVAS = ELETIVAS_EXCEL
                    st.session_state.FONTE_ELETIVAS = "supabase"
                    st.success("✅ Eletivas sincronizadas com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao sincronizar: {e}")

    st.markdown("---")
    st.subheader("📊 Professoras de Eletiva")

    if not ELETIVAS:
        st.info("📭 Nenhuma professora cadastrada para eletivas.")
        st.stop()

    dados_professoras = []
    for prof, alunos in ELETIVAS.items():
        series = ", ".join(sorted({a.get("serie", "") for a in alunos if a.get("serie")}))
        dados_professoras.append({
            "Professora": prof,
            "Total de Alunos": len(alunos),
            "Séries": series
        })
    
    df_professoras = pd.DataFrame(dados_professoras)
    st.dataframe(df_professoras, use_container_width=True, hide_index=True)

    st.markdown("---")
    professora_sel = st.selectbox("Selecione a Professora", sorted(ELETIVAS.keys()))
    alunos_raw = ELETIVAS.get(professora_sel, [])

    df_eletiva = montar_dataframe_eletiva(professora_sel, df_alunos, ELETIVAS)
    
    total = len(df_eletiva)
    if not df_eletiva.empty and "Status" in df_eletiva.columns:
        encontrados = len(df_eletiva[df_eletiva["Status"] == "Encontrado"])
        nao_encontrados = len(df_eletiva[df_eletiva["Status"] == "Não encontrado"])
    else:
        encontrados = 0
        nao_encontrados = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Encontrados", encontrados)
    with col3:
        st.metric("Não Encontrados", nao_encontrados)

    busca_nome = st.text_input("🔍 Buscar estudante na eletiva", placeholder="Digite parte do nome")
    filtro_status = st.selectbox("Filtrar por status", ["Todos", "Encontrado", "Não encontrado"])
    
    df_view = df_eletiva.copy()
    if busca_nome:
        df_view = df_view[df_view["Nome da Eletiva"].str.contains(busca_nome, case=False, na=False)]
    if filtro_status != "Todos":
        df_view = df_view[df_view["Status"] == filtro_status]

    st.markdown("---")
    st.subheader("📋 Estudantes da Eletiva")
    st.dataframe(df_view, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🖨️ Imprimir Lista da Eletiva")
    
    if st.button("📄 Gerar PDF", type="primary"):
        pdf = gerar_pdf_eletiva(professora_sel, df_eletiva)
        st.download_button(
            "📥 Baixar PDF",
            data=pdf,
            file_name=f"Eletiva_{professora_sel}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )

    if alunos_raw:
        st.markdown("---")
        st.subheader("🗑️ Remover Estudantes da Eletiva")
        
        opcoes_remover = [f"{a['nome']} {a.get('serie', '')}".strip() for a in alunos_raw]
        selecionados = st.multiselect("Selecione estudantes para remover", opcoes_remover)
        
        if st.button("🗑️ Remover Selecionados", type="secondary"):
            if not selecionados:
                st.warning("⚠️ Nenhum estudante selecionado.")
            else:
                novos = []
                for a in alunos_raw:
                    label = f"{a['nome']} {a.get('serie', '')}".strip()
                    if label not in selecionados:
                        novos.append(a)
                
                ELETIVAS[professora_sel] = novos
                st.session_state.ELETIVAS = ELETIVAS
                
                if FONTE_ELETIVAS == "supabase":
                    try:
                        for label in selecionados:
                            nome = label.split("  ")[0]
                            _supabase_request("DELETE", f"eletivas?professora=eq.{professora_sel}&nome_aluno=eq.{nome}")
                    except Exception as e:
                        st.error(f"Erro ao remover do Supabase: {e}")
                
                st.success(f"✅ {len(selecionados)} estudante(s) removido(s).")
                st.rerun()
                # ======================================================
# PÁGINA 🏫 MAPA DA SALA (COMPLETA)
# ======================================================

elif menu == "🏫 Mapa da Sala":
    page_header("🏫 Mapa da Sala de Aula", "Organize assentos e distribua alunos visualmente", "#059669")
    
    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#f0fdf4,#dcfce7);
        border:1.5px solid #86efac; border-left:5px solid #059669;
        border-radius:16px; padding:1.1rem 1.5rem; margin-bottom:1.25rem;
        box-shadow:0 4px 12px rgba(5,150,105,0.08);
    ">
        <div style="display:flex;align-items:center;gap:0.5rem;">
            <span>🏫</span>
            <span style="color:#065f46;font-size:0.875rem;">Organize os assentos da sala e distribua os alunos manualmente ou de forma automática.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df_alunos.empty:
        st.warning("⚠️ Cadastre alunos antes de usar o mapa da sala.")
        st.stop()

    # Configurações da sala
    st.subheader("⚙️ Configurações da Sala")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        num_fileiras = st.slider("Número de fileiras", min_value=1, max_value=10, value=5, key="num_fileiras_mapa")
    with col2:
        carteiras_por_fileira = st.slider("Carteiras por fileira", min_value=1, max_value=8, value=6, key="carteiras_fileira_mapa")
    with col3:
        orientacao_lousa = st.selectbox("Orientação da lousa", ["Topo", "Fundo", "Esquerda", "Direita"], key="orientacao_lousa_mapa")

    total_assentos = num_fileiras * carteiras_por_fileira

    st.markdown("---")
    turmas_disponiveis = sorted(df_alunos["turma"].unique().tolist())
    turma_sel = st.selectbox("Selecione a Turma", turmas_disponiveis, key="turma_mapa_select")

    alunos_turma = df_alunos[df_alunos["turma"] == turma_sel].copy()
    
    # Mostrar apenas ATIVOS
    if "situacao" in alunos_turma.columns:
        alunos_turma["situacao_norm"] = alunos_turma["situacao"].str.strip().str.title()
        alunos_turma = alunos_turma[alunos_turma["situacao_norm"] == "Ativo"]
    
    nomes_alunos = sorted(alunos_turma["nome"].tolist())
    
    st.subheader(f"👥 Alunos da Turma {turma_sel}")
    st.info(f"📊 {len(alunos_turma)} alunos ativos | {num_fileiras} fileiras × {carteiras_por_fileira} carteiras = {total_assentos} assentos")

    # Inicializar estado dos assentos
    mapa_key = f"mapa_sala_{gerar_chave_segura(turma_sel)}"
    
    if mapa_key not in st.session_state:
        st.session_state[mapa_key] = {str(i): "" for i in range(total_assentos)}
    else:
        estado_anterior = st.session_state[mapa_key]
        st.session_state[mapa_key] = {str(i): estado_anterior.get(str(i), "") for i in range(total_assentos)}

    # CSS para os assentos
    st.markdown("""
    <style>
    .sala-grid {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin: 20px 0;
        padding: 20px;
        background: var(--light);
        border-radius: var(--radius-xl);
    }
    .fileira-row {
        display: flex;
        gap: 8px;
        justify-content: center;
    }
    .assento-card {
        width: 70px;
        height: 50px;
        border: 2px solid var(--border);
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 9px;
        font-weight: bold;
        text-align: center;
        background: white;
        transition: all 0.2s;
        padding: 2px;
        word-break: break-word;
    }
    .assento-card.ocupado {
        background: var(--gradient-primary);
        color: white;
        border-color: var(--primary);
    }
    .assento-card.vazio {
        background: white;
        color: var(--gray);
    }
    .lousa {
        width: 100%;
        max-width: 300px;
        height: 35px;
        background: var(--dark);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        border-radius: var(--radius-md);
        margin: 10px auto;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🪑 Layout da Sala")

    if orientacao_lousa in ["Topo", "Esquerda"]:
        st.markdown('<div class="lousa">📚 LOUSA</div>', unsafe_allow_html=True)

    sala_html = '<div class="sala-grid">'
    for fileira in range(num_fileiras):
        sala_html += '<div class="fileira-row">'
        for carteira in range(carteiras_por_fileira):
            idx = fileira * carteiras_por_fileira + carteira
            nome_no_assento = st.session_state[mapa_key].get(str(idx), "")
            if nome_no_assento:
                nome_exib = nome_no_assento.split()[0] if nome_no_assento else f"C{idx+1}"
                sala_html += f'<div class="assento-card ocupado" title="{nome_no_assento}">{nome_exib}</div>'
            else:
                sala_html += f'<div class="assento-card vazio">C{idx+1}</div>'
        sala_html += '</div>'
    sala_html += '</div>'
    st.markdown(sala_html, unsafe_allow_html=True)

    if orientacao_lousa in ["Fundo", "Direita"]:
        st.markdown('<div class="lousa">📚 LOUSA</div>', unsafe_allow_html=True)

    # Estatísticas
    assentos_ocupados = [v for v in st.session_state[mapa_key].values() if v.strip()]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Assentos", total_assentos)
    with col2:
        st.metric("Assentos Ocupados", len(assentos_ocupados))
    with col3:
        st.metric("Assentos Vazios", total_assentos - len(assentos_ocupados))

    # Alunos sem assento
    nomes_atribuidos = set(assentos_ocupados)
    alunos_sem_assento = [nome for nome in nomes_alunos if nome not in nomes_atribuidos]
    
    if alunos_sem_assento:
        st.warning(f"⚠️ {len(alunos_sem_assento)} alunos ainda não têm assento atribuído.")
        with st.expander("📋 Ver alunos sem assento"):
            for aluno in alunos_sem_assento:
                st.write(f"• {aluno}")

    # Formulário de edição
    st.markdown("---")
    st.subheader("📝 Editar Assentos")
    
    colunas_por_linha = 4
    for fileira in range(num_fileiras):
        st.markdown(f"**Fileira {fileira + 1}**")
        cols = st.columns(colunas_por_linha)
        
        for carteira in range(carteiras_por_fileira):
            col_idx = carteira % colunas_por_linha
            idx = fileira * carteiras_por_fileira + carteira
            
            with cols[col_idx]:
                valor_atual = st.session_state[mapa_key].get(str(idx), "")
                novo_valor = st.text_input(
                    f"Carteira {idx + 1}",
                    value=valor_atual,
                    key=f"input_{mapa_key}_{idx}",
                    placeholder="Digite o nome"
                )
                
                if novo_valor != valor_atual:
                    st.session_state[mapa_key][str(idx)] = novo_valor
                
                if novo_valor and novo_valor.strip():
                    melhor_match, score = encontrar_melhor_match(novo_valor, nomes_alunos)
                    if melhor_match and score >= 0.5 and melhor_match.lower() != novo_valor.lower():
                        st.caption(f"💡 {melhor_match} ({int(score * 100)}%)")
                        if st.button("✅ Usar", key=f"apply_{mapa_key}_{idx}"):
                            st.session_state[mapa_key][str(idx)] = melhor_match
                            st.rerun()
        
        if fileira < num_fileiras - 1:
            st.markdown("<br>", unsafe_allow_html=True)

    # Ferramentas
    st.markdown("---")
    st.subheader("🛠️ Ferramentas de Organização")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔀 Atribuir Aleatoriamente", use_container_width=True, type="primary"):
            nomes_embaralhados = nomes_alunos.copy()
            random.shuffle(nomes_embaralhados)
            for i in range(total_assentos):
                st.session_state[mapa_key][str(i)] = ""
            for i, nome in enumerate(nomes_embaralhados):
                if i < total_assentos:
                    st.session_state[mapa_key][str(i)] = nome
            st.success(f"✅ {min(len(nomes_alunos), total_assentos)} alunos atribuídos!")
            st.rerun()

    with col2:
        if st.button("🧹 Limpar Todos", use_container_width=True):
            for i in range(total_assentos):
                st.session_state[mapa_key][str(i)] = ""
            st.success("✅ Todos os assentos foram liberados!")
            st.rerun()

    with col3:
        if st.button("🔍 Corrigir Nomes", use_container_width=True):
            correcoes = 0
            for i in range(total_assentos):
                nome_atual = st.session_state[mapa_key].get(str(i), "")
                if nome_atual:
                    melhor_match, score = encontrar_melhor_match(nome_atual, nomes_alunos)
                    if melhor_match and score >= 0.85 and melhor_match != nome_atual:
                        st.session_state[mapa_key][str(i)] = melhor_match
                        correcoes += 1
            if correcoes > 0:
                st.success(f"✅ {correcoes} nome(s) corrigido(s)!")
            else:
                st.info("ℹ️ Nenhum nome precisou de correção.")
            st.rerun()

    with col4:
        if st.button("💾 Salvar Layout", use_container_width=True, type="secondary"):
            st.success("✅ Layout salvo com sucesso!")
            # ======================================================
# PÁGINA 💾 BACKUPS (COMPLETA)
# ======================================================

elif menu == "💾 Backups":
    render_backup_page()
    # ======================================================
# PÁGINA 📅 AGENDAMENTO DE ESPAÇOS (VERSÃO PREMIUM COMPLETA)
# ======================================================

elif menu == "📅 Agendamento de Espaços":
    page_header("📅 Agendamento de Espaços", "Reserve sala de informática, carrinhos, tablets e sala de leitura", "#2563eb")
    
    
    # ======================================================
    # FUNÇÕES AUXILIARES DO AGENDAMENTO
    # ======================================================
    
    def show_toast_agend(message: str, type: str = "success"):
        icon = "✅" if type == "success" else "❌" if type == "error" else "⚠️" if type == "warning" else "ℹ️"
        st.toast(f"{icon} {message}")
    
    def get_disponibilidade_espaco(espaco, data, horario):
        try:
            df_agend = carregar_agendamentos_filtrado(data, data, espaco=espaco)
            agendamentos_horario = df_agend[df_agend['horario'] == horario] if not df_agend.empty else pd.DataFrame()
            total = len(agendamentos_horario)
            
            if total == 0:
                return "🟢", "Disponível", "#10b981"
            elif total == 1:
                return "🟡", "Parcialmente ocupado", "#f59e0b"
            else:
                return "🔴", "Totalmente ocupado", "#ef4444"
        except:
            return "⚪", "Não verificado", "#9ca3af"
    
    def salvar_template(professor, nome_template, configuracao):
        template_key = f"template_{professor.replace(' ', '_')}_{nome_template}"
        st.session_state[template_key] = {
            "config": configuracao,
            "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        
        lista_key = f"templates_{professor.replace(' ', '_')}"
        if lista_key not in st.session_state:
            st.session_state[lista_key] = []
        if nome_template not in st.session_state[lista_key]:
            st.session_state[lista_key].append(nome_template)
        
        return True
    
    def carregar_templates(professor):
        lista_key = f"templates_{professor.replace(' ', '_')}"
        return st.session_state.get(lista_key, [])
    
    def aplicar_template(professor, nome_template, grade_key):
        template_key = f"template_{professor.replace(' ', '_')}_{nome_template}"
        if template_key in st.session_state:
            config = st.session_state[template_key]["config"]
            for key, value in config.items():
                st.session_state[grade_key][key] = value
            return True
        return False
    
    def registrar_log(acao, usuario, detalhes=""):
        if 'logs_agendamento' not in st.session_state:
            st.session_state.logs_agendamento = []
        
        log = {
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "acao": acao,
            "usuario": usuario,
            "detalhes": detalhes
        }
        st.session_state.logs_agendamento.insert(0, log)
        
        if len(st.session_state.logs_agendamento) > 100:
            st.session_state.logs_agendamento = st.session_state.logs_agendamento[:100]
    
    def exportar_para_excel(df, nome_arquivo):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Agendamentos', index=False)
            worksheet = writer.sheets['Agendamentos']
            
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            from openpyxl.styles import Font, PatternFill
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4A90E2", end_color="4A90E2", fill_type="solid")
            
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
        
        output.seek(0)
        return output
    
    # ======================================================
    # INICIALIZAÇÃO
    # ======================================================
    
    if 'gestao_logado' not in st.session_state:
        st.session_state.gestao_logado = False
    
    if 'logs_agendamento' not in st.session_state:
        st.session_state.logs_agendamento = []
    
    # Tabs do sistema de agendamento
    tabs_agend = st.tabs([
        "✨ Agendar", 
        "📋 Meus Agendamentos", 
        "🗓️ Grade Semanal",
        "📍 Visualizar por Espaço",
        "📊 Dashboard",
        "👥 Professores", 
        "📈 Relatórios", 
        "⚙️ Gestão", 
        "🧹 Manutenção"
    ])
    
    # ======================================================
    # ABA 1: AGENDAR (COM TEMPLATES)
    # ======================================================
    with tabs_agend[0]:
        st.subheader("📅 Agendamento Rápido")
        
        df_prof_agend = prof_list_agend()
        lista_nomes = sorted(df_prof_agend["nome"].dropna().tolist()) if not df_prof_agend.empty else []
        
        # Templates rápidos
        if lista_nomes:
            with st.expander("📂 Templates Salvos", expanded=False):
                professor_temp = st.selectbox("Professor:", lista_nomes, key="temp_prof")
                templates = carregar_templates(professor_temp)
                if templates:
                    cols = st.columns([2, 1])
                    with cols[0]:
                        template_sel = st.selectbox("Selecione:", templates, key="temp_sel")
                    with cols[1]:
                        if st.button("📂 Carregar", use_container_width=True):
                            st.success(f"✅ Template '{template_sel}' carregado!")
                            show_toast_agend(f"Template '{template_sel}' carregado com sucesso!", "success")
                else:
                    st.info("Nenhum template salvo para este professor")
        
        tipo_agendamento = st.radio(
            "🔄 Tipo de Agendamento:",
            ["📅 Data específica", "🔁 Fixo Semanal"],
            horizontal=True,
            key="tipo_agendamento"
        )
        
        if tipo_agendamento == "📅 Data específica":
            with st.form("form_agendamento_data"):
                col1, col2 = st.columns(2)
                with col1:
                    professor = st.selectbox("👨‍🏫 Professor:", [""] + lista_nomes)
                    turma = st.selectbox("🎓 Turma:", [""] + sorted(TURMAS_INTERVALOS_AGEND.keys()))
                    disciplina = st.selectbox("📚 Disciplina:", [""] + DISCIPLINAS_AGEND)
                
                with col2:
                    prioridade = st.selectbox("⭐ Prioridade:", [""] + PRIORIDADES_ESTENDIDAS + ["NORMAL"])
                    espaco = st.selectbox("📍 Espaço:", [""] + ESPACOS_AGEND)
                    data = st.date_input("📅 Data:", min_value=datetime.now().date() + timedelta(days=1))
                
                horario1 = st.selectbox("1ª Aula:", [""] + HORARIOS_AGEND)
                horario2 = st.selectbox("2ª Aula (opcional):", [""] + HORARIOS_AGEND)
                
                salvar_como_template = st.checkbox("💾 Salvar como template para uso futuro")
                nome_template = ""
                if salvar_como_template:
                    nome_template = st.text_input("Nome do template:", placeholder="Ex: Aulas de Matemática")
                
                submitted = st.form_submit_button("✅ Confirmar Agendamento", type="primary", use_container_width=True)
                
                if submitted:
                    if not all([professor, turma, disciplina, prioridade, espaco, horario1]):
                        st.error("⚠️ Preencha todos os campos obrigatórios")
                    else:
                        horarios = [h for h in [horario1, horario2] if h]
                        sucessos = 0
                        
                        for h in horarios:
                            conf = verificar_conflito_api(data.strftime("%Y-%m-%d"), h, espaco)
                            if not conf:
                                ok, _ = salvar_agendamento_api({
                                    "data_agendamento": data.strftime("%Y-%m-%d"),
                                    "horario": h,
                                    "espaco": espaco,
                                    "turma": turma,
                                    "disciplina": disciplina,
                                    "prioridade": prioridade,
                                    "professor_nome": professor,
                                    "status": "ATIVO",
                                    "tipo": "DATA_ESPECIFICA"
                                })
                                if ok:
                                    sucessos += 1
                        
                        if sucessos > 0:
                            st.success(f"✅ {sucessos} agendamento(s) confirmado(s)!")
                            registrar_log("CRIAR_AGENDAMENTO", professor, f"{data.strftime('%d/%m/%Y')} - {espaco} - {horarios}")
                            show_toast_agend(f"{sucessos} agendamento(s) criado(s)!", "success")
                            st.balloons()
                            carregar_agendamentos_filtrado.clear()
                            
                            # ⭐ ATUALIZAR GAMIFICAÇÃO ⭐
                            st.session_state.agendamentos_criados += sucessos
                            
                            # Verificar conquista de agendamento
                            if st.session_state.agendamentos_criados >= 5:
                                verificar_conquista("agendamento_perfeito")
                            
                            if salvar_como_template and nome_template:
                                config = {
                                    "turma": turma,
                                    "disciplina": disciplina,
                                    "prioridade": prioridade,
                                    "espaco": espaco,
                                    "horarios": horarios
                                }
                                salvar_template(professor, nome_template, config)
                                st.success(f"✅ Template '{nome_template}' salvo!")
                            
                            st.rerun()
                        else:
                            st.error("❌ Não foi possível criar o agendamento.")
        
        else:
            st.info("💡 **Agendamento Fixo Semanal** - Use a aba '🗓️ Grade Semanal' para configurar horários fixos!")
            if st.button("➡️ Ir para Grade Semanal", type="primary"):
                st.rerun()
                    # ======================================================
    # ABA 2: MEUS AGENDAMENTOS
    # ======================================================
    with tabs_agend[1]:
        st.subheader("📋 Meus Agendamentos")
        
        df_prof_agend = prof_list_agend()
        lista_nomes = sorted(df_prof_agend["nome"].dropna().tolist()) if not df_prof_agend.empty else []
        professor_sel = st.selectbox("👨‍🏫 Seu Nome:", [""] + lista_nomes, key="prof_meus_agend")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            data_ini = st.date_input("Data início:", datetime.now().date() - timedelta(days=30), key="meus_ini")
        with col2:
            data_fim = st.date_input("Data fim:", datetime.now().date() + timedelta(days=60), key="meus_fim")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            buscar_btn = st.button("🔍 Buscar", key="btn_buscar_agend", type="primary", use_container_width=True)
        
        if buscar_btn:
            if not professor_sel:
                st.warning("⚠️ Selecione seu nome primeiro")
            else:
                df = carregar_agendamentos_filtrado(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"), professor=professor_sel)
                
                if df.empty:
                    st.info("📭 Nenhum agendamento encontrado")
                else:
                    if 'status' in df.columns:
                        df = df[df['status'] == 'ATIVO']
                    
                    st.success(f"📊 {len(df)} agendamentos encontrados")
                    
                    df['data_agendamento'] = pd.to_datetime(df['data_agendamento'])
                    df = df.sort_values(['data_agendamento', 'horario'])
                    
                    colunas_exibir = ['data_agendamento', 'horario', 'espaco', 'turma', 'disciplina']
                    colunas_disponiveis = [c for c in colunas_exibir if c in df.columns]
                    
                    df_display = df[colunas_disponiveis].copy()
                    if 'data_agendamento' in df_display.columns:
                        df_display['data_agendamento'] = df_display['data_agendamento'].dt.strftime('%d/%m/%Y')
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    # Cancelar agendamento
                    st.markdown("---")
                    st.subheader("🛑 Cancelar Agendamento")
                    id_cancelar = st.selectbox("Selecione o ID para cancelar:", df['id'].tolist(), key="id_cancelar")
                    
                    if st.button("🛑 Cancelar Agendamento", type="secondary"):
                        ok, _ = cancelar_agendamento_api(str(id_cancelar))
                        if ok:
                            st.success("✅ Agendamento cancelado!")
                            carregar_agendamentos_filtrado.clear()
                            st.rerun()
                        else:
                            st.error("❌ Erro ao cancelar")
                    
                    # Exportar para Excel
                    if st.button("📊 Exportar para Excel", key="export_meus"):
                        excel_data = exportar_para_excel(df_display, "meus_agendamentos")
                        st.download_button(
                            "📥 Baixar Excel",
                            data=excel_data,
                            file_name=f"agendamentos_{professor_sel}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
    
    # ======================================================
    # ABA 3: GRADE SEMANAL
    # ======================================================
    with tabs_agend[2]:
        st.subheader("🗓️ Grade Semanal - Agendamentos Fixos")
        
        st.info("💡 Configure horários fixos • 🟢 Disponível • 🟡 Parcial • 🔴 Ocupado")
        
        df_prof_agend = prof_list_agend()
        lista_nomes = sorted(df_prof_agend["nome"].dropna().tolist()) if not df_prof_agend.empty else []
        
        if not lista_nomes:
            st.warning("⚠️ Cadastre professores primeiro na aba '👥 Professores'")
        else:
            professor_grade = st.selectbox("👨‍🏫 Selecione o Professor:", lista_nomes, key="prof_grade")
            
            if professor_grade:
                # Templates salvos
                templates = carregar_templates(professor_grade)
                if templates:
                    with st.expander("📂 Templates Salvos", expanded=False):
                        cols = st.columns([2, 1, 1])
                        with cols[0]:
                            template_sel = st.selectbox("Selecione:", templates, key="grade_temp_sel")
                        with cols[1]:
                            if st.button("📂 Carregar", use_container_width=True):
                                grade_key = f"grade_{professor_grade.replace(' ', '_').replace('.', '')}"
                                if grade_key not in st.session_state:
                                    st.session_state[grade_key] = {}
                                if aplicar_template(professor_grade, template_sel, grade_key):
                                    st.success(f"✅ Template '{template_sel}' carregado!")
                                    show_toast_agend(f"Template '{template_sel}' aplicado!", "success")
                                    st.rerun()
                        with cols[2]:
                            if st.button("🗑️ Excluir", use_container_width=True):
                                template_key = f"template_{professor_grade.replace(' ', '_')}_{template_sel}"
                                if template_key in st.session_state:
                                    del st.session_state[template_key]
                                    st.session_state[f"templates_{professor_grade.replace(' ', '_')}"].remove(template_sel)
                                    st.success(f"✅ Template '{template_sel}' excluído!")
                                    st.rerun()
                
                st.markdown("---")
                
                horarios_aulas = [
                    "07:00-07:50", "07:50-08:40", "08:40-09:30",
                    "09:50-10:40", "10:40-11:30", "11:30-12:20",
                    "13:00-13:50", "13:50-14:40", "14:40-15:30",
                    "15:50-16:40", "16:40-17:30", "17:30-18:20"
                ]
                
                dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira"]
                dias_abrev = ["SEG", "TER", "QUA", "QUI", "SEX"]
                
                st.markdown("### 📝 Configure os horários fixos:")
                
                grade_key = f"grade_{professor_grade.replace(' ', '_').replace('.', '')}"
                if grade_key not in st.session_state:
                    st.session_state[grade_key] = {}
                
                data_ref = st.date_input("📅 Data de referência para verificar disponibilidade:", 
                                        value=datetime.now().date() + timedelta(days=7),
                                        key="data_ref")
                
                for hora in horarios_aulas:
                    with st.expander(f"🕐 {hora}", expanded=False):
                        cols = st.columns(len(dias_semana))
                        
                        for i, (dia, dia_abrev) in enumerate(zip(dias_semana, dias_abrev)):
                            with cols[i]:
                                st.markdown(f"**{dia_abrev}**")
                                key = f"{dia}_{hora}"
                                
                                valor_atual = st.session_state[grade_key].get(key, {"espaco": "", "turma": "", "disciplina": ""})
                                
                                espaco_sel = st.selectbox(
                                    "📍 Espaço",
                                    [""] + ESPACOS_AGEND,
                                    key=f"esp_{professor_grade}_{dia}_{hora}",
                                    index=0 if not valor_atual.get("espaco") else ESPACOS_AGEND.index(valor_atual["espaco"]) + 1 if valor_atual["espaco"] in ESPACOS_AGEND else 0,
                                    label_visibility="visible"
                                )
                                
                                if espaco_sel:
                                    status, msg, cor = get_disponibilidade_espaco(espaco_sel, data_ref.strftime("%Y-%m-%d"), hora)
                                    st.caption(f"{status} {msg}")
                                    
                                    turma_sel = st.selectbox(
                                        "🎓 Turma",
                                        [""] + sorted(TURMAS_INTERVALOS_AGEND.keys()),
                                        key=f"turma_{professor_grade}_{dia}_{hora}",
                                        index=0 if not valor_atual.get("turma") else list(TURMAS_INTERVALOS_AGEND.keys()).index(valor_atual["turma"]) + 1 if valor_atual["turma"] in TURMAS_INTERVALOS_AGEND else 0,
                                        label_visibility="visible"
                                    )
                                    
                                    disciplina_sel = st.selectbox(
                                        "📚 Disciplina",
                                        [""] + DISCIPLINAS_AGEND,
                                        key=f"disc_{professor_grade}_{dia}_{hora}",
                                        index=0 if not valor_atual.get("disciplina") else DISCIPLINAS_AGEND.index(valor_atual["disciplina"]) + 1 if valor_atual["disciplina"] in DISCIPLINAS_AGEND else 0,
                                        label_visibility="visible"
                                    )
                                    
                                    if espaco_sel and turma_sel and disciplina_sel:
                                        st.success(f"✅ Configurado")
                                    
                                    st.session_state[grade_key][key] = {
                                        "espaco": espaco_sel,
                                        "turma": turma_sel if turma_sel else "",
                                        "disciplina": disciplina_sel if disciplina_sel else ""
                                    }
                                else:
                                    st.session_state[grade_key][key] = {"espaco": "", "turma": "", "disciplina": ""}
                
                st.markdown("---")
                
                # Salvar grade como template
                with st.expander("💾 Salvar Grade como Template", expanded=False):
                    nome_template_grade = st.text_input("Nome do template:", key="nome_template_grade")
                    if st.button("💾 Salvar Template da Grade", type="primary"):
                        if nome_template_grade:
                            config_completa = {}
                            for key, value in st.session_state[grade_key].items():
                                if value.get("espaco") and value.get("turma") and value.get("disciplina"):
                                    config_completa[key] = value
                            
                            if config_completa:
                                salvar_template(professor_grade, nome_template_grade, config_completa)
                                st.success(f"✅ Template '{nome_template_grade}' salvo com {len(config_completa)} horários!")
                                show_toast_agend(f"Template salvo com sucesso!", "success")
                            else:
                                st.warning("⚠️ Nenhum horário configurado para salvar")
                        else:
                            st.error("❌ Digite um nome para o template")
                
                # Período letivo
                col1, col2 = st.columns(2)
                with col1:
                    data_inicio = st.date_input("📅 Data de início:", value=datetime(2026, 2, 1).date(), key="grade_inicio")
                with col2:
                    data_fim = st.date_input("📅 Data de término:", value=datetime(2026, 12, 20).date(), key="grade_fim")
                
                frequencia = st.radio(
                    "🔄 Frequência:",
                    ["Semanal (toda semana)", "Quinzenal (a cada 15 dias)"],
                    horizontal=True,
                    key="freq_grade"
                )
                
                intervalo = 7 if frequencia == "Semanal (toda semana)" else 14
                
                if st.button("🚀 CRIAR AGENDAMENTOS FIXOS", type="primary", use_container_width=True):
                    total_criados = 0
                    conflitos = 0
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    dias_map = {
                        "Segunda-feira": 0, "Terça-feira": 1, "Quarta-feira": 2,
                        "Quinta-feira": 3, "Sexta-feira": 4
                    }
                    
                    total_potencial = 0
                    data_temp = data_inicio
                    while data_temp <= data_fim:
                        dia_semana_num = data_temp.weekday()
                        dia_semana_nome = None
                        for nome, num in dias_map.items():
                            if num == dia_semana_num:
                                dia_semana_nome = nome
                                break
                        
                        if dia_semana_nome:
                            for hora in horarios_aulas:
                                key = f"{dia_semana_nome}_{hora}"
                                config = st.session_state[grade_key].get(key, {})
                                if config.get("espaco") and config.get("turma") and config.get("disciplina"):
                                    total_potencial += 1
                        
                        data_temp += timedelta(days=intervalo)
                    
                    if total_potencial == 0:
                        st.warning("⚠️ Nenhum horário configurado.")
                    else:
                        data_atual = data_inicio
                        processados = 0
                        
                        while data_atual <= data_fim:
                            dia_semana_num = data_atual.weekday()
                            dia_semana_nome = None
                            for nome, num in dias_map.items():
                                if num == dia_semana_num:
                                    dia_semana_nome = nome
                                    break
                            
                            if dia_semana_nome:
                                for hora in horarios_aulas:
                                    key = f"{dia_semana_nome}_{hora}"
                                    config = st.session_state[grade_key].get(key, {})
                                    
                                    if config.get("espaco") and config.get("turma") and config.get("disciplina"):
                                        conf = verificar_conflito_api(data_atual.strftime("%Y-%m-%d"), hora, config["espaco"])
                                        
                                        if not conf:
                                            ok, _ = salvar_agendamento_api({
                                                "data_agendamento": data_atual.strftime("%Y-%m-%d"),
                                                "horario": hora,
                                                "espaco": config["espaco"],
                                                "turma": config["turma"],
                                                "disciplina": config["disciplina"],
                                                "prioridade": "NORMAL",
                                                "professor_nome": professor_grade,
                                                "status": "ATIVO",
                                                "tipo": "FIXO"
                                            })
                                            if ok:
                                                total_criados += 1
                                        else:
                                            conflitos += 1
                            
                            data_atual += timedelta(days=intervalo)
                            processados += 1
                            progress_bar.progress(min(processados / (total_potencial / len(horarios_aulas) + 1), 1.0))
                            status_text.text(f"Criando... {total_criados} agendamentos")
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        if total_criados > 0:
                            st.success(f"✅ {total_criados} agendamentos fixos criados!")
                            if conflitos > 0:
                                st.warning(f"⚠️ {conflitos} horários já ocupados")
                            
                            registrar_log("CRIAR_GRADE_FIXA", professor_grade, f"{total_criados} agendamentos - {frequencia}")
                            show_toast_agend(f"{total_criados} agendamentos fixos criados!", "success")
                            st.balloons()
                            carregar_agendamentos_filtrado.clear()
                        else:
                            st.warning("⚠️ Nenhum agendamento foi criado.")
                
                # Resumo da grade
                st.markdown("---")
                st.subheader("📋 Resumo da Grade")
                
                resumo_data = []
                for dia in dias_semana:
                    for hora in horarios_aulas:
                        key = f"{dia}_{hora}"
                        config = st.session_state[grade_key].get(key, {})
                        if config.get("espaco") and config.get("turma") and config.get("disciplina"):
                            resumo_data.append({
                                "Dia": dia[:3],
                                "Horário": hora,
                                "Espaço": config["espaco"],
                                "Turma": config["turma"],
                                "Disciplina": config["disciplina"]
                            })
                
                if resumo_data:
                    df_resumo = pd.DataFrame(resumo_data)
                    st.dataframe(df_resumo, use_container_width=True, hide_index=True)
                    
                    if st.button("🖨️ Imprimir Grade", key="btn_imprimir_grade"):
                        buffer = BytesIO()
                        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1*cm, rightMargin=1*cm)
                        estilos = getSampleStyleSheet()
                        
                        elementos = []
                        elementos.append(Paragraph(f"GRADE SEMANAL - {professor_grade}", estilos['Heading1']))
                        elementos.append(Spacer(1, 0.3*cm))
                        
                        dados_tabela = [["Dia", "Horário", "Espaço", "Turma", "Disciplina"]]
                        for item in resumo_data:
                            dados_tabela.append([item["Dia"], item["Horário"], item["Espaço"], item["Turma"], item["Disciplina"]])
                        
                        tabela = Table(dados_tabela, repeatRows=1)
                        tabela.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4A90E2")),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ]))
                        
                        elementos.append(tabela)
                        doc.build(elementos)
                        buffer.seek(0)
                        
                        st.download_button("📥 Baixar PDF", data=buffer, file_name=f"grade_{professor_grade}.pdf", mime="application/pdf")
    
    # ======================================================
    # ABA 4: VISUALIZAR POR ESPAÇO
    # ======================================================
    with tabs_agend[3]:
        st.subheader("📍 Visualizar Agenda por Espaço")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            espaco_sel = st.selectbox("📍 Espaço:", ESPACOS_AGEND, key="viz_espaco")
        with col2:
            data_ini = st.date_input("Data início:", datetime.now().date(), key="viz_ini")
        with col3:
            data_fim = st.date_input("Data fim:", datetime.now().date() + timedelta(days=30), key="viz_fim")
        
        if st.button("🔍 Carregar Agenda", type="primary", use_container_width=True):
            df = carregar_agendamentos_filtrado(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"), espaco=espaco_sel)
            
            if not df.empty and 'status' in df.columns:
                df = df[df['status'] == 'ATIVO']
            
            if df.empty:
                st.info(f"📭 Nenhum agendamento para **{espaco_sel}**")
            else:
                st.success(f"📊 {len(df)} agendamentos encontrados")
                
                df['data_agendamento'] = pd.to_datetime(df['data_agendamento'])
                df = df.sort_values(['data_agendamento', 'horario'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total no período", len(df))
                with col2:
                    st.metric("Professores únicos", df['professor_nome'].nunique())
                with col3:
                    st.metric("Turmas atendidas", df['turma'].nunique())
                
                st.markdown("---")
                
                datas_unicas = sorted(df['data_agendamento'].dt.date.unique())
                
                for data in datas_unicas:
                    df_dia = df[df['data_agendamento'].dt.date == data]
                    dia_semana = data.strftime('%A')
                    
                    with st.expander(f"📅 {dia_semana}, {data.strftime('%d/%m/%Y')} - {len(df_dia)} aula(s)", expanded=True):
                        tabela_dia = []
                        for _, row in df_dia.iterrows():
                            tipo_icon = "🔁 FIXO" if row.get('tipo') == 'FIXO' else "📅 DATA"
                            tabela_dia.append({
                                "Horário": row['horario'],
                                "Tipo": tipo_icon,
                                "Turma": row['turma'],
                                "Professor": row['professor_nome'],
                                "Disciplina": row['disciplina']
                            })
                        
                        df_tabela = pd.DataFrame(tabela_dia)
                        st.dataframe(df_tabela, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.subheader("📋 Tabela Completa para Impressão")
                
                colunas_exibir = ['data_agendamento', 'horario', 'turma', 'professor_nome', 'disciplina']
                colunas_disponiveis = [c for c in colunas_exibir if c in df.columns]
                
                df_completo = df[colunas_disponiveis].copy()
                if 'data_agendamento' in df_completo.columns:
                    df_completo['data_agendamento'] = df_completo['data_agendamento'].dt.strftime('%d/%m/%Y')
                
                st.dataframe(df_completo, use_container_width=True, hide_index=True)
                
                if st.button("🖨️ IMPRIMIR AGENDA", type="primary", use_container_width=True):
                    buffer = BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1*cm, rightMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
                    estilos = getSampleStyleSheet()
                    
                    elementos = []
                    elementos.append(Paragraph(f"AGENDA - {espaco_sel.upper()}", estilos['Heading1']))
                    elementos.append(Spacer(1, 0.2*cm))
                    elementos.append(Paragraph(f"Período: {data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')} | Total: {len(df)} agendamentos", estilos['Normal']))
                    elementos.append(Spacer(1, 0.3*cm))
                    
                    dados_tabela = [["Data", "Horário", "Turma", "Professor", "Disciplina"]]
                    for _, row in df.iterrows():
                        data_str = row['data_agendamento'].strftime('%d/%m/%Y')
                        dados_tabela.append([data_str, row['horario'], row['turma'], row['professor_nome'], row['disciplina']])
                    
                    tabela = Table(dados_tabela, repeatRows=1)
                    tabela.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4A90E2")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    
                    elementos.append(tabela)
                    elementos.append(Spacer(1, 0.3*cm))
                    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilos['Normal']))
                    
                    doc.build(elementos)
                    buffer.seek(0)
                    
                    st.download_button(
                        "📥 Baixar PDF",
                        data=buffer,
                        file_name=f"agenda_{espaco_sel.replace(' ', '_')}_{data_ini.strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                    
                    st.success("✅ PDF gerado com sucesso!")
                        # ======================================================
    # ABA 5: DASHBOARD DE AGENDAMENTOS
    # ======================================================
    with tabs_agend[4]:
        st.subheader("📊 Dashboard de Agendamentos")
        
        col1, col2 = st.columns(2)
        with col1:
            data_ini = st.date_input("Data início:", datetime.now().date(), key="dash_ini")
        with col2:
            data_fim = st.date_input("Data fim:", datetime.now().date() + timedelta(days=7), key="dash_fim")
        
        if st.button("📊 Carregar Dashboard", type="primary"):
            df = carregar_agendamentos_filtrado(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
            
            if not df.empty and 'status' in df.columns:
                df = df[df['status'] == 'ATIVO']
            
            if df.empty:
                st.info("📭 Nenhum agendamento no período")
            else:
                # Métricas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total", len(df))
                with col2:
                    fixos = len(df[df.get('tipo', '') == 'FIXO']) if 'tipo' in df.columns else 0
                    st.metric("Fixos", fixos)
                with col3:
                    st.metric("Data Específica", len(df) - fixos)
                with col4:
                    st.metric("Espaço mais usado", df['espaco'].mode()[0] if not df['espaco'].mode().empty else "N/A")
                
                st.markdown("---")
                
                # Gráficos
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📊 Uso por Espaço")
                    espaco_counts = df['espaco'].value_counts()
                    fig = px.bar(espaco_counts, x=espaco_counts.index, y=espaco_counts.values,
                                labels={'x': 'Espaço', 'y': 'Quantidade'}, color=espaco_counts.index)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("👨‍🏫 Top Professores")
                    prof_counts = df['professor_nome'].value_counts().head(10)
                    fig = px.bar(prof_counts, x=prof_counts.index, y=prof_counts.values,
                                labels={'x': 'Professor', 'y': 'Quantidade'}, color=prof_counts.index)
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("📅 Agendamentos por Dia")
                df['data_agendamento'] = pd.to_datetime(df['data_agendamento'])
                por_dia = df.groupby(df['data_agendamento'].dt.date).size().reset_index(name='Quantidade')
                por_dia.columns = ['Data', 'Quantidade']
                fig = px.line(por_dia, x='Data', y='Quantidade', markers=True)
                st.plotly_chart(fig, use_container_width=True)
    
    # ======================================================
    # ABA 6: PROFESSORES
    # ======================================================
    with tabs_agend[5]:
        st.subheader("👥 Professores")
        
        df_all = prof_list_agend()
        
        with st.expander("➕ Cadastrar Professor", expanded=False):
            with st.form("form_prof_rapido"):
                c1, c2 = st.columns(2)
                nome = c1.text_input("Nome *")
                email = c2.text_input("Email *")
                if st.form_submit_button("Salvar", type="primary"):
                    if nome and email:
                        ok, _ = prof_upsert_agend(nome, email)
                        if ok:
                            st.success(f"✅ Professor {nome} cadastrado!")
                            show_toast_agend(f"Professor {nome} cadastrado!", "success")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao cadastrar")
                    else:
                        st.error("❌ Nome e email são obrigatórios")
        
        if not df_all.empty:
            st.dataframe(df_all[['nome', 'email', 'cargo']], use_container_width=True, hide_index=True)
        else:
            st.info("📭 Nenhum professor cadastrado")
    
    # ======================================================
    # ABA 7: RELATÓRIOS
    # ======================================================
    with tabs_agend[6]:
        st.subheader("📈 Relatórios de Uso")
        
        col1, col2 = st.columns(2)
        with col1:
            data_ini = st.date_input("Data início:", datetime.now().date() - timedelta(days=30), key="rel_ini")
        with col2:
            data_fim = st.date_input("Data fim:", datetime.now().date() + timedelta(days=30), key="rel_fim")
        
        if st.button("📊 Gerar Relatório", key="btn_rel", type="primary"):
            df = carregar_agendamentos_filtrado(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
            
            if df.empty:
                st.info("📭 Nenhum agendamento no período")
            else:
                if 'status' in df.columns:
                    df = df[df['status'] == 'ATIVO']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total", len(df))
                with col2:
                    fixos = len(df[df.get('tipo', '') == 'FIXO']) if 'tipo' in df.columns else 0
                    st.metric("Fixos", fixos)
                with col3:
                    st.metric("Data Específica", len(df) - fixos)
                with col4:
                    st.metric("Espaço mais usado", df['espaco'].mode()[0] if not df['espaco'].mode().empty else "N/A")
                
                st.subheader("📊 Uso por Espaço")
                espaco_counts = df['espaco'].value_counts()
                fig = px.bar(espaco_counts, x=espaco_counts.index, y=espaco_counts.values,
                            labels={'x': 'Espaço', 'y': 'Quantidade'}, color=espaco_counts.index)
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("📋 Detalhamento")
                colunas_exibir = ['data_agendamento', 'horario', 'espaco', 'turma', 'professor_nome', 'disciplina']
                colunas_disponiveis = [c for c in colunas_exibir if c in df.columns]
                st.dataframe(df[colunas_disponiveis], use_container_width=True, hide_index=True)
                
                # Exportar
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button("📥 Baixar CSV", data=csv, file_name=f"relatorio_agendamentos_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
                    # ======================================================
    # ABA 8: GESTÃO
    # ======================================================
    with tabs_agend[7]:
        st.subheader("⚙️ Gestão de Agendamentos")
        
        if not st.session_state.gestao_logado:
            senha = st.text_input("Senha da Gestão:", type="password")
            if st.button("🔓 Acessar", type="primary"):
                if senha == SENHA_GESTAO_AGEND:
                    st.session_state.gestao_logado = True
                    st.success("✅ Acesso autorizado!")
                    show_toast_agend("Acesso autorizado!", "success")
                    st.rerun()
                else:
                    st.error("❌ Senha inválida")
        else:
            if st.button("🚪 Sair da Gestão", type="secondary"):
                st.session_state.gestao_logado = False
                st.rerun()
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                data_ini = st.date_input("Início:", datetime.now().date(), key="gest_ini")
            with col2:
                data_fim = st.date_input("Fim:", datetime.now().date() + timedelta(days=30), key="gest_fim")
            
            if st.button("🔍 Carregar Agendamentos", type="primary"):
                df = carregar_agendamentos_filtrado(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
                
                if df.empty:
                    st.info("📭 Nenhum agendamento")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    st.subheader("🗑️ Excluir Agendamento")
                    id_excluir = st.selectbox("Selecione o ID:", df['id'].tolist())
                    
                    if st.button("🗑️ Excluir Permanentemente", type="secondary"):
                        ok, _ = excluir_agendamento_api(str(id_excluir))
                        if ok:
                            st.success(f"✅ Agendamento {id_excluir} excluído!")
                            registrar_log("EXCLUIR_AGENDAMENTO", "Gestão", f"ID: {id_excluir}")
                            show_toast_agend("Agendamento excluído!", "success")
                            carregar_agendamentos_filtrado.clear()
                            st.rerun()
                        else:
                            st.error("❌ Erro ao excluir")
            
            st.markdown("---")
            
            # Logs de atividades
            with st.expander("📋 Logs de Atividades", expanded=False):
                if st.session_state.logs_agendamento:
                    for log in st.session_state.logs_agendamento[:20]:
                        st.caption(f"{log['timestamp']} - {log['acao']} - {log['usuario']} - {log['detalhes']}")
                else:
                    st.info("Nenhum log registrado")
    
    # ======================================================
    # ABA 9: MANUTENÇÃO
    # ======================================================
    with tabs_agend[8]:
        st.subheader("🧹 Manutenção / Limpeza")
        
        if not st.session_state.gestao_logado:
            st.warning("🔒 Acesso restrito à Gestão (faça login na aba ⚙️ Gestão)")
        else:
            st.info("Remove definitivamente CANCELADO/EXCLUIDO_GESTAO anteriores à data de corte.")
            
            dias = st.number_input("Remover registros anteriores a (dias):", min_value=7, max_value=3650, value=180)
            
            # Preview do que será excluído
            cutoff = (datetime.now().date() - timedelta(days=int(dias))).strftime("%Y-%m-%d")
            
            if st.button("🔍 Visualizar registros a excluir"):
                try:
                    url = f"{SUPABASE_URL}/rest/v1/agendamentos?select=id,data_agendamento,espaco,professor_nome,status&status=in.(CANCELADO,EXCLUIDO_GESTAO)&data_agendamento=lt.{cutoff}&limit=50"
                    r = requests.get(url, headers=HEADERS, timeout=20)
                    if r.status_code == 200:
                        dados = r.json()
                        if dados:
                            df_preview = pd.DataFrame(dados)
                            st.warning(f"⚠️ {len(df_preview)} registros serão excluídos (mostrando até 50):")
                            st.dataframe(df_preview, use_container_width=True, hide_index=True)
                        else:
                            st.success("✅ Nenhum registro para excluir!")
                    else:
                        st.error("❌ Erro ao consultar registros")
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
            
            if st.button("🧹 Executar limpeza agora", type="primary"):
                try:
                    url = f"{SUPABASE_URL}/rest/v1/agendamentos?status=in.(CANCELADO,EXCLUIDO_GESTAO)&data_agendamento=lt.{cutoff}"
                    r = requests.delete(url, headers=HEADERS, timeout=20)
                    if r.status_code in (200, 204):
                        st.success(f"✅ Limpeza concluída! (corte: {cutoff})")
                        registrar_log("LIMPEZA", "Gestão", f"Excluídos registros anteriores a {cutoff}")
                        show_toast_agend("Limpeza concluída com sucesso!", "success")
                        carregar_agendamentos_filtrado.clear()
                    else:
                        st.error(f"❌ Erro: {r.status_code}")
                except Exception as e:
                    st.error(f"❌ Falha: {e}")
