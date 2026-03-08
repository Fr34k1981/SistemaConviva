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
except:
    SUPABASE_URL = ""
    SUPABASE_KEY = ""

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

# ============================================================================
# CORES PARA GRÁFICOS E VISUALIZAÇÃO
# ============================================================================

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

# ============================================================================
# FLUXO DE AÇÕES POR OCORRÊNCIA (PROTOCOLO 179)
# ============================================================================

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

# ============================================================================
# ENCAMINHAMENTOS POR GRAVIDADE (PROTOCOLO 179)
# ============================================================================

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
    """Carrega todos os alunos do banco de dados Supabase."""
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
    """Carrega todos os professores do banco de dados Supabase."""
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
    """Carrega todos os responsáveis ativos do banco de dados."""
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
    """Carrega todas as ocorrências do banco de dados."""
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
    """Carrega todas as turmas do banco de dados."""
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/turmas?select=*&order=nome.asc",
            headers=HEADERS
        )
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        return pd.DataFrame(columns=['nome', 'ano', 'periodo'])


def salvar_aluno(aluno_dict):
    """Salva um aluno no banco de dados."""
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/alunos",
            json=aluno_dict,
            headers=HEADERS
        )
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao salvar aluno: {str(e)}")
        return False


def salvar_professor(professor_dict):
    """Salva um professor no banco de dados."""
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/professores",
            json=professor_dict,
            headers=HEADERS
        )
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao salvar professor: {str(e)}")
        return False


def salvar_responsavel(responsavel_dict):
    """Salva um responsável no banco de dados."""
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/responsaveis",
            json=responsavel_dict,
            headers=HEADERS
        )
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao salvar responsável: {str(e)}")
        return False


def salvar_turma(turma_dict):
    """Salva uma turma no banco de dados."""
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/turmas",
            json=turma_dict,
            headers=HEADERS
        )
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao salvar turma: {str(e)}")
        return False


def salvar_ocorrencia(ocorrencia_dict):
    """Salva uma ocorrência no banco de dados."""
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/ocorrencias",
            json=ocorrencia_dict,
            headers=HEADERS
        )
        if response.status_code in [200, 201]:
            return True, "Ocorrência salva com sucesso!"
        else:
            return False, f"Erro ao salvar: {response.text}"
    except Exception as e:
        return False, f"Erro ao salvar: {str(e)}"


def atualizar_ocorrencia(id_ocorrencia, ocorrencia_dict):
    """Atualiza uma ocorrência no banco de dados."""
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}",
            json=ocorrencia_dict,
            headers=HEADERS
        )
        if response.status_code in [200, 204]:
            return True, "Ocorrência atualizada com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        return False, f"Erro ao atualizar: {str(e)}"


def excluir_ocorrencia(id_ocorrencia):
    """Exclui uma ocorrência do banco de dados."""
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}",
            headers=HEADERS
        )
        if response.status_code in [200, 204]:
            return True, "Ocorrência excluída com sucesso!"
        else:
            return False, f"Erro ao excluir: {response.text}"
    except Exception as e:
        return False, f"Erro ao excluir: {str(e)}"


def atualizar_aluno(ra, dados):
    """Atualiza dados de um aluno."""
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra}",
            json=dados,
            headers=HEADERS
        )
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao atualizar aluno: {str(e)}")
        return False


def excluir_alunos_por_turma(turma):
    """Exclui todos os alunos de uma turma."""
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/alunos?turma=eq.{turma}",
            headers=HEADERS
        )
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao excluir turma: {str(e)}")
        return False


def excluir_professor(id_prof):
    """Exclui um professor do banco de dados."""
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}",
            headers=HEADERS
        )
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao excluir professor: {str(e)}")
        return False


def excluir_responsavel(id_resp):
    """Exclui um responsável do banco de dados."""
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}",
            headers=HEADERS
        )
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao excluir responsável: {str(e)}")
        return False


def atualizar_responsavel(id_resp, dados):
    """Atualiza dados de um responsável."""
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}",
            json=dados,
            headers=HEADERS
        )
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao atualizar responsável: {str(e)}")
        return False


def excluir_turma(id_turma):
    """Exclui uma turma do banco de dados."""
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/turmas?id=eq.{id_turma}",
            headers=HEADERS
        )
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao excluir turma: {str(e)}")
        return False


def verificar_ocorrencia_duplicada(ra, categoria, data, df_ocorrencias):
    """Verifica se já existe uma ocorrência duplicada."""
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
    """Faz upload de foto para o Supabase Storage."""
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
    """Atualiza a foto de um aluno no banco de dados."""
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra}",
            json={"foto_url": foto_url},
            headers=HEADERS
        )
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao atualizar foto do aluno: {str(e)}")
        return False


def atualizar_foto_professor(nome, foto_url):
    """Atualiza a foto de um professor no banco de dados."""
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/professores?nome=eq.{nome}",
            json={"foto_url": foto_url},
            headers=HEADERS
        )
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao atualizar foto do professor: {str(e)}")
        return False


# ============================================================================
# FUNÇÕES DE GERAÇÃO DE PDF
# ============================================================================

def gerar_pdf_ocorrencia(ocorrencia, df_responsaveis=None):
    """Gera PDF da ocorrência com formatação profissional."""
    buffer = io.BytesIO()
    
    # CORREÇÃO: Margens otimizadas para caber mais conteúdo
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
    
    # CORREÇÃO: Logo no cabeçalho (16cm x 4.5cm)
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
    
    # CORREÇÃO: Professor aparece apenas uma vez nas assinaturas
    elementos.append(Spacer(1, 0.5*cm))
    
    # Assinaturas - CORREÇÃO: Sem duplicar Professor, alinhado à esquerda
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
    
    # Professor Responsável aparece apenas UMA vez aqui
    if ocorrencia.get('professor'):
        elementos.append(Paragraph(f"<b>Professor Responsável:</b> {ocorrencia.get('professor')}", estilos['Texto']))
    
    elementos.append(Spacer(1, 0.5*cm))
    
    # CORREÇÃO: Removido "CIÊNCIA DOS PAIS" e rodapé
    # Não adicionar estas linhas:
    # - elementos.append(Paragraph("<b>CIÊNCIA DOS PAIS/RESPONSÁVEIS:</b>", ...))
    # - elementos.append(Paragraph("Declaro ciência...", ...))
    # - elementos.append(Paragraph("_" * 75, ...))
    # - elementos.append(Paragraph(f"Gerado em...", ...))
    
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
    
    # CORREÇÃO: Logo no cabeçalho
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
    
    elementos.append(Paragraph(
        f"Prezados responsáveis pelo(a) estudante <b>{ocorrencia.get('aluno', 'N/A')}</b>,",
        estilos['Texto']
    ))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph(
        "Venho por meio deste comunicar que foi registrado uma ocorrência disciplinar conforme detalhes abaixo:",
        estilos['Texto']
    ))
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph(f"<b>Data:</b> {ocorrencia.get('data', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Turma:</b> {ocorrencia.get('turma', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Categoria:</b> {ocorrencia.get('categoria', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Gravidade:</b> {ocorrencia.get('gravidade', 'N/A')}", estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>Relato:</b>", estilos['Secao']))
    elementos.append(Paragraph(str(ocorrencia.get('relato', '')), estilos['Texto']))
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph("<b>Encaminhamentos Realizados:</b>", estilos['Secao']))
    encaminhamentos = ocorrencia.get('encaminhamentos', [])
    if isinstance(encaminhamentos, list):
        for enc in encaminhamentos:
            elementos.append(Paragraph(f"• {enc}", estilos['Texto']))
    else:
        elementos.append(Paragraph(str(encaminhamentos), estilos['Texto']))
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph(
        "Solicitamos que tomem conhecimento e compareçam à escola para assinatura deste comunicado.",
        estilos['Texto']
    ))
    elementos.append(Spacer(1, 1*cm))
    
    elementos.append(Paragraph(f"Atenciosamente,", estilos['Texto']))
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("_" * 50, estilos['Normal']))
    elementos.append(Paragraph("Direção / Coordenação", estilos['Assinatura']))
    
    # CORREÇÃO: Removido seção de ciência dos pais
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer


