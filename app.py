# ============================================================================
# SISTEMA CONVIVA 179 - GESTÃO DE OCORRÊNCIAS ESCOLARES
# Versão: 3.0.0 (Completo com Todas as Correções)
# Desenvolvido para SEDUC/SP - Protocolo de Convivência e Proteção Escolar
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
        'Get Help': 'https://github.com/SeuUsuario/SistemaConviva',
        'Report a bug': 'https://github.com/SeuUsuario/SistemaConviva/issues',
        'About': "# Sistema Conviva 179\nVersão 3.0.0\nDesenvolvido para SEDUC/SP"
    }
)

# ============================================================================
# CONFIGURAÇÃO DO SUPABASE (VIA REQUESTS API)
# ============================================================================

# URLs e chaves do Supabase (configurar no .streamlit/secrets.toml)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    SUPABASE_URL = ""
    SUPABASE_KEY = ""

# Headers para requisições API
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

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
    "📋 Outros": {
        "Acidentes e Eventos Inesperados": "Grave",
        "Atos Obscenos / Atos Libidinosos": "Leve",
        "Uso Inadequado de Dispositivos Eletrônicos": "Leve",
        "Copiar atividades / Colar em avaliações": "Leve",
        "Falsificar assinatura de responsáveis": "Média",
        "Indisciplina": "Leve",
        "Outros": "Leve"
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
    "📋 Outros": "#9E9E9E"
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
    margin: 0.5rem 0;
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

# ============================================================================
# FUNÇÕES DE BANCO DE DADOS (SUPABASE VIA REQUESTS)
# ============================================================================

@st.cache_data(ttl=60)
def carregar_alunos():
    """
    Carrega todos os alunos do banco de dados Supabase.
    
    Returns:
        DataFrame com dados dos alunos ou DataFrame vazio em caso de erro
    """
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/alunos?select=*&order=nome.asc",
            headers=HEADERS
        )
        response.raise_for_status()
        df = pd.DataFrame(response.json())
        if not df.empty:
            # CORREÇÃO: Ordenar alunos por nome
            df = df.sort_values('nome').reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar alunos: {str(e)}")
        return pd.DataFrame(columns=['ra', 'nome', 'data_nascimento', 'situacao', 'turma', 'genero', 'foto_url'])


@st.cache_data(ttl=60)
def carregar_professores():
    """
    Carrega todos os professores do banco de dados Supabase.
    
    Returns:
        DataFrame com dados dos professores ou DataFrame vazio em caso de erro
    """
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/professores?select=*&order=nome.asc",
            headers=HEADERS
        )
        response.raise_for_status()
        df = pd.DataFrame(response.json())
        if not df.empty:
            # CORREÇÃO: Ordenar professores por nome
            df = df.sort_values('nome').reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar professores: {str(e)}")
        return pd.DataFrame(columns=['nome', 'email', 'cargo', 'foto_url'])


@st.cache_data(ttl=60)
def carregar_responsaveis():
    """
    Carrega todos os responsáveis ativos do banco de dados.
    
    Returns:
        DataFrame com dados dos responsáveis ou DataFrame vazio em caso de erro
    """
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
    """
    Carrega todas as ocorrências do banco de dados.
    
    Returns:
        DataFrame com dados das ocorrências ou DataFrame vazio em caso de erro
    """
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


def salvar_aluno(aluno_dict):
    """
    Salva um aluno no banco de dados.
    
    Args:
        aluno_dict: Dicionário com dados do aluno
    
    Returns:
        bool: True se salvo com sucesso, False caso contrário
    """
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
    """
    Salva um professor no banco de dados.
    
    Args:
        professor_dict: Dicionário com dados do professor
    
    Returns:
        bool: True se salvo com sucesso, False caso contrário
    """
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
    """
    Salva um responsável no banco de dados.
    
    Args:
        responsavel_dict: Dicionário com dados do responsável
    
    Returns:
        bool: True se salvo com sucesso, False caso contrário
    """
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


def salvar_ocorrencia(ocorrencia_dict):
    """
    Salva uma ocorrência no banco de dados.
    
    Args:
        ocorrencia_dict: Dicionário com dados da ocorrência
    
    Returns:
        tuple: (sucesso, mensagem)
    """
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
    """
    Atualiza uma ocorrência no banco de dados.
    
    Args:
        id_ocorrencia: ID da ocorrência a atualizar
        ocorrencia_dict: Dicionário com dados atualizados
    
    Returns:
        tuple: (sucesso, mensagem)
    """
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
    """
    Exclui uma ocorrência do banco de dados.
    
    Args:
        id_ocorrencia: ID da ocorrência a excluir
    
    Returns:
        tuple: (sucesso, mensagem)
    """
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
    """
    Atualiza dados de um aluno.
    
    Args:
        ra: RA do aluno
        dados: Dicionário com dados a atualizar
    
    Returns:
        bool: True se atualizado com sucesso, False caso contrário
    """
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
    """
    Exclui todos os alunos de uma turma.
    
    Args:
        turma: Nome da turma
    
    Returns:
        bool: True se excluído com sucesso, False caso contrário
    """
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
    """
    Exclui um professor do banco de dados.
    
    Args:
        id_prof: ID do professor
    
    Returns:
        bool: True se excluído com sucesso, False caso contrário
    """
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
    """
    Exclui um responsável do banco de dados.
    
    Args:
        id_resp: ID do responsável
    
    Returns:
        bool: True se excluído com sucesso, False caso contrário
    """
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
    """
    Atualiza dados de um responsável.
    
    Args:
        id_resp: ID do responsável
        dados: Dicionário com dados a atualizar
    
    Returns:
        bool: True se atualizado com sucesso, False caso contrário
    """
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


