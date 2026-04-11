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

# ======================================================
# REPORTLAB (PDF)
# ======================================================
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# ======================================================
# IMPORTS LOCAIS
# ======================================================
from src.backup_manager import BackupManager, render_backup_page
from src.error_handler import (
    com_tratamento_erro,
    com_retry,
    com_validacao,
    ErroConexaoDB,
    ErroValidacao,
    ErroCarregamentoDados,
    ErroOperacaoDB,
    ErroArquivo,
    ErroAutenticacao,
    ErroDuplicado,
    ErroNaoEncontrado,
    ErroPermissao,
    Validadores,
    tratar_erro,
    exibir_erro,
    logger
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
)

# ======================================================
# CSS PERSONALIZADO PROFISSIONAL
# ======================================================
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

/* Sidebar */
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

/* Métricas */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

footer { visibility: hidden; }
#MainMenu { visibility: hidden; }

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

if not SUPABASE_VALID:
    st.warning(
        "⚠️ SUPABASE_URL ou SUPABASE_KEY não configuradas. "
        "As funcionalidades de banco de dados ficarão indisponíveis."
    )

# ======================================================
# DADOS DA ESCOLA
# ======================================================
ESCOLA_NOME = "E.E. Profª Eliane"
ESCOLA_SUBTITULO = "Sistema Conviva 179"
ESCOLA_ENDERECO = "R. Valter Souza Costa, 147 - Jardim Primavera, Ferraz de Vasconcelos - SP"
ESCOLA_CEP = "CEP: 08535-310"
ESCOLA_TELEFONE = "Telefone: (11) 4675-1855"
ESCOLA_EMAIL = "Email: e918623@educacao.sp.gov.br"
ESCOLA_LOGO = os.path.join("assets", "images", "eliane_dantas.png")

# ======================================================
# MENU LATERAL
# ======================================================
st.sidebar.markdown("## Menu")

menu = st.sidebar.radio(
    "",
    [
        "🏠 Início",
        "📝 Registrar Ocorrência",
        "📋 Histórico de Ocorrências",
        "📄 Comunicado aos Pais",
        "📊 Gráficos e Indicadores",
        "🖨️ Imprimir PDF",
        "👨‍🏫 Cadastrar Professores",
        "👤 Cadastrar Assinaturas",
        "🎨 Eletiva",
        "📋 Gerenciar Turmas",
        "👥 Lista de Alunos",
        "🏫 Mapa da Sala",
        "💾 Backups",
    ],
    label_visibility="collapsed",
)

# ======================================================
# ELETIVAS — ARQUIVO DE IMPORTAÇÃO
# ======================================================
ELETIVAS_ARQUIVO = r"C:\Users\Freak Work\Desktop\IMportação.xlsx"

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
    "Patricia": [],
}

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

# ======================================================
# FUNÇÕES AUXILIARES — TEXTO E NORMALIZAÇÃO
# ======================================================

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


def obter_gravidade_mais_alta(gravidades: list) -> str:
    """Retorna a gravidade mais alta da lista"""
    ordem = {"Leve": 1, "Média": 2, "Grave": 3, "Gravíssima": 4}
    if not gravidades:
        return "Leve"
    return max(gravidades, key=lambda g: ordem.get(g, 0))


def combinar_encaminhamentos(lista_encaminhamentos: list) -> str:
    """Combina encaminhamentos removendo duplicatas"""
    conjunto = []
    for texto in lista_encaminhamentos:
        for linha in texto.split("\n"):
            linha = linha.strip()
            if linha and linha not in conjunto:
                conjunto.append(linha)
    return "\n".join(conjunto)


def selecionar_turno_por_horario(data_hora_str: str) -> str:
    """Define turno com base no horário"""
    try:
        hora = datetime.strptime(data_hora_str.split()[-1], "%H:%M").time()
        if time(7, 0) <= hora < time(14, 30):
            return "Manhã"
        if time(14, 30) <= hora <= time(21, 30):
            return "Tarde"
    except Exception:
        pass
    return "Manhã"


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
    """Converte eletivas dict em lista de registros para Supabase"""
    registros = []
    for professora, alunos in eletivas_dict.items():
        for item in alunos:
            registros.append({"professora": professora, "nome_aluno": item.get("nome", ""), "serie": item.get("serie", ""), "origem": origem})
    return registros


def converter_eletivas_supabase_para_dict(df_eletivas: pd.DataFrame) -> dict:
    """Converte DataFrame do Supabase para dict de eletivas"""
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
    """Compara alunos das eletivas com alunos cadastrados no sistema"""
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


def gerar_pdf_eletiva(nome_professora: str, df_eletiva: pd.DataFrame) -> BytesIO:
    buffer = BytesIO()
    doc = _criar_documento_pdf(buffer)
    estilos = getSampleStyleSheet()
    elementos = []
    _adicionar_logo(elementos)
    elementos.append(Paragraph("LISTA DE ELETIVA", ParagraphStyle("titulo", parent=estilos["Heading1"], alignment=1, fontSize=12, textColor=colors.darkblue)))
    elementos.append(Paragraph(f"<b>Professora:</b> {nome_professora}", estilos["Normal"]))
    elementos.append(Spacer(1, 0.3*cm))
    cabecalho = [["Nome da Eletiva", "Série", "RA", "Turma", "Status"]]
    linhas = []
    for _, row in df_eletiva.iterrows():
        linhas.append([str(row.get("Nome da Eletiva", "")), str(row.get("Série da Eletiva", "")), str(row.get("RA", "")), str(row.get("Turma no Sistema", "")), str(row.get("Status", ""))])
    tabela = Table(cabecalho + linhas, colWidths=[7.5*cm, 2*cm, 2*cm, 2.5*cm, 2*cm], repeatRows=1)
    tabela.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4A90E2")), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('ALIGN', (2, 1), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTSIZE', (0, 0), (-1, -1), 8)]))
    elementos.append(tabela)
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ParagraphStyle("rodape", parent=estilos["Normal"], alignment=1, fontSize=7, textColor=colors.grey)))
    doc.build(elementos)
    buffer.seek(0)
    return buffer


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
# SESSION STATE — INICIALIZAÇÃO
# ======================================================

