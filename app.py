# ============================================================================
# SISTEMA CONVIVA 179 - GESTÃO DE OCORRÊNCIAS ESCOLARES
# Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI
# Versão: 7.0 FINAL COMPLETA
# ============================================================================

# ============================================================================
# IMPORTAÇÃO DE BIBLIOTECAS
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import io
import base64
import os
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import plotly.express as px
import plotly.graph_objects as go
from fuzzywuzzy import process
import pytz
import time
from typing import Optional, Dict, List, Any

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ============================================================================

st.set_page_config(
    page_title="Sistema Conviva 179",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/Fr34k1981/SistemaConviva',
        'Report a bug': 'https://github.com/Fr34k1981/SistemaConviva/issues',
        'About': "# Sistema Conviva 179\nVersão 7.0.0\nDesenvolvido para SEDUC/SP"
    }
)

# ============================================================================
# CONFIGURAÇÃO DO SUPABASE (VIA REQUESTS API)
# ============================================================================

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Credenciais vazias.")
except Exception as e:
    st.error("⚠️ Credenciais do Supabase não encontradas no arquivo secrets.toml. Configure-as para continuar.")
    st.stop()

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# ============================================================================
# DADOS COMPLETOS DA ESCOLA
# ============================================================================

ESCOLA_NOME = "Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI"
ESCOLA_SUBTITULO = "🌟 Escola dos Sonhos"
ESCOLA_ENDERECO = "R. Valter Souza Costa, 147 - Jardim Primavera, Ferraz de Vasconcelos - SP"
ESCOLA_CEP = "CEP: 08535-310"
ESCOLA_TELEFONE = "Telefone: (11) 4675-1855"
ESCOLA_EMAIL = "Email: e918623@educacao.sp.gov.br"
ESCOLA_LOGO = "eliane_dantas.png"
SENHA_EXCLUSAO = "040600"

# ============================================================================
# DICIONÁRIOS DO PROTOCOLO 179 - CATEGORIAS E GRAVIDADES
# ============================================================================

CATEGORIAS_OCORRENCIAS = {
    "🔴 Violência Física": {
        "Agressão Física": "Gravíssima",
        "Agressão com Arma": "Gravíssima",
        "Agressão entre Estudantes": "Grave",
        "Agressão a Servidor": "Gravíssima",
        "Bullying Físico": "Grave",
        "Briga com Lesão": "Gravíssima"
    },
    "🟠 Violência Verbal/Psicológica": {
        "Ameaça": "Grave",
        "Agressão Verbal": "Média",
        "Bullying Verbal": "Grave",
        "Discriminação": "Gravíssima",
        "Racismo": "Gravíssima",
        "Homofobia": "Gravíssima",
        "Transfobia": "Gravíssima",
        "Gordofobia": "Gravíssima",
        "Xenofobia": "Gravíssima",
        "Religioso": "Gravíssima",
        "Apologia ao Nazismo": "Gravíssima"
    },
    "🟡 Violência Sexual": {
        "Assédio Sexual": "Gravíssima",
        "Importunação Sexual": "Gravíssima",
        "Estupro": "Gravíssima",
        "Atos Libidinosos": "Gravíssima",
        "Abuso Sexual": "Gravíssima",
        "Exploração Sexual": "Gravíssima"
    },
    "🟢 Armas e Segurança": {
        "Posse de Arma de Fogo / Simulacro": "Gravíssima",
        "Posse de Arma Branca": "Gravíssima",
        "Posse de Arma de Brinquedo": "Leve",
        "Ameaça de Ataque Ativo": "Gravíssima",
        "Ataque Ativo Concretizado": "Gravíssima",
        "Invasão": "Grave",
        "Ocupação de Unidade Escolar": "Leve",
        "Roubo": "Grave",
        "Furto": "Leve",
        "Dano ao Patrimônio / Vandalismo": "Leve"
    },
    "💊 Drogas e Substâncias": {
        "Posse de Celular / Dispositivo Eletrônico": "Leve",
        "Consumo de Álcool e Tabaco": "Leve",
        "Consumo de Cigarro Eletrônico": "Leve",
        "Consumo de Substâncias Ilícitas": "Grave",
        "Comercialização de Álcool e Tabaco": "Grave",
        "Envolvimento com Tráfico de Drogas": "Gravíssima"
    },
    "📚 Infrequência e Evasão": {
        "Ausência não justificada / Cabular aula": "Leve",
        "Evasão Escolar / Infrequência": "Média",
        "Saída não autorizada": "Média",
        "Chegar atrasado": "Leve"
    },
    "💔 Saúde Mental": {
        "Sinais de Automutilação": "Gravíssima",
        "Sinais de Isolamento Social": "Grave",
        "Sinais de Alterações Emocionais": "Grave",
        "Tentativa de Suicídio": "Gravíssima",
        "Suicídio Concretizado": "Gravíssima",
        "Mal Súbito": "Média",
        "Óbito": "Gravíssima"
    },
    "🌐 Crimes Cibernéticos": {
        "Crimes Cibernéticos": "Grave",
        "Fake News / Disseminação de Informações Falsas": "Grave",
        "Cyberbullying": "Grave",
        "Sexting": "Gravíssima",
        "Pornografia Infantil": "Gravíssima",
        "Grooming": "Gravíssima"
    },
    "👨‍👩‍👧‍👦 Família e Vulnerabilidade": {
        "Violência Doméstica / Maus Tratos": "Gravíssima",
        "Vulnerabilidade Familiar / Negligência": "Gravíssima",
        "Alerta de Desaparecimento": "Gravíssima",
        "Sequestro": "Gravíssima",
        "Homicídio / Homicídio Tentado": "Gravíssima",
        "Feminicídio": "Gravíssima",
        "Incitamento a Atos Infracionais": "Grave"
    },
    "📋 Infrações Administrativas e Disciplinares": {
        "Atos Obscenos / Atos Libidinosos": "Leve",
        "Uso Inadequado de Dispositivos Eletrônicos": "Leve",
        "Copiar atividades / Colar em avaliações": "Leve",
        "Falsificar assinatura de responsáveis": "Média",
        "Indisciplina": "Leve",
        "Outros": "Leve"
    },
    "⚠️ Infrações Acadêmicas e de Pontualidade": {
        "Acidentes e Eventos Inesperados": "Grave",
        "Entrega de atividades fora do prazo": "Leve",
        "Desrespeito às normas escolares": "Média",
        "Recusa em realizar atividades": "Média"
    }
}

