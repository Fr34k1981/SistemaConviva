# ======================================================
# IMPORTS PADRÃO
# ======================================================
import streamlit as st
import pandas as pd
import openpyxl
import plotly.express as px
import plotly.graph_objects as go
import random
from datetime import datetime, timedelta, time
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
import json
import tempfile

# ======================================================
# REPORTLAB (PDF)
# ======================================================
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ======================================================
# IMPORTS LOCAIS
# ======================================================
from src.backup_manager import BackupManager, render_backup_page
from src.error_handler import (
    com_tratamento_erro, com_retry, com_validacao,
    ErroConexaoDB, ErroValidacao, ErroCarregamentoDados,
    ErroOperacaoDB, Validadores, logger
)

# ======================================================
# VARIÁVEIS DE AMBIENTE
# ======================================================
load_dotenv()

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
# CONFIGURAÇÃO STREAMLIT
# ======================================================
st.set_page_config(
    page_title="Sistema Conviva 179 - E.E. Profª Eliane",
    layout="wide",
    page_icon="🏫",
    initial_sidebar_state="expanded"
)
# ======================================================
# CSS PREMIUM COMPLETO - DESIGN MODERNO E VIBRANTE
# ======================================================
st.markdown("""
<style>
/* ============================================ */
/* ========== VARIÁVEIS E FONTES ========== */
/* ============================================ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --primary: #6366f1;
    --primary-light: #818cf8;
    --primary-dark: #4f46e5;
    --secondary: #ec4899;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --info: #06b6d4;
    --dark: #1e293b;
    --gray: #64748b;
    --light: #f8fafc;
    --border: #e2e8f0;
    
    --gradient-primary: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
    --gradient-success: linear-gradient(135deg, #10b981 0%, #34d399 100%);
    --gradient-warning: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
    --gradient-danger: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
    --gradient-dark: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    --gradient-blue: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
    --gradient-purple: linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%);
    --gradient-orange: linear-gradient(135deg, #f97316 0%, #fbbf24 100%);
    --gradient-pink: linear-gradient(135deg, #ec4899 0%, #f472b6 100%);
    --gradient-teal: linear-gradient(135deg, #14b8a6 0%, #2dd4bf 100%);
    
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
    --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
    
    --radius-sm: 0.375rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;
    --radius-2xl: 1.5rem;
    --radius-3xl: 2rem;
}

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ============================================ */
/* ========== ANIMAÇÕES ========== */
/* ============================================ */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
    from { transform: translateX(-20px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.8; transform: scale(1.02); }
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-5px); }
}

.animate-fade-in {
    animation: fadeIn 0.5s ease-out;
}

.animate-slide-in {
    animation: slideIn 0.4s ease-out;
}

.animate-pulse {
    animation: pulse 2s infinite;
}

/* ============================================ */
/* ========== LAYOUT PRINCIPAL ========== */
/* ============================================ */
.main-header {
    background: var(--gradient-primary);
    padding: 2.5rem 2rem;
    border-radius: var(--radius-3xl);
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: var(--shadow-2xl);
    position: relative;
    overflow: hidden;
}

.main-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 400px;
    height: 400px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 50%;
    animation: pulse 4s infinite;
}

.main-header::after {
    content: '';
    position: absolute;
    bottom: -30%;
    left: -5%;
    width: 300px;
    height: 300px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 50%;
    animation: pulse 5s infinite reverse;
}

.school-name {
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 1;
    text-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.school-subtitle {
    font-size: 1.2rem;
    font-weight: 500;
    opacity: 0.95;
    margin-bottom: 1rem;
    position: relative;
    z-index: 1;
}

/* ============================================ */
/* ========== CARDS MODERNOS ========== */
/* ============================================ */
.card {
    background: white;
    padding: 1.5rem;
    border-radius: var(--radius-2xl);
    border: 1.5px solid var(--border);
    margin: 0.75rem 0;
    box-shadow: var(--shadow-sm);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--gradient-primary);
    opacity: 0;
    transition: opacity 0.3s;
}

.card:hover {
    box-shadow: var(--shadow-xl);
    transform: translateY(-3px);
    border-color: transparent;
}

.card:hover::before {
    opacity: 1;
}

.card-title {
    font-weight: 700;
    color: var(--dark);
    font-size: 1.125rem;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.card-value {
    font-size: 2rem;
    font-weight: 800;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
}

/* ============================================ */
/* ========== MÉTRICAS COLORIDAS ========== */
/* ============================================ */
.metric-card {
    padding: 1.75rem;
    border-radius: var(--radius-2xl);
    text-align: center;
    box-shadow: var(--shadow-lg);
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1.5px solid var(--border);
    position: relative;
    overflow: hidden;
    color: white;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200px;
    height: 200px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    transition: all 0.5s;
}

.metric-card:hover {
    box-shadow: var(--shadow-2xl);
    transform: translateY(-5px);
}

.metric-card:hover::before {
    top: -30%;
    right: -30%;
}

.metric-value {
    font-size: 2.75rem;
    font-weight: 800;
    line-height: 1.2;
    text-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.metric-label {
    font-size: 0.95rem;
    font-weight: 500;
    margin-top: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.9;
}

/* ============================================ */
/* ========== BOTÕES PREMIUM ========== */
/* ============================================ */
.stButton > button {
    border-radius: var(--radius-xl) !important;
    font-weight: 600 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    border: none !important;
    padding: 0.625rem 1.5rem !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.01em !important;
    position: relative;
    overflow: hidden;
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
}

.stButton > button:hover::before {
    width: 300px;
    height: 300px;
}

.stButton > button[kind="primary"] {
    background: var(--gradient-primary) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4) !important;
    transform: translateY(-2px);
}

.stButton > button[kind="secondary"] {
    background: white !important;
    color: var(--dark) !important;
    border: 1.5px solid var(--border) !important;
}

.stButton > button[kind="secondary"]:hover {
    background: var(--light) !important;
    border-color: var(--primary) !important;
    transform: translateY(-1px);
}

/* ============================================ */
/* ========== INPUTS MODERNOS ========== */
/* ============================================ */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select,
.stMultiSelect > div > div > div {
    border-radius: var(--radius-xl) !important;
    border: 1.5px solid var(--border) !important;
    transition: all 0.3s !important;
    padding: 0.625rem 1rem !important;
    font-size: 0.95rem !important;
    background: white !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1) !important;
    outline: none !important;
}

/* ============================================ */
/* ========== TABS ESTILIZADAS ========== */
/* ============================================ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: var(--light);
    padding: 0.5rem;
    border-radius: var(--radius-2xl);
    border: 1.5px solid var(--border);
}

.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-xl) !important;
    padding: 0.625rem 1.25rem !important;
    font-weight: 500 !important;
    color: var(--gray) !important;
    transition: all 0.3s !important;
    border: none !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab"]:hover {
    background: white !important;
    color: var(--primary) !important;
}

.stTabs [aria-selected="true"] {
    background: white !important;
    color: var(--primary) !important;
    font-weight: 600 !important;
    box-shadow: var(--shadow-md) !important;
}

/* ============================================ */
/* ========== SIDEBAR PREMIUM ========== */
/* ============================================ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border-right: 1.5px solid var(--border);
    box-shadow: var(--shadow-xl);
}

section[data-testid="stSidebar"] .stMarkdown h2 {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--dark);
    margin-bottom: 1rem;
    padding: 0 0.5rem;
}

/* ============================================ */
/* ========== DATAFRAME PREMIUM ========== */
/* ============================================ */
[data-testid="stDataFrame"] {
    border-radius: var(--radius-2xl) !important;
    overflow: hidden !important;
    border: 1.5px solid var(--border) !important;
    box-shadow: var(--shadow-md) !important;
}

[data-testid="stDataFrame"] th {
    background: var(--gradient-primary) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.75rem 1rem !important;
}

[data-testid="stDataFrame"] td {
    padding: 0.5rem 1rem !important;
    border-bottom: 1px solid var(--border) !important;
}

[data-testid="stDataFrame"] tr:hover td {
    background: linear-gradient(135deg, #f0f4ff, #ffffff) !important;
}

/* ============================================ */
/* ========== ALERTAS E MENSAGENS ========== */
/* ============================================ */
.success-box {
    background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
    border: 1.5px solid var(--success);
    border-radius: var(--radius-2xl);
    padding: 1.25rem;
    margin: 1.25rem 0;
    color: #065f46;
    font-weight: 500;
    box-shadow: var(--shadow-md);
    animation: slideIn 0.4s ease-out;
}

.warning-box {
    background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
    border: 1.5px solid var(--warning);
    border-radius: var(--radius-2xl);
    padding: 1.25rem;
    margin: 1.25rem 0;
    color: #92400e;
    font-weight: 500;
    box-shadow: var(--shadow-md);
}

.error-box {
    background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    border: 1.5px solid var(--danger);
    border-radius: var(--radius-2xl);
    padding: 1.25rem;
    margin: 1.25rem 0;
    color: #991b1b;
    font-weight: 500;
    box-shadow: var(--shadow-md);
}

.info-box {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 1.5px solid var(--primary);
    border-radius: var(--radius-2xl);
    padding: 1.25rem;
    margin: 1.25rem 0;
    color: #1e40af;
    font-weight: 500;
    box-shadow: var(--shadow-md);
}

.stAlert {
    border-radius: 16px !important;
    border-left-width: 5px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
    animation: slideIn 0.3s ease-out !important;
}

/* ============================================ */
/* ========== EXPANDER MODERNO ========== */
/* ============================================ */
div[data-testid="stExpander"] {
    border-radius: 16px !important;
    border: 1.5px solid var(--border) !important;
    background: white !important;
    box-shadow: var(--shadow-sm) !important;
    margin: 0.75rem 0 !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stExpander"]:hover {
    box-shadow: 0 6px 16px rgba(99, 102, 241, 0.12) !important;
    border-color: var(--primary) !important;
}

.streamlit-expanderHeader {
    border-radius: 16px !important;
    background: linear-gradient(135deg, #fafbfc, #ffffff) !important;
    font-weight: 600 !important;
    color: var(--dark) !important;
    padding: 0.75rem 1.25rem !important;
}

.streamlit-expanderHeader:hover {
    background: linear-gradient(135deg, #f0f4ff, #ffffff) !important;
}

/* ============================================ */
/* ========== FORMULÁRIOS PREMIUM ========== */
/* ============================================ */
div[data-testid="stForm"] {
    background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%) !important;
    border-radius: 20px !important;
    padding: 1.75rem !important;
    border: 1.5px solid var(--border) !important;
    box-shadow: 0 8px 20px rgba(0,0,0,0.06) !important;
    margin: 1.5rem 0 !important;
}

div[data-testid="stForm"]:hover {
    border-color: var(--primary) !important;
    box-shadow: 0 12px 28px rgba(99, 102, 241, 0.12) !important;
}

/* ============================================ */
/* ========== BADGES COLORIDOS ========== */
/* ============================================ */
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.badge-success { 
    background: linear-gradient(135deg, #d1fae5, #a7f3d0); 
    color: #065f46; 
}
.badge-warning { 
    background: linear-gradient(135deg, #fef3c7, #fde68a); 
    color: #92400e; 
}
.badge-danger { 
    background: linear-gradient(135deg, #fee2e2, #fecaca); 
    color: #991b1b; 
}
.badge-info { 
    background: linear-gradient(135deg, #dbeafe, #bfdbfe); 
    color: #1e40af; 
}
.badge-primary { 
    background: var(--gradient-primary); 
    color: white; 
}

/* ============================================ */
/* ========== SCROLLBAR PREMIUM ========== */
/* ============================================ */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--light);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
}

/* ============================================ */
/* ========== PROGRESS BAR ========== */
/* ============================================ */
.stProgress > div > div > div {
    background: var(--gradient-primary) !important;
    border-radius: 9999px !important;
}

/* ============================================ */
/* ========== MÉTRICAS STREAMLIT ========== */
/* ============================================ */
[data-testid="metric-container"] {
    background: white;
    border: 1.5px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 1rem;
    box-shadow: var(--shadow-sm);
    transition: all 0.3s;
}

[data-testid="metric-container"]:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--primary);
}

/* ============================================ */
/* ========== FOOTER ========== */
/* ============================================ */
footer {
    visibility: hidden;
}

#MainMenu {
    visibility: hidden;
}

/* ============================================ */
/* ========== UTILITÁRIOS ========== */
/* ============================================ */
.glass-effect {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1.5px solid rgba(255, 255, 255, 0.3);
}

.gradient-text {
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800;
}

.shimmer {
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
}

/* ============================================ */
/* ========== RESPONSIVO ========== */
/* ============================================ */
@media (max-width: 768px) {
    .main-header {
        padding: 1.5rem 1rem;
    }
    
    .school-name {
        font-size: 1.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
    }
    
    .metric-card {
        padding: 1.25rem;
    }
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
<div style="text-align: center; padding: 1.5rem 0.5rem;">
    <h2 style="background: linear-gradient(135deg, #6366f1, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 1.8rem; margin: 0;">🏫 Conviva 179</h2>
    <p style="color: #64748b; font-size: 0.85rem; margin-top: 0.25rem;">Gestão Escolar Inteligente</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Inicializar página atual se não existir
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = "🏠 Dashboard"

# Estilo CSS para os botões do menu
st.sidebar.markdown("""
<style>
/* Estilo para os botões do menu lateral */
div[data-testid="stVerticalBlock"] > div[data-testid="stButton"] {
    margin: 0.25rem 0;
}

div[data-testid="stVerticalBlock"] > div[data-testid="stButton"] > button {
    background: transparent !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.85rem 1rem !important;
    text-align: left !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    color: #475569 !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
    box-shadow: none !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.75rem !important;
}

div[data-testid="stVerticalBlock"] > div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(236, 72, 153, 0.1)) !important;
    color: #6366f1 !important;
    transform: translateX(5px) !important;
}

