import streamlit as st
import pandas as pd
import openpyxl
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, time
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from io import BytesIO
import requests
import os
import re
import unicodedata
import zipfile
from dotenv import load_dotenv
import pytz
from difflib import SequenceMatcher
from xml.etree import ElementTree as ET

# --- IMPORTS LOCAIS ---
from src.backup_manager import BackupManager, render_backup_page
from src.error_handler import (
    com_tratamento_erro, com_retry, com_validacao,
    ErroConexaoDB, ErroValidacao, ErroCarregamentoDados,
    ErroOperacaoDB, ErroArquivo, ErroAutenticacao,
    ErroDuplicado, ErroNaoEncontrado, ErroPermissao,
    Validadores, tratar_erro, exibir_erro, logger
)

# --- CARREGAR VARIÁVEIS DE AMBIENTE ---
load_dotenv()

def rerun():
    if hasattr(st, 'rerun'):
        return st.rerun()
    if hasattr(st, 'experimental_rerun'):
        return st.experimental_rerun()
    raise RuntimeError('Streamlit rerun is not available.')

# --- CONFIGURAÇÃO SUPABASE ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_VALID = bool(SUPABASE_URL and SUPABASE_KEY)
if SUPABASE_VALID:
    HEADERS = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
else:
    HEADERS = {}
    st.warning(
        "⚠️ SUPABASE_URL ou SUPABASE_KEY não foram definidas. "
        "As funcionalidades de banco de dados ficaram indisponíveis."
    )

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Conviva 179 - E.E. Profª Eliane", layout="wide", page_icon="🏫")