def gerar_pdf_comunicado_editavel(aluno_info, occ_info, medidas_aplicadas, observacoes, 
                                   total_ocorrencias, gravissima_count, grave_count, 
                                   media_count, leve_count, texto_editado, df_responsaveis):
    """Gera PDF de comunicado com texto editável."""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    elementos = []
    estilos = getSampleStyleSheet()
    
    estilos.add(ParagraphStyle(
        'TituloComunicado',
        parent=estilos['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=1*cm
    ))
    
    estilos.add(ParagraphStyle(
        'TextoComunicado',
        parent=estilos['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=0.3*cm,
        leading=14
    ))
    
    # CORREÇÃO: Logo no cabeçalho
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4.5*cm)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 0.3*cm))
    except:
        pass
    
    elementos.append(Paragraph("📬 COMUNICADO AOS PAIS/RESPONSÁVEIS", estilos['TituloComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph(f"<b>Aluno(a):</b> {aluno_info.get('nome', 'N/A')}", estilos['TextoComunicado']))
    elementos.append(Paragraph(f"<b>RA:</b> {aluno_info.get('ra', 'N/A')}", estilos['TextoComunicado']))
    elementos.append(Paragraph(f"<b>Turma:</b> {aluno_info.get('turma', 'N/A')}", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
    texto_linhas = texto_editado.split('\n')
    for linha in texto_linhas:
        if linha.strip():
            elementos.append(Paragraph(linha.strip(), estilos['TextoComunicado']))
    
    elementos.append(Spacer(1, 1*cm))
    
    elementos.append(Paragraph("<b>ASSINATURAS:</b>", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
    cargos = ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)"]
    
    for cargo in cargos:
        if df_responsaveis is not None and not df_responsaveis.empty:
            resp = df_responsaveis[df_responsaveis['cargo'] == cargo]
            if not resp.empty and resp.iloc[0].get('nome'):
                elementos.append(Paragraph(f"<b>{cargo}:</b> {resp.iloc[0].get('nome', '')}", estilos['TextoComunicado']))
            else:
                elementos.append(Paragraph(f"<b>{cargo}:</b> _________________________________", estilos['TextoComunicado']))
        else:
            elementos.append(Paragraph(f"<b>{cargo}:</b> _________________________________", estilos['TextoComunicado']))
        elementos.append(Spacer(1, 0.5*cm))
    
    # CORREÇÃO: Removido ciência dos pais e rodapé
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer


# ============================================================================
# FUNÇÕES DE BACKUP
# ============================================================================

def criar_backup_dados():
    """Cria backup de todos os dados do sistema."""
    backup_data = {
        'ocorrencias': carregar_ocorrencias().to_dict('records'),
        'alunos': carregar_alunos().to_dict('records'),
        'professores': carregar_professores().to_dict('records'),
        'responsaveis': carregar_responsaveis().to_dict('records'),
        'data_backup': datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    return json.dumps(backup_data, ensure_ascii=False, indent=2)


def restaurar_backup_dados(backup_json):
    """Restaura backup de dados."""
    try:
        backup_data = json.loads(backup_json)
        
        contagem_ocorrencias = 0
        contagem_alunos = 0
        contagem_professores = 0
        contagem_responsaveis = 0
        
        if 'ocorrencias' in backup_data:
            for occ in backup_data['ocorrencias']:
                if salvar_ocorrencia(occ)[0]:
                    contagem_ocorrencias += 1
        
        if 'alunos' in backup_data:
            for aluno in backup_data['alunos']:
                if salvar_aluno(aluno):
                    contagem_alunos += 1
        
        if 'professores' in backup_data:
            for prof in backup_data['professores']:
                if salvar_professor(prof):
                    contagem_professores += 1
        
        if 'responsaveis' in backup_data:
            for resp in backup_data['responsaveis']:
                if salvar_responsavel(resp):
                    contagem_responsaveis += 1
        
        return True, {
            'ocorrencias': contagem_ocorrencias,
            'alunos': contagem_alunos,
            'professores': contagem_professores,
            'responsaveis': contagem_responsaveis
        }
    except Exception as e:
        return False, str(e)


# ============================================================================
# INTERFACE PRINCIPAL - CABEÇALHO E MENU LATERAL
# ============================================================================

# CORREÇÃO: Logo carregando do GitHub na Home
st.markdown(f"""
<div class="main-header">
    <img src="https://raw.githubusercontent.com/Fr34k1981/SistemaConviva/main/logo.jpg" 
         style="max-width: 150px; margin-bottom: 1rem;" 
         alt="Logo da Escola">
    <div class="school-name">🏫 {ESCOLA_NOME}</div>
    <div class="school-subtitle">{ESCOLA_SUBTITULO}</div>
    <div class="school-address">📍 {ESCOLA_ENDERECO}</div>
    <div class="school-contact">{ESCOLA_CEP} • {ESCOLA_TELEFONE} • {ESCOLA_EMAIL}</div>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.selectbox(
    "📋 Menu Principal",
    [
        "🏠 Início",
        "👨‍🏫 Cadastrar Professores",
        "👤 Cadastrar Responsáveis por Assinatura",
        "📝 Registrar Ocorrência",
        "📄 Comunicado aos Pais",
        "📥 Importar Alunos",
        "📋 Gerenciar Turmas Importadas",
        "👥 Lista de Alunos",
        "📊 Histórico de Ocorrências",
        "📈 Gráficos e Indicadores",
        "🖨️ Imprimir PDF",
        "💾 Backup de Dados",
        "⚙️ Configurações"
    ],
    index=0
)

st.session_state.pagina_atual = menu

# ============================================================================
# PÁGINA: INÍCIO / HOME
# ============================================================================

if menu == "🏠 Início":
    st.title("🏠 Dashboard - Visão Geral")
    
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    df_professores = carregar_professores()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total de Ocorrências", len(df_ocorrencias))
    
    with col2:
        if not df_ocorrencias.empty:
            gravissimas = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Gravíssima'])
            st.metric("🔴 Gravíssimas", gravissimas)
        else:
            st.metric("🔴 Gravíssimas", 0)
    
    with col3:
        st.metric("👥 Total de Alunos", len(df_alunos))
    
    with col4:
        st.metric("👨‍🏫 Total de Professores", len(df_professores))
    
    st.markdown("---")
    
    if not df_ocorrencias.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Ocorrências por Categoria")
            if 'categoria' in df_ocorrencias.columns:
                cat_counts = df_ocorrencias['categoria'].value_counts().head(10)
                fig = px.bar(
                    x=cat_counts.values,
                    y=cat_counts.index,
                    orientation='h',
                    color=cat_counts.values,
                    color_continuous_scale='Reds'
                )
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Ocorrências por Gravidade")
            if 'gravidade' in df_ocorrencias.columns:
                grav_counts = df_ocorrencias['gravidade'].value_counts()
                fig = px.pie(
                    values=grav_counts.values,
                    names=grav_counts.index,
                    color=grav_counts.index,
                    color_discrete_map=CORES_GRAVIDADE
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📋 Últimas Ocorrências Registradas")
        st.dataframe(df_ocorrencias.head(10), use_container_width=True)
    else:
        st.info("📭 Nenhuma ocorrência registrada ainda.")
    
    if not df_alunos.empty:
        st.subheader("🏫 Resumo de Turmas")
        turmas_info = df_alunos['turma'].value_counts()
        st.write(f"**Total de Turmas:** {len(turmas_info)}")
        st.write(f"**Total de Alunos:** {len(df_alunos)}")

# ============================================================================
# PÁGINA: CADASTRAR PROFESSORES (COM UPLOAD DE FOTO)
# ============================================================================

elif menu == "👨‍🏫 Cadastrar Professores":
    st.title("👨‍🏫 Cadastrar Professores")
    
    df_professores = carregar_professores()
    
    st.subheader("📝 Novo Professor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome_prof = st.text_input("Nome Completo *", placeholder="Ex: João da Silva", key="nome_prof_input")
        email_prof = st.text_input("E-mail (opcional)", placeholder="Ex: joao@educacao.sp.gov.br", key="email_prof_input")
    
    with col2:
        cargo_prof = st.text_input("Cargo (opcional)", placeholder="Ex: Professor de Matemática", key="cargo_prof_input")
        st.info("💡 Cadastre todos os professores da escola para facilitar o registro de ocorrências.")
    
    if st.button("💾 Salvar Professor", type="primary", key="btn_salvar_prof"):
        if nome_prof.strip():
            if not df_professores.empty:
                nomes_existentes = [n.lower().strip() for n in df_professores['nome'].tolist()]
                if nome_prof.lower().strip() in nomes_existentes:
                    st.error("❌ Já existe um professor com este nome cadastrado!")
                else:
                    professor_dict = {
                        'nome': nome_prof.strip(),
                        'email': email_prof.strip() if email_prof else None,
                        'cargo': cargo_prof.strip() if cargo_prof else None,
                        'foto_url': None
                    }
                    if salvar_professor(professor_dict):
                        st.success(f"✅ Professor {nome_prof} cadastrado com sucesso!")
                        carregar_professores.clear()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar professor")
            else:
                professor_dict = {
                    'nome': nome_prof.strip(),
                    'email': email_prof.strip() if email_prof else None,
                    'cargo': cargo_prof.strip() if cargo_prof else None,
                    'foto_url': None
                }
                if salvar_professor(professor_dict):
                    st.success(f"✅ Professor {nome_prof} cadastrado com sucesso!")
                    carregar_professores.clear()
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar professor")
        else:
            st.error("❌ Nome é obrigatório!")
    
    st.markdown("---")
    
    # CORREÇÃO: Upload de foto de professor restaurado
    st.subheader("📷 Upload de Foto de Professor")
    
    if not df_professores.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            professor_foto = st.selectbox("Selecione o Professor", df_professores['nome'].tolist(), key="prof_foto_sel")
        
        with col2:
            foto_file = st.file_uploader("Selecione a foto", type=['jpg', 'jpeg', 'png'], key="prof_foto_upload")
        
        if foto_file and st.button("📷 Enviar Foto", key="prof_enviar_foto_btn"):
            url, msg = upload_foto_supabase(foto_file, 'professores', f"{professor_foto}.jpg")
            if url:
                if atualizar_foto_professor(professor_foto, url):
                    st.success(f"✅ {msg}")
                    carregar_professores.clear()
                    st.rerun()
                else:
                    st.error("❌ Erro ao atualizar foto no banco")
            else:
                st.error(f"❌ {msg}")
    
    st.markdown("---")
    
    st.subheader("📋 Professores Cadastrados")
    
    if not df_professores.empty:
        for idx, prof in df_professores.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 4, 2, 1, 1])
                
                with col1:
                    if prof.get('foto_url'):
                        st.image(prof['foto_url'], width=60)
                    else:
                        st.write("👤")
                
                with col2:
                    st.markdown(f"**{prof.get('nome', 'N/A')}**")
                    if prof.get('email'):
                        st.write(f"📧 {prof['email']}")
                    if prof.get('cargo'):
                        st.write(f"💼 {prof['cargo']}")
                
                with col3:
                    st.write(f"Cargo: {prof.get('cargo', 'Não informado')}")
                
                with col4:
                    if st.button("✏️", key=f"edit_prof_{prof.get('id', idx)}", help="Editar"):
                        st.session_state.editando_prof = prof.get('id', idx)
                        st.rerun()
                
                with col5:
                    if st.button("🗑️", key=f"del_prof_{prof.get('id', idx)}", help="Excluir"):
                        if excluir_professor(prof.get('id', idx)):
                            st.success("✅ Excluído!")
                            carregar_professores.clear()
                            st.rerun()
                
                st.divider()
        
        st.info(f"📊 **Total:** {len(df_professores)} professores cadastrados")
    else:
        st.info("📭 Nenhum professor cadastrado ainda.")

# ============================================================================
# PÁGINA: CADASTRAR RESPONSÁVEIS POR ASSINATURA
# ============================================================================

elif menu == "👤 Cadastrar Responsáveis por Assinatura":
    st.title("👤 Cadastrar Responsáveis por Assinatura")
    
    st.info("💡 Cadastre os responsáveis que assinarão os documentos (Diretor, Vice, CGPG, etc.)")
    
    st.subheader("📝 Novo Responsável")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cargo_resp = st.selectbox(
            "Cargo *",
            ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)", "Orientador(a)", "Outro"]
        )
        nome_resp = st.text_input("Nome Completo *")
    
    with col2:
        ativo_resp = st.checkbox("Ativo", value=True)
        
        if st.button("💾 Salvar Responsável", type="primary"):
            if nome_resp:
                responsavel_dict = {
                    'cargo': cargo_resp,
                    'nome': nome_resp,
                    'ativo': ativo_resp
                }
                
                if salvar_responsavel(responsavel_dict):
                    st.success(f"✅ {cargo_resp} cadastrado com sucesso!")
                    carregar_responsaveis.clear()
                    st.rerun()
                else:
                    st.error("❌ Erro ao cadastrar responsável")
            else:
                st.error("❌ Nome é obrigatório!")
    
    st.markdown("---")
    
    st.subheader("📋 Responsáveis Cadastrados")
    
    df_responsaveis = carregar_responsaveis()
    
    if not df_responsaveis.empty:
        for idx, resp in df_responsaveis.iterrows():
            col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
            
            with col1:
                st.markdown(f"**{resp['cargo']}**")
            
            with col2:
                st.markdown(f"{resp['nome']}")
            
            with col3:
                status = "✅" if resp.get('ativo', True) else "❌"
                st.write(f"Ativo: {status}")
            
            with col4:
                if st.button("🗑️", key=f"del_resp_{resp.get('id', idx)}"):
                    if excluir_responsavel(resp.get('id', idx)):
                        st.success("✅ Excluído!")
                        carregar_responsaveis.clear()
                        st.rerun()
    else:
        st.info("📭 Nenhum responsável cadastrado.")

# ============================================================================
# PÁGINA: REGISTRAR OCORRÊNCIA (AUTOMÁTICO PELO PROTOCOLO 179)
# ============================================================================

elif menu == "📝 Registrar Ocorrência":
    st.title("📝 Registrar Nova Ocorrência")
    
    if st.session_state.ocorrencia_salva_sucesso:
        st.markdown('<div class="success-box">✅ OCORRÊNCIA(S) REGISTRADA(S) COM SUCESSO!</div>', unsafe_allow_html=True)
        st.session_state.ocorrencia_salva_sucesso = False
        st.session_state.salvando_ocorrencia = False
    
    df_alunos = carregar_alunos()
    
    if df_alunos.empty:
        st.warning("⚠️ Importe alunos primeiro.")
    else:
        tz_sp = pytz.timezone('America/Sao_Paulo')
        data_hora_sp = datetime.now(tz_sp)
        
        st.subheader("🏫 Selecionar Turma(s)")
        
        modo_multiplas_turmas = st.checkbox("📚 Registrar para múltiplas turmas", key="modo_multiplas_turmas")
        
        turmas = df_alunos["turma"].unique().tolist()
        
        if modo_multiplas_turmas:
            turmas_selecionadas = st.multiselect("Selecione as Turmas", turmas)
        else:
            turma_selecionada = st.selectbox("Selecione a Turma", turmas)
            turmas_selecionadas = [turma_selecionada] if turma_selecionada else []
        
        if turmas_selecionadas:
            alunos = df_alunos[df_alunos["turma"].isin(turmas_selecionadas)]
            
            if len(alunos) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 👥 Selecionar Estudante(s)")
                    st.info("💡 Selecione um ou mais estudantes envolvidos na mesma ocorrência")
                    
                    modo_multiplo = st.checkbox("👥 Registrar para múltiplos estudantes", key="modo_multiplo")
                    
                    if modo_multiplo:
                        alunos_selecionados = st.multiselect(
                            "Selecione os estudantes",
                            alunos["nome"].tolist()
                        )
                    else:
                        busca_aluno = st.text_input("🔍 Buscar Aluno (digite o nome)", "")
                        
                        if busca_aluno:
                            lista_alunos = alunos['nome'].tolist()
                            resultados = process.extract(busca_aluno, lista_alunos, limit=5)
                            aluno_selecionado = st.selectbox(
                                "Selecione o Aluno",
                                [r[0] for r in resultados]
                            )
                            alunos_selecionados = [aluno_selecionado] if aluno_selecionado else []
                        else:
                            aluno_selecionado = st.selectbox("Selecione o Aluno", alunos["nome"].tolist())
                            alunos_selecionados = [aluno_selecionado] if aluno_selecionado else []
                
                with col2:
                    st.markdown("### 📅 Data e Hora")
                    data = st.date_input("Data", value=data_hora_sp.date())
                    hora = st.time_input("Hora", value=data_hora_sp.time())
                    
                    st.markdown("### 👨‍🏫 Professor Responsável")
                    df_professores = carregar_professores()
                    if not df_professores.empty:
                        prof_lista = df_professores["nome"].tolist()
                        prof = st.selectbox("Professor", ["Selecione..."] + prof_lista)
                    else:
                        prof = st.text_input("Professor Responsável")
                
                st.markdown("---")
                
                st.markdown("### 📋 Dados da Ocorrência")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # CORREÇÃO: Seleção de ocorrência com gravidade automática
                    categoria_grupo = st.selectbox("📁 Categoria", list(CATEGORIAS_OCORRENCIAS.keys()), key="cat_grupo")
                    categorias_grupo = list(CATEGORIAS_OCORRENCIAS[categoria_grupo].keys())
                    categoria = st.selectbox("📋 Ocorrência", categorias_grupo, key="cat_ocorr")
                
                with col2:
                    # CORREÇÃO: Gravidade automática baseada na ocorrência selecionada
                    gravidade = CATEGORIAS_OCORRENCIAS[categoria_grupo].get(categoria, "Leve")
                    gravidade_select = st.selectbox(
                        "⚡ Gravidade (Automático pelo Protocolo 179)",
                        ["Gravíssima", "Grave", "Média", "Leve"],
                        index=["Gravíssima", "Grave", "Média", "Leve"].index(gravidade),
                        key="grav_select"
                    )
                
                # CORREÇÃO: Mostrar fluxo de ações do protocolo 179
                if categoria in FLUXO_ACOES:
                    st.warning(f"📌 {FLUXO_ACOES[categoria]}")
                
                relato = st.text_area("📝 Relato da Ocorrência", height=200)
                
                # CORREÇÃO: Encaminhamentos automáticos baseados na gravidade
                st.subheader("🔄 Encaminhamentos (Automático pelo Protocolo 179)")
                encaminhamentos_disponiveis = ENCAMINHAMENTOS_POR_GRAVIDADE.get(gravidade_select, [])
                encaminhamentos_selecionados = st.multiselect(
                    "Selecione os encaminhamentos realizados",
                    encaminhamentos_disponiveis,
                    default=encaminhamentos_disponiveis,
                    key="encam_select"
                )
                
                testemunhas = st.text_input("👀 Testemunhas (opcional)")
                evidencias = st.text_area("📎 Evidências (opcional)")
                
                if st.session_state.salvando_ocorrencia:
                    st.button("💾 Salvando...", disabled=True, type="primary")
                    st.info("⏳ Aguarde, registrando ocorrência...")
                else:
                    if st.button("💾 Salvar Ocorrência", type="primary"):
                        if prof and prof != "Selecione..." and relato and alunos_selecionados:
                            st.session_state.salvando_ocorrencia = True
                            
                            data_str = f"{data.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}"
                            categoria_str = categoria
                            
                            contagem_salvas = 0
                            contagem_duplicadas = 0
                            erros = 0
                            
                            for nome_aluno in alunos_selecionados:
                                ra_aluno = alunos[alunos["nome"] == nome_aluno]["ra"].values[0]
                                turma_aluno = alunos[alunos["nome"] == nome_aluno]["turma"].values[0]
                                
                                if verificar_ocorrencia_duplicada(ra_aluno, categoria_str, data_str, df_ocorrencias):
                                    contagem_duplicadas += 1
                                else:
                                    ocorrencia_dict = {
                                        'data': data_str,
                                        'aluno': nome_aluno,
                                        'ra': ra_aluno,
                                        'turma': turma_aluno,
                                        'categoria': categoria_str,
                                        'gravidade': gravidade_select,
                                        'relato': relato,
                                        'professor': prof,
                                        'encaminhamentos': encaminhamentos_selecionados,
                                        'testemunhas': testemunhas,
                                        'evidencias': evidencias
                                    }
                                    
                                    sucesso, mensagem = salvar_ocorrencia(ocorrencia_dict)
                                    
                                    if sucesso:
                                        contagem_salvas += 1
                                    else:
                                        erros += 1
                            
                            if contagem_salvas > 0:
                                st.success(f"✅ {contagem_salvas} ocorrência(s) registrada(s) com sucesso!")
                                if contagem_duplicadas > 0:
                                    st.warning(f"⚠️ {contagem_duplicadas} ocorrência(s) já existiam (ignorado)")
                                if erros > 0:
                                    st.error(f"❌ {erros} erro(s) ao salvar")
                                
                                st.session_state.ocorrencia_salva_sucesso = True
                                st.session_state.salvando_ocorrencia = False
                                st.rerun()
                            else:
                                st.error("❌ Nenhuma ocorrência foi salva. Verifique os dados.")
                                st.session_state.salvando_ocorrencia = False
                        else:
                            if not alunos_selecionados:
                                st.error("❌ Selecione pelo menos um estudante!")
                            elif not prof or prof == "Selecione...":
                                st.error("❌ Selecione o professor responsável!")
                            elif not relato:
                                st.error("❌ Preencha o relato da ocorrência!")
                            st.session_state.salvando_ocorrencia = False
        else:
            st.warning("⚠️ Selecione pelo menos uma turma.")

# ============================================================================
# PÁGINA: COMUNICADO AOS PAIS (COM MENU DE TURMAS)
# ============================================================================

elif menu == "📄 Comunicado aos Pais":
    st.title("📄 Comunicado aos Pais/Responsáveis")
    
    st.info("💡 Gere um comunicado personalizado com histórico de ocorrências do aluno")
    
    df_alunos = carregar_alunos()
    df_ocorrencias = carregar_ocorrencias()
    df_responsaveis = carregar_responsaveis()
    
    if df_alunos.empty:
        st.warning("⚠️ Cadastre alunos primeiro.")
    else:
        # CORREÇÃO: Menu de turmas para filtrar alunos
        st.subheader("🏫 Selecionar Turma")
        
        turmas = df_alunos['turma'].unique().tolist()
        turma_selecionada = st.selectbox("Selecione a Turma", ["Todas"] + turmas, key="comm_turma")
        
        if turma_selecionada != "Todas":
            df_filtrado = df_alunos[df_alunos['turma'] == turma_selecionada]
        else:
            df_filtrado = df_alunos
        
        # Busca adicional por nome ou RA
        busca = st.text_input("🔍 Buscar por nome ou RA (opcional)", placeholder="Digite o nome ou RA do aluno", key="comm_busca")
        
        if busca:
            df_filtrado = df_filtrado[
                (df_filtrado['nome'].str.contains(busca, case=False, na=False)) |
                (df_filtrado['ra'].astype(str).str.contains(busca, na=False))
            ]
        
        if not df_filtrado.empty:
            aluno_sel = st.selectbox("Selecione o Aluno", df_filtrado['nome'].tolist(), key="comm_aluno_sel")
            aluno_info = df_filtrado[df_filtrado['nome'] == aluno_sel].iloc[0]
            
            ra_aluno = aluno_info.get('ra', 'N/A')
            turma_aluno = aluno_info.get('turma', 'N/A')
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**RA:** {ra_aluno}")
            with col2:
                st.info(f"**Turma:** {turma_aluno}")
            with col3:
                if aluno_info.get('foto_url'):
                    st.image(aluno_info['foto_url'], width=80)
            
            st.markdown("---")
            
            st.subheader("📊 Histórico de Ocorrências do Aluno")
            
            if not df_ocorrencias.empty:
                ocorrencias_aluno = df_ocorrencias[df_ocorrencias['ra'] == ra_aluno]
                
                if not ocorrencias_aluno.empty:
                    total_ocorrencias = len(ocorrencias_aluno)
                    
                    gravissima_count = len(ocorrencias_aluno[ocorrencias_aluno['gravidade'] == 'Gravíssima'])
                    grave_count = len(ocorrencias_aluno[ocorrencias_aluno['gravidade'] == 'Grave'])
                    media_count = len(ocorrencias_aluno[ocorrencias_aluno['gravidade'] == 'Média'])
                    leve_count = len(ocorrencias_aluno[ocorrencias_aluno['gravidade'] == 'Leve'])
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("🔴 Gravíssimas", gravissima_count)
                    with col2:
                        st.metric("🟠 Graves", grave_count)
                    with col3:
                        st.metric("🟡 Médias", media_count)
                    with col4:
                        st.metric("🟢 Leves", leve_count)
                    
                    st.markdown("---")
                    
                    st.subheader("📋 Selecionar Ocorrência para Comunicado")
                    
                    occ_options = []
                    for idx, occ in ocorrencias_aluno.iterrows():
                        occ_options.append(f"{occ['id']} - {occ['data']} - {occ['categoria']} ({occ['gravidade']})")
                    
                    occ_sel = st.selectbox("Selecione a Ocorrência", occ_options, key="comm_occ_sel")
                    
                    if occ_sel:
                        occ_id = int(occ_sel.split(" - ")[0])
                        occ_info = ocorrencias_aluno[ocorrencias_aluno['id'] == occ_id].iloc[0]
                        
                        st.markdown("### Dados da Ocorrência Selecionada")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Data:** {occ_info.get('data', 'N/A')}")
                            st.write(f"**Categoria:** {occ_info.get('categoria', 'N/A')}")
                            st.write(f"**Gravidade:** {occ_info.get('gravidade', 'N/A')}")
                        with col2:
                            st.write(f"**Professor:** {occ_info.get('professor', 'N/A')}")
                            st.write(f"**Turma:** {occ_info.get('turma', 'N/A')}")
                        
                        st.write(f"**Relato:** {occ_info.get('relato', 'N/A')}")
                        
                        st.markdown("---")
                        
                        st.subheader("✏️ Preencher Comunicado")
                        
                        st.write("**Medidas Aplicadas (selecione as que foram aplicadas):**")
                        
                        medidas_opcoes = [
                            "Orientação ao Estudante",
                            "Comunicação aos Pais/Responsáveis",
                            "Encaminhamento à Coordenação",
                            "Encaminhamento à Direção",
                            "Registro em Ata de Ocorrência",
                            "Conselho Tutelar Notificado",
                            "Boletim de Ocorrência Registrado",
                            "Acompanhamento Pedagógico",
                            "Acompanhamento Psicopedagógico",
                            "Suspensão Temporária",
                            "Transferência de Turma",
                            "Outras Medidas"
                        ]
                        
                        medidas_aplicadas = []
                        cols = st.columns(2)
                        for i, medida in enumerate(medidas_opcoes):
                            with cols[i % 2]:
                                if st.checkbox(medida, key=f"medida_comm_{i}"):
                                    medidas_aplicadas.append(medida)
                        
                        observacoes = st.text_area(
                            "📝 Observações Adicionais (editável)",
                            placeholder="Descreva detalhes das medidas aplicadas, prazos, acompanhamentos necessários, orientações aos pais...",
                            height=150,
                            key="obs_comunicado"
                        )
                        
                        st.write("**Texto do Comunicado (editável):**")
                        
                        texto_padrao = f"""COMUNICADO AOS PAIS/RESPONSÁVEIS

Prezados responsáveis pelo(a) estudante {aluno_info['nome']},

Venho por meio deste comunicar que foi registrada uma ocorrência disciplinar conforme detalhes abaixo:

DATA: {occ_info.get('data', 'N/A')}
CATEGORIA: {occ_info.get('categoria', 'N/A')}
GRAVIDADE: {occ_info.get('gravidade', 'N/A')}
PROFESSOR RESPONSÁVEL: {occ_info.get('professor', 'N/A')}

RELATO DA OCORRÊNCIA:
{occ_info.get('relato', 'N/A')}

MEDIDAS APLICADAS:
{chr(10).join(['• ' + m for m in medidas_aplicadas]) if medidas_aplicadas else 'Em definição'}

OBSERVAÇÕES:
{observacoes if observacoes else 'Sem observações adicionais'}

HISTÓRICO DE OCORRÊNCIAS:
Este(a) estudante possui {total_ocorrencias} ocorrência(s) registrada(s) neste ano letivo, sendo:
- {gravissima_count} ocorrência(s) Gravíssima(s)
- {grave_count} ocorrência(s) Grave(s)
- {media_count} ocorrência(s) Média(s)
- {leve_count} ocorrência(s) Leve(s)

Solicitamos que tomem conhecimento e compareçam à escola para assinatura deste comunicado.

Atenciosamente,

Direção / Coordenação
{ESCOLA_NOME}
{datetime.now().strftime('%d/%m/%Y')}
"""
                        
                        texto_editado = st.text_area(
                            "Editar Texto do Comunicado",
                            value=texto_padrao,
                            height=400,
                            key="texto_comunicado_edit"
                        )
                        
                        st.markdown("---")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("🖨️ Gerar Comunicado PDF", type="primary", key="gerar_comm_pdf"):
                                pdf_buffer = gerar_pdf_comunicado_editavel(
                                    aluno_info,
                                    occ_info,
                                    medidas_aplicadas,
                                    observacoes,
                                    total_ocorrencias,
                                    gravissima_count,
                                    grave_count,
                                    media_count,
                                    leve_count,
                                    texto_editado,
                                    df_responsaveis
                                )
                                st.download_button(
                                    label="📥 Baixar Comunicado PDF",
                                    data=pdf_buffer,
                                    file_name=f"Comunicado_{ra_aluno}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                    mime="application/pdf"
                                )
                                st.success("✅ Comunicado gerado! Imprima e envie com o aluno.")
                        
                        with col2:
                            if st.button("📋 Copiar Texto", key="copiarTexto"):
                                st.code(texto_editado, language="text")
                                st.info("📋 Texto copiado! Use Ctrl+C para copiar.")
                else:
                    st.info("ℹ️ Este aluno ainda não tem ocorrências registradas.")
        else:
            st.warning("⚠️ Nenhum aluno encontrado nesta turma.")

# ============================================================================
# PÁGINA: IMPORTAR ALUNOS (COM UPLOAD DE FOTO)
# ============================================================================

elif menu == "📥 Importar Alunos":
    st.title("📥 Importar Alunos (CSV)")
    
    st.info("💡 O arquivo CSV deve ter as colunas: ra, nome, data_nascimento, situacao, turma, genero")
    
    arquivo_csv = st.file_uploader("Selecione o arquivo CSV", type=['csv'])
    
    if arquivo_csv:
        try:
            df_import = pd.read_csv(arquivo_csv)
            st.write(f"📊 {len(df_import)} alunos encontrados")
            st.dataframe(df_import.head())
            
            if st.button("✅ Confirmar Importação"):
                contagem_salvas = 0
                contagem_duplicadas = 0
                erros = 0
                
                df_alunos_existentes = carregar_alunos()
                
                for _, row in df_import.iterrows():
                    aluno_dict = row.to_dict()
                    
                    if not df_alunos_existentes.empty:
                        duplicados = df_alunos_existentes[df_alunos_existentes['ra'] == aluno_dict.get('ra')]
                        if not duplicados.empty:
                            contagem_duplicadas += 1
                            continue
                    
                    if salvar_aluno(aluno_dict):
                        contagem_salvas += 1
                    else:
                        erros += 1
                
                if contagem_salvas > 0:
                    st.success(f"✅ {contagem_salvas} aluno(s) importado(s) com sucesso!")
                if contagem_duplicadas > 0:
                    st.warning(f"⚠️ {contagem_duplicadas} aluno(s) já existiam (ignorado)")
                if erros > 0:
                    st.error(f"❌ {erros} erro(s) ao importar")
                
                carregar_alunos.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao importar: {str(e)}")
    
    st.markdown("---")
    
    # CORREÇÃO: Upload de foto de aluno restaurado
    st.subheader("📷 Upload de Foto de Aluno")
    
    df_alunos = carregar_alunos()
    
    if not df_alunos.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            aluno_foto = st.selectbox("Selecione o Aluno", df_alunos['nome'].tolist(), key="aluno_foto_sel")
            ra_aluno = df_alunos[df_alunos['nome'] == aluno_foto]['ra'].values[0] if 'ra' in df_alunos.columns else None
        
        with col2:
            foto_file = st.file_uploader("Selecione a foto", type=['jpg', 'jpeg', 'png'], key="aluno_foto_upload")
        
        if foto_file and ra_aluno and st.button("📷 Enviar Foto", key="aluno_enviar_foto_btn"):
            url, msg = upload_foto_supabase(foto_file, 'alunos', f"{ra_aluno}.jpg")
            if url:
                if atualizar_foto_aluno(ra_aluno, url):
                    st.success(f"✅ {msg}")
                    carregar_alunos.clear()
                    st.rerun()
                else:
                    st.error("❌ Erro ao atualizar foto no banco")
            else:
                st.error(f"❌ {msg}")
    
    st.markdown("---")
    
    st.subheader("📋 Alunos Cadastrados")
    
    if not df_alunos.empty:
        st.dataframe(df_alunos, use_container_width=True)
        
        if st.button("📥 Exportar Alunos (CSV)"):
            csv = df_alunos.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Baixar CSV",
                data=csv,
                file_name=f"alunos_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("📭 Nenhum aluno cadastrado.")

# ============================================================================
# PÁGINA: GERENCIAR TURMAS IMPORTADAS
# ============================================================================

elif menu == "📋 Gerenciar Turmas Importadas":
    st.title("📋 Gerenciar Turmas Importadas")
    
    df_alunos = carregar_alunos()
    
    if not df_alunos.empty:
        st.subheader("📊 Turmas com Alunos Importados")
        
        turmas_info = df_alunos['turma'].value_counts()
        
        for turma, qtd in turmas_info.items():
            st.write(f"**{turma}:** {qtd} aluno(s)")
        
        st.markdown("---")
        
        st.subheader("🗑️ Excluir Turma")
        
        turma_excluir = st.selectbox("Selecione a Turma", turmas_info.index.tolist())
        
        if st.button("🗑️ Excluir Turma"):
            if excluir_alunos_por_turma(turma_excluir):
                st.success(f"✅ Turma {turma_excluir} excluída com sucesso!")
                carregar_alunos.clear()
                st.rerun()
            else:
                st.error("❌ Erro ao excluir turma")
    else:
        st.info("📭 Nenhuma turma cadastrada.")

# ============================================================================
# PÁGINA: LISTA DE ALUNOS
# ============================================================================

elif menu == "👥 Lista de Alunos":
    st.title("👥 Lista de Alunos")
    
    df_alunos = carregar_alunos()
    
    if not df_alunos.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            filtro_turma = st.multiselect("Filtrar por Turma", df_alunos['turma'].unique().tolist())
        
        with col2:
            busca_nome = st.text_input("🔍 Buscar por Nome")
        
        df_filtrado = df_alunos.copy()
        
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        
        if busca_nome:
            df_filtrado = df_filtrado[df_filtrado['nome'].str.contains(busca_nome, case=False, na=False)]
        
        st.dataframe(df_filtrado, use_container_width=True)
        
        if st.button("📥 Exportar Lista (CSV)"):
            csv = df_filtrado.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Baixar CSV",
                data=csv,
                file_name=f"alunos_lista_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("📭 Nenhum aluno cadastrado.")

# ============================================================================
# PÁGINA: HISTÓRICO DE OCORRÊNCIAS
# ============================================================================

elif menu == "📊 Histórico de Ocorrências":
    st.title("📊 Histórico de Ocorrências")
    
    df_ocorrencias = carregar_ocorrencias()
    
    if not df_ocorrencias.empty:
        st.subheader("🔍 Filtros")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filtro_gravidade = st.multiselect("Gravidade", ["Gravíssima", "Grave", "Média", "Leve"])
        
        with col2:
            filtro_categoria = st.multiselect("Categoria", df_ocorrencias['categoria'].unique().tolist())
        
        with col3:
            filtro_turma = st.multiselect("Turma", df_ocorrencias['turma'].unique().tolist())
        
        with col4:
            filtro_periodo = st.selectbox("Período", ["Todos", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Este ano"])
        
        df_filtrado = df_ocorrencias.copy()
        
        if filtro_gravidade:
            df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(filtro_gravidade)]
        
        if filtro_categoria:
            df_filtrado = df_filtrado[df_filtrado['categoria'].isin(filtro_categoria)]
        
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        
        if filtro_periodo != "Todos":
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            
            if filtro_periodo == "Últimos 7 dias":
                df_filtrado = df_filtrado[df_filtrado['data_dt'] >= (datetime.now() - timedelta(days=7))]
            elif filtro_periodo == "Últimos 30 dias":
                df_filtrado = df_filtrado[df_filtrado['data_dt'] >= (datetime.now() - timedelta(days=30))]
            elif filtro_periodo == "Este mês":
                df_filtrado = df_filtrado[
                    (df_filtrado['data_dt'].dt.month == datetime.now().month) &
                    (df_filtrado['data_dt'].dt.year == datetime.now().year)
                ]
            elif filtro_periodo == "Este ano":
                df_filtrado = df_filtrado[df_filtrado['data_dt'].dt.year == datetime.now().year]
        
        st.dataframe(df_filtrado, use_container_width=True)
        
        st.subheader("🛠️ Ações")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            id_selecionado = st.number_input("ID da Ocorrência", min_value=1, step=1)
        
        with col2:
            if st.button("📄 Gerar PDF"):
                df_responsaveis = carregar_responsaveis()
                ocorrencia = df_filtrado[df_filtrado['id'] == id_selecionado]
                if not ocorrencia.empty:
                    pdf_buffer = gerar_pdf_ocorrencia(ocorrencia.iloc[0].to_dict(), df_responsaveis)
                    st.download_button(
                        label="📥 Baixar PDF",
                        data=pdf_buffer,
                        file_name=f"ocorrencia_{id_selecionado}.pdf",
                        mime="application/pdf"
                    )
        
        with col3:
            if st.button("📬 Gerar Comunicado"):
                df_responsaveis = carregar_responsaveis()
                ocorrencia = df_filtrado[df_filtrado['id'] == id_selecionado]
                if not ocorrencia.empty:
                    pdf_buffer = gerar_pdf_comunicado(ocorrencia.iloc[0].to_dict(), df_responsaveis)
                    st.download_button(
                        label="📥 Baixar Comunicado",
                        data=pdf_buffer,
                        file_name=f"comunicado_{id_selecionado}.pdf",
                        mime="application/pdf"
                    )
        
        st.markdown("---")
        st.subheader("🗑️ Excluir Ocorrência")
        
        senha = st.text_input("🔒 Senha para Excluir", type="password", value="", key="senha_excluir")
        
        if st.button("🗑️ Excluir Ocorrência"):
            if senha == SENHA_EXCLUSAO:
                sucesso, mensagem = excluir_ocorrencia(id_selecionado)
                if sucesso:
                    st.success(f"✅ {mensagem}")
                    st.rerun()
                else:
                    st.error(f"❌ {mensagem}")
            else:
                st.error("❌ Senha incorreta!")
    else:
        st.info("📭 Nenhuma ocorrência registrada.")

# ============================================================================
# PÁGINA: GRÁFICOS E INDICADORES
# ============================================================================

elif menu == "📈 Gráficos e Indicadores":
    st.title("📈 Gráficos e Indicadores")
    
    df_ocorrencias = carregar_ocorrencias()
    
    if not df_ocorrencias.empty:
        st.subheader("🔍 Filtros")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filtro_periodo = st.selectbox("Período", ["Todos", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Este ano", "Personalizado"])
        
        with col2:
            filtro_turma = st.multiselect("Turma", df_ocorrencias['turma'].unique().tolist())
        
        with col3:
            filtro_gravidade = st.multiselect("Gravidade", ["Gravíssima", "Grave", "Média", "Leve"])
        
        with col4:
            filtro_categoria = st.multiselect("Categoria", df_ocorrencias['categoria'].unique().tolist())
        
        if filtro_periodo == "Personalizado":
            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input("Data Início")
            with col2:
                data_fim = st.date_input("Data Fim")
        
        df_filtrado = df_ocorrencias.copy()
        
        if filtro_periodo == "Últimos 7 dias":
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[df_filtrado['data_dt'] >= (datetime.now() - timedelta(days=7))]
        elif filtro_periodo == "Últimos 30 dias":
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[df_filtrado['data_dt'] >= (datetime.now() - timedelta(days=30))]
        elif filtro_periodo == "Este mês":
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[
                (df_filtrado['data_dt'].dt.month == datetime.now().month) &
                (df_filtrado['data_dt'].dt.year == datetime.now().year)
            ]
        elif filtro_periodo == "Este ano":
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[df_filtrado['data_dt'].dt.year == datetime.now().year]
        elif filtro_periodo == "Personalizado":
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[
                (df_filtrado['data_dt'] >= pd.Timestamp(data_inicio)) &
                (df_filtrado['data_dt'] <= pd.Timestamp(data_fim) + pd.Timedelta(days=1))
            ]
        
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        
        if filtro_gravidade:
            df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(filtro_gravidade)]
        
        if filtro_categoria:
            df_filtrado = df_filtrado[df_filtrado['categoria'].isin(filtro_categoria)]
        
        st.markdown("---")
        st.subheader("📊 Ocorrências por Categoria")
        
        if not df_filtrado.empty and 'categoria' in df_filtrado.columns:
            contagem_cats = df_filtrado['categoria'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
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
            
            with col2:
                fig_barra = px.bar(
                    x=contagem_cats.values,
                    y=contagem_cats.index,
                    orientation='h',
                    title='Quantidade por Categoria',
                    color=contagem_cats.values,
                    color_continuous_scale='Reds'
                )
                fig_barra.update_layout(showlegend=False)
                st.plotly_chart(fig_barra, use_container_width=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚖️ Ocorrências por Gravidade (COLORIDO)")
            if not df_filtrado.empty and 'gravidade' in df_filtrado.columns:
                contagem_grav = df_filtrado['gravidade'].value_counts()
                fig_grav = px.bar(
                    contagem_grav,
                    x=contagem_grav.index,
                    y=contagem_grav.values,
                    title='Por Gravidade',
                    color=contagem_grav.index,
                    color_discrete_map={
                        'Leve': '#4CAF50',
                        'Grave': '#FF9800',
                        'Gravíssima': '#F44336'
                    },
                    labels={'y': 'Quantidade', 'x': 'Gravidade'}
                )
                fig_grav.update_layout(showlegend=False)
                st.plotly_chart(fig_grav, use_container_width=True)
        
        with col2:
            st.subheader("🥧 Ocorrências por Gravidade (PIZZA)")
            if not df_filtrado.empty and 'gravidade' in df_filtrado.columns:
                fig_pizza_grav = px.pie(
                    values=contagem_grav.values,
                    names=contagem_grav.index,
                    title='Distribuição por Gravidade (%)',
                    color_discrete_map={
                        'Leve': '#4CAF50',
                        'Grave': '#FF9800',
                        'Gravíssima': '#F44336'
                    },
                    hole=0.3
                )
                fig_pizza_grav.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pizza_grav, use_container_width=True)
        
        st.markdown("---")
        
        st.subheader("📈 Evolução Temporal das Ocorrências")
        if not df_filtrado.empty and 'data' in df_filtrado.columns:
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado['data_apenas'] = df_filtrado['data_dt'].dt.date
            evolucao = df_filtrado.groupby('data_apenas').size().reset_index(name='Quantidade')
            evolucao = evolucao.sort_values('data_apenas')
            fig_evolucao = px.line(
                evolucao,
                x='data_apenas',
                y='Quantidade',
                title='Evolução das Ocorrências',
                markers=True
            )
            fig_evolucao.update_layout(xaxis_title="Data", yaxis_title="Quantidade")
            st.plotly_chart(fig_evolucao, use_container_width=True)
        
        st.subheader("🏫 Top 10 Turmas com Mais Ocorrências")
        if not df_filtrado.empty and 'turma' in df_filtrado.columns:
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
            st.dataframe(
                df_filtrado[['data', 'aluno', 'turma', 'categoria', 'gravidade', 'professor']],
                use_container_width=True
            )
            
            csv = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button(
                label="📥 Baixar Dados Filtrados (CSV)",
                data=csv,
                file_name=f"ocorrencias_filtradas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("📭 Nenhuma ocorrência para gerar gráficos.")

# ============================================================================
# PÁGINA: IMPRIMIR PDF
# ============================================================================

elif menu == "🖨️ Imprimir PDF":
    st.title("🖨️ Gerar PDF")
    
    df_ocorrencias = carregar_ocorrencias()
    df_responsaveis = carregar_responsaveis()
    
    if not df_ocorrencias.empty:
        occ_sel = st.selectbox(
            "Selecione a Ocorrência",
            (df_ocorrencias["id"].astype(str) + " - " + df_ocorrencias["aluno"] + " - " + df_ocorrencias["data"]).tolist()
        )
        
        if occ_sel:
            id_occ = int(occ_sel.split(" - ")[0])
            ocorrencia = df_ocorrencias[df_ocorrencias['id'] == id_occ].iloc[0].to_dict()
            
            st.subheader("📋 Dados da Ocorrência")
            st.write(f"**ID:** {ocorrencia.get('id')}")
            st.write(f"**Data:** {ocorrencia.get('data')}")
            st.write(f"**Aluno:** {ocorrencia.get('aluno')}")
            st.write(f"**RA:** {ocorrencia.get('ra')}")
            st.write(f"**Turma:** {ocorrencia.get('turma')}")
            st.write(f"**Categoria:** {ocorrencia.get('categoria')}")
            st.write(f"**Gravidade:** {ocorrencia.get('gravidade')}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Gerar PDF da Ocorrência"):
                    pdf_buffer = gerar_pdf_ocorrencia(ocorrencia, df_responsaveis)
                    st.download_button(
                        label="📥 Baixar PDF",
                        data=pdf_buffer,
                        file_name=f"ocorrencia_{id_occ}.pdf",
                        mime="application/pdf"
                    )
            
            with col2:
                if st.button("📬 Gerar Comunicado aos Pais"):
                    pdf_buffer = gerar_pdf_comunicado(ocorrencia, df_responsaveis)
                    st.download_button(
                        label="📥 Baixar Comunicado",
                        data=pdf_buffer,
                        file_name=f"comunicado_{id_occ}.pdf",
                        mime="application/pdf"
                    )
    else:
        st.info("📭 Nenhuma ocorrência registrada.")

# ============================================================================
# PÁGINA: BACKUP DE DADOS
# ============================================================================

elif menu == "💾 Backup de Dados":
    st.title("💾 Backup de Dados")
    
    st.subheader("📥 Exportar Backup Completo")
    st.info("💡 O backup inclui todas as ocorrências, alunos, professores e responsáveis")
    
    if st.button("📊 Gerar Backup"):
        backup_data = {
            'ocorrencias': carregar_ocorrencias().to_dict('records'),
            'alunos': carregar_alunos().to_dict('records'),
            'professores': carregar_professores().to_dict('records'),
            'responsaveis': carregar_responsaveis().to_dict('records'),
            'data_backup': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        
        json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        st.download_button(
            label="📥 Baixar Backup JSON",
            data=json_str,
            file_name=f"backup_conviva_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )
        
        st.success("✅ Backup gerado com sucesso!")
    
    st.subheader("📤 Importar Backup")
    st.warning("⚠️ Esta ação irá substituir todos os dados atuais! Faça backup antes de importar.")
    
    arquivo_backup = st.file_uploader("Selecione o arquivo de backup", type=['json'])
    
    if arquivo_backup:
        if st.button("⚠️ Confirmar Importação"):
            try:
                backup_data = json.load(arquivo_backup)
                
                contagem_ocorrencias = 0
                contagem_alunos = 0
                contagem_professores = 0
                contagem_responsaveis = 0
                
                # CORREÇÃO: backup_data completo (não backup_)
                if 'ocorrencias' in backup_data:
                    for occ in backup_data['ocorrencias']:
                        if salvar_ocorrencia(occ)[0]:
                            contagem_ocorrencias += 1
                
                if 'alunos' in backup_data:
                    for aluno in backup_data['alunos']:
                        if salvar_aluno(aluno):
                            contagem_alunos += 1
                
                if 'professores' in backup_data:
                    for prof in backup_data['professores']:
                        if salvar_professor(prof):
                            contagem_professores += 1
                
                if 'responsaveis' in backup_data:
                    for resp in backup_data['responsaveis']:
                        if salvar_responsavel(resp):
                            contagem_responsaveis += 1
                
                st.success(f"""
                ✅ Backup importado com sucesso!
                - Ocorrências: {contagem_ocorrencias}
                - Alunos: {contagem_alunos}
                - Professores: {contagem_professores}
                - Responsáveis: {contagem_responsaveis}
                """)
                
                carregar_ocorrencias.clear()
                carregar_alunos.clear()
                carregar_professores.clear()
                carregar_responsaveis.clear()
                
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao importar: {str(e)}")

# ============================================================================
# PÁGINA: CONFIGURAÇÕES
# ============================================================================

elif menu == "⚙️ Configurações":
    st.title("⚙️ Configurações")
    
    st.subheader("🏫 Dados da Escola")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Nome da Escola", ESCOLA_NOME)
        st.text_input("Endereço", ESCOLA_ENDERECO)
    
    with col2:
        st.text_input("Telefone", ESCOLA_TELEFONE)
        st.text_input("Email", ESCOLA_EMAIL)
    
    st.subheader("🔐 Configurações de Segurança")
    st.info(f"Senha para exclusão: {SENHA_EXCLUSAO}")
    
    st.subheader("📊 Protocolo 179")
    st.write(f"**Total de Categorias:** {sum(len(v) for v in CATEGORIAS_OCORRENCIAS.values())}")
    st.write(f"**Níveis de Gravidade:** Gravíssima, Grave, Média, Leve")
    
    st.subheader("💾 Informações do Sistema")
    st.write(f"**Versão:** 7.0")
    st.write(f"**Banco de Dados:** Supabase")
    st.write(f"**Framework:** Streamlit")

# ============================================================================
# RODAPÉ
# ============================================================================

st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p><strong>{ESCOLA_NOME}</strong></p>
    <p>{ESCOLA_ENDERECO}</p>
    <p>{ESCOLA_TELEFONE} | {ESCOLA_EMAIL}</p>
    <p>Sistema Conviva 179 - Protocolo de Convivência e Proteção Escolar</p>
    <p>Desenvolvido para SEDUC/SP - Versão 7.0</p>
    <p>© 2025 - Todos os direitos reservados</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# FIM DO CÓDIGO
# ============================================================================