/* Botão ativo */
.menu-ativo {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
}
</style>
""", unsafe_allow_html=True)

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
    
    # Verificar se é a página ativa
    is_active = st.session_state.pagina_atual == nome_completo
    
    # Estilo do botão
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
<div style="padding: 1rem; background: linear-gradient(135deg, #f8fafc, #e2e8f0); border-radius: 12px; margin-top: 1rem;">
    <p style="margin: 0; font-size: 0.8rem; color: #64748b; text-align: center;">
        <b>🕐 {datetime.now().strftime('%d/%m/%Y')}</b><br>
        <span style="font-size: 0.75rem;">{datetime.now().strftime('%H:%M')}</span>
    </p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="text-align: center; margin-top: 1rem;">
    <p style="font-size: 0.7rem; color: #94a3b8;">v10.0 Premium</p>
</div>
""", unsafe_allow_html=True)

# ======================================================
# ELETIVAS — ARQUIVO DE IMPORTAÇÃO
# ======================================================
ELETIVAS_ARQUIVO = r"C:\Users\Freak Work\Desktop\IMportação.xlsx"

ELETIVAS = {
    "Solange": [], "Rosemeire": [], "Fernanda": [], "Fagna": [],
    "Elaine": [], "Geovana": [], "Shirley": [], "Rosangela": [],
    "Veronica": [], "Silvana": [], "Patricia": [],
}

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
# PROTOCOLO 179 COMPLETO (RESUMIDO PARA CABER)
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
        "SAIDA": ["SAIDA", "SAIR", "FUGIR", "EVADIR", "CABULAR"],
        "FALSIFICAR": ["FALSIFICAR", "ASSINATURA", "COLAR", "COPIAR"],
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
    
    # 1. Ocorrências graves nas últimas 24h
    if not df_ocorrencias.empty and 'data' in df_ocorrencias.columns:
        try:
            df_ocorrencias['data_dt'] = pd.to_datetime(df_ocorrencias['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_recentes = df_ocorrencias[df_ocorrencias['data_dt'] >= datetime.now() - timedelta(hours=24)]
            graves = df_recentes[df_recentes['gravidade'].isin(['Grave', 'Gravíssima'])]
            
            if not graves.empty:
                notificacoes.append({
                    "icone": "🚨",
                    "cor": "#ef4444",
                    "titulo": "Ocorrências Graves",
                    "texto": f"{len(graves)} ocorrências graves nas últimas 24h"
                })
        except:
            pass
    
    # 2. Alunos com muitas ocorrências (alerta de risco)
    if not df_ocorrencias.empty:
        try:
            df_ocorrencias['data_dt'] = pd.to_datetime(df_ocorrencias['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            ultimos_60_dias = df_ocorrencias[df_ocorrencias['data_dt'] >= datetime.now() - timedelta(days=60)]
            contagem = ultimos_60_dias['aluno'].value_counts()
            alunos_criticos = contagem[contagem >= 3].index.tolist()
            
            if alunos_criticos:
                notificacoes.append({
                    "icone": "⚠️",
                    "cor": "#f59e0b",
                    "titulo": "Alunos em Risco",
                    "texto": f"{len(alunos_criticos)} alunos com 3+ ocorrências em 60 dias"
                })
        except:
            pass
    
    # 3. Agendamentos para hoje
    try:
        hoje = datetime.now().strftime("%Y-%m-%d")
        df_hoje = carregar_agendamentos_filtrado(hoje, hoje)
        if not df_hoje.empty:
            notificacoes.append({
                "icone": "📅",
                "cor": "#3b82f6",
                "titulo": "Agendamentos Hoje",
                "texto": f"{len(df_hoje)} agendamentos para hoje"
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
                <div style="background: {n['cor']}10; 
                            border-left: 4px solid {n['cor']}; 
                            border-radius: 8px; 
                            padding: 0.75rem; 
                            margin: 0.5rem 0;">
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
            st.success("✅ Nenhuma notificação pendente")

            # ======================================================
# SISTEMA DE GAMIFICAÇÃO
# ======================================================

# Conquistas disponíveis
CONQUISTAS = {
    "primeiro_registro": {
        "nome": "🆕 Primeiro Registro",
        "descricao": "Registrou a primeira ocorrência",
        "pontos": 10,
        "icone": "🌟"
    },
    "10_ocorrencias": {
        "nome": "📝 Repórter Escolar",
        "descricao": "Registrou 10 ocorrências",
        "pontos": 50,
        "icone": "📋"
    },
    "50_ocorrencias": {
        "nome": "📊 Analista de Ocorrências",
        "descricao": "Registrou 50 ocorrências",
        "pontos": 100,
        "icone": "📈"
    },
    "turma_completa": {
        "nome": "🏫 Gestor de Turma",
        "descricao": "Cadastrou uma turma completa",
        "pontos": 30,
        "icone": "👥"
    },
    "agendamento_perfeito": {
        "nome": "📅 Organizador",
        "descricao": "Criou 5 agendamentos",
        "pontos": 20,
        "icone": "🗓️"
    },
    "backup_realizado": {
        "nome": "💾 Guardião dos Dados",
        "descricao": "Realizou backup do sistema",
        "pontos": 40,
        "icone": "🛡️"
    }
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
    st.session_state.pontos_usuario += pontes
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
    niveis = {
        1: "🌱 Iniciante",
        2: "📚 Aprendiz",
        3: "⭐ Experiente",
        4: "🏆 Mestre",
        5: "👑 Lendário"
    }
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
    
    with st.sidebar.expander(f"🏆 Nível {st.session_state.nivel_usuario} - {get_nivel_nome(st.session_state.nivel_usuario)}", expanded=False):
        pontos = st.session_state.pontos_usuario
        proximo_nivel = st.session_state.nivel_usuario * 100
        progresso = (pontos % 100) if pontos > 0 else 0
        
        st.markdown(f"""
        <div style="text-align: center; margin: 0.5rem 0;">
            <div style="font-size: 2rem;">{get_nivel_nome(st.session_state.nivel_usuario).split()[1]}</div>
            <div style="font-size: 1.5rem; font-weight: 700;">{pontos} pts</div>
            <div style="margin-top: 0.5rem; height: 8px; background: #e2e8f0; border-radius: 4px;">
                <div style="width: {progresso}%; height: 8px; background: linear-gradient(135deg, #6366f1, #ec4899); border-radius: 4px;"></div>
            </div>
            <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.25rem;">{progresso}/100 para próximo nível</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**🏅 Conquistas:**")
        if st.session_state.conquistas_usuario:
            for c_id in st.session_state.conquistas_usuario[:5]:
                if c_id in CONQUISTAS:
                    c = CONQUISTAS[c_id]
                    st.markdown(f"{c['icone']} {c['nome']}")
        else:
            st.caption("Continue usando o sistema para ganhar conquistas!")

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
        st.markdown("**Como posso ajudar?**")
        pergunta = st.text_input("Digite sua dúvida:", placeholder="Ex: Como registrar ocorrência?", key="assistente_input")
        
        if pergunta:
            resposta = assistente_virtual(pergunta)
            st.info(resposta)
        
        st.markdown("---")
        st.caption("💡 Dicas rápidas:")
        st.caption("• Use a busca inteligente nas ocorrências")
        st.caption("• Agendamentos fixos na Grade Semanal")
        st.caption("• Exporte relatórios em PDF ou Excel")

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
    """Atualiza o nome da turma para todos os alunos que pertencem a ela."""
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
            filtros += f"&professor_nome=eq.{professor}"
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
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["id","nome","email","cargo"])
        if not df.empty and 'cargo' in df.columns:
            df['status'] = 'ATIVO'
        return df
    except Exception:
        return pd.DataFrame(columns=["id","nome","email","cargo","status"])

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
    """
    Gera um PDF com a lista de estudantes da eletiva de uma professora
    """
    buffer = BytesIO()
    doc = _criar_documento_pdf(buffer)
    estilos = getSampleStyleSheet()
    elementos = []
    
    _adicionar_logo(elementos)
    
    # Título
    titulo_style = ParagraphStyle(
        'TituloEletiva',
        parent=estilos['Heading1'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=0.5*cm,
        textColor=colors.HexColor("#4A90E2")
    )
    elementos.append(Paragraph(f"LISTA DE ELETIVA", titulo_style))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Informações da professora
    elementos.append(Paragraph(f"<b>Professora:</b> {nome_professora}", estilos['Normal']))
    elementos.append(Paragraph(f"<b>Total de estudantes:</b> {len(df_eletiva)}", estilos['Normal']))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Tabela de estudantes
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
    
    tabela = Table(
        cabecalho + linhas,
        colWidths=[7*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm],
        repeatRows=1
    )
    
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4A90E2")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    for i in range(1, len(linhas) + 1):
        if i % 2 == 0:
            tabela.setStyle(TableStyle([
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor("#F5F5F5"))
            ]))
    
    elementos.append(tabela)
    elementos.append(Spacer(1, 0.5*cm))
    
    encontrados = len(df_eletiva[df_eletiva["Status"] == "Encontrado"])
    nao_encontrados = len(df_eletiva[df_eletiva["Status"] == "Não encontrado"])
    
    elementos.append(Paragraph(f"<b>Encontrados no sistema:</b> {encontrados}", estilos['Normal']))
    elementos.append(Paragraph(f"<b>Não encontrados:</b> {nao_encontrados}", estilos['Normal']))
    elementos.append(Spacer(1, 0.5*cm))
    
    estilo_rodape = ParagraphStyle(
        'Rodape',
        parent=estilos['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
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
        
        # ⭐ NOVOS PARA GAMIFICAÇÃO
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
# BACKUP AUTOMÁTICO
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
# PÁGINA 🏠 DASHBOARD - COMPLETO E COLORIDO
# ======================================================

if menu == "🏠 Dashboard":
    # Header Premium
    st.markdown(f"""
    <div class="main-header animate-fade-in">
        <div class="school-name">🏫 {ESCOLA_NOME}</div>
        <div class="school-subtitle">{ESCOLA_SUBTITULO}</div>
        <div style="margin-top: 1.5rem; display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
            <span style="display: flex; align-items: center; gap: 0.5rem;">📍 {ESCOLA_ENDERECO}</span>
            <span style="display: flex; align-items: center; gap: 0.5rem;">📞 {ESCOLA_TELEFONE}</span>
            <span style="display: flex; align-items: center; gap: 0.5rem;">✉️ {ESCOLA_EMAIL}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Cards de boas-vindas
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
        <div style="font-size: 2.5rem;">👋</div>
        <div>
            <h2 style="margin: 0; background: linear-gradient(135deg, #1e293b, #475569); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Bem-vindo ao Sistema Conviva 179!</h2>
            <p style="margin: 0; color: #64748b; font-size: 1.1rem;">Gerencie ocorrências, alunos e agendamentos de forma inteligente.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas Principais com cores vibrantes
    total_alunos = len(df_alunos) if not df_alunos.empty else 0
    total_ocorrencias = len(df_ocorrencias) if not df_ocorrencias.empty else 0
    total_professores = len(df_professores) if not df_professores.empty else 0
    
    if not df_alunos.empty and "situacao" in df_alunos.columns:
        df_alunos["situacao_norm"] = df_alunos["situacao"].str.strip().str.title()
        total_ativos = len(df_alunos[df_alunos["situacao_norm"] == "Ativo"])
        total_transferidos = len(df_alunos[df_alunos["situacao_norm"] == "Transferido"])
    else:
        total_ativos = total_alunos
        total_transferidos = 0
    
    # Cards coloridos
    st.markdown("### 📊 Visão Geral")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card animate-fade-in" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">👥</div>
            <div class="metric-value" style="color: white !important;">{total_alunos}</div>
            <div class="metric-label" style="color: rgba(255,255,255,0.9) !important;">Total de Alunos</div>
            <div style="margin-top: 0.5rem; color: #d1fae5; font-size: 0.85rem;">{total_ativos} ativos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        gravissimas = len(df_ocorrencias[df_ocorrencias["gravidade"] == "Gravíssima"]) if not df_ocorrencias.empty and "gravidade" in df_ocorrencias.columns else 0
        st.markdown(f"""
        <div class="metric-card animate-fade-in" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); animation-delay: 0.1s;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚠️</div>
            <div class="metric-value" style="color: white !important;">{total_ocorrencias}</div>
            <div class="metric-label" style="color: rgba(255,255,255,0.9) !important;">Ocorrências</div>
            <div style="margin-top: 0.5rem; color: #fee2e2; font-size: 0.85rem;">{gravissimas} gravíssimas</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card animate-fade-in" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); animation-delay: 0.2s;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">👨‍🏫</div>
            <div class="metric-value" style="color: white !important;">{total_professores}</div>
            <div class="metric-label" style="color: rgba(255,255,255,0.9) !important;">Professores</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card animate-fade-in" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); animation-delay: 0.3s;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
            <div class="metric-value" style="color: white !important;">{total_ativos}</div>
            <div class="metric-label" style="color: rgba(255,255,255,0.9) !important;">Alunos Ativos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card animate-fade-in" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); animation-delay: 0.4s;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔄</div>
            <div class="metric-value" style="color: white !important;">{total_transferidos}</div>
            <div class="metric-label" style="color: rgba(255,255,255,0.9) !important;">Transferidos</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Distribuição por Gravidade com cores vibrantes
    if not df_ocorrencias.empty and "gravidade" in df_ocorrencias.columns:
        st.markdown("---")
        st.markdown("### 📊 Distribuição de Ocorrências por Gravidade")
        
        col1, col2 = st.columns(2)
        
        with col1:
            contagem_grav = df_ocorrencias['gravidade'].value_counts()
            
            # Cards coloridos por gravidade
            gravidades = ['Leve', 'Média', 'Grave', 'Gravíssima']
            cores_grav = ['#10b981', '#f59e0b', '#f97316', '#ef4444']
            
            for grav, cor in zip(gravidades, cores_grav):
                qtd = contagem_grav.get(grav, 0)
                percent = (qtd / total_ocorrencias * 100) if total_ocorrencias > 0 else 0
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {cor}20, {cor}40); 
                            border-left: 4px solid {cor}; 
                            border-radius: 8px; 
                            padding: 0.75rem 1rem; 
                            margin: 0.5rem 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: {cor};">{grav}</span>
                        <span style="font-weight: 700; font-size: 1.25rem;">{qtd}</span>
                    </div>
                    <div style="margin-top: 0.25rem; height: 6px; background: #e2e8f0; border-radius: 3px;">
                        <div style="width: {percent}%; height: 6px; background: {cor}; border-radius: 3px;"></div>
                    </div>
                    <span style="font-size: 0.75rem; color: #64748b;">{percent:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            fig_grav = px.pie(
                values=contagem_grav.values,
                names=contagem_grav.index,
                title='Distribuição por Gravidade',
                color_discrete_sequence=['#10b981', '#f59e0b', '#f97316', '#ef4444'],
                hole=0.4
            )
            fig_grav.update_layout(
                font_family="Inter",
                title_font_size=16,
                legend_font_size=12,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            fig_grav.update_traces(textinfo='percent+label', textposition='inside')
            st.plotly_chart(fig_grav, use_container_width=True)
    
    # Top 10 Turmas com mais ocorrências
    if not df_ocorrencias.empty and "turma" in df_ocorrencias.columns:
        st.markdown("---")
        st.markdown("### 🏫 Top 10 Turmas com Mais Ocorrências")
        
        top_turmas = df_ocorrencias['turma'].value_counts().head(10)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_turmas = px.bar(
                x=top_turmas.values,
                y=top_turmas.index,
                orientation='h',
                title='Top 10 Turmas',
                color=top_turmas.values,
                color_continuous_scale='Blues',
                labels={'x': 'Quantidade de Ocorrências', 'y': 'Turma'}
            )
            fig_turmas.update_layout(
                font_family="Inter",
                title_font_size=16,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_turmas, use_container_width=True)
        
        with col2:
            st.markdown("#### 📋 Detalhes")
            for turma, qtd in top_turmas.items():
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #e0e7ff, #c7d2fe); 
                            border-radius: 8px; 
                            padding: 0.5rem 1rem; 
                            margin: 0.25rem 0;">
                    <b>{turma}</b>: {qtd} ocorrência(s)
                </div>
                """, unsafe_allow_html=True)
    
    # Top 10 Alunos com mais ocorrências
    if not df_ocorrencias.empty and "aluno" in df_ocorrencias.columns:
        st.markdown("---")
        st.markdown("### 🏆 Top 10 Alunos com Mais Ocorrências")
        
        top_alunos = df_ocorrencias['aluno'].value_counts().head(10)
        
        fig_alunos = px.bar(
            x=top_alunos.values,
            y=top_alunos.index,
            orientation='h',
            title='Top 10 Alunos',
            color=top_alunos.values,
            color_continuous_scale='Reds',
            labels={'x': 'Quantidade de Ocorrências', 'y': 'Aluno'}
        )
        fig_alunos.update_layout(
            font_family="Inter",
            title_font_size=16,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_alunos, use_container_width=True)
    
    # Resumo de ocorrências por categoria
    if not df_ocorrencias.empty and "categoria" in df_ocorrencias.columns:
        st.markdown("---")
        st.markdown("### 📌 Ocorrências por Categoria")
        
        categorias = df_ocorrencias['categoria'].value_counts().head(8)
        
        cols = st.columns(4)
        for i, (cat, qtd) in enumerate(categorias.items()):
            with cols[i % 4]:
                cores = ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#f5576c', '#00f2fe', '#38f9d7']
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {cores[i]}20, {cores[i]}40);
                            border: 1px solid {cores[i]};
                            border-radius: 12px;
                            padding: 1rem;
                            margin: 0.5rem 0;
                            text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: {cores[i]};">{qtd}</div>
                    <div style="font-size: 0.75rem; color: #475569; margin-top: 0.25rem;">{cat[:30]}...</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Ações Rápidas
    st.markdown("---")
    st.markdown("### ⚡ Ações Rápidas")
    
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
    
    st.markdown("---")
    st.info(f"📌 Fonte das eletivas: **{FONTE_ELETIVAS.upper()}** | 🗓️ Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            # ======================================================
# PÁGINA 📥 IMPORTAR ALUNOS
# ======================================================
# ======================================================
# PÁGINA 👨‍👩‍👧 PORTAL DO RESPONSÁVEL (COMPLETA)
# ======================================================

elif menu == "👨‍👩‍👧 Portal do Responsável":
    st.header("👨‍👩‍👧 Portal do Responsável")
    
    st.markdown("""
    <div class="info-box animate-fade-in">
        <h4 style="margin: 0 0 0.5rem 0;">🔐 Acesso Restrito</h4>
        <p style="margin: 0;">Digite o RA do aluno e a senha para acessar as informações.</p>
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
            # Buscar aluno
            aluno_encontrado = df_alunos[df_alunos['ra'].astype(str) == ra_acesso] if not df_alunos.empty else pd.DataFrame()
            
            if aluno_encontrado.empty:
                st.error("❌ Aluno não encontrado!")
            else:
                # Senha padrão para demonstração
                senha_correta = "123456"
                
                if senha_acesso != senha_correta:
                    st.error("❌ Senha incorreta!")
                else:
                    aluno = aluno_encontrado.iloc[0]
                    st.success(f"✅ Bem-vindo, responsável por **{aluno['nome']}**!")
                    
                    st.markdown("---")
                    
                    # Informações do aluno
                    st.subheader("📋 Informações do Aluno")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("RA", aluno['ra'])
                    with col2:
                        st.metric("Turma", aluno.get('turma', 'N/A'))
                    with col3:
                        st.metric("Situação", aluno.get('situacao', 'Ativo'))
                    
                    st.markdown("---")
                    
                    # Ocorrências do aluno
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
elif menu == "📥 Importar Alunos":
    st.header("📥 Importar Alunos por Turma")
    
    st.markdown("""
    <div class="info-box animate-fade-in">
        <h4 style="margin: 0 0 0.5rem 0;">💡 Como importar:</h4>
        <ol style="margin: 0; padding-left: 1.5rem;">
            <li>Digite o nome da turma (Ex: 6º Ano A, 1º Ano D)</li>
            <li>Selecione o arquivo CSV da SEDUC</li>
            <li>O sistema identificará automaticamente as colunas</li>
            <li>Clique em Importar Alunos</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    turma_alunos = st.text_input(
        "🏫 Nome da TURMA:",
        placeholder="Ex: 6º Ano B, 1º Ano D",
        key="turma_import"
    )
    
    arquivo_upload = st.file_uploader(
        "📁 Selecione o arquivo CSV da SEDUC",
        type=["csv"],
        key="arquivo_csv"
    )
    
    if arquivo_upload is not None:
        try:
            df_import = pd.read_csv(arquivo_upload, sep=';', encoding='utf-8-sig', dtype=str)
            
            st.success(f"✅ Arquivo lido! {len(df_import)} alunos encontrados.")
            
            st.write("### 👀 Pré-visualização dos dados:")
            st.dataframe(df_import.head(10), use_container_width=True)
            
            colunas = df_import.columns.tolist()
            
            # Identificação automática
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
            
            # Seleção manual se necessário
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
                            
                            aluno = {
                                'ra': ra_str,
                                'nome': nome_str,
                                'turma': turma_alunos,
                                'situacao': sit_str
                            }
                            
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
                        st.success(f"✅ Importação concluída com sucesso!")
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
    
    # Mostrar turmas existentes
    st.markdown("---")
    st.subheader("📊 Turmas cadastradas")
    if not df_alunos.empty:
        resumo = df_alunos.groupby('turma').size().reset_index(name='Total')
        resumo.columns = ['Turma', 'Total de Alunos']
        st.dataframe(resumo.sort_values('Turma'), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma turma cadastrada ainda.")
        # ======================================================
# PÁGINA 👥 LISTA DE ALUNOS (COM FILTRO ATIVO/TODOS)
# ======================================================

elif menu == "👥 Lista de Alunos":
    st.header("👥 Gerenciar Alunos")
    
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
            
            # Estatísticas
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
                                st.rerun()
                                # ======================================================
# PÁGINA 📋 GERENCIAR TURMAS
# ======================================================

elif menu == "📋 Gerenciar Turmas":
    st.header("📋 Gerenciar Turmas")

    if df_alunos.empty:
        st.info("📭 Nenhuma turma cadastrada. Use '📥 Importar Alunos' para começar.")
    else:
        st.subheader("📊 Resumo das Turmas")
        turmas_info = df_alunos.groupby("turma").agg(total_alunos=("ra", "count")).reset_index().sort_values("turma")

        for _, row in turmas_info.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                with col1:
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-title">🏫 {row['turma']}</div>
                        <div class="card-value">{row['total_alunos']} alunos</div>
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
            <div class="info-box">
                <h4 style="margin: 0 0 0.5rem 0;">💡 Instruções:</h4>
                <p style="margin: 0;">Envie o arquivo CSV da SEDUC para substituir todos os alunos desta turma.</p>
            </div>
            """, unsafe_allow_html=True)
            
            arquivo = st.file_uploader("Arquivo CSV", type=["csv"], key="substituir_csv")
            
            if arquivo is not None:
                try:
                    df_import = pd.read_csv(arquivo, sep=";", encoding="utf-8-sig", dtype=str)
                    st.success("✅ Arquivo carregado com sucesso.")
                    st.dataframe(df_import.head())
                    
                    colunas = df_import.columns.tolist()
                    
                    # Mapeamento automático
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
# PÁGINA 📝 REGISTRAR OCORRÊNCIA
# ======================================================

elif menu == "📝 Registrar Ocorrência":
    st.header("📝 Nova Ocorrência")

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
    
    # Mostrar apenas alunos ATIVOS
    if "situacao" in alunos_turma.columns:
        alunos_turma["situacao_norm"] = alunos_turma["situacao"].str.strip().str.title()
        alunos_turma = alunos_turma[alunos_turma["situacao_norm"] == "Ativo"]

    st.markdown("### 👥 Estudantes Envolvidos")
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

    st.markdown("---")
    st.subheader("📋 Infração (Protocolo 179)")

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

    st.markdown(f'<span class="badge badge-primary" style="font-size: 1rem; padding: 0.5rem 1.5rem;">🎯 {infracao_principal}</span>', unsafe_allow_html=True)

    cor_gravidade = CORES_GRAVIDADE.get(gravidade_sugerida, "#9E9E9E")
    st.markdown(f"""
    <div class="protocolo-info">
        <b>📋 Protocolo 179 - Preenchimento Automático</b><br><br>
        <b>Infração:</b> {infracao_principal}<br>
        <b>Gravidade sugerida:</b> <span style="color:{cor_gravidade};font-weight:bold">{gravidade_sugerida}</span><br><br>
        <b>Encaminhamentos sugeridos:</b><br>
        {encaminhamento_sugerido.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚖️ Gravidade")
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
            
            if duplicadas > 0:
                st.warning(f"⚠️ {duplicadas} ocorrência(s) duplicada(s) ignorada(s).")
            
            carregar_ocorrencias.clear()
            st.rerun()
            if sucesso:
    # Atualizar contagem para gamificação
    st.session_state.registros_ocorrencias += 1
    if st.session_state.registros_ocorrencias == 1:
        verificar_conquista("primeiro_registro")
    elif st.session_state.registros_ocorrencias == 10:
        verificar_conquista("10_ocorrencias")
    elif st.session_state.registros_ocorrencias == 50:
        verificar_conquista("50_ocorrencias")
            # ======================================================
# PÁGINA 📋 HISTÓRICO DE OCORRÊNCIAS
# ======================================================

elif menu == "📋 Histórico de Ocorrências":
    st.header("📋 Histórico de Ocorrências")

    if "mensagem_exclusao" in st.session_state:
        st.success(st.session_state.mensagem_exclusao)
        del st.session_state.mensagem_exclusao

    if df_ocorrencias.empty:
        st.info("📭 Nenhuma ocorrência registrada.")
        st.stop()

    # Filtros
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

    st.markdown(f"**Total de ocorrências:** {len(df_view)}")
    st.dataframe(df_view, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🛠️ Ações")
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

    # Formulário de edição
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
# PÁGINA 📊 GRÁFICOS E INDICADORES
# ======================================================

elif menu == "📊 Gráficos e Indicadores":
    st.header("📊 Gráficos e Indicadores")

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
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", len(df_filtro))
    with col2:
        st.metric("Gravíssimas", len(df_filtro[df_filtro["gravidade"] == "Gravíssima"]))
    with col3:
        st.metric("Graves", len(df_filtro[df_filtro["gravidade"] == "Grave"]))
    with col4:
        st.metric("Turmas Afetadas", df_filtro["turma"].nunique())

    st.markdown("---")

    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Por Categoria")
        contagem_cat = df_filtro["categoria"].value_counts().head(10)
        fig_cat = px.bar(x=contagem_cat.values, y=contagem_cat.index, orientation='h',
                         labels={'x': 'Quantidade', 'y': 'Categoria'},
                         color=contagem_cat.values, color_continuous_scale='Blues')
        fig_cat.update_layout(showlegend=False)
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        st.subheader("⚖️ Por Gravidade")
        contagem_grav = df_filtro["gravidade"].value_counts()
        fig_grav = px.pie(values=contagem_grav.values, names=contagem_grav.index,
                          color_discrete_sequence=['#10b981', '#f59e0b', '#f97316', '#ef4444'],
                          hole=0.4)
        st.plotly_chart(fig_grav, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 Evolução Temporal")
    df_filtro["data_apenas"] = df_filtro["data_dt"].dt.date
    evolucao = df_filtro.groupby("data_apenas").size().reset_index(name="Quantidade")
    
    if not evolucao.empty:
        fig_line = px.line(evolucao, x="data_apenas", y="Quantidade", markers=True)
        fig_line.update_traces(line_color="#6366f1")
        st.plotly_chart(fig_line, use_container_width=True)

    # Exportar
    csv = df_filtro.drop(columns=["data_dt"], errors="ignore").to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button("📥 Baixar CSV", data=csv, file_name=f"ocorrencias_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    # ======================================================
# PÁGINA 📄 COMUNICADO AOS PAIS
# ======================================================

elif menu == "📄 Comunicado aos Pais":
    st.header("📄 Comunicado aos Pais / Responsáveis")
    
    st.markdown("""
    <div class="info-box animate-fade-in">
        <h4 style="margin: 0 0 0.5rem 0;">💡 Informações</h4>
        <p style="margin: 0;">Gere comunicados individuais ou em lote para envio aos responsáveis.</p>
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
# PÁGINA 🖨️ IMPRIMIR PDF
# ======================================================

elif menu == "🖨️ Imprimir PDF":
    st.header("🖨️ Gerar PDFs de Ocorrências")

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
# PÁGINA 👨‍🏫 CADASTRAR PROFESSORES
# ======================================================

elif menu == "👨‍🏫 Cadastrar Professores":
    st.header("👨‍🏫 Cadastrar Professores")

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
    st.subheader("📋 Professores Cadastrados")
    
    if not df_professores.empty:
        for _, prof in df_professores.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([6, 1, 1])
                with col1:
                    st.markdown(f"**{prof['nome']}** — {prof.get('cargo', 'Professor')}")
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
# PÁGINA 👤 CADASTRAR ASSINATURAS
# ======================================================

elif menu == "👤 Cadastrar Assinaturas":
    st.header("👤 Cadastrar Assinaturas")

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
    st.subheader("📋 Responsáveis Cadastrados")
    
    if not df_responsaveis.empty:
        for cargo in ["Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora"]:
            grupo = df_responsaveis[df_responsaveis["cargo"] == cargo]
            if grupo.empty:
                continue
            
            st.markdown(f"### 📌 {cargo}")
            for _, resp in grupo.iterrows():
                col1, col2, col3 = st.columns([6, 1, 1])
                with col1:
                    st.markdown(f"• {resp['nome']}")
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
# PÁGINA 🎨 ELETIVA
# ======================================================

elif menu == "🎨 Eletiva":
    st.header("🎨 Eletivas")
    
    st.markdown("""
    <div class="info-box animate-fade-in">
        <h4 style="margin: 0 0 0.5rem 0;">💡 Informações</h4>
        <p style="margin: 0;">Consulte os estudantes por professora da eletiva e verifique quem já foi localizado no sistema.</p>
    </div>
    """, unsafe_allow_html=True)

    if FONTE_ELETIVAS == "supabase":
        st.success("✅ Eletivas carregadas do Supabase.")
    else:
        st.warning("⚠️ Eletivas carregadas da planilha Excel.")

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
    encontrados = len(df_eletiva[df_eletiva["Status"] == "Encontrado"])
    nao_encontrados = len(df_eletiva[df_eletiva["Status"] == "Não encontrado"])

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
# PÁGINA 🏫 MAPA DA SALA
# ======================================================

elif menu == "🏫 Mapa da Sala":
    st.header("🏫 Mapa da Sala de Aula")
    
    st.markdown("""
    <div class="info-box animate-fade-in">
        <h4 style="margin: 0 0 0.5rem 0;">💡 Informações</h4>
        <p style="margin: 0;">Organize os assentos da sala e distribua os alunos manualmente ou de forma automática.</p>
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
# PÁGINA 💾 BACKUPS
# ======================================================

elif menu == "💾 Backups":
    render_backup_page()
    # ======================================================
# PÁGINA 📅 AGENDAMENTO DE ESPAÇOS (VERSÃO PREMIUM COMPLETA)
# ======================================================

elif menu == "📅 Agendamento de Espaços":
    st.header("📅 Agendamento de Espaços e Equipamentos")
    
    from reportlab.lib.pagesizes import A4, landscape
    import json
    
    # ======================================================
    # FUNÇÕES AUXILIARES DO AGENDAMENTO
    # ======================================================
    
    def show_toast(message: str, type: str = "success"):
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
                            show_toast(f"Template '{template_sel}' carregado com sucesso!", "success")
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
                            show_toast(f"{sucessos} agendamento(s) criado(s)!", "success")
                            st.balloons()
                            carregar_agendamentos_filtrado.clear()
                            
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

                if r.status_code in (200, 201):
    # Atualizar gamificação
    st.session_state.agendamentos_criados += 1
    if st.session_state.agendamentos_criados == 5:
        verificar_conquista("agendamento_perfeito")
    
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
    # ABA 3: GRADE SEMANAL (COM TEMPLATES E DISPONIBILIDADE)
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
                                    show_toast(f"Template '{template_sel}' aplicado!", "success")
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
                                show_toast(f"Template salvo com sucesso!", "success")
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
                            show_toast(f"{total_criados} agendamentos fixos criados!", "success")
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
                            show_toast(f"Professor {nome} cadastrado!", "success")
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
                    show_toast("Acesso autorizado!", "success")
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
                            show_toast("Agendamento excluído!", "success")
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
                        show_toast("Limpeza concluída com sucesso!", "success")
                        carregar_agendamentos_filtrado.clear()
                    else:
                        st.error(f"❌ Erro: {r.status_code}")
                except Exception as e:
                    st.error(f"❌ Falha: {e}")
