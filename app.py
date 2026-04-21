======================================================
IMPORTS PADRÃO
======================================================
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

======================================================
REPORTLAB (PDF)
======================================================
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

======================================================
IMPORTS LOCAIS
======================================================
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
    def com_tratamento_erro(func): return func
    def com_retry(tentativas=2):
        def decorator(func): return func
        return decorator
    def com_validacao(func): return func
    class ErroConexaoDB(Exception): pass
    class ErroValidacao(Exception): pass
    class ErroCarregamentoDados(Exception):
        def __init__(self, acao, detalhes): super().__init__(f"Erro ao {acao}: {detalhes}")
    class ErroOperacaoDB(Exception):
        def __init__(self, acao, detalhes): super().__init__(f"Erro ao {acao}: {detalhes}")
    class Validadores:
        @staticmethod
        def validar_nao_vazio(valor, campo):
            if not valor or not str(valor).strip():
                return False, f"{campo} não pode ser vazio"
            return True, " "
    import logging
    logger = logging.getLogger(__name__)

======================================================
VARIÁVEIS DE AMBIENTE
======================================================
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

======================================================
CONFIGURAÇÃO STREAMLIT
======================================================
st.set_page_config(
    page_title="Sistema Conviva 179 - E.E. Profª Eliane",
    layout="wide",
    page_icon="🏫",
    initial_sidebar_state="expanded"
)

======================================================
DESIGN MODERNO & PROFISSIONAL
======================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Nunito:wght@600;700;800&display=swap');

:root {
    --bg: #f8fafc;
    --surface: #ffffff;
    --border: #e2e8f0;
    --text: #0f172a;
    --text-muted: #64748b;
    --primary: #2563eb;
    --primary-hover: #1d4ed8;
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    --info: #0ea5e9;
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 14px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.03);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -2px rgba(0,0,0,0.03);
}

html, body, .stApp, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    letter-spacing: -0.02em;
    margin-bottom: 0.6rem !important;
}

/* Layout Principal */
.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1320px !important;
}

footer, #MainMenu, [data-testid="stToolbar"] { visibility: hidden !important; }

/* Sidebar Profissional */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: var(--shadow-md) !important;
    padding: 1rem !important;
}
section[data-testid="stSidebar"] button {
    border-radius: var(--radius-md) !important;
    background: transparent !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    padding: 0.75rem 1rem !important;
    border: 1px solid transparent !important;
    transition: all 0.2s ease;
    justify-content: flex-start !important;
    text-align: left !important;
    margin: 0.25rem 0 !important;
}
section[data-testid="stSidebar"] button:hover {
    background: #f1f5f9 !important;
    color: var(--primary) !important;
    border-color: var(--border) !important;
    transform: translateX(2px);
}
section[data-testid="stSidebar"] button[kind="primary"] {
    background: var(--primary) !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: var(--shadow-sm);
}
section[data-testid="stSidebar"] button[kind="primary"]:hover {
    background: var(--primary-hover) !important;
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

/* Cards & Containers */
.card, [data-testid="stForm"], .page-banner, .form-panel {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-sm) !important;
    padding: 1.5rem !important;
    transition: box-shadow 0.2s, transform 0.2s;
}
.card:hover, [data-testid="stForm"]:hover {
    box-shadow: var(--shadow-md) !important;
}

.metric-card {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.25rem !important;
    text-align: center;
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }

.metric-value { font-family: 'Nunito', sans-serif !important; font-size: 2.1rem; font-weight: 800; color: var(--primary); }
.metric-label { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-top: 0.3rem; }

/* Botões */
.stButton > button {
    border-radius: var(--radius-md) !important;
    font-weight: 500 !important;
    padding: 0.65rem 1.2rem !important;
    border: 1px solid var(--border) !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.2s;
    font-size: 0.9rem !important;
}
.stButton > button:hover {
    border-color: var(--primary);
    color: var(--primary);
    box-shadow: var(--shadow-md);
}
.stButton > button[kind="primary"] {
    background: var(--primary) !important;
    color: white !important;
    border-color: var(--primary) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--primary-hover) !important;
    transform: translateY(-1px);
}

/* Inputs & Selects */
input, textarea, [data-baseweb="select"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    background: var(--surface) !important;
    padding: 0.7rem 0.9rem !important;
    font-size: 0.95rem !important;
    color: var(--text) !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}
input:focus, textarea:focus, [data-baseweb="select"]:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
    outline: none !important;
}

/* Tabelas / DataFrames */
[data-testid="stDataFrame"] {
    border-radius: var(--radius-lg) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
    background: var(--surface) !important;
}
[data-testid="stDataFrame"] th {
    background: #f8fafc !important;
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.75rem 1rem !important;
    border-bottom: 1px solid var(--border) !important;
}
[data-testid="stDataFrame"] td {
    padding: 0.7rem 1rem !important;
    font-size: 0.9rem;
    border-bottom: 1px solid var(--border);
}
[data-testid="stDataFrame"] tr:hover td { background: #f8fafc !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #f1f5f9 !important;
    border-radius: var(--radius-md) !important;
    padding: 0.3rem !important;
    gap: 0.3rem !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-sm) !important;
    padding: 0.5rem 1rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
    background: transparent !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface) !important;
    color: var(--primary) !important;
    font-weight: 600 !important;
    box-shadow: var(--shadow-sm);
}