def verificar_ocorrencia_duplicada(ra, categoria, data, df_ocorrencias):
    """
    Verifica se já existe uma ocorrência duplicada.
    
    Args:
        ra: RA do aluno
        categoria: Categoria da ocorrência
        data: Data da ocorrência
        df_ocorrencias: DataFrame com ocorrências
    
    Returns:
        bool: True se duplicada, False caso contrário
    """
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
    """
    Faz upload de foto para o Supabase Storage.
    
    Args:
        file: Arquivo de imagem
        folder: Pasta no storage (alunos ou professores)
        filename: Nome do arquivo
    
    Returns:
        tuple: (url_publica, mensagem)
    """
    try:
        file_bytes = file.getvalue()
        
        # Upload para o storage
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
            # Obter URL pública
            url_publica = f"{SUPABASE_URL}/storage/v1/object/public/fotos/{folder}/{filename}"
            return url_publica, "Foto enviada com sucesso!"
        else:
            return None, f"Erro ao enviar foto: {response.text}"
    except Exception as e:
        return None, f"Erro ao enviar foto: {str(e)}"


def atualizar_foto_aluno(ra, foto_url):
    """
    Atualiza a foto de um aluno no banco de dados.
    
    Args:
        ra: RA do aluno
        foto_url: URL da foto
    
    Returns:
        bool: True se atualizado com sucesso, False caso contrário
    """
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
    """
    Atualiza a foto de um professor no banco de dados.
    
    Args:
        nome: Nome do professor
        foto_url: URL da foto
    
    Returns:
        bool: True se atualizado com sucesso, False caso contrário
    """
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
    """
    Gera PDF da ocorrência com formatação profissional.
    
    Args:
        ocorrencia: Dicionário com dados da ocorrência
        df_responsaveis: DataFrame com responsáveis para assinatura
    
    Returns:
        BytesIO: Buffer com o PDF gerado
    """
    buffer = io.BytesIO()
    
    # CORREÇÃO: Margens reduzidas para caber mais conteúdo
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    elementos = []
    estilos = getSampleStyleSheet()
    
    # Estilos personalizados
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
    
    # CORREÇÃO: Converter <br> para quebras reais no texto
    def formatar_texto(texto):
        if texto:
            return texto.replace('<br>', '<br/>').replace('\n', '<br/>')
        return ""
    
    # Cabeçalho
    elementos.append(Paragraph("📋 REGISTRO DE OCORRÊNCIA - PROTOCOLO 179", estilos['Titulo']))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Dados da ocorrência
    elementos.append(Paragraph("<b>ID:</b> " + str(ocorrencia.get('id', 'N/A')), estilos['Texto']))
    elementos.append(Paragraph("<b>Data:</b> " + str(ocorrencia.get('data', 'N/A')), estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Dados do aluno
    elementos.append(Paragraph("<b>ESTUDANTE:</b>", estilos['Secao']))
    elementos.append(Paragraph("<b>Nome:</b> " + str(ocorrencia.get('aluno', 'N/A')), estilos['Texto']))
    elementos.append(Paragraph("<b>RA:</b> " + str(ocorrencia.get('ra', 'N/A')), estilos['Texto']))
    elementos.append(Paragraph("<b>Turma:</b> " + str(ocorrencia.get('turma', 'N/A')), estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Dados da ocorrência
    elementos.append(Paragraph("<b>OCORRÊNCIA:</b>", estilos['Secao']))
    elementos.append(Paragraph("<b>Categoria:</b> " + str(ocorrencia.get('categoria', 'N/A')), estilos['Texto']))
    
    # Badge de gravidade colorida
    gravidade = ocorrencia.get('gravidade', 'N/A')
    cor_gravidade = CORES_GRAVIDADE.get(gravidade, '#9E9E9E')
    elementos.append(Paragraph(
        f"<b>Gravidade:</b> <font color='{cor_gravidade}'><b>{gravidade}</b></font>",
        estilos['Texto']
    ))
    
    elementos.append(Spacer(1, 0.3*cm))
    
    # Relato
    elementos.append(Paragraph("<b>Relato:</b>", estilos['Secao']))
    relato_formatado = formatar_texto(ocorrencia.get('relato', ''))
    elementos.append(Paragraph(relato_formatado, estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Encaminhamentos
    elementos.append(Paragraph("<b>Encaminhamentos:</b>", estilos['Secao']))
    encaminhamentos = ocorrencia.get('encaminhamentos', [])
    if isinstance(encaminhamentos, list):
        for enc in encaminhamentos:
            elementos.append(Paragraph(f"• {enc}", estilos['Texto']))
    else:
        elementos.append(Paragraph(formatar_texto(str(encaminhamentos)), estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Professor
    elementos.append(Paragraph("<b>Professor Responsável:</b> " + str(ocorrencia.get('professor', 'N/A')), estilos['Texto']))
    
    # Testemunhas
    if ocorrencia.get('testemunhas'):
        elementos.append(Paragraph("<b>Testemunhas:</b> " + str(ocorrencia.get('testemunhas', '')), estilos['Texto']))
    
    elementos.append(Spacer(1, 0.5*cm))
    
    # Assinaturas - CORREÇÃO: Suporte para múltiplos CGPG/Vice-Diretoras
    elementos.append(Paragraph("<b>ASSINATURAS:</b>", estilos['Secao']))
    
    # Buscar responsáveis no banco
    cargos_para_assinatura = ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)", "Professor Responsável"]
    
    if df_responsaveis is not None and not df_responsaveis.empty:
        for cargo in cargos_para_assinatura:
            if cargo == "Professor Responsável":
                nome = ocorrencia.get("professor", "")
                if nome:
                    elementos.append(Paragraph(f"<b>{cargo}:</b> {nome}", estilos['Texto']))
            else:
                # Buscar responsável pelo cargo
                responsavel = df_responsaveis[df_responsaveis['cargo'] == cargo]
                if not responsavel.empty and responsavel.iloc[0].get('nome'):
                    nome_resp = responsavel.iloc[0].get('nome', '')
                    elementos.append(Paragraph(f"<b>{cargo}:</b> {nome_resp}", estilos['Texto']))
                else:
                    elementos.append(Paragraph(f"<b>{cargo}:</b> _________________________________", estilos['Texto']))
    else:
        for cargo in cargos_para_assinatura:
            if cargo == "Professor Responsável":
                nome = ocorrencia.get("professor", "")
                if nome:
                    elementos.append(Paragraph(f"<b>{cargo}:</b> {nome}", estilos['Texto']))
            else:
                elementos.append(Paragraph(f"<b>{cargo}:</b> _________________________________", estilos['Texto']))
    
    elementos.append(Spacer(1, 0.5*cm))
    
    # Ciência dos pais
    elementos.append(Paragraph("<b>CIÊNCIA DOS PAIS/RESPONSÁVEIS:</b>", estilos['Secao']))
    elementos.append(Paragraph("Declaro ciência deste comunicado.", estilos['Texto']))
    elementos.append(Spacer(1, 1*cm))
    
    # Linha de assinatura
    elementos.append(Paragraph("_" * 50, estilos['Normal']))
    elementos.append(Paragraph("Assinatura do Responsável", estilos['Assinatura']))
    
    # Rodapé
    elementos.append(Spacer(1, 0.5*cm))
    estilo_rodape = ParagraphStyle(
        'Rodape',
        parent=estilos['Normal'],
        fontSize=6,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    elementos.append(Paragraph("_" * 75, estilos['Normal']))
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer


def gerar_pdf_comunicado(ocorrencia, df_responsaveis=None):
    """
    Gera PDF de comunicado aos pais.
    
    Args:
        ocorrencia: Dicionário com dados da ocorrência
        df_responsaveis: DataFrame com responsáveis
    
    Returns:
        BytesIO: Buffer com o PDF gerado
    """
    buffer = io.BytesIO()
    
    # CORREÇÃO: Margens reduzidas
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
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
    
    # Cabeçalho
    elementos.append(Paragraph("📬 COMUNICADO AOS PAIS/RESPONSÁVEIS", estilos['TituloComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Saudação
    elementos.append(Paragraph(
        f"Prezados responsáveis pelo(a) estudante <b>{ocorrencia.get('aluno', 'N/A')}</b>,",
        estilos['Texto']
    ))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Corpo do comunicado
    elementos.append(Paragraph(
        "Venho por meio deste comunicar que foi registrado uma ocorrência disciplinar conforme detalhes abaixo:",
        estilos['Texto']
    ))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Detalhes
    elementos.append(Paragraph(f"<b>Data:</b> {ocorrencia.get('data', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Turma:</b> {ocorrencia.get('turma', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Categoria:</b> {ocorrencia.get('categoria', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Gravidade:</b> {ocorrencia.get('gravidade', 'N/A')}", estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>Relato:</b>", estilos['Secao']))
    elementos.append(Paragraph(str(ocorrencia.get('relato', '')), estilos['Texto']))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Encaminhamentos
    elementos.append(Paragraph("<b>Encaminhamentos Realizados:</b>", estilos['Secao']))
    encaminhamentos = ocorrencia.get('encaminhamentos', [])
    if isinstance(encaminhamentos, list):
        for enc in encaminhamentos:
            elementos.append(Paragraph(f"• {enc}", estilos['Texto']))
    else:
        elementos.append(Paragraph(str(encaminhamentos), estilos['Texto']))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Solicitação de ciência
    elementos.append(Paragraph(
        "Solicitamos que tomem conhecimento e compareçam à escola para assinatura deste comunicado.",
        estilos['Texto']
    ))
    elementos.append(Spacer(1, 1*cm))
    
    # Assinatura
    elementos.append(Paragraph(f"Atenciosamente,", estilos['Texto']))
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("_" * 50, estilos['Normal']))
    elementos.append(Paragraph("Direção / Coordenação", estilos['Assinatura']))
    
    # Ciência
    elementos.append(Spacer(1, 1*cm))
    elementos.append(Paragraph("<b>CIÊNCIA:</b>", estilos['Secao']))
    elementos.append(Paragraph("Declaro que recebi e tomei conhecimento deste comunicado.", estilos['Texto']))
    elementos.append(Spacer(1, 1*cm))
    elementos.append(Paragraph("_" * 50, estilos['Normal']))
    elementos.append(Paragraph("Assinatura do Responsável", estilos['Assinatura']))
    
    # Rodapé
    elementos.append(Spacer(1, 0.5*cm))
    estilo_rodape = ParagraphStyle(
        'Rodape',
        parent=estilos['Normal'],
        fontSize=6,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    elementos.append(Paragraph("_" * 75, estilos['Normal']))
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer


# ============================================================================
# INTERFACE PRINCIPAL - CABEÇALHO E MENU
# ============================================================================

# Cabeçalho principal
st.markdown("""
<div class="main-header">
    <div class="school-name">🏫 SISTEMA CONVIVA 179</div>
    <div class="school-subtitle">Gestão de Ocorrências Escolares</div>
    <div class="school-address">Protocolo de Convivência e Proteção Escolar - SEDUC/SP</div>
    <div class="school-contact">Versão 3.0.0 | Última atualização: 2025</div>
</div>
""", unsafe_allow_html=True)

# Menu lateral
menu = st.sidebar.selectbox(
    "📋 Menu Principal",
    [
        "🏠 Home",
        "📝 Registrar Ocorrência",
        "📊 Lista de Ocorrências",
        "👥 Alunos",
        "👨‍🏫 Professores",
        "👤 Responsáveis",
        "📈 Gráficos",
        "🖨️ Relatórios",
        "⚙️ Configurações",
        "💾 Backup"
    ],
    index=0
)

st.session_state.pagina_atual = menu

# ============================================================================
# PÁGINA: HOME / DASHBOARD
# ============================================================================

if menu == "🏠 Home":
    st.title("🏠 Dashboard")
    
    # Carregar dados
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    
    if not df_ocorrencias.empty:
        # Calcular métricas
        total_ocorrencias = len(df_ocorrencias)
        total_gravissima = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Gravíssima'])
        total_grave = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Grave'])
        total_media = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Média'])
        total_leve = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Leve'])
        turmas_afetadas = df_ocorrencias['turma'].nunique() if 'turma' in df_ocorrencias.columns else 0
        
        # Cards de métricas
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #D32F2F 0%, #B71C1C 100%);">
                <div class="metric-value">{total_gravissima}</div>
                <div class="metric-label">Gravíssimas</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #F57C00 0%, #E65100 100%);">
                <div class="metric-value">{total_grave}</div>
                <div class="metric-label">Graves</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #FFB300 0%, #FF8F00 100%);">
                <div class="metric-value">{total_media}</div>
                <div class="metric-label">Médias</div>
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
        
        # Gráficos
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
                    color_continuous_scale='Reds',
                    labels={'x': 'Quantidade', 'y': 'Categoria'}
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
        
        # Últimas ocorrências
        st.subheader("📋 Últimas Ocorrências")
        st.dataframe(df_ocorrencias.head(10), use_container_width=True)
        
    else:
        st.info("📭 Nenhuma ocorrência registrada ainda.")
    
    # Resumo de alunos
    if not df_alunos.empty:
        st.subheader("👥 Resumo de Alunos")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Alunos", len(df_alunos))
        with col2:
            st.metric("Total de Turmas", df_alunos['turma'].nunique())

# ============================================================================
# PÁGINA: REGISTRAR OCORRÊNCIA
# ============================================================================

elif menu == "📝 Registrar Ocorrência":
    st.title("📝 Registrar Nova Ocorrência")
    
    # Mostrar mensagem de sucesso se ocorreu
    if st.session_state.ocorrencia_salva_sucesso:
        st.markdown('<div class="success-box">✅ OCORRÊNCIA(S) REGISTRADA(S) COM SUCESSO!</div>', unsafe_allow_html=True)
        st.session_state.ocorrencia_salva_sucesso = False
        st.session_state.salvando_ocorrencia = False
        st.session_state.gravidade_alterada = False
        st.session_state.adicionar_outra_infracao = False
        st.session_state.infracoes_adicionais = []
    
    # Carregar alunos
    df_alunos = carregar_alunos()
    
    if df_alunos.empty:
        st.warning("⚠️ Importe alunos primeiro.")
    else:
        # Horário de São Paulo
        tz_sp = pytz.timezone('America/Sao_Paulo')
        data_hora_sp = datetime.now(tz_sp)
        
        # Seleção de turma
        turmas = df_alunos["turma"].unique().tolist()
        turma_sel = st.selectbox("🏫 Turma", turmas)
        
        # Filtrar alunos da turma
        alunos = df_alunos[df_alunos["turma"] == turma_sel]
        
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
                    # CORREÇÃO: Busca fuzzy para alunos
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
            
            # Dados da ocorrência
            st.markdown("### 📋 Dados da Ocorrência")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CORREÇÃO: Listener para atualizar gravidade automaticamente
                categoria_grupo = st.selectbox("📁 Categoria", list(CATEGORIAS_OCORRENCIAS.keys()))
                categorias_grupo = list(CATEGORIAS_OCORRENCIAS[categoria_grupo].keys())
                categoria = st.selectbox("📋 Ocorrência", categorias_grupo)
            
            with col2:
                # Gravidade automática baseada na categoria
                gravidade = CATEGORIAS_OCORRENCIAS[categoria_grupo].get(categoria, "Leve")
                gravidade_select = st.selectbox(
                    "⚡ Gravidade",
                    ["Gravíssima", "Grave", "Média", "Leve"],
                    index=["Gravíssima", "Grave", "Média", "Leve"].index(gravidade)
                )
            
            # CORREÇÃO: Mostrar fluxo de ações do protocolo 179
            if categoria in FLUXO_ACOES:
                st.warning(f"📌 {FLUXO_ACOES[categoria]}")
            
            # Relato
            relato = st.text_area("📝 Relato da Ocorrência", height=200)
            
            # CORREÇÃO: Encaminhamentos como checkboxes baseados no protocolo
            st.subheader("🔄 Encaminhamentos")
            encaminhamentos_disponiveis = ENCAMINHAMENTOS_POR_GRAVIDADE.get(gravidade_select, [])
            encaminhamentos_selecionados = st.multiselect(
                "Selecione os encaminhamentos realizados",
                encaminhamentos_disponiveis,
                default=encaminhamentos_disponiveis  # Já seleciona todos por padrão
            )
            
            # Testemunhas
            testemunhas = st.text_input("👀 Testemunhas (opcional)")
            
            # Evidências
            evidencias = st.text_area("📎 Evidências (opcional)")
            
            # Opção de adicionar outra infração
            st.markdown("---")
            adicionar_outra = st.checkbox("➕ Adicionar outra infração para o(s) mesmo(s) estudante(s)")
            
            # Botão salvar com prevenção de múltiplos cliques
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
                            
                            if verificar_ocorrencia_duplicada(ra_aluno, categoria_str, data_str, df_ocorrencias):
                                contagem_duplicadas += 1
                            else:
                                ocorrencia_dict = {
                                    'data': data_str,
                                    'aluno': nome_aluno,
                                    'ra': ra_aluno,
                                    'turma': turma_sel,
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
            st.warning("⚠️ Não há alunos nesta turma.")

# ============================================================================
# PÁGINA: LISTA DE OCORRÊNCIAS
# ============================================================================

elif menu == "📊 Lista de Ocorrências":
    st.title("📊 Lista de Ocorrências")
    
    df_ocorrencias = carregar_ocorrencias()
    
    if not df_ocorrencias.empty:
        # Filtros avançados
        st.subheader("🔍 Filtros")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filtro_gravidade = st.multiselect(
                "Gravidade",
                ["Gravíssima", "Grave", "Média", "Leve"]
            )
        
        with col2:
            filtro_categoria = st.multiselect(
                "Categoria",
                df_ocorrencias['categoria'].unique().tolist()
            )
        
        with col3:
            filtro_turma = st.multiselect(
                "Turma",
                df_ocorrencias['turma'].unique().tolist()
            )
        
        with col4:
            filtro_periodo = st.selectbox(
                "Período",
                ["Todos", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Este ano"]
            )
        
        # Aplicar filtros
        df_filtrado = df_ocorrencias.copy()
        
        if filtro_gravidade:
            df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(filtro_gravidade)]
        
        if filtro_categoria:
            df_filtrado = df_filtrado[df_filtrado['categoria'].isin(filtro_categoria)]
        
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        
        # Filtro de período
        if filtro_periodo != "Todos":
            df_filtrado['data_dt'] = pd.to_datetime(
                df_filtrado['data'],
                format='%d/%m/%Y %H:%M',
                errors='coerce'
            )
            
            if filtro_periodo == "Últimos 7 dias":
                df_filtrado = df_filtrado[df_filtrado['data_dt'] >= (datetime.now() - timedelta(days=7))]
            elif filtro_periodo == "Últimos 30 dias":
                df_filtrado = df_filtrado[df_filtrado['data_dt'] >= (datetime.now() - timedelta(days=30))]
        
        # Exibir dados filtrados
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Ações
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
        
        # Excluir ocorrência
        st.markdown("---")
        st.subheader("🗑️ Excluir Ocorrência")
        
        senha = st.text_input("🔒 Senha para Excluir", type="password", value="", key="senha_excluir")
        
        if st.button("🗑️ Excluir Ocorrência"):
            if senha == "040600":
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
# PÁGINA: ALUNOS
# ============================================================================

elif menu == "👥 Alunos":
    st.title("👥 Gerenciamento de Alunos")
    
    # Importação CSV
    st.subheader("📥 Importar Alunos (CSV)")
    st.info("💡 O arquivo CSV deve ter as colunas: ra, nome, data_nascimento, situacao, turma, genero")
    
    arquivo_csv = st.file_uploader("Selecione o arquivo CSV", type=['csv'])
    
    if arquivo_csv:
        try:
            df_import = pd.read_csv(arquivo_csv)
            st.write(f"📊 {len(df_import)} alunos encontrados")
            st.dataframe(df_import.head())
            
            # CORREÇÃO: Validação de nomes duplicados
            if st.button("✅ Confirmar Importação"):
                contagem_salvas = 0
                contagem_duplicadas = 0
                erros = 0
                
                df_alunos_existentes = carregar_alunos()
                
                for _, row in df_import.iterrows():
                    aluno_dict = row.to_dict()
                    
                    # Verificar duplicação por RA
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
                
                # CORREÇÃO: Clear cache após importação
                carregar_alunos.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao importar: {str(e)}")
    
    # Upload de foto de aluno
    st.subheader("📷 Upload de Foto de Aluno")
    
    df_alunos = carregar_alunos()
    
    if not df_alunos.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            aluno_foto = st.selectbox("Selecione o Aluno", df_alunos['nome'].tolist())
            ra_aluno = df_alunos[df_alunos['nome'] == aluno_foto]['ra'].values[0]
        
        with col2:
            foto_file = st.file_uploader("Selecione a foto", type=['jpg', 'jpeg', 'png'])
        
        if foto_file and st.button("📷 Enviar Foto"):
            url, msg = upload_foto_supabase(foto_file, 'alunos', f"{ra_aluno}.jpg")
            if url:
                if atualizar_foto_aluno(ra_aluno, url):
                    st.success(f"✅ {msg}")
                    # CORREÇÃO: Clear cache após upload
                    carregar_alunos.clear()
                    st.rerun()
                else:
                    st.error("❌ Erro ao atualizar foto no banco")
            else:
                st.error(f"❌ {msg}")
    
    # Lista de alunos
    st.subheader("📋 Alunos Cadastrados")
    
    if not df_alunos.empty:
        st.dataframe(df_alunos, use_container_width=True)
        
        # Exportar alunos
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
# PÁGINA: PROFESSORES
# ============================================================================

elif menu == "👨‍🏫 Professores":
    st.title("👨‍🏫 Gerenciamento de Professores")
    
    # CORREÇÃO: Importação de professores com botão igual aos alunos
    st.subheader("📥 Importar Professores (CSV)")
    st.info("💡 O arquivo CSV deve ter as colunas: nome, email, cargo")
    
    arquivo_csv = st.file_uploader("Selecione o arquivo CSV", type=['csv'], key="prof_csv")
    
    if arquivo_csv:
        try:
            df_import = pd.read_csv(arquivo_csv)
            st.write(f"📊 {len(df_import)} professores encontrados")
            st.dataframe(df_import.head())
            
            if st.button("✅ Confirmar Importação", key="prof_import"):
                contagem_salvas = 0
                erros = 0
                
                for _, row in df_import.iterrows():
                    professor_dict = row.to_dict()
                    if salvar_professor(professor_dict):
                        contagem_salvas += 1
                    else:
                        erros += 1
                
                if contagem_salvas > 0:
                    st.success(f"✅ {contagem_salvas} professor(es) importado(s) com sucesso!")
                if erros > 0:
                    st.error(f"❌ {erros} erro(s) ao importar")
                
                # CORREÇÃO: Clear cache após importação
                carregar_professores.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao importar: {str(e)}")
    
    # CORREÇÃO: Upload de foto de professor
    st.subheader("📷 Upload de Foto de Professor")
    
    df_professores = carregar_professores()
    
    if not df_professores.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            professor_foto = st.selectbox("Selecione o Professor", df_professores['nome'].tolist())
        
        with col2:
            foto_file = st.file_uploader("Selecione a foto", type=['jpg', 'jpeg', 'png'], key="prof_foto")
        
        if foto_file and st.button("📷 Enviar Foto", key="prof_enviar_foto"):
            url, msg = upload_foto_supabase(foto_file, 'professores', f"{professor_foto}.jpg")
            if url:
                if atualizar_foto_professor(professor_foto, url):
                    st.success(f"✅ {msg}")
                    # CORREÇÃO: Clear cache após upload
                    carregar_professores.clear()
                    st.rerun()
                else:
                    st.error("❌ Erro ao atualizar foto no banco")
            else:
                st.error(f"❌ {msg}")
    
    # Lista de professores
    st.subheader("📋 Professores Cadastrados")
    
    if not df_professores.empty:
        st.dataframe(df_professores, use_container_width=True)
        
        # Excluir professor
        st.markdown("---")
        st.subheader("🗑️ Excluir Professor")
        
        prof_excluir = st.selectbox("Selecione o Professor", df_professores['nome'].tolist())
        id_prof_excluir = df_professores[df_professores['nome'] == prof_excluir]['id'].values[0] if 'id' in df_professores.columns else None
        
        if id_prof_excluir and st.button("🗑️ Excluir Professor"):
            if excluir_professor(id_prof_excluir):
                st.success("✅ Professor excluído com sucesso!")
                carregar_professores.clear()
                st.rerun()
            else:
                st.error("❌ Erro ao excluir professor")
    else:
        st.info("📭 Nenhum professor cadastrado.")

# ============================================================================
# PÁGINA: RESPONSÁVEIS
# ============================================================================

elif menu == "👤 Responsáveis":
    st.title("👤 Gerenciamento de Responsáveis (Assinaturas)")
    
    st.info("💡 Cadastre os responsáveis que assinarão os documentos (Diretor, Vice, CGPG, etc.)")
    
    # Cadastrar responsável
    st.subheader("📝 Cadastrar Responsável")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cargo = st.selectbox(
            "Cargo",
            ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)", "Orientador(a)"]
        )
    
    with col2:
        nome = st.text_input("Nome Completo")
    
    if st.button("💾 Salvar Responsável"):
        if nome:
            responsavel_dict = {
                'cargo': cargo,
                'nome': nome,
                'ativo': True
            }
            
            if salvar_responsavel(responsavel_dict):
                st.success("✅ Responsável cadastrado com sucesso!")
                carregar_responsaveis.clear()
                st.rerun()
            else:
                st.error("❌ Erro ao cadastrar responsável")
        else:
            st.error("❌ Preencha o nome!")
    
    # Lista de responsáveis
    st.subheader("📋 Responsáveis Cadastrados")
    
    df_responsaveis = carregar_responsaveis()
    
    if not df_responsaveis.empty:
        st.dataframe(df_responsaveis[['cargo', 'nome', 'ativo']], use_container_width=True)
        
        # Atualizar nome
        st.markdown("---")
        st.subheader("✏️ Atualizar Nome")
        
        col1, col2 = st.columns(2)
        
        with col1:
            resp_atualizar = st.selectbox(
                "Selecione o Responsável",
                df_responsaveis['cargo'].tolist()
            )
        
        with col2:
            novo_nome = st.text_input("Novo Nome")
        
        if st.button("✏️ Atualizar"):
            id_resp = df_responsaveis[df_responsaveis['cargo'] == resp_atualizar]['id'].values[0]
            if atualizar_responsavel(id_resp, {'nome': novo_nome}):
                st.success("✅ Nome atualizado com sucesso!")
                carregar_responsaveis.clear()
                st.rerun()
            else:
                st.error("❌ Erro ao atualizar")
    else:
        st.info("📭 Nenhum responsável cadastrado.")

# ============================================================================
# PÁGINA: GRÁFICOS
# ============================================================================

elif menu == "📈 Gráficos":
    st.title("📈 Gráficos e Estatísticas")
    
    df_ocorrencias = carregar_ocorrencias()
    
    if not df_ocorrencias.empty:
        # CORREÇÃO: Filtros avançados para gráficos
        st.subheader("🔍 Filtros")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filtro_periodo = st.selectbox(
                "Período",
                ["Todos", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Este ano", "Personalizado"]
            )
        
        with col2:
            filtro_turma = st.multiselect(
                "Turma",
                df_ocorrencias['turma'].unique().tolist()
            )
        
        with col3:
            filtro_gravidade = st.multiselect(
                "Gravidade",
                ["Gravíssima", "Grave", "Média", "Leve"]
            )
        
        with col4:
            filtro_categoria = st.multiselect(
                "Categoria",
                df_ocorrencias['categoria'].unique().tolist()
            )
        
        # Filtro de data personalizado
        if filtro_periodo == "Personalizado":
            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input("Data Início")
            with col2:
                data_fim = st.date_input("Data Fim")
        
        # Aplicar filtros de período
        df_filtrado = df_ocorrencias.copy()
        
        if filtro_periodo == "Últimos 7 dias":
            df_filtrado['data_dt'] = pd.to_datetime(
                df_filtrado['data'],
                format='%d/%m/%Y %H:%M',
                errors='coerce'
            )
            df_filtrado = df_filtrado[df_filtrado['data_dt'] >= (datetime.now() - timedelta(days=7))]
        elif filtro_periodo == "Últimos 30 dias":
            df_filtrado['data_dt'] = pd.to_datetime(
                df_filtrado['data'],
                format='%d/%m/%Y %H:%M',
                errors='coerce'
            )
            df_filtrado = df_filtrado[df_filtrado['data_dt'] >= (datetime.now() - timedelta(days=30))]
        elif filtro_periodo == "Este mês":
            df_filtrado['data_dt'] = pd.to_datetime(
                df_filtrado['data'],
                format='%d/%m/%Y %H:%M',
                errors='coerce'
            )
            df_filtrado = df_filtrado[
                (df_filtrado['data_dt'].dt.month == datetime.now().month) &
                (df_filtrado['data_dt'].dt.year == datetime.now().year)
            ]
        elif filtro_periodo == "Este ano":
            df_filtrado['data_dt'] = pd.to_datetime(
                df_filtrado['data'],
                format='%d/%m/%Y %H:%M',
                errors='coerce'
            )
            df_filtrado = df_filtrado[df_filtrado['data_dt'].dt.year == datetime.now().year]
        elif filtro_periodo == "Personalizado":
            df_filtrado['data_dt'] = pd.to_datetime(
                df_filtrado['data'],
                format='%d/%m/%Y %H:%M',
                errors='coerce'
            )
            df_filtrado = df_filtrado[
                (df_filtrado['data_dt'] >= pd.Timestamp(data_inicio)) &
                (df_filtrado['data_dt'] <= pd.Timestamp(data_fim) + pd.Timedelta(days=1))
            ]
        
        # Aplicar outros filtros
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        
        if filtro_gravidade:
            df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(filtro_gravidade)]
        
        if filtro_categoria:
            df_filtrado = df_filtrado[df_filtrado['categoria'].isin(filtro_categoria)]
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Por Categoria")
            if 'categoria' in df_filtrado.columns:
                cat_counts = df_filtrado['categoria'].value_counts()
                fig = px.bar(
                    x=cat_counts.index,
                    y=cat_counts.values,
                    color=cat_counts.index,
                    color_discrete_map=CORES_CATEGORIAS
                )
                fig.update_layout(
                    height=400,
                    showlegend=False,
                    xaxis_tickangle=-45,
                    title="Ocorrências por Categoria"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Por Gravidade")
            if 'gravidade' in df_filtrado.columns:
                grav_counts = df_filtrado['gravidade'].value_counts()
                fig = px.pie(
                    values=grav_counts.values,
                    names=grav_counts.index,
                    color=grav_counts.index,
                    color_discrete_map=CORES_GRAVIDADE
                )
                fig.update_layout(height=400, title="Ocorrências por Gravidade")
                st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de linha temporal
        st.subheader("📈 Evolução Temporal")
        if 'data' in df_filtrado.columns:
            df_filtrado['data_dt'] = pd.to_datetime(
                df_filtrado['data'],
                format='%d/%m/%Y %H:%M',
                errors='coerce'
            )
            df_filtrado['data_date'] = df_filtrado['data_dt'].dt.date
            temporal = df_filtrado.groupby('data_date').size().reset_index(name='count')
            fig = px.line(temporal, x='data_date', y='count', markers=True)
            fig.update_layout(height=400, title="Evolução das Ocorrências")
            st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico por turma
        st.subheader("📊 Por Turma")
        if 'turma' in df_filtrado.columns:
            turma_counts = df_filtrado['turma'].value_counts().head(10)
            fig = px.bar(
                x=turma_counts.index,
                y=turma_counts.values,
                color=turma_counts.values,
                color_continuous_scale='Oranges'
            )
            fig.update_layout(
                height=400,
                showlegend=False,
                xaxis_tickangle=-45,
                title="Top 10 Turmas com Mais Ocorrências"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico por gênero (se disponível)
        if 'genero' in df_ocorrencias.columns:
            st.subheader("📊 Por Gênero")
            df_alunos = carregar_alunos()
            if not df_alunos.empty and 'genero' in df_alunos.columns:
                genero_counts = df_alunos['genero'].value_counts()
                fig = px.pie(
                    values=genero_counts.values,
                    names=genero_counts.index,
                    title="Distribuição por Gênero"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("📭 Nenhuma ocorrência para gerar gráficos.")

# ============================================================================
# PÁGINA: RELATÓRIOS
# ============================================================================

elif menu == "🖨️ Relatórios":
    st.title("🖨️ Relatórios")
    
    df_ocorrencias = carregar_ocorrencias()
    
    if not df_ocorrencias.empty:
        st.subheader("📥 Exportar Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Exportar CSV"):
                csv = df_ocorrencias.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Baixar CSV",
                    data=csv,
                    file_name=f"ocorrencias_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📊 Exportar Excel"):
                buffer = io.BytesIO()
                df_ocorrencias.to_excel(buffer, index=False, engine='openpyxl')
                buffer.seek(0)
                st.download_button(
                    label="📥 Baixar Excel",
                    data=buffer,
                    file_name=f"ocorrencias_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        # Relatório por aluno
        st.subheader("📋 Relatório Individual por Aluno")
        df_alunos = carregar_alunos()
        
        if not df_alunos.empty:
            aluno_relatorio = st.selectbox("Selecione o Aluno", df_alunos['nome'].tolist())
            
            if st.button("📄 Gerar Relatório"):
                ocorrencias_aluno = df_ocorrencias[df_ocorrencias['aluno'] == aluno_relatorio]
                
                if not ocorrencias_aluno.empty:
                    st.write(f"**Total de ocorrências:** {len(ocorrencias_aluno)}")
                    st.dataframe(ocorrencias_aluno, use_container_width=True)
                    
                    # Gerar PDF do relatório
                    pdf_buffer = io.BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
                    elementos = []
                    estilos = getSampleStyleSheet()
                    
                    elementos.append(Paragraph(f"Relatório Individual - {aluno_relatorio}", estilos['Heading1']))
                    elementos.append(Spacer(1, 0.5*cm))
                    
                    for _, occ in ocorrencias_aluno.iterrows():
                        elementos.append(Paragraph(f"<b>Data:</b> {occ.get('data', 'N/A')}", estilos['Normal']))
                        elementos.append(Paragraph(f"<b>Categoria:</b> {occ.get('categoria', 'N/A')}", estilos['Normal']))
                        elementos.append(Paragraph(f"<b>Gravidade:</b> {occ.get('gravidade', 'N/A')}", estilos['Normal']))
                        elementos.append(Spacer(1, 0.3*cm))
                    
                    doc.build(elementos)
                    pdf_buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Baixar Relatório PDF",
                        data=pdf_buffer,
                        file_name=f"relatorio_{aluno_relatorio}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.info("📭 Nenhuma ocorrência para este aluno.")
    
    else:
        st.info("📭 Nenhuma ocorrência para gerar relatórios.")

# ============================================================================
# PÁGINA: CONFIGURAÇÕES
# ============================================================================

elif menu == "⚙️ Configurações":
    st.title("⚙️ Configurações")
    
    st.subheader("🏫 Dados da Escola")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Nome da Escola", "Escola Estadual")
        st.text_input("Endereço", "Rua Exemplo, 123")
    
    with col2:
        st.text_input("Telefone", "(11) 9999-9999")
        st.text_input("Email", "escola@educacao.sp.gov.br")
    
    st.subheader("🔐 Configurações de Segurança")
    st.info("Senha para exclusão: 040600")
    
    st.subheader("📊 Protocolo 179")
    st.write(f"**Total de Categorias:** {sum(len(v) for v in CATEGORIAS_OCORRENCIAS.values())}")
    st.write(f"**Níveis de Gravidade:** Gravíssima, Grave, Média, Leve")
    
    st.subheader("💾 Informações do Sistema")
    st.write(f"**Versão:** 3.0.0")
    st.write(f"**Banco de Dados:** Supabase")
    st.write(f"**Framework:** Streamlit")

# ============================================================================
# PÁGINA: BACKUP
# ============================================================================

elif menu == "💾 Backup":
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
                
                # Importar dados
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
                
                st.success(f"""
                ✅ Backup importado com sucesso!
                - Ocorrências: {contagem_ocorrencias}
                - Alunos: {contagem_alunos}
                - Professores: {contagem_professores}
                - Responsáveis: {contagem_responsaveis}
                """)
                
                # Clear cache
                carregar_ocorrencias.clear()
                carregar_alunos.clear()
                carregar_professores.clear()
                carregar_responsaveis.clear()
                
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao importar: {str(e)}")

# ============================================================================
# RODAPÉ
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>Sistema Conviva 179 - Protocolo de Convivência e Proteção Escolar</p>
    <p>Desenvolvido para SEDUC/SP - Versão 3.0.0</p>
    <p>© 2025 - Todos os direitos reservados</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# FIM DO CÓDIGO
# ============================================================================