CORES_CATEGORIAS = {
    "🔴 Violência Física": "#D32F2F",
    "🟠 Violência Verbal/Psicológica": "#F57C00",
    "🟡 Violência Sexual": "#C2185B",
    "🟢 Armas e Segurança": "#388E3C",
    "💊 Drogas e Substâncias": "#7B1FA2",
    "📚 Infrequência e Evasão": "#FFA726",
    "💔 Saúde Mental": "#5C6BC0",
    "🌐 Crimes Cibernéticos": "#00BCD4",
    "👨‍👩‍👧‍👦 Família e Vulnerabilidade": "#EC407A",
    "📋 Infrações Administrativas e Disciplinares": "#9E9E9E",
    "⚠️ Infrações Acadêmicas e de Pontualidade": "#795548"
}

CORES_GRAVIDADE = {
    "Gravíssima": "#D32F2F",
    "Grave": "#F57C00",
    "Média": "#FFB300",
    "Leve": "#4CAF50"
}

FLUXO_ACOES = {
    "Agressão Física": "⚠️ Registrar B.O. se grave. Acionar Conselho Tutelar.",
    "Racismo": "⚖️ CRIME INAFIANÇÁVEL. Registrar B.O. obrigatório.",
    "Homofobia": "⚖️ CRIME (equiparado ao racismo). Registrar B.O.",
    "Transfobia": "⚖️ CRIME (equiparado ao racismo). Registrar B.O.",
    "Assédio Sexual": "🚨 CRIME. NÃO fazer mediação. Registrar B.O.",
    "Importunação Sexual / Estupro": "🚨 CRIME GRAVÍSSIMO. Registrar B.O. imediatamente.",
    "Posse de Arma de Fogo / Simulacro": "🚨 EMERGÊNCIA. Acionar PM (190).",
    "Ameaça de Ataque Ativo": "🚨 EMERGÊNCIA. Acionar PM (190) e Direção.",
    "Tentativa de Suicídio": "🚨 SAÚDE. Acionar SAMU (192) e Família.",
    "Sinais de Automutilação": "💚 SAÚDE MENTAL. Acionar Psicólogo e Família.",
    "Envolvimento com Tráfico de Drogas": "⚖️ CRIME. Registrar B.O. e Conselho Tutelar.",
    "Violência Doméstica / Maus Tratos": "🛡️ PROTEÇÃO. Acionar Conselho Tutelar e CRAS/CREAS.",
    "Vulnerabilidade Familiar / Negligência": "🤝 APOIO. Acionar Conselho Tutelar e CRAS.",
    "Feminicídio": "⚖️ CRIME HEDIONDO. Registrar B.O. e DDM.",
    "Homicídio / Homicídio Tentado": "⚖️ CRIME HEDIONDO. Registrar B.O."
}