/* Alertas / Caixas de Mensagem */
.success-box, .warning-box, .error-box, .info-box {
    border-radius: var(--radius-md) !important;
    padding: 1rem 1.25rem !important;
    border-left: 4px solid;
    font-weight: 500;
    margin: 1rem 0 !important;
}
.success-box { background: #ecfdf5 !important; border-color: var(--success); color: #065f46; }
.warning-box { background: #fffbeb !important; border-color: var(--warning); color: #92400e; }
.error-box   { background: #fef2f2 !important; border-color: var(--error);   color: #991b1b; }
.info-box    { background: #eff6ff !important; border-color: var(--info);    color: #1e3a8a; }

/* Scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

/* Responsivo */
@media (max-width: 768px) {
    .main .block-container { padding: 1rem !important; }
    .metric-value { font-size: 1.8rem; }
    section[data-testid="stSidebar"] { max-width: 280px !important; }
}
</style>
""", unsafe_allow_html=True)

======================================================
DADOS DA ESCOLA
======================================================
ESCOLA_NOME = "E.E. Profª Eliane"
ESCOLA_SUBTITULO = "Sistema Conviva 179"
ESCOLA_ENDERECO = "R. Valter Souza Costa, 147 - Jardim Primavera, Ferraz de Vasconcelos - SP"
ESCOLA_CEP = "CEP: 08535-310"
ESCOLA_TELEFONE = "(11) 4675-1855"
ESCOLA_EMAIL = "e918623@educacao.sp.gov.br"
ESCOLA_LOGO = os.path.join("assets", "images", "eliane_dantas.png")

======================================================
MENU LATERAL PREMIUM (SEM RADIO BUTTONS)
======================================================
st.sidebar.markdown(f"""
<div style="padding: 1.5rem 1rem; border-bottom: 1px solid var(--border); margin-bottom: 1rem;">
    <div style="font-family: 'Nunito', sans-serif; font-size: 1.5rem; font-weight: 800; color: var(--primary);">🏫 Conviva 179</div>
    <div style="font-size: 0.85rem; color: var(--text-muted); font-weight: 500; margin-top: 0.25rem;">{ESCOLA_NOME}</div>
</div>
""", unsafe_allow_html=True)

if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = "🏠 Dashboard"

menu_items = [
    {"nome": "Dashboard", "icone": "🏠"},
    {"nome": "Portal do Responsável", "icone": "👨‍👩‍👧"},
    {"nome": "Importar Alunos", "icone": "📥"},
    {"nome": "Gerenciar Turmas", "icone": "📋"},
    {"nome": "Lista de Alunos", "icone": "👥"},
    {"nome": "Registrar Ocorrência", "icone": "📝"},
    {"nome": "Histórico de Ocorrências", "icone": "📜"},
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
    if st.sidebar.button(nome_completo, key=f"menu_{item['nome'].replace(' ', '_')}", use_container_width=True, type=button_style):
        st.session_state.pagina_atual = nome_completo
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="text-align: center; padding: 0.5rem; color: var(--text-muted); font-size: 0.8rem;">
    🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')} · v10.0 Premium
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

======================================================
AGENDAMENTO DE ESPAÇOS - CONSTANTES
======================================================
SENHA_GESTAO_AGEND = "040600"
DIAS_PRIORITARIO = 60
DIAS_NORMAL = 15
PRIORIDADES_ESTENDIDAS = ["Redação", "Leitura", "Tecnologia", "Programação", "Khan Academy"]
PRIORIDADES_OUTRAS = ["Matific", "Alura", "Speak"]
PRIORIDADE_VALIDAS = {"PRIORITARIO", "PRIORITÁRIO", "NORMAL"} | set(PRIORIDADES_ESTENDIDAS) | set(PRIORIDADES_OUTRAS)
ESPACOS_AGEND = ["Sala de Informática", "Carrinho Positivo", "Carrinho ChromeBook", "Tablet Positivo", "Sala de Leitura"]
HORARIOS_AGEND = ["07:00-07:50", "07:50-08:40", "08:40-09:00", "08:40-09:30", "09:00-09:50", "09:30-09:50", "09:50-10:40", "10:40-11:30", "11:30-12:20", "12:20-13:10", "13:10-14:00", "14:30-15:20", "15:20-16:10", "16:30-17:20", "17:20-18:10", "18:10-19:00", "19:50-20:40", "20:40-21:30"]
TURMAS_INTERVALOS_AGEND = {"6º A": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"}, "6º B": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"}, "7º A": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"}, "7º B": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"}, "7º C": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"}, "8º A": {"cafe": "09:30-09:50", "almoco": "11:30-12:20"}, "8º B": {"cafe": "09:30-09:50", "almoco": "11:30-12:20"}, "8º C": {"cafe": "09:30-09:50", "almoco": "11:30-12:20"}, "9º A": {"cafe": "09:30-09:50", "almoco": "11:30-12:20"}, "9º B": {"cafe": "09:30-09:50", "almoco": "11:30-12:20"}, "9º C": {"cafe": "09:30-09:50", "almoco": "11:30-12:20"}, "3º A": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"}, "3º B": {"cafe": "08:40-09:00", "almoco": "10:40-11:30"}, "1º A": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}, "1º B": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}, "1º C": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}, "1º D": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}, "1º E": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}, "1º F": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}, "2º A": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}, "2º B": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}, "2º C": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}, "3º C": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}, "3º D": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}, "3º E": {"cafe": "14:40-15:00", "almoco": "16:40-17:30"}}
DISCIPLINAS_AGEND = ["Língua Portuguesa", "Matemática", "Ciências", "Geografia", "História", "Arte", "Educação Física", "Língua Inglesa", "Projeto de Vida", "Tecnologia e Inovação", "Educação Financeira", "Redação e Leitura", "Orientação de Estudos", "Biologia", "Física", "Química", "Filosofia", "Sociologia", "Tecnologia e Robótica", "Itinerários Formativos", "Matific", "Alura", "Speak", "Redação", "Tecnologia"]

======================================================
CORES PARA TIPOS DE INFRAÇÃO
======================================================
CORES_INFRACOES = {"Agressão Física": "#FF6B6B", "Agressão Verbal / Conflito Verbal": "#FFE66D", "Ameaça": "#C0B020", "Bullying": "#4ECDC4", "Racismo": "#9B59B6", "Homofobia": "#E91E63", "Furto": "#FFB74D", "Dano ao Patrimônio / Vandalismo": "#FFA726", "Posse de Celular / Dispositivo Eletrônico": "#4DB6AC", "Consumo de Substâncias Ilícitas": "#2E7D32", "Indisciplina": "#64B5F6", "Chegar atrasado": "#FFB74D", "Falsificar assinatura de responsáveis": "#EF5350"}

======================================================
CORES POR GRAVIDADE
======================================================
CORES_GRAVIDADE = {"Leve": "#10b981", "Média": "#f59e0b", "Grave": "#f97316", "Gravíssima": "#ef4444"}

======================================================
PROTOCOLO 179 COMPLETO
======================================================
PROTOCOLO_179 = {"📌 Violência e Agressão": {"Agressão Física": {"gravidade": "Grave", "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Acionar Orientação Educacional\n✅ Notificar famílias\n✅ Conselho Tutelar (se menor de 18 anos)\n✅ B.O. (se houver lesão corporal)"}, "Agressão Verbal / Conflito Verbal": {"gravidade": "Leve", "encaminhamento": "✅ Mediação pedagógica\n✅ Registrar em ata\n✅ Acionar Orientação Educacional\n✅ Acompanhamento psicológico (se necessário)"}, "Ameaça": {"gravidade": "Grave", "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. recomendado\n✅ Medidas protetivas se necessário"}, "Bullying": {"gravidade": "Leve", "encaminhamento": "✅ Programa de Mediação de Conflitos\n✅ Acompanhamento pedagógico\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Acompanhamento psicológico"}, "Racismo": {"gravidade": "Gravíssima", "encaminhamento": "⚖️ CRIME INAFIANÇÁVEL (Lei 7.716/89)\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ Diretoria de Ensino\n✅ Medidas disciplinares cabíveis"}, "Homofobia": {"gravidade": "Gravíssima", "encaminhamento": "⚖️ CRIME (equiparado ao racismo - STF)\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ Diretoria de Ensino\n✅ Medidas disciplinares cabíveis"}}, "🔫 Armas e Segurança": {"Posse de Arma de Fogo / Simulacro": {"gravidade": "Gravíssima", "encaminhamento": "🚨 EMERGÊNCIA - ACIONAR PM (190)\n✅ Isolar área\n✅ Não tocar no objeto\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Afastamento imediato"}, "Posse de Arma Branca": {"gravidade": "Gravíssima", "encaminhamento": "🚨 ACIONAR PM (190)\n✅ Isolar área\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Afastamento imediato"}}, "💊 Drogas e Substâncias": {"Posse de Celular / Dispositivo Eletrônico": {"gravidade": "Leve", "encaminhamento": "✅ Retirar dispositivo (conforme regimento)\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Devolver aos responsáveis"}, "Consumo de Substâncias Ilícitas": {"gravidade": "Grave", "encaminhamento": "✅ SAMU (192) se houver emergência\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. recomendado\n✅ CAPS/CREAS\n✅ Acompanhamento especializado"}}, "🧠 Saúde Mental e Comportamento": {"Indisciplina": {"gravidade": "Leve", "encaminhamento": "✅ Mediação pedagógica\n✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho de Classe\n✅ Acompanhamento pedagógico"}, "Tentativa de Suicídio": {"gravidade": "Gravíssima", "encaminhamento": "🚨 SAMU (192) IMEDIATO\n✅ Hospital de referência\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ CAPS\n✅ Rede de proteção\n✅ Pós-venção"}}, "⚠️ Infrações Acadêmicas e de Pontualidade": {"Chegar atrasado": {"gravidade": "Leve", "encaminhamento": "✅ Registrar em ata\n✅ Conversar com o aluno\n✅ Notificar famílias (se recorrente)\n✅ Verificar motivo dos atrasos\n✅ Orientação Educacional"}, "Falsificar assinatura de responsáveis": {"gravidade": "Grave", "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ Diretoria de Ensino\n✅ Acompanhamento psicológico\n✅ B.O. recomendado"}}}

======================================================
FUNÇÕES UTILITÁRIAS PREMIUM
======================================================
def show_toast(message: str, type: str = "success", duration: int = 3000):
    icon = "✅" if type == "success" else "❌" if type == "error" else "⚠️" if type == "warning" else "ℹ️"
    st.toast(f"{icon} {message}")

def page_header(titulo: str, subtitulo: str = "", cor: str = "#2563eb"):
    partes = titulo.split(maxsplit=1)
    icone = partes[0] if partes else "📌"
    titulo_texto = partes[1] if len(partes) > 1 else titulo
    sub_html = f'<div style="color: var(--text-muted); font-size: 0.9rem; font-weight: 500; margin-top: 0.25rem;">{subtitulo}</div>' if subtitulo else ""
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem; border-left: 4px solid {cor}; padding-left: 1rem;">
        <h2 style="margin: 0; color: var(--text);">{icone} {titulo_texto}</h2>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)

def info_message(message: str, type: str = "info"):
    box_class = f"{type}-box"
    st.markdown(f'<div class="{box_class}">{message}</div>', unsafe_allow_html=True)

def normalizar_texto(valor: str) -> str:
    if valor is None or pd.isna(valor): return " "
    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.split())

def gerar_chave_segura(valor: str) -> str:
    texto = normalizar_texto(valor)
    texto = re.sub(r"[^A-Z0-9_]+", "_", texto)
    texto = texto.strip("_")
    return texto if texto else "SEM_CHAVE"

def encontrar_melhor_match(nome_busca: str, nomes_existentes: list) -> tuple:
    if not nome_busca or not nomes_existentes: return None, 0.0
    nome_norm = normalizar_texto(nome_busca)
    melhor_match, melhor_score = None, 0.0
    for nome in nomes_existentes:
        nome_norm_candidato = normalizar_texto(nome)
        score = SequenceMatcher(None, nome_norm, nome_norm_candidato).ratio()
        if nome_norm_candidato.startswith(nome_norm): score = max(score, 0.95)
        elif nome_norm in nome_norm_candidato: score = max(score, 0.85)
        if score > melhor_score: melhor_score, melhor_match = score, nome
    return melhor_match, melhor_score

def buscar_infracao_fuzzy(busca: str, protocolo: dict) -> dict:
    if not busca or len(busca.strip()) < 2: return {}
    busca_norm = normalizar_texto(busca)
    resultados = {}
    palavras_chave = {"CELULAR": ["CELULAR", "TELEFONE", "SMARTPHONE", "DISPOSITIVO"], "ATRASO": ["ATRASO", "ATRASADO", "PONTUALIDADE"], "BULLYING": ["BULLYING", "CYBERBULLYING", "INTIMIDACAO"], "AGRESSAO": ["AGRESSAO", "AGREDIR", "VIOLENCIA"], "FURTO": ["FURTO", "ROUBO", "SUBTRAIR"], "DROGA": ["DROGA", "ALCOOL", "CIGARRO", "MACONHA", "SUBSTANCIA"], "ARMA": ["ARMA", "FACA", "CANIVETE"], "AMEACA": ["AMEACA", "INTIMIDAR"], "DISCRIMINACAO": ["RACISMO", "HOMOFOBIA", "PRECONCEITO", "DISCRIMINACAO"]}
    for grupo, infracoes in protocolo.items():
        encontradas = {}
        for nome_infracao, dados in infracoes.items():
            nome_norm = normalizar_texto(nome_infracao)
            similaridade = SequenceMatcher(None, busca_norm, nome_norm).ratio()
            match_parcial = busca_norm in nome_norm
            match_chave = any(any(t in busca_norm for t in termos) and any(t in nome_norm for t in termos) for termos in palavras_chave.values())
            if similaridade >= 0.4 or match_parcial or match_chave:
                encontradas[nome_infracao] = dados
        if encontradas: resultados[grupo] = encontradas
    return resultados

======================================================
SISTEMA DE NOTIFICAÇÕES
======================================================
def obter_notificacoes():
    notificacoes = []
    try:
        if 'df_ocorrencias' in globals() and not df_ocorrencias.empty:
            df_ocorrencias['data_dt'] = pd.to_datetime(df_ocorrencias['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_recentes = df_ocorrencias[df_ocorrencias['data_dt'] >= datetime.now() - timedelta(hours=24)]
            graves = df_recentes[df_recentes['gravidade'].isin(['Grave', 'Gravíssima'])]
            if not graves.empty:
                notificacoes.append({"icone": "🚨", "cor": "#ef4444", "titulo": "Ocorrências Graves", "texto": f"{len(graves)} ocorrências graves nas últimas 24h"})
    except: pass
    return notificacoes

def exibir_notificacoes_sidebar():
    notificacoes = obter_notificacoes()
    if notificacoes:
        with st.sidebar.expander(f"🔔 Notificações ({len(notificacoes)})", expanded=True):
            for n in notificacoes:
                st.markdown(f"""
                <div style="padding: 0.5rem; border-left: 3px solid {n['cor']}; background: #fef2f2; border-radius: var(--radius-sm); margin-bottom: 0.5rem;">
                    <strong style="color: {n['cor']}">{n['icone']} {n['titulo']}</strong>
                    <div style="font-size: 0.85rem; color: var(--text-muted);">{n['texto']}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        with st.sidebar.expander("🔔 Notificações", expanded=False):
            st.markdown('<div style="padding: 0.5rem; color: var(--success);">✅ Sistema sem alertas pendentes</div>', unsafe_allow_html=True)

# ======================================================
# SISTEMA DE GAMIFICAÇÃO
# ======================================================
CONQUISTAS = {"primeiro_registro": {"nome": "🆕 Primeiro Registro", "descricao": "Registrou a primeira ocorrência", "pontos": 10, "icone": "🌟"}, "10_ocorrencias": {"nome": "📝 Repórter Escolar", "descricao": "Registrou 10 ocorrências", "pontos": 50, "icone": "📋"}, "50_ocorrencias": {"nome": "📊 Analista de Ocorrências", "descricao": "Registrou 50 ocorrências", "pontos": 100, "icone": "📈"}, "turma_completa": {"nome": "🏫 Gestor de Turma", "descricao": "Cadastrou uma turma completa", "pontos": 30, "icone": "👥"}, "agendamento_perfeito": {"nome": "📅 Organizador", "descricao": "Criou 5 agendamentos", "pontos": 20, "icone": "🗓️"}, "backup_realizado": {"nome": "💾 Guardião dos Dados", "descricao": "Realizou backup do sistema", "pontos": 40, "icone": "🛡️"}}

def inicializar_gamificacao():
    if 'pontos_usuario' not in st.session_state: st.session_state.pontos_usuario = 0
    if 'conquistas_usuario' not in st.session_state: st.session_state.conquistas_usuario = []
    if 'nivel_usuario' not in st.session_state: st.session_state.nivel_usuario = 1
    if 'registros_ocorrencias' not in st.session_state: st.session_state.registros_ocorrencias = 0
    if 'agendamentos_criados' not in st.session_state: st.session_state.agendamentos_criados = 0

def adicionar_pontos(pontos: int, motivo: str = ""):
    st.session_state.pontos_usuario += pontos
    recalcular_nivel()
    if motivo: st.toast(f"+{pontos} pontos! {motivo}", icon="🌟")

def recalcular_nivel():
    pontos = st.session_state.pontos_usuario
    st.session_state.nivel_usuario = 5 if pontos >= 500 else 4 if pontos >= 300 else 3 if pontos >= 150 else 2 if pontos >= 50 else 1

def get_nivel_nome(nivel: int) -> str:
    return {1: "🌱 Iniciante", 2: "📚 Aprendiz", 3: "⭐ Experiente", 4: "🏆 Mestre", 5: "👑 Lendário"}.get(nivel, "🌱 Iniciante")

def verificar_conquista(conquista_id: str):
    if conquista_id not in st.session_state.conquistas_usuario:
        conquista = CONQUISTAS[conquista_id]
        st.session_state.conquistas_usuario.append(conquista_id)
        adicionar_pontos(conquista["pontos"], f"Conquista: {conquista['nome']}")
        st.balloons()
        return True
    return False

def exibir_gamificacao_sidebar():
    inicializar_gamificacao()
    with st.sidebar.expander(f"🏆 Nível {st.session_state.nivel_usuario} — {get_nivel_nome(st.session_state.nivel_usuario)}", expanded=False):
        pontos = st.session_state.pontos_usuario
        progresso = (pontos % 100) if pontos > 0 else 0
        st.markdown(f"""
        <div style="text-align: center; padding: 0.5rem 0;">
            <div style="font-size: 1.5rem; margin-bottom: 0.3rem;">{get_nivel_nome(st.session_state.nivel_usuario).split()[0]}</div>
            <div style="font-family: 'Nunito'; font-weight: 700; font-size: 1.3rem; color: var(--primary);">{pontos} pts</div>
            <div style="background: #e2e8f0; height: 6px; border-radius: 3px; margin: 0.5rem 0; overflow: hidden;">
                <div style="width: {progresso}%; background: var(--primary); height: 100%; border-radius: 3px;"></div>
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted);">{progresso}/100 para próximo nível</div>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state.conquistas_usuario:
            for c_id in st.session_state.conquistas_usuario[:5]:
                if c_id in CONQUISTAS:
                    c = CONQUISTAS[c_id]
                    st.markdown(f'<div style="font-size: 0.85rem; margin: 0.25rem 0; color: var(--text);">{c["icone"]} {c["nome"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size: 0.85rem; color: var(--text-muted); text-align: center;">🎯 Registre ocorrências para ganhar conquistas!</div>', unsafe_allow_html=True)

======================================================
ASSISTENTE VIRTUAL
======================================================
def assistente_virtual(pergunta: str) -> str:
    respostas = {"como registrar ocorrência": "Vá em '📝 Registrar Ocorrência', selecione a turma, o aluno e use a busca inteligente para encontrar a infração.", "como importar alunos": "Use '📥 Importar Alunos', selecione o arquivo CSV da SEDUC, escolha a turma e clique em Importar.", "como agendar espaço": "Em '📅 Agendamento de Espaços', use '✨ Agendar' para data específica ou '🗓️ Grade Semanal' para horários fixos.", "como criar comunicado": "Em '📄 Comunicado aos Pais', selecione o aluno e a ocorrência, marque as medidas e gere o PDF.", "como ver gráficos": "Acesse '📊 Gráficos e Indicadores' para análises visuais das ocorrências.", "como cadastrar professor": "Em '👨‍🏫 Cadastrar Professores', preencha nome e cargo, ou importe uma lista em massa.", "como fazer backup": "Vá em '💾 Backups' para gerar ou importar backups do sistema.", "mapa da sala": "Em '🏫 Mapa da Sala', configure fileiras e carteiras, depois distribua os alunos.", "portal do responsável": "Acesse '👨‍👩‍👧 Portal do Responsável' e faça login com o RA do aluno."}
    pergunta_lower = pergunta.lower()
    for chave, resposta in respostas.items():
        if chave in pergunta_lower: return resposta
    return "Desculpe, não entendi. Tente perguntar sobre: registrar ocorrência, importar alunos, agendar espaço, criar comunicado, ver gráficos, cadastrar professor, fazer backup, mapa da sala ou portal do responsável."

def exibir_assistente_sidebar():
    with st.sidebar.expander("🤖 Assistente Virtual", expanded=False):
        st.markdown('<div style="margin-bottom: 0.5rem; color: var(--text-muted); font-size: 0.9rem;">Como posso ajudar?</div>', unsafe_allow_html=True)
        pergunta = st.text_input("", placeholder="Ex: Como registrar ocorrência?", key="assistente_input", label_visibility="collapsed")
        if pergunta:
            resposta = assistente_virtual(pergunta)
            st.markdown(f'<div style="background: #f8fafc; padding: 0.75rem; border-radius: var(--radius-md); border: 1px solid var(--border); font-size: 0.9rem; margin-top: 0.5rem;">{resposta}</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 1rem; line-height: 1.5;">💡 Busca inteligente nas ocorrências<br>📅 Agendamentos fixos na Grade Semanal<br>📥 Exporte relatórios em PDF ou Excel</div>', unsafe_allow_html=True)

# ======================================================
# SUPABASE — FUNÇÕES BASE
# ======================================================
def _supabase_request(method: str, path: str, **kwargs):
    if not SUPABASE_VALID: raise ErroConexaoDB("Supabase não configurado. Verifique SUPABASE_URL e SUPABASE_KEY.")
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    response = requests.request(method, url, headers=HEADERS, timeout=15, **kwargs)
    if response.status_code >= 400:
        logger.error(f"Erro Supabase ({response.status_code}): {response.text}")
        response.raise_for_status()
    return response

def _supabase_get_dataframe(path: str, acao: str) -> pd.DataFrame:
    try:
        response = _supabase_request("GET", path)
        return pd.DataFrame(response.json())
    except ErroConexaoDB: raise
    except Exception as e: raise ErroCarregamentoDados(acao, str(e))

def _supabase_mutation(method: str, path: str, data, acao: str) -> bool:
    try:
        kwargs = {}
        if data is not None: kwargs["json"] = data
        response = _supabase_request(method, path, **kwargs)
        return response.status_code in (200, 201, 204)
    except ErroConexaoDB: raise
    except Exception as e: raise ErroOperacaoDB(acao, str(e))

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
    if not valido: raise ErroValidacao("nome", msg)
    sucesso = _supabase_mutation("POST", "alunos", aluno, "salvar aluno")
    if sucesso: carregar_alunos.clear()
    return sucesso

@com_tratamento_erro
def atualizar_aluno(ra: str, dados: dict) -> bool:
    sucesso = _supabase_mutation("PATCH", f"alunos?ra=eq.{ra}", dados, "atualizar aluno")
    if sucesso: carregar_alunos.clear()
    return sucesso

@com_tratamento_erro
def excluir_alunos_por_turma(turma: str) -> bool:
    if not turma: raise ErroValidacao("turma", "Turma não pode ser vazia")
    sucesso = _supabase_mutation("DELETE", f"alunos?turma=eq.{turma}", None, "excluir alunos da turma")
    if sucesso: carregar_alunos.clear()
    return sucesso

@com_tratamento_erro
def editar_nome_turma(turma_antiga: str, turma_nova: str) -> bool:
    if not turma_antiga or not turma_nova: raise ErroValidacao("turma", "Nome da turma não pode ser vazio")
    if turma_antiga == turma_nova: return True
    df_alunos = carregar_alunos()
    alunos_turma = df_alunos[df_alunos["turma"] == turma_antiga]
    sucesso_geral = True
    for _, aluno in alunos_turma.iterrows():
        if not atualizar_aluno(aluno["ra"], {"turma": turma_nova}): sucesso_geral = False
    if sucesso_geral: carregar_alunos.clear()
    return True

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
    if not valido: raise ErroValidacao("nome", msg)
    sucesso = _supabase_mutation("POST", "professores", professor, "salvar professor")
    if sucesso: carregar_professores.clear()
    return sucesso

@com_tratamento_erro
def atualizar_professor(id_prof: int, dados: dict) -> bool:
    sucesso = _supabase_mutation("PATCH", f"professores?id=eq.{id_prof}", dados, "atualizar professor")
    if sucesso: carregar_professores.clear()
    return sucesso

@com_tratamento_erro
def excluir_professor(id_prof: int) -> bool:
    if not id_prof: raise ErroValidacao("id", "ID do professor inválido")
    sucesso = _supabase_mutation("DELETE", f"professores?id=eq.{id_prof}", None, "excluir professor")
    if sucesso: carregar_professores.clear()
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
    try: carregar_responsaveis.clear()
    except Exception: pass

@com_tratamento_erro
def salvar_responsavel(responsavel: dict) -> bool:
    valido, msg = Validadores.validar_nao_vazio(responsavel.get("nome"), "Nome do responsável")
    if not valido: raise ErroValidacao("nome", msg)
    sucesso = _supabase_mutation("POST", "responsaveis", responsavel, "salvar responsável")
    if sucesso: limpar_cache_responsaveis()
    return sucesso

@com_tratamento_erro
def atualizar_responsavel(id_resp: int, dados: dict) -> bool:
    sucesso = _supabase_mutation("PATCH", f"responsaveis?id=eq.{id_resp}", dados, "atualizar responsável")
    if sucesso: limpar_cache_responsaveis()
    return sucesso

@com_tratamento_erro
def excluir_responsavel(id_resp: int) -> bool:
    if not id_resp: raise ErroValidacao("id", "ID do responsável inválido")
    sucesso = _supabase_mutation("DELETE", f"responsaveis?id=eq.{id_resp}", None, "excluir responsável")
    if sucesso: limpar_cache_responsaveis()
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
    if not valido: raise ErroValidacao("aluno", msg)
    sucesso = _supabase_mutation("POST", "ocorrencias", ocorrencia, "salvar ocorrência")
    if sucesso: carregar_ocorrencias.clear()
    return sucesso

@com_tratamento_erro
def editar_ocorrencia(id_ocorrencia: int, dados: dict) -> bool:
    sucesso = _supabase_mutation("PATCH", f"ocorrencias?id=eq.{id_ocorrencia}", dados, "editar ocorrência")
    if sucesso: carregar_ocorrencias.clear()
    return sucesso

@com_tratamento_erro
def excluir_ocorrencia(id_ocorrencia: int) -> bool:
    sucesso = _supabase_mutation("DELETE", f"ocorrencias?id=eq.{id_ocorrencia}", None, "excluir ocorrência")
    if sucesso: carregar_ocorrencias.clear()
    return sucesso

def verificar_ocorrencia_duplicada(ra: str, categoria: str, data_str: str, df_ocorrencias: pd.DataFrame) -> bool:
    if df_ocorrencias.empty: return False
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
        if espaco and espaco in ESPACOS_AGEND: filtros += f"&espaco=eq.{espaco}"
        if professor: filtros += f'&professor_nome=eq."{professor.replace(" ", "%20")}"'
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
    if r.status_code not in (200, 201): return False, f"{r.status_code} - {r.text}"
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
    except Exception: return None

def prof_list_agend(only_active: bool = True) -> pd.DataFrame:
    try:
        path = "/rest/v1/professores?select=id,nome,email,cargo&order=nome.asc"
        rows = _rest_get_agend(path)
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["id", "nome", "email", "cargo"])
        if not df.empty and 'cargo' in df.columns: df['status'] = 'ATIVO'
        return df
    except Exception: return pd.DataFrame(columns=["id", "nome", "email", "cargo", "status"])

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
    if not os.path.exists(caminho_arquivo): return fallback if fallback is not None else {}
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
                    if v is not None and v.text: valor = v.text
                    if tipo == "s" and valor.isdigit(): valor = shared_strings[int(valor)]
                    valores[col] = str(valor).strip()
                valor_a = valores.get("A", "")
                valor_b = valores.get("B", "")
                valor_c = valores.get("C", "")
                if valor_a and not valor_b and not valor_c:
                    professora_atual = valor_a
                    eletivas.setdefault(professora_atual, [])
                    continue
                if valor_a.upper() in ("Nº", "NO", "NUM"): continue
                if valor_b.upper().startswith("NOME"): continue
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
    if df_eletivas.empty: return {}
    eletivas = {}
    for _, row in df_eletivas.iterrows():
        professora = str(row.get("professora", "")).strip()
        nome_aluno = str(row.get("nome_aluno", "")).strip()
        serie = str(row.get("serie", "")).strip()
        if not professora or not nome_aluno: continue
        eletivas.setdefault(professora, []).append({"nome": nome_aluno, "serie": serie})
    return eletivas

def montar_dataframe_eletiva(nome_professora: str, df_alunos: pd.DataFrame, eletivas_dict: dict) -> pd.DataFrame:
    registros = []
    alunos_db = df_alunos.copy()
    nome_coluna = next((c for c in alunos_db.columns if c.lower() in ("nome", "nome do aluno", "aluno")), None)
    if nome_coluna: alunos_db["nome_norm"] = alunos_db[nome_coluna].apply(normalizar_texto)
    else: alunos_db["nome_norm"] = ""
    for item in eletivas_dict.get(nome_professora, []):
        nome_original = item.get("nome", "")
        serie_original = item.get("serie", "")
        nome_norm_excel = normalizar_texto(nome_original)
        melhor_match, melhor_score = None, 0.0
        for _, aluno in alunos_db.iterrows():
            score = SequenceMatcher(None, nome_norm_excel, aluno.get("nome_norm", "")).ratio()
            if score > melhor_score: melhor_score, melhor_match = score, aluno
        if melhor_match is not None and melhor_score >= 0.80:
            registros.append({"Professora": nome_professora, "Nome da Eletiva": nome_original, "Série da Eletiva": serie_original, "Aluno Cadastrado": melhor_match.get("nome", ""), "RA": melhor_match.get("ra", ""), "Turma no Sistema": melhor_match.get("turma", ""), "Situação": melhor_match.get("situacao", ""), "Status": "Encontrado"})
        else:
            registros.append({"Professora": nome_professora, "Nome da Eletiva": nome_original, "Série da Eletiva": serie_original, "Aluno Cadastrado": "", "RA": "", "Turma no Sistema": "", "Situação": "", "Status": "Não encontrado"})
    return pd.DataFrame(registros)

ELETIVAS_EXCEL = carregar_eletivas_do_excel(ELETIVAS_ARQUIVO, fallback=ELETIVAS)

======================================================
PDF — UTILITÁRIOS
======================================================
def _criar_documento_pdf(buffer: BytesIO) -> SimpleDocTemplate:
    return SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)

def _adicionar_logo(elementos: list):
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4*cm)
            logo.hAlign = "CENTER"
            elementos.append(logo)
            elementos.append(Spacer(1, 0.3*cm))
    except Exception: pass

======================================================
PDF — ELETIVA
======================================================
def gerar_pdf_eletiva(nome_professora: str, df_eletiva: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    doc = _criar_documento_pdf(buffer)
    estilos = getSampleStyleSheet()
    elementos = []
    _adicionar_logo(elementos)
    titulo_style = ParagraphStyle('TituloEletiva', parent=estilos['Heading1'], fontSize=14, alignment=TA_CENTER, spaceAfter=0.5*cm, textColor=colors.HexColor("#2563eb"))
    elementos.append(Paragraph(f"LISTA DE ELETIVA", titulo_style))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph(f"<b>Professora:</b> {nome_professora}", estilos['Normal']))
    elementos.append(Paragraph(f"<b>Total de estudantes:</b> {len(df_eletiva)}", estilos['Normal']))
    elementos.append(Spacer(1, 0.5*cm))
    cabecalho = ["Nome da Eletiva", "Série", "RA", "Turma", "Status"]
    linhas = []
    for _, row in df_eletiva.iterrows():
        linhas.append([str(row.get("Nome da Eletiva", ""))[:30], str(row.get("Série da Eletiva", ""))[:15], str(row.get("RA", ""))[:15], str(row.get("Turma no Sistema", ""))[:15], str(row.get("Status", ""))[:15]])
    tabela = Table(cabecalho + linhas, colWidths=[7*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm], repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563eb")), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9), ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    for i in range(1, len(linhas) + 1):
        if i % 2 == 0: tabela.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor("#F5F5F5"))]))
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

======================================================
PDF — OCORRÊNCIA
======================================================
def gerar_pdf_ocorrencia(ocorrencia: dict, df_responsaveis: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    doc = _criar_documento_pdf(buffer)
    estilos = getSampleStyleSheet()
    elementos = []
    _adicionar_logo(elementos)
    protocolo = f"PROTOCOLO: {ocorrencia.get('id', 'N/A')}/{datetime.now().year}"
    elementos.append(Paragraph(f"{protocolo}", ParagraphStyle("protocolo", parent=estilos["Normal"], alignment=2, fontSize=9, textColor=colors.darkblue)))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("REGISTRO DE OCORRÊNCIA", ParagraphStyle("titulo", parent=estilos["Heading1"], alignment=1, fontSize=12, textColor=colors.darkblue)))
    dados = [["Data", ocorrencia.get("data", "")], ["Aluno", ocorrencia.get("aluno", "")], ["RA", str(ocorrencia.get("ra", ""))], ["Turma", ocorrencia.get("turma", "")], ["Categoria", ocorrencia.get("categoria", "")], ["Gravidade", ocorrencia.get("gravidade", "")], ["Professor", ocorrencia.get("professor", "")]]
    tabela = Table(dados, colWidths=[4*cm, 11*cm])
    tabela.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#2563eb")), ('TEXTCOLOR', (0, 0), (0, -1), colors.white), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTSIZE', (0, 0), (-1, -1), 9)]))
    elementos.append(tabela)
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("RELATO", estilos["Normal"]))
    elementos.append(Paragraph(str(ocorrencia.get("relato", "")).replace("\n", " "), estilos["Normal"]))
    elementos.append(Spacer(1, 0.2*cm))
    elementos.append(Paragraph("ENCAMINHAMENTOS", estilos["Normal"]))
    elementos.append(Paragraph(str(ocorrencia.get("encaminhamento", "")).replace("\n", " "), estilos["Normal"]))
    doc.build(elementos)
    buffer.seek(0)
    return buffer

======================================================
PDF — COMUNICADO AOS PAIS
======================================================
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
    elementos.append(Paragraph("RELATO DA OCORRÊNCIA", estilos["Normal"]))
    elementos.append(Paragraph(str(ocorrencia_data.get("relato", "")).replace("\n", " "), estilos["Normal"]))
    elementos.append(Spacer(1, 0.3*cm))
    if medidas_aplicadas:
        elementos.append(Paragraph("MEDIDAS APLICADAS", estilos["Normal"]))
        for linha in medidas_aplicadas.split("\n"):
            elementos.append(Paragraph(f"• {linha}", estilos["Normal"]))
    if observacoes:
        elementos.append(Spacer(1, 0.3*cm))
        elementos.append(Paragraph("OBSERVAÇÕES", estilos["Normal"]))
        elementos.append(Paragraph(observacoes, estilos["Normal"]))
    doc.build(elementos)
    buffer.seek(0)
    return buffer

======================================================
SESSION STATE — INICIALIZAÇÃO
======================================================
def _init_session_state():
    defaults = {"editando_id": None, "dados_edicao": None, "ocorrencia_salva_sucesso": False, "salvando_ocorrencia": False, "gravidade_alterada": False, "adicionar_outra_infracao": False, "infracoes_adicionais": [], "mensagem_exclusao": None, "editando_prof": None, "professor_salvo_sucesso": False, "nome_professor_salvo": "", "cargo_professor_salvo": "", "confirmar_exclusao_prof": None, "editando_resp": None, "responsavel_salvo_sucesso": False, "nome_responsavel_salvo": "", "cargo_responsavel_salvo": "", "confirmar_exclusao_resp": None, "turma_para_editar": None, "turma_para_deletar": None, "turma_para_substituir": None, "turma_selecionada": None, "senha_exclusao_validada": False, "confirmar_exclusao_aluno": None, "ELETIVAS": None, "FONTE_ELETIVAS": None, "backup_manager": None, "backup_realizado": False, "gestao_logado": False, "aba_agendamento": "✨ Agendar", "pending_cancel_id": None, "pending_delete_id": None, "pending_delete_prof": None, "logs_agendamento": [], "pontos_usuario": 0, "conquistas_usuario": [], "nivel_usuario": 1, "registros_ocorrencias": 0, "agendamentos_criados": 0, "menu_selecionado": "🏠 Dashboard", "pagina_atual": "🏠 Dashboard"}
    for key, value in defaults.items():
        if key not in st.session_state: st.session_state[key] = value

_init_session_state()

======================================================
BACKUP AUTOMÁTICO
======================================================
if st.session_state.backup_manager is None:
    st.session_state.backup_manager = BackupManager()
if not st.session_state.backup_realizado:
    try:
        st.session_state.backup_manager.criar_backup()
        st.session_state.backup_manager.limpar_backups_antigos(dias_retencao=30)
        st.session_state.backup_realizado = True
        verificar_conquista("backup_realizado")
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
try: df_alunos = carregar_alunos()
except Exception as e: st.warning("⚠️ Não foi possível carregar alunos."); logger.error(e)
try: df_professores = carregar_professores()
except Exception as e: st.warning("⚠️ Não foi possível carregar professores."); logger.error(e)
try: df_ocorrencias = carregar_ocorrencias()
except Exception as e: st.warning("⚠️ Não foi possível carregar ocorrências."); logger.error(e)
try: df_responsaveis = carregar_responsaveis()
except Exception as e: st.warning("⚠️ Não foi possível carregar responsáveis."); logger.error(e)

# ======================================================
# ELETIVAS — DEFINIÇÃO DE FONTE
# ======================================================
if SUPABASE_VALID:
    try: df_eletivas_supabase = _supabase_get_dataframe("eletivas?select=*", "carregar eletivas")
    except Exception: df_eletivas_supabase = pd.DataFrame()
    if st.session_state.ELETIVAS is None:
        if not df_eletivas_supabase.empty:
            st.session_state.ELETIVAS = converter_eletivas_supabase_para_dict(df_eletivas_supabase)
            st.session_state.FONTE_ELETIVAS = "supabase"
        else:
            st.session_state.ELETIVAS = ELETIVAS_EXCEL
            st.session_state.FONTE_ELETIVAS = "excel"
    else:
        st.session_state.FONTE_ELETIVAS = "supabase" if not df_eletivas_supabase.empty else "excel"
else:
    st.session_state.FONTE_ELETIVAS = "excel" if df_eletivas_supabase.empty else "supabase"

ELETIVAS = st.session_state.ELETIVAS
FONTE_ELETIVAS = st.session_state.FONTE_ELETIVAS

======================================================
REMOÇÃO DEFINITIVA DE TOOLTIPS (JAVASCRIPT CORRIGIDO)
======================================================
st.components.v1.html("""
<script>
(function() {
    'use strict';
    function limparTooltips() {
        document.querySelectorAll('[data-testid="stTooltipHoverTarget"], [data-testid="stTooltipContent"], [role="tooltip"], [data-baseweb="tooltip"]').forEach(el => {
            if (!el.closest('button')) el.remove();
        });
        document.querySelectorAll('[data-testid="stSidebar"] button').forEach(btn => {
            btn.removeAttribute('title'); btn.removeAttribute('data-tooltip');
        });
        document.querySelectorAll('[data-testid="stSidebar"] button span').forEach(span => {
            span.style.removeProperty('display'); span.style.removeProperty('visibility');
            span.style.removeProperty('opacity'); span.style.removeProperty('font-size');
            span.style.removeProperty('width'); span.style.removeProperty('height');
            span.style.removeProperty('overflow');
        });
    }
    setTimeout(limparTooltips, 300);
    setTimeout(limparTooltips, 800);
    setInterval(limparTooltips, 2000);
    const observer = new MutationObserver(() => limparTooltips());
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", height=0)

exibir_notificacoes_sidebar()
exibir_gamificacao_sidebar()
exibir_assistente_sidebar()

======================================================
PÁGINA 🏠 DASHBOARD
======================================================
if menu == "🏠 Dashboard":
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #2563eb 100%); padding: 2rem; border-radius: var(--radius-lg); color: white; margin-bottom: 1.5rem; box-shadow: var(--shadow-lg); position: relative; overflow: hidden;">
        <div style="position: relative; z-index: 2;">
            <h1 style="color: white; margin: 0; font-size: 1.8rem;">🏫 {ESCOLA_NOME}</h1>
            <div style="opacity: 0.9; font-weight: 500; margin-top: 0.25rem;">{ESCOLA_SUBTITULO}</div>
            <div style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.85;">
                📍 {ESCOLA_ENDERECO} &nbsp;•&nbsp; 📞 {ESCOLA_TELEFONE} &nbsp;•&nbsp; ✉️ {ESCOLA_EMAIL}
            </div>
        </div>
        <div style="position: absolute; top: -20px; right: -20px; width: 120px; height: 120px; background: rgba(255,255,255,0.1); border-radius: 50%; filter: blur(20px);"></div>
    </div>
    """, unsafe_allow_html=True)

    hora_atual = datetime.now().hour
    saudacao = "🌅 Bom dia" if hora_atual < 12 else ("☀️ Boa tarde" if hora_atual < 18 else "🌙 Boa noite")
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 1rem; background: var(--surface); border-radius: var(--radius-lg); padding: 1rem 1.25rem; border: 1px solid var(--border); box-shadow: var(--shadow-sm); margin-bottom: 1.5rem;">
        <div style="font-size: 1.8rem;">👋</div>
        <div>
            <div style="font-family: 'Nunito'; font-size: 1.2rem; font-weight: 700; color: var(--text);">{saudacao}! Bem-vindo ao Sistema Conviva 179</div>
            <div style="color: var(--text-muted); font-size: 0.85rem;">Gerencie ocorrências, alunos e agendamentos de forma inteligente. &nbsp;· &nbsp; <b style="color: var(--primary);">{datetime.now().strftime('%A, %d de %B de %Y')}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    total_alunos = len(df_alunos) if not df_alunos.empty else 0
    total_ocorrencias = len(df_ocorrencias) if not df_ocorrencias.empty else 0
    total_professores = len(df_professores) if not df_professores.empty else 0
    total_ativos = len(df_alunos[df_alunos["situacao"].str.strip().str.title() == "Ativo"]) if not df_alunos.empty and "situacao" in df_alunos.columns else total_alunos
    total_transferidos = len(df_alunos[df_alunos["situacao"].str.strip().str.title() == "Transferido"]) if not df_alunos.empty and "situacao" in df_alunos.columns else 0
    gravissimas = len(df_ocorrencias[df_ocorrencias["gravidade"] == "Gravíssima"]) if not df_ocorrencias.empty and "gravidade" in df_ocorrencias.columns else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    metrics = [
        (col1, "👥", total_alunos, "Total de Alunos", f"{total_ativos} ativos"),
        (col2, "⚠️", total_ocorrencias, "Ocorrências", f"{gravissimas} gravíssimas"),
        (col3, "👨‍🏫", total_professores, "Professores", "cadastrados"),
        (col4, "✅", total_ativos, "Alunos Ativos", "frequentando"),
        (col5, "🔄", total_transferidos, "Transferidos", "este ano")
    ]
    for col, icon, value, label, sub in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 1.5rem; margin-bottom: 0.3rem;">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem;">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📝 Nova Ocorrência", use_container_width=True, type="primary", key="quick_ocorrencia"):
            st.session_state.pagina_atual = "📝 Registrar Ocorrência"; st.rerun()
    with col2:
        if st.button("👥 Ver Alunos", use_container_width=True, key="quick_alunos"):
            st.session_state.pagina_atual = "👥 Lista de Alunos"; st.rerun()
    with col3:
        if st.button("📅 Agendar Espaço", use_container_width=True, key="quick_agendamento"):
            st.session_state.pagina_atual = "📅 Agendamento de Espaços"; st.rerun()
    with col4:
        if st.button("📊 Relatórios", use_container_width=True, key="quick_relatorios"):
            st.session_state.pagina_atual = "📊 Gráficos e Indicadores"; st.rerun()

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #eff6ff, #f0fdf4); border: 1px solid #bfdbfe; border-radius: var(--radius-md); padding: 0.75rem 1rem; font-size: 0.85rem; color: #1e40af; display: flex; align-items: center; gap: 0.5rem; margin-top: 1rem;">
        📌 Fonte das eletivas: <b>{FONTE_ELETIVAS.upper()}</b> &nbsp;·&nbsp; 🗓️ Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>
    """, unsafe_allow_html=True)

    if not df_ocorrencias.empty:
        st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
        st.markdown('<h3 style="margin-bottom: 1rem; color: var(--text);">📈 Análise de Ocorrências</h3>', unsafe_allow_html=True)
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            contagem_grav = df_ocorrencias["gravidade"].value_counts()
            if not contagem_grav.empty:
                fig_grav_dash = px.pie(values=contagem_grav.values, names=contagem_grav.index, color_discrete_sequence=['#10b981','#f59e0b','#f97316','#ef4444'], hole=0.5)
                fig_grav_dash.update_traces(textfont_size=12, textfont_family='Inter, sans-serif')
                fig_grav_dash.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter, sans-serif', size=12, color='#334155'), margin=dict(t=10, b=10, l=0, r=0), legend=dict(font=dict(size=11), orientation='h', y=-0.15), height=250)
                st.plotly_chart(fig_grav_dash, use_container_width=True)
        with col_g2:
            contagem_cat = df_ocorrencias["categoria"].value_counts().head(6)
            if not contagem_cat.empty:
                fig_cat_dash = px.bar(x=contagem_cat.values, y=contagem_cat.index, orientation='h', color=contagem_cat.values, color_continuous_scale=[[0,'#93c5fd'],[0.5,'#2563eb'],[1,'#1d4ed8']])
                fig_cat_dash.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter, sans-serif', size=11, color='#334155'), margin=dict(t=10, b=10, l=0, r=10), xaxis=dict(gridcolor='#e2e8f0', title='Quantidade'), yaxis=dict(gridcolor='rgba(0,0,0,0)'), coloraxis_showscale=False, height=250)
                st.plotly_chart(fig_cat_dash, use_container_width=True)

        df_ocorrencias_temp = df_ocorrencias.copy()
        df_ocorrencias_temp["data_dt"] = pd.to_datetime(df_ocorrencias_temp["data"], format="%d/%m/%Y %H:%M", errors="coerce")
        df_recente = df_ocorrencias_temp[df_ocorrencias_temp["data_dt"] >= datetime.now() - timedelta(days=30)]
        if not df_recente.empty:
            evolucao = df_recente.groupby(df_recente["data_dt"].dt.date).size().reset_index(name="Quantidade")
            evolucao.columns = ["Data", "Quantidade"]
            fig_linha = px.area(evolucao, x="Data", y="Quantidade")
            fig_linha.update_traces(line_color="#2563eb", line_width=2.5, fillcolor="rgba(37,99,235,0.1)", marker=dict(size=5, color="#2563eb"))
            fig_linha.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter, sans-serif', size=11, color='#334155'), margin=dict(t=10, b=10, l=0, r=0), xaxis=dict(gridcolor='#e2e8f0'), yaxis=dict(gridcolor='#e2e8f0'), height=200)
            st.plotly_chart(fig_linha, use_container_width=True)

        top10 = df_ocorrencias["aluno"].value_counts().head(10).reset_index()
        top10.columns = ["Aluno", "Ocorrências"]
        if not df_alunos.empty and "turma" in df_alunos.columns:
            top10 = top10.merge(df_alunos[["nome", "turma"]].rename(columns={"nome": "Aluno"}), on="Aluno", how="left")
            top10["Turma"] = top10.get("turma", "—").fillna("—")
        else: top10["Turma"] = "—"
        for idx, row in top10.iterrows():
            pct = int((row["Ocorrências"] / top10["Ocorrências"].max()) * 100)
            cor = ["#ef4444","#f59e0b","#10b981","#94a3b8","#94a3b8","#94a3b8","#94a3b8","#94a3b8","#94a3b8","#94a3b8"][idx]
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:0.8rem; background:white; border-radius:var(--radius-md); border:1px solid var(--border); padding:0.6rem 0.8rem; margin-bottom:0.3rem; box-shadow:var(--shadow-sm);">
                <div style="font-size:1.1rem; width:24px; text-align:center;">{idx+1}.</div>
                <div style="flex:1; min-width:0;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
                        <div style="font-weight:600; color:var(--text); font-size:0.85rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{row['Aluno']}</div>
                        <div style="display:flex; align-items:center; gap:0.4rem;">
                            <span style="background:#f1f5f9; color:#64748b; border-radius:var(--radius-sm); padding:0.1rem 0.4rem; font-size:0.7rem; font-weight:600;">{row.get('Turma','—')}</span>
                            <span style="background:{cor}18; color:{cor}; border:1px solid {cor}40; border-radius:var(--radius-sm); padding:0.15rem 0.5rem; font-size:0.8rem; font-weight:700;">{int(row['Ocorrências'])}</span>
                        </div>
                    </div>
                    <div style="height:4px; background:#f1f5f9; border-radius:2px; overflow:hidden;">
                        <div style="width:{pct}%; height:4px; background:{cor}; border-radius:2px;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:center; padding:2rem; color:#94a3b8; background:white; border-radius:var(--radius-lg); border:1px dashed var(--border); margin-top:1rem;">📊 Nenhuma ocorrência registrada ainda.<br><span style="font-size:0.85rem;">Os gráficos aparecerão aqui após o primeiro registro.</span></div>', unsafe_allow_html=True)

# ======================================================
# PÁGINA 👨‍👩‍👧 PORTAL DO RESPONSÁVEL
# ======================================================
elif menu == "👨‍👩‍👧 Portal do Responsável":
    page_header("👨‍👩‍👧 Portal do Responsável", "Acesso seguro para pais e responsáveis", "#7c3aed")
    col1, col2 = st.columns(2)
    with col1: ra_acesso = st.text_input("RA do Aluno: ", placeholder="Digite o RA", key="portal_ra")
    with col2: senha_acesso = st.text_input("Senha: ", type="password", placeholder="Digite a senha", key="portal_senha")
    if st.button("🔓 Acessar Portal", type="primary", use_container_width=True):
        if not ra_acesso or not senha_acesso: st.error("❌ Preencha RA e senha!")
        else:
            aluno_encontrado = df_alunos[df_alunos['ra'].astype(str) == ra_acesso] if not df_alunos.empty else pd.DataFrame()
            if aluno_encontrado.empty: st.error("❌ Aluno não encontrado!")
            else:
                if senha_acesso != "123456": st.error("❌ Senha incorreta!")
                else:
                    aluno = aluno_encontrado.iloc[0]
                    st.success(f"✅ Bem-vindo, responsável por **{aluno['nome']}**!")
                    col1, col2, col3 = st.columns(3)
                    with col1: st.metric("RA", aluno['ra'])
                    with col2: st.metric("Turma", aluno.get('turma', 'N/A'))
                    with col3: st.metric("Situação", aluno.get('situacao', 'Ativo'))
                    ocorrencias_aluno = df_ocorrencias[df_ocorrencias['ra'].astype(str) == ra_acesso] if not df_ocorrencias.empty else pd.DataFrame()
                    if ocorrencias_aluno.empty: st.success("✅ Nenhuma ocorrência registrada para este aluno!")
                    else:
                        st.warning(f"⚠️ {len(ocorrencias_aluno)} ocorrência(s) registrada(s)")
                        for _, occ in ocorrencias_aluno.sort_values('data', ascending=False).iterrows():
                            with st.expander(f"📅 {occ['data']} - {occ['categoria']} ({occ['gravidade']})"):
                                st.write(f"**Professor:** {occ.get('professor', 'N/A')}")
                                st.write(f"**Relato:** {occ.get('relato', 'N/A')}")
                                st.write(f"**Encaminhamento:** {occ.get('encaminhamento', 'N/A')}")

# ======================================================
# PÁGINA 📥 IMPORTAR ALUNOS
# ======================================================
elif menu == "📥 Importar Alunos":
    page_header("📥 Importar Alunos por Turma", "Importe alunos a partir de arquivos CSV da SEDUC", "#0891b2")
    turma_alunos = st.text_input("🏫 Nome da TURMA: ", placeholder="Ex: 6º Ano B, 1º Ano D", key="turma_import")
    arquivo_upload = st.file_uploader("📁 Selecione o arquivo CSV da SEDUC", type=["csv"], key="arquivo_csv")
    if arquivo_upload is not None:
        try:
            df_import = pd.read_csv(arquivo_upload, sep=';', encoding='utf-8-sig', dtype=str)
            st.success(f"✅ Arquivo lido! {len(df_import)} alunos encontrados.")
            st.write("### 👀 Pré-visualização dos dados:")
            st.dataframe(df_import.head(10), use_container_width=True)
            colunas = df_import.columns.tolist()
            col_ra = col_nome = col_situacao = None
            for col in colunas:
                col_lower = col.lower()
                if 'dig' in col_lower or 'dígito' in col_lower: continue
                if 'ra' in col_lower and col_ra is None:
                    for val in df_import[col].dropna().head(5):
                        if len(''.join(c for c in str(val) if c.isdigit())) >= 9: col_ra = col; break
                if 'nome' in col_lower and 'aluno' in col_lower: col_nome = col
                if 'situa' in col_lower or 'status' in col_lower: col_situacao = col
            st.write("### 🔍 Colunas identificadas:")
            if col_ra: st.success(f"✅ **RA:** {col_ra}")
            else: st.error("❌ **RA:** NÃO ENCONTRADO")
            if col_nome: st.success(f"✅ **Nome:** {col_nome}")
            else: st.error("❌ **Nome:** NÃO ENCONTRADO")
            if col_situacao: st.info(f"📊 **Situação:** {col_situacao}")
            else: st.warning("📊 **Situação:** Não encontrada (usará 'Ativo')")
            if col_ra is None or col_nome is None:
                col1, col2 = st.columns(2)
                with col1: col_ra = st.selectbox("Coluna do RA: ", colunas); col_nome = st.selectbox("Coluna do Nome: ", colunas)
                with col2: col_situacao = st.selectbox("Coluna da Situação (opcional): ", ["Não usar"] + colunas)
                if col_situacao == "Não usar": col_situacao = None
            st.markdown("---")
            df_alunos_existente = carregar_alunos()
            if turma_alunos and turma_alunos in df_alunos_existente['turma'].unique().tolist():
                st.warning(f"⚠️ A turma **{turma_alunos}** já existe! Alunos serão ATUALIZADOS.")
            if st.button("🚀 IMPORTAR ALUNOS", type="primary", use_container_width=True):
                if not turma_alunos: st.error("❌ Digite o nome da turma!")
                elif col_ra is None or col_nome is None: st.error("❌ É necessário identificar as colunas de RA e Nome!")
                else:
                    novos = atualizados = ignorados = erros = 0
                    progress = st.progress(0); status = st.empty()
                    for i, (_, row) in enumerate(df_import.iterrows()):
                        try:
                            ra_valor = row[col_ra]
                            if pd.isna(ra_valor): erros += 1; continue
                            ra_str = ''.join(c for c in str(ra_valor) if c.isdigit())
                            if not ra_str or len(ra_str) < 5: erros += 1; continue
                            nome_valor = row[col_nome]
                            if pd.isna(nome_valor): erros += 1; continue
                            nome_str = str(nome_valor).strip()
                            if not nome_str or nome_str == 'nan': erros += 1; continue
                            sit_str = "Ativo"
                            if col_situacao and not pd.isna(row[col_situacao]):
                                sit_lower = str(row[col_situacao]).strip().lower()
                                if 'transfer' in sit_lower or 'baixa' in sit_lower: sit_str = "Transferido"
                                elif 'inativo' in sit_lower: sit_str = "Inativo"
                                elif 'remanej' in sit_lower: sit_str = "Remanejado"
                            aluno = {'ra': ra_str, 'nome': nome_str, 'turma': turma_alunos, 'situacao': sit_str}
                            existe = df_alunos_existente[df_alunos_existente['ra'] == ra_str] if not df_alunos_existente.empty else pd.DataFrame()
                            if not existe.empty:
                                if existe.iloc[0].get('turma', '') == turma_alunos:
                                    if atualizar_aluno(ra_str, aluno): atualizados += 1
                                    else: erros += 1
                                else: ignorados += 1
                            else:
                                if salvar_aluno(aluno): novos += 1
                                else: erros += 1
                        except Exception: erros += 1
                        progress.progress((i + 1) / len(df_import))
                        status.text(f"Processando... {i + 1}/{len(df_import)} | ✅ Novos: {novos} | 🔄 Atualizados: {atualizados}")
                    progress.empty(); status.empty()
                    if novos + atualizados > 0:
                        st.success(f"🎉 Importação concluída! {novos} novos · {atualizados} atualizados")
                        st.balloons()
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("🆕 Novos", novos); col2.metric("🔄 Atualizados", atualizados)
                    col3.metric("⚠️ Ignorados", ignorados); col4.metric("❌ Erros", erros)
                    if novos + atualizados > 0: carregar_alunos.clear(); st.rerun()
        except Exception as e: st.error(f"❌ Erro ao processar arquivo: {str(e)}")
    else: st.info("📁 Selecione um arquivo CSV para começar.")
    if not df_alunos.empty:
        resumo = df_alunos.groupby('turma').size().reset_index(name='Total')
        resumo.columns = ['Turma', 'Total de Alunos']
        st.dataframe(resumo.sort_values('Turma'), use_container_width=True, hide_index=True)
    else: st.info("Nenhuma turma cadastrada ainda.")

# ======================================================
# PÁGINA 📋 GERENCIAR TURMAS
# ======================================================
elif menu == "📋 Gerenciar Turmas":
    page_header("📋 Gerenciar Turmas", "Visualize, edite e exclua turmas cadastradas", "#059669")
    if df_alunos.empty: st.info("📭 Nenhuma turma cadastrada. Use '📥 Importar Alunos' para começar.")
    else:
        turmas_info = df_alunos.groupby("turma").agg(total_alunos=("ra", "count")).reset_index().sort_values("turma")
        for _, row in turmas_info.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            with col1:
                st.markdown(f'<div style="background:white; border:1px solid var(--border); border-radius:var(--radius-md); padding:0.8rem 1rem; box-shadow:var(--shadow-sm); display:flex; align-items:center; gap:0.5rem; border-left:4px solid var(--primary);"><div style="font-size:1.2rem;">🏫</div><div><div style="font-weight:700; color:var(--text);">{row["turma"]}</div><div style="font-size:0.8rem; color:var(--text-muted);">{row["total_alunos"]} alunos</div></div></div>', unsafe_allow_html=True)
            with col2:
                if st.button("👁️ Ver", key=f"ver_turma_{row['turma']}"): st.session_state.turma_selecionada = row["turma"]; st.rerun()
            with col3:
                if st.button("✏️ Editar", key=f"edit_turma_{row['turma']}"): st.session_state.turma_para_editar = row["turma"]; st.rerun()
            with col4:
                if st.button("🔄 Substituir", key=f"sub_turma_{row['turma']}"): st.session_state.turma_para_substituir = row["turma"]; st.rerun()
            with col5:
                if st.button("🗑️ Deletar", key=f"del_turma_{row['turma']}"): st.session_state.turma_para_deletar = row["turma"]; st.rerun()

        if st.session_state.get("turma_selecionada"):
            turma = st.session_state.turma_selecionada
            st.markdown("---")
            st.subheader(f"👥 Alunos da Turma {turma}")
            st.dataframe(df_alunos[df_alunos["turma"] == turma][["ra", "nome", "situacao"]], use_container_width=True, hide_index=True)
            if st.button("❌ Fechar Visualização"): st.session_state.turma_selecionada = None; st.rerun()

        if st.session_state.get("turma_para_editar"):
            turma_antiga = st.session_state.turma_para_editar
            st.markdown("---")
            st.subheader(f"✏️ Editar Nome da Turma: {turma_antiga}")
            novo_nome = st.text_input("Novo nome da turma", value=turma_antiga)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar Alterações", type="primary"):
                    if not novo_nome.strip(): st.error("❌ Nome da turma não pode ser vazio.")
                    elif novo_nome == turma_antiga: st.warning("⚠️ O nome não foi alterado.")
                    else:
                        if editar_nome_turma(turma_antiga, novo_nome):
                            st.success(f"✅ Turma renomeada para {novo_nome}!"); st.session_state.turma_para_editar = None; st.rerun()
            with col2:
                if st.button("❌ Cancelar"): st.session_state.turma_para_editar = None; st.rerun()

        if st.session_state.get("turma_para_substituir"):
            turma = st.session_state.turma_para_substituir
            st.markdown("---")
            st.subheader(f"🔄 Substituir Turma {turma}")
            arquivo = st.file_uploader("Arquivo CSV", type=["csv"], key="substituir_csv")
            if arquivo is not None:
                try:
                    df_import = pd.read_csv(arquivo, sep=";", encoding="utf-8-sig", dtype=str)
                    st.success("✅ Arquivo carregado com sucesso.")
                    colunas = df_import.columns.tolist()
                    col_ra = next((c for c in colunas if 'ra' in c.lower() and 'dig' not in c.lower()), None)
                    col_nome = next((c for c in colunas if 'nome' in c.lower()), None)
                    col_situacao = next((c for c in colunas if 'situa' in c.lower()), None)
                    if col_ra is None or col_nome is None:
                        col1, col2 = st.columns(2)
                        with col1: col_ra = st.selectbox("Coluna do RA: ", colunas); col_nome = st.selectbox("Coluna do Nome: ", colunas)
                        with col2: col_situacao = st.selectbox("Coluna da Situação: ", ["Não usar"] + colunas)
                        if col_situacao == "Não usar": col_situacao = None
                    if st.button("🔄 Confirmar Substituição", type="primary"):
                        excluir_alunos_por_turma(turma)
                        inseridos = 0
                        for _, row in df_import.iterrows():
                            ra = ''.join(c for c in str(row[col_ra]) if c.isdigit())
                            nome = str(row[col_nome]).strip()
                            if not ra or not nome: continue
                            situacao = "Ativo"
                            if col_situacao and 'transfer' in str(row[col_situacao]).lower(): situacao = "Transferido"
                            if salvar_aluno({"ra": ra, "nome": nome, "turma": turma, "situacao": situacao}): inseridos += 1
                        st.success(f"✅ Turma substituída! {inseridos} aluno(s) importado(s).")
                        st.session_state.turma_para_substituir = None; carregar_alunos.clear(); st.rerun()
                except Exception as e: st.error(f"❌ Erro ao processar o arquivo: {e}")
            if st.button("❌ Cancelar Substituição"): st.session_state.turma_para_substituir = None; st.rerun()

        if st.session_state.get("turma_para_deletar"):
            turma = st.session_state.turma_para_deletar
            st.markdown("---")
            st.error(f"⚠️ Tem certeza que deseja excluir a turma **{turma}?**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão", type="primary"):
                    if excluir_alunos_por_turma(turma):
                        st.success(f"✅ Turma {turma} excluída!"); st.session_state.turma_para_deletar = None; carregar_alunos.clear(); st.rerun()
            with col2:
                if st.button("❌ Cancelar"): st.session_state.turma_para_deletar = None; st.rerun()

# ======================================================
# PÁGINA 👥 LISTA DE ALUNOS
# ======================================================
elif menu == "👥 Lista de Alunos":
    page_header("👥 Gerenciar Alunos", "Cadastro, edição e exclusão de estudantes", "#2563eb")
    tab1, tab2, tab3 = st.tabs(["📋 Listar Alunos", "➕ Cadastrar Aluno", "✏️ Editar/Excluir"])
    with tab1:
        if df_alunos.empty: st.info("📭 Nenhum aluno cadastrado.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1: filtro_turma = st.selectbox("🏫 Filtrar por Turma", ["Todas"] + sorted(df_alunos["turma"].dropna().unique().tolist()), key="filtro_turma_lista")
            with col2:
                df_alunos["situacao_norm"] = df_alunos["situacao"].str.strip().str.title() if "situacao" in df_alunos.columns else "Ativo"
                filtro_situacao = st.selectbox("📊 Situação", ["Ativos", "Todos"] + sorted(df_alunos["situacao_norm"].dropna().unique().tolist()), index=0, key="filtro_situacao_lista")
            with col3: busca_nome = st.text_input("🔍 Buscar por Nome ou RA", placeholder="Digite nome ou RA", key="busca_lista")
            df_view = df_alunos.copy()
            if filtro_turma != "Todas": df_view = df_view[df_view["turma"] == filtro_turma]
            if filtro_situacao == "Ativos": df_view = df_view[df_view["situacao_norm"] == "Ativo"]
            elif filtro_situacao != "Todos": df_view = df_view[df_view["situacao_norm"] == filtro_situacao]
            if busca_nome: df_view = df_view[df_view["nome"].str.contains(busca_nome, case=False, na=False) | df_view["ra"].astype(str).str.contains(busca_nome, na=False)]
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("👥 Total de Alunos", len(df_alunos))
            with col2: st.metric("✅ Alunos Ativos", len(df_alunos[df_alunos["situacao_norm"] == "Ativo"]))
            with col3: st.metric("📋 Exibindo", len(df_view))
            st.markdown("---")
            if df_view.empty: st.info("📭 Nenhum aluno encontrado com os filtros selecionados.")
            else:
                st.dataframe(df_view.drop(columns=["situacao_norm"], errors="ignore")[["ra", "nome", "turma", "situacao"]].sort_values(["turma", "nome"]), use_container_width=True, hide_index=True)
                if st.button("📥 Exportar Lista (CSV)", key="btn_exportar_csv_lista"):
                    csv = df_view.drop(columns=["situacao_norm"], errors="ignore").to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(label="📥 Baixar CSV", data=csv, file_name=f"alunos_{filtro_situacao.lower()}_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    with tab2:
        with st.form("form_cadastrar_aluno"):
            col1, col2 = st.columns(2)
            with col1: ra = st.text_input("RA *", placeholder="Ex: 123456"); nome = st.text_input("Nome Completo *", placeholder="Ex: João da Silva"); turma = st.text_input("Turma *", placeholder="Ex: 6º Ano A")
            with col2: situacao = st.selectbox("Situação", ["Ativo", "Transferido", "Inativo", "Remanejado"], index=0); responsavel = st.text_input("Responsável", placeholder="Nome do responsável")
            if st.form_submit_button("💾 Salvar Aluno", type="primary"):
                if not ra or not nome or not turma: st.error("❌ RA, Nome e Turma são obrigatórios!")
                elif not df_alunos.empty and ra.strip() in df_alunos["ra"].astype(str).values: st.error(f"❌ RA {ra} já está cadastrado!")
                else:
                    if salvar_aluno({'ra': ra.strip(), 'nome': nome.strip(), 'turma': turma.strip(), 'situacao': situacao, 'responsavel': responsavel.strip() if responsavel else None}):
                        st.success("✅ Aluno cadastrado com sucesso!"); carregar_alunos.clear(); st.rerun()
                    else: st.error("❌ Erro ao salvar aluno.")
    with tab3:
        if df_alunos.empty: st.info("📭 Nenhum aluno cadastrado.")
        else:
            df_busca = df_alunos[df_alunos["situacao_norm"] == "Ativo"] if "situacao_norm" in df_alunos.columns else df_alunos
            if df_busca.empty: df_busca = df_alunos
            df_busca = df_busca.sort_values(["turma", "nome"])
            opcoes_alunos = [f"{row['nome']} - {row['turma']} (RA: {row['ra']}) [{row.get('situacao','Ativo')}]" for _, row in df_busca.iterrows()]
            aluno_selecionado = st.selectbox("Selecione o Aluno", opcoes_alunos, key="aluno_editar")
            if aluno_selecionado:
                ra_selecionado = aluno_selecionado.split("(RA: ")[1].split(")")[0].strip()
                aluno_info = df_alunos[df_alunos["ra"] == ra_selecionado].iloc[0]
                st.markdown("---")
                with st.form("form_editar_aluno"):
                    col1, col2 = st.columns(2)
                    with col1:
                        novo_nome = st.text_input("Nome *", value=aluno_info.get("nome", ""))
                        nova_turma = st.text_input("Turma *", value=aluno_info.get("turma", ""))
                        sit_atual = aluno_info.get("situacao", "Ativo")
                        if sit_atual not in ["Ativo", "Transferido", "Inativo", "Remanejado"]: sit_atual = "Ativo"
                        nova_situacao = st.selectbox("Situação", ["Ativo", "Transferido", "Inativo", "Remanejado"], index=["Ativo", "Transferido", "Inativo", "Remanejado"].index(sit_atual))
                    with col2: novo_responsavel = st.text_input("Responsável", value=str(aluno_info.get("responsavel", "")))
                    st.info(f"**RA:** {aluno_info.get('ra')} (não pode ser alterado)")
                    if st.form_submit_button("💾 Salvar Alterações", type="primary"):
                        if atualizar_aluno(str(aluno_info['ra']), {'nome': novo_nome.strip(), 'turma': nova_turma.strip(), 'situacao': nova_situacao, 'responsavel': novo_responsavel.strip() if novo_responsavel else None}):
                            st.success("✅ Aluno atualizado!"); carregar_alunos.clear(); st.rerun()
                        else: st.error("❌ Erro ao atualizar aluno.")
                st.markdown("---")
                st.subheader("🗑️ Excluir Aluno")
                if st.button("🗑️ Excluir Aluno", type="secondary", key="btn_excluir_aluno_tab3"): st.session_state.confirmar_exclusao_aluno = aluno_info['ra']; st.rerun()
                if st.session_state.get("confirmar_exclusao_aluno"):
                    ra_excluir = st.session_state.confirmar_exclusao_aluno
                    aluno_excluir = df_alunos[df_alunos["ra"] == ra_excluir].iloc[0] if not df_alunos[df_alunos["ra"] == ra_excluir].empty else None
                    if aluno_excluir is not None:
                        st.error(f"⚠️ Confirmar exclusão de **{aluno_excluir['nome']}**?")
                        col1, col2 = st.columns(2)
                        with col1:
                            senha = st.text_input("Digite a senha para confirmar: ", type="password", key="senha_excluir_aluno_tab3")
                            if st.button("✅ Confirmar Exclusão", type="primary", key="confirm_excluir_aluno_tab3"):
                                if senha == SENHA_EXCLUSAO:
                                    if _supabase_mutation("DELETE", f"alunos?ra=eq.{ra_excluir}", None, "excluir aluno"):
                                        st.success("✅ Aluno excluído!"); carregar_alunos.clear(); del st.session_state.confirmar_exclusao_aluno; st.rerun()
                                    else: st.error("❌ Erro ao excluir aluno.")
                                else: st.error("❌ Senha incorreta!")
                        with col2:
                            if st.button("❌ Cancelar", key="cancel_excluir_aluno_tab3"): del st.session_state.confirmar_exclusao_aluno; st.rerun()

# ======================================================
# PÁGINA 📝 REGISTRAR OCORRÊNCIA
# ======================================================
elif menu == "📝 Registrar Ocorrência":
    page_header("📝 Registrar Ocorrência", "Protocolo 179 — Preenchimento assistido por IA", "#dc2626")
    if st.session_state.ocorrencia_salva_sucesso:
        st.success("✅ Ocorrência(s) registrada(s) com sucesso!"); st.session_state.ocorrencia_salva_sucesso = False
    if df_alunos.empty or df_professores.empty: st.warning("⚠️ Cadastre alunos e professores antes de registrar ocorrências."); st.stop()
    tz_sp = pytz.timezone("America/Sao_Paulo"); agora = datetime.now(tz_sp)
    col1, col2 = st.columns(2)
    with col1: data_fato = st.date_input("📅 Data do fato", value=agora.date(), key="data_fato")
    with col2: hora_fato = st.time_input("⏰ Hora do fato", value=agora.time(), key="hora_fato")
    data_str = f"{data_fato.strftime('%d/%m/%Y')} {hora_fato.strftime('%H:%M')}"
    turmas_disponiveis = sorted(df_alunos["turma"].unique().tolist())
    turmas_sel = st.multiselect("🏫 Turma(s)", turmas_disponiveis, default=[turmas_disponiveis[0]] if turmas_disponiveis else [], key="turmas_sel")
    if not turmas_sel: st.warning("⚠️ Selecione ao menos uma turma."); st.stop()
    alunos_turma = df_alunos[df_alunos["turma"].isin(turmas_sel)]
    if "situacao" in alunos_turma.columns:
        alunos_turma["situacao_norm"] = alunos_turma["situacao"].str.strip().str.title()
        alunos_turma = alunos_turma[alunos_turma["situacao_norm"] == "Ativo"]
    modo_multiplo = st.checkbox("Registrar para múltiplos estudantes", key="modo_multiplo")
    if modo_multiplo: alunos_selecionados = st.multiselect("Selecione os estudantes", alunos_turma["nome"].tolist(), key="alunos_multiplos")
    else:
        aluno_unico = st.selectbox("Aluno", alunos_turma["nome"].tolist(), key="aluno_unico")
        alunos_selecionados = [aluno_unico] if aluno_unico else []
    if not alunos_selecionados: st.warning("⚠️ Selecione ao menos um estudante."); st.stop()
    prof = st.selectbox("Professor 👨‍🏫", df_professores["nome"].tolist(), key="professor_sel")
    busca = st.text_input("🔍 Buscar infração", placeholder="Ex: celular, bullying, atraso...", key="busca_infracao")
    if busca:
        grupos_filtrados = buscar_infracao_fuzzy(busca, PROTOCOLO_179)
        grupo = st.selectbox("Grupo", list(grupos_filtrados.keys()) if grupos_filtrados else list(PROTOCOLO_179.keys()), key="grupo_infracao")
        infracoes = grupos_filtrados.get(grupo, PROTOCOLO_179.get(grupo, {}))
    else:
        grupo = st.selectbox("Grupo", list(PROTOCOLO_179.keys()), key="grupo_infracao")
        infracoes = PROTOCOLO_179[grupo]
    infracao_principal = st.selectbox("Infração", list(infracoes.keys()), key="infracao_principal")
    dados_infracao = infracoes[infracao_principal]
    gravidade_sugerida = dados_infracao["gravidade"]
    encaminhamento_sugerido = dados_infracao["encaminhamento"]
    cor_gravidade = CORES_GRAVIDADE.get(gravidade_sugerida, "#2563eb")
    st.markdown(f'<div style="display:inline-flex; align-items:center; gap:0.5rem; background:{cor_gravidade}15; border:1px solid {cor_gravidade}40; border-left:3px solid {cor_gravidade}; border-radius:var(--radius-sm); padding:0.4rem 0.8rem; margin:0.5rem 0;"><span style="font-weight:700; color:{cor_gravidade};">{infracao_principal}</span></div>', unsafe_allow_html=True)
    _encam_html = encaminhamento_sugerido.replace('\n', '<br>').replace("✅", "<span style='color:#10b981;'>✅</span>").replace("⚖️", "<span style='color:#7c3aed;'>⚖️</span>").replace("🚨", "<span style='color:#ef4444;'>🚨</span>")
    st.markdown(f"""
    <div style="background:#f8fafc; border:1px solid var(--border); border-left:4px solid var(--primary); border-radius:var(--radius-md); padding:1rem; margin:0.5rem 0;">
        <div style="font-size:0.8rem; font-weight:600; text-transform:uppercase; color:var(--text-muted); margin-bottom:0.3rem;">Protocolo 179 — Preenchimento Automático</div>
        <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.5rem;">
            <div><div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase;">Infração</div><div style="font-weight:600;">{infracao_principal}</div></div>
            <div><div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase;">Gravidade</div><span style="background:{cor_gravidade}15; color:{cor_gravidade}; border:1px solid {cor_gravidade}40; border-radius:var(--radius-sm); padding:0.2rem 0.6rem; font-size:0.8rem; font-weight:600;">{gravidade_sugerida}</span></div>
        </div>
        <div style="font-size:0.9rem; color:var(--text); line-height:1.5;">{_encam_html}</div>
    </div>
    """, unsafe_allow_html=True)
    gravidade = st.selectbox("Gravidade", ["Leve", "Média", "Grave", "Gravíssima"], index=["Leve", "Média", "Grave", "Gravíssima"].index(gravidade_sugerida) if gravidade_sugerida in ["Leve", "Média", "Grave", "Gravíssima"] else 0, key="gravidade_sel")
    if gravidade != gravidade_sugerida: st.warning(f"⚠️ Gravidade alterada de {gravidade_sugerida} para {gravidade}.")
    encam = st.text_area("🔀 Encaminhamentos", value=encaminhamento_sugerido, height=100, key="encaminhamento")
    relato = st.text_area("📝 Relato dos fatos", height=120, placeholder="Descreva os fatos de forma clara e objetiva...", key="relato")
    if st.button("💾 Salvar Ocorrência(s)", type="primary"):
        if not prof or not relato.strip(): st.error("❌ Preencha professor e relato.")
        else:
            salvas = duplicadas = 0
            for turma in turmas_sel:
                for aluno in alunos_selecionados:
                    registro = df_alunos[(df_alunos["nome"] == aluno) & (df_alunos["turma"] == turma)]
                    if registro.empty: continue
                    ra = registro["ra"].values[0]
                    if verificar_ocorrencia_duplicada(ra, infracao_principal, data_str, df_ocorrencias): duplicadas += 1; continue
                    if salvar_ocorrencia({"data": data_str, "aluno": aluno, "ra": ra, "turma": turma, "categoria": infracao_principal, "gravidade": gravidade, "relato": relato, "encaminhamento": encam, "professor": prof}):
                        salvas += 1
                        if st.session_state.backup_manager: st.session_state.backup_manager.criar_backup()
            if salvas > 0:
                st.session_state.ocorrencia_salva_sucesso = True; show_toast(f"{salvas} ocorrência(s) registrada(s)!"); st.session_state.registros_ocorrencias += salvas
                if st.session_state.registros_ocorrencias >= 1: verificar_conquista("primeiro_registro")
                if st.session_state.registros_ocorrencias >= 10: verificar_conquista("10_ocorrencias")
                if st.session_state.registros_ocorrencias >= 50: verificar_conquista("50_ocorrencias")
            if duplicadas > 0: st.warning(f"⚠️ {duplicadas} ocorrência(s) duplicada(s) ignorada(s).")
            carregar_ocorrencias.clear(); st.rerun()

# ======================================================
# PÁGINA 📋 HISTÓRICO DE OCORRÊNCIAS
# ======================================================
elif menu == "📋 Histórico de Ocorrências":
    page_header("📋 Histórico de Ocorrências", "Consulte, edite e exclua registros de ocorrências", "#d97706")
    if "mensagem_exclusao" in st.session_state: st.success(st.session_state.mensagem_exclusao); del st.session_state.mensagem_exclusao
    if df_ocorrencias.empty: st.info("📭 Nenhuma ocorrência registrada."); st.stop()
    col1, col2, col3 = st.columns(3)
    with col1: filtro_turma = st.selectbox("🏫 Turma", ["Todas"] + sorted(df_ocorrencias["turma"].dropna().unique().tolist()))
    with col2: filtro_gravidade = st.selectbox("⚖️ Gravidade", ["Todas"] + sorted(df_ocorrencias["gravidade"].dropna().unique().tolist()))
    with col3: filtro_categoria = st.selectbox("📋 Categoria", ["Todas"] + sorted(df_ocorrencias["categoria"].dropna().unique().tolist()))
    df_view = df_ocorrencias.copy()
    if filtro_turma != "Todas": df_view = df_view[df_view["turma"] == filtro_turma]
    if filtro_gravidade != "Todas": df_view = df_view[df_view["gravidade"] == filtro_gravidade]
    if filtro_categoria != "Todas": df_view = df_view[df_view["categoria"] == filtro_categoria]
    st.markdown(f'<div style="display:inline-flex; align-items:center; gap:0.5rem; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-sm); padding:0.4rem 0.8rem; margin-bottom:1rem; font-weight:600;">📊 {len(df_view)} ocorrências encontradas</div>', unsafe_allow_html=True)
    st.dataframe(df_view, use_container_width=True, hide_index=True)
    st.markdown("---")
    col_excluir, col_editar = st.columns(2)
    with col_excluir:
        st.markdown("### 🗑️ Excluir Ocorrência")
        opcoes_excluir = [f"{row['id']} - {row['aluno']} - {row['data']} - {row['categoria']}" for _, row in df_view.iterrows()]
        if opcoes_excluir:
            opcao_sel = st.selectbox("Selecione a ocorrência", opcoes_excluir, key="select_excluir")
            id_excluir = int(opcao_sel.split(" - ")[0])
            senha = st.text_input("🔒 Senha para excluir", type="password", key="senha_excluir")
            if st.button("🗑️ Excluir Ocorrência", type="secondary"):
                if senha != SENHA_EXCLUSAO: st.error("❌ Senha incorreta!")
                else:
                    if excluir_ocorrencia(id_excluir): st.session_state.mensagem_exclusao = f"✅ Ocorrência {id_excluir} excluída!"; carregar_ocorrencias.clear(); st.rerun()
    with col_editar:
        st.markdown("### ✏️ Editar Ocorrência")
        opcoes_editar = [f"{row['id']} - {row['aluno']} - {row['data']} - {row['categoria']}" for _, row in df_view.iterrows()]
        if opcoes_editar:
            opcao_edit = st.selectbox("Selecione a ocorrência", opcoes_editar, key="select_editar")
            id_editar = int(opcao_edit.split(" - ")[0])
            if st.button("✏️ Carregar para Edição"): st.session_state.editando_id = id_editar; st.session_state.dados_edicao = df_view[df_view["id"] == id_editar].iloc[0].to_dict(); st.rerun()
    if st.session_state.get("editando_id") and st.session_state.get("dados_edicao"):
        dados = st.session_state.dados_edicao
        st.markdown("---")
        st.subheader(f"✏️ Editando Ocorrência ID {st.session_state.editando_id}")
        novo_relato = st.text_area("📝 Relato", value=str(dados.get("relato", "")), height=100)
        novo_encam = st.text_area("🔀 Encaminhamentos", value=str(dados.get("encaminhamento", "")), height=100)
        nova_gravidade = st.selectbox("⚖️ Gravidade", ["Leve", "Média", "Grave", "Gravíssima"], index=["Leve", "Média", "Grave", "Gravíssima"].index(dados.get("gravidade", "Leve")))
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Alterações", type="primary"):
                if editar_ocorrencia(st.session_state.editando_id, {"relato": novo_relato, "encaminhamento": novo_encam, "gravidade": nova_gravidade}):
                    st.success("✅ Ocorrência atualizada!"); carregar_ocorrencias.clear(); st.session_state.editando_id = None; st.session_state.dados_edicao = None; st.rerun()
        with col2:
            if st.button("❌ Cancelar Edição"): st.session_state.editando_id = None; st.session_state.dados_edicao = None; st.rerun()

# ======================================================
# PÁGINA 📄 COMUNICADO AOS PAIS
# ======================================================
elif menu == "📄 Comunicado aos Pais":
    page_header("📄 Comunicado aos Pais", "Gere comunicados individuais ou em lote para os responsáveis", "#7c3aed")
    if df_alunos.empty or df_ocorrencias.empty: st.warning("⚠️ Cadastre alunos e ocorrências antes de gerar comunicados."); st.stop()
    modo = st.radio("Modo de geração", ["👤 Individual", "🏫 Por Turma(s)"], horizontal=True)
    medidas_opcoes = ["Mediação de conflitos", "Registro em ata", "Notificação aos pais", "Atividades de reflexão", "Termo de compromisso", "Ata circunstanciada", "Conselho Tutelar", "Mudança de turma", "Acompanhamento psicológico", "Reunião com pais", "Afastamento temporário", "B.O. registrado", "Diretoria de Ensino", "Medidas protetivas"]
    if modo == "👤 Individual":
        busca = st.text_input("🔍 Buscar aluno por nome ou RA", placeholder="Digite nome ou RA do aluno")
        df_filtrado = df_alunos[df_alunos["nome"].str.contains(busca, case=False, na=False) | df_alunos["ra"].astype(str).str.contains(busca, na=False)] if busca else df_alunos
        if df_filtrado.empty: st.warning("⚠️ Nenhum aluno encontrado."); st.stop()
        aluno_sel = st.selectbox("Aluno", df_filtrado["nome"].tolist())
        aluno_info = df_alunos[df_alunos["nome"] == aluno_sel].iloc[0]
        ra_aluno = aluno_info["ra"]
        ocorrencias_aluno = df_ocorrencias[df_ocorrencias["ra"] == ra_aluno]
        if ocorrencias_aluno.empty: st.info("ℹ️ Este aluno não possui ocorrências."); st.stop()
        lista_ocorrencias = (ocorrencias_aluno["id"].astype(str) + " - " + ocorrencias_aluno["data"] + " - " + ocorrencias_aluno["categoria"])
        occ_sel = st.selectbox("Selecione a ocorrência", lista_ocorrencias.tolist())
        occ_info = ocorrencias_aluno.iloc[lista_ocorrencias.tolist().index(occ_sel)]
        st.subheader("⚖️ Medidas Aplicadas")
        medidas_aplicadas = []
        cols = st.columns(3)
        for i, medida in enumerate(medidas_opcoes):
            with cols[i % 3]:
                if st.checkbox(medida, key=f"medida_ind_{medida}"): medidas_aplicadas.append(medida)
        observacoes = st.text_area("📝 Observações adicionais", height=80)
        if st.button("📄 Gerar Comunicado (PDF)", type="primary"):
            pdf_buffer = gerar_pdf_comunicado({"nome": aluno_info["nome"], "ra": ra_aluno, "turma": aluno_info["turma"], "total_ocorrencias": len(ocorrencias_aluno)}, {"data": occ_info["data"], "categoria": occ_info["categoria"], "gravidade": occ_info["gravidade"], "professor": occ_info["professor"], "relato": occ_info["relato"], "encaminhamento": occ_info["encaminhamento"]}, "\n".join(medidas_aplicadas), observacoes, df_responsaveis)
            st.download_button("📥 Baixar Comunicado (PDF)", data=pdf_buffer, file_name=f"Comunicado_{ra_aluno}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
            st.success("✅ Comunicado gerado com sucesso!")
    else:
        turmas_sel = st.multiselect("Selecione as turmas", sorted(df_alunos["turma"].unique().tolist()))
        if not turmas_sel: st.info("ℹ️ Selecione ao menos uma turma."); st.stop()
        alunos_turmas = df_alunos[df_alunos["turma"].isin(turmas_sel)]
        alunos_com_ocorrencias = [aluno for _, aluno in alunos_turmas.iterrows() if not df_ocorrencias[df_ocorrencias["ra"] == aluno["ra"]].empty]
        if not alunos_com_ocorrencias: st.warning("⚠️ Nenhum aluno com ocorrência nas turmas selecionadas."); st.stop()
        st.success(f"📊 {len(alunos_com_ocorrencias)} alunos com ocorrências encontrados.")
        st.subheader("⚖️ Medidas para o Lote")
        medidas_aplicadas = []
        cols = st.columns(3)
        for i, medida in enumerate(medidas_opcoes):
            with cols[i % 3]:
                if st.checkbox(medida, key=f"medida_lote_{medida}"): medidas_aplicadas.append(medida)
        observacoes = st.text_area("📝 Observações gerais", height=80)
        if st.button("📦 Gerar Comunicados em Lote (ZIP)", type="primary"):
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for aluno in alunos_com_ocorrencias:
                    ra = aluno["ra"]
                    ocorrencias = df_ocorrencias[df_ocorrencias["ra"] == ra].sort_values("data", ascending=False)
                    occ = ocorrencias.iloc[0]
                    pdf = gerar_pdf_comunicado({"nome": aluno["nome"], "ra": ra, "turma": aluno["turma"], "total_ocorrencias": len(ocorrencias)}, {"data": occ["data"], "categoria": occ["categoria"], "gravidade": occ["gravidade"], "professor": occ["professor"], "relato": occ["relato"], "encaminhamento": occ["encaminhamento"]}, "\n".join(medidas_aplicadas), observacoes, df_responsaveis)
                    zip_file.writestr(f"Comunicado_{ra}_{aluno['nome'].replace(' ', '_')}.pdf", pdf.getvalue())
            zip_buffer.seek(0)
            st.download_button("📥 Baixar ZIP de Comunicados", data=zip_buffer, file_name=f"Comunicados_{datetime.now().strftime('%Y%m%d_%H%M')}.zip", mime="application/zip")
            st.success("✅ Comunicados em lote gerados com sucesso!")

# ======================================================
# PÁGINA 📊 GRÁFICOS E INDICADORES
# ======================================================
elif menu == "📊 Gráficos e Indicadores":
    page_header("📊 Gráficos e Indicadores", "Análise visual das ocorrências e indicadores escolares", "#0891b2")
    if df_ocorrencias.empty: st.info("📭 Nenhuma ocorrência registrada."); st.stop()
    col1, col2, col3 = st.columns(3)
    with col1: filtro_periodo = st.selectbox("📅 Período", ["Todos", "Últimos 30 dias", "Este ano", "Personalizado"])
    with col2: filtro_turma = st.selectbox("🏫 Turma", ["Todas"] + sorted(df_ocorrencias["turma"].dropna().unique().tolist()))
    with col3: filtro_gravidade = st.selectbox("⚖️ Gravidade", ["Todas"] + sorted(df_ocorrencias["gravidade"].dropna().unique().tolist()))
    df_filtro = df_ocorrencias.copy()
    df_filtro["data_dt"] = pd.to_datetime(df_filtro["data"], format="%d/%m/%Y %H:%M", errors="coerce")
    agora = datetime.now()
    if filtro_periodo == "Últimos 30 dias": df_filtro = df_filtro[df_filtro["data_dt"] >= agora - timedelta(days=30)]
    elif filtro_periodo == "Este ano": df_filtro = df_filtro[df_filtro["data_dt"].dt.year == agora.year]
    elif filtro_periodo == "Personalizado":
        col1, col2 = st.columns(2)
        with col1: data_ini = st.date_input("Data inicial", value=agora.date() - timedelta(days=30))
        with col2: data_fim = st.date_input("Data final", value=agora.date())
        df_filtro = df_filtro[(df_filtro["data_dt"].dt.date >= data_ini) & (df_filtro["data_dt"].dt.date <= data_fim)]
    if filtro_turma != "Todas": df_filtro = df_filtro[df_filtro["turma"] == filtro_turma]
    if filtro_gravidade != "Todas": df_filtro = df_filtro[df_filtro["gravidade"] == filtro_gravidade]
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(f'<div class="metric-card"><div style="font-size:1.2rem;">📊</div><div class="metric-value">{len(df_filtro)}</div><div class="metric-label">Total</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div style="font-size:1.2rem;">🚨</div><div class="metric-value">{len(df_filtro[df_filtro["gravidade"]=="Gravíssima"]) if not df_filtro.empty else 0}</div><div class="metric-label">Gravíssimas</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div style="font-size:1.2rem;">⚠️</div><div class="metric-value">{len(df_filtro[df_filtro["gravidade"]=="Grave"]) if not df_filtro.empty else 0}</div><div class="metric-label">Graves</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="metric-card"><div style="font-size:1.2rem;">🏫</div><div class="metric-value">{df_filtro["turma"].nunique() if not df_filtro.empty else 0}</div><div class="metric-label">Turmas</div></div>', unsafe_allow_html=True)
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Por Categoria")
        contagem_cat = df_filtro["categoria"].value_counts().head(10)
        if not contagem_cat.empty: st.plotly_chart(px.bar(x=contagem_cat.values, y=contagem_cat.index, orientation='h', color=contagem_cat.values, color_continuous_scale='Blues').update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter', size=12), margin=dict(t=10,b=10,l=0,r=0)), use_container_width=True)
    with col2:
        st.subheader("⚖️ Por Gravidade")
        contagem_grav = df_filtro["gravidade"].value_counts()
        if not contagem_grav.empty: st.plotly_chart(px.pie(values=contagem_grav.values, names=contagem_grav.index, color_discrete_sequence=['#10b981','#f59e0b','#f97316','#ef4444'], hole=0.45).update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter', size=12)), use_container_width=True)
    st.markdown("---")
    st.subheader("📈 Evolução Temporal")
    df_filtro["data_apenas"] = df_filtro["data_dt"].dt.date
    evolucao = df_filtro.groupby("data_apenas").size().reset_index(name="Quantidade")
    if not evolucao.empty: st.plotly_chart(px.line(evolucao, x="data_apenas", y="Quantidade", markers=True).update_traces(line_color="#2563eb", line_width=2.5, marker=dict(size=7)).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter', size=12)), use_container_width=True)
    st.markdown("---")
    st.subheader("🏫 Top 10 Turmas")
    top_turmas = df_filtro['turma'].value_counts().head(10)
    if not top_turmas.empty: st.plotly_chart(px.bar(x=top_turmas.values, y=top_turmas.index, orientation='h', color=top_turmas.values, color_continuous_scale='Greens').update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter', size=12)), use_container_width=True)
    st.markdown("---")
    st.subheader("👤 Top 10 Alunos")
    top_alunos = df_filtro['aluno'].value_counts().head(10)
    if not top_alunos.empty: st.plotly_chart(px.bar(x=top_alunos.values, y=top_alunos.index, orientation='h', color=top_alunos.values, color_continuous_scale='Reds').update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(family='Inter', size=12)), use_container_width=True)
    st.markdown("---")
    csv = df_filtro.drop(columns=["data_dt", "data_apenas"], errors="ignore").to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button("📥 Baixar CSV", data=csv, file_name=f"ocorrencias_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

# ======================================================
# PÁGINA 🖨️ IMPRIMIR PDF
# ======================================================
elif menu == "🖨️ Imprimir PDF":
    page_header("🖨️ Gerar PDFs de Ocorrências", "Exporte relatórios em PDF ou em lote (ZIP)", "#334155")
    if df_ocorrencias.empty: st.info("📭 Nenhuma ocorrência registrada."); st.stop()
    col1, col2 = st.columns(2)
    with col1: data_inicio = st.date_input("📅 Data inicial", value=datetime.now() - timedelta(days=30)); data_fim = st.date_input("📅 Data final", value=datetime.now())
    with col2: alunos_sel = st.multiselect("👥 Alunos", sorted(df_ocorrencias["aluno"].unique().tolist())); professores_sel = st.multiselect("👨‍🏫 Professores", sorted(df_ocorrencias["professor"].unique().tolist()))
    df_pdf = df_ocorrencias.copy()
    df_pdf["data_dt"] = pd.to_datetime(df_pdf["data"], format="%d/%m/%Y %H:%M", errors="coerce")
    df_pdf = df_pdf[(df_pdf["data_dt"] >= pd.Timestamp(data_inicio)) & (df_pdf["data_dt"] <= pd.Timestamp(data_fim) + pd.Timedelta(days=1))]
    if alunos_sel: df_pdf = df_pdf[df_pdf["aluno"].isin(alunos_sel)]
    if professores_sel: df_pdf = df_pdf[df_pdf["professor"].isin(professores_sel)]
    df_pdf = df_pdf.drop(columns=["data_dt"], errors="ignore")
    if df_pdf.empty: st.warning("⚠️ Nenhuma ocorrência encontrada."); st.stop()
    st.write(f"Total: **{len(df_pdf)}**")
    st.dataframe(df_pdf[["id", "data", "aluno", "turma", "categoria", "gravidade"]], use_container_width=True, hide_index=True)
    st.markdown("---")
    st.subheader("📦 Gerar PDFs em Lote")
    if st.button("📦 Gerar ZIP de PDFs", type="primary"):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for _, occ in df_pdf.iterrows():
                pdf = gerar_pdf_ocorrencia(occ.to_dict(), df_responsaveis)
                zip_file.writestr(f"Ocorrencia_{occ['id']}_{occ['aluno'].replace(' ', '_')}.pdf", pdf.getvalue())
        zip_buffer.seek(0)
        st.download_button("📥 Baixar ZIP com PDFs", data=zip_buffer, file_name=f"Ocorrencias_{datetime.now().strftime('%Y%m%d_%H%M')}.zip", mime="application/zip")
    st.markdown("---")
    st.subheader("📄 Gerar PDF Individual")
    lista_ind = (df_ocorrencias["id"].astype(str) + " - " + df_ocorrencias["aluno"] + " - " + df_ocorrencias["data"])
    opcao_ind = st.selectbox("Selecione a ocorrência", lista_ind.tolist())
    id_ind = int(opcao_ind.split(" - ")[0])
    occ_ind = df_ocorrencias[df_ocorrencias["id"] == id_ind].iloc[0]
    if st.button("📄 Gerar PDF Individual", type="primary"):
        pdf = gerar_pdf_ocorrencia(occ_ind.to_dict(), df_responsaveis)
        st.download_button("📥 Baixar PDF", data=pdf, file_name=f"Ocorrencia_{occ_ind['id']}.pdf", mime="application/pdf")

# ======================================================
# PÁGINA 👨‍🏫 CADASTRAR PROFESSORES
# ======================================================
elif menu == "👨‍🏫 Cadastrar Professores":
    page_header("👨‍🏫 Cadastrar Professores", "Gerencie o cadastro de professores e coordenadores", "#059669")
    if st.session_state.professor_salvo_sucesso: st.success(f"✅ {st.session_state.cargo_professor_salvo} {st.session_state.nome_professor_salvo} cadastrado!"); st.session_state.professor_salvo_sucesso = False
    with st.expander("📥 Importar Professores em Massa", expanded=False):
        texto_professores = st.text_area("Lista de professores:", height=150, placeholder="Maria Silva\nJoão Pereira")
        if st.button("📥 Importar Professores"):
            if not texto_professores.strip(): st.error("❌ Cole ao menos um nome.")
            else:
                nomes = [n.strip() for n in texto_professores.splitlines() if n.strip()]
                inseridos = sum(1 for nome in nomes if nome.lower() not in (df_professores["nome"].str.lower().tolist() if not df_professores.empty else []) and salvar_professor({"nome": nome, "cargo": "Professor"}))
                if inseridos > 0: st.success(f"✅ {inseridos} professor(es) importado(s)."); carregar_professores.clear(); st.rerun()
    st.markdown("---")
    if st.session_state.get("editando_prof"):
        prof_edit = df_professores[df_professores["id"] == st.session_state.editando_prof].iloc[0]
        st.subheader("✏️ Editar Professor")
        nome_prof = st.text_input("Nome *", value=prof_edit.get("nome", ""))
        cargo_prof = st.selectbox("Cargo", ["Professor", "Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora", "Outro"], index=["Professor", "Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora", "Outro"].index(prof_edit.get("cargo", "Professor")))
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Alterações", type="primary"):
                if not nome_prof.strip(): st.error("❌ Nome é obrigatório.")
                elif atualizar_professor(st.session_state.editando_prof, {"nome": nome_prof, "cargo": cargo_prof}): st.success("✅ Professor atualizado!"); st.session_state.editando_prof = None; carregar_professores.clear(); st.rerun()
        with col2:
            if st.button("❌ Cancelar"): st.session_state.editando_prof = None; st.rerun()
    else:
        st.subheader("➕ Novo Professor")
        nome_prof = st.text_input("Nome *", placeholder="Ex: João da Silva")
        cargo_prof = st.selectbox("Cargo", ["Professor", "Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora", "Outro"])
        if st.button("💾 Salvar Cadastro", type="primary"):
            if not nome_prof.strip(): st.error("❌ Nome é obrigatório.")
            elif nome_prof.lower() in (df_professores["nome"].str.lower().tolist() if not df_professores.empty else []): st.error("❌ Já existe um professor com esse nome.")
            else:
                if salvar_professor({"nome": nome_prof, "cargo": cargo_prof}): st.session_state.professor_salvo_sucesso = True; st.session_state.nome_professor_salvo = nome_prof; st.session_state.cargo_professor_salvo = cargo_prof; carregar_professores.clear(); st.rerun()
    st.markdown("---")
    st.markdown('<h3 style="margin-bottom:1rem;">📋 Professores Cadastrados</h3>', unsafe_allow_html=True)
    if not df_professores.empty:
        for _, prof in df_professores.iterrows():
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1:
                cargo_display = prof.get('cargo', 'Professor') or 'Professor'
                st.markdown(f'<div style="display:flex;align-items:center;gap:0.5rem;padding:0.4rem 0;"><div style="width:28px;height:28px;background:#f1f5f9;border-radius:6px;display:flex;align-items:center;justify-content:center;">👤</div><div><div style="font-weight:600;">{prof["nome"]}</div><div style="font-size:0.75rem;color:var(--text-muted);">{cargo_display}</div></div></div>', unsafe_allow_html=True)
            with col2:
                if st.button("✏️", key=f"edit_prof_{prof['id']}"): st.session_state.editando_prof = prof["id"]; st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_prof_{prof['id']}"): st.session_state.confirmar_exclusao_prof = prof["id"]; st.rerun()
        if st.session_state.get("confirmar_exclusao_prof"):
            prof_id = st.session_state.confirmar_exclusao_prof
            prof_excluir = df_professores[df_professores["id"] == prof_id].iloc[0]
            st.warning(f"⚠️ Confirma excluir **{prof_excluir['nome']}**?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão", type="primary"):
                    if excluir_professor(prof_id): st.success("✅ Professor excluído!"); del st.session_state.confirmar_exclusao_prof; carregar_professores.clear(); st.rerun()
            with col2:
                if st.button("❌ Cancelar"): del st.session_state.confirmar_exclusao_prof; st.rerun()
    else: st.info("📭 Nenhum professor cadastrado.")

# ======================================================
# PÁGINA 👤 CADASTRAR ASSINATURAS
# ======================================================
elif menu == "👤 Cadastrar Assinaturas":
    page_header("👤 Cadastrar Assinaturas", "Registre os responsáveis pelas assinaturas oficiais", "#0891b2")
    if st.session_state.responsavel_salvo_sucesso: st.success(f"✅ {st.session_state.cargo_responsavel_salvo} {st.session_state.nome_responsavel_salvo} cadastrado!"); st.session_state.responsavel_salvo_sucesso = False
    st.markdown("---")
    if st.session_state.get("editando_resp"):
        resp_edit = df_responsaveis[df_responsaveis["id"] == st.session_state.editando_resp].iloc[0]
        st.subheader("✏️ Editar Responsável")
        nome_resp = st.text_input("Nome *", value=resp_edit.get("nome", ""))
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Alterações", type="primary"):
                if not nome_resp.strip(): st.error("❌ Nome é obrigatório.")
                elif atualizar_responsavel(st.session_state.editando_resp, {"nome": nome_resp}): st.success("✅ Responsável atualizado!"); st.session_state.editando_resp = None; limpar_cache_responsaveis(); st.rerun()
        with col2:
            if st.button("❌ Cancelar"): st.session_state.editando_resp = None; st.rerun()
    else:
        st.subheader("➕ Novo Responsável")
        cargo = st.selectbox("Cargo", ["Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora"])
        nome_resp = st.text_input("Nome do Responsável *", placeholder="Ex: Maria Silva")
        if st.button("💾 Cadastrar", type="primary"):
            if not nome_resp.strip(): st.error("❌ Nome é obrigatório.")
            elif salvar_responsavel({"cargo": cargo, "nome": nome_resp, "ativo": True}): st.session_state.responsavel_salvo_sucesso = True; st.session_state.nome_responsavel_salvo = nome_resp; st.session_state.cargo_responsavel_salvo = cargo; limpar_cache_responsaveis(); st.rerun()
    st.markdown("---")
    st.markdown('<h3 style="margin-bottom:1rem;">📋 Responsáveis Cadastrados</h3>', unsafe_allow_html=True)
    if not df_responsaveis.empty:
        for cargo in ["Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora"]:
            grupo = df_responsaveis[df_responsaveis["cargo"] == cargo]
            if grupo.empty: continue
            st.markdown(f'<div style="margin:0.5rem 0; padding-bottom:0.3rem; border-bottom:1px solid var(--border); font-weight:600;">{cargo}</div>', unsafe_allow_html=True)
            for _, resp in grupo.iterrows():
                col1, col2, col3 = st.columns([6, 1, 1])
                with col1: st.markdown(f'<div style="padding:0.3rem 0; display:flex; align-items:center; gap:0.5rem;"><span>👤</span> {resp["nome"]}</div>', unsafe_allow_html=True)
                with col2:
                    if st.button("✏️", key=f"edit_resp_{resp['id']}"): st.session_state.editando_resp = resp["id"]; st.rerun()
                with col3:
                    if st.button("🗑️", key=f"del_resp_{resp['id']}"): st.session_state.confirmar_exclusao_resp = resp["id"]; st.rerun()
        if st.session_state.get("confirmar_exclusao_resp"):
            resp_id = st.session_state.confirmar_exclusao_resp
            resp_excluir = df_responsaveis[df_responsaveis["id"] == resp_id].iloc[0]
            st.warning(f"⚠️ Confirma excluir **{resp_excluir['nome']}** ({resp_excluir['cargo']})?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão", type="primary"):
                    if excluir_responsavel(resp_id): st.success("✅ Responsável excluído!"); del st.session_state.confirmar_exclusao_resp; limpar_cache_responsaveis(); st.rerun()
            with col2:
                if st.button("❌ Cancelar"): del st.session_state.confirmar_exclusao_resp; st.rerun()
    else: st.info("📭 Nenhum responsável cadastrado.")

# ======================================================
# PÁGINA 🎨 ELETIVA
# ======================================================
elif menu == "🎨 Eletiva":
    page_header("🎨 Eletivas", "Consulte e gerencie os estudantes por professora de eletiva", "#7c3aed")
    if FONTE_ELETIVAS == "supabase": st.success("✅ Eletivas carregadas do Supabase.")
    else: st.warning("⚠️ Eletivas carregadas da planilha Excel.")
    if os.path.exists(ELETIVAS_ARQUIVO):
        with st.expander("☁️ Sincronizar com Supabase", expanded=False):
            if st.button("🔄 Substituir Eletivas no Supabase", type="primary"):
                registros = converter_eletivas_para_registros(ELETIVAS_EXCEL, origem="planilha")
                try:
                    _supabase_request("DELETE", "eletivas?id=not.is.null")
                    _supabase_request("POST", "eletivas", json=registros)
                    st.session_state.ELETIVAS = ELETIVAS_EXCEL; st.session_state.FONTE_ELETIVAS = "supabase"
                    st.success("✅ Eletivas sincronizadas!"); st.rerun()
                except Exception as e: st.error(f"❌ Erro: {e}")
    st.markdown("---")
    if not ELETIVAS: st.info("📭 Nenhuma professora cadastrada para eletivas."); st.stop()
    dados_professoras = [{"Professora": prof, "Total de Alunos": len(alunos), "Séries": ", ".join(sorted({a.get("serie","") for a in alunos if a.get("serie")}))} for prof, alunos in ELETIVAS.items()]
    st.dataframe(pd.DataFrame(dados_professoras), use_container_width=True, hide_index=True)
    st.markdown("---")
    professora_sel = st.selectbox("Selecione a Professora", sorted(ELETIVAS.keys()))
    df_eletiva = montar_dataframe_eletiva(professora_sel, df_alunos, ELETIVAS)
    total = len(df_eletiva)
    encontrados = len(df_eletiva[df_eletiva["Status"] == "Encontrado"]) if not df_eletiva.empty and "Status" in df_eletiva.columns else 0
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total", total)
    with col2: st.metric("Encontrados", encontrados)
    with col3: st.metric("Não Encontrados", total - encontrados)
    busca_nome = st.text_input("🔍 Buscar estudante", placeholder="Digite parte do nome")
    filtro_status = st.selectbox("Filtrar por status", ["Todos", "Encontrado", "Não encontrado"])
    df_view = df_eletiva.copy()
    if busca_nome: df_view = df_view[df_view["Nome da Eletiva"].str.contains(busca_nome, case=False, na=False)]
    if filtro_status != "Todos": df_view = df_view[df_view["Status"] == filtro_status]
    st.markdown("---")
    st.subheader("📋 Estudantes da Eletiva")
    st.dataframe(df_view, use_container_width=True, hide_index=True)
    st.markdown("---")
    if st.button("📄 Gerar PDF", type="primary"):
        pdf = gerar_pdf_eletiva(professora_sel, df_eletiva)
        st.download_button("📥 Baixar PDF", data=pdf, file_name=f"Eletiva_{professora_sel}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", mime="application/pdf")
    alunos_raw = ELETIVAS.get(professora_sel, [])
    if alunos_raw:
        st.markdown("---")
        st.subheader("🗑️ Remover Estudantes")
        opcoes_remover = [f"{a['nome']} {a.get('serie', '')}".strip() for a in alunos_raw]
        selecionados = st.multiselect("Selecione estudantes para remover", opcoes_remover)
        if st.button("🗑️ Remover Selecionados", type="secondary"):
            if not selecionados: st.warning("⚠️ Nenhum estudante selecionado.")
            else:
                novos = [a for a in alunos_raw if f"{a['nome']} {a.get('serie', '')}".strip() not in selecionados]
                ELETIVAS[professora_sel] = novos; st.session_state.ELETIVAS = ELETIVAS
                st.success(f"✅ {len(selecionados)} estudante(s) removido(s)."); st.rerun()

# ======================================================
# PÁGINA 🏫 MAPA DA SALA
# ======================================================
elif menu == "🏫 Mapa da Sala":
    page_header("🏫 Mapa da Sala de Aula", "Organize assentos e distribua alunos visualmente", "#059669")
    if df_alunos.empty: st.warning("⚠️ Cadastre alunos antes de usar o mapa da sala."); st.stop()
    col1, col2, col3 = st.columns(3)
    with col1: num_fileiras = st.slider("Número de fileiras", min_value=1, max_value=10, value=5, key="num_fileiras_mapa")
    with col2: carteiras_por_fileira = st.slider("Carteiras por fileira", min_value=1, max_value=8, value=6, key="carteiras_fileira_mapa")
    with col3: orientacao_lousa = st.selectbox("Orientação da lousa", ["Topo", "Fundo", "Esquerda", "Direita"], key="orientacao_lousa_mapa")
    total_assentos = num_fileiras * carteiras_por_fileira
    st.markdown("---")
    turmas_disponiveis = sorted(df_alunos["turma"].unique().tolist())
    turma_sel = st.selectbox("Selecione a Turma", turmas_disponiveis, key="turma_mapa_select")
    alunos_turma = df_alunos[df_alunos["turma"] == turma_sel].copy()
    if "situacao" in alunos_turma.columns: alunos_turma = alunos_turma[alunos_turma["situacao"].str.strip().str.title() == "Ativo"]
    nomes_alunos = sorted(alunos_turma["nome"].tolist())
    st.subheader(f"👥 Alunos da Turma {turma_sel}")
    st.info(f"📊 {len(alunos_turma)} alunos ativos | {num_fileiras} fileiras × {carteiras_por_fileira} carteiras = {total_assentos} assentos")
    mapa_key = f"mapa_sala_{gerar_chave_segura(turma_sel)}"
    if mapa_key not in st.session_state: st.session_state[mapa_key] = {str(i): "" for i in range(total_assentos)}
    else:
        estado_anterior = st.session_state[mapa_key]
        st.session_state[mapa_key] = {str(i): estado_anterior.get(str(i), "") for i in range(total_assentos)}
    if orientacao_lousa in ["Topo", "Esquerda"]: st.markdown('<div style="width:100%; max-width:280px; height:30px; background:#0f172a; color:white; display:flex; align-items:center; justify-content:center; font-weight:bold; border-radius:var(--radius-sm); margin:0.5rem auto 1rem auto;">📚 LOUSA</div>', unsafe_allow_html=True)
    sala_html = '<div style="display: flex; flex-direction: column; gap: 6px; margin: 1rem 0; padding: 1rem; background:#f8fafc; border:1px solid var(--border); border-radius:var(--radius-lg);">'
    for fileira in range(num_fileiras):
        sala_html += '<div style="display: flex; gap: 6px; justify-content: center;">'
        for carteira in range(carteiras_por_fileira):
            idx = fileira * carteiras_por_fileira + carteira
            nome_no_assento = st.session_state[mapa_key].get(str(idx), "")
            sala_html += f'<div style="width:60px; height:40px; border:2px solid {"#2563eb" if nome_no_assento else "var(--border)"}; border-radius:var(--radius-sm); display:flex; align-items:center; justify-content:center; font-size:0.7rem; font-weight:600; background:{"#2563eb" if nome_no_assento else "white"}; color:{"white" if nome_no_assento else "var(--text-muted)"}; padding:2px; word-break:break-word; transition:all 0.2s;">{nome_no_assento.split()[0] if nome_no_assento else f"C{idx+1}"}</div>'
        sala_html += '</div>'
    sala_html += '</div>'
    st.markdown(sala_html, unsafe_allow_html=True)
    if orientacao_lousa in ["Fundo", "Direita"]: st.markdown('<div style="width:100%; max-width:280px; height:30px; background:#0f172a; color:white; display:flex; align-items:center; justify-content:center; font-weight:bold; border-radius:var(--radius-sm); margin:1rem auto 0.5rem auto;">📚 LOUSA</div>', unsafe_allow_html=True)
    assentos_ocupados = [v for v in st.session_state[mapa_key].values() if v.strip()]
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total de Assentos", total_assentos)
    with col2: st.metric("Ocupados", len(assentos_ocupados))
    with col3: st.metric("Vazios", total_assentos - len(assentos_ocupados))
    nomes_atribuidos = set(assentos_ocupados)
    alunos_sem_assento = [nome for nome in nomes_alunos if nome not in nomes_atribuidos]
    if alunos_sem_assento:
        st.warning(f"⚠️ {len(alunos_sem_assento)} alunos sem assento.")
        with st.expander("📋 Ver alunos sem assento"):
            for aluno in alunos_sem_assento: st.write(f"• {aluno}")
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
                novo_valor = st.text_input(f"C{idx + 1}", value=valor_atual, key=f"input_{mapa_key}_{idx}", placeholder="Nome")
                if novo_valor != valor_atual: st.session_state[mapa_key][str(idx)] = novo_valor
                if novo_valor.strip():
                    melhor_match, score = encontrar_melhor_match(novo_valor, nomes_alunos)
                    if melhor_match and score >= 0.5 and melhor_match.lower() != novo_valor.lower():
                        st.caption(f"💡 {melhor_match} ({int(score*100)}%)")
                        if st.button("✅ Usar", key=f"apply_{mapa_key}_{idx}"): st.session_state[mapa_key][str(idx)] = melhor_match; st.rerun()
    st.markdown("---")
    st.subheader("🛠️ Ferramentas")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔀 Atribuir Aleatoriamente", use_container_width=True, type="primary"):
            random.shuffle(nomes_alunos)
            for i in range(total_assentos): st.session_state[mapa_key][str(i)] = ""
            for i, nome in enumerate(nomes_alunos):
                if i < total_assentos: st.session_state[mapa_key][str(i)] = nome
            st.success("✅ Alunos atribuídos!"); st.rerun()
    with col2:
        if st.button("🧹 Limpar Todos", use_container_width=True):
            for i in range(total_assentos): st.session_state[mapa_key][str(i)] = ""
            st.success("✅ Assentos liberados!"); st.rerun()
    with col3:
        if st.button("🔍 Corrigir Nomes", use_container_width=True):
            correcoes = sum(1 for i in range(total_assentos) if (melhor_match := encontrar_melhor_match(st.session_state[mapa_key].get(str(i), ""), nomes_alunos)[0]) and melhor_match and st.session_state[mapa_key].setdefault(str(i), melhor_match) != st.session_state[mapa_key][str(i)])
            st.success(f"✅ {correcoes} nome(s) corrigido(s)!") if correcoes > 0 else st.info("ℹ️ Nenhum nome precisou de correção.")
            st.rerun()
    with col4:
        if st.button("💾 Salvar Layout", use_container_width=True, type="secondary"): st.success("✅ Layout salvo!")

# ======================================================
# PÁGINA 💾 BACKUPS
# ======================================================
elif menu == "💾 Backups":
    render_backup_page()

# ======================================================
# PÁGINA 📅 AGENDAMENTO DE ESPAÇOS (VERSÃO PREMIUM)
# ======================================================
elif menu == "📅 Agendamento de Espaços":
    page_header("📅 Agendamento de Espaços", "Reserve sala de informática, carrinhos, tablets e sala de leitura", "#2563eb")
    from reportlab.lib.pagesizes import A4, landscape
    import json
    def show_toast_agend(message: str, type: str = "success"): st.toast(f"{'✅' if type=='success' else '❌' if type=='error' else '⚠️'} {message}")
    def get_disponibilidade_espaco(espaco, data, horario):
        try:
            df_agend = carregar_agendamentos_filtrado(data, data, espaco=espaco)
            total = len(df_agend[df_agend['horario'] == horario]) if not df_agend.empty else 0
            return ("🟢", "Disponível", "#10b981") if total == 0 else ("🟡", "Parcialmente ocupado", "#f59e0b") if total == 1 else ("🔴", "Totalmente ocupado", "#ef4444")
        except: return ("⚪", "Não verificado", "#9ca3af")
    def salvar_template(professor, nome_template, configuracao):
        template_key = f"template_{professor.replace(' ', '_')}_{nome_template}"
        st.session_state[template_key] = {"config": configuracao, "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M")}
        lista_key = f"templates_{professor.replace(' ', '_')}"
        if lista_key not in st.session_state: st.session_state[lista_key] = []
        if nome_template not in st.session_state[lista_key]: st.session_state[lista_key].append(nome_template)
        return True
    def carregar_templates(professor): return st.session_state.get(f"templates_{professor.replace(' ', '_')}", [])
    def aplicar_template(professor, nome_template, grade_key):
        template_key = f"template_{professor.replace(' ', '_')}_{nome_template}"
        if template_key in st.session_state:
            for key, value in st.session_state[template_key]["config"].items(): st.session_state[grade_key][key] = value
            return True
        return False
    def registrar_log(acao, usuario, detalhes=" "):
        if 'logs_agendamento' not in st.session_state: st.session_state.logs_agendamento = []
        st.session_state.logs_agendamento.insert(0, {"timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "acao": acao, "usuario": usuario, "detalhes": detalhes})
        if len(st.session_state.logs_agendamento) > 100: st.session_state.logs_agendamento = st.session_state.logs_agendamento[:100]
    def exportar_para_excel(df, nome_arquivo):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Agendamentos', index=False)
            worksheet = writer.sheets['Agendamentos']
            for column in worksheet.columns:
                max_length = max((len(str(cell.value)) for cell in column if cell.value is not None), default=0)
                worksheet.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
            from openpyxl.styles import Font, PatternFill
            for cell in worksheet[1]: cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill(start_color="4A90E2", end_color="4A90E2", fill_type="solid")
        output.seek(0); return output
    if 'gestao_logado' not in st.session_state: st.session_state.gestao_logado = False
    if 'logs_agendamento' not in st.session_state: st.session_state.logs_agendamento = []
    tabs_agend = st.tabs(["✨ Agendar", "📋 Meus Agendamentos", "🗓️ Grade Semanal", "📍 Visualizar por Espaço", "📊 Dashboard", "👥 Professores", "📈 Relatórios", "⚙️ Gestão", "🧹 Manutenção"])
    with tabs_agend[0]:
        st.subheader("📅 Agendamento Rápido")
        df_prof_agend = prof_list_agend()
        lista_nomes = sorted(df_prof_agend["nome"].dropna().tolist()) if not df_prof_agend.empty else []
        if lista_nomes:
            with st.expander("📂 Templates Salvos", expanded=False):
                professor_temp = st.selectbox("Professor: ", lista_nomes, key="temp_prof")
                templates = carregar_templates(professor_temp)
                if templates:
                    cols = st.columns([2, 1])
                    with cols[0]: template_sel = st.selectbox("Selecione: ", templates, key="temp_sel")
                    with cols[1]:
                        if st.button("📂 Carregar", use_container_width=True): st.success(f"✅ Template '{template_sel}' carregado!"); show_toast_agend(f"Template '{template_sel}' carregado!")
                else: st.info("Nenhum template salvo para este professor")
        tipo_agendamento = st.radio("🔄 Tipo de Agendamento:", ["📅 Data específica", "🔁 Fixo Semanal"], horizontal=True, key="tipo_agendamento")
        if tipo_agendamento == "📅 Data específica":
            with st.form("form_agendamento_data"):
                col1, col2 = st.columns(2)
                with col1: professor = st.selectbox("👨‍🏫 Professor: ", [""] + lista_nomes); turma = st.selectbox("🎓 Turma: ", [""] + sorted(TURMAS_INTERVALOS_AGEND.keys())); disciplina = st.selectbox("📚 Disciplina: ", [""] + DISCIPLINAS_AGEND)
                with col2: prioridade = st.selectbox("⭐ Prioridade: ", [""] + PRIORIDADES_ESTENDIDAS + ["NORMAL"]); espaco = st.selectbox("📍 Espaço: ", [""] + ESPACOS_AGEND); data = st.date_input("📅 Data: ", min_value=datetime.now().date() + timedelta(days=1))
                horario1 = st.selectbox("1ª Aula: ", [""] + HORARIOS_AGEND)
                horario2 = st.selectbox("2ª Aula (opcional): ", [""] + HORARIOS_AGEND)
                salvar_como_template = st.checkbox("💾 Salvar como template para uso futuro")
                nome_template = ""
                if salvar_como_template: nome_template = st.text_input("Nome do template: ", placeholder="Ex: Aulas de Matemática")
                if st.form_submit_button("✅ Confirmar Agendamento", type="primary", use_container_width=True):
                    if not all([professor, turma, disciplina, prioridade, espaco, horario1]): st.error("⚠️ Preencha todos os campos obrigatórios")
                    else:
                        horarios = [h for h in [horario1, horario2] if h]; sucessos = 0
                        for h in horarios:
                            if not verificar_conflito_api(data.strftime("%Y-%m-%d"), h, espaco):
                                ok, _ = salvar_agendamento_api({"data_agendamento": data.strftime("%Y-%m-%d"), "horario": h, "espaco": espaco, "turma": turma, "disciplina": disciplina, "prioridade": prioridade, "professor_nome": professor, "status": "ATIVO", "tipo": "DATA_ESPECIFICA"})
                                if ok: sucessos += 1
                        if sucessos > 0:
                            st.success(f"✅ {sucessos} agendamento(s) confirmado(s)!"); registrar_log("CRIAR_AGENDAMENTO", professor, f"{data.strftime('%d/%m/%Y')} - {espaco} - {horarios}")
                            show_toast_agend(f"{sucessos} agendamento(s) criado(s)!"); st.balloons(); carregar_agendamentos_filtrado.clear()
                            st.session_state.agendamentos_criados += sucessos
                            if st.session_state.agendamentos_criados >= 5: verificar_conquista("agendamento_perfeito")
                            if salvar_como_template and nome_template:
                                salvar_template(professor, nome_template, {"turma": turma, "disciplina": disciplina, "prioridade": prioridade, "espaco": espaco, "horarios": horarios})
                                st.success(f"✅ Template '{nome_template}' salvo!")
                            st.rerun()
                        else: st.error("❌ Não foi possível criar o agendamento.")
        else:
            st.info("💡 **Agendamento Fixo Semanal** - Use a aba '🗓️ Grade Semanal' para configurar horários fixos!")
            if st.button("➡️ Ir para Grade Semanal", type="primary"): st.rerun()
    with tabs_agend[1]:
        st.subheader("📋 Meus Agendamentos")
        df_prof_agend = prof_list_agend(); lista_nomes = sorted(df_prof_agend["nome"].dropna().tolist()) if not df_prof_agend.empty else []
        professor_sel = st.selectbox("👨‍🏫 Seu Nome: ", [""] + lista_nomes, key="prof_meus_agend")
        col1, col2, col3 = st.columns(3)
        with col1: data_ini = st.date_input("Data início: ", datetime.now().date() - timedelta(days=30), key="meus_ini")
        with col2: data_fim = st.date_input("Data fim: ", datetime.now().date() + timedelta(days=60), key="meus_fim")
        with col3: st.markdown("<br>", unsafe_allow_html=True); buscar_btn = st.button("🔍 Buscar", key="btn_buscar_agend", type="primary", use_container_width=True)
        if buscar_btn:
            if not professor_sel: st.warning("⚠️ Selecione seu nome primeiro")
            else:
                df = carregar_agendamentos_filtrado(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"), professor=professor_sel)
                if df.empty: st.info("📭 Nenhum agendamento encontrado")
                else:
                    if 'status' in df.columns: df = df[df['status'] == 'ATIVO']
                    st.success(f"📊 {len(df)} agendamentos encontrados")
                    df['data_agendamento'] = pd.to_datetime(df['data_agendamento']); df = df.sort_values(['data_agendamento', 'horario'])
                    colunas_exibir = ['data_agendamento', 'horario', 'espaco', 'turma', 'disciplina']
                    df_display = df[[c for c in colunas_exibir if c in df.columns]].copy()
                    if 'data_agendamento' in df_display.columns: df_display['data_agendamento'] = df_display['data_agendamento'].dt.strftime('%d/%m/%Y')
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    st.markdown("---"); st.subheader("🛑 Cancelar Agendamento")
                    id_cancelar = st.selectbox("Selecione o ID para cancelar: ", df['id'].tolist(), key="id_cancelar")
                    if st.button("🛑 Cancelar Agendamento", type="secondary"):
                        if cancelar_agendamento_api(str(id_cancelar))[0]: st.success("✅ Agendamento cancelado!"); carregar_agendamentos_filtrado.clear(); st.rerun()
                        else: st.error("❌ Erro ao cancelar")
                    if st.button("📊 Exportar para Excel", key="export_meus"):
                        st.download_button("📥 Baixar Excel", data=exportar_para_excel(df_display, "meus_agendamentos"), file_name=f"agendamentos_{professor_sel}_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with tabs_agend[2]:
        st.subheader("🗓️ Grade Semanal - Agendamentos Fixos")
        st.info("💡 Configure horários fixos • 🟢 Disponível • 🟡 Parcial • 🔴 Ocupado")
        df_prof_agend = prof_list_agend(); lista_nomes = sorted(df_prof_agend["nome"].dropna().tolist()) if not df_prof_agend.empty else []
        if not lista_nomes: st.warning("⚠️ Cadastre professores primeiro na aba '👥 Professores'")
        else:
            professor_grade = st.selectbox("👨‍🏫 Selecione o Professor: ", lista_nomes, key="prof_grade")
            if professor_grade:
                templates = carregar_templates(professor_grade)
                if templates:
                    with st.expander("📂 Templates Salvos", expanded=False):
                        cols = st.columns([2, 1, 1])
                        with cols[0]: template_sel = st.selectbox("Selecione: ", templates, key="grade_temp_sel")
                        with cols[1]:
                            if st.button("📂 Carregar", use_container_width=True):
                                grade_key = f"grade_{professor_grade.replace(' ', '_').replace('.', '')}"
                                if grade_key not in st.session_state: st.session_state[grade_key] = {}
                                if aplicar_template(professor_grade, template_sel, grade_key): st.success(f"✅ Template '{template_sel}' carregado!"); show_toast_agend(f"Template '{template_sel}' aplicado!"); st.rerun()
                        with cols[2]:
                            if st.button("🗑️ Excluir", use_container_width=True):
                                template_key = f"template_{professor_grade.replace(' ', '_')}_{template_sel}"
                                if template_key in st.session_state: del st.session_state[template_key]; st.session_state[f"templates_{professor_grade.replace(' ', '_')}"].remove(template_sel); st.success(f"✅ Template '{template_sel}' excluído!"); st.rerun()
                st.markdown("---")
                horarios_aulas = ["07:00-07:50", "07:50-08:40", "08:40-09:30", "09:50-10:40", "10:40-11:30", "11:30-12:20", "13:00-13:50", "13:50-14:40", "14:40-15:30", "15:50-16:40", "16:40-17:30", "17:30-18:20"]
                dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira"]
                dias_abrev = ["SEG", "TER", "QUA", "QUI", "SEX"]
                st.markdown("### 📝 Configure os horários fixos:")
                grade_key = f"grade_{professor_grade.replace(' ', '_').replace('.', '')}"
                if grade_key not in st.session_state: st.session_state[grade_key] = {}
                data_ref = st.date_input("📅 Data de referência para verificar disponibilidade: ", value=datetime.now().date() + timedelta(days=7), key="data_ref")
                for hora in horarios_aulas:
                    with st.expander(f"🕐 {hora}", expanded=False):
                        cols = st.columns(len(dias_semana))
                        for i, (dia, dia_abrev) in enumerate(zip(dias_semana, dias_abrev)):
                            with cols[i]:
                                st.markdown(f"**{dia_abrev}**")
                                key = f"{dia}_{hora}"
                                valor_atual = st.session_state[grade_key].get(key, {"espaco": "", "turma": "", "disciplina": ""})
                                espaco_sel = st.selectbox("📍 Espaço", [""] + ESPACOS_AGEND, key=f"esp_{professor_grade}_{dia}_{hora}", index=0 if not valor_atual.get("espaco") else ESPACOS_AGEND.index(valor_atual["espaco"]) + 1 if valor_atual["espaco"] in ESPACOS_AGEND else 0, label_visibility="visible")
                                if espaco_sel:
                                    status, msg, cor = get_disponibilidade_espaco(espaco_sel, data_ref.strftime("%Y-%m-%d"), hora)
                                    st.caption(f"{status} {msg}")
                                    turma_sel = st.selectbox("🎓 Turma", [""] + sorted(TURMAS_INTERVALOS_AGEND.keys()), key=f"turma_{professor_grade}_{dia}_{hora}", index=0 if not valor_atual.get("turma") else list(TURMAS_INTERVALOS_AGEND.keys()).index(valor_atual["turma"]) + 1 if valor_atual["turma"] in TURMAS_INTERVALOS_AGEND else 0, label_visibility="visible")
                                    disciplina_sel = st.selectbox("📚 Disciplina", [""] + DISCIPLINAS_AGEND, key=f"disc_{professor_grade}_{dia}_{hora}", index=0 if not valor_atual.get("disciplina") else DISCIPLINAS_AGEND.index(valor_atual["disciplina"]) + 1 if valor_atual["disciplina"] in DISCIPLINAS_AGEND else 0, label_visibility="visible")
                                    if espaco_sel and turma_sel and disciplina_sel: st.success("✅ Configurado")
                                    st.session_state[grade_key][key] = {"espaco": espaco_sel, "turma": turma_sel or "", "disciplina": disciplina_sel or ""}
                                else: st.session_state[grade_key][key] = {"espaco": "", "turma": "", "disciplina": ""}
                st.markdown("---")
                with st.expander("💾 Salvar Grade como Template", expanded=False):
                    nome_template_grade = st.text_input("Nome do template: ", key="nome_template_grade")
                    if st.button("💾 Salvar Template da Grade", type="primary"):
                        if nome_template_grade:
                            config_completa = {k: v for k, v in st.session_state[grade_key].items() if v.get("espaco") and v.get("turma") and v.get("disciplina")}
                            if config_completa: salvar_template(professor_grade, nome_template_grade, config_completa); st.success(f"✅ Template '{nome_template_grade}' salvo com {len(config_completa)} horários!"); show_toast_agend("Template salvo com sucesso!")
                            else: st.warning("⚠️ Nenhum horário configurado para salvar")
                        else: st.error("❌ Digite um nome para o template")
                col1, col2 = st.columns(2)
                with col1: data_inicio = st.date_input("📅 Data de início: ", value=datetime(2026, 2, 1).date(), key="grade_inicio")
                with col2: data_fim = st.date_input("📅 Data de término: ", value=datetime(2026, 12, 20).date(), key="grade_fim")
                frequencia = st.radio("🔄 Frequência: ", ["Semanal (toda semana)", "Quinzenal (a cada 15 dias)"], horizontal=True, key="freq_grade")
                intervalo = 7 if frequencia == "Semanal (toda semana)" else 14
                if st.button("🚀 CRIAR AGENDAMENTOS FIXOS", type="primary", use_container_width=True):
                    total_criados = conflitos = 0
                    progress_bar = st.progress(0); status_text = st.empty()
                    dias_map = {"Segunda-feira": 0, "Terça-feira": 1, "Quarta-feira": 2, "Quinta-feira": 3, "Sexta-feira": 4}
                    total_potencial = 0; data_temp = data_inicio
                    while data_temp <= data_fim:
                        dia_semana_num = data_temp.weekday()
                        dia_semana_nome = next((nome for nome, num in dias_map.items() if num == dia_semana_num), None)
                        if dia_semana_nome:
                            for hora in horarios_aulas:
                                key = f"{dia_semana_nome}_{hora}"
                                config = st.session_state[grade_key].get(key, {})
                                if config.get("espaco") and config.get("turma") and config.get("disciplina"): total_potencial += 1
                        data_temp += timedelta(days=intervalo)
                    if total_potential == 0: st.warning("⚠️ Nenhum horário configurado.")
                    else:
                        data_atual = data_inicio; processados = 0
                        while data_atual <= data_fim:
                            dia_semana_num = data_atual.weekday()
                            dia_semana_nome = next((nome for nome, num in dias_map.items() if num == dia_semana_num), None)
                            if dia_semana_nome:
                                for hora in horarios_aulas:
                                    key = f"{dia_semana_nome}_{hora}"
                                    config = st.session_state[grade_key].get(key, {})
                                    if config.get("espaco") and config.get("turma") and config.get("disciplina"):
                                        if not verificar_conflito_api(data_atual.strftime("%Y-%m-%d"), hora, config["espaco"]):
                                            ok, _ = salvar_agendamento_api({"data_agendamento": data_atual.strftime("%Y-%m-%d"), "horario": hora, "espaco": config["espaco"], "turma": config["turma"], "disciplina": config["disciplina"], "prioridade": "NORMAL", "professor_nome": professor_grade, "status": "ATIVO", "tipo": "FIXO"})
                                            if ok: total_criados += 1
                                        else: conflitos += 1
                            data_atual += timedelta(days=intervalo); processados += 1
                            progress_bar.progress(min(processados / (total_potencial / len(horarios_aulas) + 1), 1.0))
                            status_text.text(f"Criando... {total_criados} agendamentos")
                        progress_bar.empty(); status_text.empty()
                        if total_criados > 0:
                            st.success(f"✅ {total_criados} agendamentos fixos criados!")
                            if conflitos > 0: st.warning(f"⚠️ {conflitos} horários já ocupados")
                            registrar_log("CRIAR_GRADE_FIXA", professor_grade, f"{total_criados} agendamentos - {frequencia}")
                            show_toast_agend(f"{total_criados} agendamentos fixos criados!"); st.balloons(); carregar_agendamentos_filtrado.clear()
                        else: st.warning("⚠️ Nenhum agendamento foi criado.")
                st.markdown("---"); st.subheader("📋 Resumo da Grade")
                resumo_data = []
                for dia in dias_semana:
                    for hora in horarios_aulas:
                        key = f"{dia}_{hora}"
                        config = st.session_state[grade_key].get(key, {})
                        if config.get("espaco") and config.get("turma") and config.get("disciplina"): resumo_data.append({"Dia": dia[:3], "Horário": hora, "Espaço": config["espaco"], "Turma": config["turma"], "Disciplina": config["disciplina"]})
                if resumo_data:
                    df_resumo = pd.DataFrame(resumo_data)
                    st.dataframe(df_resumo, use_container_width=True, hide_index=True)
                    if st.button("🖨️ Imprimir Grade", key="btn_imprimir_grade"):
                        buffer = BytesIO(); doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1*cm, rightMargin=1*cm)
                        estilos = getSampleStyleSheet(); elementos = []
                        elementos.append(Paragraph(f"GRADE SEMANAL - {professor_grade}", estilos['Heading1'])); elementos.append(Spacer(1, 0.3*cm))
                        dados_tabela = [["Dia", "Horário", "Espaço", "Turma", "Disciplina"]] + [[item["Dia"], item["Horário"], item["Espaço"], item["Turma"], item["Disciplina"]] for item in resumo_data]
                        tabela = Table(dados_tabela, repeatRows=1)
                        tabela.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563eb")), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('FONTSIZE', (0, 0), (-1, -1), 9)]))
                        elementos.append(tabela); doc.build(elementos); buffer.seek(0)
                        st.download_button("📥 Baixar PDF", data=buffer, file_name=f"grade_{professor_grade}.pdf", mime="application/pdf")
    with tabs_agend[3]:
        st.subheader("📍 Visualizar Agenda por Espaço")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: espaco_sel = st.selectbox("📍 Espaço: ", ESPACOS_AGEND, key="viz_espaco")
        with col2: data_ini = st.date_input("Data início: ", datetime.now().date(), key="viz_ini")
        with col3: data_fim = st.date_input("Data fim: ", datetime.now().date() + timedelta(days=30), key="viz_fim")
        if st.button("🔍 Carregar Agenda", type="primary", use_container_width=True):
            df = carregar_agendamentos_filtrado(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"), espaco=espaco_sel)
            if not df.empty and 'status' in df.columns: df = df[df['status'] == 'ATIVO']
            if df.empty: st.info(f"📭 Nenhum agendamento para **{espaco_sel}**")
            else:
                st.success(f"📊 {len(df)} agendamentos encontrados")
                df['data_agendamento'] = pd.to_datetime(df['data_agendamento']); df = df.sort_values(['data_agendamento', 'horario'])
                col1, col2, col3 = st.columns(3)
                with col1: st.metric("Total no período", len(df))
                with col2: st.metric("Professores únicos", df['professor_nome'].nunique())
                with col3: st.metric("Turmas atendidas", df['turma'].nunique())
                st.markdown("---")
                datas_unicas = sorted(df['data_agendamento'].dt.date.unique())
                for data in datas_unicas:
                    df_dia = df[df['data_agendamento'].dt.date == data]
                    with st.expander(f"📅 {data.strftime('%A')}, {data.strftime('%d/%m/%Y')} - {len(df_dia)} aula(s)", expanded=True):
                        tabela_dia = [{"Horário": row['horario'], "Tipo": "🔁 FIXO" if row.get('tipo') == 'FIXO' else "📅 DATA", "Turma": row['turma'], "Professor": row['professor_nome'], "Disciplina": row['disciplina']} for _, row in df_dia.iterrows()]
                        st.dataframe(pd.DataFrame(tabela_dia), use_container_width=True, hide_index=True)
                st.markdown("---"); st.subheader("📋 Tabela Completa para Impressão")
                colunas_exibir = ['data_agendamento', 'horario', 'turma', 'professor_nome', 'disciplina']
                df_completo = df[[c for c in colunas_exibir if c in df.columns]].copy()
                if 'data_agendamento' in df_completo.columns: df_completo['data_agendamento'] = df_completo['data_agendamento'].dt.strftime('%d/%m/%Y')
                st.dataframe(df_completo, use_container_width=True, hide_index=True)
                if st.button("🖨️ IMPRIMIR AGENDA", type="primary", use_container_width=True):
                    buffer = BytesIO(); doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1*cm, rightMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
                    estilos = getSampleStyleSheet(); elementos = []
                    elementos.append(Paragraph(f"AGENDA - {espaco_sel.upper()}", estilos['Heading1'])); elementos.append(Spacer(1, 0.2*cm))
                    elementos.append(Paragraph(f"Período: {data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')} | Total: {len(df)} agendamentos", estilos['Normal'])); elementos.append(Spacer(1, 0.3*cm))
                    dados_tabela = [["Data", "Horário", "Turma", "Professor", "Disciplina"]] + [[row['data_agendamento'].strftime('%d/%m/%Y'), row['horario'], row['turma'], row['professor_nome'], row['disciplina']] for _, row in df.iterrows()]
                    tabela = Table(dados_tabela, repeatRows=1)
                    tabela.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563eb")), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 8), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
                    elementos.append(tabela); elementos.append(Spacer(1, 0.3*cm))
                    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilos['Normal']))
                    doc.build(elementos); buffer.seek(0)
                    st.download_button("📥 Baixar PDF", data=buffer, file_name=f"agenda_{espaco_sel.replace(' ', '_')}_{data_ini.strftime('%Y%m%d')}.pdf", mime="application/pdf")
    with tabs_agend[4]:
        st.subheader("📊 Dashboard de Agendamentos")
        col1, col2 = st.columns(2)
        with col1: data_ini = st.date_input("Data início: ", datetime.now().date(), key="dash_ini")
        with col2: data_fim = st.date_input("Data fim: ", datetime.now().date() + timedelta(days=7), key="dash_fim")
        if st.button("📊 Carregar Dashboard", type="primary"):
            df = carregar_agendamentos_filtrado(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
            if not df.empty and 'status' in df.columns: df = df[df['status'] == 'ATIVO']
            if df.empty: st.info("📭 Nenhum agendamento no período")
            else:
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("Total", len(df))
                with col2: st.metric("Fixos", len(df[df.get('tipo', '') == 'FIXO']) if 'tipo' in df.columns else 0)
                with col3: st.metric("Data Específica", len(df) - (len(df[df.get('tipo', '') == 'FIXO']) if 'tipo' in df.columns else 0))
                with col4: st.metric("Espaço mais usado", df['espaco'].mode()[0] if not df['espaco'].mode().empty else "N/A")
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📊 Uso por Espaço")
                    espaco_counts = df['espaco'].value_counts()
                    st.plotly_chart(px.bar(espaco_counts, x=espaco_counts.index, y=espaco_counts.values, labels={'x': 'Espaço', 'y': 'Quantidade'}, color=espaco_counts.index), use_container_width=True)
                with col2:
                    st.subheader("👨‍🏫 Top Professores")
                    prof_counts = df['professor_nome'].value_counts().head(10)
                    st.plotly_chart(px.bar(prof_counts, x=prof_counts.index, y=prof_counts.values, labels={'x': 'Professor', 'y': 'Quantidade'}, color=prof_counts.index).update_layout(xaxis_tickangle=-45), use_container_width=True)
                st.subheader("📅 Agendamentos por Dia")
                df['data_agendamento'] = pd.to_datetime(df['data_agendamento'])
                por_dia = df.groupby(df['data_agendamento'].dt.date).size().reset_index(name='Quantidade')
                por_dia.columns = ['Data', 'Quantidade']
                st.plotly_chart(px.line(por_dia, x='Data', y='Quantidade', markers=True), use_container_width=True)
    with tabs_agend[5]:
        st.subheader("👥 Professores")
        df_all = prof_list_agend()
        with st.expander("➕ Cadastrar Professor", expanded=False):
            with st.form("form_prof_rapido"):
                c1, c2 = st.columns(2)
                nome = c1.text_input("Nome *"); email = c2.text_input("Email *")
                if st.form_submit_button("Salvar", type="primary"):
                    if nome and email:
                        if prof_upsert_agend(nome, email)[0]: st.success(f"✅ Professor {nome} cadastrado!"); show_toast_agend(f"Professor {nome} cadastrado!"); st.rerun()
                        else: st.error("❌ Erro ao cadastrar")
                    else: st.error("❌ Nome e email são obrigatórios")
        if not df_all.empty: st.dataframe(df_all[['nome', 'email', 'cargo']], use_container_width=True, hide_index=True)
        else: st.info("📭 Nenhum professor cadastrado")
    with tabs_agend[6]:
        st.subheader("📈 Relatórios de Uso")
        col1, col2 = st.columns(2)
        with col1: data_ini = st.date_input("Data início: ", datetime.now().date() - timedelta(days=30), key="rel_ini")
        with col2: data_fim = st.date_input("Data fim: ", datetime.now().date() + timedelta(days=30), key="rel_fim")
        if st.button("📊 Gerar Relatório", key="btn_rel", type="primary"):
            df = carregar_agendamentos_filtrado(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
            if df.empty: st.info("📭 Nenhum agendamento no período")
            else:
                if 'status' in df.columns: df = df[df['status'] == 'ATIVO']
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("Total", len(df))
                with col2: st.metric("Fixos", len(df[df.get('tipo', '') == 'FIXO']) if 'tipo' in df.columns else 0)
                with col3: st.metric("Data Específica", len(df) - (len(df[df.get('tipo', '') == 'FIXO']) if 'tipo' in df.columns else 0))
                with col4: st.metric("Espaço mais usado", df['espaco'].mode()[0] if not df['espaco'].mode().empty else "N/A")
                st.subheader("📊 Uso por Espaço")
                st.plotly_chart(px.bar(df['espaco'].value_counts(), x=df['espaco'].value_counts().index, y=df['espaco'].value_counts().values, labels={'x': 'Espaço', 'y': 'Quantidade'}, color=df['espaco'].value_counts().index), use_container_width=True)
                st.subheader("📋 Detalhamento")
                st.dataframe(df[['data_agendamento', 'horario', 'espaco', 'turma', 'professor_nome', 'disciplina']], use_container_width=True, hide_index=True)
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button("📥 Baixar CSV", data=csv, file_name=f"relatorio_agendamentos_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    with tabs_agend[7]:
        st.subheader("⚙️ Gestão de Agendamentos")
        if not st.session_state.gestao_logado:
            senha = st.text_input("Senha da Gestão: ", type="password")
            if st.button("🔓 Acessar", type="primary"):
                if senha == SENHA_GESTAO_AGEND: st.session_state.gestao_logado = True; st.success("✅ Acesso autorizado!"); show_toast_agend("Acesso autorizado!"); st.rerun()
                else: st.error("❌ Senha inválida")
        else:
            if st.button("🚪 Sair da Gestão", type="secondary"): st.session_state.gestao_logado = False; st.rerun()
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1: data_ini = st.date_input("Início: ", datetime.now().date(), key="gest_ini")
            with col2: data_fim = st.date_input("Fim: ", datetime.now().date() + timedelta(days=30), key="gest_fim")
            if st.button("🔍 Carregar Agendamentos", type="primary"):
                df = carregar_agendamentos_filtrado(data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))
                if df.empty: st.info("📭 Nenhum agendamento")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.subheader("🗑️ Excluir Agendamento")
                    id_excluir = st.selectbox("Selecione o ID: ", df['id'].tolist())
                    if st.button("🗑️ Excluir Permanentemente", type="secondary"):
                        if excluir_agendamento_api(str(id_excluir))[0]: st.success(f"✅ Agendamento {id_excluir} excluído!"); registrar_log("EXCLUIR_AGENDAMENTO", "Gestão", f"ID: {id_excluir}"); show_toast_agend("Agendamento excluído!"); carregar_agendamentos_filtrado.clear(); st.rerun()
                        else: st.error("❌ Erro ao excluir")
            st.markdown("---")
            with st.expander("📋 Logs de Atividades", expanded=False):
                if st.session_state.logs_agendamento:
                    for log in st.session_state.logs_agendamento[:20]: st.caption(f"{log['timestamp']} - {log['acao']} - {log['usuario']} - {log['detalhes']}")
                else: st.info("Nenhum log registrado")
    with tabs_agend[8]:
        st.subheader("🧹 Manutenção / Limpeza")
        if not st.session_state.gestao_logado: st.warning("🔒 Acesso restrito à Gestão (faça login na aba ⚙️ Gestão)")
        else:
            st.info("Remove definitivamente CANCELADO/EXCLUIDO_GESTAO anteriores à data de corte.")
            dias = st.number_input("Remover registros anteriores a (dias): ", min_value=7, max_value=3650, value=180)
            cutoff = (datetime.now().date() - timedelta(days=int(dias))).strftime("%Y-%m-%d")
            if st.button("🔍 Visualizar registros a excluir"):
                try:
                    r = requests.get(f"{SUPABASE_URL}/rest/v1/agendamentos?select=id,data_agendamento,espaco,professor_nome,status&status=in.(CANCELADO,EXCLUIDO_GESTAO)&data_agendamento=lt.{cutoff}&limit=50", headers=HEADERS, timeout=20)
                    if r.status_code == 200:
                        dados = r.json()
                        if dados: st.warning(f"⚠️ {len(dados)} registros serão excluídos"); st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)
                        else: st.success("✅ Nenhum registro para excluir!")
                    else: st.error("❌ Erro ao consultar registros")
                except Exception as e: st.error(f"❌ Erro: {e}")
            if st.button("🧹 Executar limpeza agora", type="primary"):
                try:
                    r = requests.delete(f"{SUPABASE_URL}/rest/v1/agendamentos?status=in.(CANCELADO,EXCLUIDO_GESTAO)&data_agendamento=lt.{cutoff}", headers=HEADERS, timeout=20)
                    if r.status_code in (200, 204): st.success(f"✅ Limpeza concluída! (corte: {cutoff})"); registrar_log("LIMPEZA", "Gestão", f"Excluídos registros anteriores a {cutoff}"); show_toast_agend("Limpeza concluída!"); carregar_agendamentos_filtrado.clear()
                    else: st.error(f"❌ Erro: {r.status_code}")
                except Exception as e: st.error(f"❌ Falha: {e}")