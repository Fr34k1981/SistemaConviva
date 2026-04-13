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
import logging

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
# IMPORTS LOCAIS COM FALLBACK
# ======================================================
try:
    from src.backup_manager import BackupManager, render_backup_page
except ImportError:
    BackupManager = None
    def render_backup_page():
        st.info("⚠️ Módulo de backup não disponível")

try:
    from src.error_handler import (
        com_tratamento_erro, com_retry, com_validacao,
        ErroConexaoDB, ErroValidacao, ErroCarregamentoDados,
        ErroOperacaoDB, Validadores, logger
    )
except ImportError:
    # Mock das funções de erro
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
            self.acao = acao
            self.detalhes = detalhes
            super().__init__(f"Erro ao {acao}: {detalhes}")
    
    class ErroOperacaoDB(Exception):
        def __init__(self, acao, detalhes):
            self.acao = acao
            self.detalhes = detalhes
            super().__init__(f"Erro ao {acao}: {detalhes}")
    
    class Validadores:
        @staticmethod
        def validar_nao_vazio(valor, campo):
            if not valor or not str(valor).strip():
                return False, f"{campo} não pode ser vazio"
            return True, ""
        
        @staticmethod
        def validar_email(email):
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, email):
                return False, "Email inválido"
            return True, ""
        
        @staticmethod
        def validar_ra(ra):
            digitos = ''.join(c for c in str(ra) if c.isdigit())
            if len(digitos) < 5:
                return False, "RA deve ter ao menos 5 dígitos"
            return True, ""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

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
# CSS PREMIUM COMPLETO (PARTE 1/3)
# ======================================================
st.markdown("""
<style>
* {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
}

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

[data-testid="stTooltipHoverTarget"],
[class*="tooltip"],
[class*="Tooltip"],
[role="tooltip"],
div[class*="TooltipContainer"],
.stTooltip,
#stTooltip {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

h1, h2, h3, h4, h5, h6, p, span, div, label, li, button, a {
    white-space: normal !important;
    word-wrap: break-word !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
    line-height: 1.5 !important;
}

h1 { font-size: 2rem !important; font-weight: 700 !important; }
h2 { font-size: 1.6rem !important; font-weight: 700 !important; }
h3 { font-size: 1.3rem !important; font-weight: 700 !important; }
h4 { font-size: 1.1rem !important; font-weight: 700 !important; }

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

.animate-fade-in { animation: fadeIn 0.5s ease-out; }
.animate-slide-in { animation: slideIn 0.4s ease-out; }
.animate-pulse { animation: pulse 2s infinite; }

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
    white-space: normal !important;
    word-break: break-word;
}

.school-subtitle {
    font-size: 1.2rem;
    font-weight: 500;
    opacity: 0.95;
    margin-bottom: 1rem;
    position: relative;
    z-index: 1;
}

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

.card:hover {
    box-shadow: var(--shadow-xl);
    transform: translateY(-3px);
    border-color: var(--primary-light);
}

.card-title {
    font-weight: 700;
    color: var(--dark);
    font-size: 1.125rem;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    white-space: normal !important;
    word-break: break-word;
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

.metric-card {
    padding: 1.75rem 1rem;
    border-radius: var(--radius-2xl);
    text-align: center;
    box-shadow: var(--shadow-lg);
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1.5px solid var(--border);
    position: relative;
    overflow: hidden;
    color: white;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.metric-card:hover {
    box-shadow: var(--shadow-2xl);
    transform: translateY(-5px);
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1.2;
    text-shadow: 0 2px 10px rgba(0,0,0,0.1);
    white-space: nowrap;
}

.metric-label {
    font-size: 0.9rem;
    font-weight: 500;
    margin-top: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.9;
    white-space: normal !important;
    word-break: break-word;
}

.stButton > button {
    border-radius: var(--radius-xl) !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    border: none !important;
    padding: 0.625rem 1.25rem !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.01em !important;
    position: relative;
    overflow: hidden;
    white-space: normal !important;
    word-wrap: break-word !important;
    min-height: 44px;
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

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select {
    border-radius: var(--radius-xl) !important;
    border: 1.5px solid var(--border) !important;
    transition: all 0.3s !important;
    padding: 0.625rem 1rem !important;
    font-size: 0.95rem !important;
    background: white !important;
    line-height: 1.5 !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1) !important;
    outline: none !important;
}

.stTextArea textarea {
    min-height: 120px !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: var(--light);
    padding: 0.5rem;
    border-radius: var(--radius-2xl);
    border: 1.5px solid var(--border);
    flex-wrap: wrap;
}

.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-xl) !important;
    padding: 0.625rem 1.25rem !important;
    font-weight: 500 !important;
    color: var(--gray) !important;
    transition: all 0.3s !important;
    border: none !important;
    background: transparent !important;
    white-space: nowrap !important;
    flex-shrink: 0;
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
    white-space: nowrap !important;
}

[data-testid="stDataFrame"] td {
    padding: 0.5rem 1rem !important;
    border-bottom: 1px solid var(--border) !important;
    white-space: normal !important;
    word-break: break-word;
}

[data-testid="stDataFrame"] tr:hover td {
    background: linear-gradient(135deg, #f0f4ff, #ffffff) !important;
}

.success-box {
    border-radius: var(--radius-2xl) !important;
    padding: 1.25rem !important;
    margin: 1.25rem 0 !important;
    font-weight: 500 !important;
    box-shadow: var(--shadow-md) !important;
    animation: slideIn 0.4s ease-out !important;
    white-space: normal !important;
    word-break: break-word;
    background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
    border: 1.5px solid var(--success);
    color: #065f46;
}

.warning-box {
    border-radius: var(--radius-2xl) !important;
    padding: 1.25rem !important;
    margin: 1.25rem 0 !important;
    font-weight: 500 !important;
    box-shadow: var(--shadow-md) !important;
    animation: slideIn 0.4s ease-out !important;
    white-space: normal !important;
    word-break: break-word;
    background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
    border: 1.5px solid var(--warning);
    color: #92400e;
}

.error-box {
    border-radius: var(--radius-2xl) !important;
    padding: 1.25rem !important;
    margin: 1.25rem 0 !important;
    font-weight: 500 !important;
    box-shadow: var(--shadow-md) !important;
    animation: slideIn 0.4s ease-out !important;
    white-space: normal !important;
    word-break: break-word;
    background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    border: 1.5px solid var(--danger);
    color: #991b1b;
}

.info-box {
    border-radius: var(--radius-2xl) !important;
    padding: 1.25rem !important;
    margin: 1.25rem 0 !important;
    font-weight: 500 !important;
    box-shadow: var(--shadow-md) !important;
    animation: slideIn 0.4s ease-out !important;
    white-space: normal !important;
    word-break: break-word;
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 1.5px solid var(--primary);
    color: #1e40af;
}

.badge {
    display: inline-block;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    white-space: nowrap;
}

.badge-success { background: linear-gradient(135deg, #d1fae5, #a7f3d0); color: #065f46; }
.badge-warning { background: linear-gradient(135deg, #fef3c7, #fde68a); color: #92400e; }
.badge-danger { background: linear-gradient(135deg, #fee2e2, #fecaca); color: #991b1b; }
.badge-info { background: linear-gradient(135deg, #dbeafe, #bfdbfe); color: #1e40af; }
.badge-primary { background: var(--gradient-primary); color: white; }

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

.stProgress > div > div > div {
    background: var(--gradient-primary) !important;
    border-radius: 9999px !important;
}

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

[data-testid="metric-container"] label {
    white-space: normal !important;
    word-break: break-word;
}

footer { visibility: hidden; }
#MainMenu { visibility: hidden; }

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

@media (max-width: 768px) {
    .main-header { padding: 1.5rem 1rem; }
    .school-name { font-size: 1.8rem; }
    .metric-value { font-size: 2rem; }
    .metric-card { padding: 1.25rem 0.75rem; }
    .metric-label { font-size: 0.75rem; }
    .stTabs [data-baseweb="tab"] { padding: 0.5rem 0.75rem !important; font-size: 0.8rem !important; }
}

.protocolo-info {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 1.5px solid #06b6d4;
    border-radius: var(--radius-lg);
    padding: 1rem;
    margin: 1rem 0;
    color: #0369a1;
    font-size: 0.95rem;
    line-height: 1.6;
    white-space: normal !important;
    word-break: break-word;
}

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
# CORES PARA INFRAÇÕES
# ======================================================
CORES_INFRACOES = {
    "Agressão Física": "#FF6B6B",
    "Agressão Verbal": "#FFE66D",
    "Ameaça": "#C0B020",
    "Bullying": "#4ECDC4",
    "Racismo": "#9B59B6",
    "Homofobia": "#E91E63",
    "Furto": "#FFB74D",
    "Dano ao Patrimônio": "#FFA726",
    "Posse de Celular": "#4DB6AC",
    "Consumo de Substâncias": "#2E7D32",
    "Indisciplina": "#64B5F6",
    "Chegar atrasado": "#FFB74D",
    "Falsificar assinatura": "#EF5350"
}

CORES_GRAVIDADE = {
    "Leve": "#4CAF50",
    "Média": "#FFC107",
    "Grave": "#FF9800",
    "Gravíssima": "#F44336",
}

# ======================================================
# AGENDAMENTO - CONSTANTES
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
# CONQUISTAS E GAMIFICAÇÃO
# ======================================================
CONQUISTAS = {
    "primeiro_registro": {"nome": "🆕 Primeiro Registro", "descricao": "Registrou a primeira ocorrência", "pontos": 10, "icone": "🌟"},
    "10_ocorrencias": {"nome": "📝 Repórter Escolar", "descricao": "Registrou 10 ocorrências", "pontos": 50, "icone": "📋"},
    "50_ocorrencias": {"nome": "📊 Analista de Ocorrências", "descricao": "Registrou 50 ocorrências", "pontos": 100, "icone": "📈"},
    "turma_completa": {"nome": "🏫 Gestor de Turma", "descricao": "Cadastrou uma turma completa", "pontos": 30, "icone": "👥"},
    "agendamento_perfeito": {"nome": "📅 Organizador", "descricao": "Criou 5 agendamentos", "pontos": 20, "icone": "🗓️"},
    "backup_realizado": {"nome": "💾 Guardião dos Dados", "descricao": "Realizou backup do sistema", "pontos": 40, "icone": "🛡️"}
}

# ======================================================
# MENU LATERAL
# ======================================================
st.sidebar.markdown("""
<div style="text-align: center; padding: 1.5rem 0.5rem;">
    <h2 style="background: linear-gradient(135deg, #6366f1, #ec4899); -webkit-background-clip: text; 
               -webkit-text-fill-color: transparent; font-weight: 800; font-size: 1.8rem; margin: 0;">
        🏫 Conviva 179
    </h2>
    <p style="color: #64748b; font-size: 0.85rem; margin-top: 0.25rem;">Gestão Escolar Inteligente</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Inicializar página atual
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = "🏠 Dashboard"

# Menu items
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

for item in menu_items:
    nome_completo = f"{item['icone']} {item['nome']}"
    is_active = st.session_state.pagina_atual == nome_completo
    button_style = "primary" if is_active else "secondary"
    
    if st.sidebar.button(nome_completo, use_container_width=True, type=button_style, key=f"menu_{item['nome'].replace(' ', '_')}"):
        st.session_state.pagina_atual = nome_completo
        st.rerun()

menu = st.session_state.pagina_atual

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="padding: 1rem; background: linear-gradient(135deg, #f8fafc, #e2e8f0); border-radius: 12px; margin-top: 1rem; text-align: center;">
    <p style="margin: 0; font-size: 0.8rem; color: #64748b;">
        <b>🕐 {datetime.now().strftime('%d/%m/%Y')}</b><br>
        <span style="font-size: 0.75rem;">{datetime.now().strftime('%H:%M')}</span>
    </p>
</div>
""", unsafe_allow_html=True)
# ======================================================
# FUNÇÕES UTILITÁRIAS PREMIUM
# ======================================================

def show_toast(message: str, type_msg: str = "success", duration: int = 3000):
    """Mostra notificação toast estilizada"""
    icon = "✅" if type_msg == "success" else "❌" if type_msg == "error" else "⚠️" if type_msg == "warning" else "ℹ️"
    st.toast(f"{icon} {message}")

def info_message(message: str, type_msg: str = "info"):
    """Mostra mensagem estilizada"""
    if type_msg == "success":
        st.markdown(f'<div class="success-box">{message}</div>', unsafe_allow_html=True)
    elif type_msg == "warning":
        st.markdown(f'<div class="warning-box">{message}</div>', unsafe_allow_html=True)
    elif type_msg == "error":
        st.markdown(f'<div class="error-box">{message}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="info-box">{message}</div>', unsafe_allow_html=True)

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
    st.session_state.pontos_usuario += pontos
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
        if conquista_id in CONQUISTAS:
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
        progresso = (pontos % 100) if pontos > 0 else 0
        st.markdown(f"""
        <div style="text-align: center; margin: 0.5rem 0;">
            <div style="font-size: 1.5rem;">{get_nivel_nome(st.session_state.nivel_usuario).split()[1]}</div>
            <div style="font-size: 2rem; font-weight: 700;">{pontos} pts</div>
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
# SESSION STATE - INICIALIZAÇÃO
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
        
        # Estados de Gamificação
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

_init_session_state()

# ======================================================
# SUPABASE - FUNÇÕES BASE
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
    
    df_alunos_temp = carregar_alunos()
    alunos_turma = df_alunos_temp[df_alunos_temp["turma"] == turma_antiga]
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
    duplicadas = df_ocorrencias[
        (df_ocorrencias["ra"] == ra) & 
        (df_ocorrencias["categoria"] == categoria) & 
        (df_ocorrencias["data"] == data_str)
    ]
    return not duplicadas.empty

# ======================================================
# CARREGAMENTO INICIAL DE DADOS
# ======================================================

df_alunos = pd.DataFrame()
df_professores = pd.DataFrame()
df_ocorrencias = pd.DataFrame()
df_responsaveis = pd.DataFrame()

try:
    df_alunos = carregar_alunos()
except Exception as e:
    st.warning("⚠️ Não foi possível carregar alunos.")
    logger.error(f"Erro ao carregar alunos: {e}")

try:
    df_professores = carregar_professores()
except Exception as e:
    st.warning("⚠️ Não foi possível carregar professores.")
    logger.error(f"Erro ao carregar professores: {e}")

try:
    df_ocorrencias = carregar_ocorrencias()
except Exception as e:
    st.warning("⚠️ Não foi possível carregar ocorrências.")
    logger.error(f"Erro ao carregar ocorrências: {e}")

try:
    df_responsaveis = carregar_responsaveis()
except Exception as e:
    st.warning("⚠️ Não foi possível carregar responsáveis.")
    logger.error(f"Erro ao carregar responsáveis: {e}")

# ======================================================
# BACKUP AUTOMÁTICO
# ======================================================

if st.session_state.backup_manager is None and BackupManager:
    st.session_state.backup_manager = BackupManager()

if not st.session_state.backup_realizado and BackupManager:
    try:
        st.session_state.backup_manager.criar_backup()
        st.session_state.backup_manager.limpar_backups_antigos(dias_retencao=30)
        st.session_state.backup_realizado = True
        verificar_conquista("backup_realizado")
    except Exception as e:
        logger.error(f"Erro ao executar backup automático: {e}")

# ======================================================
# WIDGETS DO SIDEBAR
# ======================================================

exibir_gamificacao_sidebar()
# ======================================================
# PÁGINAS DO APLICATIVO - PARTE 1
# ======================================================

# ======================================================
# PÁGINA 🏠 DASHBOARD
# ======================================================

if menu == "🏠 Dashboard":
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
    
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem;">
        <div style="font-size: 2.5rem;">👋</div>
        <div>
            <h2 style="margin: 0; background: linear-gradient(135deg, #1e293b, #475569); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Bem-vindo ao Sistema Conviva 179!</h2>
            <p style="margin: 0; color: #64748b; font-size: 1.1rem;">Gerencie ocorrências, alunos e agendamentos de forma inteligente.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas
    total_alunos = len(df_alunos) if not df_alunos.empty else 0
    total_ocorrencias = len(df_ocorrencias) if not df_ocorrencias.empty else 0
    total_professores = len(df_professores) if not df_professores.empty else 0
    total_ativos = total_alunos
    total_transferidos = 0
    
    if not df_alunos.empty and "situacao" in df_alunos.columns:
        df_alunos_temp = df_alunos.copy()
        df_alunos_temp["situacao_norm"] = df_alunos_temp["situacao"].str.strip().str.title()
        total_ativos = len(df_alunos_temp[df_alunos_temp["situacao_norm"] == "Ativo"])
        total_transferidos = len(df_alunos_temp[df_alunos_temp["situacao_norm"] == "Transferido"])
    
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
    st.info(f"✅ Sistema online | {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ======================================================
# PÁGINA 👥 LISTA DE ALUNOS
# ======================================================

elif menu == "👥 Lista de Alunos":
    st.header("👥 Gerenciar Alunos")
    
    tab1, tab2, tab3 = st.tabs(["📋 Listar Alunos", "➕ Cadastrar Aluno", "✏️ Editar/Excluir"])
    
    # ABA 1: LISTAR
    with tab1:
        if df_alunos.empty:
            st.info("📭 Nenhum aluno cadastrado.")
        else:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                turmas_disp = ["Todas"] + sorted(df_alunos["turma"].dropna().unique().tolist())
                filtro_turma = st.selectbox("🏫 Turma", turmas_disp, key="filtro_turma_lista")
            
            with col2:
                if "situacao" in df_alunos.columns:
                    df_temp = df_alunos.copy()
                    df_temp["situacao_norm"] = df_temp["situacao"].str.strip().str.title()
                    situacoes_unicas = sorted(df_temp["situacao_norm"].dropna().unique().tolist())
                else:
                    df_temp = df_alunos.copy()
                    df_temp["situacao_norm"] = "Ativo"
                    situacoes_unicas = ["Ativo"]
                
                situacoes_disp = ["Ativos", "Todos"] + situacoes_unicas
                filtro_situacao = st.selectbox("📊 Situação", situacoes_disp, index=0, key="filtro_situacao_lista")
            
            with col3:
                busca_nome = st.text_input("🔍 Buscar por Nome ou RA", placeholder="Digite nome ou RA", key="busca_lista")
            
            df_view = df_alunos.copy()
            if "situacao" in df_view.columns:
                df_view["situacao_norm"] = df_view["situacao"].str.strip().str.title()
            else:
                df_view["situacao_norm"] = "Ativo"
            
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
    
    # ABA 2: CADASTRAR
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
    
    # ABA 3: EDITAR/EXCLUIR
    with tab3:
        if df_alunos.empty:
            st.info("📭 Nenhum aluno cadastrado.")
        else:
            st.subheader("✏️ Editar ou Excluir Aluno")
            
            df_busca = df_alunos[df_alunos["situacao"] == "Ativo"] if "situacao" in df_alunos.columns else df_alunos
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
    
    if "situacao" in alunos_turma.columns:
        alunos_turma_temp = alunos_turma.copy()
        alunos_turma_temp["situacao_norm"] = alunos_turma_temp["situacao"].str.strip().str.title()
        alunos_turma = alunos_turma_temp[alunos_turma_temp["situacao_norm"] == "Ativo"]

    st.markdown("### 👥 Estudantes Envolvidos")
    modo_multiplo = st.checkbox("Registrar para múltiplos estudantes", key="modo_multiplo")

    if modo_multiplo:
        alunos_selecionados = st.multiselect("Selecione os estudantes", alunos_turma["nome"].tolist(), key="alunos_multiplos")
    else:
        aluno_unico = st.selectbox("Aluno", alunos_turma["nome"].tolist() if not alunos_turma.empty else [], key="aluno_unico")
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
            st.rerun()

# ======================================================
# PÁGINA 📊 GRÁFICOS E INDICADORES
# ======================================================

elif menu == "📊 Gráficos e Indicadores":
    st.header("📊 Gráficos e Indicadores")

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

    st.markdown(f"**Total de ocorrências:** {len(df_view)}")
    st.dataframe(df_view, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📈 Análise Visual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Por Categoria")
        contagem_cat = df_view["categoria"].value_counts().head(10)
        if not contagem_cat.empty:
            fig = px.bar(x=contagem_cat.values, y=contagem_cat.index, orientation='h',
                        labels={'x': 'Quantidade', 'y': 'Categoria'},
                        color=contagem_cat.values, color_continuous_scale='Blues')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes")
    
    with col2:
        st.subheader("⚖️ Por Gravidade")
        contagem_grav = df_view["gravidade"].value_counts()
        if not contagem_grav.empty:
            fig = px.pie(values=contagem_grav.values, names=contagem_grav.index,
                        color_discrete_sequence=['#10b981', '#f59e0b', '#f97316', '#ef4444'],
                        hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes")

    st.markdown("---")
    st.subheader("📈 Evolução Temporal")
    
    if "data" in df_view.columns:
        try:
            df_view["data_dt"] = pd.to_datetime(df_view["data"], format="%d/%m/%Y %H:%M", errors="coerce")
            df_view["data_apenas"] = df_view["data_dt"].dt.date
            evolucao = df_view.groupby("data_apenas").size().reset_index(name="Quantidade")
            
            if not evolucao.empty:
                fig_line = px.line(evolucao, x="data_apenas", y="Quantidade", markers=True)
                fig_line.update_traces(line_color="#6366f1")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Dados insuficientes para evolução temporal")
        except:
            st.info("Não foi possível processar dados de data")
    
    st.markdown("---")
    st.subheader("🏫 Top 10 Turmas com Mais Ocorrências")
    top_turmas = df_view['turma'].value_counts().head(10)
    if not top_turmas.empty:
        fig_turmas = px.bar(x=top_turmas.values, y=top_turmas.index, orientation='h',
                            labels={'x': 'Quantidade', 'y': 'Turma'},
                            color=top_turmas.values, color_continuous_scale='Greens')
        fig_turmas.update_layout(showlegend=False)
        st.plotly_chart(fig_turmas, use_container_width=True)
    else:
        st.info("Dados insuficientes")

    st.markdown("---")
    st.subheader("👤 Top 10 Alunos com Mais Ocorrências")
    top_alunos = df_view['aluno'].value_counts().head(10)
    if not top_alunos.empty:
        fig_alunos = px.bar(x=top_alunos.values, y=top_alunos.index, orientation='h',
                            labels={'x': 'Quantidade', 'y': 'Aluno'},
                            color=top_alunos.values, color_continuous_scale='Reds')
        fig_alunos.update_layout(showlegend=False)
        st.plotly_chart(fig_alunos, use_container_width=True)
    else:
        st.info("Dados insuficientes")

    st.markdown("---")
    st.subheader("📥 Exportar Dados")
    csv = df_view.to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button("📥 Baixar CSV", data=csv, file_name=f"ocorrencias_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

else:
    st.header(menu)
    st.info(f"Página '{menu}' em desenvolvimento...")