ENCAMINHAMENTOS_POR_GRAVIDADE = {
    "Leve": [
        "Orientação ao Estudante",
        "Comunicação aos Pais/Responsáveis",
        "Registro em Ata de Ocorrência"
    ],
    "Média": [
        "Orientação ao Estudante",
        "Comunicação aos Pais/Responsáveis",
        "Encaminhamento à Coordenação",
        "Registro em Ata de Ocorrência"
    ],
    "Grave": [
        "Orientação ao Estudante",
        "Comunicação aos Pais/Responsáveis",
        "Encaminhamento à Coordenação",
        "Encaminhamento à Direção",
        "Conselho Tutelar",
        "Registro em Ata de Ocorrência"
    ],
    "Gravíssima": [
        "Orientação ao Estudante",
        "Comunicação aos Pais/Responsáveis",
        "Encaminhamento à Coordenação",
        "Encaminhamento à Direção",
        "Conselho Tutelar",
        "Boletim de Ocorrência",
        "Rede de Saúde (UBS/CAPS)",
        "Registro em Ata de Ocorrência"
    ]
}

# ============================================================================
# CSS PERSONALIZADO PARA ESTILIZAÇÃO
# ============================================================================

st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}
.school-name {
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}
.school-subtitle {
    font-size: 1.2rem;
    font-style: italic;
    opacity: 0.9;
}
.school-address {
    font-size: 0.9rem;
    margin-top: 1rem;
    opacity: 0.8;
}
.school-contact {
    font-size: 0.85rem;
    margin-top: 0.5rem;
    opacity: 0.9;
}
.card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}
.card-title {
    font-weight: bold;
    color: #333;
}
.card-value {
    font-size: 1.5rem;
    color: #667eea;
}
.success-box {
    background: #d4edda;
    border: 2px solid #28a745;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    text-align: center;
    font-weight: bold;
    color: #155724;
}
.alert-critical {
    background: #fee;
    border-left: 5px solid #e74c3c;
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
}
.alert-warning {
    background: #fff3cd;
    border-left: 5px solid #f39c12;
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
}
.alert-success {
    background: #d4edda;
    border-left: 5px solid #27ae60;
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
}
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 10px;
    color: white;
    text-align: center;
}
.metric-value {
    font-size: 2.5rem;
    font-weight: bold;
}
.metric-label {
    font-size: 1rem;
    opacity: 0.9;
}
.search-box {
    background: #f0f0f0;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}
.photo-container {
    text-align: center;
    margin: 1rem 0;
}
.student-photo, .professor-photo {
    max-width: 120px;
    max-height: 120px;
    border-radius: 10px;
    border: 3px solid #667eea;
    object-fit: cover;
}
.encam-container {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #667eea;
    margin: 1rem 0;
}
.sidebar-menu {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE - GERENCIAMENTO DE ESTADO
# ============================================================================

if 'editando_id' not in st.session_state:
    st.session_state.editando_id = None
if 'dados_edicao' not in st.session_state:
    st.session_state.dados_edicao = None
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = "Home"
if 'ocorrencia_salva_sucesso' not in st.session_state:
    st.session_state.ocorrencia_salva_sucesso = False
if 'salvando_ocorrencia' not in st.session_state:
    st.session_state.salvando_ocorrencia = False
if 'gravidade_alterada' not in st.session_state:
    st.session_state.gravidade_alterada = False
if 'adicionar_outra_infracao' not in st.session_state:
    st.session_state.adicionar_outra_infracao = False
if 'infracoes_adicionais' not in st.session_state:
    st.session_state.infracoes_adicionais = []
if 'turma_selecionada' not in st.session_state:
    st.session_state.turma_selecionada = None
if 'turmas_selecionadas' not in st.session_state:
    st.session_state.turmas_selecionadas = []
if 'modo_multiplas_turmas' not in st.session_state:
    st.session_state.modo_multiplas_turmas = False
if 'editando_prof' not in st.session_state:
    st.session_state.editando_prof = None
if 'editando_resp' not in st.session_state:
    st.session_state.editando_resp = None

# ============================================================================
# FUNÇÕES DE BANCO DE DADOS (SUPABASE VIA REQUESTS)
# ============================================================================

@st.cache_data(ttl=60)
def carregar_alunos():
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/alunos?select=*&order=nome.asc",
            headers=HEADERS
        )
        response.raise_for_status()
        df = pd.DataFrame(response.json())
        if not df.empty:
            df = df.sort_values('nome').reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar alunos: {str(e)}")
        return pd.DataFrame(columns=['ra', 'nome', 'data_nascimento', 'situacao', 'turma', 'genero', 'foto_url'])

@st.cache_data(ttl=60)
def carregar_professores():
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/professores?select=*&order=nome.asc",
            headers=HEADERS
        )
        response.raise_for_status()
        df = pd.DataFrame(response.json())
        if not df.empty:
            df = df.sort_values('nome').reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar professores: {str(e)}")
        return pd.DataFrame(columns=['nome', 'email', 'cargo', 'foto_url'])