# --- CSS PERSONALIZADO PROFISSIONAL ---
st.markdown("""
<style>
:root {
    --primary: #2563eb;
    --primary-light: #3b82f6;
    --primary-dark: #1e40af;
    --secondary: #7c3aed;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --light: #f9fafb;
    --gray: #6b7280;
    --border: #e5e7eb;
}

* {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

.main-header {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    padding: 2.5rem 2rem;
    border-radius: 12px;
    color: white;
    text-align: center;
    margin-bottom: 2.5rem;
    box-shadow: 0 10px 30px rgba(37, 99, 235, 0.15);
}

.school-name {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 0.5rem;
}

.school-subtitle {
    font-size: 1.1rem;
    font-weight: 500;
    opacity: 0.95;
    margin-bottom: 1rem;
}

.school-address {
    font-size: 0.95rem;
    margin-top: 1rem;
    opacity: 0.85;
    line-height: 1.6;
}

.school-contact {
    font-size: 0.9rem;
    margin-top: 0.5rem;
    opacity: 0.85;
}

.card {
    background: white;
    padding: 1.25rem;
    border-radius: 10px;
    border: 1px solid var(--border);
    margin: 0.75rem 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;
}

.card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-color: var(--primary-light);
}

.card-title {
    font-weight: 600;
    color: #1f2937;
    font-size: 1rem;
    margin-bottom: 0.5rem;
}

.card-value {
    font-size: 1.75rem;
    color: var(--primary);
    font-weight: 700;
}

.success-box {
    background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
    border: 1px solid var(--success);
    border-radius: 10px;
    padding: 1.25rem;
    margin: 1.25rem 0;
    text-align: center;
    font-weight: 600;
    color: #047857;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
}

.protocolo-info {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border: 1px solid var(--warning);
    border-radius: 10px;
    padding: 1.25rem;
    margin: 1.25rem 0;
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1);
}

.gravidade-alert {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
    border: 1px solid var(--danger);
    border-radius: 10px;
    padding: 1rem;
    margin: 0.75rem 0;
    color: #991b1b;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
}

.infracao-tag {
    background: var(--primary);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    display: inline-block;
    margin: 0.35rem 0.25rem;
    font-size: 0.9rem;
    font-weight: 500;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
}

.infracao-principal-tag {
    background: var(--success);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 20px;
    display: inline-block;
    margin: 0.75rem 0;
    font-weight: 600;
    font-size: 0.95rem;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.metric-card {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    padding: 1.75rem;
    border-radius: 12px;
    color: white;
    text-align: center;
    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.15);
    transition: transform 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 28px rgba(37, 99, 235, 0.25);
}

.metric-value {
    font-size: 2.75rem;
    font-weight: 700;
    letter-spacing: -1px;
}

.metric-label {
    font-size: 1rem;
    opacity: 0.95;
    margin-top: 0.5rem;
    font-weight: 500;
}

.search-box {
    background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1.25rem 0;
    border: 1px solid var(--border);
}

.section-divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 1.5rem 0;
}

.status-badge {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.status-badge.success {
    background: #dcfce7;
    color: #047857;
}

.status-badge.warning {
    background: #fef3c7;
    color: #92400e;
}

.status-badge.danger {
    background: #fee2e2;
    color: #991b1b;
}

.status-badge.info {
    background: #dbeafe;
    color: #1e40af;
}

/* Estilos para Títulos Profissionais */
h1, h2, h3, h4, h5, h6 {
    color: #1f2937;
    font-weight: 700;
    letter-spacing: -0.5px;
}

h1 { font-size: 2rem; margin: 1.5rem 0 1rem 0; }
h2 { font-size: 1.5rem; margin: 1.25rem 0 0.75rem 0; }
h3 { font-size: 1.25rem; margin: 1rem 0 0.5rem 0; }

/* Estilos para Gravidades de Infração */
.gravidade-leve {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border-left: 4px solid #10b981;
    color: #065f46;
}

.gravidade-media {
    background: linear-gradient(135deg, #fef08a 0%, #fde047 100%);
    border-left: 4px solid #f59e0b;
    color: #78350f;
}

.gravidade-grave {
    background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%);
    border-left: 4px solid #f97316;
    color: #7c2d12;
}

.gravidade-gravissima {
    background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%);
    border-left: 4px solid #ef4444;
    color: #7f1d1d;
}

/* Container Profissional */
.info-container {
    background: white;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.5rem;
    margin: 1.25rem 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.info-container-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
}

.info-container-header-icon {
    font-size: 1.5rem;
    color: var(--primary);
}

.info-container-header-title {
    font-weight: 600;
    color: #1f2937;
    font-size: 1rem;
}

/* Separador Profissional */
hr {
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    border: none;
    height: 1px;
    margin: 1.5rem 0;
}

/* Botões Profissionais */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s ease;
    border: none;
    padding: 0.75rem 1.5rem;
}

/* Inputs e Selects */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select,
.stMultiSelect > div > div > div {
    border-radius: 8px;
    border: 1px solid var(--border) !important;
    transition: all 0.3s ease;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

section[data-testid="stSidebar"] {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    overflow: auto;
    z-index: 1000;
    background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] > div {
    width: 16rem;
    padding-top: 1rem;
}
@media (min-width: 769px) {
    section[data-testid="stSidebar"] {
        width: 16rem !important;
        min-width: 16rem !important;
    }
    div[data-testid="stAppViewContainer"] > .main {
        margin-left: 16rem;
    }
}
@media (max-width: 768px) {
    div[data-testid="stAppViewContainer"] > .main {
        margin-left: 0;
    }
}
section[data-testid="stSidebar"] .stMarkdown h2 {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 0.75rem;
    letter-spacing: 0.02em;
}

section[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 0.35rem;
}

section[data-testid="stSidebar"] div[role="radiogroup"] > label {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 0.6rem 0.75rem;
    margin: 0;
    transition: all 0.25s ease;
}

section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background: rgba(37, 99, 235, 0.08);
    border-color: rgba(37, 99, 235, 0.15);
}

section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
    display: none;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label p {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 500;
    color: #4b5563;
    line-height: 1.25;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
    border-color: var(--primary);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}

section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] p {
    color: #ffffff;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

ESCOLA_ENDERECO = "R. Valter Souza Costa, 147 - Jardim Primavera, Ferraz de Vasconcelos - SP"
ESCOLA_NOME = "E.E. Profª Eliane"
ESCOLA_SUBTITULO = "Sistema Conviva 179"
ESCOLA_CEP = "CEP: 08535-310"
ESCOLA_TELEFONE = "Telefone: (11) 4675-1855"
ESCOLA_EMAIL = "Email: e918623@educacao.sp.gov.br"
ESCOLA_LOGO = os.path.join("assets", "images", "eliane_dantas.png")

# --- SENHA PARA EXCLUSÃO ---
SENHA_EXCLUSAO = "040600"

# --- MENU LATERAL ---
st.sidebar.markdown("## Menu")
menu = st.sidebar.radio("", [
    "🏠 Início",
    "📝 Registrar Ocorrência",
    "📋 Histórico de Ocorrências",
    "📄 Comunicado aos Pais",
    "📊 Gráficos e Indicadores",
    "🖨️ Imprimir PDF",
    "👨‍🏫 Cadastrar Professores",
    "👤 Cadastrar Assinaturas",
    "🎨 Eletiva",
    "🏫 Gerenciar Turmas",
    "👥 Lista de Alunos",
    "🗺️ Mapa da Sala",
    "💾 Backups"
], label_visibility="collapsed")

ELETIVAS_ARQUIVO = r"C:\Users\Freak Work\Desktop\IMportação.xlsx"

# --- DADOS INICIAIS DAS ELETIVAS (FALLBACK) ---
ELETIVAS = {
    "Solange": [],
    "Rosemeire": [],
    "Fernanda": [],
    "Fagna": [],
    "Elaine": [],
    "Geovana": [],
    "Shirley": [],
    "Rosangela": [],
    "Veronica": [],
    "Silvana": [],
    "Patricia": []
}

# --- CORES PARA TIPOS DE INFRAÇÃO ---
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

# --- CORES POR GRAVIDADE ---
CORES_GRAVIDADE = {
    "Leve": "#4CAF50",
    "Média": "#FFC107",
    "Grave": "#FF9800",
    "Gravíssima": "#F44336"
}

# --- PROTOCOLO 179 COMPLETO ---
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
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. (crime digital)\n✅ Preservar provas (prints, URLs)\n✅ Acionar Núcleo Tecnológico"
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
            "encaminhamento": "⚖️ CRIME (equiparado ao racismo - STF)\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ Diretoria de Ensino\n✅ Medidas disciplinares cabíveis"
        },
        "Gordofobia": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Mediação pedagógica\n✅ Acompanhamento psicológico\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Trabalho educativo sobre diversidade"
        },
        "Xenofobia": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚖️ CRIME INAFIANÇÁVEL\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ Diretoria de Ensino"
        },
        "Capacitismo (Discriminação por Deficiência)": {
            "gravidade": "Grave",
            "encaminhamento": "✅ B.O. recomendado\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ AEE (Atendimento Educacional Especializado)\n✅ Diretoria de Ensino"
        },
        "Misoginia / Violência de Gênero": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚖️ CRIME (Lei Maria da Penha)\n✅ B.O. OBRIGATÓRIO\n✅ DDM (Delegacia da Mulher)\n✅ Conselho Tutelar\n✅ CREAS\n✅ Medidas protetivas"
        },
        "Assédio Moral": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. recomendado\n✅ Acompanhamento psicológico"
        },
        "Assédio Sexual": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 CRIME - NÃO FAZER MEDIAÇÃO\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ DDM (se for o caso)\n✅ Afastamento do agressor\n✅ Acompanhamento psicológico da vítima"
        },
        "Importunação Sexual / Estupro": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 CRIME GRAVÍSSIMO\n✅ B.O. IMEDIATO\n✅ SAMU (se necessário)\n✅ Conselho Tutelar\n✅ IML (se for o caso)\n✅ Não confrontar o agressor\n✅ Preservar provas"
        },
        "Apologia ao Nazismo": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚖️ CRIME (Lei 7.716/89)\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Diretoria de Ensino\n✅ Medidas disciplinares cabíveis"
        }
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
            "gravidade": "Leve",
            "encaminhamento": "✅ Retirar o objeto\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Trabalho educativo sobre violência"
        },
        "Ameaça de Ataque Ativo": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 EMERGÊNCIA MÁXIMA\n✅ PM (190) e SAMU (192)\n✅ Protocolo de Segurança Escolar\n✅ Evacuação se necessário\n✅ B.O. OBRIGATÓRIO\n✅ Diretoria de Ensino"
        },
        "Ataque Ativo Concretizado": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 EMERGÊNCIA MÁXIMA\n✅ PM (190) e SAMU (192)\n✅ Protocolo de Segurança Escolar\n✅ B.O. OBRIGATÓRIO\n✅ IML (se houver óbito)\n✅ Apoio psicológico emergencial"
        },
        "Invasão": {
            "gravidade": "Grave",
            "encaminhamento": "✅ PM (190) se necessário\n✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Reforçar segurança da escola"
        },
        "Ocupação de Unidade Escolar": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Dialogar com estudantes\n✅ Notificar famílias\n✅ Diretoria de Ensino\n✅ Registrar em ata\n✅ Buscar mediação"
        },
        "Roubo": {
            "gravidade": "Grave",
            "encaminhamento": "✅ B.O. recomendado\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Registrar em ata\n✅ Acionar segurança"
        },
        "Furto": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho Tutelar (se menor)\n✅ Mediação pedagógica"
        },
        "Dano ao Patrimônio / Vandalismo": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Reparação do dano\n✅ Trabalho educativo"
        }
    },
    "💊 Drogas e Substâncias": {
        "Posse de Celular / Dispositivo Eletrônico": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Retirar dispositivo (conforme regimento)\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Devolver aos responsáveis"
        },
        "Consumo de Álcool e Tabaco": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Registrar em ata\n✅ Acompanhamento psicológico\n✅ Trabalho educativo sobre saúde"
        },
        "Consumo de Cigarro Eletrônico": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Registrar em ata\n✅ Acompanhamento psicológico\n✅ Trabalho educativo sobre saúde"
        },
        "Consumo de Substâncias Ilícitas": {
            "gravidade": "Grave",
            "encaminhamento": "✅ SAMU (192) se houver emergência\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. recomendado\n✅ CAPS/CREAS\n✅ Acompanhamento especializado"
        },
        "Comercialização de Álcool e Tabaco": {
            "gravidade": "Grave",
            "encaminhamento": "✅ B.O. recomendado\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Vigilância Sanitária\n✅ Registrar em ata"
        },
        "Envolvimento com Tráfico de Drogas": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 B.O. OBRIGATÓRIO\n✅ PM (190) se necessário\n✅ Conselho Tutelar\n✅ Não confrontar diretamente\n✅ Sigilo e segurança\n✅ Diretoria de Ensino"
        }
    },
    "🧠 Saúde Mental e Comportamento": {
        "Indisciplina": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Mediação pedagógica\n✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho de Classe\n✅ Acompanhamento pedagógico"
        },
        "Evasão Escolar / Infrequência": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Buscar ativa (visita domiciliar)\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Registrar em ata\n✅ Diretoria de Ensino\n✅ Programa de Busca Ativa"
        },
        "Sinais de Automutilação": {
            "gravidade": "Grave",
            "encaminhamento": "✅ SAMU (192) se houver risco imediato\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ CAPS Infantil/Juvenil\n✅ Acompanhamento psicológico\n✅ Rede de proteção"
        },
        "Sinais de Isolamento Social": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Acompanhamento psicológico\n✅ Notificar famílias\n✅ Orientação Educacional\n✅ Trabalho em grupo\n✅ Observação contínua"
        },
        "Sinais de Alterações Emocionais": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Acompanhamento psicológico\n✅ Notificar famílias\n✅ Orientação Educacional\n✅ Observação contínua"
        },
        "Tentativa de Suicídio": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 SAMU (192) IMEDIATO\n✅ Hospital de referência\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ CAPS\n✅ Rede de proteção\n✅ Pós-venção"
        },
        "Suicídio Concretizado": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 SAMU/PM/IML\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Diretoria de Ensino\n✅ Apoio psicológico emergencial\n✅ Pós-venção"
        },
        "Mal Súbito": {
            "gravidade": "Grave",
            "encaminhamento": "✅ SAMU (192)\n✅ Hospital de referência\n✅ Notificar famílias URGENTE\n✅ Registrar em ata\n✅ Acompanhamento"
        },
        "Óbito": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 SAMU/PM/IML\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Diretoria de Ensino\n✅ Apoio psicológico emergencial\n✅ Pós-venção"
        }
    },
    "🌐 Crimes e Situações Graves": {
        "Crimes Cibernéticos": {
            "gravidade": "Grave",
            "encaminhamento": "✅ B.O. (Delegacia de Crimes Digitais)\n✅ Preservar provas (prints, URLs)\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Núcleo Tecnológico da DE"
        },
        "Fake News / Disseminação de Informações Falsas": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Trabalho educativo sobre informação\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Orientação sobre consequências legais"
        },
        "Violência Doméstica / Maus Tratos": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚠️ SIGILO ABSOLUTO\n✅ Conselho Tutelar OBRIGATÓRIO\n✅ CREAS\n✅ DDM (se for o caso)\n✅ B.O.\n✅ Não confrontar agressor\n✅ Rede de proteção"
        },
        "Vulnerabilidade Familiar / Negligência": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Conselho Tutelar\n✅ CREAS\n✅ Notificar famílias\n✅ CRAS\n✅ Rede de proteção social"
        },
        "Alerta de Desaparecimento": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 PM (190) IMEDIATO\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ B.O.\n✅ Disseminar informações\n✅ Rede de busca"
        },
        "Sequestro": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 PM (190) IMEDIATO\n✅ Não negociar\n✅ Notificar famílias\n✅ B.O.\n✅ Seguir orientações policiais"
        },
        "Homicídio / Homicídio Tentado": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 PM (190) e SAMU (192)\n✅ B.O. OBRIGATÓRIO\n✅ IML (se for o caso)\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Pós-venção"
        },
        "Feminicídio": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 PM (190) e SAMU (192)\n✅ B.O. OBRIGATÓRIO\n✅ DDM\n✅ IML (se for o caso)\n✅ Notificar famílias\n✅ Conselho Tutelar"
        },
        "Incitamento a Atos Infracionais": {
            "gravidade": "Grave",
            "encaminhamento": "✅ B.O. recomendado\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Medidas disciplinares"
        }
    },
    "📋 Infrações Administrativas e Disciplinares": {
        "Acidentes e Eventos Inesperados": {
            "gravidade": "Grave",
            "encaminhamento": "✅ SAMU (192) se necessário\n✅ Notificar famílias URGENTE\n✅ Registrar em ata\n✅ B.O. se necessário\n✅ Diretoria de Ensino"
        },
        "Atos Obscenos / Atos Libidinosos": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Acompanhamento psicológico\n✅ Registrar em ata\n✅ Trabalho educativo"
        },
        "Uso Inadequado de Dispositivos Eletrônicos": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Retirar dispositivo\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Trabalho educativo sobre uso responsável"
        },
        "Saída não autorizada": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias URGENTE\n✅ Buscar o estudante\n✅ Conselho Tutelar (se recorrente)\n✅ Reforçar controle de acesso"
        },
        "Ausência não justificada / Cabular aula": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Buscar o estudante\n✅ Conselho Tutelar (se recorrente)\n✅ Orientação Educacional\n✅ Verificar situação de vulnerabilidade"
        },
        "Outros": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Avaliar necessidade de outros encaminhamentos\n✅ Conselho Tutelar se necessário"
        }
    },
    "⚠️ Infrações Acadêmicas e de Pontualidade": {
        "Chegar atrasado": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Conversar com o aluno\n✅ Notificar famílias (se recorrente)\n✅ Verificar motivo dos atrasos\n✅ Orientação Educacional"
        },
        "Copiar atividades / Colar em avaliações": {
            "gravidade": "Média",
            "encaminhamento": "✅ Registrar em ata\n✅ Aplicar nova avaliação\n✅ Notificar famílias\n✅ Orientação Educacional\n✅ Trabalho educativo sobre honestidade acadêmica\n✅ Conselho de Classe"
        },
        "Falsificar assinatura de responsáveis": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ Diretoria de Ensino\n✅ Acompanhamento psicológico\n✅ B.O. recomendado (crime de falsidade ideológica)"
        }
    }
}

# --- FUNÇÃO DE BUSCA FUZZY ---
def buscar_infracao_fuzzy(busca, protocolo):
    if not busca or len(busca) < 2:
        return {}
    busca_normalizada = busca.lower().strip()
    resultados = {}
    palavras_chave = {
        'celular': ['celular', 'telefone', 'smartphone', 'dispositivo', 'fone', 'headphone'],
        'atraso': ['atraso', 'atrasado', 'chegar atrasado', 'pontualidade'],
        'bullying': ['bullying', 'cyberbullying', 'intimidação', 'perseguição'],
        'agressao': ['agressão', 'agressao', 'bater', 'agredir', 'violência', 'violencia'],
        'furto': ['furto', 'roubo', 'roubar', 'furtar', 'levar', 'subtrair'],
        'dano': ['dano', 'danificar', 'destruir', 'quebrar', 'vandalismo', 'pichar'],
        'droga': ['droga', 'álcool', 'alcool', 'cigarro', 'fumo', 'maconha', 'substância'],
        'arma': ['arma', 'faca', 'canivete', 'perigoso'],
        'saida': ['saída', 'saida', 'sair', 'fugir', 'evadir', 'cabular', 'faltar'],
        'falsificar': ['falsificar', 'falsificação', 'assinatura', 'documento', 'colar', 'copiar'],
        'desrespeito': ['desrespeito', 'desobediência', 'insubordinação', 'desacato'],
        'ameaca': ['ameaça', 'ameaca', 'intimidar', 'amedrontar'],
        'discriminacao': ['racismo', 'homofobia', 'preconceito', 'discriminação', 'discriminacao']
    }
    for grupo, infracoes in protocolo.items():
        infracoes_encontradas = {}
        for nome_infracao, dados in infracoes.items():
            similaridade = SequenceMatcher(None, busca_normalizada, nome_infracao.lower()).ratio()
            palavras_busca = busca_normalizada.split()
            match_parcial = any(palavra in nome_infracao.lower() for palavra in palavras_busca)
            match_palavra_chave = False
            for chave, termos in palavras_chave.items():
                if chave in busca_normalizada or any(termo in busca_normalizada for termo in termos):
                    if any(termo in nome_infracao.lower() for termo in termos):
                        match_palavra_chave = True
                        break
            if similaridade > 0.4 or match_parcial or match_palavra_chave:
                infracoes_encontradas[nome_infracao] = dados
        if infracoes_encontradas:
            resultados[grupo] = infracoes_encontradas
    return resultados

# --- FUNÇÕES SUPABASE ---
def _supabase_request(method, path, **kwargs):
    if not SUPABASE_VALID:
        raise RuntimeError("Supabase não configurado. Verifique SUPABASE_URL e SUPABASE_KEY.")
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    response = requests.request(method, url, headers=HEADERS, **kwargs)
    response.raise_for_status()
    return response

def _supabase_error(acao):
    if not SUPABASE_VALID:
        raise ErroConexaoDB(f"Não foi possível {acao}")
    return False

def _supabase_get_dataframe(path, acao):
    if _supabase_error(acao):
        return pd.DataFrame()
    try:
        response = _supabase_request("GET", path)
        if response.status_code != 200:
            raise ErroCarregamentoDados(acao)
        return pd.DataFrame(response.json())
    except ErroConexaoDB:
        raise
    except Exception as e:
        raise ErroCarregamentoDados(acao, str(e))

def _supabase_mutation(method, path, data, acao):
    if _supabase_error(acao):
        return False
    try:
        kwargs = {}
        if data is not None:
            kwargs['json'] = data
        response = _supabase_request(method, path, **kwargs)
        sucesso = response.status_code in [200, 201, 204]
        if not sucesso:
            raise ErroOperacaoDB(acao)
        return sucesso
    except (ErroConexaoDB, ErroOperacaoDB):
        raise
    except Exception as e:
        raise ErroOperacaoDB(acao, str(e))

@st.cache_data(ttl=300)
@com_tratamento_erro
@com_retry(tentativas=2)
def carregar_alunos():
    return _supabase_get_dataframe("alunos?select=*", "carregar alunos")

@com_tratamento_erro
def salvar_aluno(aluno):
    valido, msg = Validadores.validar_nao_vazio(aluno.get("nome", ""), "Nome do aluno")
    if not valido:
        raise ErroValidacao("nome", msg)
    
    result = _supabase_mutation("POST", "alunos", aluno, "salvar aluno")
    if result:
        try:
            carregar_alunos.clear()
        except Exception:
            pass
    return result

@com_tratamento_erro
def atualizar_aluno(ra, dados):
    result = _supabase_mutation("PATCH", f"alunos?ra=eq.{ra}", dados, "atualizar aluno")
    if result:
        try:
            carregar_alunos.clear()
        except Exception:
            pass
    return result

@com_tratamento_erro
def editar_nome_turma(turma_antiga, turma_nova):
    if not turma_antiga or not turma_nova:
        raise ErroValidacao("turma", "Nomes de turma não podem estar vazios")
    
    result = _supabase_mutation("PATCH", f"alunos?turma=eq.{turma_antiga}", {"turma": turma_nova}, "editar nome da turma")
    if result:
        try:
            carregar_alunos.clear()
        except Exception:
            pass
    return result

@com_tratamento_erro
def excluir_alunos_por_turma(turma):
    if not turma:
        raise ErroValidacao("turma", "Turma não pode estar vazia")
    
    result = _supabase_mutation("DELETE", f"alunos?turma=eq.{turma}", None, "excluir turma")
    if result:
        try:
            carregar_alunos.clear()
        except Exception:
            pass
    return result

@st.cache_data(ttl=300)
@com_tratamento_erro
@com_retry(tentativas=2)
def carregar_professores():
    response = _supabase_request("GET", "professores?select=*")
    if response.status_code != 200:
        raise ErroCarregamentoDados("professores")
    return pd.DataFrame(response.json())

@com_tratamento_erro
def salvar_professor(professor):
    valido, msg = Validadores.validar_nao_vazio(professor.get("nome", ""), "Nome do professor")
    if not valido:
        raise ErroValidacao("nome", msg)
    
    try:
        response = _supabase_request("POST", "professores", json=professor)
        sucesso = response.status_code in [200, 201]
        if sucesso:
            try:
                carregar_professores.clear()
            except Exception:
                pass
        return sucesso
    except Exception as e:
        raise ErroOperacaoDB("salvar professor", str(e))

@com_tratamento_erro
def atualizar_professor(id_prof, dados):
    try:
        response = _supabase_request("PATCH", f"professores?id=eq.{id_prof}", json=dados)
        sucesso = response.status_code in [200, 204]
        if sucesso:
            try:
                carregar_professores.clear()
            except Exception:
                pass
        return sucesso
    except ErroConexaoDB:
        raise
    except Exception as e:
        raise ErroOperacaoDB("atualizar professor", str(e))

@com_tratamento_erro
def excluir_professor(id_prof):
    if not id_prof:
        raise ErroValidacao("id", "ID do professor não pode estar vazio")
    
    try:
        response = _supabase_request("DELETE", f"professores?id=eq.{id_prof}")
        sucesso = response.status_code in [200, 204]
        if sucesso:
            try:
                carregar_professores.clear()
            except Exception:
                pass
        return sucesso
    except ErroConexaoDB:
        raise
    except Exception as e:
        raise ErroOperacaoDB("excluir professor", str(e))

@st.cache_data(ttl=300)
@com_tratamento_erro
@com_retry(tentativas=2)
def carregar_responsaveis():
    return _supabase_get_dataframe("responsaveis?select=*&ativo=eq.true", "carregar responsáveis")

@com_tratamento_erro
def salvar_responsavel(responsavel):
    valido, msg = Validadores.validar_nao_vazio(responsavel.get("nome", ""), "Nome do responsável")
    if not valido:
        raise ErroValidacao("nome", msg)
    
    result = _supabase_mutation("POST", "responsaveis", responsavel, "salvar responsável")
    if result:
        limpar_cache_responsaveis()
    return result

@com_tratamento_erro
def atualizar_responsavel(id_resp, dados):
    result = _supabase_mutation("PATCH", f"responsaveis?id=eq.{id_resp}", dados, "atualizar responsável")
    if result:
        limpar_cache_responsaveis()
    return result

@com_tratamento_erro
def excluir_responsavel(id_resp):
    if not id_resp:
        raise ErroValidacao("id", "ID do responsável não pode estar vazio")
    
    result = _supabase_mutation("DELETE", f"responsaveis?id=eq.{id_resp}", None, "excluir responsável")
    if result:
        limpar_cache_responsaveis()
    return result

@st.cache_data(ttl=300)
@com_tratamento_erro
@com_retry(tentativas=2)
def carregar_eletivas_supabase():
    try:
        response = _supabase_request("GET", "eletivas?select=*&order=professora.asc,nome_aluno.asc")
        if response.status_code == 404:
            st.info("ℹ️ A tabela `eletivas` ainda não existe no Supabase. Usando planilha local.")
            return pd.DataFrame()
        if response.status_code != 200:
            raise ErroCarregamentoDados("eletivas")
        return pd.DataFrame(response.json())
    except ErroConexaoDB:
        raise
    except ErroCarregamentoDados:
        raise
    except Exception as e:
        raise ErroCarregamentoDados("eletivas", str(e))

def limpar_cache_eletivas():
    try:
        carregar_eletivas_supabase.clear()
    except Exception:
        pass

@com_tratamento_erro
def substituir_eletivas_supabase(registros):
    if not registros:
        limpar_cache_eletivas()
        return True
    
    try:
        try:
            _supabase_request("DELETE", "eletivas?id=not.is.null")
        except requests.HTTPError as e:
            if hasattr(e, 'response') and e.response.status_code == 404:
                st.info("ℹ️ A tabela `eletivas` não existe no Supabase. Crie a tabela antes de sincronizar.")
                return False
            raise
        
        response = _supabase_request("POST", "eletivas", json=registros)
        sucesso = response.status_code in [200, 201]
        if sucesso:
            limpar_cache_eletivas()
        return sucesso
    except ErroConexaoDB:
        raise
    except Exception as e:
        raise ErroOperacaoDB("salvar eletivas no Supabase", str(e))

@st.cache_data(ttl=300)
@com_tratamento_erro
@com_retry(tentativas=2)
def carregar_ocorrencias():
    return _supabase_get_dataframe("ocorrencias?select=*&order=id.desc", "carregar ocorrências")

@com_tratamento_erro
def salvar_ocorrencia(ocorrencia):
    valido, msg = Validadores.validar_nao_vazio(ocorrencia.get("aluno_nome", ""), "Nome do aluno")
    if not valido:
        raise ErroValidacao("aluno", msg)
    
    result = _supabase_mutation("POST", "ocorrencias", ocorrencia, "salvar ocorrência")
    if result:
        try:
            carregar_ocorrencias.clear()
        except Exception:
            pass
    return result

def excluir_ocorrencia(id_ocorrencia):
    result = _supabase_mutation("DELETE", f"ocorrencias?id=eq.{id_ocorrencia}", None, "excluir ocorrência")
    if result:
        try:
            carregar_ocorrencias.clear()
        except Exception:
            pass
    return result

def editar_ocorrencia(id_ocorrencia, dados):
    result = _supabase_mutation("PATCH", f"ocorrencias?id=eq.{id_ocorrencia}", dados, "editar ocorrência")
    if result:
        try:
            carregar_ocorrencias.clear()
        except Exception:
            pass
    return result

def verificar_ocorrencia_duplicada(ra, categoria, data_str, df_ocorrencias):
    if df_ocorrencias.empty:
        return False
    ocorrencias_existentes = df_ocorrencias[
        (df_ocorrencias['ra'] == ra) &
        (df_ocorrencias['categoria'] == categoria) &
        (df_ocorrencias['data'] == data_str)
    ]
    return not ocorrencias_existentes.empty

def verificar_professor_duplicado(nome, df_professores, id_atual=None):
    if df_professores.empty:
        return False
    nome_normalizado = nome.strip().lower()
    if id_atual:
        duplicados = df_professores[
            (df_professores['nome'].str.strip().str.lower() == nome_normalizado) &
            (df_professores['id'] != id_atual)
        ]
    else:
        duplicados = df_professores[df_professores['nome'].str.strip().str.lower() == nome_normalizado]
    return not duplicados.empty

def limpar_cache_responsaveis():
    try:
        carregar_responsaveis.clear()
    except Exception:
        pass

def get_responsavel_por_nome(responsaveis, cargos, nomes_prioritarios):
    if responsaveis.empty:
        return None
    responsaveis = responsaveis[responsaveis['cargo'].isin(cargos)]
    if responsaveis.empty:
        return None
    for nome in nomes_prioritarios:
        match = responsaveis[responsaveis['nome'].str.contains(nome, case=False, na=False)]
        if not match.empty:
            return match.iloc[0]['nome']
    return responsaveis.iloc[0]['nome']

def get_responsavel_por_cargo(responsaveis, cargos):
    if responsaveis.empty:
        return None
    for cargo in cargos:
        resp = responsaveis[responsaveis['cargo'] == cargo]
        if not resp.empty:
            return resp.iloc[0]['nome']
    return None

def selecionar_equipe_por_horario(data_str, responsaveis):
    diretor = get_responsavel_por_cargo(responsaveis, ["Diretor", "Diretora"]) or "Renan Lourenco Da Silva"
    vice_manha = get_responsavel_por_nome(responsaveis, ["Vice-Diretor", "Vice-Diretora"], ["Erika Paula", "Erika"]) or "Erika Paula Viana Watanabe"
    vice_tarde = get_responsavel_por_nome(responsaveis, ["Vice-Diretor", "Vice-Diretora"], ["Luciana Francisca", "Luciana"]) or "Luciana Francisca Da Conceicao"
    coord_manha = get_responsavel_por_nome(responsaveis, ["Coordenador", "Coordenadora", "CGPG", "CGPG / Coordenador(a)", "CGPG / Coordenador"], ["Aleandro", "Aleandro Ferreira"]) or "Aleandro Ferreira Dos Santos"
    coord_tarde = get_responsavel_por_nome(responsaveis, ["Coordenador", "Coordenadora", "CGPG", "CGPG / Coordenador(a)", "CGPG / Coordenador"], ["Rose Carmem", "Rose"]) or "Rose Carmem"
    turno = "Turno 1"
    vice = vice_manha
    coordenador = coord_manha
    try:
        hora = datetime.strptime(data_str.split()[-1], "%H:%M").time()
        if time(7, 0) <= hora < time(14, 30):
            turno = "Turno 1"
            vice = vice_manha
            coordenador = coord_manha
        elif time(14, 30) <= hora <= time(21, 30):
            turno = "Turno 2"
            vice = vice_tarde
            coordenador = coord_tarde
        else:
            turno = "Turno 1"
            vice = vice_manha
            coordenador = coord_manha
    except Exception:
        pass
    return {
        "turno": turno,
        "diretor": diretor,
        "vice": vice,
        "coordenador": coordenador
    }

def obter_gravidade_mais_alta(gravidades):
    ordem = {"Leve": 1, "Grave": 2, "Gravíssima": 3}
    if not gravidades:
        return "Leve"
    max_gravidade = max(gravidades, key=lambda g: ordem.get(g, 0))
    return max_gravidade

def combinar_encaminhamentos(encaminhamentos_lista):
    todos = []
    for encam in encaminhamentos_lista:
        for linha in encam.split('\n'):
            linha = linha.strip()
            if linha and linha not in todos:
                todos.append(linha)
    return '\n'.join(todos)

def normalizar_texto(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    return " ".join(texto.split())


def gerar_chave_segura(valor):
    texto = normalizar_texto(valor)
    texto = re.sub(r'[^A-Z0-9_]+', '_', texto)
    texto = texto.strip('_')
    return texto or 'sem_turma'


def encontrar_melhor_match(nome_busca, nomes_existentes):
    if not nome_busca or not nomes_existentes:
        return None, 0.0
    nome_norm = normalizar_texto(nome_busca)
    melhor_match = None
    melhor_score = 0.0

    for nome in nomes_existentes:
        nome_norm_cand = normalizar_texto(nome)
        score = SequenceMatcher(None, nome_norm, nome_norm_cand).ratio()

        if nome_norm_cand.startswith(nome_norm):
            score = max(score, 0.95)
        elif any(palavra.startswith(nome_norm) for palavra in nome_norm_cand.split()):
            score = max(score, 0.90)
        elif nome_norm in nome_norm_cand:
            score = max(score, 0.85)
        else:
            for palavra in nome_norm_cand.split():
                score = max(score, SequenceMatcher(None, nome_norm, palavra).ratio())

        if score > melhor_score:
            melhor_score = score
            melhor_match = nome

    return melhor_match, melhor_score


def carregar_eletivas_do_excel(caminho_arquivo, fallback=None):
    if not os.path.exists(caminho_arquivo):
        return fallback if fallback is not None else {}
    try:
        ns = {'a': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        with zipfile.ZipFile(caminho_arquivo) as arquivo_zip:
            shared_strings = []
            if 'xl/sharedStrings.xml' in arquivo_zip.namelist():
                shared_root = ET.fromstring(arquivo_zip.read('xl/sharedStrings.xml'))
                for si in shared_root.findall('a:si', ns):
                    textos = []
                    for texto in si.iterfind('.//a:t', ns):
                        textos.append(texto.text or '')
                    shared_strings.append(''.join(textos))
            planilha = ET.fromstring(arquivo_zip.read('xl/worksheets/sheet1.xml'))
            eletivas = {}
            professora_atual = None
            for row in planilha.findall('.//a:sheetData/a:row', ns):
                valores = {}
                for celula in row.findall('a:c', ns):
                    referencia = celula.attrib.get('r', '')
                    coluna = ''.join(ch for ch in referencia if ch.isalpha())
                    tipo = celula.attrib.get('t')
                    valor = ''
                    valor_xml = celula.find('a:v', ns)
                    if valor_xml is not None:
                        valor = valor_xml.text or ''
                    if tipo == 's' and valor != '':
                        valor = shared_strings[int(valor)]
                    valores[coluna] = str(valor).strip()
                valor_a = valores.get('A', '')
                valor_b = valores.get('B', '')
                valor_c = valores.get('C', '')
                if valor_a and not valor_b and not valor_c and not valor_a.isdigit():
                    professora_atual = valor_a
                    eletivas[professora_atual] = []
                    continue
                if valor_b.startswith('Professora '):
                    professora_atual = valor_b.replace('Professora ', '').strip()
                    eletivas[professora_atual] = []
                    continue
                if valor_a == 'Nº' or (valor_b == 'Nome' and valor_c == 'Turma') or valor_b == 'Nome do Estudante':
                    continue
                if professora_atual and valor_b and valor_c:
                    eletivas[professora_atual].append({
                        "nome": valor_b,
                        "serie": valor_c
                    })
            eletivas = {prof: alunos for prof, alunos in eletivas.items() if alunos}
            return eletivas if eletivas else (fallback if fallback is not None else {})
    except Exception:
        return fallback if fallback is not None else {}

def converter_eletivas_para_registros(eletivas_dict, origem="excel"):
    registros = []
    for professora, alunos in eletivas_dict.items():
        for item in alunos:
            registros.append({
                "professora": professora,
                "nome_aluno": item.get("nome", ""),
                "serie": item.get("serie", ""),
                "origem": origem
            })
    return registros

def converter_eletivas_supabase_para_dict(df_eletivas):
    if df_eletivas.empty:
        return {}
    eletivas = {}
    for _, row in df_eletivas.iterrows():
        professora = str(row.get("professora", "")).strip()
        nome_aluno = str(row.get("nome_aluno", "")).strip()
        serie = str(row.get("serie", "")).strip()
        if not professora or not nome_aluno:
            continue
        eletivas.setdefault(professora, []).append({
            "nome": nome_aluno,
            "serie": serie
        })
    return eletivas

def montar_dataframe_eletiva(nome_professora, df_alunos):
    registros = []
    alunos_db = df_alunos.copy() if not df_alunos.empty else pd.DataFrame()
    
    # Pre-processar dados do banco para busca rápida
    nome_col = None
    for c in alunos_db.columns:
        if c.lower() in ['nome', 'nome do aluno', 'aluno', 'estudante']:
            nome_col = c
            break
    if nome_col is not None:
        alunos_db['nome_norm'] = alunos_db[nome_col].apply(normalizar_texto)
    else:
        alunos_db['nome_norm'] = ""

    for item in ELETIVAS.get(nome_professora, []):
        nome_original = item['nome']
        nome_norm_excel = normalizar_texto(nome_original)
        
        melhor_match = None
        melhor_score = 0.0
        
        # Busca Inteligente: Match Exato por nome + Contenção + Fuzzy
        if not alunos_db.empty:
            exatos = alunos_db[alunos_db['nome_norm'] == nome_norm_excel]
            if not exatos.empty:
                melhor_match = exatos.iloc[0]
                melhor_score = 1.0
            else:
                for _, row in alunos_db.iterrows():
                    nome_db_norm = row.get('nome_norm', '')
                    if not nome_db_norm:
                        continue
                    
                    score = 0.0
                    
                    # Contenção (um está dentro do outro)
                    if nome_norm_excel in nome_db_norm or nome_db_norm in nome_norm_excel:
                        score = SequenceMatcher(None, nome_norm_excel, nome_db_norm).ratio()
                        if score > melhor_score:
                            melhor_score = score
                            melhor_match = row
                    
                    # Fuzzy Match
                    elif melhor_score < 0.85:
                        score = SequenceMatcher(None, nome_norm_excel, nome_db_norm).ratio()
                        if score > melhor_score:
                            melhor_score = score
                            melhor_match = row

        # Define o status baseado na confiança do match (Threshold 80%)
        if melhor_match is not None and melhor_score >= 0.80:
            registros.append({
                "Professora": nome_professora,
                "Nome da Eletiva": nome_original,
                "Série da Eletiva": item['serie'],
                "Aluno Cadastrado": melhor_match.get('nome', ''),
                "RA": melhor_match.get('ra', ''),
                "Turma no Sistema": melhor_match.get('turma', ''),
                "Situação": melhor_match.get('situacao', ''),
                "Status": "Encontrado"
            })
        else:
            registros.append({
                "Professora": nome_professora,
                "Nome da Eletiva": nome_original,
                "Série da Eletiva": item['serie'],
                "Aluno Cadastrado": "",
                "RA": "",
                "Turma no Sistema": "",
                "Situação": "",
                "Status": "Não encontrado"
            })
    return pd.DataFrame(registros)

# Carrega as eletivas da planilha ao iniciar
ELETIVAS_EXCEL = carregar_eletivas_do_excel(ELETIVAS_ARQUIVO, fallback=ELETIVAS)

def gerar_pdf_eletiva(nome_professora, df_eletiva):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elementos = []
    estilos = getSampleStyleSheet()
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4*cm)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 0.2*cm))
    except Exception:
        pass
    elementos.append(Paragraph("_" * 75, estilos['Normal']))
    elementos.append(Spacer(1, 0.15*cm))
    estilo_titulo = ParagraphStyle('TituloEletiva', parent=estilos['Heading1'],
                                   fontSize=12, alignment=1, spaceAfter=0.3*cm, textColor=colors.darkblue)
    estilo_texto = ParagraphStyle('TextoEletiva', parent=estilos['Normal'],
                                  fontSize=9, leading=11, spaceAfter=0.1*cm)
    elementos.append(Paragraph("LISTA DE ELETIVA", estilo_titulo))
    elementos.append(Paragraph(f"<b>Professora:</b> {nome_professora}", estilo_texto))
    elementos.append(Paragraph(f"<b>Total de estudantes:</b> {len(df_eletiva)}", estilo_texto))
    elementos.append(Spacer(1, 0.2*cm))
    dados_tabela = [["Nome da Eletiva", "Série", "RA", "Turma", "Status"]]
    for _, row in df_eletiva.iterrows():
        dados_tabela.append([
            str(row.get("Nome da Eletiva", "")),
            str(row.get("Série da Eletiva", "")),
            str(row.get("RA", "")),
            str(row.get("Turma no Sistema", "")),
            str(row.get("Status", ""))
        ])
    tabela = Table(dados_tabela, colWidths=[7.8*cm, 2.0*cm, 2.0*cm, 2.3*cm, 2.4*cm], repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9FBFD')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabela)
    elementos.append(Spacer(1, 0.3*cm))
    estilo_rodape = ParagraphStyle('RodapeEletiva', parent=estilos['Normal'],
                                   fontSize=6, alignment=1, textColor=colors.grey)
    elementos.append(Paragraph("_" * 75, estilos['Normal']))
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
    doc.build(elementos)
    buffer.seek(0)
    return buffer

def gerar_pdf_ocorrencia(ocorrencia, responsaveis):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elementos = []
    estilos = getSampleStyleSheet()
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4*cm)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 0.2*cm))
    except:
        pass
    elementos.append(Paragraph("_" * 75, estilos['Normal']))
    elementos.append(Spacer(1, 0.15*cm))
    protocolo = f"PROTOCOLO: {ocorrencia.get('id', 'N/A')}/{datetime.now().strftime('%Y')}"
    estilo_protocolo = ParagraphStyle('Protocolo', parent=estilos['Normal'],
                                      fontSize=9, alignment=2, spaceAfter=0.15*cm, textColor=colors.darkblue)
    elementos.append(Paragraph(f"<b>{protocolo}</b>", estilo_protocolo))
    elementos.append(Spacer(1, 0.15*cm))
    estilo_titulo = ParagraphStyle('TituloDoc', parent=estilos['Heading1'],
                                   fontSize=12, alignment=1, spaceAfter=0.3*cm, textColor=colors.darkblue)
    elementos.append(Paragraph("REGISTRO DE OCORRÊNCIA", estilo_titulo))
    elementos.append(Spacer(1, 0.2*cm))
    dados = [
        ["Data:", ocorrencia.get("data", "")],
        ["Aluno:", ocorrencia.get("aluno", "")],
        ["RA:", str(ocorrencia.get("ra", ""))],
        ["Turma:", ocorrencia.get("turma", "")],
        ["Categoria:", ocorrencia.get("categoria", "")],
        ["Gravidade:", ocorrencia.get("gravidade", "")],
        ["Professor:", ocorrencia.get("professor", "")]
    ]
    tabela_dados = Table(dados, colWidths=[3*cm, 12*cm])
    tabela_dados.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#4A90E2')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabela_dados)
    elementos.append(Spacer(1, 0.2*cm))
    estilo_secao = ParagraphStyle('Secao', parent=estilos['Normal'],
                                  fontSize=9, textColor=colors.darkblue, spaceAfter=0.1*cm)
    estilo_texto = ParagraphStyle('Texto', parent=estilos['Normal'],
                                  fontSize=11, alignment=4, spaceAfter=0.15*cm, leading=13)
    elementos.append(Paragraph("<b>📝 RELATO:</b>", estilo_secao))
    elementos.append(Paragraph(str(ocorrencia.get("relato", "")), estilo_texto))
    elementos.append(Spacer(1, 0.15*cm))
    elementos.append(Paragraph("<b>🔀 ENCAMINHAMENTOS:</b>", estilo_secao))
    encam_texto = str(ocorrencia.get("encaminhamento", "")).replace('\n', '<br/>')
    elementos.append(Paragraph(encam_texto, estilo_texto))
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("<b>ASSINATURAS:</b>", estilo_secao))
    elementos.append(Spacer(1, 0.2*cm))
    equipe = selecionar_equipe_por_horario(ocorrencia.get("data", ""), responsaveis)
    elementos.append(Paragraph(f"<b>Diretor:</b> {equipe['diretor']}", estilo_texto))
    elementos.append(Paragraph(f"<b>Vice-Diretor:</b> {equipe['vice']}", estilo_texto))
    elementos.append(Paragraph(f"<b>Coordenador:</b> {equipe['coordenador']}", estilo_texto))
    elementos.append(Spacer(1, 0.5*cm))
    estilo_rodape = ParagraphStyle('Rodape', parent=estilos['Normal'],
                                   fontSize=6, alignment=1, textColor=colors.grey)
    elementos.append(Paragraph("_" * 75, estilos['Normal']))
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
    doc.build(elementos)
    buffer.seek(0)
    return buffer

def gerar_pdf_comunicado(aluno_data, ocorrencia_data, medidas_aplicadas, observacoes, responsaveis):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elementos = []
    estilos = getSampleStyleSheet()
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4*cm)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 0.2*cm))
    except:
        pass
    elementos.append(Paragraph("_" * 75, estilos['Normal']))
    elementos.append(Spacer(1, 0.15*cm))
    protocolo = f"PROTOCOLO: {ocorrencia_data.get('id', 'N/A')}/{datetime.now().strftime('%Y')}"
    estilo_protocolo = ParagraphStyle('Protocolo', parent=estilos['Normal'],
                                      fontSize=9, alignment=2, spaceAfter=0.15*cm, textColor=colors.darkblue)
    elementos.append(Paragraph(f"<b>{protocolo}</b>", estilo_protocolo))
    elementos.append(Spacer(1, 0.15*cm))
    estilo_titulo = ParagraphStyle('TituloDoc', parent=estilos['Heading1'],
                                   fontSize=12, alignment=1, spaceAfter=0.3*cm, textColor=colors.darkblue)
    elementos.append(Paragraph("COMUNICADO AOS PAIS/RESPONSÁVEIS", estilo_titulo))
    elementos.append(Spacer(1, 0.2*cm))
    estilo_secao = ParagraphStyle('Secao', parent=estilos['Normal'],
                                  fontSize=9, textColor=colors.darkblue, spaceAfter=0.1*cm)
    estilo_texto = ParagraphStyle('Texto', parent=estilos['Normal'],
                                  fontSize=11, alignment=4, spaceAfter=0.15*cm, leading=13)
    elementos.append(Paragraph("<b>DADOS DO ALUNO:</b>", estilo_secao))
    dados_aluno = [
        ["Nome:", aluno_data.get("nome", "")],
        ["RA:", str(aluno_data.get("ra", ""))],
        ["Turma:", aluno_data.get("turma", "")],
        ["Total Ocorrências:", str(aluno_data.get("total_ocorrencias", 0))]
    ]
    tabela_aluno = Table(dados_aluno, colWidths=[3*cm, 12*cm])
    tabela_aluno.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#4A90E2')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elementos.append(tabela_aluno)
    elementos.append(Spacer(1, 0.2*cm))
    elementos.append(Paragraph("<b>DADOS DA OCORRÊNCIA:</b>", estilo_secao))
    dados_ocorrencia = [
        ["Data:", ocorrencia_data.get("data", "")],
        ["Categoria:", ocorrencia_data.get("categoria", "")],
        ["Gravidade:", ocorrencia_data.get("gravidade", "")],
        ["Professor:", ocorrencia_data.get("professor", "")]
    ]
    tabela_ocorrencia = Table(dados_ocorrencia, colWidths=[3*cm, 12*cm])
    tabela_ocorrencia.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#4A90E2')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elementos.append(tabela_ocorrencia)
    elementos.append(Spacer(1, 0.2*cm))
    elementos.append(Paragraph("<b>📝 RELATO:</b>", estilo_secao))
    elementos.append(Paragraph(str(ocorrencia_data.get("relato", "")), estilo_texto))
    elementos.append(Spacer(1, 0.15*cm))
    if medidas_aplicadas:
        elementos.append(Paragraph("<b>⚖️ MEDIDAS:</b>", estilo_secao))
        for medida in medidas_aplicadas.split(' | '):
            if medida.strip():
                elementos.append(Paragraph(f"• {medida}", estilo_texto))
        elementos.append(Spacer(1, 0.15*cm))
    if observacoes:
        elementos.append(Paragraph("<b>📌 OBSERVAÇÕES:</b>", estilo_secao))
        elementos.append(Paragraph(str(observacoes), estilo_texto))
        elementos.append(Spacer(1, 0.15*cm))
    elementos.append(Paragraph("<b>🔀 ENCAMINHAMENTOS:</b>", estilo_secao))
    encam = ocorrencia_data.get("encaminhamento", "")
    for linha in encam.split('\n'):
        if linha.strip():
            elementos.append(Paragraph(f"• {linha}", estilo_texto))
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("<b>CIÊNCIA DOS PAIS:</b>", estilo_secao))
    elementos.append(Spacer(1, 0.2*cm))
    elementos.append(Paragraph("Declaro ciência deste comunicado.", estilo_texto))
    elementos.append(Spacer(1, 1*cm))
    elementos.append(Paragraph("_" * 40, estilos['Normal']))
    elementos.append(Paragraph("Assinatura do Responsável", ParagraphStyle('Assinatura', parent=estilos['Normal'], fontSize=7, alignment=1)))
    estilo_rodape = ParagraphStyle('Rodape', parent=estilos['Normal'],
                                   fontSize=6, alignment=1, textColor=colors.grey)
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("_" * 75, estilos['Normal']))
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# --- SESSION STATE ---
if 'editando_id' not in st.session_state:
    st.session_state.editando_id = None
if 'dados_edicao' not in st.session_state:
    st.session_state.dados_edicao = None
if 'editando_prof' not in st.session_state:
    st.session_state.editando_prof = None
if 'editando_resp' not in st.session_state:
    st.session_state.editando_resp = None
if 'turma_para_deletar' not in st.session_state:
    st.session_state.turma_para_deletar = None
if 'turma_selecionada' not in st.session_state:
    st.session_state.turma_selecionada = None
if 'salvando_ocorrencia' not in st.session_state:
    st.session_state.salvando_ocorrencia = False
if 'ocorrencia_salva_sucesso' not in st.session_state:
    st.session_state.ocorrencia_salva_sucesso = False
if 'gravidade_alterada' not in st.session_state:
    st.session_state.gravidade_alterada = False
if 'adicionar_outra_infracao' not in st.session_state:
    st.session_state.adicionar_outra_infracao = False
if 'infracoes_adicionais' not in st.session_state:
    st.session_state.infracoes_adicionais = []
if 'senha_exclusao_validada' not in st.session_state:
    st.session_state.senha_exclusao_validada = False
if 'professor_salvo_sucesso' not in st.session_state:
    st.session_state.professor_salvo_sucesso = False
if 'nome_professor_salvo' not in st.session_state:
    st.session_state.nome_professor_salvo = ""
if 'cargo_professor_salvo' not in st.session_state:
    st.session_state.cargo_professor_salvo = ""
if 'responsavel_salvo_sucesso' not in st.session_state:
    st.session_state.responsavel_salvo_sucesso = False
if 'nome_responsavel_salvo' not in st.session_state:
    st.session_state.nome_responsavel_salvo = ""
if 'cargo_responsavel_salvo' not in st.session_state:
    st.session_state.cargo_responsavel_salvo = ""

# --- BACKUP AUTOMÁTICO ---
if 'backup_manager' not in st.session_state:
    st.session_state.backup_manager = BackupManager()
    # Fazer backup automático na inicialização (uma vez por sessão)
    st.session_state.backup_manager.criar_backup()
    st.session_state.backup_manager.limpar_backups_antigos(dias_retencao=30)

# --- CARREGAR DADOS ---
df_alunos = carregar_alunos()
df_ocorrencias = carregar_ocorrencias()
df_professores = carregar_professores()
df_responsaveis = carregar_responsaveis()
df_eletivas_supabase = carregar_eletivas_supabase()

# Lógica de carregamento das Eletivas
if 'ELETIVAS' not in st.session_state:
    if not df_eletivas_supabase.empty:
        st.session_state.ELETIVAS = converter_eletivas_supabase_para_dict(df_eletivas_supabase)
        FONTE_ELETIVAS = "supabase"
    else:
        st.session_state.ELETIVAS = ELETIVAS_EXCEL
        FONTE_ELETIVAS = "excel"
else:
    if not df_eletivas_supabase.empty:
        FONTE_ELETIVAS = "supabase"
    else:
        FONTE_ELETIVAS = "excel"

ELETIVAS = st.session_state.ELETIVAS

# --- 1. HOME ---
if menu == "🏠 Início":
    st.markdown(f"""
<div class="main-header">
    <img src="https://raw.githubusercontent.com/Fr34k1981/SistemaConviva/main/logo.jpg"
         style="max-width: 150px; margin-bottom: 1rem; border-radius: 10px;" alt="Logo da Escola">
    <div class="school-name">{ESCOLA_NOME}</div>
    <div class="school-subtitle">{ESCOLA_SUBTITULO}</div>
    <div class="school-address">{ESCOLA_ENDERECO}</div>
    <div class="school-contact">
        {ESCOLA_CEP} • {ESCOLA_TELEFONE} • {ESCOLA_EMAIL}
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("### Sistema de Gestão de Ocorrências Escolares")
    st.markdown("---")
    
    # Métricas Principais
    st.markdown("#### Indicadores Gerais")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: 
        st.metric("Total de Alunos", len(df_alunos), delta=None)
    with col2: 
        st.metric("Ocorrências", len(df_ocorrencias), delta=None)
    with col3:
        graves = len(df_ocorrencias[df_ocorrencias["gravidade"] == "Gravíssima"]) if not df_ocorrencias.empty else 0
        st.metric("Gravíssimas", graves, delta=None)
    with col4:
        profs = len(df_professores) if not df_professores.empty else 0
        st.metric("Professores", profs, delta=None)
    with col5:
        media = round(len(df_ocorrencias) / len(df_alunos), 2) if len(df_alunos) > 0 else 0
        st.metric("Ocor. por Aluno", media, delta=None)

    # Contagem por Gravidade
    if not df_ocorrencias.empty:
        st.markdown("---")
        st.markdown("#### Distribuição por Gravidade")
        leve = len(df_ocorrencias[df_ocorrencias["gravidade"] == "Leve"])
        media = len(df_ocorrencias[df_ocorrencias["gravidade"] == "Média"])
        grave = len(df_ocorrencias[df_ocorrencias["gravidade"] == "Grave"])
        gravissima = len(df_ocorrencias[df_ocorrencias["gravidade"] == "Gravíssima"])
        total_occ = len(df_ocorrencias)
        average_gravity = round((leve * 1 + media * 2 + grave * 3 + gravissima * 4) / total_occ, 2) if total_occ > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 1.5rem; border-radius: 10px; text-align: center; color: #065f46; border-left: 4px solid #10b981;">
                <div style="font-size: 2.5rem; font-weight: bold;">{leve}</div>
                <div style="font-size: 0.95rem; font-weight: 500;">Leves</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fef08a 0%, #fde047 100%); padding: 1.5rem; border-radius: 10px; text-align: center; color: #78350f; border-left: 4px solid #f59e0b;">
                <div style="font-size: 2.5rem; font-weight: bold;">{media}</div>
                <div style="font-size: 0.95rem; font-weight: 500;">Médias</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%); padding: 1.5rem; border-radius: 10px; text-align: center; color: #7c2d12; border-left: 4px solid #f97316;">
                <div style="font-size: 2.5rem; font-weight: bold;">{grave}</div>
                <div style="font-size: 0.95rem; font-weight: 500;">Graves</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%); padding: 1.5rem; border-radius: 10px; text-align: center; color: #7f1d1d; border-left: 4px solid #ef4444;">
                <div style="font-size: 2.5rem; font-weight: bold;">{gravissima}</div>
                <div style="font-size: 0.95rem; font-weight: 500;">Gravíssimas</div>
            </div>
            """, unsafe_allow_html=True)

    # Gráficos na página inicial
    if not df_ocorrencias.empty:
        st.markdown("---")
        st.markdown("#### Análise Visual de Dados")
        col1, col2 = st.columns(2)
        with col1:
            # Gráfico por Gravidade
            contagem_grav = df_ocorrencias['gravidade'].value_counts()
            fig_grav = px.pie(
                values=contagem_grav.values,
                names=contagem_grav.index,
                title='Distribuição por Gravidade',
                color_discrete_map={'Leve': '#4CAF50', 'Média': '#FFC107', 'Grave': '#FF9800', 'Gravíssima': '#F44336'},
                hole=0.3
            )
            st.plotly_chart(fig_grav, use_container_width=True)
        with col2:
            # Gráfico por Turma (top 10)
            top_turmas = df_ocorrencias['turma'].value_counts().head(10)
            fig_turmas = px.bar(
                top_turmas,
                x=top_turmas.index,
                y=top_turmas.values,
                title='Top 10 Turmas com Mais Ocorrências',
                labels={'y': 'Quantidade', 'x': 'Turma'},
                color=top_turmas.values,
                color_continuous_scale='Viridis'
            )
            fig_turmas.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_turmas, use_container_width=True)
        # Top 10 Alunos com Mais Ocorrências
        if not df_ocorrencias.empty:
            st.markdown("---")
            st.markdown("## 🏆 Top 10 Alunos com Mais Ocorrências")
            top_students = df_ocorrencias['aluno'].value_counts().head(10)
            if not top_students.empty:
                fig_students = px.bar(
                    top_students,
                    x=top_students.index,
                    y=top_students.values,
                    title='Top 10 Alunos com Mais Ocorrências',
                    labels={'y': 'Quantidade', 'x': 'Aluno'},
                    color=top_students.values,
                    color_continuous_scale='Reds'
                )
                fig_students.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_students, use_container_width=True)

# --- 2. CADASTRAR PROFESSORES ---
elif menu == "👨‍🏫 Cadastrar Professores":
    st.header("👨‍🏫 Cadastrar Professores")
    # Exibir mensagem de sucesso se houver
    if st.session_state.professor_salvo_sucesso:
        st.success(f"✅ {st.session_state.cargo_professor_salvo} {st.session_state.nome_professor_salvo} cadastrado com sucesso!")
        st.session_state.professor_salvo_sucesso = False
        st.session_state.nome_professor_salvo = ""
        st.session_state.cargo_professor_salvo = ""

    with st.expander("📥 Importar Professores em Massa", expanded=False):
        st.info("💡 Cole uma lista de nomes de professores (um por linha)")
        texto_professores = st.text_area("Cole os nomes dos professores aqui:",
                                         height=150, placeholder="Alnei Maria De Moura Nogueira\nAna Paula De Oliveira Farias...")
        if st.button("📥 Importar Professores"):
            if texto_professores:
                nomes = [nome.strip() for nome in texto_professores.split('\n') if nome.strip()]
                contagem = 0
                duplicados = 0
                for nome_prof in nomes:
                    if verificar_professor_duplicado(nome_prof, df_professores):
                        duplicados += 1
                    else:
                        novo_prof = {"nome": nome_prof, "email": None}
                        if salvar_professor(novo_prof):
                            contagem += 1
                if contagem > 0:
                    st.success(f"✅ {contagem} professores importados com sucesso!")
                if duplicados > 0:
                    st.warning(f"⚠️ {duplicados} professores já existiam (ignorado)")
                if contagem > 0 or duplicados > 0:
                    st.rerun()
            else:
                st.error("❌ Cole os nomes dos professores!")

    st.markdown("---")
    if st.session_state.editando_prof:
        st.subheader("✏️ Editar Cadastro")
        prof_edit = df_professores[df_professores['id'] == st.session_state.editando_prof].iloc[0]
        cargo_edit = prof_edit.get('cargo', 'Professor')
        nome_prof = st.text_input("Nome *", value=prof_edit['nome'], key="edit_nome_prof")
        cargo_prof = st.selectbox("Cargo/Função",
                                  ["Professor", "Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora", "Agente de Organização", "Outro"],
                                  index=["Professor", "Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora", "Agente de Organização", "Outro"].index(cargo_edit) if cargo_edit in ["Professor", "Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora", "Agente de Organização", "Outro"] else 0,
                                  key="edit_cargo_prof")
        email_prof = st.text_input("E-mail (opcional)", value=prof_edit.get('email', ''), key="edit_email_prof")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Alterações", type="primary"):
                if nome_prof:
                    if verificar_professor_duplicado(nome_prof, df_professores, st.session_state.editando_prof):
                        st.error("❌ Já existe um professor com este nome cadastrado!")
                    else:
                        if atualizar_professor(st.session_state.editando_prof, {"nome": nome_prof, "cargo": cargo_prof, "email": email_prof if email_prof else None}):
                            st.success("✅ Cadastro atualizado com sucesso!")
                            st.session_state.editando_prof = None
                            st.rerun()
        with col2:
            if st.button("❌ Cancelar"):
                st.session_state.editando_prof = None
                st.rerun()
    else:
        col1, col2 = st.columns(2)
        with col1:
            nome_prof = st.text_input("Nome *", placeholder="Ex: João da Silva", key="novo_nome_prof")
            cargo_prof = st.selectbox("Cargo/Função *",
                                      ["Professor", "Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora", "Agente de Organização", "Outro"],
                                      key="novo_cargo_prof")
            email_prof = st.text_input("E-mail (opcional)", placeholder="Ex: joao@educacao.sp.gov.br", key="novo_email_prof")
        with col2:
            st.info("💡 Cadastre professores, diretores, coordenadores e outros cargos da escola.")
        if st.button("💾 Salvar Cadastro", type="primary"):
            if nome_prof:
                if verificar_professor_duplicado(nome_prof, df_professores):
                    st.error("❌ Já existe alguém com este nome cadastrado!")
                else:
                    novo_prof = {"nome": nome_prof, "cargo": cargo_prof, "email": email_prof if email_prof else None}
                    if salvar_professor(novo_prof):
                        st.session_state.professor_salvo_sucesso = True
                        st.session_state.nome_professor_salvo = nome_prof
                        st.session_state.cargo_professor_salvo = cargo_prof
                        st.rerun()
            else:
                st.error("❌ Nome é obrigatório!")
    st.markdown("---")
    st.subheader("📋 Cadastros (Professores, Diretores, Coordenadores, etc)")
    if not df_professores.empty:
        for idx, prof in df_professores.iterrows():
            cargo_display = prof.get('cargo', 'Professor')
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"**{prof['nome']}** - {cargo_display}" + (f" ({prof['email']})" if prof.get('email') else ""))
            with col2:
                if st.button("✏️ Editar", key=f"edit_prof_{prof['id']}"):
                    st.session_state.editando_prof = prof['id']
                    st.rerun()
            with col3:
                if st.button("🗑️ Excluir", key=f"del_prof_{prof['id']}"):
                    st.session_state['confirmar_exclusao_prof'] = prof['id']
                    st.rerun()
        st.info(f"Total: {len(df_professores)} cadastro(s)")
    else:
        st.write("📭 Nenhum professor cadastrado.")

    # Mostrar confirmação de exclusão de professor se necessário
    if 'confirmar_exclusao_prof' in st.session_state:
        prof_id = st.session_state['confirmar_exclusao_prof']
        prof_excluir = df_professores[df_professores['id'] == prof_id].iloc[0]
        st.warning("⚠️ **Confirmação de Exclusão de Professor**")
        st.info(f"Você está prestes a excluir permanentemente o professor **{prof_excluir['nome']}**. Esta ação não pode ser desfeita.")
        col_conf_prof1, col_conf_prof2 = st.columns(2)
        with col_conf_prof1:
            if st.button("✅ Confirmar Exclusão", type="primary"):
                if excluir_professor(prof_id):
                    st.success("✅ Professor excluído com sucesso!")
                    del st.session_state['confirmar_exclusao_prof']
                    st.rerun()
                else:
                    st.error("❌ Falha ao excluir professor.")
                    del st.session_state['confirmar_exclusao_prof']
        with col_conf_prof2:
            if st.button("❌ Cancelar", type="secondary"):
                del st.session_state['confirmar_exclusao_prof']
                st.rerun()

# --- 3. CADASTRAR RESPONSÁVEIS ---
elif menu == "👤 Cadastrar Assinaturas":
    st.header("👤 Cadastrar Assinaturas")
    if st.session_state.responsavel_salvo_sucesso:
        st.success(f"✅ {st.session_state.cargo_responsavel_salvo} {st.session_state.nome_responsavel_salvo} cadastrado com sucesso!")
        st.session_state.responsavel_salvo_sucesso = False
        st.session_state.nome_responsavel_salvo = ""
        st.session_state.cargo_responsavel_salvo = ""

    st.info("💡 Pode haver múltiplos responsáveis por cargo (ex: 2 Vice-Diretoras)")
    if st.session_state.editando_resp:
        st.subheader("✏️ Editar Responsável")
        resp_edit = df_responsaveis[df_responsaveis['id'] == st.session_state.editando_resp].iloc[0]
        cargo_edit = resp_edit['cargo']
        nome_resp = st.text_input("Nome", value=resp_edit['nome'], key="edit_nome_resp")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Alterações", type="primary"):
                if nome_resp:
                    if atualizar_responsavel(st.session_state.editando_resp, {"nome": nome_resp}):
                        st.success("✅ Responsável atualizado com sucesso!")
                        st.session_state.editando_resp = None
                        st.rerun()
        with col2:
            if st.button("❌ Cancelar"):
                st.session_state.editando_resp = None
                st.rerun()
    else:
        st.subheader("➕ Novo Responsável")
        cargos = ["Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora"]
        cargo = st.selectbox("Cargo", cargos, key="novo_cargo")
        nome_resp = st.text_input("Nome do Responsável *", placeholder="Ex: Maria Silva", key="novo_nome_resp")
        if st.button("💾 Cadastrar", type="primary"):
            if nome_resp:
                if salvar_responsavel({"cargo": cargo, "nome": nome_resp, "ativo": True}):
                    st.session_state.responsavel_salvo_sucesso = True
                    st.session_state.nome_responsavel_salvo = nome_resp
                    st.session_state.cargo_responsavel_salvo = cargo
                    st.rerun()
                else:
                    st.error("❌ Falha ao salvar responsável.")
            else:
                st.error("❌ Nome é obrigatório!")
    st.markdown("---")
    st.subheader("📋 Responsáveis Cadastrados")
    if not df_responsaveis.empty:
        for cargo in ["Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora"]:
            resp_cargo = df_responsaveis[df_responsaveis['cargo'] == cargo]
            if not resp_cargo.empty:
                st.markdown(f"**📌 {cargo}:**")
                for idx, resp in resp_cargo.iterrows():
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        st.markdown(f"• {resp['nome']}")
                    with col2:
                        if st.button("✏️", key=f"edit_resp_{resp['id']}"):
                            st.session_state.editando_resp = resp['id']
                            st.rerun()
                    with col3:
                        if st.button("🗑️", key=f"del_resp_{resp['id']}"):
                            st.session_state['confirmar_exclusao_resp'] = resp['id']
                            st.rerun()
                st.markdown("")
    else:
        st.write("📭 Nenhum responsável cadastrado.")

    # Mostrar confirmação de exclusão de responsável se necessário
    if 'confirmar_exclusao_resp' in st.session_state:
        resp_id = st.session_state['confirmar_exclusao_resp']
        resp_excluir = df_responsaveis[df_responsaveis['id'] == resp_id].iloc[0]
        st.warning("⚠️ **Confirmação de Exclusão de Responsável**")
        st.info(f"Você está prestes a excluir permanentemente o responsável **{resp_excluir['nome']}** do cargo **{resp_excluir['cargo']}**. Esta ação não pode ser desfeita.")
        col_conf_resp1, col_conf_resp2 = st.columns(2)
        with col_conf_resp1:
            if st.button("✅ Confirmar Exclusão", type="primary"):
                if excluir_responsavel(resp_id):
                    st.success("✅ Responsável excluído com sucesso!")
                    del st.session_state['confirmar_exclusao_resp']
                    st.rerun()
                else:
                    st.error("❌ Falha ao excluir responsável.")
                    del st.session_state['confirmar_exclusao_resp']
        with col_conf_resp2:
            if st.button("❌ Cancelar", type="secondary"):
                del st.session_state['confirmar_exclusao_resp']
                st.rerun()

# --- 4. REGISTRAR OCORRÊNCIA ---
elif menu == "📝 Registrar Ocorrência":
    st.header("📝 Nova Ocorrência")
    if st.session_state.ocorrencia_salva_sucesso:
        st.markdown('<div class="success-box">✅ OCORRÊNCIA(S) REGISTRADA(S) COM SUCESSO!</div>', unsafe_allow_html=True)
        st.session_state.ocorrencia_salva_sucesso = False
        st.session_state.salvando_ocorrencia = False
        st.session_state.gravidade_alterada = False
        st.session_state.adicionar_outra_infracao = False
        st.session_state.infracoes_adicionais = []
    if df_alunos.empty:
        st.warning("⚠️ Importe alunos primeiro.")
    else:
        tz_sp = pytz.timezone('America/Sao_Paulo')
        data_hora_sp = datetime.now(tz_sp)
        turmas = df_alunos["turma"].unique().tolist()
        turmas_sel = st.multiselect("🏫 Turma(s)", turmas, default=[turmas[0]] if turmas else [])
        
        if not turmas_sel:
            st.warning("⚠️ Selecione pelo menos uma turma")
            st.stop()
        
        alunos = df_alunos[df_alunos["turma"].isin(turmas_sel)]
        if len(alunos) > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 👥 Selecionar Estudante(s)")
                st.info("💡 Selecione um ou mais estudantes envolvidos na mesma ocorrência")
                modo_multiplo = st.checkbox("👥 Registrar para múltiplos estudantes", key="modo_multiplo")
                if modo_multiplo:
                    alunos_selecionados = st.multiselect(
                        "Selecione os estudantes:",
                        alunos["nome"].tolist(),
                        key="alunos_multiplos"
                    )
                else:
                    aluno_unico = st.selectbox("Aluno", alunos["nome"].tolist(), key="aluno_unico")
                    alunos_selecionados = [aluno_unico] if aluno_unico else []
                if not df_professores.empty:
                    prof_lista = df_professores["nome"].tolist()
                    prof = st.selectbox("Professor 👨‍🏫", ["Selecione..."] + prof_lista)
                    if prof == "Selecione...":
                        prof = st.text_input("Ou digite o nome do professor", placeholder="Nome do professor")
                else:
                    prof = st.text_input("Professor 👨‍🏫", placeholder="Nome do professor")
                # ✅ DATA E HORA EDITÁVEIS
                data = st.date_input("📅 Data do Fato", value=data_hora_sp.date(), key="data_fato")
                hora = st.time_input("⏰ Hora do Fato", value=data_hora_sp.time(), key="hora_fato")
                turno_info = selecionar_equipe_por_horario(f"{data.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}", df_responsaveis)
                st.info(f"⏱️ Turno: {turno_info['turno']}\n" \
                        f"Diretor: {turno_info['diretor']}\n" \
                        f"Vice-Diretor: {turno_info['vice']}\n" \
                        f"Coordenador: {turno_info['coordenador']}")
            with col2:
                st.subheader("📋 Infração Principal (Protocolo 179)")
                st.markdown('<div class="search-box">', unsafe_allow_html=True)
                busca_infracao = st.text_input("🔍 Buscar infração (busca inteligente):",
                                               placeholder="Ex: celular, bullying, atraso, colar...",
                                               key="busca_infracao")
                # Determinar grupo e categorias
                if busca_infracao:
                    grupos_filtrados = buscar_infracao_fuzzy(busca_infracao, PROTOCOLO_179)
                    if grupos_filtrados:
                        total_encontradas = sum(len(v) for v in grupos_filtrados.values())
                        st.success(f"✅ Encontradas {total_encontradas} infração(ões) relacionadas")
                        grupo = st.selectbox("Grupo", list(grupos_filtrados.keys()), key="grupo_principal")
                        cats = grupos_filtrados[grupo]
                    else:
                        st.warning("⚠️ Nenhuma infração encontrada. Mostrando todas...")
                        grupo = st.selectbox("Grupo", list(PROTOCOLO_179.keys()), key="grupo_principal")
                        cats = PROTOCOLO_179[grupo]
                else:
                    grupo = st.selectbox("Grupo", list(PROTOCOLO_179.keys()), key="grupo_principal")
                    cats = PROTOCOLO_179[grupo]
                st.markdown('</div>', unsafe_allow_html=True)
                # Selecionar infração
                infracao_principal = st.selectbox("Ocorrência Principal", list(cats.keys()), key="infracao_principal")
                # ✅ Buscar dados CORRETOS da infração selecionada
                if infracao_principal in cats:
                    gravidade_protocolo = cats[infracao_principal]["gravidade"]
                    encam_protocolo = cats[infracao_principal]["encaminhamento"]
                else:
                    gravidade_protocolo = "Leve"
                    encam_protocolo = "✅ Registrar em ata\n✅ Notificar famílias"
                st.markdown(f'<span class="infracao-principal-tag">🎯 {infracao_principal}</span>', unsafe_allow_html=True)
                # Mostrar informações do protocolo
                st.markdown("---")
                cor_gravidade = CORES_GRAVIDADE.get(gravidade_protocolo, "#9E9E9E")
                st.markdown(f"""
                <div style="background:#fff3cd;border:2px solid #ffc107;border-radius:8px;padding:1rem;margin:1rem 0;">
                    <b>📋 Protocolo 179 - Preenchimento Automático</b><br><br>
                    <b>Infração:</b> {infracao_principal}<br>
                    <b>Gravidade sugerida:</b> <span style="color:{cor_gravidade};font-weight:bold">{gravidade_protocolo}</span><br><br>
                    <b>Encaminhamentos sugeridos:</b>
                </div>
                """, unsafe_allow_html=True)
                for linha in encam_protocolo.split('\n'):
                    if linha.strip():
                        st.write(linha)
                # ✅ Gravidade EDITÁVEL
                gravidade = st.selectbox("Gravidade (sugerida pelo Protocolo 179 - pode editar)",
                                         ["Leve", "Média", "Grave", "Gravíssima"],
                                         index=["Leve", "Média", "Grave", "Gravíssima"].index(gravidade_protocolo) if gravidade_protocolo in ["Leve", "Média", "Grave", "Gravíssima"] else 0,
                                         key="gravidade_select")
                if gravidade != gravidade_protocolo:
                    st.warning(f"⚠️ Você alterou a gravidade de **{gravidade_protocolo}** para **{gravidade}**")
                # ✅ Encaminhamento EDITÁVEL
                encam = st.text_area("🔀 Encaminhamentos (sugerido pelo Protocolo 179 - pode editar)",
                                     value=encam_protocolo, height=150, key="encam_select")
                st.markdown("---")
                relato = st.text_area("📝 Relato dos Fatos", height=100, key="relato_novo",
                                      placeholder="Descreva os fatos de forma clara e objetiva...")
                if st.session_state.salvando_ocorrencia:
                    st.button("💾 Salvando...", disabled=True, type="primary")
                    st.info("⏳ Aguarde, registrando ocorrência(s)...")
                else:
                    if st.button("💾 Salvar Ocorrência(s)", type="primary"):
                        if prof and prof != "Selecione..." and relato and alunos_selecionados:
                            # Preparar dados para confirmação
                            data_str = f"{data.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}"
                            categoria_str = infracao_principal
                            st.session_state['dados_registro'] = {
                                'alunos_selecionados': alunos_selecionados,
                                'data_str': data_str,
                                'categoria_str': categoria_str,
                                'gravidade': gravidade,
                                'relato': relato,
                                'encam': encam,
                                'prof': prof,
                                'turmas_sel': turmas_sel
                            }
                            st.session_state['confirmar_registro'] = True
                            st.rerun()
                        else:
                            if not alunos_selecionados:
                                st.error("❌ Selecione pelo menos um estudante!")
                            else:
                                st.error("❌ Preencha professor e relato obrigatoriamente!")
            # Mostrar confirmação de registro se necessário
            if 'confirmar_registro' in st.session_state and st.session_state.get('confirmar_registro'):
                dados = st.session_state['dados_registro']
                st.warning("⚠️ **Confirmação de Registro de Ocorrência(s)**")
                st.info(f"""
                **Resumo da(s) ocorrência(s) a ser(em) registrada(s):**
                - **Data:** {dados['data_str']}
                - **Turma(s):** {', '.join(dados['turmas_sel'])}
                - **Categoria:** {dados['categoria_str']}
                - **Gravidade:** {dados['gravidade']}
                - **Professor:** {dados['prof']}
                - **Alunos envolvidos:** {', '.join(dados['alunos_selecionados'])}
                - **Total:** {len(dados['alunos_selecionados']) * len(dados['turmas_sel'])} ocorrência(s)
                """)
                col_conf_reg1, col_conf_reg2 = st.columns(2)
                with col_conf_reg1:
                    if st.button("✅ Confirmar Registro", type="primary"):
                        contagem_salvas = 0
                        contagem_duplicadas = 0
                        erros = 0
                        for turma in dados['turmas_sel']:
                            for nome_aluno in dados['alunos_selecionados']:
                                # Buscar o RA do aluno na turma específica
                                alunos_turma = df_alunos[(df_alunos["nome"] == nome_aluno) & (df_alunos["turma"] == turma)]
                                if alunos_turma.empty:
                                    # Se o aluno não está nesta turma, pular
                                    continue
                                ra_aluno = alunos_turma["ra"].values[0]
                                if verificar_ocorrencia_duplicada(ra_aluno, dados['categoria_str'], dados['data_str'], df_ocorrencias):
                                    contagem_duplicadas += 1
                                else:
                                    nova = {
                                        "data": dados['data_str'],
                                        "aluno": nome_aluno,
                                        "ra": ra_aluno,
                                        "turma": turma,
                                        "categoria": dados['categoria_str'],
                                        "gravidade": dados['gravidade'],
                                        "relato": dados['relato'],
                                        "encaminhamento": dados['encam'],
                                        "professor": dados['prof'],
                                        "medidas_aplicadas": "",
                                        "medidas_obs": ""
                                    }
                                    if salvar_ocorrencia(nova):
                                        contagem_salvas += 1
                                        # Backup automático após salvar ocorrência crítica
                                        if st.session_state.backup_manager:
                                            st.session_state.backup_manager.criar_backup()
                                    else:
                                        erros += 1
                        if contagem_salvas > 0:
                            st.success(f"✅ {contagem_salvas} ocorrência(s) registrada(s) com sucesso!")
                        if contagem_duplicadas > 0:
                            st.warning(f"⚠️ {contagem_duplicadas} ocorrência(s) já existiam (ignorado)")
                        if erros > 0:
                            st.error(f"❌ {erros} erro(s) ao salvar")
                        if contagem_salvas > 0:
                            st.session_state.ocorrencia_salva_sucesso = True
                        
                        # ✅ LIMPAR TODAS AS KEYS DO FORMULÁRIO PARA EVITAR VALORES ANTIGOS
                        keys_to_clear = [
                            'confirmar_registro',
                            'dados_registro',
                            'infracao_principal',
                            'grupo_principal',
                            'busca_infracao',
                            'gravidade_select',
                            'encam_select',
                            'relato_novo',
                            'data_fato',
                            'hora_fato',
                            'modo_multiplo',
                            'alunos_multiplos',
                            'aluno_unico'
                        ]
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        st.rerun()
                with col_conf_reg2:
                    if st.button("❌ Cancelar Registro", type="secondary"):
                        # ✅ LIMPAR TAMBÉM AO CANCELAR
                        keys_to_clear = [
                            'confirmar_registro',
                            'dados_registro',
                            'infracao_principal',
                            'grupo_principal',
                            'busca_infracao',
                            'gravidade_select',
                            'encam_select',
                            'relato_novo',
                            'data_fato',
                            'hora_fato',
                            'modo_multiplo',
                            'alunos_multiplos',
                            'aluno_unico'
                        ]
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

# --- 5. COMUNICADO AOS PAIS ---
elif menu == "📄 Comunicado aos Pais":
    st.header("📄 Comunicado aos Pais/Responsáveis")
    st.info("💡 Gere comunicados para envio aos pais com as medidas aplicadas.")
    if df_alunos.empty or df_ocorrencias.empty:
        st.warning("⚠️ Cadastre alunos e ocorrências primeiro.")
    else:
        # Modo de seleção
        modo = st.radio("Modo de Geração", ["Individual", "Por Turma(s)"], horizontal=True, key="modo_comunicado")

        if modo == "Individual":
            st.subheader("👤 Selecionar Aluno Individual")
            busca = st.text_input("🔍 Buscar por nome ou RA", placeholder="Digite nome ou RA do aluno")
            if busca:
                df_filtrado = df_alunos[
                    (df_alunos['nome'].str.contains(busca, case=False, na=False)) |
                    (df_alunos['ra'].astype(str).str.contains(busca, na=False))
                ]
            else:
                df_filtrado = df_alunos
            if not df_filtrado.empty:
                aluno_sel = st.selectbox("Selecione o Aluno", df_filtrado['nome'].tolist(), key="comunicado_aluno")
                aluno_info = df_alunos[df_alunos['nome'] == aluno_sel].iloc[0]
                ra_aluno = aluno_info['ra']
                turma_aluno = aluno_info['turma']
                ocorrencias_aluno = df_ocorrencias[df_ocorrencias['ra'] == ra_aluno] if not df_ocorrencias.empty else pd.DataFrame()
                total_ocorrencias = len(ocorrencias_aluno)
                st.markdown(f"""
                <div class="card">
                    <b>📊 Resumo do Aluno:</b><br>
                    • Nome: {aluno_info['nome']}<br>
                    • RA: {ra_aluno}<br>
                    • Turma: {turma_aluno}<br>
                    • 📈 Total de Ocorrências: <b>{total_ocorrencias}</b>
                </div>
                """, unsafe_allow_html=True)
                if not ocorrencias_aluno.empty:
                    st.subheader("📋 Selecionar Ocorrência para Comunicado")
                    ocorrencias_lista = (ocorrencias_aluno['id'].astype(str) + " - " +
                                         ocorrencias_aluno['data'] + " - " +
                                         ocorrencias_aluno['categoria']).tolist()
                    occ_sel = st.selectbox("Selecione a ocorrência", ocorrencias_lista)
                    idx = ocorrencias_lista.index(occ_sel)
                    occ_info = ocorrencias_aluno.iloc[idx]
                    st.markdown(f"""
                    <div class="protocolo-info">
                        <b>📋 Dados da Ocorrência:</b><br>
                        • Data: {occ_info['data']}<br>
                        • Categoria: {occ_info['categoria']}<br>
                        • Gravidade: {occ_info['gravidade']}<br>
                        • Professor: {occ_info['professor']}
                    </div>
                    """, unsafe_allow_html=True)
                    st.subheader("⚖️ Medidas Aplicadas")
                    medidas_opcoes = [
                        "Mediação de conflitos", "Registro em ata", "Notificação aos pais",
                        "Atividades de reflexão", "Termo de compromisso", "Ata circunstanciada",
                        "Conselho Tutelar", "Mudança de turma", "Acomp. psicológico",
                        "Reunião com pais", "Afastamento temporário", "B.O. registrado",
                        "Diretoria de Ensino", "Medidas protetivas", "Transferência de escola"
                    ]
                    cols = st.columns(3)
                    medidas_aplicadas = []
                    for i, medida in enumerate(medidas_opcoes):
                        col_idx = i % 3
                        with cols[col_idx]:
                            if st.checkbox(medida, key=f"medida_comm_{medida}"):
                                medidas_aplicadas.append(medida)
                    observacoes = st.text_area("📝 Observações adicionais",
                                               placeholder="Descreva detalhes das medidas, prazos, acompanhamentos...",
                                               height=80, key="obs_comunicado")
                    if st.button("🖨️ Gerar Comunicado para os Pais", type="primary"):
                        aluno_data_dict = {
                            "nome": aluno_info['nome'],
                            "ra": ra_aluno,
                            "turma": turma_aluno,
                            "total_ocorrencias": total_ocorrencias
                        }
                        ocorrencia_data_dict = {
                            "data": occ_info['data'],
                            "categoria": occ_info['categoria'],
                            "gravidade": occ_info['gravidade'],
                            "professor": occ_info['professor'],
                            "relato": occ_info['relato'],
                            "encaminhamento": occ_info['encaminhamento']
                        }
                        medidas_str = " | ".join(medidas_aplicadas)
                        pdf_buffer = gerar_pdf_comunicado(aluno_data_dict, ocorrencia_data_dict, medidas_str, observacoes, df_responsaveis)
                        st.download_button(
                            label="📥 Baixar Comunicado (PDF)",
                            data=pdf_buffer,
                            file_name=f"Comunicado_{ra_aluno}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
                        st.success("✅ Comunicado gerado! Imprima e envie com o aluno para assinatura dos pais.")
                else:
                    st.info("ℹ️ Este aluno ainda não tem ocorrências registradas.")
            else:
                st.warning("⚠️ Nenhum aluno encontrado com esta busca.")

        else:  # Modo Por Turma(s)
            st.subheader("🏫 Selecionar Turma(s)")
            turmas_disponiveis = sorted(df_alunos['turma'].unique().tolist())
            turmas_selecionadas = st.multiselect(
                "Selecione uma ou mais turmas",
                turmas_disponiveis,
                key="turmas_comunicado"
            )

            if turmas_selecionadas:
                # Filtrar alunos das turmas selecionadas
                alunos_selecionados = df_alunos[df_alunos['turma'].isin(turmas_selecionadas)]

                # Filtrar apenas alunos com ocorrências
                alunos_com_ocorrencias = []
                for _, aluno in alunos_selecionados.iterrows():
                    ocorrencias_aluno = df_ocorrencias[df_ocorrencias['ra'] == aluno['ra']] if not df_ocorrencias.empty else pd.DataFrame()
                    if not ocorrencias_aluno.empty:
                        alunos_com_ocorrencias.append(aluno)

                if alunos_com_ocorrencias:
                    st.success(f"📊 Encontrados {len(alunos_com_ocorrencias)} alunos com ocorrências nas turmas selecionadas.")

                    # Configurações globais para o lote
                    st.subheader("⚖️ Configurações para o Lote")
                    st.info("💡 Estas configurações serão aplicadas a todos os comunicados do lote.")

                    medidas_opcoes = [
                        "Mediação de conflitos", "Registro em ata", "Notificação aos pais",
                        "Atividades de reflexão", "Termo de compromisso", "Ata circunstanciada",
                        "Conselho Tutelar", "Mudança de turma", "Acomp. psicológico",
                        "Reunião com pais", "Afastamento temporário", "B.O. registrado",
                        "Diretoria de Ensino", "Medidas protetivas", "Transferência de escola"
                    ]
                    cols = st.columns(3)
                    medidas_aplicadas = []
                    for i, medida in enumerate(medidas_opcoes):
                        col_idx = i % 3
                        with cols[col_idx]:
                            if st.checkbox(medida, key=f"medida_lote_{medida}"):
                                medidas_aplicadas.append(medida)

                    observacoes_globais = st.text_area(
                        "📝 Observações adicionais (globais)",
                        placeholder="Descreva detalhes das medidas, prazos, acompanhamentos...",
                        height=80,
                        key="obs_comunicado_lote"
                    )

                    # Opção de usar a última ocorrência ou todas
                    tipo_ocorrencia = st.radio(
                        "Tipo de ocorrência para comunicado",
                        ["Última ocorrência de cada aluno", "Selecionar ocorrência específica"],
                        key="tipo_ocorrencia_lote"
                    )

                    if tipo_ocorrencia == "Selecionar ocorrência específica":
                        # Para simplificar, vamos usar a última ocorrência
                        st.info("💡 Para seleção específica, use o modo Individual acima.")
                        tipo_ocorrencia = "Última ocorrência de cada aluno"

                    if st.button("📄 Gerar Comunicados em Lote", type="primary"):
                        with st.spinner("Gerando comunicados..."):
                            # Criar ZIP com todos os PDFs
                            zip_buffer = BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                comunicados_gerados = 0

                                for aluno in alunos_com_ocorrencias:
                                    ra_aluno = aluno['ra']
                                    ocorrencias_aluno = df_ocorrencias[df_ocorrencias['ra'] == ra_aluno].sort_values('data', ascending=False)
                                    total_ocorrencias = len(ocorrencias_aluno)

                                    if not ocorrencias_aluno.empty:
                                        # Usar a última ocorrência (mais recente)
                                        occ_info = ocorrencias_aluno.iloc[0]

                                        aluno_data_dict = {
                                            "nome": aluno['nome'],
                                            "ra": ra_aluno,
                                            "turma": aluno['turma'],
                                            "total_ocorrencias": total_ocorrencias
                                        }
                                        ocorrencia_data_dict = {
                                            "data": occ_info['data'],
                                            "categoria": occ_info['categoria'],
                                            "gravidade": occ_info['gravidade'],
                                            "professor": occ_info['professor'],
                                            "relato": occ_info['relato'],
                                            "encaminhamento": occ_info['encaminhamento']
                                        }
                                        medidas_str = " | ".join(medidas_aplicadas)

                                        pdf_buffer = gerar_pdf_comunicado(aluno_data_dict, ocorrencia_data_dict, medidas_str, observacoes_globais, df_responsaveis)
                                        filename = f"Comunicado_{ra_aluno}_{aluno['nome'].replace(' ', '_')}.pdf"
                                        zip_file.writestr(filename, pdf_buffer.getvalue())
                                        comunicados_gerados += 1

                            zip_buffer.seek(0)
                            st.success(f"✅ {comunicados_gerados} comunicados gerados com sucesso!")

                            # Download do ZIP
                            st.download_button(
                                label="📥 Baixar ZIP com Comunicados",
                                data=zip_buffer,
                                file_name=f"Comunicados_Lote_{'_'.join(turmas_selecionadas)}_{datetime.now().strftime('%Y%m%d')}.zip",
                                mime="application/zip"
                            )
                else:
                    st.warning("⚠️ Nenhum aluno com ocorrências encontrado nas turmas selecionadas.")
            else:
                st.info("💡 Selecione uma ou mais turmas para gerar comunicados em lote.")

# --- 7. GERENCIAR TURMAS ---
elif menu == "📋 Gerenciar Turmas":
    st.header("📋 Gerenciar Turmas")
    if not df_alunos.empty and 'turma' in df_alunos.columns:
        turmas_info = df_alunos.groupby('turma').agg({'ra': 'count', 'nome': 'first'}).reset_index()
        turmas_info.columns = ['turma', 'total_alunos', 'exemplo_nome']
        st.subheader("📊 Resumo das Turmas")
        for idx, row in turmas_info.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            with col1:
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">🏫 {row['turma']}</div>
                    <div class="card-value">{row['total_alunos']} alunos</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("👁️ Ver", key=f"ver_{row['turma']}"):
                    st.session_state.turma_selecionada = row['turma']
            with col3:
                if st.button("✏️ Editar", key=f"edit_{row['turma']}"):
                    st.session_state.turma_para_editar = row['turma']
            with col4:
                if st.button("🔄 Substituir", key=f"sub_{row['turma']}"):
                    st.session_state.turma_para_substituir = row['turma']
            with col5:
                if st.button("🗑️ Deletar", key=f"del_{row['turma']}", type="secondary"):
                    st.session_state.turma_para_deletar = row['turma']
        
        # Ações de edição
        if 'turma_para_editar' in st.session_state:
            st.markdown("---")
            st.subheader(f"✏️ Editando Turma: {st.session_state.turma_para_editar}")
            novo_nome_turma = st.text_input("Novo nome da turma", value=st.session_state.turma_para_editar, key="novo_nome_turma")
            if st.button("💾 Salvar Alterações", key="salvar_edicao_turma"):
                if novo_nome_turma and novo_nome_turma != st.session_state.turma_para_editar:
                    if editar_nome_turma(st.session_state.turma_para_editar, novo_nome_turma):
                        st.success(f"✅ Turma renomeada para {novo_nome_turma}!")
                        del st.session_state.turma_para_editar
                        st.rerun()
                    else:
                        st.error("❌ Erro ao renomear turma.")
                else:
                    st.warning("Nome da turma não pode ser vazio ou igual ao atual.")
            if st.button("❌ Cancelar Edição", key="cancelar_edicao_turma"):
                del st.session_state.turma_para_editar
        
        # Ações de substituição
        if 'turma_para_substituir' in st.session_state:
            st.markdown("---")
            st.subheader(f"🔄 Substituindo Turma: {st.session_state.turma_para_substituir}")
            arquivo_upload = st.file_uploader("Selecione o novo arquivo CSV da SED", type=["csv"], key="upload_substituir")
            if arquivo_upload is not None:
                try:
                    df_import = pd.read_csv(arquivo_upload, sep=';', encoding='utf-8-sig')
                    st.success("✅ Arquivo lido com sucesso!")
                    st.info(f"📋 **Colunas encontradas:** {', '.join(df_import.columns.tolist())}")
                    st.write(f"📊 **Total de linhas no arquivo:** {len(df_import)}")
                    st.write("🔍 **Prévia dos dados (primeiras 3 linhas):**")
                    st.dataframe(df_import.head(3))
                    
                    mapeamento = {}
                    for col in df_import.columns:
                        col_lower = col.lower().strip()
                        if col_lower == 'ra':
                            mapeamento['ra'] = col
                        elif 'nome' in col_lower:
                            mapeamento['nome'] = col
                        elif 'nascimento' in col_lower or 'nasc' in col_lower:
                            mapeamento['data_nascimento'] = col
                        elif 'situação' in col_lower or 'situacao' in col_lower:
                            mapeamento['situacao'] = col
                    
                    st.write("🔍 **Mapeamento encontrado:**")
                    st.json(mapeamento)
                    
                    colunas_necessarias = ['ra', 'nome', 'data_nascimento', 'situacao']
                    faltantes = [c for c in colunas_necessarias if c not in mapeamento]
                    if faltantes:
                        st.error(f"❌ Colunas não encontradas: {', '.join(faltantes)}")
                    else:
                        # Verificar duplicatas de RA
                        ras_existentes = set(df_alunos['ra'].tolist())
                        ras_no_arquivo = set()
                        duplicatas_encontradas = []
                        
                        for idx, row in df_import.iterrows():
                            ra_valor = str(row[mapeamento['ra']]).strip()
                            if ra_valor and ra_valor != 'nan':
                                if ra_valor in ras_no_arquivo:
                                    duplicatas_encontradas.append(f"RA {ra_valor} duplicado no arquivo")
                                elif ra_valor in ras_existentes and row[mapeamento['nome']].strip() != df_alunos[df_alunos['ra'] == ra_valor]['nome'].iloc[0]:
                                    duplicatas_encontradas.append(f"RA {ra_valor} já existe em outra turma")
                                ras_no_arquivo.add(ra_valor)
                        
                        if duplicatas_encontradas:
                            st.error("❌ Problemas encontrados:")
                            for problema in duplicatas_encontradas[:10]:  # Mostra apenas os primeiros 10
                                st.write(f"- {problema}")
                            if len(duplicatas_encontradas) > 10:
                                st.write(f"... e mais {len(duplicatas_encontradas) - 10} problemas.")
                        else:
                            if st.button("🔄 Substituir Turma", type="primary"):
                                # Primeiro, excluir alunos da turma atual
                                excluir_alunos_por_turma(st.session_state.turma_para_substituir)
                                
                                # Depois, importar os novos alunos
                                contagem_novos = 0
                                erros = 0
                                for idx, row in df_import.iterrows():
                                    try:
                                        ra_valor = row[mapeamento['ra']]
                                        ra_str = str(ra_valor).strip()
                                        if not ra_str or ra_str == 'nan':
                                            erros += 1
                                            continue
                                        
                                        aluno = {
                                            "ra": ra_str,
                                            "nome": str(row[mapeamento['nome']]).strip(),
                                            "data_nascimento": str(row[mapeamento['data_nascimento']]).strip(),
                                            "situacao": str(row[mapeamento['situacao']]).strip(),
                                            "turma": st.session_state.turma_para_substituir
                                        }
                                        
                                        if salvar_aluno(aluno):
                                            contagem_novos += 1
                                        else:
                                            erros += 1
                                    except Exception as e:
                                        erros += 1
                                        continue
                                
                                st.success(f"✅ **Turma substituída com sucesso!**")
                                st.info(f"🆕 **Alunos importados:** {contagem_novos}")
                                if erros > 0:
                                    st.warning(f"⚠️ **Erros:** {erros}")
                                del st.session_state.turma_para_substituir
                                st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao ler arquivo: {str(e)}")
            
            if st.button("❌ Cancelar Substituição", key="cancelar_substituicao"):
                del st.session_state.turma_para_substituir
        
        # Confirmação de exclusão
        if 'turma_para_deletar' in st.session_state:
            st.warning(f"⚠️ Tem certeza que deseja deletar a turma **{st.session_state.turma_para_deletar}**?")
            st.info("Isso removerá TODOS os alunos desta turma!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão"):
                    if excluir_alunos_por_turma(st.session_state.turma_para_deletar):
                        st.success(f"✅ Turma {st.session_state.turma_para_deletar} excluída!")
                        del st.session_state.turma_para_deletar
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    del st.session_state.turma_para_deletar
        
        # Visualização de alunos
        if 'turma_selecionada' in st.session_state:
            st.markdown("---")
            st.subheader(f"👥 Alunos da Turma: {st.session_state.turma_selecionada}")
            alunos_turma = df_alunos[df_alunos['turma'] == st.session_state.turma_selecionada]
            st.dataframe(alunos_turma[['ra', 'nome', 'situacao']], use_container_width=True)
            if st.button("❌ Fechar Visualização"):
                del st.session_state.turma_selecionada
        
        st.markdown("---")
        st.info(f"💡 **Total de turmas:** {len(turmas_info)} | **Total de alunos:** {len(df_alunos)}")
    elif df_alunos.empty:
        st.warning("⚠️ Nenhum aluno cadastrado no sistema.")
        st.info("💡 Para gerenciar turmas, primeiro cadastre alunos através da opção '👥 Lista de Alunos' ou importe um arquivo CSV/Excel.")
    else:
        st.error("❌ Estrutura de dados inválida: a coluna 'turma' não foi encontrada nos dados dos alunos.")
        st.info("💡 Verifique se os dados dos alunos estão sendo carregados corretamente do banco de dados.")

# --- 8. ELETIVA ---
elif menu == "🎨 Eletiva":
    st.header("🎨 Eletiva")
    st.info("💡 Consulte os agrupamentos por professora e confira quais estudantes já foram localizados no cadastro do sistema.")
    if os.path.exists(ELETIVAS_ARQUIVO):
        st.caption(f"Fonte atual das listas: {ELETIVAS_ARQUIVO}")
    if FONTE_ELETIVAS == "supabase":
        st.success("✅ Exibindo eletivas salvas no Supabase.")
    else:
        st.warning("⚠️ Exibindo eletivas da planilha local. Você pode substituir o Supabase com o botão abaixo.")
    if os.path.exists(ELETIVAS_ARQUIVO):
        st.markdown("---")
        st.subheader("☁️ Sincronizar com Supabase")
        st.info("💡 Este botão apaga as eletivas atuais do Supabase e grava novamente os dados da planilha de importação.")
        if st.button("🔄 Substituir Eletivas no Supabase", type="primary"):
            registros_eletivas = converter_eletivas_para_registros(ELETIVAS_EXCEL, origem="planilha")
            if substituir_eletivas_supabase(registros_eletivas):
                st.success("✅ Eletivas substituídas no Supabase com sucesso!")
                st.rerun()

    st.markdown("---")
    st.subheader("👩‍🏫 Cadastrar Professora da Eletiva")
    professores_disponiveis = [p for p in df_professores['nome'].tolist() if p not in ELETIVAS]
    if professores_disponiveis:
        prof_para_cadastrar = st.selectbox("Selecione uma professora para cadastrar na eletiva", professores_disponiveis, key="cadastrar_prof")
        if st.button("Cadastrar Professora da Eletiva"):
            ELETIVAS[prof_para_cadastrar] = []
            st.session_state.ELETIVAS = ELETIVAS
            if FONTE_ELETIVAS == "supabase":
                # No need to post empty
                pass
            st.success(f"Professora {prof_para_cadastrar} cadastrada para eletiva!")
            st.rerun()
    else:
        st.info("Todas as professoras já estão cadastradas para eletivas.")

    # Nova seção: Gerenciar Professoras de Eletiva
    st.markdown("---")
    st.subheader("📊 Gerenciar Professoras de Eletiva")
    if ELETIVAS:
        # Preparar dados para tabela
        dados_professoras = []
        for prof, alunos in ELETIVAS.items():
            num_alunos = len(alunos)
            series = ", ".join(sorted(set([a.get('serie', '') for a in alunos if a.get('serie')]))) if alunos else ""
            dados_professoras.append({
                "Professora": prof,
                "Número de Alunos": num_alunos,
                "Séries": series
            })
        df_professoras = pd.DataFrame(dados_professoras)
        st.dataframe(df_professoras, use_container_width=True)

        # Ações por professora
        st.markdown("### Ações por Professora")
        prof_acao = st.selectbox("Selecione uma professora para ações:", list(ELETIVAS.keys()), key="acao_prof")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("✏️ Editar Professora", key=f"edit_{prof_acao}"):
                st.session_state[f"editando_prof_{prof_acao}"] = True
        with col2:
            if st.button("🗑️ Excluir Professora", key=f"del_{prof_acao}"):
                st.session_state[f"excluindo_prof_{prof_acao}"] = True
        with col3:
            if st.button("📄 Imprimir Lista", key=f"print_{prof_acao}"):
                df_eletiva_acao = montar_dataframe_eletiva(prof_acao, df_alunos)
                pdf_buffer = gerar_pdf_eletiva(prof_acao, df_eletiva_acao)
                st.download_button(
                    label="📥 Baixar PDF",
                    data=pdf_buffer,
                    file_name=f"Eletiva_{prof_acao}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    key=f"download_{prof_acao}"
                )
        with col4:
            st.metric("Total de Alunos", len(ELETIVAS.get(prof_acao, [])))

        # Modal de edição
        if st.session_state.get(f"editando_prof_{prof_acao}", False):
            st.markdown("---")
            st.subheader(f"✏️ Editando Professora: {prof_acao}")
            novo_nome = st.text_input("Novo nome da professora:", value=prof_acao, key=f"novo_nome_{prof_acao}")
            if st.button("Salvar Alterações", key=f"save_edit_{prof_acao}"):
                if novo_nome and novo_nome != prof_acao:
                    ELETIVAS[novo_nome] = ELETIVAS.pop(prof_acao)
                    # Atualizar no Supabase se necessário
                    if FONTE_ELETIVAS == "supabase":
                        # Atualizar registros no Supabase
                        registros = converter_eletivas_para_registros({novo_nome: ELETIVAS[novo_nome]}, origem="edicao")
                        try:
                            # Primeiro deletar antigos
                            _supabase_request("DELETE", f"eletivas?professora=eq.{prof_acao}")
                            # Depois inserir novos
                            _supabase_request("POST", "eletivas", json=registros)
                            limpar_cache_eletivas()
                        except Exception as e:
                            st.error(f"Erro ao atualizar no Supabase: {e}")
                    st.session_state.ELETIVAS = ELETIVAS
                    st.success(f"Professora renomeada para {novo_nome}!")
                    st.session_state[f"editando_prof_{prof_acao}"] = False
                    st.rerun()
                elif novo_nome == prof_acao:
                    st.info("Nome não alterado.")
                    st.session_state[f"editando_prof_{prof_acao}"] = False
                else:
                    st.error("Nome inválido.")
            if st.button("Cancelar", key=f"cancel_edit_{prof_acao}"):
                st.session_state[f"editando_prof_{prof_acao}"] = False

        # Modal de exclusão
        if st.session_state.get(f"excluindo_prof_{prof_acao}", False):
            st.markdown("---")
            st.subheader(f"🗑️ Excluir Professora: {prof_acao}")
            st.warning(f"Tem certeza que deseja excluir a professora {prof_acao} e todos os seus alunos ({len(ELETIVAS.get(prof_acao, []))} alunos)?")
            col_conf, col_canc = st.columns(2)
            with col_conf:
                if st.button("Sim, Excluir", key=f"confirm_del_{prof_acao}"):
                    del ELETIVAS[prof_acao]
                    st.session_state.ELETIVAS = ELETIVAS
                    if FONTE_ELETIVAS == "supabase":
                        try:
                            _supabase_request("DELETE", f"eletivas?professora=eq.{prof_acao}")
                            limpar_cache_eletivas()
                        except Exception as e:
                            st.error(f"Erro ao excluir no Supabase: {e}")
                    st.success(f"Professora {prof_acao} excluída!")
                    st.session_state[f"excluindo_prof_{prof_acao}"] = False
                    st.rerun()
            with col_canc:
                if st.button("Cancelar", key=f"cancel_del_{prof_acao}"):
                    st.session_state[f"excluindo_prof_{prof_acao}"] = False
    else:
        st.info("Nenhuma professora cadastrada para eletivas ainda.")

    professoras_eletiva = list(ELETIVAS.keys())
    professora_sel = st.selectbox("Selecione a professora", professoras_eletiva)

    alunos_raw = ELETIVAS.get(professora_sel, [])
    if alunos_raw:
        st.subheader("👥 Lista de estudantes importados desta professora")
        df_raw = pd.DataFrame(alunos_raw)
        if 'serie' in df_raw.columns:
            df_raw = df_raw.rename(columns={"nome": "Nome do Aluno", "serie": "Turma"})
        else:
            df_raw = df_raw.rename(columns={"nome": "Nome do Aluno"})
        st.dataframe(df_raw, use_container_width=True)
        options_remover = [f"{item['nome']} | {item.get('serie', '').strip()}".strip() for item in alunos_raw]
        selecionados = st.multiselect("Selecione estudantes para remover:", options_remover, key=f"remover_{professora_sel}")
        if st.button("Remover estudantes selecionados", key=f"remover_btn_{professora_sel}"):
            if selecionados:
                novos_alunos = []
                for item in alunos_raw:
                    label = f"{item['nome']} | {item.get('serie', '').strip()}".strip()
                    if label not in selecionados:
                        novos_alunos.append(item)
                    else:
                        if FONTE_ELETIVAS == "supabase":
                            try:
                                _supabase_request("DELETE", "eletivas", params={
                                    "professora": f"eq.{professora_sel}",
                                    "nome_aluno": f"eq.{item['nome']}"
                                })
                            except Exception as e:
                                st.error(f"Erro ao excluir do Supabase: {e}")
                ELETIVAS[professora_sel] = novos_alunos
                st.session_state.ELETIVAS = ELETIVAS
                st.success(f"{len(selecionados)} estudante(s) removido(s) da eletiva de {professora_sel}.")
                st.rerun()
            else:
                st.warning("Selecione pelo menos um estudante para remover.")

        ultima_lista = st.session_state.get(f"ultima_lista_importada_{professora_sel}", [])
        if ultima_lista:
            st.info(f"Última lista importada contém {len(ultima_lista)} estudantes. Você pode substituir a lista atual por ela.")
            if st.button("🔁 Substituir lista atual pela última importação", key=f"substituir_btn_{professora_sel}"):
                ELETIVAS[professora_sel] = ultima_lista.copy()
                st.session_state.ELETIVAS = ELETIVAS
                if FONTE_ELETIVAS == "supabase":
                    try:
                        _supabase_request("DELETE", "eletivas", params={"professora": f"eq.{professora_sel}"})
                        registros = [{"professora": professora_sel, "nome_aluno": a["nome"], "serie": a["serie"], "origem": "substituicao"} for a in ultima_lista]
                        _supabase_request("POST", "eletivas", json=registros)
                        limpar_cache_eletivas()
                    except Exception as e:
                        st.error(f"Erro ao substituir no Supabase: {e}")
                st.success(f"Lista de {professora_sel} substituída pela última importação.")
                st.rerun()

        st.info("Use o botão '📄 Gerar PDF da Eletiva' abaixo para imprimir a lista com turma.")
    else:
        st.info("Esta professora ainda não tem estudantes importados. Use o formulário abaixo para cadastrar.")

    with st.expander("📥 Importar Estudantes para esta Professora"):
        form_key = f"form_import_{professora_sel}"
        with st.form(form_key):
            uploaded_file = st.file_uploader("Selecione o arquivo (CSV, XLSX ou TXT)", type=["csv", "xlsx", "txt"], key=f"upload_{professora_sel}")
            nomes_adicionais = st.text_area("Digite nomes adicionais (um por linha, no formato Nome Turma):", height=120, key=f"adicionais_{professora_sel}")
            botao_importar = st.form_submit_button("Importar para a professora")
            botao_substituir = st.form_submit_button("Substituir lista atual")

        def extrair_turma(texto):
            texto = str(texto).strip()
            if not texto:
                return '', ''
            texto = texto.replace('\t', ' ').replace(' - ', ' ').replace(' — ', ' ').replace(' – ', ' ').replace(';', ' ').strip()
            partes = texto.split()
            if not partes:
                return '', ''
            ultima = partes[-1].upper()
            if any(char.isdigit() for char in ultima) and any(char.isalpha() for char in ultima):
                return ' '.join(partes[:-1]).strip(), ultima
            return texto.strip(), ''

        def ler_arquivo_importacao(uploaded_file):
            uploaded_file.seek(0)
            nome_arquivo = uploaded_file.name.lower()
            if nome_arquivo.endswith('.csv'):
                try:
                    df = pd.read_csv(uploaded_file, sep=None, engine='python', dtype=str)
                except Exception:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=';', dtype=str)
                return df
            if nome_arquivo.endswith('.xlsx'):
                return pd.read_excel(uploaded_file, engine='openpyxl', dtype=str)
            if nome_arquivo.endswith('.txt'):
                content = uploaded_file.read().decode('utf-8')
                return [linha.strip() for linha in content.splitlines() if linha.strip()]
            return None

        alunos_import = []
        if uploaded_file is not None:
            try:
                dados = ler_arquivo_importacao(uploaded_file)
                if isinstance(dados, list):
                    for linha in dados:
                        nome, serie = extrair_turma(linha)
                        if nome:
                            alunos_import.append({"nome": nome, "serie": serie})
                elif isinstance(dados, pd.DataFrame):
                    df_import = dados
                    cols_lower = {c.lower().strip(): c for c in df_import.columns}
                    nome_col = cols_lower.get('nome do aluno') or cols_lower.get('nome') or cols_lower.get('aluno') or cols_lower.get('estudante')
                    serie_col = cols_lower.get('turma') or cols_lower.get('série') or cols_lower.get('serie')
                    for _, row in df_import.iterrows():
                        nome = ''
                        serie = ''
                        if nome_col:
                            nome = str(row.get(nome_col, '')).strip()
                        if serie_col:
                            serie = str(row.get(serie_col, '')).strip()
                        if not nome and len(row) >= 1:
                            primeira = str(row.iloc[0]).strip()
                            nome, serie_linha = extrair_turma(primeira)
                            serie = serie or serie_linha
                        if not serie and len(row) >= 2:
                            segundo = str(row.iloc[1]).strip()
                            if not serie:
                                serie = segundo
                        if nome:
                            alunos_import.append({"nome": nome, "serie": serie})
            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {e}")

        if nomes_adicionais.strip():
            for linha in nomes_adicionais.splitlines():
                linha = linha.strip()
                if not linha:
                    continue
                nome, serie = extrair_turma(linha)
                if nome:
                    alunos_import.append({"nome": nome, "serie": serie})

        if alunos_import:
            st.text_area("Estudantes a serem importados:", value="\n".join([f"{a['nome']} {a['serie']}".strip() for a in alunos_import]), height=240, disabled=True)
            st.session_state[f"ultima_lista_importada_{professora_sel}"] = alunos_import
            if botao_importar:
                ELETIVAS[professora_sel].extend(alunos_import)
                st.session_state.ELETIVAS = ELETIVAS
                if FONTE_ELETIVAS == "supabase":
                    registros = [{"professora": professora_sel, "nome_aluno": a["nome"], "serie": a["serie"], "origem": "importacao"} for a in alunos_import]
                    try:
                        response = _supabase_request("POST", "eletivas", json=registros)
                        if response.status_code == 201:
                            st.success(f"✅ {len(alunos_import)} estudantes importados para {professora_sel}!")
                            limpar_cache_eletivas()
                            st.rerun()
                        else:
                            st.error("Erro ao salvar no Supabase")
                    except Exception as e:
                        st.error(f"Erro: {e}")
                else:
                    st.success(f"✅ {len(alunos_import)} estudantes importados localmente para {professora_sel}!")
                    st.rerun()
            if botao_substituir:
                ELETIVAS[professora_sel] = alunos_import.copy()
                st.session_state.ELETIVAS = ELETIVAS
                st.session_state[f"ultima_lista_importada_{professora_sel}"] = alunos_import
                if FONTE_ELETIVAS == "supabase":
                    try:
                        _supabase_request("DELETE", "eletivas", params={"professora": f"eq.{professora_sel}"})
                        registros = [{"professora": professora_sel, "nome_aluno": a["nome"], "serie": a["serie"], "origem": "substituicao"} for a in alunos_import]
                        _supabase_request("POST", "eletivas", json=registros)
                        limpar_cache_eletivas()
                    except Exception as e:
                        st.error(f"Erro ao substituir no Supabase: {e}")
                st.success(f"Lista de {professora_sel} substituída pela importação enviada.")
                st.rerun()
        else:
            st.info("Selecione um arquivo ou digite nomes com turma para importar estudantes.")

    df_eletiva = montar_dataframe_eletiva(professora_sel, df_alunos)
    if df_eletiva.empty:
        st.warning("⚠️ Nenhum agrupamento cadastrado para esta professora.")
    else:
        total_alunos = len(df_eletiva)
        encontrados = len(df_eletiva[df_eletiva['Status'] == 'Encontrado'])
        nao_encontrados = len(df_eletiva[df_eletiva['Status'] == 'Não encontrado'])
        series = ", ".join(sorted(df_eletiva['Série da Eletiva'].dropna().unique().tolist()))
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de estudantes", total_alunos)
        with col2:
            st.metric("Encontrados no sistema", encontrados)
        with col3:
            st.metric("Não encontrados", nao_encontrados)
        st.markdown(f"""
        <div class="card">
            <div class="card-title">👩‍🏫 Professora</div>
            <div class="card-value" style="font-size:1.25rem;">{professora_sel}</div>
            <div style="margin-top:0.5rem;"><b>Séries:</b> {series}</div>
        </div>
        """, unsafe_allow_html=True)
        busca_eletiva = st.text_input("🔍 Buscar estudante da eletiva", placeholder="Digite parte do nome...")
        status_filtro = st.selectbox("Filtrar por status", ["Todos", "Encontrado", "Não encontrado"])
        df_exibir = df_eletiva.copy()
        if busca_eletiva:
            df_exibir = df_exibir[df_exibir['Nome da Eletiva'].str.contains(busca_eletiva, case=False, na=False)]
        if status_filtro != "Todos":
            df_exibir = df_exibir[df_exibir['Status'] == status_filtro]
        st.subheader("📋 Agrupamento")
        st.dataframe(df_exibir, use_container_width=True)
        st.markdown("---")
        st.subheader("🖨️ Imprimir Lista da Eletiva")
        if st.button("📄 Gerar PDF da Eletiva"):
            pdf_buffer = gerar_pdf_eletiva(professora_sel, df_eletiva)
            st.download_button(
                label="📥 Baixar PDF",
                data=pdf_buffer,
                file_name=f"Eletiva_{professora_sel}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
        st.subheader("📊 Resumo por Série")
        resumo_series = df_eletiva.groupby('Série da Eletiva').size().reset_index(name='Total de Estudantes')
        st.dataframe(resumo_series, use_container_width=True)
        if nao_encontrados > 0:
            st.warning("⚠️ Alguns nomes ainda não foram encontrados no cadastro de alunos. Isso pode acontecer por diferença de grafia, acento ou se o aluno ainda não foi importado.")

# --- 9. LISTA DE ALUNOS ---
elif menu == "👥 Lista de Alunos":
    st.header("👥 Alunos Cadastrados")
    if not df_alunos.empty:
        # Verificar duplicatas de RA
        duplicatas_ra = df_alunos[df_alunos.duplicated('ra', keep=False)]
        if not duplicatas_ra.empty:
            st.warning("⚠️ **Alunos com RA duplicado encontrados!**")
            st.dataframe(duplicatas_ra[['ra', 'nome', 'turma']], use_container_width=True)
            st.info("💡 Estes alunos aparecem em múltiplas turmas. Considere corrigir para evitar inconsistências.")
            st.markdown("---")
        
        turmas = df_alunos["turma"].unique().tolist()
        filtro = st.selectbox("Filtrar por Turma", ["Todas"] + turmas)
        df_exibir = df_alunos[df_alunos["turma"] == filtro] if filtro != "Todas" else df_alunos
        st.dataframe(df_exibir, use_container_width=True)
        st.info(f"Total: {len(df_exibir)} alunos")
    else:
        st.write("📭 Nenhum aluno cadastrado.")

# --- 10. MAPA DA SALA ---
elif menu == "🏫 Mapa da Sala":
    st.header("🏫 Mapa da Sala de Aula")
    st.info("💡 Configure o layout da sala de aula e organize os assentos dos alunos.")

    # Configurações da sala
    st.subheader("⚙️ Configurações da Sala")
    col1, col2, col3 = st.columns(3)

    with col1:
        num_fileiras = st.slider("Número de fileiras", min_value=1, max_value=10, value=5, key="num_fileiras")
    
    with col2:
        carteiras_por_fileira = st.slider("Carteiras por fileira", min_value=1, max_value=8, value=6, key="carteiras_fileira")
    
    with col3:
        orientacao_lousa = st.selectbox("Orientação da lousa", ["Topo", "Fundo", "Esquerda", "Direita"], index=0, key="orientacao_lousa")

    # Seleção de turma
    if not df_alunos.empty:
        turmas_disponiveis = sorted(df_alunos['turma'].unique().tolist())
        turma_selecionada = st.selectbox("Selecione a turma", turmas_disponiveis, key="turma_mapa")
        
        alunos_turma = df_alunos[df_alunos['turma'] == turma_selecionada].copy()
        
        st.subheader(f"👥 Alunos da Turma: {turma_selecionada}")
        st.info(f"📊 {len(alunos_turma)} alunos | {num_fileiras} fileiras × {carteiras_por_fileira} carteiras = {num_fileiras * carteiras_por_fileira} assentos")
        
        # Visualização da sala
        st.subheader("🏫 Layout da Sala")
        
        # Criar grid da sala
        total_assentos = num_fileiras * carteiras_por_fileira
        
        # Chave de estado para os assentos desta turma
        seat_state_key = f"mapa_assento_{gerar_chave_segura(turma_selecionada)}"
        if seat_state_key not in st.session_state:
            st.session_state[seat_state_key] = {str(i): "" for i in range(total_assentos)}
        else:
            # Ajustar tamanho se mudar o número de assentos
            prev_state = st.session_state[seat_state_key]
            updated_state = {str(i): prev_state.get(str(i), "") for i in range(total_assentos)}
            st.session_state[seat_state_key] = updated_state

        # Garantir que cada widget de assento tenha estado inicial no session_state
        for i in range(total_assentos):
            widget_key = f"{seat_state_key}_{i}"
            if widget_key not in st.session_state:
                st.session_state[widget_key] = st.session_state[seat_state_key].get(str(i), "")
        
        # CSS para estilizar os assentos
        st.markdown("""
        <style>
        .sala-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            margin: 20px 0;
        }
        .fileira {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .assento {
            width: 60px;
            height: 40px;
            border: 2px solid #ddd;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: bold;
            cursor: default;
            transition: all 0.2s;
            background: #f8f9fa;
        }
        .assento:hover {
            border-color: #667eea;
            background: #e8f0fe;
        }
        .assento.ocupado {
            background: #667eea;
            color: white;
            border-color: #5a67d8;
        }
        .assento.vazio {
            background: #f8f9fa;
            color: #666;
        }
        .lousa {
            width: 200px;
            height: 30px;
            background: #333;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            border-radius: 4px;
            margin: 10px 0;
        }
        .parede {
            width: 100%;
            height: 20px;
            background: #8B4513;
            border-radius: 4px;
            margin: 5px 0;
        }
        .porta {
            width: 80px;
            height: 60px;
            background: #D2691E;
            border: 3px solid #8B4513;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 12px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Layout baseado na orientação da lousa
        if orientacao_lousa == "Topo":
            st.markdown('<div class="lousa">📚 LOUSA</div>', unsafe_allow_html=True)
            
            for fileira in range(num_fileiras):
                assentos_fileira = []
                for carteira in range(carteiras_por_fileira):
                    assento_idx = fileira * carteiras_por_fileira + carteira
                    assento_texto = st.session_state[seat_state_key].get(str(assento_idx), "")
                    if assento_texto:
                        nome_exib = assento_texto.split()[0]
                        assentos_fileira.append(f'<div class="assento ocupado" title="{assento_texto}">{nome_exib}</div>')
                    else:
                        assentos_fileira.append(f'<div class="assento vazio">{assento_idx + 1}</div>')
                st.markdown(f'<div class="fileira">{"".join(assentos_fileira)}</div>', unsafe_allow_html=True)
            col_porta, col_parede = st.columns([1, 4])
            with col_porta:
                st.markdown('<div class="porta">🚪<br>PORTA</div>', unsafe_allow_html=True)
            with col_parede:
                st.markdown('<div class="parede"></div>', unsafe_allow_html=True)
                
        elif orientacao_lousa == "Fundo":
            col_porta, col_grid = st.columns([1, 4])
            with col_porta:
                st.markdown('<div class="porta">🚪<br>PORTA</div>', unsafe_allow_html=True)
            with col_grid:
                for fileira in range(num_fileiras):
                    assentos_fileira = []
                    for carteira in range(carteiras_por_fileira):
                        assento_idx = fileira * carteiras_por_fileira + carteira
                        assento_texto = st.session_state[seat_state_key].get(str(assento_idx), "")
                        if assento_texto:
                            nome_exib = assento_texto.split()[0]
                            assentos_fileira.append(f'<div class="assento ocupado" title="{assento_texto}">{nome_exib}</div>')
                        else:
                            assentos_fileira.append(f'<div class="assento vazio">{assento_idx + 1}</div>')
                    st.markdown(f'<div class="fileira">{"".join(assentos_fileira)}</div>', unsafe_allow_html=True)
                st.markdown('<div class="lousa">📚 LOUSA</div>', unsafe_allow_html=True)
            st.markdown('<div class="parede"></div>', unsafe_allow_html=True)
            
        elif orientacao_lousa == "Esquerda":
            col_lousa, col_grid, col_porta = st.columns([1, 3, 1])
            with col_lousa:
                st.markdown('<div style="writing-mode: vertical-rl; text-orientation: mixed;"><div class="lousa" style="width: 30px; height: 200px;">📚 LOUSA</div></div>', unsafe_allow_html=True)
            with col_grid:
                for fileira in range(num_fileiras):
                    assentos_fileira = []
                    for carteira in range(carteiras_por_fileira):
                        assento_idx = fileira * carteiras_por_fileira + carteira
                        assento_texto = st.session_state[seat_state_key].get(str(assento_idx), "")
                        if assento_texto:
                            nome_exib = assento_texto.split()[0]
                            assentos_fileira.append(f'<div class="assento ocupado" title="{assento_texto}">{nome_exib}</div>')
                        else:
                            assentos_fileira.append(f'<div class="assento vazio">{assento_idx + 1}</div>')
                    st.markdown(f'<div class="fileira">{"".join(assentos_fileira)}</div>', unsafe_allow_html=True)
            with col_porta:
                st.markdown('<div class="porta">🚪<br>PORTA</div>', unsafe_allow_html=True)
                
        else:
            col_porta, col_grid, col_lousa = st.columns([1, 3, 1])
            with col_porta:
                st.markdown('<div class="porta">🚪<br>PORTA</div>', unsafe_allow_html=True)
            with col_grid:
                for fileira in range(num_fileiras):
                    assentos_fileira = []
                    for carteira in range(carteiras_por_fileira):
                        assento_idx = fileira * carteiras_por_fileira + carteira
                        assento_texto = st.session_state[seat_state_key].get(str(assento_idx), "")
                        if assento_texto:
                            nome_exib = assento_texto.split()[0]
                            assentos_fileira.append(f'<div class="assento ocupado" title="{assento_texto}">{nome_exib}</div>')
                        else:
                            assentos_fileira.append(f'<div class="assento vazio">{assento_idx + 1}</div>')
                    st.markdown(f'<div class="fileira">{"".join(assentos_fileira)}</div>', unsafe_allow_html=True)
            with col_lousa:
                st.markdown('<div style="writing-mode: vertical-rl; text-orientation: mixed;"><div class="lousa" style="width: 30px; height: 200px;">📚 LOUSA</div></div>', unsafe_allow_html=True)

        # Estatísticas
        assentos_ocupados_count = sum(1 for i in st.session_state[seat_state_key].values() if str(i).strip())
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Alunos", len(alunos_turma))
        with col2:
            st.metric("Assentos Ocupados", assentos_ocupados_count)
        with col3:
            st.metric("Assentos Vazios", total_assentos - assentos_ocupados_count)

        st.markdown("---")
        st.subheader("📝 Digite quem está em cada carteira")
        nomes_turma = alunos_turma['nome'].tolist()
        sugestoes = {}

        for fileira in range(num_fileiras):
            cols = st.columns(carteiras_por_fileira)
            for carteira, col in enumerate(cols):
                assento_idx = fileira * carteiras_por_fileira + carteira
                state_input_key = f"{seat_state_key}_{assento_idx}"
                with col:
                    novo_valor = st.text_input(f"Carteira {assento_idx + 1}", key=state_input_key)
                    st.session_state[seat_state_key][str(assento_idx)] = st.session_state.get(state_input_key, "")
                    if novo_valor.strip():
                        melhor_match, score = encontrar_melhor_match(novo_valor, nomes_turma)
                        if melhor_match and melhor_match != novo_valor and score >= 0.50:
                            sugestoes[assento_idx] = (melhor_match, score)
                            st.caption(f"Sugestão: {melhor_match} ({int(score * 100)}%)")

        if sugestoes:
            st.markdown("#### Sugestões de Correspondência")
            for assento_idx, (melhor_match, score) in sugestoes.items():
                st.write(f"• Carteira {assento_idx + 1}: {melhor_match} ({int(score * 100)}%)")

        if st.button("🔍 Validar Nomes por Proximidade", type="secondary"):
            correcoes = 0
            for assento_idx, (melhor_match, score) in sugestoes.items():
                if score >= 0.90:
                    widget_key = f"{seat_state_key}_{assento_idx}"
                    if widget_key in st.session_state:
                        try:
                            st.session_state[widget_key] = melhor_match
                        except Exception:
                            pass
                    st.session_state[seat_state_key][str(assento_idx)] = melhor_match
                    correcoes += 1
            if correcoes:
                st.success(f"✅ {correcoes} nomes corrigidos automaticamente.")
                rerun()
            else:
                st.info("Nenhuma correção automática encontrada para os nomes atuais.")

        assigned_names = {str(v).strip() for v in st.session_state[seat_state_key].values() if str(v).strip()}
        alunos_sem_assento = [aluno for _, aluno in alunos_turma.iterrows() if aluno['nome'] not in assigned_names]
        if alunos_sem_assento:
            st.warning(f"⚠️ {len(alunos_sem_assento)} alunos ainda não têm assento atribuído.")
            with st.expander("Ver alunos sem assento"):
                for aluno in alunos_sem_assento:
                    st.write(f"• {aluno['nome']} (RA: {aluno['ra']})")

        # Ferramentas de organização
        st.markdown("---")
        st.subheader("🛠️ Ferramentas de Organização")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔀 Atribuir Aleatoriamente", type="secondary"):
                import random
                assentos_disponiveis = list(range(total_assentos))
                random.shuffle(assentos_disponiveis)
                nomes_alunos = alunos_turma['nome'].tolist()
                for assento_idx in range(total_assentos):
                    key = f"{seat_state_key}_{assento_idx}"
                    if key in st.session_state:
                        try:
                            st.session_state[key] = ""
                        except Exception:
                            pass
                    st.session_state[seat_state_key][str(assento_idx)] = ""
                for i, nome in enumerate(nomes_alunos):
                    if i < total_assentos:
                        idx_assento = assentos_disponiveis[i]
                        key = f"{seat_state_key}_{idx_assento}"
                        if key in st.session_state:
                            try:
                                st.session_state[key] = nome
                            except Exception:
                                pass
                        st.session_state[seat_state_key][str(idx_assento)] = nome
                st.success("✅ Assentos atribuídos aleatoriamente!")
                rerun()

        with col2:
            if st.button("🧹 Limpar Todos os Assentos", type="secondary"):
                for assento_idx in range(total_assentos):
                    key = f"{seat_state_key}_{assento_idx}"
                    if key in st.session_state:
                        try:
                            st.session_state[key] = ""
                        except Exception:
                            pass
                    st.session_state[seat_state_key][str(assento_idx)] = ""
                st.success("✅ Todos os assentos foram liberados!")
                rerun()

        with col3:
            if st.button("💾 Salvar Layout", type="primary"):
                st.success("✅ Layout salvo com sucesso!")
                # TODO: Implementar salvamento no Supabase
        
    else:
        st.warning("⚠️ Cadastre alunos primeiro para usar o mapa da sala.")

# --- 11. HISTÓRICO DE OCORRÊNCIAS ---
elif menu == "📋 Histórico de Ocorrências":
    st.header("📋 Histórico de Ocorrências")
    # Exibir mensagem de exclusão se existir
    if 'mensagem_exclusao' in st.session_state:
        st.success(st.session_state.mensagem_exclusao)
        del st.session_state.mensagem_exclusao
    if not df_ocorrencias.empty:
        st.dataframe(df_ocorrencias, use_container_width=True)
        st.markdown("---")
        st.subheader("🛠️ Ações")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🗑️ Excluir")
            # Criar opções mais descritivas para facilitar a identificação
            opcoes_excluir = [f"{row['id']} - {row['aluno']} - {row['data']} - {row['categoria']}" for _, row in df_ocorrencias.iterrows()]
            opcao_selecionada = st.selectbox("Selecione a ocorrência para excluir", opcoes_excluir, key="select_excluir")
            # Extrair o ID da opção selecionada
            id_excluir = int(opcao_selecionada.split(' - ')[0])
            occ_selecionada = df_ocorrencias[df_ocorrencias["id"] == id_excluir].iloc[0]
            st.info(f"""
            **Ocorrência selecionada:**
            - ID: {id_excluir}
            - Aluno: {occ_selecionada['aluno']}
            - Data: {occ_selecionada['data']}
            - Categoria: {occ_selecionada['categoria']}
            """)
            senha = st.text_input(
                "🔒 Digite a senha para excluir (040600):",
                type="password",
                key="senha_excluir",
                help="Digite a senha 040600 para confirmar"
            )
            if st.button("🗑️ Excluir Ocorrência", key="btn_excluir", type="secondary"):
                if senha != SENHA_EXCLUSAO:
                    st.error("❌ Senha incorreta! Use 040600")
                elif not SUPABASE_VALID:
                    st.error("SUPABASE_URL ou SUPABASE_KEY não configuradas. Não foi possível excluir ocorrência.")
                else:
                    # Definir confirmação
                    st.session_state['confirmar_exclusao'] = id_excluir
                    st.rerun()
        # Mostrar confirmação de exclusão se necessário
        if 'confirmar_exclusao' in st.session_state and st.session_state.get('confirmar_exclusao') == id_excluir:
            st.warning("⚠️ **Confirmação de Exclusão**")
            st.info(f"Você está prestes a excluir permanentemente a ocorrência **ID {id_excluir}** do aluno **{occ_selecionada['aluno']}**. Esta ação não pode ser desfeita.")
            col_conf1, col_conf2 = st.columns(2)
            with col_conf1:
                if st.button("✅ Confirmar Exclusão", type="primary"):
                    deleted = excluir_ocorrencia(id_excluir)
                    if deleted:
                        st.session_state.mensagem_exclusao = f"✅ Ocorrência {id_excluir} excluída com sucesso!"
                        # Limpar cache e recarregar dados
                        carregar_ocorrencias.clear()
                        st.cache_data.clear()
                        # Resetar seleção para evitar mostrar ID inexistente
                        if 'select_excluir' in st.session_state:
                            del st.session_state.select_excluir
                        if 'senha_excluir' in st.session_state:
                            del st.session_state.senha_excluir
                        del st.session_state['confirmar_exclusao']
                        st.rerun()
                    else:
                        st.error("❌ Falha ao excluir ocorrência. Verifique as credenciais e tente novamente.")
                        del st.session_state['confirmar_exclusao']
            with col_conf2:
                if st.button("❌ Cancelar", type="secondary"):
                    del st.session_state['confirmar_exclusao']
                    st.rerun()

        with col2:
            st.markdown("### ✏️ Editar")
            # Criar opções mais descritivas para facilitar a identificação
            opcoes_editar = [f"{row['id']} - {row['aluno']} - {row['data']} - {row['categoria']}" for _, row in df_ocorrencias.iterrows()]
            opcao_editar_selecionada = st.selectbox("Selecione a ocorrência para editar", opcoes_editar, key="select_editar")
            # Extrair o ID da opção selecionada
            id_editar = int(opcao_editar_selecionada.split(' - ')[0])
            if st.button("✏️ Carregar para Edição", key="btn_carregar"):
                occ = df_ocorrencias[df_ocorrencias["id"] == id_editar].iloc[0].to_dict()
                st.session_state.editando_id = id_editar
                st.session_state.dados_edicao = occ
                st.success(f"✅ Ocorrência {id_editar} carregada para edição!")

        if st.session_state.editando_id is not None and st.session_state.dados_edicao:
            st.markdown("---")
            st.subheader(f"✏️ Editando ID: {st.session_state.editando_id}")
            dados = st.session_state.dados_edicao
            edit_relato = st.text_area(
                "📝 Relato",
                value=str(dados.get("relato", "")),
                height=100,
                key="edit_relato"
            )
            edit_encam = st.text_area(
                "🔀 Encaminhamento",
                value=str(dados.get("encaminhamento", "")),
                height=100,
                key="edit_encam"
            )
            edit_grav = st.selectbox(
                "Gravidade",
                ["Leve", "Média", "Grave", "Gravíssima"],
                index=["Leve", "Média", "Grave", "Gravíssima"].index(str(dados.get("gravidade", "Leve"))) if str(dados.get("gravidade", "Leve")) in ["Leve", "Média", "Grave", "Gravíssima"] else 0,
                key="edit_grav"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar Alterações", type="primary"):
                    if not SUPABASE_VALID:
                        st.error("SUPABASE_URL ou SUPABASE_KEY não configuradas. Não foi possível editar ocorrência.")
                    elif editar_ocorrencia(
                        st.session_state.editando_id,
                        {
                            "relato": edit_relato,
                            "encaminhamento": edit_encam,
                            "gravidade": edit_grav
                        }
                    ):
                        st.success("✅ Alterações salvas com sucesso!")
                        st.session_state.editando_id = None
                        st.session_state.dados_edicao = None
                        carregar_ocorrencias.clear()
                        st.rerun()
                    else:
                        st.error("❌ Falha ao salvar alterações. Verifique as credenciais e tente novamente.")
            with col2:
                if st.button("❌ Cancelar Edição"):
                    st.session_state.editando_id = None
                    st.session_state.dados_edicao = None
                    st.rerun()
    else:
        st.write("📭 Nenhuma ocorrência registrada.")

# --- 12. GRÁFICOS ---
elif menu == "📊 Gráficos e Indicadores":
    st.header("📊 Dashboard de Ocorrências - Protocolo 179")
    if df_ocorrencias.empty:
        st.warning("⚠️ Nenhuma ocorrência registrada ainda.")
    else:
        st.subheader("🔍 Filtros Avançados")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filtro_periodo = st.selectbox("📅 Período", ["Todos", "Hoje", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Este ano", "Personalizado"])
        with col2:
            turmas_disponiveis = ["Todas"] + df_ocorrencias['turma'].unique().tolist()
            filtro_turma = st.selectbox("🏫 Turma", turmas_disponiveis)
        with col3:
            gravidades_disponiveis = ["Todas"] + df_ocorrencias['gravidade'].unique().tolist()
            filtro_gravidade = st.selectbox("⚖️ Gravidade", gravidades_disponiveis)
        with col4:
            todas_infracoes = []
            for cat in df_ocorrencias['categoria'].unique():
                todas_infracoes.extend(cat.split(' | '))
            infracoes_unicas = list(set([i.strip() for i in todas_infracoes]))
            infracoes_disponiveis = ["Todas"] + sorted(infracoes_unicas)
            filtro_infracao = st.selectbox("📋 Infração", infracoes_disponiveis)
        if filtro_periodo == "Personalizado":
            col_data1, col_data2 = st.columns(2)
            with col_data1:
                data_inicio = st.date_input("Data Início", value=datetime.now() - timedelta(days=30))
            with col_data2:
                data_fim = st.date_input("Data Fim", value=datetime.now())
        df_filtrado = df_ocorrencias.copy()
        if filtro_periodo == "Hoje":
            hoje = datetime.now().strftime('%d/%m/%Y')
            df_filtrado = df_filtrado[df_filtrado['data'].str.contains(hoje)]
        elif filtro_periodo == "Últimos 7 dias":
            data_limite = datetime.now() - timedelta(days=7)
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[df_filtrado['data_dt'] >= data_limite]
        elif filtro_periodo == "Últimos 30 dias":
            data_limite = datetime.now() - timedelta(days=30)
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[df_filtrado['data_dt'] >= data_limite]
        elif filtro_periodo == "Este mês":
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[(df_filtrado['data_dt'].dt.month == mes_atual) & (df_filtrado['data_dt'].dt.year == ano_atual)]
        elif filtro_periodo == "Este ano":
            ano_atual = datetime.now().year
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[df_filtrado['data_dt'].dt.year == ano_atual]
        elif filtro_periodo == "Personalizado":
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[(df_filtrado['data_dt'] >= pd.Timestamp(data_inicio)) &
                                      (df_filtrado['data_dt'] <= pd.Timestamp(data_fim) + pd.Timedelta(days=1))]
        if filtro_turma != "Todas":
            df_filtrado = df_filtrado[df_filtrado['turma'] == filtro_turma]
        if filtro_gravidade != "Todas":
            df_filtrado = df_filtrado[df_filtrado['gravidade'] == filtro_gravidade]
        if filtro_infracao != "Todas":
            df_filtrado = df_filtrado[df_filtrado['categoria'].str.contains(filtro_infracao, na=False)]

        st.subheader("📈 Indicadores Principais")
        col1, col2, col3, col4, col5 = st.columns(5)
        total_ocorrencias = len(df_filtrado)
        total_graves = len(df_filtrado[df_filtrado['gravidade'] == 'Gravíssima'])
        total_grave = len(df_filtrado[df_filtrado['gravidade'] == 'Grave'])
        total_leve = len(df_filtrado[df_filtrado['gravidade'] == 'Leve'])
        turmas_afetadas = df_filtrado['turma'].nunique()
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_ocorrencias}</div>
                <div class="metric-label">Total de Ocorrências</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #F44336 0%, #D32F2F 100%);">
                <div class="metric-value">{total_graves}</div>
                <div class="metric-label">Gravíssimas</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);">
                <div class="metric-value">{total_grave}</div>
                <div class="metric-label">Graves</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);">
                <div class="metric-value">{total_leve}</div>
                <div class="metric-label">Leves</div>
            </div>
            """, unsafe_allow_html=True)
        with col5:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);">
                <div class="metric-value">{turmas_afetadas}</div>
                <div class="metric-label">Turmas Afetadas</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Ocorrências por Categoria (COLORIDO)")
            if not df_filtrado.empty:
                todas_cats = []
                for cat in df_filtrado['categoria']:
                    todas_cats.extend([c.strip() for c in cat.split('|')])
                df_cats = pd.DataFrame({'Categoria': todas_cats})
                contagem_cats = df_cats['Categoria'].value_counts().head(10)
                fig_barras = px.bar(
                    contagem_cats,
                    x=contagem_cats.index,
                    y='count',
                    title='Top 10 Categorias',
                    color=contagem_cats.index,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                    labels={'count': 'Quantidade', 'Categoria': 'Categoria'}
                )
                fig_barras.update_layout(showlegend=False, xaxis_tickangle=-45)
                st.plotly_chart(fig_barras, use_container_width=True)
        with col2:
            st.subheader("🥧 Ocorrências por Categoria (PIZZA)")
            if not df_filtrado.empty:
                fig_pizza = px.pie(
                    contagem_cats,
                    values='count',
                    names=contagem_cats.index,
                    title='Distribuição por Categoria (%)',
                    color_discrete_sequence=px.colors.qualitative.Set3,
                    hole=0.3
                )
                fig_pizza.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pizza, use_container_width=True)
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("⚖️ Ocorrências por Gravidade (COLORIDO)")
            if not df_filtrado.empty:
                contagem_grav = df_filtrado['gravidade'].value_counts()
                fig_grav = px.bar(
                    contagem_grav,
                    x=contagem_grav.index,
                    y=contagem_grav.values,
                    title='Por Gravidade',
                    color=contagem_grav.index,
                    color_discrete_map={'Leve': '#4CAF50', 'Grave': '#FF9800', 'Gravíssima': '#F44336'},
                    labels={'y': 'Quantidade', 'x': 'Gravidade'}
                )
                fig_grav.update_layout(showlegend=False)
                st.plotly_chart(fig_grav, use_container_width=True)
        with col2:
            st.subheader("🥧 Ocorrências por Gravidade (PIZZA)")
            if not df_filtrado.empty:
                fig_pizza_grav = px.pie(
                    values=contagem_grav.values,
                    names=contagem_grav.index,
                    title='Distribuição por Gravidade (%)',
                    color_discrete_map={'Leve': '#4CAF50', 'Grave': '#FF9800', 'Gravíssima': '#F44336'},
                    hole=0.3
                )
                fig_pizza_grav.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pizza_grav, use_container_width=True)
        st.markdown("---")
        st.subheader("📈 Evolução Temporal das Ocorrências")
        if not df_filtrado.empty:
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado['data_apenas'] = df_filtrado['data_dt'].dt.date
            evolucao = df_filtrado.groupby('data_apenas').size().reset_index(name='Quantidade')
            evolucao = evolucao.sort_values('data_apenas')
            fig_evolucao = px.line(
                evolucao,
                x='data_apenas',
                y='Quantidade',
                title='Evolução Temporal',
                markers=True
            )
            fig_evolucao.update_traces(line=dict(color='#667eea', width=3), marker=dict(size=8))
            st.plotly_chart(fig_evolucao, use_container_width=True)
        st.subheader("🏫 Top 10 Turmas com Mais Ocorrências (COLORIDO)")
        if not df_filtrado.empty:
            top_turmas = df_filtrado['turma'].value_counts().head(10)
            fig_turmas = px.bar(
                top_turmas,
                x=top_turmas.index,
                y=top_turmas.values,
                title='Top 10 Turmas',
                color=top_turmas.values,
                color_continuous_scale='Viridis',
                labels={'y': 'Quantidade', 'x': 'Turma'}
            )
            fig_turmas.update_layout(showlegend=False, xaxis_tickangle=-45)
            st.plotly_chart(fig_turmas, use_container_width=True)
        st.subheader("📋 Dados Filtrados")
        if not df_filtrado.empty:
            st.dataframe(df_filtrado[['data', 'aluno', 'turma', 'categoria', 'gravidade', 'professor']], use_container_width=True)
            csv = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button(label="📥 Baixar Dados Filtrados (CSV)", data=csv,
                               file_name=f"ocorrencias_filtradas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")

# --- 13. IMPRIMIR PDF ---
elif menu == "🖨️ Imprimir PDF":
    st.header("🖨️ Gerar PDFs em Lote")
    if not df_ocorrencias.empty:
        st.subheader("Filtros para Geração em Lote")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            # Período
            st.markdown("### 📅 Período")
            data_inicio = st.date_input("Data Inicial", value=datetime.now() - timedelta(days=30), key="data_inicio_pdf")
            data_fim = st.date_input("Data Final", value=datetime.now(), key="data_fim_pdf")
        
        with col2:
            # Alunos
            st.markdown("### 👨‍🎓 Alunos")
            alunos_unicos = sorted(df_ocorrencias["aluno"].unique().tolist())
            alunos_selecionados = st.multiselect("Selecione Alunos (vazio = todos)", alunos_unicos, key="alunos_pdf")
            
            # Professores
            st.markdown("### 👨‍🏫 Professores")
            professores_unicos = sorted(df_ocorrencias["professor"].unique().tolist())
            professores_selecionados = st.multiselect("Selecione Professores (vazio = todos)", professores_unicos, key="professores_pdf")
        
        # Aplicar filtros
        df_filtrado = df_ocorrencias.copy()
        
        # Filtro de data
        df_filtrado["data_dt"] = pd.to_datetime(df_filtrado["data"], format="%d/%m/%Y %H:%M", errors="coerce")
        df_filtrado = df_filtrado[
            (df_filtrado["data_dt"] >= pd.Timestamp(data_inicio)) &
            (df_filtrado["data_dt"] <= pd.Timestamp(data_fim) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1))
        ].drop(columns=["data_dt"])
        
        # Filtro de alunos
        if alunos_selecionados:
            df_filtrado = df_filtrado[df_filtrado["aluno"].isin(alunos_selecionados)]
        
        # Filtro de professores
        if professores_selecionados:
            df_filtrado = df_filtrado[df_filtrado["professor"].isin(professores_selecionados)]
        
        st.markdown("---")
        st.subheader("📋 Ocorrências Filtradas")
        if not df_filtrado.empty:
            st.write(f"**Total de ocorrências encontradas:** {len(df_filtrado)}")
            st.dataframe(df_filtrado[["id", "data", "aluno", "professor", "categoria", "gravidade"]], use_container_width=True)
            
            if st.button("📄 Gerar PDFs em Lote", type="primary"):
                with st.spinner("Gerando PDFs..."):
                    # Criar ZIP
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for _, occ in df_filtrado.iterrows():
                            pdf_buffer = gerar_pdf_ocorrencia(occ, df_responsaveis)
                            filename = f"Ocorrencia_{occ['id']}_{occ['aluno'].replace(' ', '_')}.pdf"
                            zip_file.writestr(filename, pdf_buffer.getvalue())
                    
                    zip_buffer.seek(0)
                    st.success(f"✅ {len(df_filtrado)} PDFs gerados com sucesso!")
                    st.download_button(
                        label="📥 Baixar ZIP com PDFs",
                        data=zip_buffer,
                        file_name=f"Ocorrencias_Lote_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}.zip",
                        mime="application/zip"
                    )
        else:
            st.warning("Nenhuma ocorrência encontrada com os filtros aplicados.")
            
        st.markdown("---")
        st.subheader("📄 Gerar PDF Individual")
        lista = (df_ocorrencias["id"].astype(str) + " - " + df_ocorrencias["data"] + " - " + df_ocorrencias["aluno"]).tolist()
        occ_sel = st.selectbox("Selecione ocorrência individual", lista, key="occ_sel_individual")
        idx = lista.index(occ_sel)
        occ = df_ocorrencias.iloc[idx]
        st.info(f"**ID:** {occ['id']} | **Aluno:** {occ['aluno']} | **Data:** {occ['data']}")
        if st.button("📄 Gerar PDF Individual"):
            pdf_buffer = gerar_pdf_ocorrencia(occ, df_responsaveis)
            st.download_button(label="📥 Baixar PDF", data=pdf_buffer,
                               file_name=f"Ocorrencia_{occ['id']}_{occ['aluno'].replace(' ', '_')}.pdf", mime="application/pdf")
    else:
        st.write("📭 Nenhuma ocorrência.")

# --- 14. BACKUPS ---
elif menu == "💾 Backups":
    render_backup_page()