def _init_session_state():
    defaults = {
        "editando_id": None,
        "dados_edicao": None,
        "ocorrencia_salva_sucesso": False,
        "salvando_ocorrencia": False,
        "gravidade_alterada": False,
        "adicionar_outra_infracao": False,
        "infracoes_adicionais": [],
        "editando_prof": None,
        "professor_salvo_sucesso": False,
        "nome_professor_salvo": "",
        "cargo_professor_salvo": "",
        "editando_resp": None,
        "responsavel_salvo_sucesso": False,
        "nome_responsavel_salvo": "",
        "cargo_responsavel_salvo": "",
        "turma_para_editar": None,
        "turma_para_deletar": None,
        "turma_para_substituir": None,
        "turma_selecionada": None,
        "senha_exclusao_validada": False,
        "ELETIVAS": None,
        "FONTE_ELETIVAS": None,
        "backup_manager": None,
        "backup_realizado": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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
# PÁGINA 🏠 INÍCIO — DASHBOARD PRINCIPAL
# ======================================================

if menu == "🏠 Início":
    st.markdown(f"""
    <div class="main-header">
        <div class="school-name">{ESCOLA_NOME}</div>
        <div class="school-subtitle">{ESCOLA_SUBTITULO}</div>
        <div class="school-address">{ESCOLA_ENDERECO}</div>
        <div class="school-contact">{ESCOLA_CEP} • {ESCOLA_TELEFONE} • {ESCOLA_EMAIL}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Sistema de Gestão de Ocorrências Escolares")
    st.markdown("---")

    total_alunos = len(df_alunos) if not df_alunos.empty else 0
    total_ocorrencias = len(df_ocorrencias) if not df_ocorrencias.empty else 0
    total_professores = len(df_professores) if not df_professores.empty else 0
    gravissimas = len(df_ocorrencias[df_ocorrencias["gravidade"] == "Gravíssima"]) if not df_ocorrencias.empty and "gravidade" in df_ocorrencias.columns else 0
    media_ocorrencias = round(total_ocorrencias / total_alunos, 2) if total_alunos > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{total_alunos}</div><div class="metric-label">Alunos</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{total_ocorrencias}</div><div class="metric-label">Ocorrências</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card" style="background: linear-gradient(135deg, #F44336 0%, #D32F2F 100%);"><div class="metric-value">{gravissimas}</div><div class="metric-label">Gravíssimas</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card" style="background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);"><div class="metric-value">{total_professores}</div><div class="metric-label">Professores</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card" style="background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);"><div class="metric-value">{media_ocorrencias}</div><div class="metric-label">Ocorr./Aluno</div></div>', unsafe_allow_html=True)

    if not df_ocorrencias.empty and "gravidade" in df_ocorrencias.columns:
        st.markdown("---")
        st.markdown("### 📊 Distribuição por Gravidade")
        contagem_gravidade = df_ocorrencias["gravidade"].value_counts()
        col1, col2 = st.columns(2)
        with col1:
            fig_grav_pie = px.pie(values=contagem_gravidade.values, names=contagem_gravidade.index, title="Ocorrências por Gravidade", color=contagem_gravidade.index, color_discrete_map=CORES_GRAVIDADE, hole=0.35)
            fig_grav_pie.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_grav_pie, use_container_width=True)
        with col2:
            fig_grav_bar = px.bar(contagem_gravidade, x=contagem_gravidade.index, y=contagem_gravidade.values, title="Quantidade por Gravidade", labels={"x": "Gravidade", "y": "Quantidade"}, color=contagem_gravidade.index, color_discrete_map=CORES_GRAVIDADE)
            fig_grav_bar.update_layout(xaxis_tickangle=-20)
            st.plotly_chart(fig_grav_bar, use_container_width=True)

    if not df_ocorrencias.empty and "turma" in df_ocorrencias.columns:
        st.markdown("---")
        st.markdown("### 🏫 Top 10 Turmas com Mais Ocorrências")
        top_turmas = df_ocorrencias["turma"].value_counts().head(10)
        fig_turmas = px.bar(top_turmas, x=top_turmas.index, y=top_turmas.values, labels={"x": "Turma", "y": "Quantidade"}, color=top_turmas.index)
        fig_turmas.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig_turmas, use_container_width=True)

    if not df_ocorrencias.empty and "aluno" in df_ocorrencias.columns:
        st.markdown("---")
        st.markdown("### 🏆 Top 10 Alunos com Mais Ocorrências")
        top_alunos = df_ocorrencias["aluno"].value_counts().head(10)
        fig_alunos = px.bar(top_alunos, x=top_alunos.index, y=top_alunos.values, labels={"x": "Aluno", "y": "Quantidade"}, color=top_alunos.values, color_continuous_scale="Reds")
        fig_alunos.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig_alunos, use_container_width=True)

    st.markdown("---")
    st.info(f"📌 Fonte das eletivas: **{FONTE_ELETIVAS.upper()}** | 🗓️ Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# ======================================================
# PÁGINA 👨‍🏫 CADASTRAR PROFESSORES
# ======================================================

elif menu == "👨‍🏫 Cadastrar Professores":
    st.header("👨‍🏫 Cadastrar Professores")

    if st.session_state.professor_salvo_sucesso:
        st.markdown(f'<div class="success-box">✅ {st.session_state.cargo_professor_salvo} {st.session_state.nome_professor_salvo} cadastrado com sucesso!</div>', unsafe_allow_html=True)
        st.session_state.professor_salvo_sucesso = False
        st.session_state.nome_professor_salvo = ""
        st.session_state.cargo_professor_salvo = ""

    with st.expander("📥 Importar Professores em Massa"):
        st.info("💡 Cole uma lista de nomes (um por linha)")
        texto_professores = st.text_area("Lista de professores:", height=150, placeholder="Maria Silva\nJoão Pereira\nAna Souza")
        if st.button("📥 Importar Professores"):
            if not texto_professores.strip():
                st.error("❌ Cole ao menos um nome.")
            else:
                nomes = [n.strip() for n in texto_professores.splitlines() if n.strip()]
                inseridos = 0
                duplicados = 0
                nomes_existentes = df_professores["nome"].str.lower().tolist() if not df_professores.empty else []
                for nome in nomes:
                    if nome.lower() in nomes_existentes:
                        duplicados += 1
                        continue
                    if salvar_professor({"nome": nome, "cargo": "Professor"}):
                        inseridos += 1
                if inseridos > 0:
                    st.success(f"✅ {inseridos} professor(es) importado(s).")
                if duplicados > 0:
                    st.warning(f"⚠️ {duplicados} nome(s) já existiam.")
                if inseridos > 0:
                    st.rerun()

    st.markdown("---")

    if st.session_state.editando_prof:
        prof_edit = df_professores[df_professores["id"] == st.session_state.editando_prof].iloc[0]
        st.subheader("✏️ Editar Professor")
        nome_prof = st.text_input("Nome *", value=prof_edit.get("nome", ""), key="edit_nome_prof")
        cargo_prof = st.selectbox("Cargo", ["Professor", "Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora", "Outro"], index=["Professor", "Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora", "Outro"].index(prof_edit.get("cargo", "Professor")))
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Alterações", type="primary"):
                if not nome_prof.strip():
                    st.error("❌ Nome é obrigatório.")
                else:
                    sucesso = atualizar_professor(st.session_state.editando_prof, {"nome": nome_prof, "cargo": cargo_prof})
                    if sucesso:
                        st.success("✅ Professor atualizado.")
                        st.session_state.editando_prof = None
                        st.rerun()
        with col2:
            if st.button("❌ Cancelar"):
                st.session_state.editando_prof = None
                st.rerun()
    else:
        st.subheader("➕ Novo Professor")
        nome_prof = st.text_input("Nome *", placeholder="Ex: João da Silva", key="novo_nome_prof")
        cargo_prof = st.selectbox("Cargo", ["Professor", "Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora", "Outro"], key="novo_cargo_prof")
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
                        st.rerun()

    st.markdown("---")
    st.subheader("📋 Professores Cadastrados")
    if not df_professores.empty:
        for _, prof in df_professores.iterrows():
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
        if "confirmar_exclusao_prof" in st.session_state:
            prof_id = st.session_state.confirmar_exclusao_prof
            prof_excluir = df_professores[df_professores["id"] == prof_id].iloc[0]
            st.warning(f"⚠️ Confirma excluir o professor **{prof_excluir['nome']}**?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão", type="primary"):
                    if excluir_professor(prof_id):
                        st.success("✅ Professor excluído.")
                        del st.session_state.confirmar_exclusao_prof
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
        st.markdown(f'<div class="success-box">✅ {st.session_state.cargo_responsavel_salvo} {st.session_state.nome_responsavel_salvo} cadastrado(a) com sucesso!</div>', unsafe_allow_html=True)
        st.session_state.responsavel_salvo_sucesso = False
        st.session_state.nome_responsavel_salvo = ""
        st.session_state.cargo_responsavel_salvo = ""

    st.info("💡 Você pode cadastrar mais de um responsável para o mesmo cargo (ex: duas Vice-Diretoras).")
    st.markdown("---")

    if st.session_state.editando_resp:
        resp_edit = df_responsaveis[df_responsaveis["id"] == st.session_state.editando_resp].iloc[0]
        st.subheader("✏️ Editar Responsável")
        nome_resp = st.text_input("Nome *", value=resp_edit.get("nome", ""), key="edit_nome_resp")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Alterações", type="primary"):
                if not nome_resp.strip():
                    st.error("❌ Nome é obrigatório.")
                else:
                    sucesso = atualizar_responsavel(st.session_state.editando_resp, {"nome": nome_resp})
                    if sucesso:
                        st.success("✅ Responsável atualizado.")
                        st.session_state.editando_resp = None
                        st.rerun()
        with col2:
            if st.button("❌ Cancelar"):
                st.session_state.editando_resp = None
                st.rerun()
    else:
        st.subheader("➕ Novo Responsável")
        cargos_disponiveis = ["Diretor", "Diretora", "Vice-Diretor", "Vice-Diretora", "Coordenador", "Coordenadora"]
        cargo = st.selectbox("Cargo", cargos_disponiveis, key="novo_cargo_resp")
        nome_resp = st.text_input("Nome do Responsável *", placeholder="Ex: Maria Silva", key="novo_nome_resp")
        if st.button("💾 Cadastrar", type="primary"):
            if not nome_resp.strip():
                st.error("❌ Nome é obrigatório.")
            else:
                sucesso = salvar_responsavel({"cargo": cargo, "nome": nome_resp, "ativo": True})
                if sucesso:
                    st.session_state.responsavel_salvo_sucesso = True
                    st.session_state.nome_responsavel_salvo = nome_resp
                    st.session_state.cargo_responsavel_salvo = cargo
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
        if "confirmar_exclusao_resp" in st.session_state:
            resp_id = st.session_state.confirmar_exclusao_resp
            resp_excluir = df_responsaveis[df_responsaveis["id"] == resp_id].iloc[0]
            st.warning(f"⚠️ Confirma excluir o responsável **{resp_excluir['nome']}** ({resp_excluir['cargo']})?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão", type="primary"):
                    if excluir_responsavel(resp_id):
                        st.success("✅ Responsável excluído.")
                        del st.session_state.confirmar_exclusao_resp
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    del st.session_state.confirmar_exclusao_resp
                    st.rerun()
    else:
        st.info("📭 Nenhum responsável cadastrado.")


# ======================================================
# PÁGINA 📝 REGISTRAR OCORRÊNCIA
# ======================================================

elif menu == "📝 Registrar Ocorrência":
    st.header("📝 Nova Ocorrência")

    if st.session_state.ocorrencia_salva_sucesso:
        st.markdown('<div class="success-box">✅ Ocorrência(s) registrada(s) com sucesso!</div>', unsafe_allow_html=True)
        st.session_state.ocorrencia_salva_sucesso = False
        st.session_state.salvando_ocorrencia = False
        st.session_state.gravidade_alterada = False
        st.session_state.infracoes_adicionais = []

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

    st.markdown(f'<span class="infracao-principal-tag">🎯 {infracao_principal}</span>', unsafe_allow_html=True)

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
    gravidade = st.selectbox("Gravidade (sugerida pelo protocolo)", ["Leve", "Média", "Grave", "Gravíssima"], index=["Leve", "Média", "Grave", "Gravíssima"].index(gravidade_sugerida), key="gravidade_sel")

    if gravidade != gravidade_sugerida:
        st.session_state.gravidade_alterada = True
        st.warning(f"⚠️ Gravidade alterada de {gravidade_sugerida} para {gravidade}.")

    encam = st.text_area("🔀 Encaminhamentos", value=encaminhamento_sugerido, height=140, key="encaminhamento")
    relato = st.text_area("📝 Relato dos fatos", height=160, placeholder="Descreva os fatos de forma clara e objetiva...", key="relato")

    st.markdown("---")

    if st.button("💾 Salvar Ocorrência(s)", type="primary"):
        if not prof or not relato.strip():
            st.error("❌ Preencha professor e relato.")
        else:
            st.session_state.dados_registro = {
                "alunos": alunos_selecionados,
                "turmas": turmas_sel,
                "data": data_str,
                "categoria": infracao_principal,
                "gravidade": gravidade,
                "relato": relato,
                "encaminhamento": encam,
                "professor": prof,
            }
            st.session_state.confirmar_registro = True
            st.rerun()

    if st.session_state.get("confirmar_registro"):
        dados = st.session_state.dados_registro
        st.warning("⚠️ Confirma o registro das seguintes ocorrências?")
        st.markdown(f"""
        <div class="card">
            <b>Data:</b> {dados["data"]}<br>
            <b>Infração:</b> {dados["categoria"]}<br>
            <b>Gravidade:</b> {dados["gravidade"]}<br>
            <b>Professor:</b> {dados["professor"]}<br>
            <b>Alunos:</b> {", ".join(dados["alunos"])}<br>
            <b>Turmas:</b> {", ".join(dados["turmas"])}
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar Registro", type="primary"):
                salvas = 0
                duplicadas = 0
                for turma in dados["turmas"]:
                    for aluno in dados["alunos"]:
                        registro = df_alunos[(df_alunos["nome"] == aluno) & (df_alunos["turma"] == turma)]
                        if registro.empty:
                            continue
                        ra = registro["ra"].values[0]
                        if verificar_ocorrencia_duplicada(ra, dados["categoria"], dados["data"], df_ocorrencias):
                            duplicadas += 1
                            continue
                        nova = {
                            "data": dados["data"],
                            "aluno": aluno,
                            "ra": ra,
                            "turma": turma,
                            "categoria": dados["categoria"],
                            "gravidade": dados["gravidade"],
                            "relato": dados["relato"],
                            "encaminhamento": dados["encaminhamento"],
                            "professor": dados["professor"],
                        }
                        if salvar_ocorrencia(nova):
                            salvas += 1
                            if st.session_state.backup_manager:
                                st.session_state.backup_manager.criar_backup()
                if salvas > 0:
                    st.session_state.ocorrencia_salva_sucesso = True
                if duplicadas > 0:
                    st.warning(f"⚠️ {duplicadas} ocorrência(s) duplicada(s) ignorada(s).")
                for k in ["confirmar_registro", "dados_registro", "relato", "busca_infracao", "infracao_principal", "grupo_infracao"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
        with col2:
            if st.button("❌ Cancelar"):
                del st.session_state.confirmar_registro
                del st.session_state.dados_registro
                st.rerun()


# ======================================================
# PÁGINA 📄 COMUNICADO AOS PAIS
# ======================================================

elif menu == "📄 Comunicado aos Pais":
    st.header("📄 Comunicado aos Pais / Responsáveis")
    st.info("💡 Gere comunicados individuais ou em lote para envio aos responsáveis.")

    if df_alunos.empty or df_ocorrencias.empty:
        st.warning("⚠️ Cadastre alunos e ocorrências antes de gerar comunicados.")
        st.stop()

    modo = st.radio("Modo de geração", ["Individual", "Por Turma(s)"], horizontal=True)

    medidas_opcoes = ["Mediação de conflitos", "Registro em ata", "Notificação aos pais", "Atividades de reflexão", "Termo de compromisso", "Ata circunstanciada", "Conselho Tutelar", "Mudança de turma", "Acompanhamento psicológico", "Reunião com pais", "Afastamento temporário", "B.O. registrado", "Diretoria de Ensino", "Medidas protetivas"]

    if modo == "Individual":
        st.subheader("👤 Seleção Individual")
        busca = st.text_input("🔍 Buscar aluno por nome ou RA", placeholder="Digite nome ou RA do aluno")
        if busca:
            df_filtrado = df_alunos[df_alunos["nome"].str.contains(busca, case=False, na=False) | df_alunos["ra"].astype(str).str.contains(busca, na=False)]
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
            <b>Aluno:</b> {aluno_info['nome']}<br>
            <b>RA:</b> {ra_aluno}<br>
            <b>Turma:</b> {aluno_info['turma']}<br>
            <b>Total de ocorrências:</b> {len(ocorrencias_aluno)}
        </div>
        """, unsafe_allow_html=True)
        if ocorrencias_aluno.empty:
            st.info("ℹ️ Este aluno não possui ocorrências.")
            st.stop()
        lista_ocorrencias = (ocorrencias_aluno["id"].astype(str) + " - " + ocorrencias_aluno["data"] + " - " + ocorrencias_aluno["categoria"])
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
            aluno_data = {"nome": aluno_info["nome"], "ra": ra_aluno, "turma": aluno_info["turma"], "total_ocorrencias": len(ocorrencias_aluno)}
            ocorrencia_data = {"data": occ_info["data"], "categoria": occ_info["categoria"], "gravidade": occ_info["gravidade"], "professor": occ_info["professor"], "relato": occ_info["relato"], "encaminhamento": occ_info["encaminhamento"]}
            pdf_buffer = gerar_pdf_comunicado(aluno_data, ocorrencia_data, "\n".join(medidas_aplicadas), observacoes, df_responsaveis)
            st.download_button("📥 Baixar Comunicado (PDF)", data=pdf_buffer, file_name=f"Comunicado_{ra_aluno}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
            st.success("✅ Comunicado gerado com sucesso!")

    else:
        st.subheader("🏫 Comunicado por Turmas")
        turmas_sel = st.multiselect("Selecione as turmas", sorted(df_alunos["turma"].unique().tolist()))
        if not turmas_sel:
            st.info("ℹ️ Selecione ao menos uma turma.")
            st.stop()
        alunos_turmas = df_alunos[df_alunos["turma"].isin(turmas_sel)]
        alunos_com_ocorrencias = [aluno for _, aluno in alunos_turmas.iterrows() if not df_ocorrencias[df_ocorrencias["ra"] == aluno["ra"]].empty]
        if not alunos_com_ocorrencias:
            st.warning("⚠️ Nenhum aluno com ocorrência nas turmas selecionadas.")
            st.stop()
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
                    aluno_data = {"nome": aluno["nome"], "ra": ra, "turma": aluno["turma"], "total_ocorrencias": len(ocorrencias)}
                    ocorrencia_data = {"data": occ["data"], "categoria": occ["categoria"], "gravidade": occ["gravidade"], "professor": occ["professor"], "relato": occ["relato"], "encaminhamento": occ["encaminhamento"]}
                    pdf = gerar_pdf_comunicado(aluno_data, ocorrencia_data, "\n".join(medidas_aplicadas), observacoes, df_responsaveis)
                    nome_pdf = f"Comunicado_{ra}_{aluno['nome'].replace(' ', '_')}.pdf"
                    zip_file.writestr(nome_pdf, pdf.getvalue())
            zip_buffer.seek(0)
            st.download_button("📥 Baixar ZIP de Comunicados", data=zip_buffer, file_name=f"Comunicados_{datetime.now().strftime('%Y%m%d_%H%M')}.zip", mime="application/zip")
            st.success("✅ Comunicados em lote gerados com sucesso!")


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

    st.subheader("🗂️ Ocorrências Registradas")
    st.dataframe(df_ocorrencias, use_container_width=True)

    st.markdown("---")
    st.subheader("🛠️ Ações")
    col_excluir, col_editar = st.columns(2)

    with col_excluir:
        st.markdown("### 🗑️ Excluir Ocorrência")
        opcoes_excluir = [f"{row['id']} - {row['aluno']} - {row['data']} - {row['categoria']}" for _, row in df_ocorrencias.iterrows()]
        opcao_sel = st.selectbox("Selecione a ocorrência", opcoes_excluir, key="select_excluir")
        id_excluir = int(opcao_sel.split(" - ")[0])
        ocorrencia_sel = df_ocorrencias[df_ocorrencias["id"] == id_excluir].iloc[0]
        st.markdown(f"""
        <div class="card">
            <b>Ocorrência selecionada:</b><br>
            • ID: {id_excluir}<br>
            • Aluno: {ocorrencia_sel['aluno']}<br>
            • Data: {ocorrencia_sel['data']}<br>
            • Categoria: {ocorrencia_sel['categoria']}
        </div>
        """, unsafe_allow_html=True)
        senha = st.text_input("🔒 Digite a senha para excluir", type="password", key="senha_excluir", help="Digite a senha definida no sistema")
        if st.button("🗑️ Excluir Ocorrência", type="secondary"):
            if senha != SENHA_EXCLUSAO:
                st.error("❌ Senha incorreta.")
            else:
                st.session_state.confirmar_exclusao = id_excluir
                st.rerun()
        if st.session_state.get("confirmar_exclusao") == id_excluir:
            st.warning(f"⚠️ Confirma excluir permanentemente a ocorrência ID {id_excluir} do aluno {ocorrencia_sel['aluno']}?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Confirmar Exclusão", type="primary"):
                    sucesso = excluir_ocorrencia(id_excluir)
                    if sucesso:
                        st.session_state.mensagem_exclusao = f"✅ Ocorrência {id_excluir} excluída com sucesso!"
                        carregar_ocorrencias.clear()
                        st.cache_data.clear()
                        for k in ["confirmar_exclusao", "select_excluir", "senha_excluir"]:
                            if k in st.session_state:
                                del st.session_state[k]
                        st.rerun()
            with c2:
                if st.button("❌ Cancelar"):
                    del st.session_state.confirmar_exclusao
                    st.rerun()

    with col_editar:
        st.markdown("### ✏️ Editar Ocorrência")
        opcoes_editar = [f"{row['id']} - {row['aluno']} - {row['data']} - {row['categoria']}" for _, row in df_ocorrencias.iterrows()]
        opcao_edit = st.selectbox("Selecione a ocorrência", opcoes_editar, key="select_editar")
        id_editar = int(opcao_edit.split(" - ")[0])
        if st.button("✏️ Carregar para Edição"):
            st.session_state.editando_id = id_editar
            st.session_state.dados_edicao = df_ocorrencias[df_ocorrencias["id"] == id_editar].iloc[0].to_dict()
            st.success("✅ Ocorrência carregada para edição.")
        if st.session_state.get("editando_id") is not None and st.session_state.get("dados_edicao"):
            dados = st.session_state.dados_edicao
            st.markdown("---")
            st.subheader(f"✏️ Editando Ocorrência ID {id_editar}")
            novo_relato = st.text_area("📝 Relato", value=str(dados.get("relato", "")), height=120, key="edit_relato")
            novo_encam = st.text_area("🔀 Encaminhamentos", value=str(dados.get("encaminhamento", "")), height=120, key="edit_encam")
            nova_gravidade = st.selectbox("⚖️ Gravidade", ["Leve", "Média", "Grave", "Gravíssima"], index=["Leve", "Média", "Grave", "Gravíssima"].index(dados.get("gravidade", "Leve")), key="edit_gravidade")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Salvar Alterações", type="primary"):
                    sucesso = editar_ocorrencia(st.session_state.editando_id, {"relato": novo_relato, "encaminhamento": novo_encam, "gravidade": nova_gravidade})
                    if sucesso:
                        st.success("✅ Ocorrência atualizada com sucesso!")
                        carregar_ocorrencias.clear()
                        st.session_state.editando_id = None
                        st.session_state.dados_edicao = None
                        st.rerun()
            with c2:
                if st.button("❌ Cancelar Edição"):
                    st.session_state.editando_id = None
                    st.session_state.dados_edicao = None
                    st.rerun()


# ======================================================
# PÁGINA 📊 GRÁFICOS E INDICADORES
# ======================================================

elif menu == "📊 Gráficos e Indicadores":
    st.header("📊 Gráficos e Indicadores — Protocolo 179")

    if df_ocorrencias.empty:
        st.warning("⚠️ Nenhuma ocorrência registrada.")
        st.stop()

    st.subheader("🔍 Filtros")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filtro_periodo = st.selectbox("📅 Período", ["Todos", "Hoje", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Este ano", "Personalizado"])
    with col2:
        turmas_disp = ["Todas"] + sorted(df_ocorrencias["turma"].dropna().unique().tolist())
        filtro_turma = st.selectbox("🏫 Turma", turmas_disp)
    with col3:
        gravidades_disp = ["Todas"] + sorted(df_ocorrencias["gravidade"].dropna().unique().tolist())
        filtro_gravidade = st.selectbox("⚖️ Gravidade", gravidades_disp)
    with col4:
        categorias_unicas = sorted(set(df_ocorrencias["categoria"].dropna().tolist()))
        filtro_categoria = st.selectbox("📋 Infração", ["Todas"] + categorias_unicas)

    df_filtro = df_ocorrencias.copy()
    df_filtro["data_dt"] = pd.to_datetime(df_filtro["data"], format="%d/%m/%Y %H:%M", errors="coerce")
    agora = datetime.now()

    if filtro_periodo == "Hoje":
        hoje = agora.date()
        df_filtro = df_filtro[df_filtro["data_dt"].dt.date == hoje]
    elif filtro_periodo == "Últimos 7 dias":
        df_filtro = df_filtro[df_filtro["data_dt"] >= agora - timedelta(days=7)]
    elif filtro_periodo == "Últimos 30 dias":
        df_filtro = df_filtro[df_filtro["data_dt"] >= agora - timedelta(days=30)]
    elif filtro_periodo == "Este mês":
        df_filtro = df_filtro[(df_filtro["data_dt"].dt.month == agora.month) & (df_filtro["data_dt"].dt.year == agora.year)]
    elif filtro_periodo == "Este ano":
        df_filtro = df_filtro[df_filtro["data_dt"].dt.year == agora.year]
    elif filtro_periodo == "Personalizado":
        c1, c2 = st.columns(2)
        with c1:
            data_inicio = st.date_input("Data inicial", value=agora.date() - timedelta(days=30))
        with c2:
            data_fim = st.date_input("Data final", value=agora.date())
        df_filtro = df_filtro[(df_filtro["data_dt"] >= pd.Timestamp(data_inicio)) & (df_filtro["data_dt"] <= pd.Timestamp(data_fim) + pd.Timedelta(days=1))]

    if filtro_turma != "Todas":
        df_filtro = df_filtro[df_filtro["turma"] == filtro_turma]
    if filtro_gravidade != "Todas":
        df_filtro = df_filtro[df_filtro["gravidade"] == filtro_gravidade]
    if filtro_categoria != "Todas":
        df_filtro = df_filtro[df_filtro["categoria"] == filtro_categoria]

    st.markdown("---")
    st.subheader("📈 Indicadores")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Ocorrências", len(df_filtro))
    with col2:
        st.metric("Gravíssimas", len(df_filtro[df_filtro["gravidade"] == "Gravíssima"]))
    with col3:
        st.metric("Graves", len(df_filtro[df_filtro["gravidade"] == "Grave"]))
    with col4:
        st.metric("Turmas Afetadas", df_filtro["turma"].nunique())

    st.markdown("---")
    st.subheader("📊 Ocorrências por Categoria")

    if not df_filtro.empty:
        contagem_cat = df_filtro["categoria"].value_counts().head(10)
        col1, col2 = st.columns(2)
        with col1:
            fig_bar_cat = px.bar(contagem_cat, x=contagem_cat.index, y=contagem_cat.values, labels={"x": "Categoria", "y": "Quantidade"}, color=contagem_cat.index, title="Top 10 Categorias")
            fig_bar_cat.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig_bar_cat, use_container_width=True)
        with col2:
            fig_pie_cat = px.pie(values=contagem_cat.values, names=contagem_cat.index, title="Distribuição por Categoria (%)", hole=0.4)
            fig_pie_cat.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_pie_cat, use_container_width=True)

    st.markdown("---")
    st.subheader("⚖️ Ocorrências por Gravidade")

    contagem_grav = df_filtro["gravidade"].value_counts()
    col1, col2 = st.columns(2)
    with col1:
        fig_bar_grav = px.bar(contagem_grav, x=contagem_grav.index, y=contagem_grav.values, labels={"x": "Gravidade", "y": "Quantidade"}, color=contagem_grav.index, color_discrete_map=CORES_GRAVIDADE)
        st.plotly_chart(fig_bar_grav, use_container_width=True)
    with col2:
        fig_pie_grav = px.pie(values=contagem_grav.values, names=contagem_grav.index, title="Distribuição por Gravidade (%)", color=contagem_grav.index, color_discrete_map=CORES_GRAVIDADE, hole=0.4)
        fig_pie_grav.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_pie_grav, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 Evolução Temporal das Ocorrências")

    df_filtro["data_apenas"] = df_filtro["data_dt"].dt.date
    evolucao = df_filtro.groupby("data_apenas").size().reset_index(name="Quantidade")
    if not evolucao.empty:
        fig_line = px.line(evolucao, x="data_apenas", y="Quantidade", markers=True, title="Ocorrências por Dia")
        st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")
    st.subheader("📥 Exportar Dados Filtrados")
    csv = df_filtro.drop(columns=["data_dt"], errors="ignore").to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button("📄 Baixar CSV", data=csv, file_name=f"ocorrencias_filtradas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")


# ======================================================
# PÁGINA 📋 GERENCIAR TURMAS
# ======================================================

elif menu == "📋 Gerenciar Turmas":
    st.header("📋 Gerenciar Turmas")

    if df_alunos.empty:
        st.info("📭 Nenhuma turma cadastrada.")
        st.stop()

    st.subheader("📊 Resumo das Turmas")
    turmas_info = df_alunos.groupby("turma").agg(total_alunos=("ra", "count"), exemplo_nome=("nome", "first")).reset_index().sort_values("turma")

    for _, row in turmas_info.iterrows():
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
        with col3:
            if st.button("✏️ Editar", key=f"edit_turma_{row['turma']}"):
                st.session_state.turma_para_editar = row["turma"]
        with col4:
            if st.button("🔄 Substituir", key=f"sub_turma_{row['turma']}"):
                st.session_state.turma_para_substituir = row["turma"]
        with col5:
            if st.button("🗑️ Deletar", key=f"del_turma_{row['turma']}"):
                st.session_state.turma_para_deletar = row["turma"]

    if st.session_state.turma_selecionada:
        turma = st.session_state.turma_selecionada
        st.markdown("---")
        st.subheader(f"👥 Alunos da Turma {turma}")
        alunos_turma = df_alunos[df_alunos["turma"] == turma]
        st.dataframe(alunos_turma[["ra", "nome", "situacao"]], use_container_width=True)
        if st.button("❌ Fechar Visualização"):
            st.session_state.turma_selecionada = None
            st.rerun()

    if st.session_state.turma_para_editar:
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
                        st.success(f"✅ Turma renomeada para {novo_nome}.")
                        st.session_state.turma_para_editar = None
                        st.rerun()
        with col2:
            if st.button("❌ Cancelar"):
                st.session_state.turma_para_editar = None
                st.rerun()

    if st.session_state.turma_para_substituir:
        turma = st.session_state.turma_para_substituir
        st.markdown("---")
        st.subheader(f"🔄 Substituir Turma {turma}")
        st.info("💡 Envie o arquivo CSV da SED para substituir os alunos da turma.")
        arquivo = st.file_uploader("Arquivo CSV", type=["csv"])
        if arquivo is not None:
            try:
                df_import = pd.read_csv(arquivo, sep=";", encoding="utf-8-sig", dtype=str)
                st.success("✅ Arquivo carregado com sucesso.")
                st.dataframe(df_import.head())
                col_map = {}
                for col in df_import.columns:
                    nome_col = col.lower()
                    if nome_col == "ra":
                        col_map["ra"] = col
                    elif "nome" in nome_col:
                        col_map["nome"] = col
                    elif "situacao" in nome_col or "situação" in nome_col:
                        col_map["situacao"] = col
                faltantes = [c for c in ["ra", "nome"] if c not in col_map]
                if faltantes:
                    st.error(f"❌ Colunas obrigatórias não encontradas: {', '.join(faltantes)}")
                else:
                    if st.button("🔄 Confirmar Substituição", type="primary"):
                        excluir_alunos_por_turma(turma)
                        inseridos = 0
                        erros = 0
                        for _, row in df_import.iterrows():
                            ra = str(row[col_map["ra"]]).strip()
                            nome = str(row[col_map["nome"]]).strip()
                            situacao = str(row[col_map["situacao"]]).strip() if "situacao" in col_map else "Ativo"
                            if not ra or not nome:
                                erros += 1
                                continue
                            aluno = {"ra": ra, "nome": nome, "turma": turma, "situacao": situacao}
                            if salvar_aluno(aluno):
                                inseridos += 1
                            else:
                                erros += 1
                        st.success(f"✅ Turma substituída. {inseridos} aluno(s) importado(s).")
                        if erros > 0:
                            st.warning(f"⚠️ {erros} erro(s) durante a importação.")
                        st.session_state.turma_para_substituir = None
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao processar o arquivo: {e}")
        if st.button("❌ Cancelar Substituição"):
            st.session_state.turma_para_substituir = None
            st.rerun()

    if st.session_state.turma_para_deletar:
        turma = st.session_state.turma_para_deletar
        st.markdown("---")
        st.warning(f"⚠️ Tem certeza que deseja excluir a turma **{turma}**? Todos os alunos desta turma serão removidos.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar Exclusão", type="primary"):
                sucesso = excluir_alunos_por_turma(turma)
                if sucesso:
                    st.success(f"✅ Turma {turma} excluída com sucesso.")
                    st.session_state.turma_para_deletar = None
                    st.rerun()
        with col2:
            if st.button("❌ Cancelar"):
                st.session_state.turma_para_deletar = None
                st.rerun()


# ======================================================
# PÁGINA 🎨 ELETIVA
# ======================================================

elif menu == "🎨 Eletiva":
    st.header("🎨 Eletivas")
    st.info("💡 Consulte os estudantes por professora da eletiva, verifique quem já foi localizado no sistema e gere PDFs.")

    if FONTE_ELETIVAS == "supabase":
        st.success("✅ Eletivas carregadas do Supabase.")
    else:
        st.warning("⚠️ Eletivas carregadas da planilha Excel.")

    if os.path.exists(ELETIVAS_ARQUIVO):
        with st.expander("☁️ Sincronizar com Supabase"):
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
        dados_professoras.append({"Professora": prof, "Total de Alunos": len(alunos), "Séries": ", ".join(sorted({a.get("serie", "") for a in alunos if a.get("serie")}))})
    df_professoras = pd.DataFrame(dados_professoras)
    st.dataframe(df_professoras, use_container_width=True)

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
    st.dataframe(df_view, use_container_width=True)

    st.markdown("---")
    st.subheader("🖨️ Imprimir Lista da Eletiva")
    if st.button("📄 Gerar PDF"):
        pdf = gerar_pdf_eletiva(professora_sel, df_eletiva)
        st.download_button("📥 Baixar PDF", data=pdf, file_name=f"Eletiva_{professora_sel}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", mime="application/pdf")

    if alunos_raw:
        st.markdown("---")
        st.subheader("🗑️ Remover Estudantes da Eletiva")
        opcoes_remover = [f"{a['nome']} {a.get('serie', '')}".strip() for a in alunos_raw]
        selecionados = st.multiselect("Selecione estudantes para remover", opcoes_remover)
        if st.button("🗑️ Remover Selecionados"):
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
# PÁGINA 👥 LISTA DE ALUNOS
# ======================================================

elif menu == "👥 Lista de Alunos":
    st.header("👥 Lista de Alunos Cadastrados")

    if df_alunos.empty:
        st.info("📭 Nenhum aluno cadastrado.")
        st.stop()

    duplicatas_ra = df_alunos[df_alunos.duplicated("ra", keep=False)]
    if not duplicatas_ra.empty:
        st.warning("⚠️ Alunos com RA duplicado encontrados!")
        st.dataframe(duplicatas_ra[["ra", "nome", "turma"]], use_container_width=True)
        st.info("💡 Estes alunos aparecem em mais de uma turma. Verifique e corrija para evitar inconsistências.")
        st.markdown("---")

    turmas_disp = sorted(df_alunos["turma"].dropna().unique().tolist())
    filtro_turma = st.selectbox("🏫 Filtrar por Turma", ["Todas"] + turmas_disp)
    df_view = df_alunos if filtro_turma == "Todas" else df_alunos[df_alunos["turma"] == filtro_turma]

    st.subheader("📋 Alunos")
    colunas_exibir = [col for col in ["ra", "nome", "turma", "situacao"] if col in df_view.columns]
    st.dataframe(df_view[colunas_exibir].sort_values(["turma", "nome"]), use_container_width=True)
    st.info(f"👥 Total de alunos exibidos: {len(df_view)}")


# ======================================================
# PÁGINA 🏫 MAPA DA SALA
# ======================================================

# ======================================================
# PÁGINA 🏫 MAPA DA SALA - VERSÃO CORRIGIDA E FUNCIONAL
# ======================================================

elif menu == "🏫 Mapa da Sala":
    st.header("🏫 Mapa da Sala de Aula")
    st.info("💡 Organize os assentos da sala e distribua os alunos manualmente ou de forma automática.")

    if df_alunos.empty:
        st.warning("⚠️ Cadastre alunos antes de usar o mapa da sala.")
        st.stop()

    # --------------------------------------------------
    # CONFIGURAÇÕES DA SALA
    # --------------------------------------------------
    st.subheader("⚙️ Configurações da Sala")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_fileiras = st.slider(
            "Número de fileiras",
            min_value=1,
            max_value=10,
            value=5,
            key="num_fileiras_mapa"
        )
    
    with col2:
        carteiras_por_fileira = st.slider(
            "Carteiras por fileira",
            min_value=1,
            max_value=8,
            value=6,
            key="carteiras_fileira_mapa"
        )
    
    with col3:
        orientacao_lousa = st.selectbox(
            "Orientação da lousa",
            ["Topo", "Fundo", "Esquerda", "Direita"],
            key="orientacao_lousa_mapa"
        )

    total_assentos = num_fileiras * carteiras_por_fileira

    # --------------------------------------------------
    # SELEÇÃO DA TURMA
    # --------------------------------------------------
    st.markdown("---")
    turmas_disponiveis = sorted(df_alunos["turma"].unique().tolist())
    turma_sel = st.selectbox(
        "Selecione a Turma",
        turmas_disponiveis,
        key="turma_mapa_select"
    )

    alunos_turma = df_alunos[df_alunos["turma"] == turma_sel].copy()
    nomes_alunos = sorted(alunos_turma["nome"].tolist())
    
    st.subheader(f"👥 Alunos da Turma {turma_sel}")
    st.info(f"📊 {len(alunos_turma)} alunos | {num_fileiras} fileiras × {carteiras_por_fileira} carteiras = {total_assentos} assentos")

    # --------------------------------------------------
    # INICIALIZAR ESTADO DOS ASSENTOS
    # --------------------------------------------------
    mapa_key = f"mapa_sala_{gerar_chave_segura(turma_sel)}"
    
    # Inicializar o estado se não existir
    if mapa_key not in st.session_state:
        st.session_state[mapa_key] = {str(i): "" for i in range(total_assentos)}
    else:
        # Ajustar tamanho se a configuração mudou
        estado_anterior = st.session_state[mapa_key]
        novo_estado = {}
        for i in range(total_assentos):
            novo_estado[str(i)] = estado_anterior.get(str(i), "")
        st.session_state[mapa_key] = novo_estado

    # --------------------------------------------------
    # CSS PARA OS ASSENTOS
    # --------------------------------------------------
    st.markdown("""
    <style>
    .sala-grid {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin: 20px 0;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 12px;
    }
    .fileira-row {
        display: flex;
        gap: 8px;
        justify-content: center;
    }
    .assento-card {
        width: 70px;
        height: 50px;
        border: 2px solid #ddd;
        border-radius: 8px;
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: #5a67d8;
    }
    .assento-card.vazio {
        background: white;
        color: #666;
    }
    .lousa {
        width: 100%;
        max-width: 300px;
        height: 35px;
        background: #2d3748;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        border-radius: 6px;
        margin: 10px auto;
    }
    .sugestao-item {
        padding: 8px;
        background: #fef3c7;
        border-radius: 6px;
        margin: 4px 0;
        border-left: 4px solid #f59e0b;
    }
    </style>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # EXIBIR LAYOUT DA SALA
    # --------------------------------------------------
    st.markdown("---")
    st.subheader("🪑 Layout da Sala")

    # Mostrar lousa conforme orientação
    if orientacao_lousa in ["Topo", "Esquerda"]:
        st.markdown('<div class="lousa">📚 LOUSA</div>', unsafe_allow_html=True)

    # Container da sala
    sala_html = '<div class="sala-grid">'
    
    for fileira in range(num_fileiras):
        sala_html += '<div class="fileira-row">'
        for carteira in range(carteiras_por_fileira):
            idx = fileira * carteiras_por_fileira + carteira
            nome_no_assento = st.session_state[mapa_key].get(str(idx), "")
            
            if nome_no_assento:
                # Mostrar apenas primeiro nome para caber
                nome_exib = nome_no_assento.split()[0] if nome_no_assento else f"C{idx+1}"
                sala_html += f'<div class="assento-card ocupado" title="{nome_no_assento}">{nome_exib}</div>'
            else:
                sala_html += f'<div class="assento-card vazio">C{idx+1}</div>'
        sala_html += '</div>'
    
    sala_html += '</div>'
    st.markdown(sala_html, unsafe_allow_html=True)

    if orientacao_lousa in ["Fundo", "Direita"]:
        st.markdown('<div class="lousa">📚 LOUSA</div>', unsafe_allow_html=True)

    # --------------------------------------------------
    # ESTATÍSTICAS
    # --------------------------------------------------
    assentos_ocupados = [v for v in st.session_state[mapa_key].values() if v.strip()]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Assentos", total_assentos)
    with col2:
        st.metric("Assentos Ocupados", len(assentos_ocupados))
    with col3:
        st.metric("Assentos Vazios", total_assentos - len(assentos_ocupados))

    # --------------------------------------------------
    # ALUNOS SEM ASSENTO
    # --------------------------------------------------
    nomes_atribuidos = set(assentos_ocupados)
    alunos_sem_assento = [nome for nome in nomes_alunos if nome not in nomes_atribuidos]
    
    if alunos_sem_assento:
        st.warning(f"⚠️ {len(alunos_sem_assento)} alunos ainda não têm assento atribuído.")
        with st.expander("📋 Ver alunos sem assento"):
            for aluno in alunos_sem_assento:
                st.write(f"• {aluno}")

    # --------------------------------------------------
    # FORMULÁRIO DE EDIÇÃO DOS ASSENTOS
    # --------------------------------------------------
    st.markdown("---")
    st.subheader("📝 Editar Assentos")
    
    # Organizar em colunas para melhor visualização
    colunas_por_linha = 4
    for fileira in range(num_fileiras):
        st.markdown(f"**Fileira {fileira + 1}**")
        cols = st.columns(colunas_por_linha)
        
        for carteira in range(carteiras_por_fileira):
            col_idx = carteira % colunas_por_linha
            idx = fileira * carteiras_por_fileira + carteira
            
            with cols[col_idx]:
                # Campo de entrada com sugestão automática
                valor_atual = st.session_state[mapa_key].get(str(idx), "")
                
                # Input do usuário
                novo_valor = st.text_input(
                    f"Carteira {idx + 1}",
                    value=valor_atual,
                    key=f"input_{mapa_key}_{idx}",
                    placeholder="Digite o nome"
                )
                
                # Atualizar estado
                if novo_valor != valor_atual:
                    st.session_state[mapa_key][str(idx)] = novo_valor
                
                # Buscar sugestão por proximidade
                if novo_valor and novo_valor.strip():
                    melhor_match, score = encontrar_melhor_match(novo_valor, nomes_alunos)
                    
                    # Mostrar sugestão se encontrada com boa similaridade
                    if melhor_match and score >= 0.5 and melhor_match.lower() != novo_valor.lower():
                        st.caption(f"💡 {melhor_match} ({int(score * 100)}%)")
                        
                        # Botão para aplicar sugestão
                        if st.button("✅ Usar", key=f"apply_{mapa_key}_{idx}"):
                            st.session_state[mapa_key][str(idx)] = melhor_match
                            st.rerun()
        
        # Pular linha entre fileiras
        if fileira < num_fileiras - 1:
            st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------
    # FERRAMENTAS DE ORGANIZAÇÃO
    # --------------------------------------------------
    st.markdown("---")
    st.subheader("🛠️ Ferramentas de Organização")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔀 Atribuir Aleatoriamente", use_container_width=True, key="btn_aleatorio"):
            # Criar cópia da lista de alunos
            nomes_embaralhados = nomes_alunos.copy()
            random.shuffle(nomes_embaralhados)
            
            # Limpar todos os assentos primeiro
            for i in range(total_assentos):
                st.session_state[mapa_key][str(i)] = ""
            
            # Preencher assentos com alunos embaralhados
            for i, nome in enumerate(nomes_embaralhados):
                if i < total_assentos:
                    st.session_state[mapa_key][str(i)] = nome
            
            st.success(f"✅ {min(len(nomes_alunos), total_assentos)} alunos atribuídos aleatoriamente!")
            st.rerun()

    with col2:
        if st.button("🧹 Limpar Todos", use_container_width=True, key="btn_limpar"):
            for i in range(total_assentos):
                st.session_state[mapa_key][str(i)] = ""
            st.success("✅ Todos os assentos foram liberados!")
            st.rerun()

    with col3:
        if st.button("🔍 Corrigir Nomes", use_container_width=True, key="btn_corrigir"):
            correcoes = 0
            for i in range(total_assentos):
                nome_atual = st.session_state[mapa_key].get(str(i), "")
                if nome_atual:
                    melhor_match, score = encontrar_melhor_match(nome_atual, nomes_alunos)
                    # Só corrige se tiver alta confiança (>= 85%)
                    if melhor_match and score >= 0.85 and melhor_match != nome_atual:
                        st.session_state[mapa_key][str(i)] = melhor_match
                        correcoes += 1
            
            if correcoes > 0:
                st.success(f"✅ {correcoes} nome(s) corrigido(s) automaticamente!")
            else:
                st.info("ℹ️ Nenhum nome precisou de correção.")
            st.rerun()

    with col4:
        if st.button("💾 Salvar Layout", use_container_width=True, type="primary", key="btn_salvar"):
            # Aqui você pode implementar o salvamento no Supabase
            st.success("✅ Layout salvo com sucesso!")
            st.info("💡 O layout foi salvo na sessão atual. Para salvar permanentemente, implemente a integração com o banco de dados.")

    # --------------------------------------------------
    # VISUALIZAÇÃO DE ALUNOS NA TURMA
    # --------------------------------------------------
    st.markdown("---")
    with st.expander("📋 Ver todos os alunos da turma"):
        st.dataframe(
            alunos_turma[["nome", "ra", "situacao"]].sort_values("nome"),
            use_container_width=True
        )

    # --------------------------------------------------
    # LEGENDA
    # --------------------------------------------------
    st.markdown("---")
    st.caption("""
    **Legenda:**
    - 🟣 **Assento ocupado** - Aluno atribuído
    - ⬜ **Assento vazio** - Disponível para atribuição
    - 💡 **Sugestão** - Clique em "Usar" para aplicar a correção sugerida
    """)

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
    df_pdf = df_pdf[(df_pdf["data_dt"] >= pd.Timestamp(data_inicio)) & (df_pdf["data_dt"] <= pd.Timestamp(data_fim) + pd.Timedelta(days=1))]
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
    st.dataframe(df_pdf[["id", "data", "aluno", "turma", "categoria", "gravidade"]], use_container_width=True)

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
        st.download_button("📥 Baixar ZIP com PDFs", data=zip_buffer, file_name=f"Ocorrencias_{datetime.now().strftime('%Y%m%d_%H%M')}.zip", mime="application/zip")
        st.success("✅ PDFs gerados com sucesso!")

    st.markdown("---")
    st.subheader("📄 Gerar PDF Individual")
    lista_ind = (df_ocorrencias["id"].astype(str) + " - " + df_ocorrencias["aluno"] + " - " + df_ocorrencias["data"])
    opcao_ind = st.selectbox("Selecione a ocorrência", lista_ind.tolist())
    id_ind = int(opcao_ind.split(" - ")[0])
    occ_ind = df_ocorrencias[df_ocorrencias["id"] == id_ind].iloc[0]
    st.markdown(f"""
    <div class="card">
        <b>ID:</b> {occ_ind['id']}<br>
        <b>Aluno:</b> {occ_ind['aluno']}<br>
        <b>Data:</b> {occ_ind['data']}<br>
        <b>Categoria:</b> {occ_ind['categoria']}
    </div>
    """, unsafe_allow_html=True)
    if st.button("📄 Gerar PDF Individual"):
        pdf = gerar_pdf_ocorrencia(occ_ind.to_dict(), df_responsaveis)
        st.download_button("📥 Baixar PDF", data=pdf, file_name=f"Ocorrencia_{occ_ind['id']}.pdf", mime="application/pdf")


# ======================================================
# PÁGINA 💾 BACKUPS
# ======================================================

elif menu == "💾 Backups":
    render_backup_page()