@st.cache_data(ttl=60)
def carregar_responsaveis():
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/responsaveis?select=*&ativo=eq.true&order=cargo.asc",
            headers=HEADERS
        )
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Erro ao carregar responsáveis: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def carregar_ocorrencias():
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/ocorrencias?select=*&order=id.desc",
            headers=HEADERS
        )
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Erro ao carregar ocorrências: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def carregar_turmas():
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/turmas?select=*&order=nome.asc",
            headers=HEADERS
        )
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Erro ao carregar turmas: {str(e)}")
        return pd.DataFrame(columns=['nome', 'ano', 'periodo'])

def salvar_aluno(aluno_dict):
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/alunos",
            json=aluno_dict,
            headers=HEADERS
        )
        if response.status_code in [200, 201]:
            carregar_alunos.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao salvar aluno: {str(e)}")
        return False

def salvar_professor(professor_dict):
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/professores",
            json=professor_dict,
            headers=HEADERS
        )
        if response.status_code in [200, 201]:
            carregar_professores.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao salvar professor: {str(e)}")
        return False

def salvar_responsavel(responsavel_dict):
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/responsaveis",
            json=responsavel_dict,
            headers=HEADERS
        )
        if response.status_code in [200, 201]:
            carregar_responsaveis.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao salvar responsável: {str(e)}")
        return False

def salvar_turma(turma_dict):
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/turmas",
            json=turma_dict,
            headers=HEADERS
        )
        if response.status_code in [200, 201]:
            carregar_turmas.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao salvar turma: {str(e)}")
        return False

def salvar_ocorrencia(ocorrencia_dict):
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/ocorrencias",
            json=ocorrencia_dict,
            headers=HEADERS
        )
        if response.status_code in [200, 201]:
            carregar_ocorrencias.clear()
            return True, "Ocorrência salva com sucesso!"
        else:
            return False, f"Erro ao salvar: {response.text}"
    except Exception as e:
        return False, f"Erro ao salvar: {str(e)}"

def atualizar_ocorrencia(id_ocorrencia, ocorrencia_dict):
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}",
            json=ocorrencia_dict,
            headers=HEADERS
        )
        if response.status_code in [200, 204]:
            carregar_ocorrencias.clear()
            return True, "Ocorrência atualizada com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        return False, f"Erro ao atualizar: {str(e)}"

def excluir_ocorrencia(id_ocorrencia):
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}",
            headers=HEADERS
        )
        if response.status_code in [200, 204]:
            carregar_ocorrencias.clear()
            return True, "Ocorrência excluída com sucesso!"
        else:
            return False, f"Erro ao excluir: {response.text}"
    except Exception as e:
        return False, f"Erro ao excluir: {str(e)}"

def atualizar_aluno(ra, dados):
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra}",
            json=dados,
            headers=HEADERS
        )
        if response.status_code in [200, 204]:
            carregar_alunos.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar aluno: {str(e)}")
        return False

def excluir_alunos_por_turma(turma):
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/alunos?turma=eq.{turma}",
            headers=HEADERS
        )
        if response.status_code in [200, 204]:
            carregar_alunos.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao excluir turma: {str(e)}")
        return False

def excluir_professor(id_prof):
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}",
            headers=HEADERS
        )
        if response.status_code in [200, 204]:
            carregar_professores.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao excluir professor: {str(e)}")
        return False

