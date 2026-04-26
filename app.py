# ======================================================
# IMPORTS PADRÃO
# ======================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import random
import html
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from difflib import SequenceMatcher
from xml.etree import ElementTree as ET
import requests
import os
import re
import json
import zipfile
import pytz
import unicodedata
from pathlib import Path

# 👇 IMPORT DO DOTENV
from dotenv import find_dotenv, load_dotenv

def carregar_variaveis_ambiente():
    """Carrega o .env local mesmo quando o Streamlit inicia em outro diretório."""
    env_do_projeto = Path(__file__).resolve().parent / ".env"
    if env_do_projeto.exists():
        load_dotenv(dotenv_path=env_do_projeto, override=False)
        return

    env_encontrado = find_dotenv(usecwd=True)
    if env_encontrado:
        load_dotenv(dotenv_path=env_encontrado, override=False)


carregar_variaveis_ambiente()

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
    BackupManager = None
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
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SENHA_EXCLUSAO = os.getenv("SENHA_EXCLUSAO", "040600")
SUPABASE_VALID = bool(SUPABASE_URL and SUPABASE_KEY)

HEADERS = {}
if SUPABASE_VALID:
    HEADERS = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


# ======================================================
# IA CONVIVA PEDAGÓGICA ONLINE — GOOGLE GEMINI
# ======================================================
# SEGURANÇA:
# Não coloque sua chave diretamente neste arquivo.
# Configure no Streamlit Cloud em Settings > Secrets:
# GEMINI_API_KEY = "sua_chave_aqui"
# GEMINI_MODEL = "gemini-2.5-flash"
#
# Para rodar localmente, você também pode usar arquivo .env:
# GEMINI_API_KEY=sua_chave_aqui
# GEMINI_MODEL=gemini-2.5-flash

def _obter_config_secreta(nome: str, padrao: str = "") -> str:
    """Busca configuração primeiro no ambiente/.env e depois no st.secrets."""
    valor = str(os.getenv(nome, "") or "").strip()
    if valor:
        return valor
    try:
        if hasattr(st, "secrets"):
            return str(st.secrets.get(nome, padrao) or padrao).strip()
    except Exception:
        pass
    return padrao

GEMINI_API_KEY = _obter_config_secreta("GEMINI_API_KEY", "")
GEMINI_MODEL = _obter_config_secreta("GEMINI_MODEL", "gemini-2.5-flash")

# ======================================================
# CONFIGURAÇÃO STREAMLIT
# ======================================================
st.set_page_config(
    page_title="Sistema Conviva 179 - ELIANE APARECIDA DANTAS DA SILVA PROFESSORA - PEI",
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
    --primary:        #d946ef;
    --primary-light:  #f472b6;
    --primary-xlight: #fdf2ff;
    --primary-dark:   #a21caf;

    /* Acento verde sucesso */
    --success:        #10b981;
    --success-light:  #d1fae5;

    /* Acento âmbar aviso */
    --warning:        #f59e0b;
    --warning-light:  #fef9c3;

    /* Vermelho perigo */
    --danger:         #f43f5e;
    --danger-light:   #ffe4e6;

    /* Info ciano */
    --info:           #06b6d4;
    --info-light:     #cffafe;

    /* Roxo destaque */
    --purple:         #8b5cf6;
    --purple-light:   #ede9fe;

    /* Neutros */
    --dark:           #2b2140;
    --dark-mid:       #3f2d63;
    --gray-dark:      #54467a;
    --gray:           #7b6ea3;
    --gray-light:     #a79aca;
    --border:         #edd7ff;
    --border-light:   #f8ecff;
    --bg:             #fff8ff;
    --white:          #ffffff;

    /* Gradientes */
    --grad-primary:   linear-gradient(120deg, #ff7fd1 0%, #ffd67f 23%, #97f7f0 46%, #9cc7ff 70%, #d8a0ff 100%);
    --grad-teal:      linear-gradient(135deg, #38bdf8 0%, #22d3ee 100%);
    --grad-emerald:   linear-gradient(135deg, #34d399 0%, #10b981 100%);
    --grad-amber:     linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    --grad-danger:    linear-gradient(135deg, #fb7185 0%, #f43f5e 100%);
    --grad-purple:    linear-gradient(135deg, #a78bfa 0%, #d946ef 100%);
    --grad-school:    linear-gradient(120deg, #ff95d6 0%, #ffd67f 28%, #9ce7ff 55%, #b39bff 82%, #ff9ee2 100%);
    --grad-warm:      linear-gradient(120deg, #fdba74 0%, #fda4af 50%, #f9a8d4 100%);

    /* Sombras */
    --shadow-xs:  0 1px 2px rgba(15,23,42,0.06);
    --shadow-sm:  0 2px 4px rgba(15,23,42,0.08);
    --shadow-md:  0 4px 12px rgba(15,23,42,0.10);
    --shadow-lg:  0 8px 24px rgba(15,23,42,0.12);
    --shadow-xl:  0 16px 40px rgba(15,23,42,0.14);
    --shadow-2xl: 0 24px 64px rgba(15,23,42,0.18);
    --shadow-blue: 0 8px 24px rgba(168,85,247,0.30);
    --shadow-green: 0 8px 24px rgba(45,212,191,0.28);

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
        radial-gradient(circle at 8% 6%, rgba(244,114,182,0.28), transparent 34%),
        radial-gradient(circle at 86% 10%, rgba(147,197,253,0.24), transparent 30%),
        radial-gradient(circle at 80% 85%, rgba(45,212,191,0.22), transparent 28%),
        linear-gradient(135deg, #fff7fb 0%, #fffaf0 26%, #f3fcff 50%, #f6f2ff 76%, #fff8fd 100%) !important;
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
/* ========== SIDEBAR SIMPLES ========== */
/* ============================================ */
section[data-testid="stSidebar"] {
    background: #f8fbff !important;
    border-right: 1px solid #e2e8f0 !important;
    min-width: 300px !important;
    max-width: 300px !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding: 0.75rem !important;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #334155 !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] {
    margin: 0.2rem 0 !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
    background: #ffffff !important;
    border: 1px solid #d9e2f0 !important;
    border-radius: 12px !important;
    color: #1e293b !important;
    min-height: 46px !important;
    text-align: left !important;
    box-shadow: none !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
    border-color: #93c5fd !important;
    background: #f8fbff !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] {
    background: #e0ecff !important;
    border-color: #60a5fa !important;
    color: #1e3a8a !important;
    font-weight: 700 !important;
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
        radial-gradient(circle at top right, rgba(255,255,255,0.7), transparent 36%),
        linear-gradient(120deg, #fff7fc 0%, #fffaf2 38%, #f6fbff 72%, #faf5ff 100%);
    padding: 2.2rem 2.2rem;
    border-radius: 24px;
    color: #241b4d;
    text-align: center;
    margin-bottom: 2rem;
    border: 1.5px solid rgba(196,181,253,0.35);
    box-shadow: 0 14px 26px rgba(76,29,149,0.08), 0 0 0 1px rgba(255,255,255,0.55) inset;
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
    background: rgba(129,140,248,0.12);
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
    background: rgba(244,114,182,0.10);
    border-radius: 50%;
    pointer-events: none;
}

/* Pattern decorativo */
.main-header .pattern {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        radial-gradient(circle at 20% 50%, rgba(124,58,237,0.10) 1px, transparent 1px),
        radial-gradient(circle at 80% 20%, rgba(236,72,153,0.10) 1px, transparent 1px);
    background-size: 46px 46px;
    pointer-events: none;
}

.school-header-inner {
    position: relative;
    z-index: 1;
    max-width: 940px;
    margin: 0 auto;
}

.school-name {
    font-family: 'Nunito', sans-serif !important;
    font-size: clamp(1.8rem, 2.6vw, 2.45rem);
    font-weight: 900;
    letter-spacing: -0.03em;
    margin-bottom: 0.45rem;
    color: #31215f;
    line-height: 1.2;
    text-shadow: 0 1px 0 rgba(255,255,255,0.7);
    white-space: normal !important;
}

.school-subtitle {
    font-size: 0.98rem;
    font-weight: 700;
    opacity: 1;
    margin-bottom: 1rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #6d28d9;
}

.school-info-chips {
    display: flex;
    justify-content: center;
    gap: 0.7rem;
    flex-wrap: wrap;
}

.school-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(255,255,255,0.62);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(124,58,237,0.22);
    border-radius: 999px;
    padding: 0.5rem 0.9rem;
    font-size: 0.8rem;
    font-weight: 700;
    color: #3f2d77;
    white-space: normal;
}

.school-chip-address {
    width: min(100%, 820px);
    justify-content: center;
}

/* ============================================ */
/* ========== CARDS DE MÉTRICAS ========== */
/* ============================================ */
.metric-card {
    border-radius: 26px;
    padding: 1.2rem 1.05rem 1rem 1.05rem;
    text-align: left;
    transition: all 0.3s cubic-bezier(.16,1,.3,1);
    position: relative;
    overflow: hidden;
    color: white;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    align-items: flex-start;
    border: 1px solid rgba(255,255,255,0.14);
    backdrop-filter: blur(10px);
    box-shadow: 0 16px 30px rgba(15,23,42,0.10);
}

.metric-card::before {
    content: '';
    position: absolute;
    top: -24px; right: -24px;
    width: 108px; height: 108px;
    background: rgba(255,255,255,0.12);
    border-radius: 50%;
}

.metric-card:hover {
    transform: translateY(-7px) scale(1.01);
    filter: brightness(1.05);
    box-shadow: 0 22px 40px rgba(15,23,42,0.20) !important;
}

.metric-icon {
    font-size: 1.55rem;
    margin-bottom: 0.75rem;
    width: 50px;
    height: 50px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255,255,255,0.16);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.18);
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
    font-weight: 700;
    margin-top: 0.55rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    opacity: 0.92;
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

/* Menu suspenso novo (do zero, simples e estável) */
[data-baseweb="select"] > div:first-child {
    border-radius: 12px !important;
    border: 1px solid #d9e2f0 !important;
    background: #ffffff !important;
    min-height: 44px !important;
    box-shadow: none !important;
}

[data-baseweb="select"] > div:first-child:focus-within {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.14) !important;
}

[data-baseweb="select"] [role="combobox"],
[data-baseweb="select"] input,
[data-baseweb="select"] [aria-live],
[data-baseweb="select"] [aria-live] * {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    opacity: 1 !important;
}

[data-baseweb="menu"],
[role="listbox"] {
    background: #ffffff !important;
    border: 1px solid #d9e2f0 !important;
    border-radius: 10px !important;
}

[role="option"] {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
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
    background: linear-gradient(120deg, rgba(255,241,250,0.92), rgba(240,249,255,0.95), rgba(245,243,255,0.95));
    border: 1px solid rgba(196,181,253,0.45);
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
    background: radial-gradient(circle, rgba(168,85,247,0.12), transparent 70%);
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
    color: #6d28d9;
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
    .school-subtitle { letter-spacing: 0.05em; }
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
ESCOLA_NOME = "ELIANE APARECIDA DANTAS DA SILVA PROFESSORA - PEI"
ESCOLA_SUBTITULO = "Escola dos Sonhos • Escola Estadual"
ESCOLA_ENDERECO = "VALTER DE SOUZA COSTA, 147 - RUA JARDIM PRIMAVERA - Ferraz de Vasconcelos - São Paulo"
ESCOLA_CEP = "CEP: 08535-310"
ESCOLA_TELEFONE = "(11) 4675-3400"
ESCOLA_EMAIL = "e918623@educacao.sp.gov.br"
ESCOLA_LOGO = os.path.join("assets", "images", "eliane_dantas.png")

# Imagem da escola exibida no topo do menu lateral.
# A imagem está incorporada em base64 para funcionar no Streamlit Cloud sem depender de arquivo externo.
ESCOLA_IMAGEM_MENU_BASE64 = """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"""

# ======================================================
# MENU LATERAL PREMIUM (SEM RADIO BUTTONS)
# ======================================================

st.sidebar.markdown(f"""
<div style="
    position: relative;
    padding: 1.2rem 1rem 1rem 1rem;
    margin: 0.2rem 0.2rem 0.9rem 0.2rem;
    border-radius: 28px;
    background: linear-gradient(145deg, rgba(255,236,247,0.9) 0%, rgba(237,246,255,0.9) 45%, rgba(241,232,255,0.92) 100%);
    border: 1px solid rgba(196,181,253,0.45);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.75), 0 12px 24px rgba(76,29,149,0.10);
    overflow: hidden;
    text-align: center;
">
    <div style="
        width: 100%;
        height: 118px;
        border-radius: 22px;
        overflow: hidden;
        margin-bottom: 0.85rem;
        box-shadow: 0 10px 22px rgba(15,23,42,0.16);
        border: 1px solid rgba(255,255,255,0.75);
        background: #e0f2fe;
    ">
        <img src="data:image/jpeg;base64,{ESCOLA_IMAGEM_MENU_BASE64}" style="
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        ">
    </div>
    <div style="
        color:#7c3aed;
        font-size:0.72rem;
        font-weight:700;
        letter-spacing:0.18em;
        text-transform:uppercase;
        margin-bottom:0.35rem;
    ">Plataforma Escolar</div>
    <h2 style="
        font-family: 'Nunito', sans-serif;
        color: #31215f;
        font-weight: 900;
        font-size: 1.85rem;
        line-height: 1.05;
        margin: 0 0 0.25rem 0;
        letter-spacing: -0.03em;
    ">{ESCOLA_SUBTITULO}</h2>
    <p style="
        color: #5b3d9b;
        font-size: 0.82rem;
        margin: 0 0 0.9rem 0;
        font-weight: 700;
        letter-spacing: 0.02em;
    ">{ESCOLA_NOME}</p>
</div>
<div style="height: 1px; background: linear-gradient(90deg, transparent, #c4b5fd, transparent); margin: 0 1rem 0.5rem 1rem;"></div>
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

# Lista de itens do menu com ícones
menu_items = [
    {"nome": "Dashboard", "icone": "🏠"},
    {"nome": "Registrar Ocorrência", "icone": "📝"},
    {"nome": "Relatório dos Estudantes", "icone": "🧾"},
    {"nome": "Histórico de Ocorrências", "icone": "📋"},
    {"nome": "Comunicado aos Pais", "icone": "📄"},
    {"nome": "Lista de Alunos", "icone": "👥"},
    {"nome": "Importar Alunos", "icone": "📥"},
    {"nome": "Gerenciar Turmas", "icone": "📋"},
    {"nome": "Cadastrar Professores", "icone": "👨‍🏫"},
    {"nome": "Cadastrar Assinaturas", "icone": "👤"},
    {"nome": "Eletiva", "icone": "🎨"},
    {"nome": "Tutoria", "icone": "🫂"},
    {"nome": "Gráficos e Indicadores", "icone": "📊"},
    {"nome": "Imprimir PDF", "icone": "🖨️"},
    {"nome": "Mapa da Sala", "icone": "🏫"},
    {"nome": "Agendamento de Espaços", "icone": "📅"},
    {"nome": "Portal do Responsável", "icone": "👨‍👩‍👧"},
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
ELETIVAS_ARQUIVO = r"C:\Users\Freak Work\Desktop\IMportação.xlsx"
TUTORIA_ARQUIVOS_CANDIDATOS = [
    os.path.join(os.getcwd(), "Tutoria.xlsx"),
    os.path.join(os.getcwd(), "Tutoria (3).xlsx"),
    r"C:\Users\Freak Work\Downloads\Tutoria (3).xlsx",
]

ELETIVAS = {
    "Solange": [], "Rosemeire": [], "Fernanda": [], "Fagna": [],
    "Elaine": [], "Geovana": [], "Shirley": [], "Rosangela": [],
    "Veronica": [], "Silvana": [], "Patricia": [],
}

def resolver_primeiro_arquivo_existente(candidatos: list[str]) -> str:
    for caminho in candidatos:
        if caminho and os.path.exists(caminho):
            return caminho
    return candidatos[0] if candidatos else ""

TUTORIA_ARQUIVO = resolver_primeiro_arquivo_existente(TUTORIA_ARQUIVOS_CANDIDATOS)
TUTORIA_CACHE_ARQUIVO = os.path.join(os.getcwd(), "data", "tutoria_cadastro.json")
DIAS_SEMANA_TUTORIA = ("segunda", "terca", "terça", "quarta", "quinta", "sexta", "sabado", "sábado")
PERFIS_TUTORIA = [
    "Professor(a)",
    "Professor(a) Tutor(a)",
    "Tutor(a)",
    "CGPG",
    "Diretor(a)",
    "Vice-Diretor(a)",
    "Coordenador(a)"
]
MAPA_PERFIS_TUTORIA = {
    "professor": "Professor(a)",
    "professora": "Professor(a)",
    "professor(a)": "Professor(a)",
    "professor(a) tutor(a)": "Professor(a) Tutor(a)",
    "tutor": "Tutor(a)",
    "tutora": "Tutor(a)",
    "tutor(a)": "Tutor(a)",
    "cgpg": "CGPG",
    "diretor": "Diretor(a)",
    "diretora": "Diretor(a)",
    "diretor(a)": "Diretor(a)",
    "vice-diretor": "Vice-Diretor(a)",
    "vice diretora": "Vice-Diretor(a)",
    "vice-diretora": "Vice-Diretor(a)",
    "vice diretor": "Vice-Diretor(a)",
    "vice-diretor(a)": "Vice-Diretor(a)",
    "coordenador": "Coordenador(a)",
    "coordenadora": "Coordenador(a)",
    "coordenador(a)": "Coordenador(a)"
}

def normalizar_perfil_tutoria(tipo: str = "") -> str:
    perfil = str(tipo or "").strip()
    if not perfil:
        return "Professor(a)"
    return MAPA_PERFIS_TUTORIA.get(normalizar_texto(perfil), perfil)

def mensagem_erro_tutoria_supabase(erro: Exception) -> str:
    texto = str(erro)
    resposta = getattr(erro, "response", None)
    if resposta is not None and getattr(resposta, "status_code", None) == 404:
        return "A tabela de tutoria não está disponível no Supabase agora. O cadastro local continua salvo normalmente."
    return f"Não foi possível sincronizar a tutoria com o Supabase: {texto}"

def estrutura_tutoria_vazia(nome: str = "", tipo: str = "Professor(a)") -> dict:
    return {
        "nome": str(nome or "").strip(),
        "tipo": normalizar_perfil_tutoria(tipo),
        "espaco": "",
        "horario": "",
        "dia": "",
        "alunos": []
    }

def normalizar_alunos_tutoria(alunos_raw) -> list:
    alunos = []
    for item in alunos_raw or []:
        if isinstance(item, dict):
            nome = str(item.get("nome", "")).strip()
            serie = formatar_turma_eletiva(str(item.get("serie", "")).strip())
            ra = "".join(ch for ch in str(item.get("ra", "")) if ch.isdigit())
        else:
            nome = str(item or "").strip()
            serie = ""
            ra = ""
        if not nome:
            continue
        aluno = {"nome": nome, "serie": serie}
        if ra:
            aluno["ra"] = ra
        alunos.append(aluno)
    return alunos

def normalizar_base_tutoria(tutoria_raw: dict | None) -> dict:
    base = {}
    for tutor, dados in (tutoria_raw or {}).items():
        nome_tutor = str(tutor or "").strip()
        if not nome_tutor:
            continue
        if isinstance(dados, dict):
            registro = estrutura_tutoria_vazia(
                nome=nome_tutor,
                tipo=normalizar_perfil_tutoria(dados.get("tipo", "Professor(a)"))
            )
            registro["espaco"] = str(dados.get("espaco", "")).strip()
            registro["horario"] = str(dados.get("horario", "")).strip()
            registro["dia"] = str(dados.get("dia", "")).strip()
            registro["alunos"] = normalizar_alunos_tutoria(dados.get("alunos", []))
        else:
            registro = estrutura_tutoria_vazia(nome=nome_tutor)
            registro["alunos"] = normalizar_alunos_tutoria(dados)
        base[nome_tutor] = registro
    return base

def obter_registro_tutoria(tutoria_dict: dict, tutor: str) -> dict:
    nome_tutor = str(tutor or "").strip()
    if not nome_tutor:
        return estrutura_tutoria_vazia()
    return normalizar_base_tutoria({nome_tutor: tutoria_dict.get(nome_tutor, {})}).get(
        nome_tutor,
        estrutura_tutoria_vazia(nome=nome_tutor)
    )

def mesclar_tutoria_com_metadados(base_tutoria: dict, referencia_tutoria: dict) -> dict:
    base = normalizar_base_tutoria(base_tutoria)
    referencia = normalizar_base_tutoria(referencia_tutoria)
    for tutor, dados in referencia.items():
        if tutor not in base:
            base[tutor] = dados
            continue
        for campo in ("tipo", "espaco", "horario", "dia"):
            if str(dados.get(campo, "")).strip():
                base[tutor][campo] = str(dados.get(campo, "")).strip()
    return base

def carregar_tutoria_local(fallback: dict | None = None) -> dict:
    try:
        if os.path.exists(TUTORIA_CACHE_ARQUIVO):
            with open(TUTORIA_CACHE_ARQUIVO, "r", encoding="utf-8") as f:
                return normalizar_base_tutoria(json.load(f))
    except Exception as e:
        logger.error(f"Erro ao carregar cache local da tutoria: {e}")
    return normalizar_base_tutoria(fallback or {})

def salvar_tutoria_local(tutoria_dict: dict):
    try:
        os.makedirs(os.path.dirname(TUTORIA_CACHE_ARQUIVO), exist_ok=True)
        with open(TUTORIA_CACHE_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(normalizar_base_tutoria(tutoria_dict), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar cache local da tutoria: {e}")

# ======================================================
# AGENDAMENTO DE ESPAÇOS - CONSTANTES
# ======================================================
SENHA_GESTAO_AGEND = "040600"
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
    "Cyberbullying": "#45B7D1",
    "Racismo": "#9B59B6",
    "Homofobia": "#E91E63",
    "Transfobia": "#D4537E",
    "Gordofobia": "#FFA726",
    "Xenofobia": "#0C703E",
    "Capacitismo (Discriminação por Deficiência)": "#BA68C8",
    "Misoginia / Violência de Gênero": "#167E91",
    "Assédio Moral": "#F06292",
    "Assédio Sexual": "#861C9B",
    "Importunação Sexual / Estupro": "#880E4F",
    "Apologia ao Nazismo": "#4A148C",
    "Posse de Arma de Fogo / Simulacro": "#D32F2F",
    "Posse de Arma Branca": "#B71C1C",
    "Posse de Arma de Brinquedo": "#FFCDD2",
    "Ameaça de Ataque Ativo": "#47187C",
    "Ataque Ativo Concretizado": "#880E4F",
    "Invasão": "#F44336",
    "Ocupação de Unidade Escolar": "#FF5722",
    "Roubo": "#FF7043",
    "Furto": "#FFB74D",
    "Dano ao Patrimônio / Vandalismo": "#FFA726",
    "Posse de Celular / Dispositivo Eletrônico": "#4DB6AC",
    "Consumo de Álcool e Tabaco": "#81C784",
    "Consumo de Cigarro Eletrônico": "#66BB6A",
    "Consumo de Substâncias Ilícitas": "#2E7D32",
    "Comercialização de Álcool e Tabaco": "#388E3C",
    "Envolvimento com Tráfico de Drogas": "#1B5E20",
    "Indisciplina": "#64B5F6",
    "Evasão Escolar / Infrequência": "#42A5F5",
    "Sinais de Automutilação": "#5C6BC0",
    "Sinais de Isolamento Social": "#7986CB",
    "Sinais de Alterações Emocionais": "#9FA8DA",
    "Tentativa de Suicídio": "#3949AB",
    "Suicídio Concretizado": "#1A237E",
    "Mal Súbito": "#FFD54F",
    "Óbito": "#424242",
    "Crimes Cibernéticos": "#00BCD4",
    "Fake News / Disseminação de Informações Falsas": "#26C6DA",
    "Violência Doméstica / Maus Tratos": "#D81B60",
    "Vulnerabilidade Familiar / Negligência": "#EC407A",
    "Alerta de Desaparecimento": "#C2185B",
    "Sequestro": "#880E4F",
    "Homicídio / Homicídio Tentado": "#212121",
    "Feminicídio": "#880E4F",
    "Incitamento a Atos Infracionais": "#5D4037",
    "Acidentes e Eventos Inesperados": "#FFB300",
    "Atos Obscenos / Atos Libidinosos": "#F06292",
    "Uso Inadequado de Dispositivos Eletrônicos": "#4DD0E1",
    "Saída não autorizada": "#FF9800",
    "Ausência não justificada / Cabular aula": "#FF9800",
    "Chegar atrasado": "#FFB74D",
    "Copiar atividades / Colar em avaliações": "#FFA726",
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
        "Cyberbullying": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar evidências digitais\n✅ Notificar famílias\n✅ Acionar Orientação Educacional\n✅ Conselho Tutelar (se menor)\n✅ B.O. recomendado"
        },
        "Racismo": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚖️ CRIME INAFIANÇÁVEL (Lei 7.716/89)\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ Diretoria de Ensino\n✅ Medidas disciplinares cabíveis"
        },
        "Homofobia": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚖️ CRIME (equiparado ao racismo - STF)\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ Diretoria de Ensino\n✅ Medidas disciplinares cabíveis"
        },
        "Transfobia": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚖️ CRIME (equiparado ao racismo - STF)\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ Diretoria de Ensino"
        },
        "Gordofobia": {
            "gravidade": "Média",
            "encaminhamento": "✅ Mediação pedagógica\n✅ Registrar em ata\n✅ Notificar famílias\n✅ Acompanhamento da equipe escolar"
        },
        "Xenofobia": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias\n✅ Acionar rede de proteção\n✅ B.O. recomendado"
        },
        "Capacitismo (Discriminação por Deficiência)": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Acionar equipe de inclusão\n✅ Medidas pedagógicas e disciplinares"
        },
        "Misoginia / Violência de Gênero": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias\n✅ Acionar rede de proteção\n✅ B.O. recomendado"
        },
        "Assédio Moral": {
            "gravidade": "Média",
            "encaminhamento": "✅ Registrar em ata\n✅ Escuta qualificada\n✅ Notificar famílias\n✅ Acompanhamento pedagógico"
        },
        "Assédio Sexual": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 Acionar rede de proteção\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. OBRIGATÓRIO\n✅ Preservar evidências"
        },
        "Importunação Sexual / Estupro": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 Acionar PM (190) e SAMU (192)\n✅ Conselho Tutelar\n✅ B.O. OBRIGATÓRIO\n✅ Hospital de referência\n✅ Rede de proteção"
        },
        "Apologia ao Nazismo": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚖️ CRIME (Lei 7.716/89)\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Diretoria de Ensino\n✅ Medidas disciplinares"
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
        "Posse de Arma de Brinquedo": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Isolar área\n✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho Tutelar (se necessário)"
        },
        "Ameaça de Ataque Ativo": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 ACIONAR PM (190)\n✅ Plano de contingência\n✅ Isolar área\n✅ B.O. OBRIGATÓRIO\n✅ Rede de proteção"
        },
        "Ataque Ativo Concretizado": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 EMERGÊNCIA MÁXIMA (190/192)\n✅ Evacuação e isolamento\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Rede de proteção"
        },
        "Invasão": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Acionar segurança/PM\n✅ Isolar área\n✅ Registrar em ata\n✅ B.O. recomendado"
        },
        "Ocupação de Unidade Escolar": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Acionar gestão e DE\n✅ Registro em ata\n✅ Notificar famílias\n✅ B.O. quando aplicável"
        },
    },
    "🛡️ Patrimônio e Segurança Escolar": {
        "Roubo": {
            "gravidade": "Gravíssima",
            "encaminhamento": "✅ B.O. OBRIGATÓRIO\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Registrar em ata circunstanciada"
        },
        "Furto": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ B.O. recomendado\n✅ Medidas disciplinares cabíveis"
        },
        "Dano ao Patrimônio / Vandalismo": {
            "gravidade": "Média",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Reparação educativa\n✅ Medidas disciplinares"
        }
    },
    "💊 Drogas e Substâncias": {
        "Posse de Celular / Dispositivo Eletrônico": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Retirar dispositivo (conforme regimento)\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Devolver aos responsáveis"
        },
        "Consumo de Álcool e Tabaco": {
            "gravidade": "Média",
            "encaminhamento": "✅ Notificar famílias\n✅ Registrar em ata\n✅ Orientação Educacional\n✅ Encaminhamento à rede de apoio"
        },
        "Consumo de Cigarro Eletrônico": {
            "gravidade": "Média",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Orientação Educacional\n✅ Acompanhamento pedagógico"
        },
        "Consumo de Substâncias Ilícitas": {
            "gravidade": "Grave",
            "encaminhamento": "✅ SAMU (192) se houver emergência\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. recomendado\n✅ CAPS/CREAS\n✅ Acompanhamento especializado"
        },
        "Comercialização de Álcool e Tabaco": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. recomendado"
        },
        "Envolvimento com Tráfico de Drogas": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 ACIONAR PM (190)\n✅ Conselho Tutelar\n✅ B.O. OBRIGATÓRIO\n✅ Notificar famílias\n✅ Rede de proteção"
        },
    },
    "🧠 Saúde Mental e Comportamento": {
        "Indisciplina": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Mediação pedagógica\n✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho de Classe\n✅ Acompanhamento pedagógico"
        },
        "Evasão Escolar / Infrequência": {
            "gravidade": "Média",
            "encaminhamento": "✅ Busca ativa\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Rede de proteção"
        },
        "Sinais de Automutilação": {
            "gravidade": "Grave",
            "encaminhamento": "🚨 Acionamento imediato da rede de proteção\n✅ Notificar famílias\n✅ CAPS\n✅ Conselho Tutelar"
        },
        "Sinais de Isolamento Social": {
            "gravidade": "Média",
            "encaminhamento": "✅ Escuta qualificada\n✅ Notificar famílias\n✅ Acompanhamento psicológico\n✅ Plano de acolhimento"
        },
        "Sinais de Alterações Emocionais": {
            "gravidade": "Média",
            "encaminhamento": "✅ Escuta e acolhimento\n✅ Notificar famílias\n✅ Encaminhar para acompanhamento especializado"
        },
        "Tentativa de Suicídio": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 SAMU (192) IMEDIATO\n✅ Hospital de referência\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ CAPS\n✅ Rede de proteção\n✅ Pós-venção"
        },
        "Suicídio Concretizado": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 Acionar autoridades e rede de emergência\n✅ Protocolo de crise\n✅ Apoio psicossocial à comunidade\n✅ Comunicação oficial orientada"
        },
        "Mal Súbito": {
            "gravidade": "Grave",
            "encaminhamento": "🚨 SAMU (192)\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Encaminhamento médico"
        },
        "Óbito": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 Acionar autoridades competentes\n✅ Notificar famílias\n✅ Registro formal\n✅ Apoio psicossocial"
        },
    },
    "🌐 Crimes e Riscos Digitais": {
        "Crimes Cibernéticos": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Preservar evidências\n✅ Notificar famílias\n✅ B.O. recomendado\n✅ Orientação de segurança digital"
        },
        "Fake News / Disseminação de Informações Falsas": {
            "gravidade": "Média",
            "encaminhamento": "✅ Registrar em ata\n✅ Orientação pedagógica\n✅ Notificar famílias\n✅ Reforço de educação midiática"
        },
        "Uso Inadequado de Dispositivos Eletrônicos": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Aplicar regimento interno"
        }
    },
    "🏠 Proteção Social e Familiar": {
        "Violência Doméstica / Maus Tratos": {
            "gravidade": "Gravíssima",
            "encaminhamento": "✅ Conselho Tutelar\n✅ Notificação compulsória (quando cabível)\n✅ Rede de proteção\n✅ Registro em ata circunstanciada"
        },
        "Vulnerabilidade Familiar / Negligência": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Conselho Tutelar\n✅ CRAS/CREAS\n✅ Notificar famílias\n✅ Plano de acompanhamento"
        },
        "Alerta de Desaparecimento": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 ACIONAR PM (190)\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ Registro oficial imediato"
        },
        "Sequestro": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 ACIONAR PM (190) IMEDIATO\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ B.O. OBRIGATÓRIO"
        },
        "Homicídio / Homicídio Tentado": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 ACIONAR PM (190) e SAMU (192)\n✅ B.O. OBRIGATÓRIO\n✅ Rede de proteção\n✅ Apoio psicossocial"
        },
        "Feminicídio": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 ACIONAR PM (190)\n✅ B.O. OBRIGATÓRIO\n✅ Rede de proteção\n✅ Apoio psicossocial"
        },
        "Incitamento a Atos Infracionais": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. recomendado"
        },
        "Acidentes e Eventos Inesperados": {
            "gravidade": "Média",
            "encaminhamento": "✅ Primeiros socorros\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Encaminhamento médico quando necessário"
        },
        "Atos Obscenos / Atos Libidinosos": {
            "gravidade": "Gravíssima",
            "encaminhamento": "✅ Conselho Tutelar\n✅ Notificar famílias\n✅ B.O. OBRIGATÓRIO\n✅ Rede de proteção"
        },
    },
    "⚠️ Infrações Acadêmicas e de Pontualidade": {
        "Saída não autorizada": {
            "gravidade": "Média",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Reforçar protocolo de segurança\n✅ Orientação Educacional"
        },
        "Ausência não justificada / Cabular aula": {
            "gravidade": "Média",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Busca ativa\n✅ Orientação Educacional"
        },
        "Chegar atrasado": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Conversar com o aluno\n✅ Notificar famílias (se recorrente)\n✅ Verificar motivo dos atrasos\n✅ Orientação Educacional"
        },
        "Copiar atividades / Colar em avaliações": {
            "gravidade": "Média",
            "encaminhamento": "✅ Registrar em ata\n✅ Revisão pedagógica\n✅ Notificar famílias\n✅ Medidas previstas no regimento"
        },
        "Falsificar assinatura de responsáveis": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ Diretoria de Ensino\n✅ Acompanhamento psicológico\n✅ B.O. recomendado"
        },
    },
}

REPAROS_MOJIBAKE = {
    "Ã¡": "á",
    "Ã ": "à",
    "Ã¢": "â",
    "Ã£": "ã",
    "Ã¤": "ä",
    "Ã©": "é",
    "Ãª": "ê",
    "Ã­": "í",
    "Ã³": "ó",
    "Ã´": "ô",
    "Ãµ": "õ",
    "Ãº": "ú",
    "Ã§": "ç",
    "Ã": "Á",
    "Ã€": "À",
    "Ã‚": "Â",
    "Ãƒ": "Ã",
    "Ã‰": "É",
    "ÃŠ": "Ê",
    "Ã": "Í",
    "Ã“": "Ó",
    "Ã”": "Ô",
    "Ã•": "Õ",
    "Ãš": "Ú",
    "Ã‡": "Ç",
    "â€¢": "•",
    "âœ…": "✅",
    "âš–ï¸": "⚖️",
    "ðŸš¨": "🚨",
    "ðŸ”«": "🔫",
    "ðŸ“Œ": "📌",
    "ðŸ›¡ï¸": "🛡️",
    "ðŸ’Š": "💊",
    "ðŸ§ ": "🧠",
    "ðŸŒ": "🌐",
    "ðŸ ": "🏠",
    "âš ï¸": "⚠️",
}
GRAVIDADES_PROTOCOLO = ["Leve", "Média", "Grave", "Gravíssima"]
ORDEM_GRAVIDADE_PROTOCOLO = {nome: idx for idx, nome in enumerate(GRAVIDADES_PROTOCOLO, start=1)}

def corrigir_texto_mojibake(texto: str) -> str:
    texto_corrigido = str(texto or "")
    for origem, destino in REPAROS_MOJIBAKE.items():
        texto_corrigido = texto_corrigido.replace(origem, destino)
    return texto_corrigido.strip()

def normalizar_gravidade_protocolo(valor: str) -> str:
    gravidade = corrigir_texto_mojibake(valor)
    gravidade_norm = "".join(
        ch for ch in unicodedata.normalize("NFD", gravidade.lower())
        if unicodedata.category(ch) != "Mn"
    ).strip()
    mapa = {
        "leve": "Leve",
        "media": "Média",
        "média": "Média",
        "grave": "Grave",
        "gravissima": "Gravíssima",
        "gravíssima": "Gravíssima",
    }
    return mapa.get(gravidade_norm, "Leve")

def corrigir_protocolo_179(protocolo: dict) -> dict:
    protocolo_corrigido = {}
    for grupo, infracoes in (protocolo or {}).items():
        grupo_corrigido = corrigir_texto_mojibake(grupo)
        protocolo_corrigido[grupo_corrigido] = {}
        for nome_infracao, dados in (infracoes or {}).items():
            infracao_corrigida = corrigir_texto_mojibake(nome_infracao)
            protocolo_corrigido[grupo_corrigido][infracao_corrigida] = {
                "gravidade": normalizar_gravidade_protocolo(dados.get("gravidade", "Leve")),
                "encaminhamento": corrigir_texto_mojibake(dados.get("encaminhamento", "")),
            }
    return protocolo_corrigido

PROTOCOLO_179 = corrigir_protocolo_179(PROTOCOLO_179)
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


def page_header(titulo: str, subtitulo: str = "", cor: str = "#2563eb"):
    """Renderiza um cabeçalho de página moderno e consistente."""
    partes = titulo.split(maxsplit=1)
    primeiro_token = partes[0] if partes else ""
    token_tem_texto = any(ch.isalnum() for ch in primeiro_token)

    if len(partes) > 1 and not token_tem_texto:
        icone = primeiro_token
        titulo_texto = partes[1]
    else:
        icone = "📌"
        titulo_texto = titulo

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

def serie_compativel_turma(serie_eletiva: str, turma_sistema: str) -> bool:
    """Verifica se uma série da eletiva (ex.: 6A) combina com turma do sistema (ex.: 6º Ano A)."""
    serie_norm = normalizar_texto(str(serie_eletiva or ""))
    turma_norm = normalizar_texto(str(turma_sistema or ""))
    if not serie_norm:
        return True
    letras = "".join(ch for ch in serie_norm if ch.isalpha())
    numeros = "".join(ch for ch in serie_norm if ch.isdigit())
    if numeros and numeros not in turma_norm:
        return False
    if letras and letras not in turma_norm:
        return False
    return True

def formatar_turma_eletiva(valor: str) -> str:
    """
    Padroniza a escrita da turma/série.
    Exemplos aceitos: 6a, 6 A, 6º A, 6º Ano A, 6 ano a -> 6º A.
    """
    texto = corrigir_texto_mojibake(str(valor or "").strip())
    if not texto:
        return ""

    texto_norm = normalizar_texto(texto)
    texto_norm = (
        texto_norm
        .replace("TURMA", " ")
        .replace("ANO", " ")
        .replace("SERIE", " ")
        .replace("SÉRIE", " ")
        .replace("º", " ")
        .replace("ª", " ")
        .replace("-", " ")
        .replace("/", " ")
    )
    texto_norm = re.sub(r"\s+", " ", texto_norm).strip()

    m = re.search(r"\b(\d{1,2})\s*([A-Z])\b", texto_norm)
    if m:
        return f"{int(m.group(1))}º {m.group(2).upper()}"

    m = re.search(r"\b(\d{1,2})([A-Z])\b", texto_norm)
    if m:
        return f"{int(m.group(1))}º {m.group(2).upper()}"

    m = re.search(r"\b(\d{1,2})\b", texto_norm)
    if m:
        return f"{int(m.group(1))}º"

    return texto.strip()


def turma_para_comparacao(valor: str) -> str:
    """Normaliza turma para comparação segura, sem depender de variações de escrita."""
    return normalizar_texto(formatar_turma_eletiva(valor))




# ======================================================
# TUTORIA - CLASSIFICACAO POR TURNO E ETAPA
# ======================================================
def extrair_numero_letra_turma(valor: str) -> tuple[int | None, str]:
    """Extrai numero e letra da turma padronizada. Ex.: 9A, 9º A -> (9, 'A')."""
    turma = formatar_turma_eletiva(valor)
    m = re.search(r"(\d{1,2})\D*([A-Z])?", normalizar_texto(turma))
    if not m:
        return None, ""
    return int(m.group(1)), (m.group(2) or "").upper()

def classificar_etapa_tutoria(valor: str) -> str:
    numero, _ = extrair_numero_letra_turma(valor)
    if numero in (6, 7, 8, 9):
        return "Ensino Fundamental"
    if numero in (1, 2, 3):
        return "Ensino Medio"
    return "Sem etapa definida"

def classificar_turno_tutoria(valor: str) -> str:
    """Turno 1 = 6º ao 9º + 3º A e 3º B. Turno 2 = demais turmas do Ensino Medio."""
    numero, letra = extrair_numero_letra_turma(valor)
    if numero in (6, 7, 8, 9):
        return "Turno 1"
    if numero == 3 and letra in {"A", "B"}:
        return "Turno 1"
    if numero in (1, 2, 3):
        return "Turno 2"
    return "Sem turno definido"

def ordenar_turma_tutoria(turma: str) -> tuple[int, str]:
    numero, letra = extrair_numero_letra_turma(turma)
    return (numero if numero is not None else 99, letra or "Z")

def estudante_ativo(linha) -> bool:
    """Considera ativo todo estudante que nao esteja claramente marcado como inativo."""
    for coluna in ["situacao", "situação", "status", "ativo"]:
        if coluna not in linha.index:
            continue
        valor = linha.get(coluna)
        if isinstance(valor, bool):
            return valor
        if valor is None or str(valor).strip() == "" or str(valor).lower().strip() in {"nan", "none", "null"}:
            return True
        valor_norm = normalizar_texto(valor)
        termos_inativos = [
            "INATIVO", "INATIVA", "TRANSFERIDO", "TRANSFERIDA", "REMOVIDO", "REMOVIDA",
            "EVADIDO", "EVADIDA", "CANCELADO", "CANCELADA", "BAIXADO", "BAIXADA",
            "DESISTENTE", "ABANDONO", "ENCERRADO", "ENCERRADA"
        ]
        if any(termo in valor_norm for termo in termos_inativos):
            return False
        return True
    return True

def preparar_base_alunos_ativos_tutoria(df_alunos: pd.DataFrame) -> pd.DataFrame:
    """Prepara a base de estudantes do Supabase para busca inteligente da tutoria."""
    if df_alunos is None or df_alunos.empty or "nome" not in df_alunos.columns:
        return pd.DataFrame()

    base = df_alunos.copy()
    if "turma" not in base.columns:
        base["turma"] = ""
    if "ra" not in base.columns:
        base["ra"] = ""
    if "situacao" not in base.columns:
        base["situacao"] = ""

    base["nome"] = base["nome"].astype(str).str.strip()
    base["turma"] = base["turma"].astype(str).apply(formatar_turma_eletiva)
    base["ra"] = base["ra"].astype(str).str.replace(r"\D", "", regex=True)
    base["nome_norm"] = base["nome"].apply(normalizar_texto)
    base["nome_aprox"] = base["nome"].apply(_nome_para_busca_aproximada)
    base["turma_norm"] = base["turma"].apply(turma_para_comparacao)
    base = base[base.apply(estudante_ativo, axis=1)]
    base = base[base["nome"].str.strip() != ""]
    return base.reset_index(drop=True)

def _nome_para_busca_aproximada(valor: str) -> str:
    """
    Cria uma versao fonetica simples para nomes brasileiros.

    A ideia e priorizar a sonoridade, nao a grafia:
    Elizabete/Elisabete, Thalita/Talita, Henzo/Enzo, Iago/Yago,
    Manuela/Manuella, Felipe/Phelipe, Kauan/Cauan etc.
    """
    texto = normalizar_texto(valor)

    trocas = [
        ("PH", "F"),
        ("TH", "T"),
        ("Y", "I"),
        ("W", "V"),
        ("K", "C"),
        ("QU", "C"),
        ("Q", "C"),
        ("Ç", "S"),
        ("CE", "SE"),
        ("CI", "SI"),
        ("SC", "S"),
        ("SÇ", "S"),
        ("SS", "S"),
        ("XC", "S"),
        ("Z", "S"),
        ("CH", "X"),
        ("LH", "LI"),
        ("NH", "NI"),
        ("H", ""),
    ]
    for antigo, novo in trocas:
        texto = texto.replace(antigo, novo)

    texto = re.sub(r"[^A-Z0-9 ]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    # Reduz letras repetidas: ALLANA -> ALANA, MANUELLA -> MANUELA.
    texto = re.sub(r"([A-Z])\1+", r"\1", texto)
    return texto


def _score_nome_tutoria(nome_digitado: str, nome_base: str) -> float:
    """Pontua semelhanca considerando escrita, fonetica e tokens do nome."""
    nome_norm = normalizar_texto(nome_digitado)
    base_norm = normalizar_texto(nome_base)
    nome_aprox = _nome_para_busca_aproximada(nome_digitado)
    base_aprox = _nome_para_busca_aproximada(nome_base)
    if not nome_norm or not base_norm:
        return 0.0

    score = max(
        SequenceMatcher(None, nome_norm, base_norm).ratio(),
        SequenceMatcher(None, nome_aprox, base_aprox).ratio(),
    )

    if base_norm.startswith(nome_norm) or base_aprox.startswith(nome_aprox):
        score = max(score, 0.97)
    elif nome_norm in base_norm or nome_aprox in base_aprox:
        score = max(score, 0.93)

    tokens_digitados = [t for t in nome_aprox.split() if len(t) >= 2]
    tokens_base = [t for t in base_aprox.split() if len(t) >= 2]

    if tokens_digitados and tokens_base:
        pontos = 0.0
        for token in tokens_digitados:
            melhor_token = 0.0
            for tb in tokens_base:
                s = SequenceMatcher(None, token, tb).ratio()
                if token == tb:
                    s = 1.0
                elif token in tb or tb in token:
                    s = max(s, 0.90)
                melhor_token = max(melhor_token, s)
            pontos += melhor_token

        score_tokens = pontos / max(len(tokens_digitados), 1)
        score = max(score, score_tokens)

        primeiro_digitado = tokens_digitados[0]
        primeiro_base = tokens_base[0]
        score_primeiro = SequenceMatcher(None, primeiro_digitado, primeiro_base).ratio()
        if primeiro_digitado == primeiro_base or primeiro_digitado in primeiro_base or primeiro_base in primeiro_digitado:
            score_primeiro = max(score_primeiro, 0.94)
        if score_primeiro >= 0.78:
            score = max(score, 0.70 + min(score_primeiro, 1.0) * 0.25)

    return float(min(score, 1.0))

def buscar_estudante_ativo_mais_proximo(nome_digitado: str, serie_digitada: str, df_alunos: pd.DataFrame) -> dict | None:
    """Busca o estudante ativo mais proximo no Supabase usando turma como confirmacao forte."""
    base = preparar_base_alunos_ativos_tutoria(df_alunos)
    if base.empty:
        return None

    nome_original = str(nome_digitado or "").strip()
    serie_original = formatar_turma_eletiva(serie_digitada)
    nome_norm = normalizar_texto(nome_original)
    serie_norm = turma_para_comparacao(serie_original)
    ra_digitado = "".join(ch for ch in nome_original if ch.isdigit())

    if ra_digitado and len(ra_digitado) >= 5:
        por_ra = base[base["ra"] == ra_digitado]
        if not por_ra.empty:
            aluno = por_ra.iloc[0]
            return {"nome": aluno.get("nome", ""), "serie": aluno.get("turma", ""), "ra": aluno.get("ra", ""), "score": 1.0, "status_busca": "RA encontrado"}

    if not nome_norm:
        return None

    candidatos = base
    if serie_norm:
        candidatos_mesma_turma = base[base["turma_norm"] == serie_norm]
        if candidatos_mesma_turma.empty:
            candidatos_mesma_turma = base[base["turma"].apply(lambda t: serie_compativel_turma(serie_original, t))]
        if not candidatos_mesma_turma.empty:
            candidatos = candidatos_mesma_turma

    melhor = None
    melhor_score_nome = 0.0
    melhor_score_final = 0.0
    melhor_serie_ok = False

    for _, aluno in candidatos.iterrows():
        score_nome = _score_nome_tutoria(nome_original, aluno.get("nome", ""))
        turma_aluno = aluno.get("turma", "")
        turma_aluno_norm = aluno.get("turma_norm", turma_para_comparacao(turma_aluno))
        serie_ok = True
        if serie_norm:
            serie_ok = (serie_norm == turma_aluno_norm) or serie_compativel_turma(serie_original, turma_aluno)
        score_final = score_nome + (0.25 if serie_norm and serie_ok else (-0.45 if serie_norm else 0))
        if score_final > melhor_score_final:
            melhor_score_final = score_final
            melhor_score_nome = score_nome
            melhor = aluno
            melhor_serie_ok = serie_ok

    limite_nome = 0.42 if serie_norm and melhor_serie_ok else 0.72
    limite_final = 0.60 if serie_norm and melhor_serie_ok else 0.78
    if melhor is None or melhor_score_nome < limite_nome or melhor_score_final < limite_final:
        return None

    return {
        "nome": melhor.get("nome", ""),
        "serie": melhor.get("turma", ""),
        "ra": melhor.get("ra", ""),
        "score": round(float(min(melhor_score_final, 1.0)), 3),
        "status_busca": "Encontrado por sonoridade do nome e turma compativel" if melhor_serie_ok else "Encontrado por sonoridade do nome",
    }

def resolver_estudantes_tutoria(novos_estudantes: list, df_alunos: pd.DataFrame) -> tuple[list, list]:
    resolvidos = []
    nao_encontrados = []
    for item in novos_estudantes or []:
        nome_digitado = str(item.get("nome", "")).strip()
        serie_digitada = formatar_turma_eletiva(str(item.get("serie", "")).strip())
        if not nome_digitado:
            continue
        encontrado = buscar_estudante_ativo_mais_proximo(nome_digitado, serie_digitada, df_alunos)
        if encontrado:
            resolvidos.append({
                "nome": encontrado["nome"],
                "serie": encontrado["serie"],
                "ra": encontrado.get("ra", ""),
                "nome_digitado": nome_digitado,
                "serie_digitada": serie_digitada,
                "score": encontrado.get("score", 0),
                "status_busca": encontrado.get("status_busca", ""),
            })
        else:
            nao_encontrados.append({"nome": nome_digitado, "serie": serie_digitada, "motivo": "Nao localizado com seguranca por sonoridade entre estudantes ativos do Supabase"})
    return resolvidos, nao_encontrados

# ======================================================
# TUTORIA - ESPACOS PADRAO
# ======================================================
# Espacos fisicos separados do nome do responsavel.
# Ex.: responsavel = Patricia | espaco = Sala 1
TUTORIA_ESPACOS_PADRAO = [
    "Sala 1",
    "Sala 2",
    "Sala 3",
    "Sala 4",
    "Sala de Leitura",
    "Sala 5",
    "Sala 6",
    "Sala de video",
    "Sala 7",
    "Sala 8",
    "Sala 9",
    "Sala 10",
    "Sala 11",
    "Patio",
    "Direcao",
    "Coordenacao",
    "Informatica",
]

TUTORIA_RESPONSAVEIS_REFERENCIA = {
    "Sala 1": "Patricia",
    "Sala 2": "Veronica",
    "Sala 3": "Fagna",
    "Sala 4": "Elaine",
    "Sala de Leitura": "Giovana",
    "Sala 5": "Fernanda",
    "Sala 6": "Lourdes",
    "Sala de video": "Anderson",
    "Sala 7": "Shirley",
    "Sala 8": "Rosemeire",
    "Sala 9": "Rosangela",
    "Sala 10": "Solange",
    "Sala 11": "Silvana/Jaqueline",
    "Patio": "Itatiara / Lucineide / Guilherme C.",
    "Direcao": "Renan",
    "Coordenacao": "Aleandro",
    "Informatica": "Erika",
}

def normalizar_espaco_tutoria(valor: str) -> str:
    """
    Padroniza o campo de espaço da tutoria.
    Se houver cadastro antigo como "Sala 1 - Patrícia", mantém apenas "Sala 1".
    """
    texto = str(valor or "").strip()
    if not texto:
        return ""

    texto = corrigir_texto_mojibake(texto)

    # Remove nome do responsável quando vier no formato antigo "Espaço - Professor".
    if " - " in texto:
        possivel_espaco = texto.split(" - ", 1)[0].strip()
        if possivel_espaco:
            texto = possivel_espaco

    mapa_padrao = {normalizar_texto(item): item for item in TUTORIA_ESPACOS_PADRAO}
    chave = normalizar_texto(texto)
    return mapa_padrao.get(chave, texto)


def obter_opcoes_espacos_tutoria(tutoria_dict: dict) -> list[str]:
    """Lista espaços padrão e inclui novos espaços já cadastrados na tutoria."""
    opcoes = []
    vistos = set()

    for espaco in TUTORIA_ESPACOS_PADRAO:
        espaco_limpo = normalizar_espaco_tutoria(espaco)
        chave = normalizar_texto(espaco_limpo)
        if espaco_limpo and chave not in vistos:
            opcoes.append(espaco_limpo)
            vistos.add(chave)

    for _, dados in normalizar_base_tutoria(tutoria_dict).items():
        espaco = normalizar_espaco_tutoria(dados.get("espaco", ""))
        chave = normalizar_texto(espaco)
        if espaco and chave not in vistos:
            opcoes.append(espaco)
            vistos.add(chave)

    return opcoes

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
        "SAIDA": ["SAIDA", "SAIR", "FUGIR", "EVADIR", "CABULAR", "AUSENCIA"],
        "FALSIFICAR": ["FALSIFICAR", "ASSINATURA", "COLAR", "COPIAR"],
        "SUICIDIO": ["SUICIDIO", "AUTOMUTILACAO", "EMOCIONAL", "ISOLAMENTO"],
        "DIGITAL": ["CYBER", "CIBERNETICO", "FAKE NEWS", "ONLINE"],
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
# IA CONVIVA PEDAGÓGICA ONLINE — CONFIGURAÇÃO
# ======================================================

PROMPT_IA_CONVIVA_PEDAGOGICA = """
Você é a IA Conviva Pedagógica, uma assistente educacional que apoia professores, coordenação e gestão escolar na produção de registros escolares.

FUNÇÃO:
Auxiliar na escrita, revisão, organização e qualificação pedagógica de textos escolares com linguagem clara, ética, profissional e adequada ao contexto da escola pública.

LIMITES:
- Não substitui professor, coordenação ou gestão;
- Não realiza diagnósticos clínicos ou psicológicos;
- Não inventa fatos;
- Não utiliza linguagem ofensiva ou discriminatória.

PRINCÍPIOS:
1. Linguagem pedagógica, respeitosa e não discriminatória;
2. Escrita objetiva, clara e formal;
3. Preservação da dignidade do estudante e da família;
4. Uso de termos adequados ao contexto escolar;
5. Foco em registros observáveis e pedagógicos.

ESTILO DE ESCRITA:
- Profissional
- Claro
- Humanizado
- Objetivo
- Sem julgamentos
- Sem linguagem punitiva
- Sem exposição desnecessária

AO RECEBER UM TEXTO:
- Corrigir ortografia e gramática;
- Melhorar organização das ideias;
- Transformar linguagem informal em pedagógica;
- Manter o sentido original;
- Não adicionar informações novas;
- Gerar versão pronta para uso escolar.
"""

INSTRUCOES_TAREFAS_IA_RELATORIO = {
    "Corrigir ortografia e gramática": (
        "Corrija ortografia, acentuação, pontuação e concordância, "
        "mantendo o sentido original e adequando a linguagem ao contexto escolar."
    ),
    "Melhorar escrita pedagógica": (
        "Reescreva o texto em linguagem pedagógica, profissional e objetiva, "
        "removendo julgamentos, rótulos ou termos inadequados."
    ),
    "Deixar mais objetivo": (
        "Reescreva de forma mais direta, clara e adequada ao contexto escolar, "
        "mantendo apenas as informações essenciais."
    ),
    "Transformar em parecer descritivo": (
        "Transforme o texto em um parecer descritivo escolar, com linguagem formal, "
        "baseado em evidências e sem tom punitivo."
    ),
    "Sugerir encaminhamentos pedagógicos": (
        "Elabore encaminhamentos pedagógicos possíveis no contexto escolar, "
        "sem realizar diagnósticos clínicos."
    ),
    "Gerar escrita corrida do relatório": (
        "Organize as informações em texto corrido de relatório escolar, "
        "com estrutura clara e coesa."
    ),
}

TERMOS_OFENSIVOS_RELATORIO = [
    "idiota",
    "burro",
    "burra",
    "preguiçoso",
    "preguiçosa",
    "incapaz",
    "insuportável",
    "insuportavel",
    "problema",
    "mau aluno",
    "má aluna",
]
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
    ra_url = requests.utils.quote(str(ra), safe="")
    sucesso = _supabase_mutation("PATCH", f"alunos?ra=eq.{ra_url}", dados, "atualizar aluno")
    if sucesso:
        carregar_alunos.clear()
    return sucesso

@com_tratamento_erro
def excluir_alunos_por_turma(turma: str) -> bool:
    if not turma:
        raise ErroValidacao("turma", "Turma não pode ser vazia")
    turma_url = requests.utils.quote(str(turma), safe="")
    sucesso = _supabase_mutation("DELETE", f"alunos?turma=eq.{turma_url}", None, "excluir alunos da turma")
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

def consolidar_categoria_ocorrencia(infracoes: list[str]) -> str:
    categorias = []
    vistos = set()
    for item in infracoes or []:
        nome = str(item or "").strip()
        chave = normalizar_texto(nome)
        if not nome or chave in vistos:
            continue
        vistos.add(chave)
        categorias.append(nome)
    return " / ".join(categorias)

# ======================================================
# RELATÓRIOS DOS ESTUDANTES
# ======================================================

RELATORIOS_LOCAL_PATH = os.path.join(os.getcwd(), "data", "relatorios_estudantes_local.json")
TURMAS_CONFIG_LOCAL_PATH = os.path.join(os.getcwd(), "data", "turmas_config_local.json")

def _garantir_arquivo_json_local(caminho: str, padrao):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    if not os.path.exists(caminho):
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(padrao, arquivo, ensure_ascii=False, indent=2)

def _garantir_arquivo_relatorios_local():
    _garantir_arquivo_json_local(RELATORIOS_LOCAL_PATH, [])

def _carregar_relatorios_local() -> list[dict]:
    _garantir_arquivo_relatorios_local()
    try:
        with open(RELATORIOS_LOCAL_PATH, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, list) else []
    except Exception:
        return []

def _salvar_relatorios_local(registros: list[dict]) -> bool:
    _garantir_arquivo_relatorios_local()
    with open(RELATORIOS_LOCAL_PATH, "w", encoding="utf-8") as arquivo:
        json.dump(registros, arquivo, ensure_ascii=False, indent=2)
    return True

def normalizar_config_turmas(config_raw) -> dict:
    base = {}
    if isinstance(config_raw, list):
        itens = config_raw
    elif isinstance(config_raw, dict):
        itens = [{"turma": chave, **(valor if isinstance(valor, dict) else {})} for chave, valor in config_raw.items()]
    else:
        itens = []
    for item in itens:
        turma = str(item.get("turma", "")).strip()
        if not turma:
            continue
        base[turma] = {
            "turma": turma,
            "coordenador_sala": str(item.get("coordenador_sala", "")).strip(),
            "updated_at": str(item.get("updated_at", datetime.now().isoformat())).strip() or datetime.now().isoformat(),
        }
    return dict(sorted(base.items()))

def _carregar_turmas_config_local() -> dict:
    _garantir_arquivo_json_local(TURMAS_CONFIG_LOCAL_PATH, {})
    try:
        with open(TURMAS_CONFIG_LOCAL_PATH, "r", encoding="utf-8") as arquivo:
            return normalizar_config_turmas(json.load(arquivo))
    except Exception:
        return {}

def _salvar_turmas_config_local(config: dict) -> bool:
    _garantir_arquivo_json_local(TURMAS_CONFIG_LOCAL_PATH, {})
    with open(TURMAS_CONFIG_LOCAL_PATH, "w", encoding="utf-8") as arquivo:
        json.dump(normalizar_config_turmas(config), arquivo, ensure_ascii=False, indent=2)
    return True

def _limpar_cache_turmas_config():
    try:
        carregar_config_turmas.clear()
    except Exception:
        pass

@st.cache_data(ttl=300)
def carregar_config_turmas() -> pd.DataFrame:
    if SUPABASE_VALID:
        try:
            return _supabase_get_dataframe("turmas_config?select=*&order=turma.asc", "carregar configuração das turmas")
        except Exception as e:
            logger.warning(f"Fallback local da configuração de turmas ativado: {e}")
    return pd.DataFrame(list(_carregar_turmas_config_local().values()))

def salvar_config_turma(turma: str, coordenador_sala: str) -> tuple[bool, str]:
    turma = str(turma).strip()
    coordenador_sala = str(coordenador_sala).strip()
    if not turma:
        raise ErroValidacao("turma", "Informe a turma para salvar a configuração.")

    payload = {
        "turma": turma,
        "coordenador_sala": coordenador_sala,
        "updated_at": datetime.now().isoformat(),
    }

    if SUPABASE_VALID:
        try:
            _supabase_request("DELETE", f"turmas_config?turma=eq.{requests.utils.quote(turma, safe='')}")
            _supabase_request("POST", "turmas_config", json=payload)
            _limpar_cache_turmas_config()
            return True, "supabase"
        except Exception as e:
            logger.warning(f"Salvando configuração de turma em base local por indisponibilidade do Supabase: {e}")

    config = _carregar_turmas_config_local()
    config[turma] = payload
    _salvar_turmas_config_local(config)
    _limpar_cache_turmas_config()
    return True, "local"

def renomear_config_turma(turma_antiga: str, turma_nova: str):
    turma_antiga = str(turma_antiga).strip()
    turma_nova = str(turma_nova).strip()
    if not turma_antiga or not turma_nova or turma_antiga == turma_nova:
        return
    config_df = carregar_config_turmas()
    coordenador = ""
    if not config_df.empty and "turma" in config_df.columns:
        config_filtrada = config_df[config_df["turma"].astype(str).str.strip() == turma_antiga]
        if not config_filtrada.empty:
            coordenador = str(config_filtrada.iloc[0].get("coordenador_sala", "")).strip()
    if coordenador:
        salvar_config_turma(turma_nova, coordenador)
        excluir_config_turma(turma_antiga)

def excluir_config_turma(turma: str):
    turma = str(turma).strip()
    if not turma:
        return False, "local"
    if SUPABASE_VALID:
        try:
            sucesso = _supabase_mutation("DELETE", f"turmas_config?turma=eq.{turma}", None, "excluir configuração da turma")
            if sucesso:
                _limpar_cache_turmas_config()
                return True, "supabase"
        except Exception as e:
            logger.warning(f"Excluindo configuração de turma em base local por indisponibilidade do Supabase: {e}")
    config = _carregar_turmas_config_local()
    if turma in config:
        del config[turma]
        _salvar_turmas_config_local(config)
        _limpar_cache_turmas_config()
        return True, "local"
    return False, "local"

def _limpar_cache_relatorios():
    try:
        carregar_relatorios_estudantes.clear()
    except Exception:
        pass

def _padronizar_relatorio_registro(registro: dict) -> dict:
    agora_iso = datetime.now().isoformat()
    base = {
        "id": registro.get("id"),
        "turma": str(registro.get("turma", "")).strip(),
        "ra": str(registro.get("ra", "")).strip(),
        "aluno": str(registro.get("aluno", "")).strip(),
        "data_inicio": str(registro.get("data_inicio", "")).strip(),
        "data_fim": str(registro.get("data_fim", "")).strip(),
        "professor_autor": str(registro.get("professor_autor", "")).strip(),
        "professor_responsavel_sala": str(registro.get("professor_responsavel_sala", "")).strip(),
        "coordenador_sala": str(registro.get("coordenador_sala", "")).strip(),
        "componente_curricular": str(registro.get("componente_curricular", "")).strip(),
        "situacao_geral": str(registro.get("situacao_geral", "Em acompanhamento")).strip(),
        "frequencia_percentual": float(registro.get("frequencia_percentual", 100) or 0),
        "desenvolvimento_academico": str(registro.get("desenvolvimento_academico", "")).strip(),
        "observacoes_comportamentais": str(registro.get("observacoes_comportamentais", "")).strip(),
        "estrategias_adotadas": str(registro.get("estrategias_adotadas", "")).strip(),
        "pontos_atencao": str(registro.get("pontos_atencao", "")).strip(),
        "pontos_atencao_automaticos": registro.get("pontos_atencao_automaticos", []),
        "indicacao_grave_professor": bool(registro.get("indicacao_grave_professor", False)),
        "descricao_ponto_grave": str(registro.get("descricao_ponto_grave", "")).strip(),
        "escrita_corrida_ultima": str(registro.get("escrita_corrida_ultima", "")).strip(),
        "escrita_corrida_historico": str(registro.get("escrita_corrida_historico", "")).strip(),
        "ultima_edicao_por": str(registro.get("ultima_edicao_por", registro.get("professor_autor", ""))).strip(),
        "created_at": str(registro.get("created_at", agora_iso)).strip() or agora_iso,
        "updated_at": str(registro.get("updated_at", agora_iso)).strip() or agora_iso,
    }
    if not isinstance(base["pontos_atencao_automaticos"], list):
        try:
            base["pontos_atencao_automaticos"] = json.loads(base["pontos_atencao_automaticos"])
        except Exception:
            base["pontos_atencao_automaticos"] = []
    return base

def _proximo_id_relatorio_local(registros: list[dict]) -> int:
    ids = []
    for item in registros:
        try:
            ids.append(int(item.get("id", 0)))
        except Exception:
            continue
    return (max(ids) if ids else 0) + 1

@st.cache_data(ttl=300)
def carregar_relatorios_estudantes() -> pd.DataFrame:
    if SUPABASE_VALID:
        try:
            return _supabase_get_dataframe(
                "relatorios_estudantes?select=*&order=data_fim.desc,id.desc",
                "carregar relatórios dos estudantes"
            )
        except Exception as e:
            logger.warning(f"Fallback local de relatórios ativado: {e}")
    return pd.DataFrame(_carregar_relatorios_local())

def salvar_relatorio_estudante(relatorio: dict) -> tuple[bool, str]:
    relatorio = _padronizar_relatorio_registro(relatorio)
    if not relatorio.get("aluno"):
        raise ErroValidacao("aluno", "Selecione um estudante para salvar o relatório.")

    relatorio["updated_at"] = datetime.now().isoformat()

    if SUPABASE_VALID:
        try:
            payload = dict(relatorio)
            if payload.get("id") in ("", None):
                payload.pop("id", None)
            try:
                sucesso = _supabase_mutation("POST", "relatorios_estudantes", payload, "salvar relatório do estudante")
                if sucesso:
                    _limpar_cache_relatorios()
                    return True, "supabase"
            except Exception:
                payload_sem_extras = dict(payload)
                payload_sem_extras.pop("escrita_corrida_ultima", None)
                payload_sem_extras.pop("escrita_corrida_historico", None)
                if payload_sem_extras != payload:
                    sucesso = _supabase_mutation("POST", "relatorios_estudantes", payload_sem_extras, "salvar relatório do estudante")
                    if sucesso:
                        _limpar_cache_relatorios()
                        return True, "supabase"
                raise
        except Exception as e:
            logger.warning(f"Salvando relatório em base local por indisponibilidade do Supabase: {e}")

    registros = [_padronizar_relatorio_registro(item) for item in _carregar_relatorios_local()]
    if not relatorio.get("id"):
        relatorio["id"] = _proximo_id_relatorio_local(registros)
    registros.append(relatorio)
    _salvar_relatorios_local(registros)
    _limpar_cache_relatorios()
    return True, "local"

def atualizar_relatorio_estudante(id_relatorio, dados: dict) -> tuple[bool, str]:
    if not id_relatorio:
        raise ErroValidacao("id", "Informe um relatório válido para edição.")

    dados = dict(dados)
    dados["updated_at"] = datetime.now().isoformat()

    if SUPABASE_VALID:
        try:
            try:
                sucesso = _supabase_mutation(
                    "PATCH",
                    f"relatorios_estudantes?id=eq.{id_relatorio}",
                    dados,
                    "atualizar relatório do estudante"
                )
                if sucesso:
                    _limpar_cache_relatorios()
                    return True, "supabase"
            except Exception:
                dados_sem_extras = dict(dados)
                dados_sem_extras.pop("escrita_corrida_ultima", None)
                dados_sem_extras.pop("escrita_corrida_historico", None)
                if dados_sem_extras != dados:
                    sucesso = _supabase_mutation(
                        "PATCH",
                        f"relatorios_estudantes?id=eq.{id_relatorio}",
                        dados_sem_extras,
                        "atualizar relatório do estudante"
                    )
                    if sucesso:
                        _limpar_cache_relatorios()
                        return True, "supabase"
                raise
        except Exception as e:
            logger.warning(f"Atualizando relatório em base local por indisponibilidade do Supabase: {e}")

    registros = [_padronizar_relatorio_registro(item) for item in _carregar_relatorios_local()]
    atualizado = False
    for idx, item in enumerate(registros):
        if str(item.get("id")) == str(id_relatorio):
            novo = dict(item)
            novo.update(dados)
            registros[idx] = _padronizar_relatorio_registro(novo)
            atualizado = True
            break
    if not atualizado:
        return False, "local"
    _salvar_relatorios_local(registros)
    _limpar_cache_relatorios()
    return True, "local"

def excluir_relatorio_estudante(id_relatorio) -> tuple[bool, str]:
    if not id_relatorio:
        raise ErroValidacao("id", "Informe um relatório válido para exclusão.")

    if SUPABASE_VALID:
        try:
            sucesso = _supabase_mutation(
                "DELETE",
                f"relatorios_estudantes?id=eq.{id_relatorio}",
                None,
                "excluir relatório do estudante"
            )
            if sucesso:
                _limpar_cache_relatorios()
                return True, "supabase"
        except Exception as e:
            logger.warning(f"Excluindo relatório em base local por indisponibilidade do Supabase: {e}")

    registros = _carregar_relatorios_local()
    restantes = [item for item in registros if str(item.get("id")) != str(id_relatorio)]
    if len(restantes) == len(registros):
        return False, "local"
    _salvar_relatorios_local(restantes)
    _limpar_cache_relatorios()
    return True, "local"

    from difflib import SequenceMatcher

def obter_professor_tutor_do_aluno(
    nome_aluno: str,
    turma_aluno: str,
    ra_aluno: str,
    tutoria_dict: dict,
) -> str:
    nome_norm = normalizar_texto(nome_aluno)
    # Garante que RA seja apenas números
    ra_norm = "".join(ch for ch in str(ra_aluno or "") if ch.isdigit())
    turma_norm = normalizar_texto(turma_aluno)
 
    melhor_tutor = ""
    melhor_score = 0.0
 
    # Verifica se o dict existe
    if not tutoria_dict:
        return ""

    for tutor, dados in tutoria_dict.items():
        if not dados or "alunos" not in dados:
            continue

        for item in dados["alunos"]:
            # --- 1. Prioridade Máxima: RA ---
            ra_item = "".join(ch for ch in str(item.get("ra", "")) if ch.isdigit())
            if ra_norm and ra_item and ra_norm == ra_item:
                return tutor # RA é único, achou, volta imediatamente
 
            # --- 2. Verificação de Nome ---
            item_norm = normalizar_texto(item.get("nome", ""))
            if not item_norm:
                continue
 
            # --- 3. Lógica de Série Mais Segura ---
            # Tenta verificar se é exatamente a mesma string ou se contém
            serie_item = normalizar_texto(item.get("serie", ""))
            serie_ok = False
            
            if not serie_item or not turma_norm:
                serie_ok = True # Se não tem info de série, assume ok
            elif serie_item == turma_norm:
                serie_ok = True
            # Lógica de substring apenas se for número curto (ex: "7" em "7A")
            # Evita que "8" case com "18"
            elif len(serie_item) < 3 and len(turma_norm) < 5: 
                 if serie_item in turma_norm or turma_norm in serie_item:
                     serie_ok = True

            if not serie_ok:
                continue # Pula se a série não bater, economiza processamento

            # --- 4. Comparação Fuzzy ---
            if nome_norm == item_norm:
                return tutor # Exato e série ok, retorna
            
            score = SequenceMatcher(None, nome_norm, item_norm).ratio()
            
            # Atualiza melhor score, mas NÃO retorna ainda (para achar o melhor)
            if score > melhor_score:
                melhor_score = score
                melhor_tutor = tutor

    # Retorna apenas se o score for muito alto
    return melhor_tutor if melhor_score >= 0.85 else ""
 
 
def obter_eletiva_do_aluno(
    nome_aluno: str,
    turma_aluno: str,
    ra_aluno: str,
    eletivas_dict: dict,
) -> str:
    """
    Retorna o nome da(o) professora(o) de eletiva vinculado ao aluno.
    Retorna "" se não encontrado.
    """
    nome_norm  = normalizar_texto(nome_aluno)
    ra_norm    = "".join(ch for ch in str(ra_aluno or "") if ch.isdigit())
    turma_norm = normalizar_texto(turma_aluno)
 
    melhor_prof  = ""
    melhor_score = 0.0
 
    for prof, alunos in (eletivas_dict or {}).items():
        for item in alunos:
            # --- match por RA ---
            ra_item = "".join(ch for ch in str(item.get("ra", "")) if ch.isdigit())
            if ra_norm and ra_item and ra_norm == ra_item:
                return prof
 
            item_norm = normalizar_texto(item.get("nome", ""))
            if not item_norm:
                continue
 
            serie_item = normalizar_texto(item.get("serie", ""))
            serie_ok = (not serie_item) or (not turma_norm) or (serie_item in turma_norm) or (turma_norm in serie_item)
 
            score = SequenceMatcher(None, nome_norm, item_norm).ratio()
            if nome_norm == item_norm and serie_ok:
                return prof
            if score > melhor_score and serie_ok:
                melhor_score = score
                melhor_prof  = prof
 
    return melhor_prof if melhor_score >= 0.85 else ""

def gerar_pontos_atencao_automaticos(df_ocorrencias: pd.DataFrame, turma: str, ra: str, aluno: str, data_inicio, data_fim) -> list[str]:
    if df_ocorrencias.empty:
        return []

    df_base = df_ocorrencias.copy()
    if "data" in df_base.columns:
        df_base["data_ref"] = pd.to_datetime(df_base["data"], format="%d/%m/%Y %H:%M", errors="coerce")
    else:
        df_base["data_ref"] = pd.NaT

    data_inicio_ts = pd.Timestamp(data_inicio)
    data_fim_ts = pd.Timestamp(data_fim) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    filtro = pd.Series([True] * len(df_base))
    if "turma" in df_base.columns and turma:
        filtro &= df_base["turma"].astype(str).str.strip() == str(turma).strip()
    if "ra" in df_base.columns and ra:
        filtro &= df_base["ra"].astype(str).str.strip() == str(ra).strip()
    elif "aluno" in df_base.columns and aluno:
        filtro &= df_base["aluno"].astype(str).str.strip() == str(aluno).strip()
    if "gravidade" in df_base.columns:
        filtro &= df_base["gravidade"].astype(str).str.strip().isin(["Grave", "Gravíssima"])
    if "data_ref" in df_base.columns:
        filtro &= df_base["data_ref"].between(data_inicio_ts, data_fim_ts, inclusive="both")

    encontrados = []
    for _, row in df_base[filtro].sort_values("data_ref", ascending=False).iterrows():
        data_txt = row["data_ref"].strftime("%d/%m/%Y") if pd.notna(row["data_ref"]) else str(row.get("data", "Sem data"))
        categoria = str(row.get("categoria", "Sem categoria")).strip()
        gravidade = str(row.get("gravidade", "")).strip()
        professor = str(row.get("professor", "")).strip()
        partes = [data_txt, categoria]
        if gravidade:
            partes.append(gravidade)
        if professor:
            partes.append(f"Prof. {professor}")
        encontrados.append(" - ".join(partes))
    return encontrados
# ======================================================
# AGENDAMENTO - FUNÇÕES SUPABASE
# ======================================================

@st.cache_data(ttl=120)
def carregar_agendamentos_filtrado(data_ini: str, data_fim: str, espaco: str = None, professor: str = None) -> pd.DataFrame:
    try:
        path = "/rest/v1/agendamentos"
        # requests não permite chave duplicada no dict; montar como lista de tuplas
        params_list = [
            ("select", "id,data_agendamento,horario,espaco,turma,disciplina,prioridade,semanas,professor_nome,professor_email,status"),
            ("order", "data_agendamento.asc,horario.asc"),
            ("data_agendamento", f"gte.{data_ini}"),
            ("data_agendamento", f"lte.{data_fim}"),
        ]

        if espaco and espaco in ESPACOS_AGEND:
            params_list.append(("espaco", f"eq.{espaco}"))

        if professor:
            params_list.append(("professor_nome", f"eq.{professor}"))

        rows = _rest_get_agend(path, params=params_list)
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
    # Compatibilidade: algumas bases não possuem a coluna 'tipo'
    if r.status_code >= 400 and "tipo" in str(dados).lower() and "'tipo' column" in r.text:
        dados_retry = dict(dados)
        dados_retry.pop("tipo", None)
        r = requests.post(url, json=dados_retry, headers=HEADERS, timeout=20)
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

def carregar_tutoria_do_excel(caminho_arquivo: str, fallback: dict = None) -> dict:
    """Lê planilha XLSX de tutoria considerando cada aba como um tutor(a)."""
    if not caminho_arquivo or not os.path.exists(caminho_arquivo):
        return normalizar_base_tutoria(fallback if fallback is not None else {})
    try:
        ns = {
            "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        }
        with zipfile.ZipFile(caminho_arquivo) as arquivo_zip:
            shared_strings = []
            if "xl/sharedStrings.xml" in arquivo_zip.namelist():
                root = ET.fromstring(arquivo_zip.read("xl/sharedStrings.xml"))
                for si in root.findall("a:si", ns):
                    textos = [t.text or "" for t in si.iterfind(".//a:t", ns)]
                    shared_strings.append("".join(textos))

            workbook = ET.fromstring(arquivo_zip.read("xl/workbook.xml"))
            rels = ET.fromstring(arquivo_zip.read("xl/_rels/workbook.xml.rels"))
            rel_map = {rel.attrib.get("Id", ""): rel.attrib.get("Target", "") for rel in rels}

            tutoria = {}
            for sheet in workbook.findall("a:sheets/a:sheet", ns):
                tutor_atual = str(sheet.attrib.get("name", "")).strip()
                rel_id = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id", "")
                target = rel_map.get(rel_id, "")
                if not tutor_atual or not target:
                    continue

                caminho_sheet = target.replace("\\", "/")
                if not caminho_sheet.startswith("xl/"):
                    caminho_sheet = f"xl/{caminho_sheet}"
                if caminho_sheet not in arquivo_zip.namelist():
                    continue

                root_sheet = ET.fromstring(arquivo_zip.read(caminho_sheet))
                registro_tutor = estrutura_tutoria_vazia(nome=tutor_atual)
                alunos_tutor = []

                for row in root_sheet.findall(".//a:sheetData/a:row", ns):
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

                    valor_a = str(valores.get("A", "")).strip()
                    valor_b = str(valores.get("B", "")).strip()
                    valor_c = str(valores.get("C", "")).strip()
                    valor_d = str(valores.get("D", "")).strip()
                    valor_e = str(valores.get("E", "")).strip()
                    valor_f = str(valores.get("F", "")).strip()

                    for valor_meta in [valor_a, valor_b, valor_c, valor_d, valor_e, valor_f]:
                        valor_meta = str(valor_meta).strip()
                        if not valor_meta:
                            continue
                        valor_norm = normalizar_texto(valor_meta)
                        if not registro_tutor["espaco"] and any(chave in valor_norm for chave in ("sala", "patio", "pátio", "leitura")) and not valor_norm.startswith("horario"):
                            registro_tutor["espaco"] = valor_meta
                        if not registro_tutor["horario"] and re.search(r"\d{1,2}:\d{2}", valor_meta):
                            registro_tutor["horario"] = valor_meta
                        if not registro_tutor["dia"] and any(dia in valor_norm for dia in DIAS_SEMANA_TUTORIA):
                            registro_tutor["dia"] = valor_meta

                    nome = ""
                    serie = ""

                    if valor_b and valor_c:
                        if not any(ch.isdigit() for ch in valor_b[:4]):
                            nome = valor_b
                            serie = valor_c
                    elif valor_a and valor_b:
                        if not valor_a.replace(".", "").isdigit():
                            nome = valor_a
                            serie = valor_b
                    elif valor_a:
                        combinado = re.match(r"^(.*?)(\d+\s*(?:º|°)?\s*[A-Za-z])$", valor_a)
                        if combinado:
                            nome = combinado.group(1).strip()
                            serie = combinado.group(2).strip()

                    nome_norm = normalizar_texto(nome)
                    if (
                        not nome
                        or nome_norm in {"nome", "nomes", "nome:", "numero", "numero nome:", "vagas", "cadastrados"}
                        or nome_norm.startswith("horario")
                        or nome_norm.startswith("sala")
                        or nome_norm.startswith("patio")
                    ):
                        continue

                    alunos_tutor.append({
                        "nome": nome.strip(),
                        "serie": formatar_turma_eletiva(serie.strip())
                    })

                if alunos_tutor:
                    registro_tutor["alunos"] = alunos_tutor
                    tutoria[tutor_atual] = registro_tutor

            return normalizar_base_tutoria(tutoria if tutoria else (fallback or {}))
    except Exception as e:
        logger.error(f"Erro ao importar tutoria: {e}")
        return normalizar_base_tutoria(fallback if fallback is not None else {})

def converter_eletivas_para_registros(eletivas_dict: dict, origem: str = "excel") -> list:
    registros = []
    for professora, alunos in eletivas_dict.items():
        for item in alunos:
            registros.append({
                "professora": professora,
                "nome_aluno": item.get("nome", ""),
                "serie": formatar_turma_eletiva(item.get("serie", "")),
                "origem": origem
            })
    return registros

def converter_eletivas_supabase_para_dict(df_eletivas: pd.DataFrame) -> dict:
    if df_eletivas.empty:
        return {}
    eletivas = {}
    for _, row in df_eletivas.iterrows():
        professora = str(row.get("professora", "")).strip()
        nome_aluno = str(row.get("nome_aluno", "")).strip()
        serie = formatar_turma_eletiva(str(row.get("serie", "")).strip())
        if not professora or not nome_aluno:
            continue
        eletivas.setdefault(professora, []).append({"nome": nome_aluno, "serie": serie})
    return eletivas

def converter_tutoria_para_registros(tutoria_dict: dict, origem: str = "excel") -> list:
    registros = []
    for tutor, dados in normalizar_base_tutoria(tutoria_dict).items():
        for item in dados.get("alunos", []):
            registros.append({
                "professora": tutor,
                "nome_aluno": item.get("nome", ""),
                "serie": formatar_turma_eletiva(item.get("serie", "")),
                "origem": origem,
                "tipo": normalizar_perfil_tutoria(dados.get("tipo", "Professor(a)")),
                "espaco": str(dados.get("espaco", "")).strip(),
                "horario": str(dados.get("horario", "")).strip(),
                "dia": str(dados.get("dia", "")).strip()
            })
    return registros

def converter_tutoria_supabase_para_dict(df_tutoria: pd.DataFrame) -> dict:
    if df_tutoria.empty:
        return {}
    tutoria = {}
    for _, row in df_tutoria.iterrows():
        tutor = str(row.get("professora", "")).strip()
        nome_aluno = str(row.get("nome_aluno", "")).strip()
        serie = formatar_turma_eletiva(str(row.get("serie", "")).strip())
        if not tutor:
            continue
        tutoria.setdefault(tutor, estrutura_tutoria_vazia(nome=tutor))
        tipo = normalizar_perfil_tutoria(row.get("tipo", "Professor(a)"))
        espaco = str(row.get("espaco", "")).strip()
        horario = str(row.get("horario", "")).strip()
        dia = str(row.get("dia", "")).strip()
        if tipo:
            tutoria[tutor]["tipo"] = tipo
        if espaco:
            tutoria[tutor]["espaco"] = espaco
        if horario:
            tutoria[tutor]["horario"] = horario
        if dia:
            tutoria[tutor]["dia"] = dia
        if nome_aluno:
            tutoria[tutor]["alunos"].append({"nome": nome_aluno, "serie": serie})
    return normalizar_base_tutoria(tutoria)

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
    if "ra" in alunos_db.columns:
        alunos_db["ra_norm"] = alunos_db["ra"].astype(str).apply(lambda x: "".join(ch for ch in x if ch.isdigit()))
    else:
        alunos_db["ra_norm"] = ""
    if "turma" in alunos_db.columns:
        alunos_db["turma_norm"] = alunos_db["turma"].astype(str).apply(normalizar_texto)
    else:
        alunos_db["turma_norm"] = ""

    for item in eletivas_dict.get(nome_professora, []):
        nome_original = item.get("nome", "")
        serie_original = formatar_turma_eletiva(item.get("serie", ""))
        ra_original = "".join(ch for ch in str(item.get("ra", "")) if ch.isdigit())
        nome_norm_excel = normalizar_texto(nome_original)
        melhor_match = None

        # 1) Prioriza match por RA quando disponível
        if ra_original:
            match_ra = alunos_db[alunos_db["ra_norm"] == ra_original]
            if not match_ra.empty:
                melhor_match = match_ra.iloc[0]

        # 2) Match exato por nome (evita pegar irmã/irmão por similaridade)
        if melhor_match is None and nome_norm_excel:
            exatos = alunos_db[alunos_db["nome_norm"] == nome_norm_excel]
            if not exatos.empty:
                exatos_serie = exatos[exatos["turma_norm"].apply(lambda t: serie_compativel_turma(serie_original, t))]
                melhor_match = (exatos_serie.iloc[0] if not exatos_serie.empty else exatos.iloc[0])

        # 3) Fuzzy apenas como fallback, com regra de primeiro nome + série
        if melhor_match is None and nome_norm_excel:
            primeiro_nome = nome_norm_excel.split()[0] if nome_norm_excel.split() else ""
            melhor_score = 0.0
            for _, aluno in alunos_db.iterrows():
                nome_sis = aluno.get("nome_norm", "")
                if not nome_sis:
                    continue
                if primeiro_nome and not nome_sis.startswith(primeiro_nome):
                    continue
                if not serie_compativel_turma(serie_original, aluno.get("turma_norm", "")):
                    continue
                score = SequenceMatcher(None, nome_norm_excel, nome_sis).ratio()
                if score > melhor_score:
                    melhor_score = score
                    melhor_match = aluno
            if melhor_score < 0.92:
                melhor_match = None

        if melhor_match is not None:
            turma_final = str(melhor_match.get("turma", "")).strip() or serie_original
            registros.append({
                "Professor(a)": nome_professora,
                "Nome": nome_original,
                "Turma": turma_final,
                "Aluno Cadastrado": melhor_match.get("nome", ""),
                "RA": melhor_match.get("ra", ""),
                "Turma no Sistema": melhor_match.get("turma", ""),
                "Situação": melhor_match.get("situacao", ""),
                "Status": "Encontrado",
            })
        else:
            registros.append({
                "Professor(a)": nome_professora,
                "Nome": nome_original,
                "Turma": serie_original,
                "Aluno Cadastrado": "",
                "RA": "",
                "Turma no Sistema": "",
                "Situação": "",
                "Status": "Não encontrado",
            })
    return pd.DataFrame(registros)

def montar_dataframe_tutoria(nome_tutor: str, df_alunos: pd.DataFrame, tutoria_dict: dict) -> pd.DataFrame:
    registro_tutor = obter_registro_tutoria(tutoria_dict, nome_tutor)
    df_tutoria = montar_dataframe_eletiva(
        nome_tutor,
        df_alunos,
        {nome_tutor: registro_tutor.get("alunos", [])}
    )
    if df_tutoria.empty:
        return df_tutoria
    df_tutoria["Espaço"] = registro_tutor.get("espaco", "")
    df_tutoria["Horário"] = registro_tutor.get("horario", "")
    df_tutoria["Dia"] = registro_tutor.get("dia", "")
    df_tutoria["Perfil"] = registro_tutor.get("tipo", "Professor(a)")
    return df_tutoria

ELETIVAS_EXCEL = carregar_eletivas_do_excel(ELETIVAS_ARQUIVO, fallback=ELETIVAS)
TUTORIA_EXCEL = carregar_tutoria_do_excel(TUTORIA_ARQUIVO, fallback={})
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

def gerar_pdf_eletiva(contexto: str, df_eletiva: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    doc = _criar_documento_pdf(buffer)
    estilos = getSampleStyleSheet()
    elementos = []
    _adicionar_logo(elementos)

    titulo_style = ParagraphStyle(
        'TituloEletiva',
        parent=estilos['Heading1'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=0.2 * cm,
        textColor=colors.HexColor("#0f766e")
    )
    elementos.append(Paragraph("LISTA DE ELETIVA", titulo_style))
    elementos.append(Spacer(1, 0.1 * cm))
    elementos.append(Paragraph(f"<b>Filtro:</b> {contexto}", estilos['Normal']))
    elementos.append(Paragraph(f"<b>Total de estudantes:</b> {len(df_eletiva)}", estilos['Normal']))
    elementos.append(Spacer(1, 0.2 * cm))

    cabecalho = ["Nome", "Turma", "Professor(a)"]
    linhas = []
    for _, row in df_eletiva.iterrows():
        turma_pdf = str(row.get("Turma", "")).strip() or str(row.get("Turma no Sistema", "")).strip()
        linhas.append([
            str(row.get("Nome", ""))[:48],
            turma_pdf[:24],
            str(row.get("Professor(a)", ""))[:24]
        ])

    tabela = Table([cabecalho] + linhas, colWidths=[9.0 * cm, 4.0 * cm, 5.0 * cm], repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    for i in range(1, len(linhas) + 1):
        bg = colors.whitesmoke if i % 2 == 0 else colors.HexColor("#ecfeff")
        tabela.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), bg)]))

    elementos.append(tabela)
    elementos.append(Spacer(1, 0.2 * cm))

    estilo_rodape = ParagraphStyle(
        'Rodape',
        parent=estilos['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
    elementos.append(Paragraph(f"Sistema Conviva 179 - {ESCOLA_NOME}", estilo_rodape))

    doc.build(elementos)
    buffer.seek(0)
    return buffer

def gerar_pdf_tutoria(contexto: str, df_tutoria: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    doc = _criar_documento_pdf(buffer)
    estilos = getSampleStyleSheet()
    elementos = []
    _adicionar_logo(elementos)

    titulo_style = ParagraphStyle(
        'TituloTutoria',
        parent=estilos['Heading1'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=0.2 * cm,
        textColor=colors.HexColor("#0f766e")
    )
    elementos.append(Paragraph("LISTA DE TUTORIA", titulo_style))
    elementos.append(Spacer(1, 0.1 * cm))
    elementos.append(Paragraph(f"<b>Filtro:</b> {contexto}", estilos['Normal']))
    elementos.append(Paragraph(f"<b>Total de estudantes:</b> {len(df_tutoria)}", estilos['Normal']))
    elementos.append(Spacer(1, 0.2 * cm))

    cabecalho = ["Nome", "Turma", "Professor(a)"]
    linhas = []
    for _, row in df_tutoria.iterrows():
        tutor = str(row.get("Professor(a)", ""))
        turma_pdf = str(row.get("Turma", "")).strip() or str(row.get("Turma no Sistema", "")).strip()
        linhas.append([
            str(row.get("Nome", ""))[:48],
            turma_pdf[:24],
            tutor[:24]
        ])

    tabela = Table([cabecalho] + linhas, colWidths=[9.0 * cm, 4.0 * cm, 5.0 * cm], repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    for i in range(1, len(linhas) + 1):
        bg = colors.whitesmoke if i % 2 == 0 else colors.HexColor("#ecfeff")
        tabela.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), bg)]))

    elementos.append(tabela)
    doc.build(elementos)
    buffer.seek(0)
    return buffer


def gerar_pdf_estudantes_sem_tutor(contexto: str, df_sem_tutor: pd.DataFrame) -> BytesIO:
    """Gera PDF dos estudantes que ainda estão sem tutoria.

    Usa as colunas já montadas na seção Estudantes Sem Tutor:
    Nome, Turma, Etapa, Turno, RA e Situação.
    """
    buffer = BytesIO()
    doc = _criar_documento_pdf(buffer)
    estilos = getSampleStyleSheet()
    elementos = []
    _adicionar_logo(elementos)

    titulo_style = ParagraphStyle(
        'TituloSemTutor',
        parent=estilos['Heading1'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=0.2 * cm,
        textColor=colors.HexColor("#7c2d12")
    )
    elementos.append(Paragraph("ESTUDANTES SEM TUTORIA", titulo_style))
    elementos.append(Spacer(1, 0.1 * cm))
    elementos.append(Paragraph(f"<b>Filtro:</b> {html.escape(str(contexto))}", estilos['Normal']))
    elementos.append(Paragraph(f"<b>Total de estudantes:</b> {len(df_sem_tutor)}", estilos['Normal']))
    elementos.append(Spacer(1, 0.2 * cm))

    cabecalho = ["Nome", "Turma", "Turno", "Etapa", "RA", "Situação"]
    linhas = []
    if df_sem_tutor is not None and not df_sem_tutor.empty:
        for _, row in df_sem_tutor.iterrows():
            linhas.append([
                str(row.get("Nome", ""))[:42],
                str(row.get("Turma", ""))[:14],
                str(row.get("Turno", ""))[:16],
                str(row.get("Etapa", ""))[:20],
                str(row.get("RA", ""))[:14],
                str(row.get("Situação", ""))[:18],
            ])

    if not linhas:
        elementos.append(Paragraph("Nenhum estudante encontrado para este filtro.", estilos['Normal']))
    else:
        tabela = Table([cabecalho] + linhas, colWidths=[6.4 * cm, 2.3 * cm, 2.4 * cm, 3.0 * cm, 2.3 * cm, 2.6 * cm], repeatRows=1)
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#7c2d12")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        for i in range(1, len(linhas) + 1):
            bg = colors.whitesmoke if i % 2 == 0 else colors.HexColor("#fff7ed")
            tabela.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), bg)]))
        elementos.append(tabela)

    elementos.append(Spacer(1, 0.2 * cm))
    estilo_rodape = ParagraphStyle(
        'RodapeSemTutor',
        parent=estilos['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
    elementos.append(Paragraph(f"Sistema Conviva 179 - {ESCOLA_NOME}", estilo_rodape))

    doc.build(elementos)
    buffer.seek(0)
    return buffer


def ler_csv_flexivel(arquivo_upload) -> pd.DataFrame:
    bruto = arquivo_upload.getvalue()
    ultimo_erro = None
    for enc in ("utf-8-sig", "latin-1"):
        try:
            texto = bruto.decode(enc)
            # Tentativa principal: autodetecta delimitador.
            df = pd.read_csv(StringIO(texto), sep=None, engine="python", dtype=str)
            if len(df.columns) <= 1:
                # Fallbacks comuns de exportação escolar.
                for sep in (";", "\t", ","):
                    df = pd.read_csv(StringIO(texto), sep=sep, dtype=str)
                    if len(df.columns) > 1:
                        break
            return df
        except Exception as e:
            ultimo_erro = e
    raise ValueError(f"Não foi possível ler o CSV: {ultimo_erro}")

def normalizar_dataframe_importacao(df_import: pd.DataFrame) -> pd.DataFrame:
    df = df_import.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    df = df.loc[:, ~df.columns.duplicated()]

    # Quando o cabeçalho real vem na primeira linha de dados (ex.: Unnamed:0, Unnamed:1...).
    palavras_chave = ("nome", "aluno", "ra")
    linha_header = None
    limite = min(len(df), 4)
    for i in range(limite):
        vals = [normalizar_texto(v) for v in df.iloc[i].fillna("").astype(str).tolist()]
        joined = " ".join(vals)
        if all(p in joined for p in palavras_chave):
            linha_header = i
            break
    if linha_header is not None:
        novo_header = [str(v).strip() for v in df.iloc[linha_header].fillna("").astype(str).tolist()]
        df = df.iloc[linha_header + 1:].copy()
        df.columns = novo_header

    # Remove colunas completamente vazias ou lixo "Unnamed".
    colunas_validas = []
    for c in df.columns:
        serie = df[c].fillna("").astype(str).str.strip()
        if serie.eq("").all():
            continue
        if str(c).strip().lower().startswith("unnamed") and serie.eq("").all():
            continue
        colunas_validas.append(c)
    if colunas_validas:
        df = df[colunas_validas]

    return df.reset_index(drop=True)

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
def gerar_pdf_relatorio_estudante(registro: dict, df_ocorrencias_aluno: pd.DataFrame) -> BytesIO:
    """
    Gera PDF completo do relatório do estudante com:
    - Cabeçalho da escola (logo se disponível)
    - Dados do aluno (nome, RA, turma, tutor, eletiva)
    - Indicadores (frequência, situação, alertas)
    - Ocorrências graves/gravíssimas no período
    - Desenvolvimento acadêmico, comportamento, estratégias e pontos de atenção
    - Assinatura com data de impressão
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, HRFlowable, Image
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.8 * cm,
    )

    estilos = getSampleStyleSheet()

    COR_PRIMARIA   = colors.HexColor("#1d4ed8")
    COR_SECUNDARIA = colors.HexColor("#0f766e")
    COR_ALERTA     = colors.HexColor("#dc2626")
    COR_AVISO      = colors.HexColor("#d97706")
    COR_CINZA_CLR  = colors.HexColor("#f8fafc")
    COR_BORDA      = colors.HexColor("#e2e8f0")
    COR_TEXTO      = colors.HexColor("#0f172a")
    COR_SUBTEXTO   = colors.HexColor("#475569")

    def _estilo(nome, **kwargs):
        base = kwargs.pop("base", "Normal")
        estilo = ParagraphStyle(nome, parent=estilos[base], **kwargs)
        return estilo

    est_titulo    = _estilo("Titulo",    base="Heading1", fontSize=13, textColor=COR_PRIMARIA,
                            spaceAfter=4, spaceBefore=0, leading=16)
    est_subtitulo = _estilo("Subtitulo", base="Heading2", fontSize=10, textColor=COR_SECUNDARIA,
                            spaceAfter=4, spaceBefore=8, leading=13)
    est_label     = _estilo("Label",     fontSize=8,  textColor=COR_SUBTEXTO,
                            fontName="Helvetica-Bold", spaceAfter=1, leading=10)
    est_valor     = _estilo("Valor",     fontSize=9,  textColor=COR_TEXTO,
                            spaceAfter=2, leading=12)
    est_corpo     = _estilo("Corpo",     fontSize=9,  textColor=COR_TEXTO,
                            spaceAfter=4, leading=13)
    est_rodape    = _estilo("Rodape",    fontSize=7,  textColor=COR_SUBTEXTO,
                            alignment=TA_CENTER, leading=10)
    est_centro    = _estilo("Centro",    fontSize=9,  textColor=COR_TEXTO,
                            alignment=TA_CENTER, leading=12)

    elementos = []

    # Logo / cabeçalho
    logo_path = os.path.join("assets", "images", "eliane_dantas.png")
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=15 * cm, height=3.6 * cm)
            logo.hAlign = "CENTER"
            elementos.append(logo)
            elementos.append(Spacer(1, 0.3 * cm))
        except Exception:
            elementos.append(Paragraph("E.E. ELIANE APARECIDA DANTAS DA SILVA PROFESSORA - PEI", est_titulo))
    else:
        elementos.append(Paragraph("E.E. ELIANE APARECIDA DANTAS DA SILVA PROFESSORA - PEI", est_titulo))
        elementos.append(Spacer(1, 0.2 * cm))

    elementos.append(HRFlowable(width="100%", thickness=2, color=COR_PRIMARIA, spaceAfter=6))
    elementos.append(Paragraph("RELATÓRIO DE ACOMPANHAMENTO DO ESTUDANTE", est_titulo))
    elementos.append(HRFlowable(width="100%", thickness=1, color=COR_BORDA, spaceAfter=8))

    # Dados do aluno
    aluno           = str(registro.get("aluno", "")).strip()
    ra              = str(registro.get("ra", "")).strip()
    turma           = str(registro.get("turma", "")).strip()
    tutor           = str(registro.get("professor_tutor", "")).strip() or "Não localizado"
    eletiva         = str(registro.get("eletiva", "")).strip() or "Não localizado"
    data_inicio     = str(registro.get("data_inicio", "")).strip()
    data_fim        = str(registro.get("data_fim", "")).strip()
    try:
        frequencia = float(registro.get("frequencia_percentual", 100) or 100)
    except (ValueError, TypeError):
        frequencia = 100.0
    situacao        = str(registro.get("situacao_geral", "Em acompanhamento")).strip()
    coordenador     = str(registro.get("coordenador_sala", "")).strip() or "—"
    componente      = str(registro.get("componente_curricular", "")).strip() or "—"
    editor          = str(registro.get("ultima_edicao_por", registro.get("professor_autor", ""))).strip() or "—"

    try:
        data_ini_fmt = pd.to_datetime(data_inicio, errors="coerce").strftime("%d/%m/%Y")
    except Exception:
        data_ini_fmt = data_inicio
    try:
        data_fim_fmt = pd.to_datetime(data_fim, errors="coerce").strftime("%d/%m/%Y")
    except Exception:
        data_fim_fmt = data_fim

    dados_id = [
        [Paragraph("<b>Estudante</b>", est_label),    Paragraph(aluno, est_valor),
         Paragraph("<b>RA</b>", est_label),           Paragraph(ra, est_valor)],
        [Paragraph("<b>Turma</b>", est_label),        Paragraph(turma, est_valor),
         Paragraph("<b>Componente</b>", est_label),   Paragraph(componente, est_valor)],
        [Paragraph("<b>Tutor(a)</b>", est_label),     Paragraph(tutor, est_valor),
         Paragraph("<b>Eletiva</b>", est_label),      Paragraph(eletiva, est_valor)],
        [Paragraph("<b>Período</b>", est_label),      Paragraph(f"{data_ini_fmt} a {data_fim_fmt}", est_valor),
         Paragraph("<b>Coordenador(a)</b>", est_label), Paragraph(coordenador, est_valor)],
    ]

    tab_id = Table(dados_id, colWidths=[3.2 * cm, 7.3 * cm, 3.2 * cm, 5.3 * cm])
    tab_id.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), COR_CINZA_CLR),
        ("BOX",         (0, 0), (-1, -1), 1, COR_BORDA),
        ("INNERGRID",   (0, 0), (-1, -1), 0.5, COR_BORDA),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0),(-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elementos.append(tab_id)
    elementos.append(Spacer(1, 0.4 * cm))

    # Indicadores
    freq_cor = COR_SECUNDARIA if frequencia >= 75 else COR_AVISO if frequencia >= 60 else COR_ALERTA
    freq_txt = f"{frequencia:.1f}%"

    total_ocorr = len(df_ocorrencias_aluno) if not df_ocorrencias_aluno.empty else 0
    graves_count = 0
    if not df_ocorrencias_aluno.empty and "gravidade" in df_ocorrencias_aluno.columns:
        try:
            graves_count = int(df_ocorrencias_aluno["gravidade"].isin(["Grave", "Gravíssima"]).sum())
        except Exception:
            graves_count = 0

    alerta_prof = bool(registro.get("indicacao_grave_professor", False))

    dados_ind = [
        [
            Paragraph("<b>FREQUÊNCIA</b>", _estilo("L1", fontSize=7, textColor=COR_SUBTEXTO,
                                                    fontName="Helvetica-Bold", alignment=TA_CENTER)),
            Paragraph("<b>SITUAÇÃO GERAL</b>", _estilo("L2", fontSize=7, textColor=COR_SUBTEXTO,
                                                         fontName="Helvetica-Bold", alignment=TA_CENTER)),
            Paragraph("<b>OCORRÊNCIAS NO PERÍODO</b>", _estilo("L3", fontSize=7, textColor=COR_SUBTEXTO,
                                                                 fontName="Helvetica-Bold", alignment=TA_CENTER)),
            Paragraph("<b>ALERTA DO PROFESSOR</b>", _estilo("L4", fontSize=7, textColor=COR_SUBTEXTO,
                                                              fontName="Helvetica-Bold", alignment=TA_CENTER)),
        ],
        [
            Paragraph(freq_txt, _estilo("V1", fontSize=16, fontName="Helvetica-Bold",
                                         textColor=freq_cor, alignment=TA_CENTER)),
            Paragraph(situacao, _estilo("V2", fontSize=9, fontName="Helvetica-Bold",
                                         textColor=COR_TEXTO, alignment=TA_CENTER)),
            Paragraph(f"{total_ocorr} ({graves_count} graves)",
                      _estilo("V3", fontSize=11, fontName="Helvetica-Bold",
                               textColor=COR_ALERTA if graves_count else COR_TEXTO,
                               alignment=TA_CENTER)),
            Paragraph("⚠ SIM" if alerta_prof else "OK",
                      _estilo("V4", fontSize=11, fontName="Helvetica-Bold",
                               textColor=COR_ALERTA if alerta_prof else COR_SECUNDARIA,
                               alignment=TA_CENTER)),
        ],
    ]

    tab_ind = Table(dados_ind, colWidths=[4.5 * cm] * 4)
    tab_ind.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#eff6ff")),
        ("BACKGROUND",  (0, 1), (-1, 1), colors.white),
        ("BOX",         (0, 0), (-1, -1), 1, COR_BORDA),
        ("INNERGRID",   (0, 0), (-1, -1), 0.5, COR_BORDA),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0),(-1, -1), 6),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elementos.append(tab_ind)
    elementos.append(Spacer(1, 0.5 * cm))

    # Seções de texto
    def _secao(titulo: str, conteudo: str, cor_titulo=COR_PRIMARIA):
        if not conteudo or not str(conteudo).strip():
            return
        elementos.append(HRFlowable(width="100%", thickness=1, color=COR_BORDA, spaceAfter=4))
        elementos.append(Paragraph(titulo, _estilo(
            f"sec_{titulo[:8]}", base="Heading2",
            fontSize=9, textColor=cor_titulo, fontName="Helvetica-Bold",
            spaceAfter=3, spaceBefore=4, leading=12,
        )))
        for linha in str(conteudo).strip().splitlines():
            linha = linha.strip()
            if linha:
                elementos.append(Paragraph(linha.replace("\n", "<br/>"), est_corpo))
        elementos.append(Spacer(1, 0.15 * cm))

    _secao("📚 Desenvolvimento Acadêmico",
           registro.get("desenvolvimento_academico", ""))
    _secao("🧠 Observações Comportamentais e Socioemocionais",
           registro.get("observacoes_comportamentais", ""))
    _secao("🛠️ Estratégias e Encaminhamentos",
           registro.get("estrategias_adotadas", ""))
    _secao("🔎 Pontos de Atenção Complementares",
           registro.get("pontos_atencao", ""))
    _secao("📝 Escrita Corrida do Acompanhamento",
           registro.get("escrita_corrida_ultima", ""))
    _secao("📅 Histórico de Escritas Corridas",
           registro.get("escrita_corrida_historico", ""))

    if alerta_prof and str(registro.get("descricao_ponto_grave", "")).strip():
        _secao("⚠ Ponto Grave Sinalizado pelo Professor",
               registro.get("descricao_ponto_grave", ""),
               cor_titulo=COR_ALERTA)

    # Pontos automáticos
    pontos_auto = registro.get("pontos_atencao_automaticos", [])
    if isinstance(pontos_auto, list) and pontos_auto:
        elementos.append(HRFlowable(width="100%", thickness=1, color=COR_BORDA, spaceAfter=4))
        elementos.append(Paragraph(
            "🚨 Ocorrências Graves/Gravíssimas no Período",
            _estilo("sec_auto", base="Heading2", fontSize=9, textColor=COR_ALERTA,
                    fontName="Helvetica-Bold", spaceAfter=3, spaceBefore=4, leading=12),
        ))
        for item in pontos_auto:
            elementos.append(Paragraph(f"• {item}", est_corpo))
        elementos.append(Spacer(1, 0.15 * cm))

    # Histórico de ocorrências
    if not df_ocorrencias_aluno.empty:
        elementos.append(HRFlowable(width="100%", thickness=1, color=COR_BORDA, spaceAfter=4))
        elementos.append(Paragraph(
            "📋 Histórico de Ocorrências no Período",
            _estilo("sec_ocorr", base="Heading2", fontSize=9, textColor=COR_PRIMARIA,
                    fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=4, leading=12),
        ))

        cabecalho_ocorr = [
            Paragraph("<b>Data</b>", _estilo("th1", fontSize=8, fontName="Helvetica-Bold",
                                              textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Categoria</b>", _estilo("th2", fontSize=8, fontName="Helvetica-Bold",
                                                    textColor=colors.white)),
            Paragraph("<b>Gravidade</b>", _estilo("th3", fontSize=8, fontName="Helvetica-Bold",
                                                    textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("<b>Professor</b>", _estilo("th4", fontSize=8, fontName="Helvetica-Bold",
                                                    textColor=colors.white)),
        ]
        linhas_ocorr = [cabecalho_ocorr]

        df_sorted = df_ocorrencias_aluno.copy()
        if "data" in df_sorted.columns:
            df_sorted["_dt"] = pd.to_datetime(df_sorted["data"], format="%d/%m/%Y %H:%M", errors="coerce")
            df_sorted = df_sorted.sort_values("_dt", ascending=False).head(15)
        else:
            df_sorted = df_sorted.head(15)

        for _, row in df_sorted.iterrows():
            grav = str(row.get("gravidade", "")).strip()
            grav_cor = {
                "Gravíssima": COR_ALERTA,
                "Grave":      COR_AVISO,
                "Média":      colors.HexColor("#0891b2"),
                "Leve":       COR_SECUNDARIA,
            }.get(grav, COR_TEXTO)

            data_str = str(row.get("data", ""))
            if " " in data_str:
                data_str = data_str.split()[0]

            linhas_ocorr.append([
                Paragraph(data_str, _estilo(f"td_d{_}", fontSize=8, alignment=TA_CENTER)),
                Paragraph(str(row.get("categoria", ""))[:60], _estilo(f"td_c{_}", fontSize=8)),
                Paragraph(grav, _estilo(f"td_g{_}", fontSize=8, textColor=grav_cor,
                                         fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(str(row.get("professor", ""))[:30], _estilo(f"td_p{_}", fontSize=8)),
            ])

        tab_ocorr = Table(linhas_ocorr, colWidths=[2.8 * cm, 7.5 * cm, 2.5 * cm, 5.2 * cm],
                          repeatRows=1)
        tab_ocorr.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), COR_PRIMARIA),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_CINZA_CLR]),
            ("BOX",          (0, 0), (-1, -1), 1, COR_BORDA),
            ("INNERGRID",    (0, 0), (-1, -1), 0.3, COR_BORDA),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("LEFTPADDING",  (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elementos.append(tab_ocorr)
        if len(df_ocorrencias_aluno) > 15:
            elementos.append(Paragraph(
                f"* Exibindo as 15 mais recentes de {len(df_ocorrencias_aluno)} ocorrências no período.",
                _estilo("nota", fontSize=7, textColor=COR_SUBTEXTO),
            ))
        elementos.append(Spacer(1, 0.4 * cm))

    # Assinaturas e rodapé
    elementos.append(Spacer(1, 0.6 * cm))
    elementos.append(HRFlowable(width="100%", thickness=1, color=COR_BORDA, spaceAfter=6))

    dados_assinatura = [
        [
            Paragraph("_______________________________\nProfessor(a) Responsável\n" + editor,
                       _estilo("ass1", fontSize=8, alignment=TA_CENTER, leading=12)),
            Paragraph("_______________________________\nCoordenador(a) de Sala\n" + coordenador,
                       _estilo("ass2", fontSize=8, alignment=TA_CENTER, leading=12)),
            Paragraph("_______________________________\nDiretor(a) / Gestão\n ",
                       _estilo("ass3", fontSize=8, alignment=TA_CENTER, leading=12)),
        ]
    ]
    tab_ass = Table(dados_assinatura, colWidths=[6 * cm, 6 * cm, 6 * cm])
    tab_ass.setStyle(TableStyle([
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    elementos.append(tab_ass)
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(Paragraph(
        f"Documento gerado pelo Sistema Conviva 179 em {datetime.now().strftime('%d/%m/%Y às %H:%M')} — "
        f"E.E. ELIANE APARECIDA DANTAS DA SILVA PROFESSORA - PEI",
        est_rodape,
    ))

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
        "relatorio_feedback": None,
        
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
        "TUTORIA": None,
        "FONTE_TUTORIA": None,
        
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
df_tutoria_supabase = pd.DataFrame()

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

if SUPABASE_VALID:
    try:
        df_tutoria_supabase = _supabase_get_dataframe("tutoria?select=*", "carregar tutoria")
    except Exception:
        df_tutoria_supabase = pd.DataFrame()

if st.session_state.ELETIVAS is None:
    if SUPABASE_VALID:
        if not df_eletivas_supabase.empty:
            st.session_state.ELETIVAS = converter_eletivas_supabase_para_dict(df_eletivas_supabase)
        else:
            # Base oficial: Supabase (inicia vazio quando não há registros)
            st.session_state.ELETIVAS = {k: [] for k in ELETIVAS.keys()}
        st.session_state.FONTE_ELETIVAS = "supabase"
    else:
        st.session_state.ELETIVAS = {k: [] for k in ELETIVAS.keys()}
        st.session_state.FONTE_ELETIVAS = "indisponivel"
else:
    if SUPABASE_VALID:
        st.session_state.FONTE_ELETIVAS = "supabase"
    else:
        st.session_state.FONTE_ELETIVAS = "indisponivel"

ELETIVAS = st.session_state.ELETIVAS
FONTE_ELETIVAS = st.session_state.FONTE_ELETIVAS

TUTORIA_LOCAL = carregar_tutoria_local()

if st.session_state.TUTORIA is None:
    if TUTORIA_LOCAL:
        st.session_state.TUTORIA = TUTORIA_LOCAL
        st.session_state.FONTE_TUTORIA = "local"
    elif SUPABASE_VALID and not df_tutoria_supabase.empty:
        st.session_state.TUTORIA = converter_tutoria_supabase_para_dict(df_tutoria_supabase)
        st.session_state.FONTE_TUTORIA = "supabase"
    else:
        st.session_state.TUTORIA = normalizar_base_tutoria(TUTORIA_EXCEL.copy() if TUTORIA_EXCEL else {})
        st.session_state.FONTE_TUTORIA = "excel" if TUTORIA_EXCEL else "indisponivel"
else:
    st.session_state.TUTORIA = normalizar_base_tutoria(st.session_state.TUTORIA)
    if TUTORIA_LOCAL:
        st.session_state.FONTE_TUTORIA = "local"
    elif SUPABASE_VALID and not df_tutoria_supabase.empty:
        st.session_state.FONTE_TUTORIA = "supabase"
    elif TUTORIA_EXCEL:
        st.session_state.FONTE_TUTORIA = "excel"
    else:
        st.session_state.FONTE_TUTORIA = "indisponivel"

TUTORIA = normalizar_base_tutoria(st.session_state.TUTORIA)
st.session_state.TUTORIA = TUTORIA
FONTE_TUTORIA = st.session_state.FONTE_TUTORIA
ROTAS_MENU_SUPORTADAS = {
    normalizar_texto("🏠 Dashboard"),
    normalizar_texto("📝 Registrar Ocorrência"),
    normalizar_texto("🧾 Relatório dos Estudantes"),
    normalizar_texto("📋 Histórico de Ocorrências"),
    normalizar_texto("📄 Comunicado aos Pais"),
    normalizar_texto("👥 Lista de Alunos"),
    normalizar_texto("📥 Importar Alunos"),
    normalizar_texto("📋 Gerenciar Turmas"),
    normalizar_texto("👨‍🏫 Cadastrar Professores"),
    normalizar_texto("👤 Cadastrar Assinaturas"),
    normalizar_texto("🎨 Eletiva"),
    normalizar_texto("🫂 Tutoria"),
    normalizar_texto("📊 Gráficos e Indicadores"),
    normalizar_texto("🖨️ Imprimir PDF"),
    normalizar_texto("🏫 Mapa da Sala"),
    normalizar_texto("📅 Agendamento de Espaços"),
    normalizar_texto("👨‍👩‍👧 Portal do Responsável"),
    normalizar_texto("💾 Backups"),
}
PAGINAS_MENU_ATIVAS = {normalizar_texto(f"{item['icone']} {item['nome']}") for item in menu_items}
ROTAS_MENU_AUSENTES = sorted(PAGINAS_MENU_ATIVAS - ROTAS_MENU_SUPORTADAS)
menu_normalizado = normalizar_texto(menu)

if ROTAS_MENU_AUSENTES:
    st.sidebar.error("Algumas páginas do menu estão sem rota de exibição configurada.")
    st.sidebar.caption("Rotas ausentes: " + ", ".join(ROTAS_MENU_AUSENTES))
# ======================================================`r`n# BLOCO JS DE OVERRIDE REMOVIDO (VERSAO SIMPLES)`r`n# ======================================================
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
        <div class="school-header-inner">
            <div class="school-name">🏫 {ESCOLA_NOME}</div>
            <div class="school-subtitle">{ESCOLA_SUBTITULO}</div>
            <div class="school-info-chips">
                <span class="school-chip school-chip-address">📍 {ESCOLA_ENDERECO}</span>
                <span class="school-chip">📞 {ESCOLA_TELEFONE}</span>
                <span class="school-chip">✉️ {ESCOLA_EMAIL}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Boas-vindas ───────────────────────────────────────────
    hora_atual = datetime.now().hour
    saudacao = "🌅 Bom dia" if hora_atual < 12 else ("☀️ Boa tarde" if hora_atual < 18 else "🌙 Boa noite")
    st.markdown(f"""
    <div style="
        display: flex; align-items: center; gap: 1rem;
        background: linear-gradient(120deg, rgba(255,255,255,0.95), rgba(250,245,255,0.96));
        border-radius: 18px; padding: 1.25rem 1.5rem;
        border: 1.5px solid rgba(196,181,253,0.45); box-shadow: 0 6px 16px rgba(76,29,149,0.08);
        margin-bottom: 1.75rem;
    ">
        <div style="font-size: 2.35rem; line-height:1;">👋</div>
        <div>
            <div style="
                font-family: 'Nunito', sans-serif;
                font-size: 1.3rem; font-weight: 800;
                color: #1f1b3a; margin-bottom: 0.15rem;
            ">{saudacao}! Bem-vindo ao Sistema Conviva 179</div>
            <div style="color: #5b5679; font-size: 0.9rem;">
                Gerencie ocorrências, alunos e agendamentos de forma inteligente.
                &nbsp;·&nbsp; <b style="color: #7c3aed;">{datetime.now().strftime('%A, %d de %B de %Y')}</b>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Métricas Principais ───────────────────────────────────
    total_ocorrencias = len(df_ocorrencias) if not df_ocorrencias.empty else 0
    total_professores = len(df_professores) if not df_professores.empty else 0

    # Validação de status por RA (evita duplicidade e conta somente ativos reais)
    total_ativos = 0
    total_transferidos = 0
    total_transferidos_turno1 = 0
    total_remanejados = 0
    total_inativos = 0
    total_outros_status = 0
    total_duplicados_ra = 0
    status_brutos = {}
    turmas_ativas = 0
    if not df_alunos.empty:
        base = df_alunos.copy()
        if "situacao" not in base.columns:
            base["situacao"] = "Ativo"
        if "ra" not in base.columns:
            base["ra"] = ""
        base["ra_norm"] = base["ra"].astype(str).str.strip()

        # dedupe por RA: mantém registro mais recente quando houver created_at
        base_valid_ra = base[base["ra_norm"] != ""].copy()
        total_duplicados_ra = int(base_valid_ra.loc[base_valid_ra.duplicated("ra_norm", keep=False), "ra_norm"].nunique())
        if "created_at" in base_valid_ra.columns:
            base_valid_ra["created_at"] = pd.to_datetime(base_valid_ra["created_at"], errors="coerce")
            base_valid_ra = base_valid_ra.sort_values("created_at").drop_duplicates("ra_norm", keep="last")
        else:
            base_valid_ra = base_valid_ra.drop_duplicates("ra_norm", keep="last")

        # inclui também linhas sem RA (não deduplicáveis)
        base_sem_ra = base[base["ra_norm"] == ""].copy()
        base_status = pd.concat([base_valid_ra, base_sem_ra], ignore_index=True)

        for _, linha_status in base_status.iterrows():
            s = str(linha_status.get("situacao", "") or "").strip()
            status_brutos[s if s else "(vazio)"] = status_brutos.get(s if s else "(vazio)", 0) + 1
            s_norm = normalizar_texto(s)
            turma_status = str(linha_status.get("turma", "") or "").strip()
            if any(k in s_norm for k in ["TRANSFER", "BAIXA"]):
                total_transferidos += 1
                if classificar_turno_tutoria(turma_status) == "Turno 1":
                    total_transferidos_turno1 += 1
            elif any(k in s_norm for k in ["REMANEJ", "REALOC", "RELOC"]):
                total_remanejados += 1
            elif any(k in s_norm for k in ["INATIV", "DESLIG", "CANCEL", "EVADI", "ABANDON"]):
                total_inativos += 1
            elif "ATIVO" in s_norm:
                total_ativos += 1
            else:
                total_outros_status += 1

        if "turma" in base_status.columns:
            ativos_df = base_status[
                base_status["situacao"].astype(str).apply(lambda s: "ATIVO" in normalizar_texto(s))
            ]
            turmas_ativas = int(ativos_df["turma"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique())

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

    with st.expander("🔎 Verificação de Situação dos Estudantes", expanded=False):
        st.info("As métricas usam RA único. Transferidos, remanejados/realocados e inativos ficam fora do total ativo.")
        col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
        col_v1.metric("Ativos", total_ativos)
        col_v2.metric("Transferidos", total_transferidos)
        col_v3.metric("Remanej./Realoc.", total_remanejados)
        col_v4.metric("Inativos/Outros", total_inativos + total_outros_status)
        col_v5.metric("Transferidos - Turno 1", total_transferidos_turno1)
        if status_brutos:
            df_status = pd.DataFrame(
                [{"Situação Original": k, "Quantidade": v} for k, v in sorted(status_brutos.items(), key=lambda x: (-x[1], x[0]))]
            )
            st.dataframe(df_status, use_container_width=True, hide_index=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    cards_data = [
        (col1, "linear-gradient(135deg,#1d4ed8 0%,#2563eb 100%)", "✅", total_ativos, "Alunos Ativos", "RA único validado", "0"),
        (col2, "linear-gradient(135deg,#dc2626 0%,#ef4444 100%)", "⚠️", total_ocorrencias, "Ocorrências", f"{gravissimas} gravíssimas", "0.08s"),
        (col3, "linear-gradient(135deg,#0891b2 0%,#06b6d4 100%)", "👨‍🏫", total_professores, "Professores", "cadastrados", "0.16s"),
        (col4, "linear-gradient(135deg,#059669 0%,#10b981 100%)", "🏫", turmas_ativas, "Turmas Ativas", "com alunos ativos", "0.24s"),
        (col5, "linear-gradient(135deg,#7c3aed 0%,#8b5cf6 100%)", "🔁", total_transferidos_turno1, "Transferidos T1", "6º ao 9º + 3º A/B", "0.32s"),
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

    col1, col2, col3, col4, col5 = st.columns(5)
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
                    
                    st.subheader("Informacoes do Aluno")
                    st.write(f"Nome: {aluno['nome']}")
                    st.write(f"RA: {aluno['ra']}")
                    st.write(f"Turma: {aluno.get('turma', '')}")

                    ocorr_aluno = df_ocorrencias[df_ocorrencias['ra'].astype(str) == str(aluno['ra'])] if not df_ocorrencias.empty else pd.DataFrame()
                    if ocorr_aluno.empty:
                        st.info("Nenhuma ocorrencia registrada para este aluno.")
                    else:
                        st.write("Ocorrencias recentes:")
                        cols_show = [c for c in ["data", "categoria", "gravidade", "professor"] if c in ocorr_aluno.columns]
                        st.dataframe(ocorr_aluno[cols_show].head(20), use_container_width=True, hide_index=True)

# ======================================================
# PAGINA REGISTRAR OCORRENCIA
# ======================================================

elif "REGISTRAR OCORR" in normalizar_texto(menu):
    page_header("Registro de Ocorrência", "Cadastre ocorrências com Protocolo 179", "#dc2626")

    if df_alunos.empty:
        st.warning("Cadastre alunos antes de registrar ocorrencias.")
        st.stop()
    if df_professores.empty:
        st.warning("Cadastre ao menos um professor antes de registrar ocorrencias.")
        st.stop()

    tz_sp = pytz.timezone("America/Sao_Paulo")
    agora = datetime.now(tz_sp)

    c1, c2 = st.columns(2)
    with c1:
        data_fato = st.date_input("Data do fato", value=agora.date(), key="data_fato")
    with c2:
        hora_fato = st.time_input("Hora do fato", value=agora.time(), key="hora_fato")

    data_str = f"{data_fato.strftime('%d/%m/%Y')} {hora_fato.strftime('%H:%M')}"

    turmas_disponiveis = sorted(df_alunos["turma"].dropna().astype(str).unique().tolist()) if "turma" in df_alunos.columns else []
    turmas_sel = st.multiselect("Turma(s)", turmas_disponiveis, default=turmas_disponiveis[:1], key="turmas_sel")

    alunos_turma = df_alunos[df_alunos["turma"].astype(str).isin(turmas_sel)].copy() if turmas_sel else pd.DataFrame()
    if "situacao" in alunos_turma.columns:
        alunos_turma = alunos_turma[alunos_turma["situacao"].astype(str).str.strip().str.lower() == "ativo"]

    if alunos_turma.empty:
        st.info("Selecione ao menos uma turma com alunos ativos.")
        st.stop()

    alunos_turma["aluno_label"] = alunos_turma["nome"].astype(str) + " - " + alunos_turma["turma"].astype(str)
    labels_alunos = alunos_turma["aluno_label"].drop_duplicates().tolist()
    alunos_sel_labels = st.multiselect("Estudantes envolvidos", labels_alunos, key="alunos_multiplos")

    prof = st.selectbox("Professor", df_professores["nome"].dropna().astype(str).tolist(), key="professor_sel")

    resumo_ocorrencia = [
        ("Turmas selecionadas", len(turmas_sel), "#2563eb", ", ".join(turmas_sel[:3]) if turmas_sel else "Nenhuma turma"),
        ("Estudantes envolvidos", len(alunos_sel_labels), "#7c3aed", ", ".join(alunos_sel_labels[:2]) if alunos_sel_labels else "Nenhum estudante"),
        ("Professor", 1 if prof else 0, "#dc2626", prof or "Não selecionado")
    ]
    cols_resumo = st.columns(3)
    for coluna, (titulo, valor, cor, detalhe) in zip(cols_resumo, resumo_ocorrencia):
        with coluna:
            st.markdown(
                f"""
                <div style="
                    background:white;
                    border:1.5px solid {cor}26;
                    border-top:4px solid {cor};
                    border-radius:18px;
                    padding:1rem 1rem 0.9rem 1rem;
                    box-shadow:0 8px 20px rgba(15,23,42,0.06);
                    margin:0.25rem 0 0.75rem 0;
                    min-height:112px;
                ">
                    <div style="font-size:0.78rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:{cor};margin-bottom:0.45rem;">{titulo}</div>
                    <div style="font-family:'Nunito',sans-serif;font-size:1.7rem;font-weight:800;color:#1e293b;line-height:1;">{valor}</div>
                    <div style="font-size:0.88rem;color:#64748b;margin-top:0.55rem;line-height:1.35;">{html.escape(str(detalhe))}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.subheader("Infração (Protocolo 179)")
    busca = st.text_input("Buscar infração", placeholder="Ex: celular, bullying, atraso...", key="busca_infracao")

    if busca:
        grupos_filtrados = buscar_infracao_fuzzy(busca, PROTOCOLO_179)
        if grupos_filtrados:
            grupo = st.selectbox("Grupo", list(grupos_filtrados.keys()), key="grupo_infracao")
            infracoes = grupos_filtrados[grupo]
        else:
            st.warning("Nenhuma infração encontrada. Mostrando todas.")
            grupo = st.selectbox("Grupo", list(PROTOCOLO_179.keys()), key="grupo_infracao")
            infracoes = PROTOCOLO_179[grupo]
    else:
        grupo = st.selectbox("Grupo", list(PROTOCOLO_179.keys()), key="grupo_infracao")
        infracoes = PROTOCOLO_179[grupo]

    infracao_principal = st.selectbox("Infração principal", list(infracoes.keys()), key="infracao_principal")
    outras_infracoes = st.multiselect("Infrações adicionais", [i for i in infracoes.keys() if i != infracao_principal], key="infracoes_adicionais")
    infracoes_selecionadas = [infracao_principal] + [i for i in outras_infracoes if i != infracao_principal]

    dados_infracoes_sel = [infracoes[i] for i in infracoes_selecionadas]
    gravidade_sugerida = max(
        [normalizar_gravidade_protocolo(d.get("gravidade", "Leve")) for d in dados_infracoes_sel],
        key=lambda g: ORDEM_GRAVIDADE_PROTOCOLO.get(g, 1)
    )

    linhas_encam = []
    for d in dados_infracoes_sel:
        for linha in str(d.get("encaminhamento", "")).splitlines():
            ln = linha.strip()
            if ln and ln not in linhas_encam:
                linhas_encam.append(ln)
    encaminhamento_sugerido = "\n".join(linhas_encam)

    gravidade = gravidade_sugerida
    st.text_input("Gravidade", value=gravidade, key="gravidade_sel_auto", disabled=True)
    st.caption("A gravidade é definida automaticamente conforme o Protocolo 179.")
    encam = st.text_area("Encaminhamentos", value=encaminhamento_sugerido, height=120, key="encaminhamento")
    relato = st.text_area("Relato dos fatos", height=140, key="relato")
    categoria_consolidada = consolidar_categoria_ocorrencia(infracoes_selecionadas)

    feedback_ocorrencia = st.session_state.get("ocorrencia_feedback")
    if feedback_ocorrencia:
        tipo_feedback = feedback_ocorrencia.get("tipo", "info")
        msg_feedback = feedback_ocorrencia.get("msg", "")
        if tipo_feedback == "success":
            st.success(msg_feedback)
            st.toast(msg_feedback, icon="✅")
        elif tipo_feedback == "warning":
            st.warning(msg_feedback)
        elif tipo_feedback == "error":
            st.error(msg_feedback)
        else:
            st.info(msg_feedback)
        st.session_state["ocorrencia_feedback"] = None

    if st.button("Salvar Ocorrencia(s)", type="primary"):
        if not prof or not relato.strip() or not alunos_sel_labels:
            st.error("Preencha professor, estudantes e relato.")
        else:
            salvas = 0
            duplicadas = 0
            for lbl in alunos_sel_labels:
                reg = alunos_turma[alunos_turma["aluno_label"] == lbl]
                if reg.empty:
                    continue
                row = reg.iloc[0]
                aluno = str(row.get("nome", "")).strip()
                turma = str(row.get("turma", "")).strip()
                ra = str(row.get("ra", "")).strip()
                if verificar_ocorrencia_duplicada(ra, categoria_consolidada, data_str, df_ocorrencias):
                    duplicadas += 1
                    continue
                nova = {
                    "data": data_str,
                    "aluno": aluno,
                    "ra": ra,
                    "turma": turma,
                    "categoria": categoria_consolidada,
                    "gravidade": gravidade,
                    "relato": relato,
                    "encaminhamento": encam,
                    "professor": prof,
                }
                if salvar_ocorrencia(nova):
                    salvas += 1
            if salvas > 0:
                msg_sucesso = f"Ação concluída: {salvas} ocorrência(s) salva(s)."
                if duplicadas > 0:
                    msg_sucesso += f" {duplicadas} duplicada(s) ignorada(s)."
                st.session_state["ocorrencia_feedback"] = {"tipo": "success", "msg": msg_sucesso}
                carregar_ocorrencias.clear()
                st.rerun()
            elif duplicadas > 0:
                st.session_state["ocorrencia_feedback"] = {"tipo": "warning", "msg": f"{duplicadas} ocorrência(s) duplicada(s) ignorada(s)."}
                st.rerun()
            else:
                st.session_state["ocorrencia_feedback"] = {"tipo": "info", "msg": "Nenhuma ocorrência foi salva."}
                st.rerun()

# ======================================================
# P?GINA ?? HIST?RICO DE OCORR?NCIAS (COMPLETA)
# ======================================================

elif "HISTORICO DE OCORRENCIA" in normalizar_texto(menu):
    page_header("📋 Histórico de Ocorrências", "Consulte, edite e exclua registros de ocorrências", "#d97706")

    mensagem_exclusao = st.session_state.get("mensagem_exclusao")
    if mensagem_exclusao:
        st.success(mensagem_exclusao)
        st.session_state.mensagem_exclusao = None

    if df_ocorrencias.empty:
        st.info("📭 Nenhuma ocorrência registrada.")
        st.stop()
    col1, col2, col3 = st.columns(3)
    with col1:
        turmas_disp = ["Todas"] + sorted(df_ocorrencias["turma"].dropna().unique().tolist())
        filtro_turma = st.selectbox("Turma", turmas_disp)
    with col2:
        gravidades_disp = ["Todas"] + sorted(df_ocorrencias["gravidade"].dropna().unique().tolist())
        filtro_gravidade = st.selectbox("Gravidade", gravidades_disp)
    with col3:
        categorias_unicas = sorted(df_ocorrencias["categoria"].dropna().unique().tolist())
        filtro_categoria = st.selectbox("Categoria", ["Todas"] + categorias_unicas)

    col4, col5 = st.columns(2)
    with col4:
        if "professor" in df_ocorrencias.columns:
            professores_disp = ["Todos"] + sorted([
                p for p in df_ocorrencias["professor"].dropna().astype(str).str.strip().unique().tolist() if p
            ])
            filtro_professor = st.selectbox("Professor", professores_disp)
        else:
            filtro_professor = "Todos"
            st.selectbox("Professor", ["Todos"], disabled=True)
    with col5:
        data_parse = pd.to_datetime(df_ocorrencias["data"], format="%d/%m/%Y %H:%M", errors="coerce")
        if data_parse.notna().any():
            dt_min = data_parse.min().date()
            dt_max = data_parse.max().date()
        else:
            hoje = datetime.now().date()
            dt_min = hoje
            dt_max = hoje
        periodo = st.date_input("Per?odo", value=(dt_min, dt_max), min_value=dt_min, max_value=dt_max, key="hist_periodo")

    df_view = df_ocorrencias.copy()
    if filtro_turma != "Todas":
        df_view = df_view[df_view["turma"] == filtro_turma]
    if filtro_gravidade != "Todas":
        df_view = df_view[df_view["gravidade"] == filtro_gravidade]
    if filtro_categoria != "Todas":
        df_view = df_view[df_view["categoria"] == filtro_categoria]
    if filtro_professor != "Todos" and "professor" in df_view.columns:
        df_view = df_view[df_view["professor"].astype(str).str.strip() == filtro_professor]

    df_view["data_dt_filtro"] = pd.to_datetime(df_view["data"], format="%d/%m/%Y %H:%M", errors="coerce")
    if isinstance(periodo, tuple) and len(periodo) == 2:
        ini, fim = periodo
    else:
        ini = periodo
        fim = periodo
    df_view = df_view[
        (df_view["data_dt_filtro"].dt.date >= ini) &
        (df_view["data_dt_filtro"].dt.date <= fim)
    ]
    df_view = df_view.drop(columns=["data_dt_filtro"], errors="ignore")

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
                    show_toast("Senha incorreta para exclusão.", "error")
                else:
                    sucesso = excluir_ocorrencia(id_excluir)
                    if sucesso:
                        st.session_state.mensagem_exclusao = f"✅ Ocorrência {id_excluir} excluída com sucesso!"
                        show_toast(f"Ocorrência {id_excluir} excluída.", "success")
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
                    show_toast("Ocorrência atualizada com sucesso.", "success")
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
# PÁGINA 🧾 RELATÓRIO DOS ESTUDANTES
# ======================================================
elif "RELATORIO DOS ESTUDANTES" in normalizar_texto(menu):
    page_header("🧾 Relatório dos Estudantes",
                "Acompanhamentos por turma com professor tutor, eletiva e impressão em PDF",
                "#0f766e")
 
    feedback_relatorio = st.session_state.get("relatorio_feedback")
    if feedback_relatorio:
        tipo_feedback    = feedback_relatorio.get("tipo", "success")
        mensagem_feedback = feedback_relatorio.get("msg", "")
        if tipo_feedback == "success":
            st.success(mensagem_feedback)
        elif tipo_feedback == "warning":
            st.warning(mensagem_feedback)
        else:
            st.info(mensagem_feedback)
        st.session_state.relatorio_feedback = None
 
    if df_alunos.empty:
        st.info("📭 Cadastre ou importe estudantes antes de criar relatórios por turma.")
        st.stop()
 
    df_relatorios = carregar_relatorios_estudantes()
    relatorio_suporta_escrita_corrida = (
        not SUPABASE_VALID
        or "escrita_corrida_historico" in df_relatorios.columns
    )
    if not df_relatorios.empty and "pontos_atencao_automaticos" in df_relatorios.columns:
        def _normalizar_pontos_auto(valor):
            if isinstance(valor, list):
                return valor
            if valor in (None, "", float("nan")):
                return []
            if isinstance(valor, str):
                texto = valor.strip()
                if not texto:
                    return []
                try:
                    carregado = json.loads(texto)
                    return carregado if isinstance(carregado, list) else []
                except Exception:
                    return [texto]
            return []
        df_relatorios["pontos_atencao_automaticos"] = \
            df_relatorios["pontos_atencao_automaticos"].apply(_normalizar_pontos_auto)
 
    turmas_disponiveis = sorted([
        turma for turma in df_alunos["turma"].dropna().astype(str).str.strip().unique().tolist() if turma
    ])
    turma_sel = st.selectbox("🏫 Turma", turmas_disponiveis, key="relatorio_turma")
 
    alunos_turma = (
        df_alunos[df_alunos["turma"].astype(str).str.strip() == turma_sel]
        .copy()
        .sort_values("nome")
    )
    alunos_turma["aluno_label"] = alunos_turma.apply(
        lambda row: f"{str(row.get('nome', '')).strip()} • RA {str(row.get('ra', '')).strip()}",
        axis=1
    )
 
    relatorios_turma = df_relatorios.copy()
    if not relatorios_turma.empty and "turma" in relatorios_turma.columns:
        relatorios_turma = relatorios_turma[
            relatorios_turma["turma"].astype(str).str.strip() == turma_sel
        ].copy()
 
    def _valor_booleano_seguro(valor) -> bool:
        if isinstance(valor, bool):
            return valor
        return normalizar_texto(valor) in {"TRUE", "SIM", "YES", "1"}
 
    total_alertas = 0
    if not relatorios_turma.empty:
        if "indicacao_grave_professor" in relatorios_turma.columns:
            total_alertas = int(
                relatorios_turma["indicacao_grave_professor"].apply(_valor_booleano_seguro).sum()
            )
        if "pontos_atencao_automaticos" in relatorios_turma.columns:
            total_alertas += int(
                relatorios_turma["pontos_atencao_automaticos"]
                .apply(lambda itens: len(itens) > 0).sum()
            )
 
    col_metric_1, col_metric_2, col_metric_3 = st.columns(3)
    col_metric_1.metric("👥 Estudantes da turma", len(alunos_turma))
    col_metric_2.metric("🧾 Relatórios cadastrados", len(relatorios_turma))
    col_metric_3.metric("🚨 Sinalizações de atenção", total_alertas)
 
    professores_lista = []
    coordenadores_lista = []
    if not df_professores.empty and "nome" in df_professores.columns:
        professores_lista = sorted([
            nome for nome in df_professores["nome"].dropna().astype(str).str.strip().unique().tolist()
            if nome
        ])
        if "cargo" in df_professores.columns:
            coordenadores_lista = sorted([
                str(row.get("nome", "")).strip()
                for _, row in df_professores.iterrows()
                if "COORDEN" in normalizar_texto(row.get("cargo", ""))
                and str(row.get("nome", "")).strip()
            ])
 
    df_config_turmas = carregar_config_turmas()
    coordenador_auto_turma = ""
    if not df_config_turmas.empty and "turma" in df_config_turmas.columns:
        config_atual = df_config_turmas[
            df_config_turmas["turma"].astype(str).str.strip() == turma_sel
        ]
        if not config_atual.empty:
            coordenador_auto_turma = str(config_atual.iloc[0].get("coordenador_sala", "")).strip()
 
    modo_relatorio = "Novo relatório"
    if not relatorios_turma.empty:
        modo_relatorio = st.radio(
            "Modo",
            ["Novo relatório", "Editar relatório existente"],
            horizontal=True,
            key="relatorio_modo"
        )
 
    registro_relatorio = {}
    if modo_relatorio == "Editar relatório existente" and not relatorios_turma.empty:
        opcoes_relatorios = []
        mapa_relatorios = {}
        for _, row in relatorios_turma.sort_values(
            ["data_fim", "aluno"], ascending=[False, True]
        ).iterrows():
            data_ini_txt = str(row.get("data_inicio", "")).strip()
            data_fim_txt = str(row.get("data_fim", "")).strip()
            aluno_txt    = str(row.get("aluno", "")).strip()
            autor_txt    = str(row.get("ultima_edicao_por", row.get("professor_autor", ""))).strip()
            label = f"#{row.get('id')} • {aluno_txt} • {data_ini_txt} a {data_fim_txt}"
            if autor_txt:
                label += f" • {autor_txt}"
            opcoes_relatorios.append(label)
            mapa_relatorios[label] = row.to_dict()
        escolha_relatorio = st.selectbox(
            "Selecione o relatório", opcoes_relatorios, key="relatorio_existente_sel"
        )
        registro_relatorio = mapa_relatorios.get(escolha_relatorio, {})
 
    aluno_padrao = ""
    if registro_relatorio:
        aluno_padrao = f"{str(registro_relatorio.get('aluno', '')).strip()} • RA {str(registro_relatorio.get('ra', '')).strip()}"
    elif not alunos_turma.empty:
        aluno_padrao = alunos_turma.iloc[0]["aluno_label"]
 
    opcoes_alunos   = alunos_turma["aluno_label"].tolist()
    indice_aluno    = opcoes_alunos.index(aluno_padrao) if aluno_padrao in opcoes_alunos else 0
    aluno_label_sel = st.selectbox(
        "🎓 Estudante", opcoes_alunos, index=indice_aluno, key="relatorio_aluno_sel"
    )
    aluno_info  = alunos_turma[alunos_turma["aluno_label"] == aluno_label_sel].iloc[0]
    aluno_nome  = str(aluno_info.get("nome", "")).strip()
    aluno_ra    = str(aluno_info.get("ra", "")).strip()
 
    professor_tutor_auto = obter_professor_tutor_do_aluno(
        aluno_nome, turma_sel, aluno_ra, TUTORIA
    )
    eletiva_auto = obter_eletiva_do_aluno(
        aluno_nome, turma_sel, aluno_ra, ELETIVAS
    )
 
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        if professor_tutor_auto:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#ecfeff,#ccfbf1);border:1.5px solid #5eead4;
                        border-left:5px solid #0f766e;border-radius:14px;padding:.75rem 1rem;margin:.35rem 0;">
                <div style="font-size:.72rem;font-weight:800;color:#0f766e;letter-spacing:.08em;
                            text-transform:uppercase;margin-bottom:.2rem;">Professor(a) Tutor(a)</div>
                <div style="font-size:.97rem;font-weight:700;color:#134e4a;">🫂 {professor_tutor_auto}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#f8fafc;border:1.5px dashed #cbd5e1;border-radius:14px;
                        padding:.75rem 1rem;margin:.35rem 0;">
                <div style="font-size:.72rem;font-weight:800;color:#64748b;letter-spacing:.08em;
                            text-transform:uppercase;margin-bottom:.2rem;">Professor(a) Tutor(a)</div>
                <div style="font-size:.88rem;color:#94a3b8;">Não localizado na base de tutoria</div>
            </div>
            """, unsafe_allow_html=True)
 
    with col_info2:
        if eletiva_auto:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#faf5ff,#ede9fe);border:1.5px solid #c4b5fd;
                        border-left:5px solid #7c3aed;border-radius:14px;padding:.75rem 1rem;margin:.35rem 0;">
                <div style="font-size:.72rem;font-weight:800;color:#7c3aed;letter-spacing:.08em;
                            text-transform:uppercase;margin-bottom:.2rem;">Eletiva — Professor(a)</div>
                <div style="font-size:.97rem;font-weight:700;color:#4c1d95;">🎨 {eletiva_auto}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#f8fafc;border:1.5px dashed #cbd5e1;border-radius:14px;
                        padding:.75rem 1rem;margin:.35rem 0;">
                <div style="font-size:.72rem;font-weight:800;color:#64748b;letter-spacing:.08em;
                            text-transform:uppercase;margin-bottom:.2rem;">Eletiva — Professor(a)</div>
                <div style="font-size:.88rem;color:#94a3b8;">Não localizado na base de eletivas</div>
            </div>
            """, unsafe_allow_html=True)
 
    def _parse_data_relatorio(valor, padrao):
        try:
            data_convertida = pd.to_datetime(valor, errors="coerce")
            if pd.isna(data_convertida):
                return padrao
            return data_convertida.date()
        except Exception:
            return padrao
 
    def _normalizar_estado_date_input(chave: str, padrao):
        if chave not in st.session_state:
            return
        try:
            valor_normalizado = _parse_data_relatorio(st.session_state.get(chave), padrao)
            st.session_state[chave] = valor_normalizado
        except Exception:
            st.session_state[chave] = padrao
 
    hoje              = datetime.now().date()
    data_inicio_padrao = _parse_data_relatorio(
        registro_relatorio.get("data_inicio"), hoje - timedelta(days=30)
    )
    data_fim_padrao = _parse_data_relatorio(registro_relatorio.get("data_fim"), hoje)
    if data_fim_padrao < data_inicio_padrao:
        data_fim_padrao = data_inicio_padrao
 
    _normalizar_estado_date_input("relatorio_data_inicio", data_inicio_padrao)
    _normalizar_estado_date_input("relatorio_data_fim",    data_fim_padrao)
 
    professor_autor_padrao = str(registro_relatorio.get("professor_autor", "")).strip()
    coordenador_padrao     = coordenador_auto_turma or str(registro_relatorio.get("coordenador_sala", "")).strip()
 
    opcoes_professores = professores_lista + (["Digitar manualmente"] if professores_lista else [])
    idx_autor = (
        opcoes_professores.index(professor_autor_padrao)
        if professor_autor_padrao in opcoes_professores
        else (len(opcoes_professores) - 1 if opcoes_professores else 0)
    )
 
    col_form_1, col_form_2 = st.columns(2)
    with col_form_1:
        editor_sel = st.selectbox(
            "👨‍🏫 Professor que está editando",
            opcoes_professores if opcoes_professores else ["Digitar manualmente"],
            index=idx_autor,
            key="relatorio_editor_sel"
        )
        if editor_sel == "Digitar manualmente" or not professores_lista:
            editor_manual = st.text_input(
                "Nome do professor editor", value=professor_autor_padrao,
                key="relatorio_editor_manual"
            )
        else:
            editor_manual = ""
        data_inicio = st.date_input("📅 Data inicial", value=data_inicio_padrao,
                                     key="relatorio_data_inicio")
        frequencia = st.number_input(
            "📊 Frequência (%)", min_value=0.0, max_value=100.0,
            value=float(registro_relatorio.get("frequencia_percentual", 100) or 100),
            step=1.0, key="relatorio_frequencia"
        )
    with col_form_2:
        st.text_input("🧭 Coordenador(a) da sala", value=coordenador_padrao,
                      disabled=True, key="relatorio_coord_auto")
        if not coordenador_padrao:
            st.caption("Cadastre o coordenador desta turma em '📋 Gerenciar Turmas'.")
        else:
            st.caption("Preenchido automaticamente pela turma selecionada.")
        componente_curricular = st.text_input(
            "📘 Componente curricular / área",
            value=str(registro_relatorio.get("componente_curricular", "")).strip(),
            placeholder="Ex: Língua Portuguesa, Matemática, acompanhamento geral",
            key="relatorio_componente"
        )
        data_fim = st.date_input("📅 Data final", value=data_fim_padrao,
                                  min_value=data_inicio, key="relatorio_data_fim")
        situacao_geral = st.selectbox(
            "🧩 Situação geral",
            ["Em acompanhamento", "Evoluindo bem", "Atenção", "Atenção imediata", "Necessita intervenção"],
            index=["Em acompanhamento", "Evoluindo bem", "Atenção", "Atenção imediata",
                   "Necessita intervenção"].index(
                str(registro_relatorio.get("situacao_geral", "Em acompanhamento")).strip()
                if str(registro_relatorio.get("situacao_geral", "Em acompanhamento")).strip()
                in ["Em acompanhamento", "Evoluindo bem", "Atenção", "Atenção imediata",
                    "Necessita intervenção"]
                else "Em acompanhamento"
            ),
            key="relatorio_situacao"
        )
 
    professor_editor = (
        editor_manual.strip()
        if editor_sel == "Digitar manualmente" or not professores_lista
        else editor_sel
    )
    coordenador_sala = coordenador_padrao.strip()
 
    pontos_automaticos = gerar_pontos_atencao_automaticos(
        df_ocorrencias, turma_sel, aluno_ra, aluno_nome, data_inicio, data_fim
    )
    if pontos_automaticos:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#fff7ed,#fffbeb);border:1.5px solid #fdba74;
                    border-left:5px solid #ea580c;border-radius:16px;padding:1rem 1.25rem;margin:1rem 0;">
            <div style="font-weight:800;color:#9a3412;margin-bottom:.35rem;">
                🚨 Pontos de atenção sugeridos automaticamente
            </div>
            <div style="color:#9a3412;font-size:.86rem;">
                Ocorrências graves ou gravíssimas encontradas no período.
            </div>
        </div>
        """, unsafe_allow_html=True)
        for item in pontos_automaticos:
            st.markdown(f"- {item}")
    else:
        st.info("Nenhuma ocorrência grave/gravíssima localizada no período.")
 
    indicacao_grave = st.checkbox(
        "⚠️ Sinalizar um ponto grave adicional neste relatório",
        value=bool(registro_relatorio.get("indicacao_grave_professor", False)),
        key="relatorio_indicacao_grave"
    )
    descricao_ponto_grave = st.text_area(
        "Descrição do ponto grave",
        value=str(registro_relatorio.get("descricao_ponto_grave", "")).strip(),
        height=90,
        placeholder="Explique o fato grave, o impacto e a urgência do acompanhamento.",
        key="relatorio_ponto_grave"
    )
 
    desenvolvimento_academico = st.text_area(
        "📚 Desenvolvimento acadêmico",
        value=str(registro_relatorio.get("desenvolvimento_academico", "")).strip(),
        height=120,
        placeholder="Descreva avanços, dificuldades e evidências de aprendizagem.",
        key="relatorio_desenvolvimento"
    )
    observacoes_comportamentais = st.text_area(
        "🧠 Observações comportamentais e socioemocionais",
        value=str(registro_relatorio.get("observacoes_comportamentais", "")).strip(),
        height=120,
        placeholder="Registre postura em sala, convivência, autorregulação e participação.",
        key="relatorio_comportamental"
    )
    estrategias_adotadas = st.text_area(
        "🛠️ Estratégias e encaminhamentos",
        value=str(registro_relatorio.get("estrategias_adotadas", "")).strip(),
        height=120,
        placeholder="Ações do professor, combinados, contatos com família, próximos passos.",
        key="relatorio_estrategias"
    )
    pontos_atencao_manuais = st.text_area(
        "🔎 Pontos de atenção complementares",
        value=str(registro_relatorio.get("pontos_atencao", "")).strip(),
        height=120,
        placeholder="Liste pontos que merecem monitoramento contínuo.",
        key="relatorio_pontos_manuais"
    )

    # ======================================================
    # 🤖 IA CONVIVA PEDAGÓGICA ONLINE — DENTRO DO RELATÓRIO
    # ======================================================
    with st.expander("🤖 IA Conviva Pedagógica Online", expanded=False):
        render_ia_conviva_relatorio({
            "aluno": aluno_nome,
            "ra": aluno_ra,
            "turma": turma_sel,
            "professor_editor": professor_editor,
            "coordenador_sala": coordenador_sala,
            "componente_curricular": componente_curricular,
            "situacao_geral": situacao_geral,
            "frequencia": frequencia,
        })

    st.markdown("---")
    st.markdown("""
    <div style="display:flex;align-items:center;gap:.5rem;margin:.25rem 0 .75rem 0;
                padding-bottom:.5rem;border-bottom:2px solid #e2e8f0;position:relative;">
        <div style="position:absolute;bottom:-2px;left:0;width:45px;height:2px;
                    background:linear-gradient(90deg,#7c3aed,transparent);border-radius:4px;"></div>
        <span>📝</span>
        <h3 style="margin:0;font-family:'Nunito',sans-serif;font-size:1rem;color:#0f172a;">
            Escrita corrida do acompanhamento
        </h3>
    </div>
    """, unsafe_allow_html=True)

    chave_escrita_base = gerar_chave_segura(f"{turma_sel}_{aluno_ra}_{registro_relatorio.get('id', 'novo')}")
    chave_escrita_atual = f"relatorio_escrita_corrida_atual_{chave_escrita_base}"
    chave_escrita_historico = f"relatorio_escrita_corrida_historico_{chave_escrita_base}"
    if chave_escrita_atual not in st.session_state:
        st.session_state[chave_escrita_atual] = str(registro_relatorio.get("escrita_corrida_ultima", "")).strip()
    if chave_escrita_historico not in st.session_state:
        st.session_state[chave_escrita_historico] = str(registro_relatorio.get("escrita_corrida_historico", "")).strip()

    if st.session_state.get("relatorio_escrita_corrida_atual") and not st.session_state.get(chave_escrita_atual):
        st.session_state[chave_escrita_atual] = st.session_state.pop("relatorio_escrita_corrida_atual")

    col_ec1, col_ec2 = st.columns([1, 1])
    with col_ec1:
        gerar_escrita = st.button(
            "✨ Gerar escrita corrida dos blocos",
            use_container_width=True,
            key="btn_gerar_escrita_corrida"
        )
    with col_ec2:
        adicionar_escrita = st.button(
            "➕ Adicionar ao histórico com data",
            use_container_width=True,
            key="btn_adicionar_escrita_corrida"
        )

    if gerar_escrita:
        textos_para_escrita = {
            "Desenvolvimento acadêmico": st.session_state.get("relatorio_desenvolvimento", ""),
            "Observações comportamentais": st.session_state.get("relatorio_comportamental", ""),
            "Estratégias e encaminhamentos": st.session_state.get("relatorio_estrategias", ""),
            "Pontos de atenção": st.session_state.get("relatorio_pontos_manuais", ""),
            "Ponto grave": st.session_state.get("relatorio_ponto_grave", ""),
        }
        base_escrita = montar_escrita_corrida_relatorio(
            {
                "aluno": aluno_nome,
                "ra": aluno_ra,
                "turma": turma_sel,
                "professor_editor": professor_editor,
                "situacao_geral": situacao_geral,
                "frequencia": frequencia,
            },
            textos_para_escrita
        )
        if not base_escrita.strip():
            st.warning("Preencha ao menos um bloco do relatório para gerar a escrita corrida.")
        else:
            with st.spinner("Gerando escrita corrida do relatório..."):
                st.session_state[chave_escrita_atual] = chamar_ia_conviva_online(
                    texto=base_escrita,
                    tarefa="Gerar escrita corrida do relatório",
                    contexto=(
                        f"Estudante: {aluno_nome}\nRA: {aluno_ra}\nTurma: {turma_sel}\n"
                        f"Professor editor: {professor_editor}\nSituação geral: {situacao_geral}\n"
                        f"Frequência: {frequencia}%"
                    )
                )

    if adicionar_escrita:
        st.session_state[chave_escrita_historico] = adicionar_entrada_historico_escrita_corrida(
            st.session_state.get(chave_escrita_historico, ""),
            professor_editor,
            st.session_state.get(chave_escrita_atual, "")
        )
        st.success("Escrita adicionada ao histórico com data e professor.")

    escrita_corrida_atual = st.text_area(
        "Escrita corrida atual",
        height=180,
        key=chave_escrita_atual,
        placeholder="Gere pela IA ou escreva aqui um relato corrido do acompanhamento."
    )
    escrita_corrida_historico = st.text_area(
        "Histórico de escritas corridas",
        height=220,
        key=chave_escrita_historico,
        placeholder="Cada entrada será adicionada abaixo da anterior, com data e professor."
    )
    if not relatorio_suporta_escrita_corrida:
        st.caption(
            "A escrita corrida fica disponível na tela. Para salvar esse histórico no Supabase, "
            "atualize a tabela `relatorios_estudantes` com as novas colunas do arquivo SQL."
        )
 
    col_salvar, col_excluir = st.columns([2, 1])
    with col_salvar:
        if st.button("💾 Salvar relatório", type="primary",
                     use_container_width=True, key="relatorio_salvar_btn"):
            if not professor_editor:
                st.error("Informe o professor que está registrando a edição.")
            elif not coordenador_sala:
                st.error("Cadastre o coordenador desta turma em '📋 Gerenciar Turmas'.")
            elif indicacao_grave and not descricao_ponto_grave.strip():
                st.error("Descreva o ponto grave sinalizado pelo professor.")
            elif data_fim < data_inicio:
                st.error("A data final não pode ser anterior à data inicial.")
            else:
                payload_relatorio = {
                    "turma":                    turma_sel,
                    "ra":                       aluno_ra,
                    "aluno":                    aluno_nome,
                    "data_inicio":              str(data_inicio),
                    "data_fim":                 str(data_fim),
                    "professor_autor":          str(registro_relatorio.get("professor_autor", professor_editor)).strip() or professor_editor,
                    "professor_responsavel_sala": "",
                    "coordenador_sala":         coordenador_sala,
                    "componente_curricular":    componente_curricular,
                    "situacao_geral":           situacao_geral,
                    "frequencia_percentual":    frequencia,
                    "desenvolvimento_academico": desenvolvimento_academico,
                    "observacoes_comportamentais": observacoes_comportamentais,
                    "estrategias_adotadas":     estrategias_adotadas,
                    "pontos_atencao":           pontos_atencao_manuais,
                    "pontos_atencao_automaticos": pontos_automaticos,
                    "indicacao_grave_professor": indicacao_grave,
                    "descricao_ponto_grave":    descricao_ponto_grave.strip(),
                    "ultima_edicao_por":        professor_editor,
                    "professor_tutor":          professor_tutor_auto,
                    "eletiva":                  eletiva_auto,
                    "created_at":               registro_relatorio.get("created_at", datetime.now().isoformat()),
                }
                payload_relatorio["escrita_corrida_ultima"] = escrita_corrida_atual.strip()
                payload_relatorio["escrita_corrida_historico"] = escrita_corrida_historico.strip()
                if registro_relatorio and registro_relatorio.get("id"):
                    sucesso, base = atualizar_relatorio_estudante(
                        registro_relatorio.get("id"), payload_relatorio
                    )
                    if sucesso:
                        st.session_state.relatorio_feedback = {
                            "tipo": "success",
                            "msg": f"Relatório de {aluno_nome} atualizado com sucesso ({base})."
                        }
                        st.rerun()
                else:
                    sucesso, base = salvar_relatorio_estudante(payload_relatorio)
                    if sucesso:
                        st.session_state.relatorio_feedback = {
                            "tipo": "success",
                            "msg": f"Relatório de {aluno_nome} criado com sucesso ({base})."
                        }
                        st.rerun()
    with col_excluir:
        if registro_relatorio and registro_relatorio.get("id"):
            if st.button("🗑️ Excluir relatório",
                         use_container_width=True, key="relatorio_excluir_btn"):
                sucesso, base = excluir_relatorio_estudante(registro_relatorio.get("id"))
                if sucesso:
                    st.session_state.relatorio_feedback = {
                        "tipo": "warning",
                        "msg": f"Relatório #{registro_relatorio.get('id')} excluído ({base})."
                    }
                    st.rerun()
 
    st.markdown("---")
    st.markdown("""
    <div style="display:flex;align-items:center;gap:.5rem;margin:.25rem 0 .75rem 0;
                padding-bottom:.5rem;border-bottom:2px solid #e2e8f0;position:relative;">
        <div style="position:absolute;bottom:-2px;left:0;width:45px;height:2px;
                    background:linear-gradient(90deg,#0f766e,transparent);border-radius:4px;"></div>
        <span>🖨️</span>
        <h3 style="margin:0;font-family:'Nunito',sans-serif;font-size:1rem;color:#0f172a;">
            Imprimir Relatório em PDF
        </h3>
    </div>
    """, unsafe_allow_html=True)
 
    if registro_relatorio and registro_relatorio.get("id"):
        payload_pdf = dict(registro_relatorio)
        payload_pdf["professor_tutor"] = str(registro_relatorio.get("professor_tutor", "") or professor_tutor_auto).strip()
        payload_pdf["eletiva"]         = str(registro_relatorio.get("eletiva", "") or eletiva_auto).strip()
        payload_pdf["escrita_corrida_ultima"] = escrita_corrida_atual.strip()
        payload_pdf["escrita_corrida_historico"] = escrita_corrida_historico.strip()
 
        df_ocorr_pdf = pd.DataFrame()
        if not df_ocorrencias.empty:
            df_tmp = df_ocorrencias.copy()
            df_tmp["_dt"] = pd.to_datetime(df_tmp.get("data", ""), format="%d/%m/%Y %H:%M", errors="coerce")
            ini_ts = pd.Timestamp(str(registro_relatorio.get("data_inicio", data_inicio)))
            fim_ts = pd.Timestamp(str(registro_relatorio.get("data_fim", data_fim)))
            mask = (
                (df_tmp.get("ra", pd.Series(dtype=str)).astype(str).str.strip() == aluno_ra) &
                (df_tmp["_dt"].between(ini_ts, fim_ts + pd.Timedelta(days=1), inclusive="both"))
            )
            df_ocorr_pdf = df_tmp[mask].drop(columns=["_dt"], errors="ignore")
 
        if st.button("🖨️ Gerar PDF deste Relatório", type="primary",
                     use_container_width=True, key="btn_imprimir_relatorio"):
            try:
                pdf_buffer = gerar_pdf_relatorio_estudante(payload_pdf, df_ocorr_pdf)
                nome_arquivo = (
                    f"Relatorio_{aluno_ra}_{aluno_nome.replace(' ', '_')}"
                    f"_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                )
                st.download_button(
                    "📥 Baixar PDF do Relatório",
                    data=pdf_buffer,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_relatorio_pdf"
                )
                st.success("✅ PDF gerado com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao gerar PDF: {e}")
    else:
        st.info(
            "Salve o relatório para habilitar a impressão, "
            "ou use o botão abaixo para gerar PDF com os dados do formulário atual."
        )
        if st.button("🖨️ Gerar PDF (dados atuais)", use_container_width=True,
                     key="btn_imprimir_relatorio_novo"):
            payload_novo = {
                "turma":                      turma_sel,
                "ra":                         aluno_ra,
                "aluno":                      aluno_nome,
                "data_inicio":                str(data_inicio),
                "data_fim":                   str(data_fim),
                "professor_autor":            professor_editor,
                "coordenador_sala":           coordenador_sala,
                "componente_curricular":      componente_curricular,
                "situacao_geral":             situacao_geral,
                "frequencia_percentual":      frequencia,
                "desenvolvimento_academico":  desenvolvimento_academico,
                "observacoes_comportamentais": observacoes_comportamentais,
                "estrategias_adotadas":       estrategias_adotadas,
                "pontos_atencao":             pontos_atencao_manuais,
                "pontos_atencao_automaticos": pontos_automaticos,
                "indicacao_grave_professor":  indicacao_grave,
                "descricao_ponto_grave":      descricao_ponto_grave.strip(),
                "ultima_edicao_por":          professor_editor,
                "professor_tutor":            professor_tutor_auto,
                "eletiva":                    eletiva_auto,
                "escrita_corrida_ultima":     escrita_corrida_atual.strip(),
                "escrita_corrida_historico":  escrita_corrida_historico.strip(),
            }
            df_ocorr_novo = pd.DataFrame()
            if not df_ocorrencias.empty:
                df_tmp2 = df_ocorrencias.copy()
                df_tmp2["_dt"] = pd.to_datetime(
                    df_tmp2.get("data", ""), format="%d/%m/%Y %H:%M", errors="coerce"
                )
                ini_ts = pd.Timestamp(data_inicio)
                fim_ts = pd.Timestamp(data_fim)
                mask = (
                    (df_tmp2.get("ra", pd.Series(dtype=str)).astype(str).str.strip() == aluno_ra) &
                    (df_tmp2["_dt"].between(ini_ts, fim_ts + pd.Timedelta(days=1), inclusive="both"))
                )
                df_ocorr_novo = df_tmp2[mask].drop(columns=["_dt"], errors="ignore")
            try:
                pdf_buffer = gerar_pdf_relatorio_estudante(payload_novo, df_ocorr_novo)
                nome_arquivo = (
                    f"Relatorio_{aluno_ra}_{aluno_nome.replace(' ', '_')}"
                    f"_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                )
                st.download_button(
                    "📥 Baixar PDF",
                    data=pdf_buffer,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_relatorio_pdf_novo"
                )
                st.success("✅ PDF gerado!")
            except Exception as e:
                st.error(f"❌ Erro ao gerar PDF: {e}")
 
    st.markdown("---")
    st.markdown("""
    <div style="display:flex;align-items:center;gap:.5rem;margin:.25rem 0 .75rem 0;
                padding-bottom:.5rem;border-bottom:2px solid #e2e8f0;position:relative;">
        <div style="position:absolute;bottom:-2px;left:0;width:45px;height:2px;
                    background:linear-gradient(90deg,#0f766e,transparent);border-radius:4px;"></div>
        <span>📚</span>
        <h3 style="margin:0;font-family:'Nunito',sans-serif;font-size:1rem;color:#0f172a;">
            Relatórios da turma
        </h3>
    </div>
    """, unsafe_allow_html=True)
 
    if relatorios_turma.empty:
        st.info("Nenhum relatório cadastrado para esta turma ainda.")
    else:
        df_lista = relatorios_turma.copy()
        df_lista["alerta"] = df_lista.apply(
            lambda row: "Sim"
            if _valor_booleano_seguro(row.get("indicacao_grave_professor", False))
            or len(row.get("pontos_atencao_automaticos", [])) > 0
            else "Não",
            axis=1
        )
        if "updated_at" in df_lista.columns:
            df_lista["updated_at"] = pd.to_datetime(
                df_lista["updated_at"], errors="coerce"
            ).dt.strftime("%d/%m/%Y %H:%M")
 
        def _buscar_tutor(row):
            return str(row.get("professor_tutor", "")).strip() or obter_professor_tutor_do_aluno(
                str(row.get("aluno", "")), str(row.get("turma", "")), str(row.get("ra", "")), TUTORIA
            )
        def _buscar_eletiva(row):
            return str(row.get("eletiva", "")).strip() or obter_eletiva_do_aluno(
                str(row.get("aluno", "")), str(row.get("turma", "")), str(row.get("ra", "")), ELETIVAS
            )
        df_lista["Tutor(a)"]  = df_lista.apply(_buscar_tutor, axis=1)
        df_lista["Eletiva"]   = df_lista.apply(_buscar_eletiva, axis=1)
 
        colunas_relatorio = [
            coluna for coluna in [
                "id", "aluno", "ra", "data_inicio", "data_fim", "situacao_geral",
                "Tutor(a)", "Eletiva", "coordenador_sala",
                "ultima_edicao_por", "updated_at", "alerta"
            ] if coluna in df_lista.columns
        ]
        st.dataframe(
            df_lista[colunas_relatorio].sort_values(["data_fim", "aluno"], ascending=[False, True]),
            use_container_width=True, hide_index=True
        )
 
        csv_relatorios = df_lista.copy()
        if "pontos_atencao_automaticos" in csv_relatorios.columns:
            csv_relatorios["pontos_atencao_automaticos"] = csv_relatorios[
                "pontos_atencao_automaticos"
            ].apply(lambda itens: " | ".join(itens) if isinstance(itens, list) else str(itens))
        st.download_button(
            "📥 Exportar relatórios da turma em CSV",
            data=csv_relatorios.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"relatorios_estudantes_{gerar_chave_segura(turma_sel).lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
 
        st.markdown("---")
        st.subheader("📦 Imprimir Todos os Relatórios da Turma (ZIP)")
        if st.button("📦 Gerar ZIP com PDFs da Turma", use_container_width=True,
                     key="btn_zip_relatorios_turma"):
            zip_buffer = BytesIO()
            gerados = 0
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for _, row in relatorios_turma.iterrows():
                    payload_lote = row.to_dict()
                    payload_lote["professor_tutor"] = (
                        str(payload_lote.get("professor_tutor", "")).strip()
                        or obter_professor_tutor_do_aluno(
                            str(payload_lote.get("aluno", "")),
                            str(payload_lote.get("turma", "")),
                            str(payload_lote.get("ra", "")),
                            TUTORIA,
                        )
                    )
                    payload_lote["eletiva"] = (
                        str(payload_lote.get("eletiva", "")).strip()
                        or obter_eletiva_do_aluno(
                            str(payload_lote.get("aluno", "")),
                            str(payload_lote.get("turma", "")),
                            str(payload_lote.get("ra", "")),
                            ELETIVAS,
                        )
                    )
                    df_ocorr_lote = pd.DataFrame()
                    if not df_ocorrencias.empty:
                        df_tmp3 = df_ocorrencias.copy()
                        df_tmp3["_dt"] = pd.to_datetime(
                            df_tmp3.get("data", ""), format="%d/%m/%Y %H:%M", errors="coerce"
                        )
                        ra_lote  = str(payload_lote.get("ra", "")).strip()
                        ini_lote = pd.Timestamp(str(payload_lote.get("data_inicio", ""))) \
                            if payload_lote.get("data_inicio") else pd.Timestamp("1900-01-01")
                        fim_lote = pd.Timestamp(str(payload_lote.get("data_fim", ""))) \
                            if payload_lote.get("data_fim") else pd.Timestamp("2100-12-31")
                        mask_l = (
                            (df_tmp3.get("ra", pd.Series(dtype=str)).astype(str).str.strip() == ra_lote) &
                            (df_tmp3["_dt"].between(ini_lote, fim_lote + pd.Timedelta(days=1), inclusive="both"))
                        )
                        df_ocorr_lote = df_tmp3[mask_l].drop(columns=["_dt"], errors="ignore")
                    try:
                        pdf_lote = gerar_pdf_relatorio_estudante(payload_lote, df_ocorr_lote)
                        nome_pdf = (
                            f"Relatorio_{str(payload_lote.get('ra', '')).strip()}"
                            f"_{str(payload_lote.get('aluno', '')).replace(' ', '_')}.pdf"
                        )
                        zf.writestr(nome_pdf, pdf_lote.getvalue())
                        gerados += 1
                    except Exception:
                        pass
            if gerados:
                zip_buffer.seek(0)
                st.download_button(
                    "📥 Baixar ZIP com todos os PDFs",
                    data=zip_buffer,
                    file_name=f"Relatorios_{gerar_chave_segura(turma_sel)}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="download_zip_relatorios"
                )
                st.success(f"✅ {gerados} PDF(s) gerado(s)!")
            else:
                st.warning("Nenhum PDF foi gerado.")
 
    st.caption(
        "Os relatórios usam o Supabase quando a tabela `relatorios_estudantes` estiver criada. "
        "Fallback local em `data/relatorios_estudantes_local.json`."
    )

# ======================================================
# PÁGINA 📥 IMPORTAR ALUNOS
# ======================================================

elif "IMPORTAR ALUNOS" in normalizar_texto(menu):
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
            # =========================================================
            # IMPORTAÇÃO SEDUC — LEITURA PADRÃO AUTOMÁTICA
            # =========================================================
            # O CSV da SEDUC costuma vir com linhas vazias antes do cabeçalho:
            # ;;; 
            # ;;;
            # Nome do Aluno;RA;Dig. RA;Situação do Aluno
            # Por isso, a leitura é feita sem cabeçalho e o sistema localiza
            # automaticamente a linha onde estão Nome do Aluno, RA e Situação.

            arquivo_upload.seek(0)
            df_raw = pd.read_csv(
                arquivo_upload,
                sep=";",
                encoding="utf-8-sig",
                dtype=str,
                header=None,
                keep_default_na=False
            )

            # Remove linhas/colunas totalmente vazias.
            df_raw = df_raw.replace(r"^\s*$", "", regex=True)
            df_raw = df_raw.loc[~df_raw.apply(lambda linha: all(str(v).strip() == "" for v in linha), axis=1)]
            df_raw = df_raw.loc[:, ~df_raw.apply(lambda col: all(str(v).strip() == "" for v in col), axis=0)]
            df_raw = df_raw.reset_index(drop=True)

            def _normalizar_coluna_importacao(valor: str) -> str:
                texto = normalizar_texto(str(valor or ""))
                texto = texto.replace(".", " ").replace("_", " ").replace("-", " ")
                return " ".join(texto.split())

            def _linha_parece_cabecalho_seduc(linha) -> bool:
                valores = [_normalizar_coluna_importacao(v) for v in linha.tolist()]
                tem_nome = any(("NOME" in v and "ALUNO" in v) or v == "NOME" for v in valores)
                tem_ra = any((v == "RA" or v.endswith(" RA") or " RA " in f" {v} ") and "DIG" not in v for v in valores)
                return tem_nome and tem_ra

            header_idx = None
            for idx_linha, linha in df_raw.head(12).iterrows():
                if _linha_parece_cabecalho_seduc(linha):
                    header_idx = idx_linha
                    break

            if header_idx is not None:
                novas_colunas = []
                usados = {}
                for idx_col, valor in enumerate(df_raw.iloc[header_idx].tolist()):
                    nome_coluna = str(valor or "").strip()
                    if not nome_coluna:
                        nome_coluna = f"Coluna {idx_col + 1}"
                    if nome_coluna in usados:
                        usados[nome_coluna] += 1
                        nome_coluna = f"{nome_coluna} {usados[nome_coluna]}"
                    else:
                        usados[nome_coluna] = 1
                    novas_colunas.append(nome_coluna)

                df_import = df_raw.iloc[header_idx + 1:].copy()
                df_import.columns = novas_colunas
            else:
                # Fallback para CSVs que já venham com cabeçalho correto na primeira linha.
                arquivo_upload.seek(0)
                df_import = pd.read_csv(
                    arquivo_upload,
                    sep=";",
                    encoding="utf-8-sig",
                    dtype=str,
                    keep_default_na=False
                )

            # Limpeza final dos dados.
            df_import = df_import.replace(r"^\s*$", "", regex=True)
            df_import = df_import.loc[~df_import.apply(lambda linha: all(str(v).strip() == "" for v in linha), axis=1)]
            df_import = df_import.reset_index(drop=True)

            # Remove eventual repetição do cabeçalho dentro do corpo.
            if len(df_import) > 0:
                primeira_coluna = df_import.columns[0]
                df_import = df_import[
                    df_import[primeira_coluna].apply(lambda v: "NOME DO ALUNO" not in normalizar_texto(v))
                ].reset_index(drop=True)

            colunas = df_import.columns.tolist()

            def _detectar_coluna_ra(colunas_df: list[str]) -> str | None:
                for col in colunas_df:
                    col_norm = _normalizar_coluna_importacao(col)
                    if "DIG" in col_norm:
                        continue
                    if col_norm == "RA" or col_norm.endswith(" RA") or " RA " in f" {col_norm} ":
                        return col

                # Fallback por conteúdo: RA costuma ser numérico e ter 7+ dígitos.
                for col in colunas_df:
                    col_norm = _normalizar_coluna_importacao(col)
                    if "DIG" in col_norm:
                        continue
                    amostra = df_import[col].dropna().astype(str).head(12)
                    qtd_ra = 0
                    for val in amostra:
                        digitos = "".join(c for c in str(val) if c.isdigit())
                        if len(digitos) >= 7:
                            qtd_ra += 1
                    if qtd_ra >= 3:
                        return col
                return None

            def _detectar_coluna_nome(colunas_df: list[str]) -> str | None:
                for col in colunas_df:
                    col_norm = _normalizar_coluna_importacao(col)
                    if ("NOME" in col_norm and "ALUNO" in col_norm) or col_norm == "NOME":
                        return col

                # Fallback por conteúdo: nomes costumam ter letras e espaços.
                melhor_col = None
                melhor_pontos = -1
                for col in colunas_df:
                    pontos = 0
                    for val in df_import[col].dropna().astype(str).head(12):
                        texto_val = str(val).strip()
                        if len(texto_val) >= 6 and any(ch.isalpha() for ch in texto_val) and not texto_val.isdigit():
                            pontos += 1
                    if pontos > melhor_pontos:
                        melhor_pontos = pontos
                        melhor_col = col
                return melhor_col if melhor_pontos >= 3 else None

            def _detectar_coluna_situacao(colunas_df: list[str]) -> str | None:
                for col in colunas_df:
                    col_norm = _normalizar_coluna_importacao(col)
                    if "SITUACAO" in col_norm or "STATUS" in col_norm:
                        return col
                return None

            col_ra = _detectar_coluna_ra(colunas)
            col_nome = _detectar_coluna_nome(colunas)
            col_situacao = _detectar_coluna_situacao(colunas)

            st.success(f"✅ Arquivo lido no padrão SEDUC! {len(df_import)} estudantes encontrados.")
            st.write("### 👀 Pré-visualização dos dados:")
            st.dataframe(df_import.head(10), use_container_width=True)

            # Mostra a identificação de colunas de forma discreta.
            with st.expander("🔍 Colunas identificadas automaticamente", expanded=False):
                st.write(f"**Nome:** {col_nome or 'não identificado'}")
                st.write(f"**RA:** {col_ra or 'não identificado'}")
                st.write(f"**Situação:** {col_situacao or 'não encontrada — será usado Ativo'}")

            # Só pede seleção manual se realmente não conseguir identificar.
            if col_ra is None or col_nome is None:
                st.warning("⚠️ Não foi possível identificar automaticamente todas as colunas. Selecione manualmente:")
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
            turma_alunos_padronizada = formatar_turma_eletiva(turma_alunos)

            if turma_alunos_padronizada:
                turmas_existentes = df_alunos_existente["turma"].unique().tolist() if not df_alunos_existente.empty and "turma" in df_alunos_existente.columns else []
                if turma_alunos_padronizada in turmas_existentes:
                    st.warning(f"⚠️ A turma **{turma_alunos_padronizada}** já existe. Estudantes com o mesmo RA serão atualizados.")

            if st.button("🚀 IMPORTAR ALUNOS", type="primary", use_container_width=True):
                if not turma_alunos_padronizada:
                    st.error("❌ Digite o nome da turma.")
                elif col_ra is None or col_nome is None:
                    st.error("❌ É necessário identificar as colunas de RA e Nome.")
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
                            ra_valor = row.get(col_ra, "")
                            ra_str = "".join(c for c in str(ra_valor or "") if c.isdigit())

                            if not ra_str or len(ra_str) < 5:
                                erros += 1
                                continue

                            nome_valor = row.get(col_nome, "")
                            nome_str = str(nome_valor or "").strip()

                            if not nome_str or normalizar_texto(nome_str) in ("NAN", "NONE", "NOME DO ALUNO"):
                                erros += 1
                                continue

                            sit_str = "Ativo"
                            if col_situacao:
                                sit_valor = row.get(col_situacao, "")
                                if str(sit_valor or "").strip():
                                    sit_original = str(sit_valor).strip()
                                    sit_lower = normalizar_texto(sit_original)

                                    if "TRANSFER" in sit_lower:
                                        sit_str = "Transferido"
                                    elif "REMANEJ" in sit_lower:
                                        sit_str = "Remanejado"
                                    elif "BAIX" in sit_lower:
                                        sit_str = "Baixado"
                                    elif "INATIV" in sit_lower:
                                        sit_str = "Inativo"
                                    elif "ATIV" in sit_lower:
                                        sit_str = "Ativo"
                                    else:
                                        sit_str = sit_original

                            aluno = {
                                "ra": ra_str,
                                "nome": nome_str,
                                "turma": turma_alunos_padronizada,
                                "situacao": sit_str
                            }

                            existe = (
                                df_alunos_existente[df_alunos_existente["ra"].astype(str) == ra_str]
                                if not df_alunos_existente.empty and "ra" in df_alunos_existente.columns
                                else pd.DataFrame()
                            )

                            if not existe.empty:
                                if atualizar_aluno(ra_str, aluno):
                                    atualizados += 1
                                else:
                                    erros += 1
                            else:
                                if salvar_aluno(aluno):
                                    novos += 1
                                else:
                                    erros += 1

                        except Exception as e:
                            logger.error(f"Erro ao importar aluno da linha {i}: {e}")
                            erros += 1

                        if total:
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
        <h3 style="margin:0;font-family:'Nunito',sans-serif;font-size:1rem;color:#0f172a;">Turmas cadastradas no sistema</h3>
    </div>
    """, unsafe_allow_html=True)
    if not df_alunos.empty:
        resumo = df_alunos.groupby("turma").size().reset_index(name="Total")
        resumo.columns = ["Turma", "Total de Alunos"]
        st.dataframe(resumo.sort_values("Turma"), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma turma cadastrada ainda.")

# ======================================================
# PÁGINA 📋 GERENCIAR TURMAS
# ======================================================

elif "GERENCIAR TURMAS" in normalizar_texto(menu):
    page_header("📋 Gerenciar Turmas", "Visualize, edite e exclua turmas cadastradas", "#059669")

    if df_alunos.empty:
        st.info("📭 Nenhuma turma cadastrada. Use '📥 Importar Alunos' para começar.")
    else:
        df_config_turmas = carregar_config_turmas()
        mapa_coord_turma = {}
        if not df_config_turmas.empty and "turma" in df_config_turmas.columns:
            for _, cfg in df_config_turmas.iterrows():
                turma_cfg = str(cfg.get("turma", "")).strip()
                if turma_cfg:
                    mapa_coord_turma[turma_cfg] = str(cfg.get("coordenador_sala", "")).strip()
        coordenadores_disponiveis = []
        if not df_professores.empty and "cargo" in df_professores.columns:
            coordenadores_disponiveis = sorted([
                str(row.get("nome", "")).strip()
                for _, row in df_professores.iterrows()
                if "COORDEN" in normalizar_texto(row.get("cargo", ""))
                and str(row.get("nome", "")).strip()
            ])

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
                            <div style="font-size:0.76rem;color:#0f766e;font-weight:600;margin-top:0.15rem;">Coordenador(a): {mapa_coord_turma.get(row['turma'], 'Não vinculado')}</div>
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

        if st.session_state.get("turma_selecionada"):
            turma = st.session_state.turma_selecionada
            st.markdown("---")
            st.subheader(f"👥 Alunos da Turma {turma}")
            alunos_turma = df_alunos[df_alunos["turma"] == turma]
            st.dataframe(alunos_turma[["ra", "nome", "situacao"]], use_container_width=True, hide_index=True)
            if st.button("❌ Fechar Visualização"):
                st.session_state.turma_selecionada = None
                st.rerun()

        if st.session_state.get("turma_para_editar"):
            turma_antiga = st.session_state.turma_para_editar
            st.markdown("---")
            st.subheader(f"✏️ Editar Turma: {turma_antiga}")
            novo_nome = st.text_input("Novo nome da turma", value=turma_antiga)
            coord_atual = mapa_coord_turma.get(turma_antiga, "")
            opcoes_coord_turma = coordenadores_disponiveis + (["Digitar manualmente"] if coordenadores_disponiveis else ["Digitar manualmente"])
            idx_coord_turma = opcoes_coord_turma.index(coord_atual) if coord_atual in opcoes_coord_turma else len(opcoes_coord_turma) - 1
            coord_sel_turma = st.selectbox("Coordenador(a) da sala", opcoes_coord_turma, index=idx_coord_turma, key="coord_turma_edit")
            coord_manual_turma = ""
            if coord_sel_turma == "Digitar manualmente":
                coord_manual_turma = st.text_input("Nome do coordenador(a)", value=coord_atual if coord_atual not in coordenadores_disponiveis else "", key="coord_turma_manual")
            coordenador_turma_final = coord_manual_turma.strip() if coord_sel_turma == "Digitar manualmente" else coord_sel_turma
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar Alterações", type="primary"):
                    if not novo_nome.strip():
                        st.error("❌ Nome da turma não pode ser vazio.")
                    elif not coordenador_turma_final:
                        st.error("❌ Informe o coordenador(a) da sala.")
                    elif novo_nome == turma_antiga:
                        sucesso_cfg, _ = salvar_config_turma(turma_antiga, coordenador_turma_final)
                        if sucesso_cfg:
                            st.success("✅ Coordenador(a) da turma atualizado com sucesso!")
                            st.session_state.turma_para_editar = None
                            st.rerun()
                    else:
                        sucesso = editar_nome_turma(turma_antiga, novo_nome)
                        if sucesso:
                            renomear_config_turma(turma_antiga, novo_nome)
                            salvar_config_turma(novo_nome, coordenador_turma_final)
                            st.success(f"✅ Turma renomeada para {novo_nome}!")
                            st.session_state.turma_para_editar = None
                            st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    st.session_state.turma_para_editar = None
                    st.rerun()

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
                        if "ra" in col_lower and "dig" not in col_lower:
                            col_ra = col
                        if "nome" in col_lower:
                            col_nome = col
                        if "situa" in col_lower:
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
                        # Segurança: primeiro prepara e valida os registros.
                        # A turma antiga só é apagada depois que houver alunos válidos para importar.
                        registros_importacao = []
                        for _, row in df_import.iterrows():
                            ra = "".join(c for c in str(row[col_ra]) if c.isdigit())
                            nome = str(row[col_nome]).strip()
                            if not ra or not nome or nome.lower() in {"nan", "none", "nome do aluno"}:
                                continue

                            situacao = "Ativo"
                            if col_situacao:
                                sit_valor = str(row[col_situacao]).strip()
                                sit_norm = normalizar_texto(sit_valor)
                                if "TRANSFER" in sit_norm:
                                    situacao = "Transferido"
                                elif "REMANEJ" in sit_norm or "REALOC" in sit_norm or "RELOC" in sit_norm:
                                    situacao = "Remanejamento"
                                elif "ATIVO" in sit_norm:
                                    situacao = "Ativo"
                                elif sit_valor and sit_valor.lower() not in {"nan", "none", "null"}:
                                    situacao = sit_valor

                            registros_importacao.append({"ra": ra, "nome": nome, "turma": turma, "situacao": situacao})

                        if not registros_importacao:
                            st.error("❌ Nenhum aluno válido foi identificado no arquivo. A turma atual NÃO foi apagada.")
                            st.stop()

                        excluir_ok = excluir_alunos_por_turma(turma)
                        if not excluir_ok:
                            st.error("❌ Não foi possível limpar a turma atual. A substituição foi cancelada para evitar perda de dados.")
                            st.stop()

                        inseridos = 0
                        for aluno in registros_importacao:
                            if salvar_aluno(aluno):
                                inseridos += 1

                        st.success(f"✅ Turma substituída com segurança! {inseridos} aluno(s) importado(s).")
                        st.session_state.turma_para_substituir = None
                        carregar_alunos.clear()
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao processar o arquivo: {e}")

            if st.button("❌ Cancelar Substituição"):
                st.session_state.turma_para_substituir = None
                st.rerun()

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
                        excluir_config_turma(turma)
                        st.success(f"✅ Turma {turma} excluída com sucesso!")
                        st.session_state.turma_para_deletar = None
                        carregar_alunos.clear()
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar", key="cancelar_exclusao_turma"):
                    st.session_state.turma_para_deletar = None
                    st.rerun()

# ======================================================
# PÁGINA 👥 LISTA DE ALUNOS
# ======================================================

elif "LISTA DE ALUNOS" in normalizar_texto(menu):
    page_header("👥 Gerenciar Alunos", "Cadastro, edição e exclusão de estudantes", "#2563eb")

    tab1, tab2, tab3 = st.tabs(["📋 Listar Alunos", "➕ Cadastrar Aluno", "✏️ Editar/Excluir"])

    with tab1:
        if df_alunos.empty:
            st.info("📭 Nenhum aluno cadastrado. Use a aba '➕ Cadastrar Aluno' ou '📥 Importar Alunos'.")
        else:
            df_alunos_lista = df_alunos.copy()
            col1, col2, col3 = st.columns(3)

            with col1:
                turmas_disp = ["Todas"] + sorted(df_alunos_lista["turma"].dropna().unique().tolist())
                filtro_turma = st.selectbox("🏫 Filtrar por Turma", turmas_disp, key="filtro_turma_lista")

            with col2:
                if "situacao" in df_alunos_lista.columns:
                    df_alunos_lista["situacao_norm"] = df_alunos_lista["situacao"].astype(str).str.strip().str.title()
                    situacoes_unicas = sorted(df_alunos_lista["situacao_norm"].dropna().unique().tolist())
                else:
                    df_alunos_lista["situacao_norm"] = "Ativo"
                    situacoes_unicas = ["Ativo"]

                situacoes_disp = ["Ativos", "Todos"] + situacoes_unicas
                filtro_situacao = st.selectbox("📊 Situação", situacoes_disp, index=0, key="filtro_situacao_lista")

            with col3:
                busca_nome = st.text_input("🔍 Buscar por Nome ou RA", placeholder="Digite nome ou RA", key="busca_lista")

            df_view = df_alunos_lista.copy()
            if filtro_turma != "Todas":
                df_view = df_view[df_view["turma"] == filtro_turma]

            if filtro_situacao == "Ativos":
                df_view = df_view[df_view["situacao_norm"] == "Ativo"]
            elif filtro_situacao != "Todos":
                df_view = df_view[df_view["situacao_norm"] == filtro_situacao]

            if busca_nome:
                df_view = df_view[
                    df_view["nome"].astype(str).str.contains(busca_nome, case=False, na=False) |
                    df_view["ra"].astype(str).str.contains(busca_nome, na=False)
                ]

            total_geral = len(df_alunos_lista)
            total_ativos = len(df_alunos_lista[df_alunos_lista["situacao_norm"] == "Ativo"])

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

                csv = df_display.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 Exportar Lista (CSV)",
                    data=csv,
                    file_name=f"alunos_{filtro_situacao.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="btn_exportar_csv_lista",
                )

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
                            "ra": ra.strip(),
                            "nome": nome.strip(),
                            "turma": turma.strip(),
                            "situacao": situacao,
                            "responsavel": responsavel.strip() if responsavel else None,
                        }

                        if salvar_aluno(aluno):
                            st.success(f"✅ Aluno {nome} cadastrado com sucesso!")
                            carregar_alunos.clear()
                            st.rerun()
                        else:
                            st.error("❌ Erro ao salvar aluno.")

    with tab3:
        if df_alunos.empty:
            st.info("📭 Nenhum aluno cadastrado.")
        else:
            st.subheader("✏️ Editar ou Excluir Aluno")
            df_busca = df_alunos.copy()
            if "situacao" in df_busca.columns:
                df_busca["situacao_norm"] = df_busca["situacao"].astype(str).str.strip().str.title()
                ativos = df_busca[df_busca["situacao_norm"] == "Ativo"]
                if not ativos.empty:
                    df_busca = ativos

            df_busca = df_busca.sort_values(["turma", "nome"])
            opcoes_alunos = []
            for _, row in df_busca.iterrows():
                sit = row.get("situacao", "Ativo")
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
                            index=["Ativo", "Transferido", "Inativo", "Remanejado"].index(sit_atual),
                        )
                    with col2:
                        novo_responsavel = st.text_input("Responsável", value=str(aluno_info.get("responsavel", "")))

                    st.info(f"**RA:** {aluno_info.get('ra')} (não pode ser alterado)")

                    if st.form_submit_button("💾 Salvar Alterações", type="primary"):
                        dados_atualizados = {
                            "nome": novo_nome.strip(),
                            "turma": nova_turma.strip(),
                            "situacao": nova_situacao,
                            "responsavel": novo_responsavel.strip() if novo_responsavel else None,
                        }

                        if atualizar_aluno(str(aluno_info["ra"]), dados_atualizados):
                            st.success("✅ Aluno atualizado com sucesso!")
                            carregar_alunos.clear()
                            st.rerun()
                        else:
                            st.error("❌ Erro ao atualizar aluno.")

                st.markdown("---")
                st.subheader("🗑️ Excluir Aluno")
                st.warning(f"⚠️ Esta ação é irreversível! O aluno **{aluno_info['nome']}** (RA: {aluno_info['ra']}) será removido permanentemente.")

                if st.button("🗑️ Excluir Aluno", type="secondary", key="btn_excluir_aluno_tab3"):
                    st.session_state.confirmar_exclusao_aluno = aluno_info["ra"]
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

    col1, col2, col3, col4, col5 = st.columns(5)
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
        aluno_podio = top_alunos.index[0]
        ocorrencias_podio = int(top_alunos.iloc[0])
        turma_podio = ""
        if "turma" in df_filtro.columns:
            turmas_podio = df_filtro[df_filtro["aluno"] == aluno_podio]["turma"].dropna().astype(str).str.strip()
            turma_podio = turmas_podio.mode().iloc[0] if not turmas_podio.empty else ""
        gravidade_podio = ""
        if "gravidade" in df_filtro.columns:
            gravidades_podio = df_filtro[df_filtro["aluno"] == aluno_podio]["gravidade"].dropna().astype(str).str.strip()
            gravidade_podio = gravidades_podio.mode().iloc[0] if not gravidades_podio.empty else ""

        detalhe_podio = []
        if turma_podio:
            detalhe_podio.append(f"Turma: {turma_podio}")
        if gravidade_podio:
            detalhe_podio.append(f"Gravidade mais comum: {gravidade_podio}")
        detalhe_podio_txt = " • ".join(detalhe_podio) if detalhe_podio else "Maior volume de ocorrências no filtro atual"

        st.markdown(
            f"""
            <div style="
                position:relative;
                overflow:hidden;
                margin:0.35rem 0 1rem 0;
                padding:1.25rem 1.3rem;
                border-radius:28px;
                background:
                    radial-gradient(circle at 90% 18%, rgba(245,158,11,0.16), transparent 26%),
                    linear-gradient(135deg, #fff8e6 0%, #fffdf7 48%, #f8fafc 100%);
                border:1px solid rgba(245,158,11,0.28);
                box-shadow:0 18px 36px rgba(15,23,42,0.08);
            ">
                <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:1rem;">
                    <div>
                        <div style="font-size:0.76rem; font-weight:900; letter-spacing:0.12em; text-transform:uppercase; color:#b45309; margin-bottom:0.35rem;">Estudante do Pódio</div>
                        <div style="font-family:'Nunito',sans-serif; font-size:1.45rem; font-weight:900; color:#1f2937; line-height:1.15;">{html.escape(str(aluno_podio))}</div>
                        <div style="font-size:0.92rem; color:#6b7280; margin-top:0.45rem;">{html.escape(detalhe_podio_txt)}</div>
                    </div>
                    <div style="text-align:right; min-width:112px;">
                        <div style="
                            width:58px; height:58px; margin-left:auto; margin-bottom:0.45rem;
                            border-radius:18px; display:flex; align-items:center; justify-content:center;
                            background:linear-gradient(135deg,#f59e0b,#fbbf24); color:white;
                            font-size:1.55rem; box-shadow:0 12px 24px rgba(245,158,11,0.28);
                        ">🏆</div>
                        <div style="font-family:'Nunito',sans-serif; font-size:2rem; font-weight:900; color:#b45309; line-height:1;">{ocorrencias_podio}</div>
                        <div style="font-size:0.82rem; font-weight:700; color:#92400e;">ocorrência(s)</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
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
        st.subheader("âž• Novo Professor")
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
        st.success("✅ Base oficial ativa: Supabase.")
    else:
        st.error("❌ Supabase indisponível no momento. Verifique conexão/credenciais.")

    if SUPABASE_VALID:
        col_sync1, col_sync2 = st.columns([1, 1])
        with col_sync1:
            if st.button("🔄 Recarregar Eletivas do Supabase", key="reload_eletivas_supabase", use_container_width=True):
                try:
                    df_refresh = _supabase_get_dataframe("eletivas?select=*", "recarregar eletivas")
                    st.session_state.ELETIVAS = converter_eletivas_supabase_para_dict(df_refresh) if not df_refresh.empty else {k: [] for k in ELETIVAS.keys()}
                    st.session_state.FONTE_ELETIVAS = "supabase"
                    st.success("✅ Eletivas recarregadas do Supabase.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao recarregar: {e}")
        with col_sync2:
            if st.button("💾 Forçar Salvar Estado Atual no Supabase", key="persistir_eletivas_supabase", use_container_width=True):
                try:
                    registros = converter_eletivas_para_registros(ELETIVAS, origem="sessao_manual")
                    _supabase_request("DELETE", "eletivas?id=not.is.null")
                    if registros:
                        _supabase_request("POST", "eletivas", json=registros)
                    st.session_state.FONTE_ELETIVAS = "supabase"
                    st.success("✅ Estado atual persistido no Supabase.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao persistir: {e}")

    st.markdown("---")
    st.subheader("📊 Professoras de Eletiva")

    if not ELETIVAS:
        st.info("📭 Nenhuma professora cadastrada para eletivas.")
        st.stop()

    dados_professoras = []
    for prof, alunos in ELETIVAS.items():
        series = ", ".join(sorted({formatar_turma_eletiva(a.get("serie", "")) for a in alunos if a.get("serie")}))
        dados_professoras.append({
            "Professora": prof,
            "Total de Alunos": len(alunos),
            "Turmas": series
        })
    
    df_professoras = pd.DataFrame(dados_professoras)
    st.dataframe(df_professoras, use_container_width=True, hide_index=True)

    st.markdown("---")
    professora_sel = st.selectbox("Selecione a Professora", sorted(ELETIVAS.keys()))
    alunos_raw = ELETIVAS.get(professora_sel, [])

    st.markdown("---")
    st.subheader("➕ Inserir Estudantes na Eletiva")
    st.caption("Você pode buscar no cadastro, digitar manualmente, colar lista ou enviar arquivo.")

    def _normalizar_linha_lista(linha: str, serie_padrao: str = ""):
        bruto = str(linha or "").strip().lstrip("•-").strip()
        if not bruto:
            return None
        nome = bruto
        serie = str(serie_padrao or "").strip()

        # Formato escolar colado com TAB:
        # Turma | RA | Nome | Situação | ...
        if "\t" in bruto:
            partes_tab = [p.strip() for p in bruto.split("\t")]
            if len(partes_tab) >= 3:
                possivel_serie = partes_tab[0]
                possivel_nome = partes_tab[2]
                if possivel_nome:
                    nome = possivel_nome
                if possivel_serie:
                    serie = possivel_serie
                return {"nome": nome, "serie": formatar_turma_eletiva(serie)}

        for sep in [";", "\t", "|", " - ", " – ", ","]:
            if sep in bruto:
                partes = [p.strip() for p in bruto.split(sep, 1)]
                if partes and partes[0]:
                    nome = partes[0]
                    if len(partes) > 1 and partes[1]:
                        serie = partes[1]
                    break
        return {"nome": nome, "serie": formatar_turma_eletiva(serie)}

    def _adicionar_estudantes_eletiva(novos_estudantes: list, origem: str):
        existentes = ELETIVAS.get(professora_sel, [])
        chaves_existentes = {
            f"{normalizar_texto(item.get('nome', ''))}|{normalizar_texto(item.get('serie', ''))}"
            for item in existentes
        }

        inseridos = []
        for item in novos_estudantes:
            nome = str(item.get("nome", "")).strip()
            serie = formatar_turma_eletiva(str(item.get("serie", "")).strip())
            if not nome:
                continue
            chave = f"{normalizar_texto(nome)}|{normalizar_texto(serie)}"
            if chave in chaves_existentes:
                continue
            existentes.append({"nome": nome, "serie": serie})
            chaves_existentes.add(chave)
            inseridos.append({"nome": nome, "serie": serie})

        if not inseridos:
            return 0

        ELETIVAS[professora_sel] = existentes
        st.session_state.ELETIVAS = ELETIVAS

        if SUPABASE_VALID:
            registros = [
                {
                    "professora": professora_sel,
                    "nome_aluno": item["nome"],
                    "serie": item["serie"],
                    "origem": origem
                }
                for item in inseridos
            ]
            _supabase_request("POST", "eletivas", json=registros)
            st.session_state.FONTE_ELETIVAS = "supabase"

        return len(inseridos)

    tab_busca, tab_digitar, tab_colar, tab_upload = st.tabs(
        ["🔎 Buscar no Cadastro", "✍️ Digitar", "📋 Colar Lista", "📁 Upload de Arquivo"]
    )

    with tab_busca:
        if df_alunos.empty:
            st.info("Não há alunos cadastrados para buscar.")
        else:
            base_busca = preparar_base_alunos_ativos_tutoria(df_alunos)
            base_busca["nome"] = base_busca["nome"].astype(str)
            if "turma" not in base_busca.columns:
                base_busca["turma"] = ""
            base_busca["turma"] = base_busca["turma"].astype(str)
            termo_busca = st.text_input("Buscar aluno por nome", key="eletiva_busca_nome")
            if termo_busca:
                base_busca = base_busca[base_busca["nome"].str.contains(termo_busca, case=False, na=False)]

            opcoes = []
            mapa_opcoes = {}
            for _, linha in base_busca.drop_duplicates(subset=["nome", "turma"]).iterrows():
                label = f"{linha['nome']} ({linha['turma']})" if linha["turma"] else linha["nome"]
                opcoes.append(label)
                mapa_opcoes[label] = {"nome": linha["nome"], "serie": linha["turma"], "ra": linha.get("ra", "")}

            selecionados_busca = st.multiselect("Selecione estudantes para adicionar", opcoes, key="eletiva_sel_busca")
            if st.button("✅ Registrar Selecionados", key="eletiva_btn_add_busca", type="primary"):
                try:
                    novos = [mapa_opcoes[item] for item in selecionados_busca]
                    qtd = _adicionar_estudantes_eletiva(novos, origem="busca_cadastro")
                    if qtd > 0:
                        st.success(f"{qtd} estudante(s) adicionados.")
                        st.rerun()
                    else:
                        st.warning("Nenhum estudante novo para adicionar.")
                except Exception as e:
                    st.error(f"Erro ao registrar estudantes: {e}")

    with tab_digitar:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            nome_manual = st.text_input("Nome do estudante", key="eletiva_nome_manual")
        with col_b:
            serie_manual = st.text_input("Turma", key="eletiva_serie_manual", placeholder="Ex: 6º Ano A")
        if st.button("✅ Registrar Estudante", key="eletiva_btn_add_manual", type="primary"):
            try:
                qtd = _adicionar_estudantes_eletiva(
                    [{"nome": nome_manual, "serie": serie_manual}],
                    origem="digitacao_manual"
                )
                if qtd > 0:
                    st.success("Estudante registrado com sucesso.")
                    st.rerun()
                else:
                    st.warning("Informe um nome válido ou escolha um estudante novo.")
            except Exception as e:
                st.error(f"Erro ao registrar estudante: {e}")

    with tab_colar:
        feedback_eletiva = st.session_state.get("eletiva_feedback", {})
        if feedback_eletiva.get("tipo") == "success":
            st.success(feedback_eletiva.get("msg", ""))
        elif feedback_eletiva.get("tipo") == "error":
            st.error(feedback_eletiva.get("msg", ""))
        elif feedback_eletiva.get("tipo") == "warning":
            st.warning(feedback_eletiva.get("msg", ""))

        serie_padrao = st.text_input("Turma padrao (opcional)", key="eletiva_serie_padrao", placeholder="Ex: 6o Ano A")
        lista_colada = st.text_area(
            "Cole a lista (1 estudante por linha). Opcional: Nome;Turma",
            key="eletiva_lista_colada",
            height=160,
            placeholder="Maria Silva; 7A\nJoao Santos; 8B\nAna Souza"
        )

        if st.button("Registrar Lista Colada", key="eletiva_btn_add_colada", type="primary"):
            try:
                novos = []
                for linha in lista_colada.splitlines():
                    item = _normalizar_linha_lista(linha, serie_padrao=serie_padrao)
                    if item:
                        novos.append(item)
                qtd = _adicionar_estudantes_eletiva(novos, origem="lista_colada")
                if qtd > 0:
                    msg = f"Sucesso: {qtd} estudante(s) adicionados via lista."
                    st.session_state["eletiva_feedback"] = {"tipo": "success", "msg": msg}
                    st.success(msg)
                else:
                    msg = "Nenhum item valido novo foi encontrado na lista."
                    st.session_state["eletiva_feedback"] = {"tipo": "warning", "msg": msg}
                    st.warning(msg)
            except Exception as e:
                msg = f"Erro ao registrar lista: {e}"
                st.session_state["eletiva_feedback"] = {"tipo": "error", "msg": msg}
                st.error(msg)

        if st.button("Salvar Agora no Supabase", key="eletiva_salvar_agora_colar", use_container_width=True):
            if not SUPABASE_VALID:
                msg = "Erro: conexao com Supabase indisponivel. Verifique URL/KEY e tente novamente."
                st.session_state["eletiva_feedback"] = {"tipo": "error", "msg": msg}
                st.error(msg)
            else:
                try:
                    registros_prof = [
                        {
                            "professora": professora_sel,
                            "nome_aluno": str(item.get("nome", "")).strip(),
                            "serie": formatar_turma_eletiva(str(item.get("serie", "")).strip()),
                            "origem": "salvar_agora"
                        }
                        for item in ELETIVAS.get(professora_sel, [])
                        if str(item.get("nome", "")).strip()
                    ]

                    prof_q = requests.utils.quote(str(professora_sel), safe="")
                    _supabase_request("DELETE", f"eletivas?professora=eq.{prof_q}")
                    if registros_prof:
                        _supabase_request("POST", "eletivas", json=registros_prof)

                    st.session_state.FONTE_ELETIVAS = "supabase"
                    msg = f"Salvamento concluido para {professora_sel}: {len(registros_prof)} estudante(s) gravado(s) no Supabase."
                    st.session_state["eletiva_feedback"] = {"tipo": "success", "msg": msg}
                    st.success(msg)
                except Exception as e:
                    msg = f"Erro ao salvar no Supabase: {e}"
                    st.session_state["eletiva_feedback"] = {"tipo": "error", "msg": msg}
                    st.error(msg)

    with tab_upload:
        arquivo_eletiva = st.file_uploader(
            "Envie CSV, TXT ou XLSX com nomes dos estudantes",
            type=["csv", "txt", "xlsx"],
            key="eletiva_upload"
        )
        serie_upload = st.text_input("Turma padrão para upload (opcional)", key="eletiva_serie_upload", placeholder="Ex: 6º Ano A")
        if st.button("✅ Registrar Arquivo", key="eletiva_btn_add_upload", type="primary"):
            if not arquivo_eletiva:
                st.warning("Selecione um arquivo para continuar.")
            else:
                try:
                    nome_arquivo = arquivo_eletiva.name.lower()
                    novos = []
                    if nome_arquivo.endswith(".xlsx"):
                        df_up = pd.read_excel(arquivo_eletiva)
                        colunas_norm = {c: normalizar_texto(str(c)) for c in df_up.columns}
                        col_nome = next((c for c, n in colunas_norm.items() if "nome" in n or "aluno" in n or "estudante" in n), None)
                        col_serie = next((c for c, n in colunas_norm.items() if "serie" in n or "ano" in n or "turma" in n), None)
                        if not col_nome and len(df_up.columns) > 0:
                            col_nome = df_up.columns[0]
                        if col_nome:
                            for _, linha in df_up.iterrows():
                                item = {
                                    "nome": str(linha.get(col_nome, "")).strip(),
                                    "serie": str(linha.get(col_serie, serie_upload) if col_serie else serie_upload).strip()
                                }
                                if item["nome"] and item["nome"].lower() != "nan":
                                    novos.append(item)
                    else:
                        bruto = arquivo_eletiva.getvalue()
                        try:
                            conteudo = bruto.decode("utf-8-sig")
                        except UnicodeDecodeError:
                            conteudo = bruto.decode("latin-1", errors="ignore")
                        if nome_arquivo.endswith(".csv"):
                            df_csv = pd.read_csv(StringIO(conteudo), sep=None, engine="python")
                            if len(df_csv.columns) == 1:
                                for linha in df_csv.iloc[:, 0].astype(str).tolist():
                                    item = _normalizar_linha_lista(linha, serie_padrao=serie_upload)
                                    if item:
                                        novos.append(item)
                            else:
                                colunas_norm = {c: normalizar_texto(str(c)) for c in df_csv.columns}
                                col_nome = next((c for c, n in colunas_norm.items() if "nome" in n or "aluno" in n or "estudante" in n), df_csv.columns[0])
                                col_serie = next((c for c, n in colunas_norm.items() if "serie" in n or "ano" in n or "turma" in n), None)
                                for _, linha in df_csv.iterrows():
                                    item = {
                                        "nome": str(linha.get(col_nome, "")).strip(),
                                        "serie": str(linha.get(col_serie, serie_upload) if col_serie else serie_upload).strip()
                                    }
                                    if item["nome"] and item["nome"].lower() != "nan":
                                        novos.append(item)
                        else:
                            for linha in conteudo.splitlines():
                                item = _normalizar_linha_lista(linha, serie_padrao=serie_upload)
                                if item:
                                    novos.append(item)

                    qtd = _adicionar_estudantes_eletiva(novos, origem="upload_arquivo")
                    if qtd > 0:
                        st.success(f"{qtd} estudante(s) adicionados via upload.")
                        st.rerun()
                    else:
                        st.warning("Nenhum estudante novo válido foi encontrado no arquivo.")
                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {e}")

    def _apagar_registro_supabase_eletiva(professora: str, nome: str, serie: str = ""):
        prof_q = requests.utils.quote(str(professora), safe="")
        nome_q = requests.utils.quote(str(nome), safe="")
        path = f"eletivas?professora=eq.{prof_q}&nome_aluno=eq.{nome_q}"
        if str(serie).strip():
            serie_q = requests.utils.quote(str(serie), safe="")
            path += f"&serie=eq.{serie_q}"
        _supabase_request("DELETE", path)

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
        df_view = df_view[df_view["Nome"].str.contains(busca_nome, case=False, na=False)]
    if filtro_status != "Todos":
        df_view = df_view[df_view["Status"] == filtro_status]

    st.markdown("---")
    st.subheader("📋 Estudantes da Eletiva")
    colunas_visiveis = [
        "Professor(a)", "Nome", "Turma", "Aluno Cadastrado",
        "RA", "Turma no Sistema", "Situação", "Status"
    ]
    colunas_visiveis = [c for c in colunas_visiveis if c in df_view.columns]
    st.dataframe(df_view[colunas_visiveis], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🖨️ Imprimir Lista da Eletiva")
    modo_impressao = st.radio(
        "Tipo de impressão",
        ["Por Professor(a)", "Por Turma"],
        horizontal=True,
        key="eletiva_modo_impressao"
    )

    if modo_impressao == "Por Professor(a)":
        professoras_lista = sorted(ELETIVAS.keys())
        prof_impressao = st.selectbox(
            "Professor(a) para imprimir",
            professoras_lista,
            index=professoras_lista.index(professora_sel) if professora_sel in professoras_lista else 0,
            key="eletiva_prof_impressao"
        )
        df_imp = montar_dataframe_eletiva(prof_impressao, df_alunos, ELETIVAS)
        if st.button("Gerar PDF por Professor(a)", type="primary", key="btn_pdf_eletiva_prof"):
            if df_imp.empty:
                st.warning("Nao ha estudantes para imprimir nesse professor(a).")
            else:
                pdf = gerar_pdf_eletiva(f"Professor(a): {prof_impressao}", df_imp)
                st.download_button(
                    "Baixar PDF",
                    data=pdf,
                    file_name=f"Eletiva_Professor_{gerar_chave_segura(prof_impressao)}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    key="download_pdf_eletiva_prof"
                )

        st.markdown("### Imprimir varias professoras")
        professoras_sel = st.multiselect(
            "Selecione as professoras para imprimir",
            professoras_lista,
            default=[prof_impressao] if prof_impressao else [],
            key="eletiva_professoras_mult"
        )

        if st.button("Imprimir Professoras Selecionadas", key="btn_zip_eletiva_prof_mult"):
            if not professoras_sel:
                st.warning("Selecione ao menos uma professora.")
            else:
                zip_buffer = BytesIO()
                total_pdfs = 0
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for prof_sel in professoras_sel:
                        df_prof = montar_dataframe_eletiva(prof_sel, df_alunos, ELETIVAS)
                        if df_prof.empty:
                            continue
                        pdf_prof = gerar_pdf_eletiva(f"Professor(a): {prof_sel}", df_prof)
                        zip_file.writestr(f"Eletiva_Professor_{gerar_chave_segura(prof_sel)}.pdf", pdf_prof.getvalue())
                        total_pdfs += 1

                if total_pdfs == 0:
                    st.warning("Nenhum PDF foi gerado para as professoras selecionadas.")
                else:
                    zip_buffer.seek(0)
                    st.download_button(
                        "Baixar ZIP de Professoras",
                        data=zip_buffer,
                        file_name=f"Eletiva_Professoras_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                        mime="application/zip",
                        key="download_zip_eletiva_professoras"
                    )

    else:
        frames = []
        for prof in sorted(ELETIVAS.keys()):
            df_tmp = montar_dataframe_eletiva(prof, df_alunos, ELETIVAS)
            if not df_tmp.empty:
                frames.append(df_tmp)
        df_geral_eletivas = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        turmas_eletiva = sorted([
            t for t in df_geral_eletivas.get("Turma", pd.Series(dtype=str)).dropna().astype(str).str.strip().unique().tolist() if t
        ])
        if not turmas_eletiva:
            st.info("Nao ha turmas de eletiva para imprimir.")
        else:
            turma_impressao = st.selectbox("Turma da Eletiva", turmas_eletiva, key="eletiva_turma_impressao")
            df_imp = df_geral_eletivas[
                df_geral_eletivas["Turma"].astype(str).str.strip() == str(turma_impressao).strip()
            ].copy()
            if st.button("Gerar PDF por Turma", type="primary", key="btn_pdf_eletiva_turma"):
                if df_imp.empty:
                    st.warning("Nao ha estudantes para imprimir nessa turma.")
                else:
                    pdf = gerar_pdf_eletiva(f"Turma: {turma_impressao}", df_imp)
                    st.download_button(
                        "Baixar PDF",
                        data=pdf,
                        file_name=f"Eletiva_Turma_{gerar_chave_segura(turma_impressao)}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        key="download_pdf_eletiva_turma"
                    )

            st.markdown("### Imprimir varias turmas")
            turmas_sel = st.multiselect(
                "Selecione as turmas para imprimir",
                turmas_eletiva,
                default=[turma_impressao] if turma_impressao else [],
                key="eletiva_turmas_mult"
            )

            if st.button("Imprimir Turmas Selecionadas", key="btn_zip_eletiva_turma_mult"):
                if not turmas_sel:
                    st.warning("Selecione ao menos uma turma.")
                else:
                    zip_buffer = BytesIO()
                    total_pdfs = 0
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for turma_sel in turmas_sel:
                            df_turma = df_geral_eletivas[
                                df_geral_eletivas["Turma"].astype(str).str.strip() == str(turma_sel).strip()
                            ].copy()
                            if df_turma.empty:
                                continue
                            pdf_turma = gerar_pdf_eletiva(f"Turma: {turma_sel}", df_turma)
                            zip_file.writestr(f"Eletiva_Turma_{gerar_chave_segura(turma_sel)}.pdf", pdf_turma.getvalue())
                            total_pdfs += 1

                    if total_pdfs == 0:
                        st.warning("Nenhum PDF foi gerado para as turmas selecionadas.")
                    else:
                        zip_buffer.seek(0)
                        st.download_button(
                            "Baixar ZIP de Turmas",
                            data=zip_buffer,
                            file_name=f"Eletiva_Turmas_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                            mime="application/zip",
                            key="download_zip_eletiva_turmas"
                        )

    st.markdown("---")

    st.subheader("🔎 Estudantes Sem Professor Na Eletiva")
    st.caption("Selecione turmas do sistema para identificar alunos que ainda não estão vinculados a nenhum professor de eletiva.")
    if df_alunos.empty or "nome" not in df_alunos.columns:
        st.info("Não há base de alunos para pesquisa.")
    elif "turma" not in df_alunos.columns:
        st.info("A base de alunos não possui coluna de turma para pesquisa.")
    else:
        turmas_base = sorted([t for t in df_alunos["turma"].dropna().astype(str).str.strip().unique().tolist() if t])
        turmas_pesquisa = st.multiselect(
            "Turmas para pesquisar",
            turmas_base,
            default=turmas_base,
            key="eletiva_turmas_pesquisa_nao_localizados"
        )
        if turmas_pesquisa:
            frames = []
            for prof in sorted(ELETIVAS.keys()):
                df_tmp = montar_dataframe_eletiva(prof, df_alunos, ELETIVAS)
                if not df_tmp.empty:
                    frames.append(df_tmp)
            df_geral_eletivas = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

            vinculados = set()
            if not df_geral_eletivas.empty:
                df_vinc = df_geral_eletivas[
                    (df_geral_eletivas["Status"] == "Encontrado")
                    & (df_geral_eletivas["Aluno Cadastrado"].astype(str).str.strip() != "")
                    & (df_geral_eletivas["Professor(a)"].astype(str).str.strip() != "")
                ].copy()
                for _, r in df_vinc.iterrows():
                    vinculados.add((
                        normalizar_texto(r.get("Aluno Cadastrado", "")),
                        normalizar_texto(r.get("Turma no Sistema", ""))
                    ))

            base_turmas = df_alunos[df_alunos["turma"].astype(str).isin(turmas_pesquisa)].copy()
            base_turmas["nome_norm"] = base_turmas["nome"].astype(str).apply(normalizar_texto)
            base_turmas["turma_norm"] = base_turmas["turma"].astype(str).apply(normalizar_texto)

            sem_professor = []
            for _, aluno in base_turmas.iterrows():
                chave = (aluno.get("nome_norm", ""), aluno.get("turma_norm", ""))
                if chave not in vinculados:
                    sem_professor.append({
                        "Nome": aluno.get("nome", ""),
                        "Turma": aluno.get("turma", ""),
                        "RA": aluno.get("ra", ""),
                        "Situação": aluno.get("situacao", ""),
                        "Professor(a)": ""
                    })

            df_pendentes = pd.DataFrame(sem_professor)
            st.metric("Estudantes sem professor de eletiva", len(df_pendentes))
            if df_pendentes.empty:
                st.success("Todos os estudantes das turmas selecionadas já possuem professor na eletiva.")
            else:
                st.dataframe(df_pendentes, use_container_width=True, hide_index=True)
        else:
            st.info("Selecione pelo menos uma turma para pesquisar.")

    if alunos_raw:
        st.markdown("---")
        st.subheader("✏️ Editar ou Excluir Estudante")
        opcoes_estudantes = [
            f"{a.get('nome', '').strip()} — {a.get('serie', '').strip()}".strip(" —")
            for a in alunos_raw
        ]
        idx_sel = st.selectbox(
            "Selecione o estudante",
            options=list(range(len(opcoes_estudantes))),
            format_func=lambda i: opcoes_estudantes[i],
            key="eletiva_idx_edicao"
        )

        estudante_sel = alunos_raw[idx_sel]
        nome_antigo = str(estudante_sel.get("nome", "")).strip()
        serie_antiga = str(estudante_sel.get("serie", "")).strip()

        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            novo_nome = st.text_input("Nome", value=nome_antigo, key=f"eletiva_nome_edit_{idx_sel}")
        with col_ed2:
            nova_serie = st.text_input("Turma", value=serie_antiga, key=f"eletiva_serie_edit_{idx_sel}")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✅ Editar Estudante", type="primary", key="btn_editar_estudante_eletiva"):
                novo_nome = novo_nome.strip()
                nova_serie = formatar_turma_eletiva(nova_serie.strip())
                if not novo_nome:
                    st.warning("Informe um nome válido para salvar.")
                else:
                    try:
                        ELETIVAS[professora_sel][idx_sel] = {"nome": novo_nome, "serie": nova_serie}
                        st.session_state.ELETIVAS = ELETIVAS
                        if SUPABASE_VALID:
                            _apagar_registro_supabase_eletiva(professora_sel, nome_antigo, serie_antiga)
                            _supabase_request("POST", "eletivas", json=[{
                                "professora": professora_sel,
                                "nome_aluno": novo_nome,
                                "serie": nova_serie,
                                "origem": "edicao_manual"
                            }])
                            st.session_state.FONTE_ELETIVAS = "supabase"
                        st.success("✅ Estudante atualizado com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao editar estudante: {e}")

        with col_btn2:
            confirmar_exc = st.checkbox("Confirmar exclusão", key=f"confirmar_exclusao_eletiva_{idx_sel}")
            if st.button("🗑️ Excluir Estudante", type="secondary", key="btn_excluir_estudante_eletiva"):
                if not confirmar_exc:
                    st.warning("Marque a confirmação para excluir.")
                else:
                    try:
                        removido = ELETIVAS[professora_sel].pop(idx_sel)
                        st.session_state.ELETIVAS = ELETIVAS
                        if SUPABASE_VALID:
                            _apagar_registro_supabase_eletiva(
                                professora_sel,
                                str(removido.get("nome", "")),
                                str(removido.get("serie", ""))
                            )
                            st.session_state.FONTE_ELETIVAS = "supabase"
                        st.success("✅ Estudante excluído com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir estudante: {e}")

        st.markdown("---")
        st.subheader("🧹 Limpeza em Massa")
        confirmar_excluir_todos = st.checkbox(
            f"Confirmo excluir todos os estudantes da professora {professora_sel}",
            key=f"confirmar_excluir_todos_{gerar_chave_segura(professora_sel)}"
        )
        if st.button("🗑️ Excluir Todos os Alunos da Eletiva", type="secondary", key="btn_excluir_todos_eletiva"):
            if not confirmar_excluir_todos:
                st.warning("Marque a confirmação para excluir todos.")
            else:
                try:
                    ELETIVAS[professora_sel] = []
                    st.session_state.ELETIVAS = ELETIVAS
                    if SUPABASE_VALID:
                        prof_q = requests.utils.quote(str(professora_sel), safe="")
                        _supabase_request("DELETE", f"eletivas?professora=eq.{prof_q}")
                        st.session_state.FONTE_ELETIVAS = "supabase"
                    st.success("✅ Todos os estudantes da eletiva foram excluídos.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir todos os estudantes: {e}")
                # ======================================================
# PÁGINA 🫂 TUTORIA
# ======================================================
elif menu == "🫂 Tutoria":
    
    # ======================================================
    # TUTORIA — BUSCA FLEXÍVEL + VALIDAÇÃO VISUAL
    # ======================================================
    def estudante_ativo(linha) -> bool:
        """Considera ativo todo estudante que nao esteja claramente marcado como inativo."""
        for coluna in ["situacao", "situação", "status", "ativo"]:
            if coluna not in linha.index:
                continue
            valor = linha.get(coluna)
            if isinstance(valor, bool):
                return valor
            if valor is None or str(valor).strip() == "" or str(valor).lower().strip() in {"nan", "none", "null"}:
                return True
            valor_norm = normalizar_texto(valor)
            termos_inativos = [
                "INATIVO", "INATIVA", "TRANSFERIDO", "TRANSFERIDA", "REMOVIDO", "REMOVIDA",
                "EVADIDO", "EVADIDA", "CANCELADO", "CANCELADA", "BAIXADO", "BAIXADA",
                "DESISTENTE", "ABANDONO", "ENCERRADO", "ENCERRADA"
            ]
            if any(termo in valor_norm for termo in termos_inativos):
                return False
            return True
        return True

    def preparar_base_alunos_ativos_tutoria(df_alunos: pd.DataFrame) -> pd.DataFrame:
        """Prepara a base de estudantes do Supabase para busca inteligente da tutoria."""
        if df_alunos is None or df_alunos.empty or "nome" not in df_alunos.columns:
            return pd.DataFrame()

        base = df_alunos.copy()
        if "turma" not in base.columns:
            base["turma"] = ""
        if "ra" not in base.columns:
            base["ra"] = ""
        if "situacao" not in base.columns:
            base["situacao"] = ""

        base["nome"] = base["nome"].astype(str).str.strip()
        base["turma"] = base["turma"].astype(str).apply(formatar_turma_eletiva)
        base["ra"] = base["ra"].astype(str).str.replace(r"\D", "", regex=True)
        base["nome_norm"] = base["nome"].apply(normalizar_texto)
        base["nome_aprox"] = base["nome"].apply(_nome_para_busca_aproximada)
        base["turma_norm"] = base["turma"].apply(turma_para_comparacao)
        base = base[base.apply(estudante_ativo, axis=1)]
        base = base[base["nome"].str.strip() != ""]
        return base.reset_index(drop=True)


    def _score_nome_tutoria(nome_digitado: str, nome_base: str) -> float:
        nome_norm = normalizar_texto(nome_digitado)
        base_norm = normalizar_texto(nome_base)
        nome_aprox = _nome_para_busca_aproximada(nome_digitado)
        base_aprox = _nome_para_busca_aproximada(nome_base)
        if not nome_norm or not base_norm:
            return 0.0

        score = max(
            SequenceMatcher(None, nome_norm, base_norm).ratio(),
            SequenceMatcher(None, nome_aprox, base_aprox).ratio(),
        )
        if base_norm.startswith(nome_norm) or base_aprox.startswith(nome_aprox):
            score = max(score, 0.96)
        elif nome_norm in base_norm or nome_aprox in base_aprox:
            score = max(score, 0.92)

        tokens_digitados = [t for t in nome_aprox.split() if len(t) >= 2]
        tokens_base = [t for t in base_aprox.split() if len(t) >= 2]
        if tokens_digitados and tokens_base:
            acertos = 0
            for token in tokens_digitados:
                if any(token == tb or token in tb or tb in token or SequenceMatcher(None, token, tb).ratio() >= 0.82 for tb in tokens_base):
                    acertos += 1
            if acertos:
                score_tokens = acertos / max(len(tokens_digitados), 1)
                score = max(score, min(0.98, 0.55 + score_tokens * 0.40))
        return float(score)

    def buscar_estudante_ativo_mais_proximo(nome_digitado: str, serie_digitada: str, df_alunos: pd.DataFrame) -> dict | None:
        """Busca o estudante ativo mais proximo no Supabase usando turma como confirmacao forte."""
        base = preparar_base_alunos_ativos_tutoria(df_alunos)
        if base.empty:
            return None

        nome_original = str(nome_digitado or "").strip()
        serie_original = formatar_turma_eletiva(serie_digitada)
        nome_norm = normalizar_texto(nome_original)
        serie_norm = turma_para_comparacao(serie_original)
        ra_digitado = "".join(ch for ch in nome_original if ch.isdigit())

        if ra_digitado and len(ra_digitado) >= 5:
            por_ra = base[base["ra"] == ra_digitado]
            if not por_ra.empty:
                aluno = por_ra.iloc[0]
                return {"nome": aluno.get("nome", ""), "serie": aluno.get("turma", ""), "ra": aluno.get("ra", ""), "score": 1.0, "status_busca": "RA encontrado"}

        if not nome_norm:
            return None

        candidatos = base
        if serie_norm:
            candidatos_mesma_turma = base[base["turma_norm"] == serie_norm]
            if candidatos_mesma_turma.empty:
                candidatos_mesma_turma = base[base["turma"].apply(lambda t: serie_compativel_turma(serie_original, t))]
            if not candidatos_mesma_turma.empty:
                candidatos = candidatos_mesma_turma

        melhor = None
        melhor_score_nome = 0.0
        melhor_score_final = 0.0
        melhor_serie_ok = False

        for _, aluno in candidatos.iterrows():
            score_nome = _score_nome_tutoria(nome_original, aluno.get("nome", ""))
            turma_aluno = aluno.get("turma", "")
            turma_aluno_norm = aluno.get("turma_norm", turma_para_comparacao(turma_aluno))
            serie_ok = True
            if serie_norm:
                serie_ok = (serie_norm == turma_aluno_norm) or serie_compativel_turma(serie_original, turma_aluno)
            score_final = score_nome + (0.25 if serie_norm and serie_ok else (-0.45 if serie_norm else 0))
            if score_final > melhor_score_final:
                melhor_score_final = score_final
                melhor_score_nome = score_nome
                melhor = aluno
                melhor_serie_ok = serie_ok

        limite_nome = 0.42 if serie_norm and melhor_serie_ok else 0.72
        limite_final = 0.60 if serie_norm and melhor_serie_ok else 0.78
        if melhor is None or melhor_score_nome < limite_nome or melhor_score_final < limite_final:
            return None

        return {
            "nome": melhor.get("nome", ""),
            "serie": melhor.get("turma", ""),
            "ra": melhor.get("ra", ""),
            "score": round(float(min(melhor_score_final, 1.0)), 3),
            "status_busca": "Encontrado por sonoridade do nome e turma compativel" if melhor_serie_ok else "Encontrado por sonoridade do nome",
        }

    def sugerir_estudantes_tutoria(nome_digitado: str, serie_digitada: str, df_alunos: pd.DataFrame, limite_minimo: float = 0.18, max_sugestoes: int = 5) -> list[dict]:
        """
        Retorna candidatos próximos para conferência manual.
        Aqui a intenção NÃO é inserir automaticamente, mas mostrar opções para o usuário escolher.
        Por isso o limite é mais baixo e a turma funciona como filtro/preferência forte.
        """
        base = preparar_base_alunos_ativos_tutoria(df_alunos)
        if base.empty:
            return []

        nome_original = str(nome_digitado or "").strip()
        serie_original = formatar_turma_eletiva(serie_digitada)
        nome_norm = normalizar_texto(nome_original)
        serie_norm = turma_para_comparacao(serie_original)
        if not nome_norm:
            return []

        candidatos = []
        for _, aluno in base.iterrows():
            nome_base = str(aluno.get("nome", "")).strip()
            turma_base = formatar_turma_eletiva(str(aluno.get("turma", "")).strip())
            turma_base_norm = aluno.get("turma_norm", turma_para_comparacao(turma_base))

            if not nome_base:
                continue

            serie_ok = True
            if serie_norm:
                serie_ok = (serie_norm == turma_base_norm) or serie_compativel_turma(serie_original, turma_base)

            score_nome = _score_nome_tutoria(nome_original, nome_base)

            # Se a turma foi informada e não bate, mantém como sugestão fraca, mas penaliza.
            score_final = score_nome + (0.35 if serie_norm and serie_ok else (-0.20 if serie_norm else 0))

            # Quando a turma bate, nomes curtos/incompletos podem ser úteis como sugestão manual.
            if serie_norm and serie_ok:
                limite = limite_minimo
            else:
                limite = max(limite_minimo, 0.35)

            if score_final >= limite or score_nome >= limite:
                candidatos.append({
                    "nome": nome_base,
                    "serie": turma_base,
                    "ra": str(aluno.get("ra", "")).strip(),
                    "score": round(float(min(max(score_final, score_nome), 1.0)), 3),
                    "turma_compativel": bool(serie_ok),
                })

        candidatos.sort(key=lambda x: (x.get("turma_compativel", False), x.get("score", 0)), reverse=True)

        vistos = set()
        unicos = []
        for cand in candidatos:
            chave = (normalizar_texto(cand.get("nome", "")), turma_para_comparacao(cand.get("serie", "")), cand.get("ra", ""))
            if chave in vistos:
                continue
            vistos.add(chave)
            unicos.append(cand)
            if len(unicos) >= max_sugestoes:
                break
        return unicos

    def resolver_estudantes_tutoria(novos_estudantes: list, df_alunos: pd.DataFrame) -> tuple[list, list]:
        resolvidos = []
        nao_encontrados = []
        for item in novos_estudantes or []:
            nome_digitado = str(item.get("nome", "")).strip()
            serie_digitada = formatar_turma_eletiva(str(item.get("serie", "")).strip())
            if not nome_digitado:
                continue
            encontrado = buscar_estudante_ativo_mais_proximo(nome_digitado, serie_digitada, df_alunos)
            if encontrado:
                resolvidos.append({
                    "nome": encontrado["nome"],
                    "serie": encontrado["serie"],
                    "ra": encontrado.get("ra", ""),
                    "nome_digitado": nome_digitado,
                    "serie_digitada": serie_digitada,
                    "score": encontrado.get("score", 0),
                    "status_busca": encontrado.get("status_busca", ""),
                })
            else:
                sugestoes = sugerir_estudantes_tutoria(nome_digitado, serie_digitada, df_alunos)
                nao_encontrados.append({
                    "nome": nome_digitado,
                    "serie": serie_digitada,
                    "motivo": "Não localizado automaticamente. Escolha uma sugestão manual se corresponder ao estudante.",
                    "sugestoes": sugestoes,
                })
        return resolvidos, nao_encontrados

    def montar_validacao_visual_tutoria(resolvidos: list, nao_encontrados: list) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Monta tabelas visuais para conferência da lista importada/digitada."""
        encontrados = []
        for item in resolvidos or []:
            score = float(item.get("score", 0) or 0)
            encontrados.append({
                "Digitado": item.get("nome_digitado", ""),
                "Turma digitada": item.get("serie_digitada", ""),
                "Encontrado no Supabase": item.get("nome", ""),
                "Turma Supabase": item.get("serie", ""),
                "RA": item.get("ra", ""),
                "Confiança": f"{round(score * 100)}%",
                "Como encontrou": item.get("status_busca", ""),
            })
        pendentes = []
        for idx, item in enumerate(nao_encontrados or []):
            sugestoes = item.get("sugestoes", []) or []
            texto_sugestoes = "; ".join([
                f"{s.get('nome', '')} ({s.get('serie', '')}) - {round(float(s.get('score', 0)) * 100)}%"
                for s in sugestoes
            ])
            pendentes.append({
                "ID": idx,
                "Digitado": item.get("nome", ""),
                "Turma digitada": item.get("serie", ""),
                "Situação": item.get("motivo", "Não encontrado automaticamente"),
                "Sugestões próximas": texto_sugestoes or "Sem sugestão próxima",
            })
        return pd.DataFrame(encontrados), pd.DataFrame(pendentes)

    page_header("🫂 Tutoria", "Cadastre professores, estudantes e espaços usados na tutoria", "#0f766e")
    TUTORIA = normalizar_base_tutoria(st.session_state.get("TUTORIA", {}))
    st.session_state.TUTORIA = TUTORIA
    nomes_tutoria = sorted(TUTORIA.keys())

    def _salvar_estado_tutoria(fonte: str = "local"):
        st.session_state.TUTORIA = normalizar_base_tutoria(TUTORIA)
        salvar_tutoria_local(st.session_state.TUTORIA)
        st.session_state.FONTE_TUTORIA = fonte

    def _carregar_campos_edicao_tutoria(nome_responsavel: str):
        dados = obter_registro_tutoria(TUTORIA, nome_responsavel)
        st.session_state["tutoria_edit_nome"] = nome_responsavel
        st.session_state["tutoria_edit_espaco"] = dados.get("espaco", "")
        st.session_state["tutoria_edit_tipo"] = normalizar_perfil_tutoria(dados.get("tipo", "Professor(a)"))
        st.session_state["tutoria_edit_horario"] = dados.get("horario", "")
        st.session_state["tutoria_edit_dia"] = dados.get("dia", "")
        st.session_state["tutoria_edit_loaded_for"] = nome_responsavel

    def _sincronizar_responsavel_tutoria(origem: str):
        nomes_atuais = sorted(TUTORIA.keys())
        if not nomes_atuais:
            return
        selecionado = str(st.session_state.get(origem, "")).strip()
        if selecionado not in nomes_atuais:
            selecionado = nomes_atuais[0]
        st.session_state["tutoria_responsavel_atual"] = selecionado
        st.session_state["tutoria_tutor_select"] = selecionado
        st.session_state["tutoria_tutor_lista_lote"] = selecionado
        st.session_state["tutoria_tutor_edicao"] = selecionado
        _carregar_campos_edicao_tutoria(selecionado)

    def _normalizar_linha_lista_tutoria(linha: str, serie_padrao: str = ""):
        """
        Le uma linha colada na tutoria e separa automaticamente NOME e TURMA.

        Aceita:
        1<TAB>Alice Elizabete<TAB>9 A
        1 Alice Elizabete 9 A
        2 Allana 9A
        20 Gabriel Costa 9o A
        Gabriel Costa 9o A
        Alice Elizabete; 9 A
        Alice Elizabete - 9o A

        Regra principal:
        - remove numeracao inicial da lista;
        - considera turma quando ela aparece no FINAL da linha;
        - tudo que vem antes da turma vira nome.
        """
        bruto = str(linha or "").strip()
        bruto = bruto.replace("\u00a0", " ").strip().lstrip("•-").strip()
        if not bruto:
            return None

        serie_padrao_formatada = formatar_turma_eletiva(serie_padrao)

        def _parece_turma(valor: str) -> bool:
            valor = str(valor or "").strip()
            if not valor:
                return False
            valor = valor.replace("º", " º ").replace("ª", " ª ")
            valor = re.sub(r"\s+", " ", valor).strip()
            padrao = r"^\d{1,2}\s*(?:º|ª|O|o)?\s*(?:ANO|ANOS|SERIE|SÉRIE)?\s*[A-Za-z]?$"
            return bool(re.fullmatch(padrao, valor, flags=re.I))

        def _limpar_numero_lista(valor: str) -> str:
            texto = str(valor or "").strip()
            return re.sub(r"^\s*\d{1,3}\s*[.)ºª-]?\s+", "", texto).strip()

        def _limpar_nome(valor: str) -> str:
            texto = _limpar_numero_lista(valor)
            texto = re.sub(r"\s+", " ", texto).strip(" -;|,\t")
            return texto

        def _montar(nome: str, turma: str = ""):
            nome = _limpar_nome(nome)
            turma_final = formatar_turma_eletiva(turma or serie_padrao_formatada)
            if not nome:
                return None
            return {"nome": nome, "serie": turma_final}

        # 1) Modelo de planilha: numero | nome | turma, geralmente por TAB.
        if "\t" in bruto:
            partes = [p.strip() for p in bruto.split("\t") if str(p).strip()]
            if len(partes) >= 3 and re.fullmatch(r"\d{1,3}", partes[0]):
                return _montar(partes[1], partes[2])
            if len(partes) >= 2 and _parece_turma(partes[-1]):
                nome_partes = partes[:-1]
                if nome_partes and re.fullmatch(r"\d{1,3}", nome_partes[0]):
                    nome_partes = nome_partes[1:]
                return _montar(" ".join(nome_partes), partes[-1])
            if len(partes) >= 2:
                if re.fullmatch(r"\d{1,3}", partes[0]):
                    return _montar(" ".join(partes[1:]), serie_padrao_formatada)
                return _montar(" ".join(partes), serie_padrao_formatada)

        # 2) Separadores explicitos.
        for sep in [";", "|", " – ", " - ", ","]:
            if sep in bruto:
                partes = [p.strip() for p in bruto.split(sep) if p.strip()]
                if len(partes) >= 2 and _parece_turma(partes[-1]):
                    return _montar(" ".join(partes[:-1]), partes[-1])
                if len(partes) >= 2:
                    return _montar(partes[0], partes[1])

        # 3) Modelo com tudo na mesma linha:
        #    "1 Alice Elizabete 9 A", "2 Allana 9A", "20 Gabriel Costa 9o A".
        sem_numero = _limpar_numero_lista(bruto)
        sem_numero = re.sub(r"\s+", " ", sem_numero).strip()

        m = re.match(
            r"^(?P<nome>.+?)\s+(?P<turma>\d{1,2}\s*(?:º|ª|O|o)?\s*(?:ANO|ANOS|SERIE|SÉRIE)?\s*[A-Za-z])\s*$",
            sem_numero,
            flags=re.I,
        )
        if m:
            return _montar(m.group("nome"), m.group("turma"))

        # 4) Ultima tentativa: se os dois ultimos tokens formarem turma, separa.
        tokens = sem_numero.split()
        if len(tokens) >= 2:
            ultimo = tokens[-1]
            penultimo = tokens[-2]
            if _parece_turma(ultimo):
                return _montar(" ".join(tokens[:-1]), ultimo)
            if _parece_turma(f"{penultimo} {ultimo}"):
                return _montar(" ".join(tokens[:-2]), f"{penultimo} {ultimo}")

        return _montar(sem_numero, serie_padrao_formatada)

    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#f0fdfa,#ecfeff);
        border:1px solid #99f6e4;
        border-radius:16px;
        padding:1.1rem 1.5rem;
        margin-bottom:1.25rem;
        box-shadow:0 4px 12px rgba(15,118,110,0.08);
    ">
        <div style="display:flex;align-items:center;gap:0.5rem;">
            <span>🫂</span>
            <span style="color:#134e4a;font-size:0.875rem;">Cada professor(a) agora pode ter estudantes vinculados, espaço usado, horário e dia de atendimento.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ======================================================
    # ÁREA TÉCNICA DA TUTORIA — OCULTA DA TELA PRINCIPAL
    # ======================================================
    # Esta parte concentra mensagens de fonte de dados e botões de restauração/sincronização.
    # Para deixar a tela pedagógica limpa, ela fica dentro de um expander fechado.
    # Se quiser esconder completamente, troque para False.
    EXIBIR_MANUTENCAO_TUTORIA = True

    if EXIBIR_MANUTENCAO_TUTORIA:
        with st.expander("⚙️ Ferramentas internas da Tutoria", expanded=False):
            if FONTE_TUTORIA == "supabase":
                st.success("✅ Tutoria online conectada ao Supabase.")
            elif FONTE_TUTORIA == "local" and SUPABASE_VALID:
                st.info("☁️ Tutoria pronta para sincronização online com o Supabase.")
            elif FONTE_TUTORIA == "local":
                st.info("💾 Tutoria em uso no armazenamento desta máquina.")
            elif FONTE_TUTORIA == "excel":
                st.info(f"📄 Base carregada do arquivo de tutoria: {os.path.basename(TUTORIA_ARQUIVO) if TUTORIA_ARQUIVO else 'arquivo local'}")
            else:
                st.warning("⚠️ Tutoria sem fonte oficial disponível no momento.")

            col_sync1, col_sync2 = st.columns(2)
            with col_sync1:
                if st.button("🔄 Restaurar da Planilha/Arquivo", key="reload_tutoria_local", use_container_width=True):
                    base_restaurada = normalizar_base_tutoria(TUTORIA_EXCEL if TUTORIA_EXCEL else carregar_tutoria_local({}))
                    st.session_state.TUTORIA = normalizar_base_tutoria(base_restaurada)
                    st.session_state.FONTE_TUTORIA = "excel" if TUTORIA_EXCEL else ("local" if os.path.exists(TUTORIA_CACHE_ARQUIVO) else "indisponivel")
                    st.success("✅ Tutoria restaurada.")
                    st.rerun()
            with col_sync2:
                if SUPABASE_VALID:
                    if st.button("☁️ Importar Estudantes do Supabase", key="importar_tutoria_supabase", use_container_width=True):
                        try:
                            df_refresh = _supabase_get_dataframe("tutoria?select=*", "recarregar tutoria")
                            base_supabase = converter_tutoria_supabase_para_dict(df_refresh) if not df_refresh.empty else {}
                            st.session_state.TUTORIA = mesclar_tutoria_com_metadados(base_supabase, TUTORIA)
                            _salvar_estado_tutoria("local")
                            st.success("✅ Estudantes importados do Supabase e metadados locais preservados.")
                            st.rerun()
                        except Exception as e:
                            st.warning(mensagem_erro_tutoria_supabase(e))
                else:
                    st.caption("Supabase indisponível nesta instalação.")

    st.markdown("---")
    st.subheader("👩‍🏫 Cadastro de Responsáveis e Espaços")
    tab_novo_tutor, tab_editar_tutor = st.tabs(["➕ Novo cadastro", "⚙️ Editar cadastro"])

    if nomes_tutoria:
        if st.session_state.get("tutoria_responsavel_atual") not in nomes_tutoria:
            st.session_state["tutoria_responsavel_atual"] = nomes_tutoria[0]
        for chave in ("tutoria_tutor_select", "tutoria_tutor_lista_lote", "tutoria_tutor_edicao"):
            if st.session_state.get(chave) not in nomes_tutoria:
                st.session_state[chave] = st.session_state["tutoria_responsavel_atual"]
        if st.session_state.get("tutoria_edit_loaded_for") != st.session_state["tutoria_tutor_edicao"]:
            _carregar_campos_edicao_tutoria(st.session_state["tutoria_tutor_edicao"])

    with tab_novo_tutor:
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            professores_lista = []
            if not df_professores.empty and "nome" in df_professores.columns:
                professores_lista = sorted(df_professores["nome"].dropna().astype(str).unique().tolist())
            
            if professores_lista:
                nome_novo_tutor = st.selectbox("Nome do responsável", professores_lista, key="tutoria_novo_nome")
            else:
                st.warning("Nenhum professor cadastrado. Cadastre professores em '👨‍🏫 Cadastrar Professores'.")
                nome_novo_tutor = ""
            
            opcoes_espacos_tutoria = obter_opcoes_espacos_tutoria(TUTORIA)
            espaco_novo_tutor_select = st.selectbox(
                "Espaço usado",
                opcoes_espacos_tutoria + ["Outro espaço"],
                key="tutoria_novo_espaco_select"
            )
            if espaco_novo_tutor_select == "Outro espaço":
                espaco_novo_tutor = st.text_input(
                    "Digite o novo espaço",
                    key="tutoria_novo_espaco",
                    placeholder="Ex: Sala 12"
                )
            else:
                espaco_novo_tutor = espaco_novo_tutor_select
        
        with col_n2:
            tipo_novo_tutor = st.selectbox("Perfil", PERFIS_TUTORIA, key="tutoria_novo_tipo")
            horario_novo_tutor = st.text_input("Horário", key="tutoria_novo_horario", placeholder="Ex: 13:10 às 14:00")
        
        dia_novo_tutor = st.text_input("Dia", key="tutoria_novo_dia", placeholder="Ex: Quarta-feira")
        
        if st.button("✅ Cadastrar Responsável", key="btn_cadastrar_tutor_tutoria", type="primary"):
            nome_novo_tutor = str(nome_novo_tutor).strip()
            if not nome_novo_tutor:
                st.warning("Informe o nome do responsável.")
            elif any(normalizar_texto(nome_novo_tutor) == normalizar_texto(nome_existente) for nome_existente in TUTORIA.keys()):
                st.warning("Já existe um cadastro com esse nome.")
            else:
                TUTORIA[nome_novo_tutor] = {
                    "nome": nome_novo_tutor,
                    "tipo": normalizar_perfil_tutoria(tipo_novo_tutor),
                    "espaco": normalizar_espaco_tutoria(espaco_novo_tutor),
                    "horario": str(horario_novo_tutor).strip(),
                    "dia": str(dia_novo_tutor).strip(),
                    "alunos": []
                }
                _salvar_estado_tutoria("local")
                st.success("✅ Cadastro realizado com sucesso.")
                st.rerun()

    with tab_editar_tutor:
        if not TUTORIA:
            st.info("Cadastre um responsável para habilitar a edição.")
        else:
            tutor_edicao = st.selectbox(
                "Cadastro para editar",
                nomes_tutoria,
                key="tutoria_tutor_edicao",
                on_change=_sincronizar_responsavel_tutoria,
                args=("tutoria_tutor_edicao",)
            )
            dados_edicao = obter_registro_tutoria(TUTORIA, tutor_edicao)
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                professores_lista = []
                if not df_professores.empty and "nome" in df_professores.columns:
                    professores_lista = sorted(df_professores["nome"].dropna().astype(str).unique().tolist())
                
                nome_atual = dados_edicao.get("nome", "")
                if professores_lista:
                    idx_atual = professores_lista.index(nome_atual) if nome_atual in professores_lista else 0
                    nome_edit_tutor = st.selectbox("Nome", professores_lista, index=idx_atual, key="tutoria_edit_nome")
                else:
                    nome_edit_tutor = st.text_input("Nome", value=nome_atual, key="tutoria_edit_nome")
                    st.warning("Nenhum professor cadastrado. Cadastre professores primeiro.")
                
                opcoes_espacos_tutoria = obter_opcoes_espacos_tutoria(TUTORIA)
                espaco_atual = dados_edicao.get("espaco", "")
                opcoes_edit_espacos = list(opcoes_espacos_tutoria)
                if espaco_atual and normalizar_texto(espaco_atual) not in {normalizar_texto(e) for e in opcoes_edit_espacos}:
                    opcoes_edit_espacos.append(espaco_atual)
                idx_espaco = opcoes_edit_espacos.index(espaco_atual) if espaco_atual in opcoes_edit_espacos else 0
                espaco_edit_tutor_select = st.selectbox(
                    "Espaço usado",
                    opcoes_edit_espacos + ["Outro espaço"],
                    index=idx_espaco,
                    key="tutoria_edit_espaco_select"
                )
                if espaco_edit_tutor_select == "Outro espaço":
                    espaco_edit_tutor = st.text_input(
                        "Digite o novo espaço",
                        value=espaco_atual,
                        key="tutoria_edit_espaco"
                    )
                else:
                    espaco_edit_tutor = espaco_edit_tutor_select
            with col_e2:
                tipo_edit_tutor = st.selectbox("Perfil", PERFIS_TUTORIA, key="tutoria_edit_tipo")
                horario_edit_tutor = st.text_input("Horário", key="tutoria_edit_horario")
            dia_edit_tutor = st.text_input("Dia", key="tutoria_edit_dia")

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("💾 Salvar Professor(a)", key="btn_salvar_tutor_tutoria", type="primary"):
                    nome_edit_tutor = str(nome_edit_tutor).strip()
                    if not nome_edit_tutor:
                        st.warning("Informe um nome válido.")
                    elif nome_edit_tutor != tutor_edicao and any(normalizar_texto(nome_edit_tutor) == normalizar_texto(nome_existente) for nome_existente in TUTORIA.keys()):
                        st.warning("Já existe outro cadastro com esse nome.")
                    else:
                        dados_salvos = obter_registro_tutoria(TUTORIA, tutor_edicao)
                        dados_salvos["nome"] = nome_edit_tutor
                        dados_salvos["tipo"] = normalizar_perfil_tutoria(tipo_edit_tutor)
                        dados_salvos["espaco"] = str(espaco_edit_tutor).strip()
                        dados_salvos["horario"] = str(horario_edit_tutor).strip()
                        dados_salvos["dia"] = str(dia_edit_tutor).strip()
                        if nome_edit_tutor != tutor_edicao:
                            TUTORIA.pop(tutor_edicao, None)
                        TUTORIA[nome_edit_tutor] = dados_salvos
                        _salvar_estado_tutoria("local")
                        if SUPABASE_VALID and nome_edit_tutor != tutor_edicao:
                            try:
                                tutor_q = requests.utils.quote(str(tutor_edicao), safe="")
                                _supabase_request("DELETE", f"tutoria?professora=eq.{tutor_q}")
                                registros = converter_tutoria_para_registros({nome_edit_tutor: dados_salvos}, origem="renomeacao_tutor")
                                if registros:
                                    _supabase_request("POST", "tutoria", json=registros)
                            except Exception:
                                pass
                        st.success("✅ Cadastro atualizado com sucesso.")
                        st.rerun()
            with col_b2:
                confirmar_exclusao_tutor = st.checkbox("Confirmar exclusão do cadastro", key="confirmar_exclusao_tutor_tutoria")
                if st.button("🗑️ Excluir Cadastro", key="btn_excluir_tutor_tutoria", type="secondary"):
                    if not confirmar_exclusao_tutor:
                        st.warning("Marque a confirmação para excluir.")
                    else:
                        TUTORIA.pop(tutor_edicao, None)
                        _salvar_estado_tutoria("local")
                        if SUPABASE_VALID:
                            try:
                                tutor_q = requests.utils.quote(str(tutor_edicao), safe="")
                                _supabase_request("DELETE", f"tutoria?professora=eq.{tutor_q}")
                            except Exception:
                                pass
                        st.success("✅ Cadastro excluído com sucesso.")
                        st.rerun()

    st.markdown("---")
    st.subheader("📊 Cadastros da Tutoria")
    if TUTORIA:
        dados_tutores = []
        for tutor, dados in sorted(TUTORIA.items()):
            alunos = dados.get("alunos", [])
            series = ", ".join(sorted({formatar_turma_eletiva(a.get("serie", "")) for a in alunos if a.get("serie")}))
            dados_tutores.append({
                "Responsável": tutor,
                "Perfil": dados.get("tipo", "Professor(a)"),
                "Espaço": dados.get("espaco", ""),
                "Horário": dados.get("horario", ""),
                "Dia": dados.get("dia", ""),
                "Total de Alunos": len(alunos),
                "Turmas": series
            })
        st.dataframe(pd.DataFrame(dados_tutores), use_container_width=True, hide_index=True)
    else:
        st.info("📭 Nenhum cadastro realizado em tutoria.")
        st.stop()

    st.markdown("---")
    tutor_sel = st.selectbox(
        "Selecione o responsável",
        nomes_tutoria,
        key="tutoria_tutor_select",
        on_change=_sincronizar_responsavel_tutoria,
        args=("tutoria_tutor_select",)
    )
    tutor_info = obter_registro_tutoria(TUTORIA, tutor_sel)
    alunos_raw = tutor_info.get("alunos", [])

    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    meta_tutoria = [
        ("Perfil", tutor_info.get("tipo", "Professor(a)")),
        ("Espaço", tutor_info.get("espaco", "") or "Não informado"),
        ("Horário", tutor_info.get("horario", "") or "Não informado"),
        ("Dia", tutor_info.get("dia", "") or "Não informado")
    ]
    for coluna, (rotulo, valor) in zip((col_meta1, col_meta2, col_meta3, col_meta4), meta_tutoria):
        with coluna:
            st.markdown(
                f"""
                <div style="padding:0.25rem 0 0.75rem 0;">
                    <div style="font-size:0.95rem;color:#475569;margin-bottom:0.35rem;">{rotulo}</div>
                    <div style="font-family:'Nunito',sans-serif;font-size:0.95rem;line-height:1.35;font-weight:700;color:#1e293b;word-break:break-word;">
                        {html.escape(str(valor))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # ======================================================
    # TUTORIA - CONTROLE DE DUPLICIDADE
    # Objetivo: impedir que um estudante já vinculado a um tutor
    # apareça disponível para outro tutor, além de apontar registros
    # duplicados já existentes para correção manual.
    # ======================================================
    def _nome_fonetico_seguro_tutoria(valor: str) -> str:
        try:
            return normalizar_nome_fonetico(valor)
        except Exception:
            return normalizar_texto(valor)

    def _chaves_estudante_tutoria(item: dict) -> set[str]:
        """Gera chaves de comparação por RA, nome normalizado e nome fonético."""
        ra = "".join(ch for ch in str(item.get("ra", "")) if ch.isdigit())
        nome = str(item.get("nome", item.get("Nome", item.get("aluno", "")))).strip()
        serie = formatar_turma_eletiva(str(item.get("serie", item.get("turma", item.get("Turma", "")))).strip())
        turma_cmp = turma_para_comparacao(serie)
        chaves = set()
        if ra:
            chaves.add(f"RA|{ra}")
        if nome:
            chaves.add(f"NOME|{normalizar_texto(nome)}|{turma_cmp}")
            chaves.add(f"FON|{_nome_fonetico_seguro_tutoria(nome)}|{turma_cmp}")
        return {c for c in chaves if c and not c.endswith("||")}

    def _mapear_estudantes_vinculados_tutoria(tutoria_dict: dict) -> dict:
        """Retorna chave -> lista de vínculos encontrados em todas as listas de tutoria."""
        mapa = {}
        for tutor_nome, dados_tutor in normalizar_base_tutoria(tutoria_dict).items():
            for aluno_item in dados_tutor.get("alunos", []) or []:
                registro = {
                    "tutor": tutor_nome,
                    "nome": str(aluno_item.get("nome", "")).strip(),
                    "serie": formatar_turma_eletiva(aluno_item.get("serie", "")),
                    "ra": "".join(ch for ch in str(aluno_item.get("ra", "")) if ch.isdigit()),
                }
                for chave in _chaves_estudante_tutoria(aluno_item):
                    mapa.setdefault(chave, []).append(registro)
        return mapa

    def _vinculos_do_estudante_tutoria(item: dict, tutoria_dict: dict) -> list[dict]:
        mapa = _mapear_estudantes_vinculados_tutoria(tutoria_dict)
        encontrados = []
        vistos = set()
        for chave in _chaves_estudante_tutoria(item):
            for vinculo in mapa.get(chave, []):
                id_vinculo = (
                    vinculo.get("tutor", ""),
                    vinculo.get("ra", ""),
                    normalizar_texto(vinculo.get("nome", "")),
                    turma_para_comparacao(vinculo.get("serie", "")),
                )
                if id_vinculo not in vistos:
                    encontrados.append(vinculo)
                    vistos.add(id_vinculo)
        return encontrados

    def _estudante_ja_tem_tutor(item: dict, tutoria_dict: dict, tutor_permitido: str | None = None) -> tuple[bool, list[dict]]:
        """Retorna True quando o estudante já está em qualquer lista de tutoria."""
        vinculos = _vinculos_do_estudante_tutoria(item, tutoria_dict)
        if tutor_permitido:
            vinculos = [v for v in vinculos if str(v.get("tutor", "")).strip() != str(tutor_permitido).strip()]
        return bool(vinculos), vinculos

    def _localizar_duplicidades_tutoria(tutoria_dict: dict) -> pd.DataFrame:
        """Monta uma tabela de estudantes que aparecem em mais de uma lista."""
        mapa = _mapear_estudantes_vinculados_tutoria(tutoria_dict)
        linhas = []
        chaves_processadas = set()
        for chave, vinculos in mapa.items():
            tutores = sorted({str(v.get("tutor", "")).strip() for v in vinculos if str(v.get("tutor", "")).strip()})
            if len(tutores) <= 1:
                continue
            assinatura = tuple(tutores) + (chave,)
            if assinatura in chaves_processadas:
                continue
            chaves_processadas.add(assinatura)
            primeiro = vinculos[0] if vinculos else {}
            linhas.append({
                "Estudante": primeiro.get("nome", ""),
                "Turma": primeiro.get("serie", ""),
                "RA": primeiro.get("ra", ""),
                "Aparece em": ", ".join(tutores),
                "Quantidade de listas": len(tutores),
            })
        return pd.DataFrame(linhas)

    duplicidades_tutoria_df = _localizar_duplicidades_tutoria(TUTORIA)
    if not duplicidades_tutoria_df.empty:
        st.warning(f"⚠️ Existem {len(duplicidades_tutoria_df)} estudante(s) em duplicidade nas listas de tutoria.")
        with st.expander("🔁 Ver estudantes em duplicidade", expanded=False):
            st.dataframe(duplicidades_tutoria_df, use_container_width=True, hide_index=True)
            st.caption("Remova o estudante da lista incorreta antes de tentar vinculá-lo a outro responsável.")

    # ======================================================
    # ======================================================
    # TUTORIA - GERENCIAR LISTA ATUAL DE ESTUDANTES
    # ======================================================
    # Este bloco fica visivel na pagina principal de Tutoria.
    # Ele permite editar, remover estudante individualmente e limpar a lista inteira
    # do responsavel selecionado.

    def _apagar_registro_supabase_tutoria(tutor_nome: str, nome_aluno: str = "", serie: str = "") -> bool:
        """Remove um estudante da tabela tutoria no Supabase, quando a conexao estiver ativa."""
        if not SUPABASE_VALID:
            return False
        tutor_q = requests.utils.quote(str(tutor_nome or ""), safe="")
        filtro = f"tutoria?professora=eq.{tutor_q}"
        nome_aluno = str(nome_aluno or "").strip()
        serie = str(serie or "").strip()
        if nome_aluno:
            nome_q = requests.utils.quote(nome_aluno, safe="")
            filtro += f"&nome_aluno=eq.{nome_q}"
        if serie:
            serie_q = requests.utils.quote(serie, safe="")
            filtro += f"&serie=eq.{serie_q}"
        return _supabase_mutation("DELETE", filtro, None, "excluir estudante da tutoria")

    st.markdown("---")
    st.subheader("🛠️ Gerenciar estudantes da lista selecionada")
    st.caption("Use esta área para editar ou excluir estudantes da lista do responsável selecionado.")

    alunos_raw = normalizar_alunos_tutoria(tutor_info.get("alunos", []))
    if tutor_sel not in TUTORIA:
        TUTORIA[tutor_sel] = estrutura_tutoria_vazia(nome=tutor_sel)
    TUTORIA[tutor_sel]["alunos"] = alunos_raw

    if alunos_raw:
        df_lista_atual = pd.DataFrame([
            {
                "Nº": idx + 1,
                "Nome": str(aluno.get("nome", "")).strip(),
                "Turma": formatar_turma_eletiva(str(aluno.get("serie", "")).strip()),
                "RA": "".join(ch for ch in str(aluno.get("ra", "")) if ch.isdigit()),
            }
            for idx, aluno in enumerate(alunos_raw)
        ])
        st.dataframe(df_lista_atual, use_container_width=True, hide_index=True)

        aba_remover, aba_editar, aba_limpar = st.tabs([
            "🗑️ Excluir estudante",
            "✏️ Editar estudante",
            "🧹 Excluir todos"
        ])

        with aba_remover:
            st.markdown("#### Excluir um estudante desta lista")
            opcoes_excluir = list(range(len(alunos_raw)))
            idx_excluir = st.selectbox(
                "Selecione o estudante que deseja remover",
                options=opcoes_excluir,
                format_func=lambda i: f"{alunos_raw[i].get('nome', '')} — {formatar_turma_eletiva(alunos_raw[i].get('serie', ''))}",
                key=f"tutoria_excluir_idx_{gerar_chave_segura(tutor_sel)}"
            )
            aluno_excluir = alunos_raw[idx_excluir]
            st.warning(
                f"Você vai remover **{aluno_excluir.get('nome', '')}** "
                f"({formatar_turma_eletiva(aluno_excluir.get('serie', ''))}) da lista de **{tutor_sel}**."
            )
            confirmar_excluir_um = st.checkbox(
                "Confirmo a exclusão deste estudante",
                key=f"confirmar_excluir_um_tutoria_{gerar_chave_segura(tutor_sel)}"
            )
            if st.button(
                "🗑️ Excluir estudante selecionado",
                type="secondary",
                key=f"btn_excluir_um_tutoria_{gerar_chave_segura(tutor_sel)}"
            ):
                if not confirmar_excluir_um:
                    st.warning("Marque a confirmação antes de excluir.")
                else:
                    try:
                        removido = TUTORIA[tutor_sel]["alunos"].pop(idx_excluir)
                        _salvar_estado_tutoria("local")
                        if SUPABASE_VALID:
                            _apagar_registro_supabase_tutoria(
                                tutor_sel,
                                str(removido.get("nome", "")),
                                str(removido.get("serie", ""))
                            )
                        st.success("✅ Estudante removido da lista.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir estudante: {e}")

        with aba_editar:
            st.markdown("#### Editar dados de um estudante desta lista")
            opcoes_editar = list(range(len(alunos_raw)))
            idx_editar = st.selectbox(
                "Selecione o estudante que deseja editar",
                options=opcoes_editar,
                format_func=lambda i: f"{alunos_raw[i].get('nome', '')} — {formatar_turma_eletiva(alunos_raw[i].get('serie', ''))}",
                key=f"tutoria_editar_idx_{gerar_chave_segura(tutor_sel)}"
            )
            aluno_editar = alunos_raw[idx_editar]
            nome_antigo = str(aluno_editar.get("nome", "")).strip()
            turma_antiga = formatar_turma_eletiva(str(aluno_editar.get("serie", "")).strip())
            ra_antigo = "".join(ch for ch in str(aluno_editar.get("ra", "")) if ch.isdigit())

            col_edit_nome, col_edit_turma, col_edit_ra = st.columns([3, 1, 1])
            with col_edit_nome:
                novo_nome = st.text_input(
                    "Nome",
                    value=nome_antigo,
                    key=f"tutoria_editar_nome_{gerar_chave_segura(tutor_sel)}_{idx_editar}"
                )
            with col_edit_turma:
                nova_turma = st.text_input(
                    "Turma",
                    value=turma_antiga,
                    key=f"tutoria_editar_turma_{gerar_chave_segura(tutor_sel)}_{idx_editar}"
                )
            with col_edit_ra:
                novo_ra = st.text_input(
                    "RA",
                    value=ra_antigo,
                    key=f"tutoria_editar_ra_{gerar_chave_segura(tutor_sel)}_{idx_editar}"
                )

            if st.button(
                "💾 Salvar edição do estudante",
                type="primary",
                key=f"btn_salvar_edicao_estudante_tutoria_{gerar_chave_segura(tutor_sel)}"
            ):
                novo_nome = str(novo_nome or "").strip()
                nova_turma = formatar_turma_eletiva(str(nova_turma or "").strip())
                novo_ra = "".join(ch for ch in str(novo_ra or "") if ch.isdigit())
                if not novo_nome:
                    st.warning("Informe o nome do estudante.")
                else:
                    try:
                        novo_item = {"nome": novo_nome, "serie": nova_turma}
                        if novo_ra:
                            novo_item["ra"] = novo_ra
                        TUTORIA[tutor_sel]["alunos"][idx_editar] = novo_item
                        _salvar_estado_tutoria("local")
                        if SUPABASE_VALID:
                            _apagar_registro_supabase_tutoria(tutor_sel, nome_antigo, turma_antiga)
                            _supabase_request("POST", "tutoria", json=[{
                                "professora": tutor_sel,
                                "nome_aluno": novo_nome,
                                "serie": nova_turma,
                                "origem": "edicao_manual"
                            }])
                        st.success("✅ Estudante atualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao editar estudante: {e}")

        with aba_limpar:
            st.markdown("#### Excluir todos os estudantes desta lista")
            st.error(f"Esta ação remove todos os estudantes vinculados a {tutor_sel}.")
            confirmar_limpar_lista = st.checkbox(
                f"Confirmo excluir todos os estudantes de {tutor_sel}",
                key=f"confirmar_limpar_lista_tutoria_{gerar_chave_segura(tutor_sel)}"
            )
            if st.button(
                "🧹 Excluir todos os estudantes desta lista",
                type="secondary",
                key=f"btn_limpar_lista_tutoria_{gerar_chave_segura(tutor_sel)}"
            ):
                if not confirmar_limpar_lista:
                    st.warning("Marque a confirmação antes de excluir todos.")
                else:
                    try:
                        TUTORIA[tutor_sel]["alunos"] = []
                        _salvar_estado_tutoria("local")
                        if SUPABASE_VALID:
                            tutor_q = requests.utils.quote(str(tutor_sel), safe="")
                            _supabase_request("DELETE", f"tutoria?professora=eq.{tutor_q}")
                        st.success("✅ Todos os estudantes desta lista foram removidos.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao limpar lista: {e}")
    else:
        st.info("Este responsável ainda não possui estudantes vinculados. Use a área de cadastro abaixo para inserir estudantes.")
    def _adicionar_estudantes_tutoria(novos_estudantes: list, origem: str, tutor_destino: str | None = None):
        tutor_destino = str(tutor_destino or tutor_sel).strip()
        registro = TUTORIA.setdefault(tutor_destino, estrutura_tutoria_vazia(nome=tutor_destino))
        existentes = registro.get("alunos", [])

        # Recarrega a base de alunos antes de validar para evitar cache antigo ou base vazia.
        df_alunos_validacao = df_alunos
        try:
            if SUPABASE_VALID:
                try:
                    carregar_alunos.clear()
                except Exception:
                    pass
                df_alunos_validacao = carregar_alunos()
        except Exception as e:
            logger.warning(f"Nao foi possivel recarregar alunos para validacao da tutoria: {e}")

        estudantes_resolvidos, nao_encontrados = resolver_estudantes_tutoria(novos_estudantes, df_alunos_validacao)

        bloqueados_por_tutor = []
        estudantes_liberados = []
        for estudante_item in estudantes_resolvidos:
            ja_tem, vinculos = _estudante_ja_tem_tutor(estudante_item, TUTORIA, tutor_permitido=tutor_destino)
            if ja_tem:
                bloqueados_por_tutor.append({
                    "nome": estudante_item.get("nome", ""),
                    "serie": estudante_item.get("serie", ""),
                    "ra": estudante_item.get("ra", ""),
                    "tutores": ", ".join(sorted({v.get("tutor", "") for v in vinculos if v.get("tutor", "")})),
                })
                continue
            estudantes_liberados.append(estudante_item)
        estudantes_resolvidos = estudantes_liberados

        chaves_existentes = set()
        for item in existentes:
            ra_existente = "".join(ch for ch in str(item.get("ra", "")) if ch.isdigit())
            nome_existente = normalizar_texto(item.get("nome", ""))
            serie_existente = turma_para_comparacao(item.get("serie", ""))
            if ra_existente:
                chaves_existentes.add(f"RA|{ra_existente}")
            chaves_existentes.add(f"NOME|{nome_existente}|{serie_existente}")

        inseridos = []
        for item in estudantes_resolvidos:
            nome = str(item.get("nome", "")).strip()
            serie = formatar_turma_eletiva(str(item.get("serie", "")).strip())
            ra = "".join(ch for ch in str(item.get("ra", "")) if ch.isdigit())
            if not nome:
                continue

            chave_ra = f"RA|{ra}" if ra else ""
            chave_nome = f"NOME|{normalizar_texto(nome)}|{turma_para_comparacao(serie)}"
            if chave_ra and chave_ra in chaves_existentes:
                continue
            if chave_nome in chaves_existentes:
                continue

            novo_registro = {
                "nome": nome,
                "serie": serie,
                "ra": ra,
                "nome_digitado": item.get("nome_digitado", ""),
                "serie_digitada": item.get("serie_digitada", ""),
                "score": item.get("score", 0),
                "status_busca": item.get("status_busca", ""),
            }
            existentes.append(novo_registro)
            inseridos.append(novo_registro)
            if chave_ra:
                chaves_existentes.add(chave_ra)
            chaves_existentes.add(chave_nome)

        df_ok, df_pendentes = montar_validacao_visual_tutoria(estudantes_resolvidos, nao_encontrados)
        st.session_state["tutoria_validacao_ultimo"] = {
            "responsavel": tutor_destino,
            "encontrados": df_ok.to_dict("records") if not df_ok.empty else [],
            "pendentes": df_pendentes.to_dict("records") if not df_pendentes.empty else [],
            "pendentes_raw": nao_encontrados,
        }

        if nao_encontrados:
            st.warning(
                "Alguns estudantes ficaram para conferência manual. Confira se existem no Supabase e se a turma está correta: "
                + ", ".join([f"{a['nome']} ({a['serie']})".strip() for a in nao_encontrados[:10]])
            )

        if bloqueados_por_tutor:
            nomes_bloqueados = ", ".join([
                f"{a['nome']} ({a['serie']}) já está com {a['tutores']}"
                for a in bloqueados_por_tutor[:10]
            ])
            st.warning("Estudantes não inseridos porque já possuem tutor: " + nomes_bloqueados)
            st.session_state["tutoria_bloqueados_ultimo"] = bloqueados_por_tutor

        if not inseridos:
            return 0

        registro["alunos"] = existentes
        TUTORIA[tutor_destino] = registro
        _salvar_estado_tutoria("local")

        if SUPABASE_VALID:
            registros = [
                {
                    "professora": tutor_destino,
                    "nome_aluno": item["nome"],
                    "serie": item["serie"],
                    "origem": origem
                }
                for item in inseridos
            ]
            try:
                _supabase_request("POST", "tutoria", json=registros)
            except Exception as e:
                st.session_state["tutoria_feedback"] = {
                    "tipo": "warning",
                    "msg": (
                        f"{len(inseridos)} estudante(s) foram salvos localmente para {tutor_destino}, "
                        f"mas a sincronização com o Supabase falhou. {mensagem_erro_tutoria_supabase(e)}"
                    )
                }

        return len(inseridos)

    st.markdown("---")
    st.subheader("📝 Cadastro em Lista por Responsável")
    st.caption("Escolha o responsável e cole a lista inteira, como na eletiva.")

    validacao_anterior = st.session_state.get("tutoria_validacao_ultimo")
    if validacao_anterior:
        with st.expander("🔎 Validação da última lista enviada", expanded=True):
            st.caption(f"Responsável: {validacao_anterior.get('responsavel', '')}")
            encontrados_df = pd.DataFrame(validacao_anterior.get("encontrados", []))
            pendentes_df = pd.DataFrame(validacao_anterior.get("pendentes", []))
            if not encontrados_df.empty:
                st.success(f"{len(encontrados_df)} estudante(s) encontrados no Supabase e validados pela turma/nome aproximado.")
                st.dataframe(encontrados_df, use_container_width=True, hide_index=True)
            if not pendentes_df.empty:
                st.warning(f"{len(pendentes_df)} estudante(s) precisam de conferência manual.")
                st.dataframe(pendentes_df, use_container_width=True, hide_index=True)

                pendentes_raw = validacao_anterior.get("pendentes_raw", []) or []
                selecoes_manuais = []
                if pendentes_raw:
                    st.markdown("**Selecionar manualmente estudantes não encontrados**")
                    st.caption("Escolha uma sugestão apenas quando tiver certeza de que corresponde ao estudante digitado.")
                    for idx, pend in enumerate(pendentes_raw):
                        sugestoes = pend.get("sugestoes", []) or []
                        if not sugestoes:
                            st.info(f"Sem sugestão próxima para: {pend.get('nome', '')} ({pend.get('serie', '')})")
                            continue

                        opcoes = ["Não adicionar"]
                        mapa_sugestoes = {"Não adicionar": None}
                        for s in sugestoes:
                            confianca = round(float(s.get("score", 0) or 0) * 100)
                            label = f"{s.get('nome', '')} — {s.get('serie', '')} — RA {s.get('ra', '')} — {confianca}%"
                            opcoes.append(label)
                            mapa_sugestoes[label] = {
                                "nome": s.get("nome", ""),
                                "serie": s.get("serie", ""),
                                "ra": s.get("ra", ""),
                            }

                        escolha = st.selectbox(
                            f"{pend.get('nome', '')} ({pend.get('serie', '')})",
                            opcoes,
                            key=f"tutoria_conferencia_manual_{idx}_{gerar_chave_segura(pend.get('nome', ''))}"
                        )
                        if mapa_sugestoes.get(escolha):
                            selecoes_manuais.append(mapa_sugestoes[escolha])

                    if st.button("✅ Adicionar selecionados manualmente", key="tutoria_btn_add_conferencia_manual", type="primary"):
                        if not selecoes_manuais:
                            st.warning("Nenhuma sugestão foi selecionada para adicionar.")
                        else:
                            qtd_manual = _adicionar_estudantes_tutoria(
                                selecoes_manuais,
                                origem="conferencia_manual",
                                tutor_destino=validacao_anterior.get("responsavel", tutor_sel)
                            )
                            if qtd_manual > 0:
                                st.success(f"{qtd_manual} estudante(s) adicionados por conferência manual.")
                                st.rerun()
                            else:
                                st.warning("Os estudantes selecionados já estavam na lista ou não puderam ser adicionados.")
            if st.button("Limpar validação exibida", key="tutoria_limpar_validacao_ultimo"):
                st.session_state.pop("tutoria_validacao_ultimo", None)
                st.rerun()
    col_lista1, col_lista2 = st.columns([2, 1])
    with col_lista1:
        # Campo somente informativo.
        # Nao usar st.text_input com key fixa aqui, porque o Streamlit preserva
        # o valor antigo e pode mostrar outro responsavel.
        st.markdown("<div style='font-size:0.82rem;font-weight:700;color:#54467a;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.25rem;'>Responsável da lista</div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="
                background:#ffffff;
                border:1px solid rgba(148,163,184,0.30);
                border-radius:18px;
                padding:0.72rem 0.95rem;
                min-height:44px;
                color:#2b2140;
                box-shadow:0 10px 22px rgba(15,23,42,0.05);
            ">{html.escape(str(tutor_sel))}</div>
            """,
            unsafe_allow_html=True
        )
        tutor_lista_lote = tutor_sel
    with col_lista2:
        serie_padrao_lote = st.text_input(
            "Turma padrão",
            key="tutoria_serie_padrao_lote",
            placeholder="Ex: 6º Ano A"
        )
    lista_lote = st.text_area(
        "Cole a lista para esse responsável. Opcional: Nome;Turma",
        key="tutoria_lista_lote_professor",
        height=160,
        placeholder="Maria Silva; 7A\nJoão Santos; 8B\nAna Souza"
    )
    if st.button("✅ Registrar Lista do Responsável", key="tutoria_btn_lista_lote_professor", type="primary"):
        try:
            novos = []
            for linha in lista_lote.splitlines():
                item = _normalizar_linha_lista_tutoria(linha, serie_padrao=serie_padrao_lote)
                if item:
                    novos.append(item)
            qtd = _adicionar_estudantes_tutoria(novos, origem="lista_por_professor", tutor_destino=tutor_lista_lote)
            if qtd > 0:
                st.success(f"{qtd} estudante(s) adicionados para {tutor_lista_lote}.")
                st.rerun()
            else:
                st.warning("Nenhum estudante novo válido foi encontrado nessa lista.")
        except Exception as e:
            st.error(f"Erro ao registrar lista do responsável: {e}")

    # ======================================================
    # TUTORIA - INSERIR ESTUDANTES
    # Objetivo: buscar estudantes ativos do Supabase por nome e/ou sala,
    # montar uma lista temporaria, permitir remover itens e salvar somente
    # quando o usuario confirmar.
    # ======================================================
    st.markdown("---")
    st.subheader("➕ Inserir Estudantes na Tutoria")
    st.caption("Busque por estudante, por sala ou pelos dois. Adicione na lista temporária, confira e depois salve.")

    chave_lista_temp = f"tutoria_lista_temp_{gerar_chave_segura(tutor_sel)}"
    if chave_lista_temp not in st.session_state:
        st.session_state[chave_lista_temp] = []

    def _chave_aluno_temp(item: dict) -> str:
        ra = "".join(ch for ch in str(item.get("ra", "")) if ch.isdigit())
        nome = normalizar_texto(item.get("nome", ""))
        turma = normalizar_texto(formatar_turma_eletiva(item.get("serie", item.get("turma", ""))))
        return f"RA:{ra}" if ra else f"NOME:{nome}|TURMA:{turma}"

    def _adicionar_na_lista_temp(itens: list[dict]) -> int:
        existentes = {_chave_aluno_temp(item) for item in st.session_state[chave_lista_temp]}
        adicionados = 0
        bloqueados = []
        for item in itens or []:
            nome = str(item.get("nome", "")).strip()
            turma = formatar_turma_eletiva(str(item.get("serie", item.get("turma", ""))).strip())
            ra = "".join(ch for ch in str(item.get("ra", "")) if ch.isdigit())
            if not nome:
                continue
            novo = {"nome": nome, "serie": turma, "ra": ra}
            ja_tem, vinculos = _estudante_ja_tem_tutor(novo, TUTORIA)
            if ja_tem:
                bloqueados.append({
                    "nome": nome,
                    "serie": turma,
                    "ra": ra,
                    "tutores": ", ".join(sorted({v.get("tutor", "") for v in vinculos if v.get("tutor", "")})),
                })
                continue
            chave = _chave_aluno_temp(novo)
            if chave in existentes:
                continue
            st.session_state[chave_lista_temp].append(novo)
            existentes.add(chave)
            adicionados += 1
        if bloqueados:
            st.session_state["tutoria_bloqueados_temp"] = bloqueados
            st.warning(
                "Estudantes não adicionados porque já estão em outra lista: "
                + ", ".join([f"{b['nome']} ({b['serie']}) — {b['tutores']}" for b in bloqueados[:10]])
            )
        return adicionados

    # ------------------------------------------------------
    # 1) Busca no cadastro oficial de alunos ativos
    # ------------------------------------------------------
    st.markdown("#### 🔎 Buscar no cadastro oficial")
    if df_alunos.empty:
        st.info("Não há alunos carregados do Supabase para buscar.")
    else:
        base_busca = preparar_base_alunos_ativos_tutoria(df_alunos).copy()
        if base_busca.empty:
            st.warning("Nenhum estudante ativo foi encontrado na tabela de alunos.")
        else:
            base_busca["nome"] = base_busca["nome"].astype(str)
            if "turma" not in base_busca.columns:
                base_busca["turma"] = ""
            base_busca["turma"] = base_busca["turma"].astype(str)
            base_busca["turma_padrao"] = base_busca["turma"].apply(formatar_turma_eletiva)

            turmas_opcoes = sorted([t for t in base_busca["turma_padrao"].dropna().unique().tolist() if str(t).strip()])
            col_busca_nome, col_busca_turma = st.columns([2, 1])
            with col_busca_nome:
                termo_busca = st.text_input(
                    "Buscar estudante por nome",
                    key="tutoria_busca_nome_cadastro",
                    placeholder="Ex: Jameson, Henzo, Alice"
                )
            with col_busca_turma:
                filtro_turma_busca = st.selectbox(
                    "Buscar por sala/turma",
                    ["Todas"] + turmas_opcoes,
                    key="tutoria_busca_turma_cadastro"
                )

            df_resultado = base_busca.copy()
            if filtro_turma_busca != "Todas":
                df_resultado = df_resultado[df_resultado["turma_padrao"] == filtro_turma_busca]

            if termo_busca.strip():
                termo_norm = normalizar_texto(termo_busca)
                try:
                    termo_fon = normalizar_nome_fonetico(termo_busca)
                except Exception:
                    termo_fon = termo_norm

                def _combina_nome_busca(nome):
                    nome_norm = normalizar_texto(nome)
                    try:
                        nome_fon = normalizar_nome_fonetico(nome)
                    except Exception:
                        nome_fon = nome_norm
                    return (
                        termo_norm in nome_norm
                        or termo_fon in nome_fon
                        or SequenceMatcher(None, termo_norm, nome_norm).ratio() >= 0.55
                        or SequenceMatcher(None, termo_fon, nome_fon).ratio() >= 0.55
                    )

                df_resultado = df_resultado[df_resultado["nome"].apply(_combina_nome_busca)]

            df_resultado = df_resultado.drop_duplicates(subset=["nome", "turma_padrao", "ra"])

            if not df_resultado.empty:
                def _linha_disponivel_para_tutoria(linha):
                    candidato = {
                        "nome": linha.get("nome", ""),
                        "serie": linha.get("turma_padrao", linha.get("turma", "")),
                        "ra": linha.get("ra", ""),
                    }
                    ja_tem, _ = _estudante_ja_tem_tutor(candidato, TUTORIA)
                    return not ja_tem

                total_antes_disponibilidade = len(df_resultado)
                df_resultado = df_resultado[df_resultado.apply(_linha_disponivel_para_tutoria, axis=1)]
                total_ocultos = total_antes_disponibilidade - len(df_resultado)
                if total_ocultos > 0:
                    st.info(f"{total_ocultos} estudante(s) foram ocultados porque já possuem tutor em outra lista.")

            df_resultado = df_resultado.head(80)

            mapa_opcoes = {}
            opcoes = []
            for _, linha in df_resultado.iterrows():
                nome = str(linha.get("nome", "")).strip()
                turma = formatar_turma_eletiva(str(linha.get("turma_padrao", linha.get("turma", ""))).strip())
                ra = "".join(ch for ch in str(linha.get("ra", "")) if ch.isdigit())
                label = f"{nome} — {turma}" if turma else nome
                if ra:
                    label = f"{label} — RA {ra}"
                opcoes.append(label)
                mapa_opcoes[label] = {"nome": nome, "serie": turma, "ra": ra}

            selecionados = st.multiselect(
                "Selecione estudantes para inserir na lista temporária",
                opcoes,
                key="tutoria_busca_cadastro_selecionados"
            )

            col_add1, col_add2 = st.columns([1, 2])
            with col_add1:
                if st.button("➕ Adicionar selecionados", key="tutoria_btn_temp_add_busca", type="primary", use_container_width=True):
                    qtd_add = _adicionar_na_lista_temp([mapa_opcoes[item] for item in selecionados])
                    if qtd_add:
                        st.success(f"{qtd_add} estudante(s) adicionados à lista temporária.")
                    else:
                        st.info("Nenhum estudante novo foi adicionado à lista temporária.")
            with col_add2:
                st.caption(f"Resultados exibidos: {len(df_resultado)} | Na lista temporária: {len(st.session_state[chave_lista_temp])}")

    # ------------------------------------------------------
    # 2) Colar lista quando houver relacao pronta
    # ------------------------------------------------------
    with st.expander("📋 Colar lista pronta para adicionar à lista temporária", expanded=False):
        st.caption("Aceita formatos como: '1 Alice Elizabete 9 A', 'Alice Elizabete;9A' ou 'Alice Elizabete 9º A'.")
        serie_padrao = st.text_input("Turma padrão opcional", key="tutoria_temp_serie_padrao", placeholder="Ex: 9º A")
        lista_colada = st.text_area(
            "Cole a lista aqui",
            key="tutoria_temp_lista_colada",
            height=150,
            placeholder="1 Alice Elizabete 9 A\n2 Allana 9A\n3 Emanuelle 9B"
        )
        if st.button("➕ Adicionar lista colada", key="tutoria_btn_temp_add_colada", use_container_width=True):
            novos = []
            for linha in lista_colada.splitlines():
                item = _normalizar_linha_lista_tutoria(linha, serie_padrao=serie_padrao)
                if item:
                    encontrado = buscar_estudante_ativo_mais_proximo(item.get("nome", ""), item.get("serie", ""), df_alunos)
                    novos.append(encontrado if encontrado else item)
            qtd_add = _adicionar_na_lista_temp(novos)
            if qtd_add:
                st.success(f"{qtd_add} estudante(s) adicionados à lista temporária.")
            else:
                st.warning("Nenhum estudante novo foi adicionado. Verifique se já estão na lista ou se os dados estão vazios.")

    # ------------------------------------------------------
    # 3) Lista temporaria com opcao de remover antes de salvar
    # ------------------------------------------------------
    st.markdown("#### 📌 Lista temporária para salvar")
    lista_temp = st.session_state[chave_lista_temp]
    if not lista_temp:
        st.info("Nenhum estudante na lista temporária. Busque por nome/sala ou cole uma lista para começar.")
    else:
        df_temp = pd.DataFrame(lista_temp)
        if "serie" in df_temp.columns:
            df_temp["serie"] = df_temp["serie"].apply(formatar_turma_eletiva)
        st.dataframe(
            df_temp.rename(columns={"nome": "Estudante", "serie": "Turma", "ra": "RA"}),
            use_container_width=True,
            hide_index=True
        )

        remover_opcoes = []
        remover_mapa = {}
        for idx, item in enumerate(lista_temp):
            label = f"{idx + 1}. {item.get('nome', '')} — {formatar_turma_eletiva(item.get('serie', ''))}"
            remover_opcoes.append(label)
            remover_mapa[label] = idx

        col_remover, col_limpar = st.columns([2, 1])
        with col_remover:
            itens_remover = st.multiselect("Selecionar estudantes para remover da lista temporária", remover_opcoes, key="tutoria_temp_remover")
            if st.button("➖ Remover selecionados", key="tutoria_btn_temp_remover", use_container_width=True):
                indices = sorted([remover_mapa[item] for item in itens_remover], reverse=True)
                for idx in indices:
                    if 0 <= idx < len(st.session_state[chave_lista_temp]):
                        st.session_state[chave_lista_temp].pop(idx)
                st.rerun()
        with col_limpar:
            st.write("")
            st.write("")
            if st.button("🧹 Limpar lista", key="tutoria_btn_temp_limpar", use_container_width=True):
                st.session_state[chave_lista_temp] = []
                st.rerun()

    # ------------------------------------------------------
    # 4) Botao principal de salvamento
    # ------------------------------------------------------
    if st.button("💾 Salvar lista na tutoria", key="tutoria_btn_temp_salvar", type="primary", use_container_width=True):
        if not st.session_state[chave_lista_temp]:
            st.warning("Adicione pelo menos um estudante antes de salvar.")
        else:
            try:
                qtd = _adicionar_estudantes_tutoria(
                    st.session_state[chave_lista_temp],
                    origem="busca_por_nome_sala",
                    tutor_destino=tutor_sel
                )
                if qtd > 0:
                    st.session_state[chave_lista_temp] = []
                    st.success(f"{qtd} estudante(s) salvos na lista de {tutor_sel}.")
                    st.rerun()
                else:
                    st.info("Nenhum estudante novo foi salvo. Eles podem já estar na lista do responsável.")
            except Exception as e:
                st.error(f"Erro ao salvar lista na tutoria: {e}")

    df_tutoria = montar_dataframe_tutoria(tutor_sel, df_alunos, TUTORIA)
    total = len(df_tutoria)
    if not df_tutoria.empty and "Status" in df_tutoria.columns:
        encontrados = len(df_tutoria[df_tutoria["Status"] == "Encontrado"])
        nao_encontrados = len(df_tutoria[df_tutoria["Status"] == "Não encontrado"])
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

    busca_nome = st.text_input("🔍 Buscar estudante na tutoria", placeholder="Digite parte do nome", key="tutoria_busca_estudante")
    filtro_status = st.selectbox("Filtrar por status", ["Todos", "Encontrado", "Não encontrado"], key="tutoria_filtro_status")
    df_view = df_tutoria.copy()
    if busca_nome:
        df_view = df_view[df_view["Nome"].str.contains(busca_nome, case=False, na=False)]
    if filtro_status != "Todos":
        df_view = df_view[df_view["Status"] == filtro_status]

    st.markdown("---")
    st.subheader("📋 Estudantes da Tutoria")
    colunas_visiveis = [
        "Professor(a)", "Nome", "Turma", "Espaço", "Horário", "Dia",
        "Aluno Cadastrado", "RA", "Turma no Sistema", "Situação", "Status"
    ]
    colunas_visiveis = [c for c in colunas_visiveis if c in df_view.columns]
    st.dataframe(df_view[colunas_visiveis], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🖨️ Imprimir Lista da Tutoria")
    modo_impressao = st.radio("Tipo de impressão", ["Por Professor(a)", "Por Turma"], horizontal=True, key="tutoria_modo_impressao")

    if modo_impressao == "Por Professor(a)":
        tutores_lista = sorted(TUTORIA.keys())
        tutor_impressao = st.selectbox(
            "Professor(a) para imprimir",
            tutores_lista,
            index=tutores_lista.index(tutor_sel) if tutor_sel in tutores_lista else 0,
            key="tutoria_tutor_impressao"
        )
        df_imp = montar_dataframe_tutoria(tutor_impressao, df_alunos, TUTORIA)
        if st.button("Gerar PDF por Professor(a)", type="primary", key="btn_pdf_tutoria_tutor"):
            if df_imp.empty:
                st.warning("Não há estudantes para imprimir nesse professor(a).")
            else:
                pdf = gerar_pdf_tutoria(f"Professor(a): {tutor_impressao}", df_imp)
                st.download_button(
                    "Baixar PDF",
                    data=pdf,
                    file_name=f"Tutoria_Tutor_{gerar_chave_segura(tutor_impressao)}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    key="download_pdf_tutoria_tutor"
                )
    else:
        frames = []
        for tutor_item in sorted(TUTORIA.keys()):
            df_tmp = montar_dataframe_tutoria(tutor_item, df_alunos, TUTORIA)
            if not df_tmp.empty:
                frames.append(df_tmp)
        df_geral_tutoria = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        turmas_tutoria = sorted([t for t in df_geral_tutoria.get("Turma", pd.Series(dtype=str)).dropna().astype(str).str.strip().unique().tolist() if t])
        if not turmas_tutoria:
            st.info("Não há turmas de tutoria para imprimir.")
        else:
            turma_impressao = st.selectbox("Turma da Tutoria", turmas_tutoria, key="tutoria_turma_impressao")
            df_imp = df_geral_tutoria[df_geral_tutoria["Turma"].astype(str).str.strip() == str(turma_impressao).strip()].copy()
            if st.button("Gerar PDF por Turma", type="primary", key="btn_pdf_tutoria_turma"):
                if df_imp.empty:
                    st.warning("Não há estudantes para imprimir nessa turma.")
                else:
                    pdf = gerar_pdf_tutoria(f"Turma: {turma_impressao}", df_imp)
                    st.download_button(
                        "Baixar PDF",
                        data=pdf,
                        file_name=f"Tutoria_Turma_{gerar_chave_segura(turma_impressao)}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        key="download_pdf_tutoria_turma"
                    )

    st.markdown("---")
    st.subheader("🔎 Estudantes Sem Tutor")
    st.caption("Mostra estudantes ativos do Supabase que ainda não aparecem em nenhuma lista de tutoria. É possível ver no geral ou por sala.")

    if not df_alunos.empty and "nome" in df_alunos.columns and "turma" in df_alunos.columns:
        base_ativa_tutoria = preparar_base_alunos_ativos_tutoria(df_alunos)

        frames = []
        for tutor_item in sorted(TUTORIA.keys()):
            df_tmp = montar_dataframe_tutoria(tutor_item, df_alunos, TUTORIA)
            if not df_tmp.empty:
                frames.append(df_tmp)
        df_geral_tutoria = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

        vinculados = set()
        if not df_geral_tutoria.empty:
            df_vinc = df_geral_tutoria[
                (df_geral_tutoria["Status"] == "Encontrado")
                & (df_geral_tutoria["Aluno Cadastrado"].astype(str).str.strip() != "")
                & (df_geral_tutoria["Professor(a)"].astype(str).str.strip() != "")
            ].copy()
            for _, r in df_vinc.iterrows():
                ra_vinc = "".join(ch for ch in str(r.get("RA", "")) if ch.isdigit())
                if ra_vinc:
                    vinculados.add(("RA", ra_vinc))
                vinculados.add((
                    "NOME_TURMA",
                    normalizar_texto(r.get("Aluno Cadastrado", "")),
                    turma_para_comparacao(r.get("Turma no Sistema", ""))
                ))

        sem_tutor = []
        for _, aluno in base_ativa_tutoria.iterrows():
            ra = "".join(ch for ch in str(aluno.get("ra", "")) if ch.isdigit())
            chave_ra = ("RA", ra) if ra else None
            chave_nome_turma = (
                "NOME_TURMA",
                normalizar_texto(aluno.get("nome", "")),
                turma_para_comparacao(aluno.get("turma", ""))
            )
            if (chave_ra and chave_ra in vinculados) or chave_nome_turma in vinculados:
                continue

            turma_aluno = formatar_turma_eletiva(aluno.get("turma", ""))
            sem_tutor.append({
                "Nome": aluno.get("nome", ""),
                "Turma": turma_aluno,
                "Etapa": classificar_etapa_tutoria(turma_aluno),
                "Turno": classificar_turno_tutoria(turma_aluno),
                "RA": aluno.get("ra", ""),
                "Situação": aluno.get("situacao", aluno.get("situação", aluno.get("status", ""))),
            })

        df_sem_tutor = pd.DataFrame(sem_tutor)
        if not df_sem_tutor.empty:
            df_sem_tutor["ordem_turma"] = df_sem_tutor["Turma"].apply(ordenar_turma_tutoria)
            df_sem_tutor = df_sem_tutor.sort_values(["Turno", "ordem_turma", "Nome"]).drop(columns=["ordem_turma"]).reset_index(drop=True)

        total_ativos = len(base_ativa_tutoria)
        total_sem_tutor = len(df_sem_tutor)
        total_com_tutor = max(total_ativos - total_sem_tutor, 0)

        total_turno1 = int((df_sem_tutor["Turno"] == "Turno 1").sum()) if not df_sem_tutor.empty else 0
        total_turno2 = int((df_sem_tutor["Turno"] == "Turno 2").sum()) if not df_sem_tutor.empty else 0

        col_st1, col_st2, col_st3, col_st4, col_st5 = st.columns(5)
        col_st1.metric("Ativos no Supabase", total_ativos)
        col_st2.metric("Com tutor", total_com_tutor)
        col_st3.metric("Sem tutor", total_sem_tutor)
        col_st4.metric("Sem tutor - Turno 1", total_turno1)
        col_st5.metric("Sem tutor - Turno 2", total_turno2)

        aba_geral_sem_tutor, aba_turno_sem_tutor, aba_sala_sem_tutor = st.tabs(["📌 Geral", "🕒 Por turno/etapa", "🏫 Por sala"])

        with aba_geral_sem_tutor:
            if df_sem_tutor.empty:
                st.success("Todos os estudantes ativos já possuem tutor cadastrado.")
            else:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    filtro_turno_geral = st.selectbox(
                        "Filtrar por turno",
                        ["Todos"] + sorted(df_sem_tutor["Turno"].dropna().unique().tolist()),
                        key="sem_tutor_filtro_turno_geral"
                    )
                with col_f2:
                    filtro_etapa_geral = st.selectbox(
                        "Filtrar por etapa",
                        ["Todas"] + sorted(df_sem_tutor["Etapa"].dropna().unique().tolist()),
                        key="sem_tutor_filtro_etapa_geral"
                    )
                df_sem_tutor_exibir = df_sem_tutor.copy()
                if filtro_turno_geral != "Todos":
                    df_sem_tutor_exibir = df_sem_tutor_exibir[df_sem_tutor_exibir["Turno"] == filtro_turno_geral]
                if filtro_etapa_geral != "Todas":
                    df_sem_tutor_exibir = df_sem_tutor_exibir[df_sem_tutor_exibir["Etapa"] == filtro_etapa_geral]
                st.markdown(f"**Total exibido:** {len(df_sem_tutor_exibir)} estudante(s)")
                st.dataframe(df_sem_tutor_exibir, use_container_width=True, hide_index=True)
                csv_sem_tutor = df_sem_tutor_exibir.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "⬇️ Baixar lista geral em CSV",
                    data=csv_sem_tutor,
                    file_name=f"estudantes_sem_tutor_geral_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="download_sem_tutor_geral_csv"
                )

                pdf_sem_tutor_geral = gerar_pdf_estudantes_sem_tutor(
                    f"Geral | Turno: {filtro_turno_geral} | Etapa: {filtro_etapa_geral}",
                    df_sem_tutor_exibir
                )
                st.download_button(
                    "🖨️ Baixar lista geral em PDF",
                    data=pdf_sem_tutor_geral,
                    file_name=f"estudantes_sem_tutor_geral_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    key="download_sem_tutor_geral_pdf"
                )


        with aba_turno_sem_tutor:
            if df_sem_tutor.empty:
                st.success("Não há estudantes sem tutor para agrupar por turno.")
            else:
                resumo_turno = (
                    df_sem_tutor.groupby(["Turno", "Etapa"])
                    .size()
                    .reset_index(name="Sem tutor")
                    .sort_values(["Turno", "Etapa"])
                )
                st.dataframe(resumo_turno, use_container_width=True, hide_index=True)

                turno_sel = st.selectbox(
                    "Selecionar turno para detalhar",
                    ["Todos", "Turno 1", "Turno 2", "Sem turno definido"],
                    key="sem_tutor_turno_detalhe"
                )
                df_turno = df_sem_tutor if turno_sel == "Todos" else df_sem_tutor[df_sem_tutor["Turno"] == turno_sel]

                resumo_turma_turno = (
                    df_turno.groupby(["Turno", "Etapa", "Turma"])
                    .size()
                    .reset_index(name="Sem tutor")
                    .sort_values(["Turno", "Turma"])
                ) if not df_turno.empty else pd.DataFrame()

                st.markdown("**Resumo por turma dentro do turno selecionado:**")
                st.dataframe(resumo_turma_turno, use_container_width=True, hide_index=True)
                st.markdown(f"**Total no detalhe:** {len(df_turno)} estudante(s)")
                st.dataframe(df_turno, use_container_width=True, hide_index=True)

                csv_turno = df_turno.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "⬇️ Baixar turno selecionado em CSV",
                    data=csv_turno,
                    file_name=f"estudantes_sem_tutor_{gerar_chave_segura(turno_sel)}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="download_sem_tutor_turno_csv"
                )

                pdf_sem_tutor_turno = gerar_pdf_estudantes_sem_tutor(
                    f"Turno/Etapa | {turno_sel}",
                    df_turno
                )
                st.download_button(
                    "🖨️ Baixar turno selecionado em PDF",
                    data=pdf_sem_tutor_turno,
                    file_name=f"estudantes_sem_tutor_{gerar_chave_segura(turno_sel)}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    key="download_sem_tutor_turno_pdf"
                )

        with aba_sala_sem_tutor:
            if df_sem_tutor.empty:
                st.success("Não há estudantes sem tutor para agrupar por sala.")
            else:
                turmas_sem_tutor = sorted(df_sem_tutor["Turma"].dropna().astype(str).unique().tolist(), key=ordenar_turma_tutoria)
                turma_sem_tutor_sel = st.selectbox(
                    "Selecione a sala/turma",
                    options=["Todas"] + turmas_sem_tutor,
                    key="turma_sem_tutor_select"
                )

                resumo_sem_tutor = (
                    df_sem_tutor.groupby(["Turno", "Etapa", "Turma"])
                    .size()
                    .reset_index(name="Sem tutor")
                    .sort_values(["Turno", "Turma"])
                )
                st.dataframe(resumo_sem_tutor, use_container_width=True, hide_index=True)

                if turma_sem_tutor_sel == "Todas":
                    df_sala = df_sem_tutor
                else:
                    df_sala = df_sem_tutor[df_sem_tutor["Turma"] == turma_sem_tutor_sel]

                st.markdown(f"**Total exibido:** {len(df_sala)} estudante(s)")
                st.dataframe(df_sala, use_container_width=True, hide_index=True)

                csv_sala = df_sala.to_csv(index=False).encode("utf-8-sig")
                nome_arquivo_sala = gerar_chave_segura(turma_sem_tutor_sel) if turma_sem_tutor_sel != "Todas" else "TODAS"
                st.download_button(
                    "⬇️ Baixar sala selecionada em CSV",
                    data=csv_sala,
                    file_name=f"estudantes_sem_tutor_{nome_arquivo_sala}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="download_sem_tutor_sala_csv"
                )

                pdf_sem_tutor_sala = gerar_pdf_estudantes_sem_tutor(
                    f"Sala/Turma: {turma_sem_tutor_sel}",
                    df_sala
                )
                st.download_button(
                    "🖨️ Baixar sala selecionada em PDF",
                    data=pdf_sem_tutor_sala,
                    file_name=f"estudantes_sem_tutor_{nome_arquivo_sala}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    key="download_sem_tutor_sala_pdf"
                )
    else:
        st.info("Para mostrar estudantes sem tutor, a tabela de alunos precisa ter pelo menos as colunas nome e turma.")

    if alunos_raw:
        st.markdown("---")
        st.subheader("✏️ Editar ou Excluir Estudante")
        opcoes_estudantes = [f"{a.get('nome', '').strip()} — {a.get('serie', '').strip()}".strip(" —") for a in alunos_raw]
        idx_sel = st.selectbox(
            "Selecione o estudante",
            options=list(range(len(opcoes_estudantes))),
            format_func=lambda i: opcoes_estudantes[i],
            key="tutoria_idx_edicao"
        )

        estudante_sel = alunos_raw[idx_sel]
        nome_antigo = str(estudante_sel.get("nome", "")).strip()
        serie_antiga = str(estudante_sel.get("serie", "")).strip()
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            novo_nome = st.text_input("Nome", value=nome_antigo, key=f"tutoria_nome_edit_{idx_sel}")
        with col_ed2:
            nova_serie = st.text_input("Turma", value=serie_antiga, key=f"tutoria_serie_edit_{idx_sel}")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✅ Editar Estudante", type="primary", key="btn_editar_estudante_tutoria"):
                novo_nome = novo_nome.strip()
                nova_serie = formatar_turma_eletiva(nova_serie.strip())
                if not novo_nome:
                    st.warning("Informe um nome válido para salvar.")
                else:
                    try:
                        TUTORIA[tutor_sel]["alunos"][idx_sel] = {"nome": novo_nome, "serie": nova_serie}
                        _salvar_estado_tutoria("local")
                        if SUPABASE_VALID:
                            _apagar_registro_supabase_tutoria(tutor_sel, nome_antigo, serie_antiga)
                            _supabase_request("POST", "tutoria", json=[{
                                "professora": tutor_sel,
                                "nome_aluno": novo_nome,
                                "serie": nova_serie,
                                "origem": "edicao_manual"
                            }])
                        st.success("✅ Estudante atualizado com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao editar estudante: {e}")

        with col_btn2:
            confirmar_exc = st.checkbox("Confirmar exclusão", key=f"confirmar_exclusao_tutoria_{idx_sel}")
            if st.button("🗑️ Excluir Estudante", type="secondary", key="btn_excluir_estudante_tutoria"):
                if not confirmar_exc:
                    st.warning("Marque a confirmação para excluir.")
                else:
                    try:
                        removido = TUTORIA[tutor_sel]["alunos"].pop(idx_sel)
                        _salvar_estado_tutoria("local")
                        if SUPABASE_VALID:
                            _apagar_registro_supabase_tutoria(tutor_sel, str(removido.get("nome", "")), str(removido.get("serie", "")))
                        st.success("✅ Estudante excluído com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir estudante: {e}")

        st.markdown("---")
        st.subheader("🧹 Limpeza em Massa")
        confirmar_excluir_todos = st.checkbox(f"Confirmo excluir todos os estudantes do professor {tutor_sel}", key=f"confirmar_excluir_todos_tutoria_{gerar_chave_segura(tutor_sel)}")
        if st.button("🗑️ Excluir Todos os Alunos da Tutoria", type="secondary", key="btn_excluir_todos_tutoria"):
            if not confirmar_excluir_todos:
                st.warning("Marque a confirmação para excluir todos.")
            else:
                try:
                    TUTORIA[tutor_sel]["alunos"] = []
                    _salvar_estado_tutoria("local")
                    if SUPABASE_VALID:
                        tutor_q = requests.utils.quote(str(tutor_sel), safe="")
                        _supabase_request("DELETE", f"tutoria?professora=eq.{tutor_q}")
                    st.success("✅ Todos os estudantes da tutoria foram excluídos.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir todos os estudantes: {e}")

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

    def obter_indice_assento(fileira, carteira):
        return carteira * num_fileiras + fileira

    def construir_grade_mapa_impressao():
        grade = []
        for fileira in range(num_fileiras):
            linha = []
            for carteira in range(carteiras_por_fileira):
                idx = obter_indice_assento(fileira, carteira)
                nome = st.session_state[mapa_key].get(str(idx), "").strip()
                linha.append(nome if nome else f"Carteira {idx + 1}")
            grade.append(linha)
        return grade

    def renderizar_html_mapa_impressao(grade):
        html_mapa = [
            """
            <style>
            .mapa-impressao-wrap {
                margin-top: 1rem;
                padding: 1.2rem;
                border: 1px solid #d1d5db;
                border-radius: 16px;
                background: #ffffff;
            }
            .mapa-impressao-topo {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 1rem;
                margin-bottom: 1rem;
            }
            .mapa-impressao-lousa {
                flex: 0 1 42%;
                padding: 0.55rem 0.9rem;
                border-radius: 12px;
                background: #111827;
                color: #ffffff;
                text-align: center;
                font-weight: 700;
                letter-spacing: 0.04em;
            }
            .mapa-impressao-professor,
            .mapa-impressao-porta {
                min-width: 170px;
                padding: 0.7rem 1rem;
                border-radius: 12px;
                text-align: center;
                font-weight: 700;
            }
            .mapa-impressao-professor {
                background: #fef3c7;
                border: 1px solid #f59e0b;
                color: #92400e;
            }
            .mapa-impressao-porta {
                background: #dcfce7;
                border: 1px solid #22c55e;
                color: #166534;
            }
            .mapa-impressao-tabela {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
            }
            .mapa-impressao-tabela th,
            .mapa-impressao-tabela td {
                border: 1px solid #cbd5e1;
                padding: 0.75rem 0.5rem;
                text-align: center;
                vertical-align: middle;
            }
            .mapa-impressao-tabela th {
                background: #eff6ff;
                color: #1e3a8a;
                font-size: 0.9rem;
            }
            .mapa-impressao-tabela td {
                min-height: 72px;
                background: #f8fafc;
                color: #0f172a;
                font-size: 0.95rem;
                font-weight: 600;
                word-break: break-word;
            }
            .mapa-impressao-posicao {
                display: block;
                margin-bottom: 0.25rem;
                font-size: 0.72rem;
                font-weight: 700;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.03em;
            }
            </style>
            """
        ]

        if orientacao_lousa in ["Topo", "Esquerda"]:
            html_mapa.append(
                '<div class="mapa-impressao-topo"><div class="mapa-impressao-professor">MESA DO PROFESSOR</div><div class="mapa-impressao-lousa">LOUSA</div><div class="mapa-impressao-porta">PORTA</div></div>'
            )

        html_mapa.append('<div class="mapa-impressao-wrap"><table class="mapa-impressao-tabela">')
        html_mapa.append("<thead><tr><th>Carteira</th>")
        for carteira in range(carteiras_por_fileira):
            html_mapa.append(f"<th>Fileira {carteira + 1}</th>")
        html_mapa.append("</tr></thead><tbody>")

        for fileira, linha in enumerate(grade, start=1):
            html_mapa.append("<tr>")
            html_mapa.append(f"<th>Carteira {fileira}</th>")
            for carteira, valor in enumerate(linha, start=1):
                html_mapa.append(
                    f"<td><span class='mapa-impressao-posicao'>Carteira {fileira} - Fileira {carteira}</span>{html.escape(valor)}</td>"
                )
            html_mapa.append("</tr>")

        html_mapa.append("</tbody></table></div>")

        if orientacao_lousa in ["Fundo", "Direita"]:
            html_mapa.append(
                '<div class="mapa-impressao-topo"><div class="mapa-impressao-professor">MESA DO PROFESSOR</div><div class="mapa-impressao-lousa">LOUSA</div><div class="mapa-impressao-porta">PORTA</div></div>'
            )

        return "".join(html_mapa)

    def gerar_pdf_mapa_sala():
        grade = construir_grade_mapa_impressao()
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=1 * cm,
            rightMargin=1 * cm,
            topMargin=1 * cm,
            bottomMargin=1 * cm
        )

        estilos = getSampleStyleSheet()
        estilo_celula = ParagraphStyle(
            "MapaSalaCelula",
            parent=estilos["Normal"],
            alignment=TA_CENTER,
            fontSize=8,
            leading=10,
            spaceAfter=0,
            spaceBefore=0
        )

        elementos = [
            Paragraph(f"Mapa da Sala - Turma {turma_sel}", estilos["Heading1"]),
            Spacer(1, 0.2 * cm),
            Paragraph(
                f"Lousa: {orientacao_lousa} | Fileiras: {num_fileiras} | Carteiras por fileira: {carteiras_por_fileira}",
                estilos["Normal"]
            ),
            Spacer(1, 0.4 * cm),
        ]

        if orientacao_lousa in ["Topo", "Esquerda"]:
            elementos.append(
                Table(
                    [["MESA DO PROFESSOR", "LOUSA", "PORTA"]],
                    colWidths=[5.6 * cm, 14.2 * cm, 4.2 * cm],
                    style=TableStyle([
                        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#FEF3C7")),
                        ("TEXTCOLOR", (0, 0), (0, 0), colors.HexColor("#92400E")),
                        ("BOX", (0, 0), (0, 0), 1, colors.HexColor("#F59E0B")),
                        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#111827")),
                        ("TEXTCOLOR", (1, 0), (1, 0), colors.white),
                        ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#DCFCE7")),
                        ("TEXTCOLOR", (2, 0), (2, 0), colors.HexColor("#166534")),
                        ("BOX", (2, 0), (2, 0), 1, colors.HexColor("#22C55E")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ])
                )
            )
            elementos.append(Spacer(1, 0.25 * cm))

        dados_tabela = [["Carteira"] + [f"Fileira {i + 1}" for i in range(carteiras_por_fileira)]]
        for fileira, linha in enumerate(grade, start=1):
            linha_pdf = [Paragraph(f"<b>Carteira {fileira}</b>", estilo_celula)]
            for carteira, valor in enumerate(linha, start=1):
                conteudo = f"<b>Carteira {fileira} - Fileira {carteira}</b><br/>{html.escape(valor)}"
                linha_pdf.append(Paragraph(conteudo, estilo_celula))
            dados_tabela.append(linha_pdf)

        largura_coluna = 22.5 * cm / max(carteiras_por_fileira, 1)
        tabela = Table(dados_tabela, colWidths=[2.5 * cm] + [largura_coluna] * carteiras_por_fileira, repeatRows=1)
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DBEAFE")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#94A3B8")),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
            ("TOPPADDING", (0, 1), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 10),
        ]))
        elementos.append(tabela)

        if orientacao_lousa in ["Fundo", "Direita"]:
            elementos.append(Spacer(1, 0.25 * cm))
            elementos.append(
                Table(
                    [["MESA DO PROFESSOR", "LOUSA", "PORTA"]],
                    colWidths=[5.6 * cm, 14.2 * cm, 4.2 * cm],
                    style=TableStyle([
                        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#FEF3C7")),
                        ("TEXTCOLOR", (0, 0), (0, 0), colors.HexColor("#92400E")),
                        ("BOX", (0, 0), (0, 0), 1, colors.HexColor("#F59E0B")),
                        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#111827")),
                        ("TEXTCOLOR", (1, 0), (1, 0), colors.white),
                        ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#DCFCE7")),
                        ("TEXTCOLOR", (2, 0), (2, 0), colors.HexColor("#166534")),
                        ("BOX", (2, 0), (2, 0), 1, colors.HexColor("#22C55E")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ])
                )
            )

        elementos.append(Spacer(1, 0.3 * cm))
        elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilos["Normal"]))

        doc.build(elementos)
        buffer.seek(0)
        return buffer.getvalue()

    # CSS para os assentos
    st.markdown("""
    <style>
    .sala-grid {
        display: inline-flex;
        flex-direction: column;
        gap: 8px;
        margin: 20px 0;
        padding: 20px;
        background: var(--light);
        border-radius: var(--radius-xl);
        border: 1px solid var(--border);
    }
    .fileira-row {
        display: flex;
        gap: 8px;
        align-items: stretch;
    }
    .frente-sala-row {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-bottom: 4px;
    }
    .fileira-label,
    .carteira-header,
    .sala-corner,
    .sala-professor,
    .sala-porta {
        width: 82px;
        min-height: 40px;
        border: 2px solid var(--border);
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        font-size: 11px;
        font-weight: 700;
        background: #eff6ff;
        color: #1e3a8a;
        padding: 4px;
    }
    .fileira-label {
        background: #e2e8f0;
        color: #0f172a;
    }
    .sala-corner {
        background: transparent;
        border-style: dashed;
        color: #64748b;
    }
    .sala-professor {
        width: 172px;
        background: #fef3c7;
        border-color: #f59e0b;
        color: #92400e;
    }
    .sala-porta {
        width: 172px;
        background: #dcfce7;
        border-color: #22c55e;
        color: #166534;
    }
    .assento-card {
        width: 82px;
        min-height: 58px;
        border: 2px solid var(--border);
        border-radius: var(--radius-md);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-size: 9px;
        font-weight: bold;
        text-align: center;
        background: white;
        transition: all 0.2s;
        padding: 4px;
        word-break: break-word;
    }
    .assento-posicao {
        font-size: 8px;
        line-height: 1.1;
        color: inherit;
        opacity: 0.9;
    }
    .assento-nome {
        font-size: 10px;
        line-height: 1.15;
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
        flex: 0 1 320px;
        max-width: 320px;
        height: 30px;
        background: var(--dark);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        border-radius: var(--radius-md);
        margin: 0 auto;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🪑 Layout da Sala")

    if False and orientacao_lousa in ["Topo", "Esquerda"]:
        st.markdown('<div class="lousa">📚 LOUSA</div>', unsafe_allow_html=True)

    sala_html = '<div class="sala-grid">'
    sala_html += '<div class="frente-sala-row"><div class="sala-professor">Mesa do Professor</div><div class="lousa">📚 LOUSA</div><div class="sala-porta">Porta</div></div>'
    sala_html += '<div class="fileira-row"><div class="sala-corner">Mapa</div>'
    for carteira in range(carteiras_por_fileira):
        sala_html += f'<div class="carteira-header">Fileira {carteira + 1}</div>'
    sala_html += '</div>'
    for fileira in range(num_fileiras):
        sala_html += f'<div class="fileira-row"><div class="fileira-label">Carteira {fileira + 1}</div>'
        for carteira in range(carteiras_por_fileira):
            idx = obter_indice_assento(fileira, carteira)
            nome_no_assento = st.session_state[mapa_key].get(str(idx), "")
            if nome_no_assento:
                nome_exib = nome_no_assento.split()[0] if nome_no_assento else f"C{idx+1}"
                sala_html += f'<div class="assento-card ocupado" title="{nome_no_assento}"><span class="assento-posicao">Carteira {fileira + 1} • Fileira {carteira + 1}</span><span class="assento-nome">{nome_exib}</span></div>'
            else:
                sala_html += f'<div class="assento-card vazio"><span class="assento-posicao">Carteira {fileira + 1} • Fileira {carteira + 1}</span><span class="assento-nome">Assento {idx + 1}</span></div>'
        sala_html += '</div>'
    sala_html += '</div>'
    st.markdown(sala_html, unsafe_allow_html=True)

    if False and orientacao_lousa in ["Fundo", "Direita"]:
        st.markdown('<div class="lousa">📚 LOUSA</div>', unsafe_allow_html=True)

    # Estatísticas
    st.markdown("---")
    st.subheader("Mapa para Impressao")
    grade_mapa_impressao = construir_grade_mapa_impressao()
    st.caption("Visualizacao com nomes completos para facilitar a leitura e a impressao da sala.")
    st.markdown(renderizar_html_mapa_impressao(grade_mapa_impressao), unsafe_allow_html=True)

    pdf_mapa = None
    try:
        pdf_mapa = gerar_pdf_mapa_sala()
        st.download_button(
            "Imprimir Mapa (PDF)",
            data=pdf_mapa,
            file_name=f"mapa_sala_{gerar_chave_segura(turma_sel)}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"download_mapa_pdf_{mapa_key}"
        )
    except Exception as e:
        st.error(f"Nao foi possivel gerar o PDF do mapa: {e}")

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
            idx = obter_indice_assento(fileira, carteira)
            
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

    col1, col2, col3, col4, col5 = st.columns(5)
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
    with col5:
        if pdf_mapa:
            st.download_button(
                "Imprimir Mapeamento",
                data=pdf_mapa,
                file_name=f"mapa_sala_{gerar_chave_segura(turma_sel)}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"download_mapa_pdf_tools_{mapa_key}"
            )

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
                        show_toast_agend("Preencha os campos obrigatórios.", "warning")
                    else:
                        horarios = [h for h in [horario1, horario2] if h]
                        # Evita tentativa duplicada na mesma submissão (ex.: 1ª e 2ª aulas iguais)
                        horarios = list(dict.fromkeys(horarios))
                        if not horarios:
                            st.error("⚠️ Selecione ao menos um horário válido.")
                            show_toast_agend("Selecione um horário válido.", "warning")
                        else:
                            professor_email = ""
                            if not df_prof_agend.empty and "email" in df_prof_agend.columns:
                                linha_prof = df_prof_agend[df_prof_agend["nome"] == professor]
                                if not linha_prof.empty:
                                    professor_email = str(linha_prof.iloc[0].get("email", "") or "").strip()

                            sucessos = 0
                            conflitos = 0
                            falhas = 0
                            detalhes_falha = []
                            
                            for h in horarios:
                                conf = verificar_conflito_api(data.strftime("%Y-%m-%d"), h, espaco)
                                if conf:
                                    conflitos += 1
                                else:
                                    ok, msg = salvar_agendamento_api({
                                        "data_agendamento": data.strftime("%Y-%m-%d"),
                                        "horario": h,
                                        "espaco": espaco,
                                        "turma": turma,
                                        "disciplina": disciplina,
                                    "prioridade": prioridade,
                                    "professor_nome": professor,
                                    "professor_email": professor_email,
                                    "status": "ATIVO"
                                })
                                    if ok:
                                        sucessos += 1
                                    else:
                                        falhas += 1
                                        detalhes_falha.append(f"{h}: {msg}")
                            
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
                            elif conflitos > 0 and falhas == 0:
                                st.error(f"❌ Não foi possível criar: {conflitos} horário(s) já ocupado(s) para este espaço/data.")
                                show_toast_agend("Horário já ocupado no espaço selecionado.", "error")
                            elif falhas > 0:
                                st.error("❌ Falha ao salvar no banco de dados.")
                                if detalhes_falha:
                                    st.caption("Detalhes: " + " | ".join(detalhes_falha[:3]))
                                show_toast_agend("Erro ao salvar agendamento.", "error")
                            else:
                                st.error("❌ Não foi possível criar o agendamento.")
                                show_toast_agend("Não foi possível criar o agendamento.", "error")
        
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
                                                "status": "ATIVO"
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

        st.markdown("---")
        st.subheader("🗓️ Grade do Dia por Espaço (7 Aulas)")
        data_grade_dia = st.date_input(
            "Data da grade diária:",
            datetime.now().date(),
            key="grade_dia_data_espacos"
        )
        horarios_grade_dia = [
            "07:00-07:50",
            "07:50-08:40",
            "09:00-09:50",
            "09:50-10:40",
            "10:40-11:30",
            "11:30-12:20",
            "12:20-13:10",
        ]

        if st.button("📊 Montar Grade do Dia", key="btn_grade_dia_espacos", type="primary", use_container_width=True):
            try:
                df_dia_espacos = carregar_agendamentos_filtrado(
                    data_grade_dia.strftime("%Y-%m-%d"),
                    data_grade_dia.strftime("%Y-%m-%d")
                )

                if not df_dia_espacos.empty and "status" in df_dia_espacos.columns:
                    df_dia_espacos = df_dia_espacos[df_dia_espacos["status"] == "ATIVO"]

                tabela_grade = []
                for horario in horarios_grade_dia:
                    linha = {"Horário": horario}
                    for espaco_grade in ESPACOS_AGEND:
                        if df_dia_espacos.empty:
                            linha[espaco_grade] = "🟢 Livre"
                            continue
                        slot = df_dia_espacos[
                            (df_dia_espacos["horario"] == horario) &
                            (df_dia_espacos["espaco"] == espaco_grade)
                        ]
                        if slot.empty:
                            linha[espaco_grade] = "🟢 Livre"
                        elif len(slot) > 1:
                            textos = []
                            for _, r in slot.iterrows():
                                textos.append(f"{r.get('turma', '')} | {r.get('disciplina', '')} | {r.get('professor_nome', '')}")
                            linha[espaco_grade] = "🟡 Parcial: " + " / ".join(textos)
                        else:
                            textos = []
                            for _, r in slot.iterrows():
                                textos.append(f"{r.get('turma', '')} | {r.get('disciplina', '')} | {r.get('professor_nome', '')}")
                            linha[espaco_grade] = "🔴 Ocupado: " + " / ".join(textos)
                    tabela_grade.append(linha)

                df_grade_dia = pd.DataFrame(tabela_grade)
                st.caption(f"Grade diária de {data_grade_dia.strftime('%d/%m/%Y')} para todos os espaços.")
                st.caption("Legenda: 🟢 Livre | 🟡 Parcial (mais de 1 lançamento no mesmo horário/espaço) | 🔴 Ocupado")
                st.markdown("""
                <style>
                .agenda-grid-board{border:1px solid rgba(196,181,253,.45);border-radius:16px;overflow:hidden;background:rgba(255,255,255,.6);margin:.4rem 0 1rem 0}
                .agenda-grid-head{display:grid;grid-template-columns:180px repeat(5,minmax(170px,1fr));background:linear-gradient(120deg,#f5f3ff,#eef2ff);border-bottom:1px solid rgba(196,181,253,.35)}
                .agenda-grid-row{display:grid;grid-template-columns:180px repeat(5,minmax(170px,1fr));border-top:1px solid rgba(226,232,240,.7)}
                .agenda-grid-cell{padding:.55rem .55rem;min-height:86px;border-left:1px solid rgba(226,232,240,.75);font-size:.78rem;color:#334155}
                .agenda-grid-cell:first-child{border-left:none}
                .agenda-grid-slot{background:#f8fafc;border:1px solid rgba(226,232,240,.85);border-radius:10px;padding:.45rem}
                .agenda-status{display:inline-block;font-size:.72rem;font-weight:800;padding:.1rem .45rem;border-radius:999px;margin-bottom:.25rem}
                .agenda-green{background:rgba(16,185,129,.16);color:#065f46}
                .agenda-yellow{background:rgba(245,158,11,.16);color:#92400e}
                .agenda-red{background:rgba(239,68,68,.16);color:#7f1d1d}
                .agenda-slot-line{font-size:.72rem;line-height:1.35}
                .agenda-slot-time{font-weight:800;color:#312e81}
                .agenda-slot-label{font-weight:800;color:#4c1d95}
                @media (max-width:1200px){
                  .agenda-grid-head,.agenda-grid-row{grid-template-columns:150px repeat(5,minmax(150px,1fr))}
                }
                </style>
                """, unsafe_allow_html=True)

                horarios_lista = horarios_grade_dia
                espacos_lista = ESPACOS_AGEND[:]
                board_html = ['<div class="agenda-grid-board">']
                board_html.append('<div class="agenda-grid-head">')
                board_html.append('<div class="agenda-grid-cell"><span class="agenda-slot-label">Horário / Aula</span></div>')
                for espaco_hdr in espacos_lista:
                    board_html.append(f'<div class="agenda-grid-cell"><span class="agenda-slot-label">{html.escape(str(espaco_hdr))}</span></div>')
                board_html.append('</div>')

                for idx, horario in enumerate(horarios_lista, start=1):
                    board_html.append('<div class="agenda-grid-row">')
                    board_html.append(
                        f'<div class="agenda-grid-cell"><div class="agenda-grid-slot"><div class="agenda-slot-label">{idx}ª Aula</div><div class="agenda-slot-time">{html.escape(horario)}</div></div></div>'
                    )
                    for espaco in espacos_lista:
                        slot = df_dia_espacos[
                            (df_dia_espacos["horario"] == horario) &
                            (df_dia_espacos["espaco"] == espaco)
                        ] if not df_dia_espacos.empty else pd.DataFrame()

                        if slot.empty:
                            cell = '<div class="agenda-grid-slot"><span class="agenda-status agenda-green">🟢 Livre</span></div>'
                        elif len(slot) > 1:
                            lines = []
                            for _, r in slot.iterrows():
                                t = html.escape(str(r.get("turma", "")))
                                d = html.escape(str(r.get("disciplina", "")))
                                p = html.escape(str(r.get("professor_nome", "")))
                                lines.append(f'<div class="agenda-slot-line">{t} | {d} | {p}</div>')
                            cell = '<div class="agenda-grid-slot"><span class="agenda-status agenda-yellow">🟡 Parcial</span>' + "".join(lines) + '</div>'
                        else:
                            r = slot.iloc[0]
                            t = html.escape(str(r.get("turma", "")))
                            d = html.escape(str(r.get("disciplina", "")))
                            p = html.escape(str(r.get("professor_nome", "")))
                            cell = (
                                '<div class="agenda-grid-slot"><span class="agenda-status agenda-red">🔴 Ocupado</span>'
                                f'<div class="agenda-slot-line">{t}</div>'
                                f'<div class="agenda-slot-line">{d}</div>'
                                f'<div class="agenda-slot-line">{p}</div>'
                                '</div>'
                            )
                        board_html.append(f'<div class="agenda-grid-cell">{cell}</div>')
                    board_html.append('</div>')
                board_html.append('</div>')
                st.markdown("".join(board_html), unsafe_allow_html=True)

                with st.expander("Ver Tabela Simples", expanded=False):
                    st.dataframe(df_grade_dia, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"❌ Erro ao montar grade do dia: {e}")
        
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
                
                try:
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
                        data_val = row.get('data_agendamento')
                        data_str = pd.to_datetime(data_val, errors='coerce')
                        data_fmt = data_str.strftime('%d/%m/%Y') if pd.notna(data_str) else ""
                        dados_tabela.append([
                            data_fmt,
                            str(row.get('horario', '')),
                            str(row.get('turma', '')),
                            str(row.get('professor_nome', '')),
                            str(row.get('disciplina', ''))
                        ])
                    
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
                        "🖨️ IMPRIMIR AGENDA (PDF)",
                        data=buffer.getvalue(),
                        file_name=f"agenda_{espaco_sel.replace(' ', '_')}_{data_ini.strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="download_imprimir_agenda_pdf"
                    )
                except Exception as e:
                    st.error(f"❌ Erro ao gerar PDF da agenda: {e}")
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
        
        with st.expander("âž• Cadastrar Professor", expanded=False):
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
else:
    page_header("Página não encontrada", "A página selecionada não possui um bloco de renderização ativo.", "#dc2626")
    st.error(f"Não foi possível exibir o conteúdo de: {menu}")
    st.caption(f"Chave normalizada da página: {menu_normalizado}")
    if st.button("Voltar para o Dashboard", type="primary", key="voltar_dashboard_fallback"):
        st.session_state.pagina_atual = "🏠 Dashboard"
        st.rerun()