def excluir_responsavel(id_resp):
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}",
            headers=HEADERS
        )
        if response.status_code in [200, 204]:
            carregar_responsaveis.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao excluir responsável: {str(e)}")
        return False

def atualizar_responsavel(id_resp, dados):
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}",
            json=dados,
            headers=HEADERS
        )
        if response.status_code in [200, 204]:
            carregar_responsaveis.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar responsável: {str(e)}")
        return False

def excluir_turma(id_turma):
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/turmas?id=eq.{id_turma}",
            headers=HEADERS
        )
        if response.status_code in [200, 204]:
            carregar_turmas.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao excluir turma: {str(e)}")
        return False

def verificar_ocorrencia_duplicada(ra, categoria, data, df_ocorrencias):
    if df_ocorrencias.empty:
        return False
    
    duplicadas = df_ocorrencias[
        (df_ocorrencias['ra'] == ra) &
        (df_ocorrencias['categoria'] == categoria) &
        (df_ocorrencias['data'] == data)
    ]
    
    return len(duplicadas) > 0


# ============================================================================
# FUNÇÕES DE UPLOAD DE FOTOS (SUPABASE STORAGE)
# ============================================================================

def upload_foto_supabase(file, folder, filename):
    try:
        file_bytes = file.getvalue()
        
        response = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/fotos/{folder}/{filename}",
            data=file_bytes,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": file.type
            }
        )
        
        if response.status_code in [200, 201]:
            url_publica = f"{SUPABASE_URL}/storage/v1/object/public/fotos/{folder}/{filename}"
            return url_publica, "Foto enviada com sucesso!"
        else:
            return None, f"Erro ao enviar foto: {response.text}"
    except Exception as e:
        return None, f"Erro ao enviar foto: {str(e)}"

def atualizar_foto_aluno(ra, foto_url):
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra}",
            json={"foto_url": foto_url},
            headers=HEADERS
        )
        if response.status_code in [200, 204]:
            carregar_alunos.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar foto do aluno: {str(e)}")
        return False

def atualizar_foto_professor(nome, foto_url):
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/professores?nome=eq.{nome}",
            json={"foto_url": foto_url},
            headers=HEADERS
        )
        if response.status_code in [200, 204]:
            carregar_professores.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar foto do professor: {str(e)}")
        return False


# ============================================================================
# FUNÇÕES DE GERAÇÃO DE PDF
# ============================================================================

def gerar_pdf_ocorrencia(ocorrencia, df_responsaveis=None):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=2*cm,
        bottomMargin=1*cm
    )
    
    elementos = []
    estilos = getSampleStyleSheet()
    
    estilos.add(ParagraphStyle(
        'Titulo',
        parent=estilos['Heading1'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=0.5*cm
    ))
    
    estilos.add(ParagraphStyle(
        'Secao',
        parent=estilos['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=0.3*cm
    ))
    
    estilos.add(ParagraphStyle(
        'Texto',
        parent=estilos['Normal'],
        fontSize=9,
        alignment=TA_JUSTIFY,
        spaceAfter=0.2*cm
    ))
    
    estilos.add(ParagraphStyle(
        'Assinatura',
        parent=estilos['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        spaceAfter=0.5*cm
    ))
    
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4.5*cm)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 0.2*cm))
    except:
        pass
    
    def formatar_texto(texto):
        if texto:
            return texto.replace('<br>', '<br/>').replace('\n', '<br/>')
        return ""
    
    elementos.append(Paragraph("📋 REGISTRO DE OCORRÊNCIA - PROTOCOLO 179", estilos['Titulo']))
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph("<b>ID:</b> " + str(ocorrencia.get('id', 'N/A')), estilos['Texto']))
    elementos.append(Paragraph("<b>Data:</b> " + str(ocorrencia.get('data', 'N/A')), estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>ESTUDANTE:</b>", estilos['Secao']))
    elementos.append(Paragraph("<b>Nome:</b> " + str(ocorrencia.get('aluno', 'N/A')), estilos['Texto']))
    elementos.append(Paragraph("<b>RA:</b> " + str(ocorrencia.get('ra', 'N/A')), estilos['Texto']))
    elementos.append(Paragraph("<b>Turma:</b> " + str(ocorrencia.get('turma', 'N/A')), estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>OCORRÊNCIA:</b>", estilos['Secao']))
    elementos.append(Paragraph("<b>Categoria:</b> " + str(ocorrencia.get('categoria', 'N/A')), estilos['Texto']))
    
    gravidade = ocorrencia.get('gravidade', 'N/A')
    cor_gravidade = CORES_GRAVIDADE.get(gravidade, '#9E9E9E')
    elementos.append(Paragraph(
        f"<b>Gravidade:</b> <font color='{cor_gravidade}'><b>{gravidade}</b></font>",
        estilos['Texto']
    ))
    
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>Relato:</b>", estilos['Secao']))
    relato_formatado = formatar_texto(ocorrencia.get('relato', ''))
    elementos.append(Paragraph(relato_formatado, estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>Encaminhamentos:</b>", estilos['Secao']))
    encaminhamentos = ocorrencia.get('encaminhamentos', [])
    if isinstance(encaminhamentos, list):
        for enc in encaminhamentos:
            elementos.append(Paragraph(f"• {enc}", estilos['Texto']))
    else:
        elementos.append(Paragraph(formatar_texto(str(encaminhamentos)), estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph("<b>ASSINATURAS:</b>", estilos['Secao']))
    elementos.append(Spacer(1, 0.3*cm))
    
    cargos_fixos = ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)"]
    
    if df_responsaveis is not None and not df_responsaveis.empty:
        for cargo in cargos_fixos:
            responsavel = df_responsaveis[df_responsaveis['cargo'] == cargo]
            if not responsavel.empty and responsavel.iloc[0].get('nome'):
                nome_resp = responsavel.iloc[0].get('nome', '')
                elementos.append(Paragraph(f"<b>{cargo}:</b> {nome_resp}", estilos['Texto']))
            else:
                elementos.append(Paragraph(f"<b>{cargo}:</b> _________________________________", estilos['Texto']))
            elementos.append(Spacer(1, 0.2*cm))
    else:
        for cargo in cargos_fixos:
            elementos.append(Paragraph(f"<b>{cargo}:</b> _________________________________", estilos['Texto']))
            elementos.append(Spacer(1, 0.2*cm))
    
    if ocorrencia.get('professor'):
        elementos.append(Paragraph(f"<b>Professor Responsável:</b> {ocorrencia.get('professor')}", estilos['Texto']))
    
    elementos.append(Spacer(1, 0.5*cm))
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer


def gerar_pdf_comunicado(ocorrencia, df_responsaveis=None):
    """Gera PDF de comunicado aos pais."""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=2*cm,
        bottomMargin=1*cm
    )
    
    elementos = []
    estilos = getSampleStyleSheet()
    
    estilos.add(ParagraphStyle(
        'TituloComunicado',
        parent=estilos['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=0.5*cm
    ))
    
    estilos.add(ParagraphStyle(
        'Secao',
        parent=estilos['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=0.3*cm
    ))
    
    estilos.add(ParagraphStyle(
        'Texto',
        parent=estilos['Normal'],
        fontSize=9,
        alignment=TA_JUSTIFY,
        spaceAfter=0.2*cm
    ))
    
    estilos.add(ParagraphStyle(
        'Assinatura',
        parent=estilos['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        spaceAfter=0.5*cm
    ))
    
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4.5*cm)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 0.2*cm))
    except:
        pass
    
    elementos.append(Paragraph("📬 COMUNICADO AOS PAIS/RESPONSÁVEIS", estilos['TituloComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph(f"<b>Prezados Pais/Responsáveis do(a) aluno(a):</b> {ocorrencia.get('aluno', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Turma:</b> {ocorrencia.get('turma', 'N/A')} | <b>Data:</b> {ocorrencia.get('data', 'N/A')}", estilos['Texto']))
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph("Gostaríamos de solicitar o seu comparecimento à escola para tratarmos de assuntos relacionados ao desenvolvimento escolar e disciplinar do estudante mencionado acima.", estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>Motivo:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"Registro de ocorrência: {ocorrencia.get('categoria', 'N/A')} (Gravidade: {ocorrencia.get('gravidade', 'N/A')})", estilos['Texto']))
    
    elementos.append(Spacer(1, 1*cm))
    elementos.append(Paragraph("Contamos com a sua colaboração, pois a parceria entre família e escola é fundamental para o sucesso do aluno.", estilos['Texto']))
    
    elementos.append(Spacer(1, 2*cm))
    elementos.append(Paragraph("____________________________________________________", estilos['Assinatura']))
    elementos.append(Paragraph("Assinatura da Direção / Coordenação", estilos['Assinatura']))
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer