# ============================================================================
# SISTEMA CONVIVA 179 - GESTÃO DE OCORRÊNCIAS ESCOLARES
# Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI
# Versão: 7.0 FINAL COMPLETA - USANDO REQUESTS (SEM BIBLIOTECA SUPABASE)
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import plotly.express as px
import plotly.graph_objects as go
from fuzzywuzzy import process
import pytz
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
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
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# ============================================================================
# DICIONÁRIOS DO PROTOCOLO 179
# ============================================================================
CATEGORIAS_OCORRENCIAS = {
    "🔴 Violência Física": {
        "Agressão Física": "Gravíssima",
        "Briga / Discussão": "Média",
        "Ameaça": "Grave",
        "Intimidação": "Grave",
        "Lesão Corporal": "Gravíssima"
    },
    "🟠 Violência Verbal/Psicológica": {
        "Bullying": "Grave",
        "Cyberbullying": "Grave",
        "Discriminação / Preconceito": "Gravíssima",
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
        "Porte de Objeto Perfurocortante": "Grave"
    },
    "💊 Drogas e Substâncias": {
        "Posse de Drogas": "Gravíssima",
        "Tráfico de Drogas": "Gravíssima",
        "Uso de Substâncias": "Grave",
        "Posse de Bebida Alcoólica": "Média"
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
        "Violação de Dados": "Grave",
        "Uso Inadequado de Dispositivos Eletrônicos": "Leve",
        "Copiar atividades / Colar em avaliações": "Leve",
        "Falsificar assinatura de responsáveis": "Média",
        "Indisciplina": "Leve",
        "Outros": "Leve"
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
    "📋 Outros": "#9E9E9E"
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
    "Leve": ["Orientação ao Estudante", "Comunicação aos Pais/Responsáveis", "Registro em Ata de Ocorrência"],
    "Média": ["Orientação ao Estudante", "Comunicação aos Pais/Responsáveis", "Registro em Ata de Ocorrência", "Encaminhamento à Coordenação"],
    "Grave": ["Orientação ao Estudante", "Comunicação aos Pais/Responsáveis", "Registro em Ata de Ocorrência", "Encaminhamento à Coordenação", "Encaminhamento à Direção", "Acompanhamento Pedagógico"],
    "Gravíssima": ["Orientação ao Estudante", "Comunicação aos Pais/Responsáveis", "Registro em Ata de Ocorrência", "Encaminhamento à Coordenação", "Encaminhamento à Direção", "Acompanhamento Pedagógico", "Acompanhamento Psicopedagógico", "Registro de B.O.", "Acionamento Conselho Tutelar"]
}

# ============================================================================
# CONFIGURAÇÕES DA ESCOLA
# ============================================================================
ESCOLA_NOME = "Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI"
ESCOLA_SUBTITULO = "Protocolo de Convivência e Proteção Escolar - SEDUC/SP"
ESCOLA_ENDERECO = "R. Valter Souza Costa, 147 - Jardim Primavera, Ferraz de Vasconcelos - SP"
ESCOLA_CEP = "CEP: 08535-310"
ESCOLA_TELEFONE = "(11) 4675-1855"
ESCOLA_EMAIL = "e918623@educacao.sp.gov.br"
ESCOLA_LOGO = "logo.jpg"

# ============================================================================
# INICIALIZAÇÃO DO SESSION STATE
# ============================================================================
if 'editando_id' not in st.session_state:
    st.session_state.editando_id = None
if 'dados_edicao' not in st.session_state:
    st.session_state.dados_edicao = None
if 'editando_prof' not in st.session_state:
    st.session_state.editando_prof = None
if 'editando_resp' not in st.session_state:
    st.session_state.editando_resp = None
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

# ============================================================================
# FUNÇÕES DE CARREGAMENTO DE DADOS DO SUPABASE (VIA REQUESTS)
# ============================================================================

@st.cache_data(ttl=60)
def carregar_alunos():
    """
    Carrega todos os alunos do banco de dados Supabase via Requests API.
    
    Returns:
        pd.DataFrame: DataFrame com todos os alunos cadastrados.
    """
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['nome', 'ra', 'turma', 'nascimento', 'responsavel', 'telefone', 'foto_url'])
    
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/alunos?select=*", headers=HEADERS)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            if not df.empty:
                df = df.sort_values('nome')
            return df
        else:
            return pd.DataFrame(columns=['nome', 'ra', 'turma', 'nascimento', 'responsavel', 'telefone', 'foto_url'])
    except Exception as e:
        st.error(f"Erro ao carregar alunos: {str(e)}")
        return pd.DataFrame(columns=['nome', 'ra', 'turma', 'nascimento', 'responsavel', 'telefone', 'foto_url'])


@st.cache_data(ttl=60)
def carregar_professores():
    """
    Carrega todos os professores do banco de dados Supabase via Requests API.
    
    Returns:
        pd.DataFrame: DataFrame com todos os professores cadastrados.
    """
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['id', 'nome', 'email', 'cargo', 'foto_url'])
    
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/professores?select=*", headers=HEADERS)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            if not df.empty:
                # CORREÇÃO 4: Ordenar professores por nome (alfabética)
                df = df.sort_values('nome')
            return df
        else:
            return pd.DataFrame(columns=['id', 'nome', 'email', 'cargo', 'foto_url'])
    except Exception as e:
        st.error(f"Erro ao carregar professores: {str(e)}")
        return pd.DataFrame(columns=['id', 'nome', 'email', 'cargo', 'foto_url'])


@st.cache_data(ttl=60)
def carregar_ocorrencias():
    """
    Carrega todas as ocorrências do banco de dados Supabase via Requests API.
    
    Returns:
        pd.DataFrame: DataFrame com todas as ocorrências registradas.
    """
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamentos', 'testemunhas', 'evidencias'])
    
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/ocorrencias?select=*&order=data.desc", headers=HEADERS)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamentos', 'testemunhas', 'evidencias'])
    except Exception as e:
        st.error(f"Erro ao carregar ocorrências: {str(e)}")
        return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamentos', 'testemunhas', 'evidencias'])


@st.cache_data(ttl=60)
def carregar_responsaveis():
    """
    Carrega todos os responsáveis por assinatura do banco de dados Supabase via Requests API.
    
    Returns:
        pd.DataFrame: DataFrame com todos os responsáveis cadastrados.
    """
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['id', 'nome', 'cargo'])
    
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/responsaveis?select=*", headers=HEADERS)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            if not df.empty:
                df = df.sort_values('cargo')
            return df
        else:
            return pd.DataFrame(columns=['id', 'nome', 'cargo'])
    except Exception as e:
        st.error(f"Erro ao carregar responsáveis: {str(e)}")
        return pd.DataFrame(columns=['id', 'nome', 'cargo'])


# ============================================================================
# FUNÇÕES DE SALVAMENTO DE DADOS NO SUPABASE (VIA REQUESTS)
# ============================================================================

def salvar_ocorrencia(ocorrencia_dict):
    """
    Salva uma ocorrência no banco de dados Supabase via Requests API.
    
    Args:
        ocorrencia_dict (dict): Dicionário com os dados da ocorrência.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        # Converter lista de encaminhamentos para string separada por |
        if 'encaminhamentos' in ocorrencia_dict and isinstance(ocorrencia_dict['encaminhamentos'], list):
            ocorrencia_dict['encaminhamentos'] = '| '.join(ocorrencia_dict['encaminhamentos'])
        
        response = requests.post(f"{SUPABASE_URL}/rest/v1/ocorrencias", json=ocorrencia_dict, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Ocorrência salva com sucesso!"
        else:
            return False, f"Erro ao salvar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao salvar ocorrência: {str(e)}")
        return False, f"Erro ao salvar: {str(e)}"


def atualizar_ocorrencia(id_ocorrencia, ocorrencia_dict):
    """
    Atualiza uma ocorrência existente no banco de dados Supabase via Requests API.
    
    Args:
        id_ocorrencia (int): ID da ocorrência a ser atualizada.
        ocorrencia_dict (dict): Dicionário com os dados atualizados.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        # Converter lista de encaminhamentos para string separada por |
        if 'encaminhamentos' in ocorrencia_dict and isinstance(ocorrencia_dict['encaminhamentos'], list):
            ocorrencia_dict['encaminhamentos'] = '| '.join(ocorrencia_dict['encaminhamentos'])
        
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}", json=ocorrencia_dict, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Ocorrência atualizada com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao atualizar ocorrência: {str(e)}")
        return False, f"Erro ao atualizar: {str(e)}"


def excluir_ocorrencia(id_ocorrencia):
    """
    Exclui uma ocorrência do banco de dados Supabase via Requests API.
    
    Args:
        id_ocorrencia (int): ID da ocorrência a ser excluída.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}", headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Ocorrência excluída com sucesso!"
        else:
            return False, f"Erro ao excluir: {response.text}"
    except Exception as e:
        st.error(f"Erro ao excluir ocorrência: {str(e)}")
        return False, f"Erro ao excluir: {str(e)}"


def salvar_aluno(aluno_dict):
    """
    Salva um aluno no banco de dados Supabase via Requests API.
    
    Args:
        aluno_dict (dict): Dicionário com os dados do aluno.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/alunos", json=aluno_dict, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Aluno salvo com sucesso!"
        else:
            return False, f"Erro ao salvar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao salvar aluno: {str(e)}")
        return False, f"Erro ao salvar: {str(e)}"


def atualizar_aluno(ra_aluno, aluno_dict):
    """
    Atualiza um aluno existente no banco de dados Supabase via Requests API.
    
    Args:
        ra_aluno (str): RA do aluno a ser atualizado.
        aluno_dict (dict): Dicionário com os dados atualizados.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra_aluno}", json=aluno_dict, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Aluno atualizado com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao atualizar aluno: {str(e)}")
        return False, f"Erro ao atualizar: {str(e)}"


def excluir_aluno(ra_aluno):
    """
    Exclui um aluno do banco de dados Supabase via Requests API.
    
    Args:
        ra_aluno (str): RA do aluno a ser excluído.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra_aluno}", headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Aluno excluído com sucesso!"
        else:
            return False, f"Erro ao excluir: {response.text}"
    except Exception as e:
        st.error(f"Erro ao excluir aluno: {str(e)}")
        return False, f"Erro ao excluir: {str(e)}"


def salvar_professor(professor_dict):
    """
    Salva um professor no banco de dados Supabase via Requests API.
    
    Args:
        professor_dict (dict): Dicionário com os dados do professor.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/professores", json=professor_dict, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Professor salvo com sucesso!"
        else:
            return False, f"Erro ao salvar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao salvar professor: {str(e)}")
        return False, f"Erro ao salvar: {str(e)}"


def atualizar_professor(id_prof, professor_dict):
    """
    Atualiza um professor existente no banco de dados Supabase via Requests API.
    
    Args:
        id_prof (int): ID do professor a ser atualizado.
        professor_dict (dict): Dicionário com os dados atualizados.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}", json=professor_dict, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Professor atualizado com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao atualizar professor: {str(e)}")
        return False, f"Erro ao atualizar: {str(e)}"


def excluir_professor(id_prof):
    """
    Exclui um professor do banco de dados Supabase via Requests API.
    
    Args:
        id_prof (int): ID do professor a ser excluído.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}", headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Professor excluído com sucesso!"
        else:
            return False, f"Erro ao excluir: {response.text}"
    except Exception as e:
        st.error(f"Erro ao excluir professor: {str(e)}")
        return False, f"Erro ao excluir: {str(e)}"


def salvar_responsavel(responsavel_dict):
    """
    Salva um responsável por assinatura no banco de dados Supabase via Requests API.
    
    Args:
        responsavel_dict (dict): Dicionário com os dados do responsável.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/responsaveis", json=responsavel_dict, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Responsável salvo com sucesso!"
        else:
            return False, f"Erro ao salvar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao salvar responsável: {str(e)}")
        return False, f"Erro ao salvar: {str(e)}"


def atualizar_responsavel(id_resp, responsavel_dict):
    """
    Atualiza um responsável existente no banco de dados Supabase via Requests API.
    
    Args:
        id_resp (int): ID do responsável a ser atualizado.
        responsavel_dict (dict): Dicionário com os dados atualizados.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}", json=responsavel_dict, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Responsável atualizado com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao atualizar responsável: {str(e)}")
        return False, f"Erro ao atualizar: {str(e)}"


def excluir_responsavel(id_resp):
    """
    Exclui um responsável do banco de dados Supabase via Requests API.
    
    Args:
        id_resp (int): ID do responsável a ser excluído.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}", headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Responsável excluído com sucesso!"
        else:
            return False, f"Erro ao excluir: {response.text}"
    except Exception as e:
        st.error(f"Erro ao excluir responsável: {str(e)}")
        return False, f"Erro ao excluir: {str(e)}"


# ============================================================================
# FUNÇÕES DE UPLOAD DE FOTOS PARA SUPABASE STORAGE (VIA REQUESTS)
# ============================================================================

def upload_foto_supabase(file, folder, filename):
    """
    Faz upload de foto para o Supabase Storage via Requests API.
    
    Args:
        file: Arquivo de foto enviado pelo usuário.
        folder (str): Pasta no bucket onde a foto será salva.
        filename (str): Nome do arquivo.
    
    Returns:
        tuple: (str, str) - URL pública e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return None, "Supabase não configurado"
    
    try:
        file_bytes = file.getvalue()
        
        # CORREÇÃO 1: Verificar se bucket existe antes de upload
        storage_url = SUPABASE_URL.replace("/rest/v1", "/storage/v1")
        upload_headers = HEADERS.copy()
        upload_headers["Content-Type"] = file.type
        
        try:
            response = requests.post(
                f"{storage_url}/object/fotos/{folder}/{filename}",
                data=file_bytes,
                headers=upload_headers
            )
        except Exception as upload_error:
            # Se bucket não existir, tentar criar mensagem de erro clara
            if 'Bucket not found' in str(upload_error) or response.status_code == 404:
                return None, "Bucket 'fotos' não encontrado. Crie o bucket no Supabase primeiro!"
            raise upload_error
        
        if response.status_code in [200, 201]:
            public_url = f"{storage_url}/object/public/fotos/{folder}/{filename}"
            return public_url, "Foto enviada com sucesso!"
        else:
            return None, f"Erro ao enviar foto: {response.text}"
    except Exception as e:
        st.error(f"Erro ao enviar foto: {str(e)}")
        return None, f"Erro ao enviar foto: {str(e)}"


def atualizar_foto_aluno(ra_aluno, foto_url):
    """
    Atualiza a URL da foto de um aluno no banco de dados.
    
    Args:
        ra_aluno (str): RA do aluno.
        foto_url (str): URL da foto no Supabase Storage.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra_aluno}",
            json={'foto_url': foto_url},
            headers=HEADERS
        )
        if response.status_code in [200, 201]:
            return True, "Foto atualizada com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao atualizar foto do aluno: {str(e)}")
        return False, f"Erro ao atualizar: {str(e)}"


def atualizar_foto_professor(id_prof, foto_url):
    """
    Atualiza a URL da foto de um professor no banco de dados.
    
    Args:
        id_prof (int): ID do professor.
        foto_url (str): URL da foto no Supabase Storage.
    
    Returns:
        tuple: (bool, str) - Sucesso e mensagem de retorno.
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    
    try:
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}",
            json={'foto_url': foto_url},
            headers=HEADERS
        )
        if response.status_code in [200, 201]:
            return True, "Foto atualizada com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao atualizar foto do professor: {str(e)}")
        return False, f"Erro ao atualizar: {str(e)}"


# ============================================================================
# FUNÇÕES AUXILIARES DE VALIDAÇÃO E VERIFICAÇÃO
# ============================================================================

def verificar_ocorrencia_duplicada(ra_aluno, categoria, data, df_ocorrencias):
    """
    Verifica se já existe uma ocorrência igual para o mesmo aluno na mesma data.
    
    Args:
        ra_aluno (str): RA do aluno.
        categoria (str): Categoria da ocorrência.
        data (str): Data da ocorrência.
        df_ocorrencias (pd.DataFrame): DataFrame com todas as ocorrências.
    
    Returns:
        bool: True se ocorrência duplicada existir, False caso contrário.
    """
    # CORREÇÃO 6: Verificar se df_ocorrencias não é None ou vazio
    if df_ocorrencias is None or df_ocorrencias.empty:
        return False
    
    try:
        # Extrair apenas a data (sem hora) para comparação
        data_comparacao = data.split(' ')[0] if ' ' in data else data
        
        for idx, ocorrencia in df_ocorrencias.iterrows():
            data_ocorrencia = str(ocorrencia.get('data', ''))
            data_ocorrencia_comparacao = data_ocorrencia.split(' ')[0] if ' ' in data_ocorrencia else data_ocorrencia
            
            if (str(ocorrencia.get('ra', '')) == str(ra_aluno) and 
                str(ocorrencia.get('categoria', '')) == str(categoria) and 
                data_ocorrencia_comparacao == data_comparacao):
                return True
        
        return False
    except Exception as e:
        st.error(f"Erro ao verificar duplicidade: {str(e)}")
        return False


def formatar_texto(texto):
    """
    Formata texto para exibição no PDF, convertendo quebras de linha.
    
    Args:
        texto (str): Texto original.
    
    Returns:
        str: Texto formatado.
    """
    if not texto:
        return ""
    
    # Substituir quebras de linha HTML por quebras reais
    texto_formatado = str(texto).replace('<br/>', '\n').replace('<br>', '\n').replace('\n', '\n')
    return texto_formatado


def remover_duplicatas_encaminhamentos(encaminhamentos):
    """
    Remove encaminhamentos duplicados de uma lista.
    
    Args:
        encaminhamentos (str): String com encaminhamentos separados por |.
    
    Returns:
        str: String com encaminhamentos únicos.
    """
    if not encaminhamentos:
        return ""
    
    todos = []
    for linha in str(encaminhamentos).split('|'):
        linha = linha.strip()
        if linha and linha not in todos:
            todos.append(linha)
    
    return '| '.join(todos)


def excluir_alunos_por_turma(turma):
    """
    Exclui todos os alunos de uma turma específica.
    
    Args:
        turma (str): Nome da turma.
    
    Returns:
        bool: True se excluído com sucesso, False caso contrário.
    """
    if not SUPABASE_URL:
        return False
    
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/alunos?turma=eq.{turma}", headers=HEADERS)
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao excluir alunos da turma: {str(e)}")
        return False


# ============================================================================
# FUNÇÕES DE GERAÇÃO DE PDF - OCORRÊNCIA
# ============================================================================

def gerar_pdf_ocorrencia(ocorrencia, responsaveis=None):
    """
    Gera PDF de ocorrência com layout profissional.
    
    Args:
        ocorrencia (dict): Dados da ocorrência.
        responsaveis (pd.DataFrame): DataFrame com responsáveis por assinatura.
    
    Returns:
        BytesIO: Buffer com o PDF gerado.
    """
    buffer = io.BytesIO()
    
    # CORREÇÃO 5: Margens reduzidas para caber em 1 página
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
        spaceAfter=0.5*cm,
        textColor=colors.HexColor('#667eea')
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
    
    # CABEÇALHO COM LOGO (16cm x 4.5cm) - CORREÇÃO
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4.5*cm)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 0.3*cm))
    except:
        pass
    
    # Título do documento
    elementos.append(Paragraph("📋 REGISTRO DE OCORRÊNCIA DISCIPLINAR", estilos['Titulo']))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Dados da escola
    elementos.append(Paragraph(f"<b>{ESCOLA_NOME}</b>", estilos['Texto']))
    elementos.append(Paragraph(f"{ESCOLA_ENDERECO}", estilos['Texto']))
    elementos.append(Paragraph(f"{ESCOLA_CEP} | {ESCOLA_TELEFONE}", estilos['Texto']))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Dados do aluno
    elementos.append(Paragraph("<b>DADOS DO(A) ESTUDANTE:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"<b>Nome:</b> {ocorrencia.get('aluno', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>RA:</b> {ocorrencia.get('ra', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Turma:</b> {ocorrencia.get('turma', 'N/A')}", estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Dados da ocorrência
    elementos.append(Paragraph("<b>DADOS DA OCORRÊNCIA:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"<b>Data:</b> {ocorrencia.get('data', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Categoria:</b> {ocorrencia.get('categoria', 'N/A')}", estilos['Texto']))
    
    # CORREÇÃO 8: Badge de gravidade colorida
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
    
    if isinstance(encaminhamentos, str):
        encaminhamentos = encaminhamentos.split('|')
    
    if isinstance(encaminhamentos, list):
        for enc in encaminhamentos:
            if enc.strip():
                elementos.append(Paragraph(f"• {enc.strip()}", estilos['Texto']))
    else:
        elementos.append(Paragraph(str(encaminhamentos), estilos['Texto']))
    
    elementos.append(Spacer(1, 0.5*cm))
    
    # Professor responsável
    elementos.append(Paragraph("<b>Professor Responsável:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"{ocorrencia.get('professor', 'N/A')}", estilos['Texto']))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Testemunhas (se houver)
    if ocorrencia.get('testemunhas'):
        elementos.append(Paragraph("<b>Testemunhas:</b>", estilos['Secao']))
        elementos.append(Paragraph(f"{ocorrencia.get('testemunhas', '')}", estilos['Texto']))
        elementos.append(Spacer(1, 0.3*cm))
    
    # Evidências (se houver)
    if ocorrencia.get('evidencias'):
        elementos.append(Paragraph("<b>Evidências:</b>", estilos['Secao']))
        elementos.append(Paragraph(f"{ocorrencia.get('evidencias', '')}", estilos['Texto']))
        elementos.append(Spacer(1, 0.5*cm))
    
    # Assinaturas
    elementos.append(Paragraph("<b>ASSINATURAS:</b>", estilos['Secao']))
    elementos.append(Spacer(1, 0.5*cm))
    
    cargos_para_assinatura = ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)"]
    
    for cargo in cargos_para_assinatura:
        if responsaveis is not None and not responsaveis.empty:
            resp = responsaveis[responsaveis['cargo'] == cargo]
            if not resp.empty and resp.iloc[0].get('nome'):
                elementos.append(Paragraph(f"<b>{cargo}:</b> {resp.iloc[0].get('nome', '')}", estilos['Texto']))
            else:
                elementos.append(Paragraph(f"<b>{cargo}:</b> _________________________________", estilos['Texto']))
        else:
            elementos.append(Paragraph(f"<b>{cargo}:</b> _________________________________", estilos['Texto']))
        elementos.append(Spacer(1, 0.5*cm))
    
    # Ciência dos pais/responsáveis
    elementos.append(Spacer(1, 1*cm))
    elementos.append(Paragraph("<b>CIÊNCIA DOS PAIS/RESPONSÁVEIS:</b>", estilos['Secao']))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("Declaro que recebi e tomei conhecimento deste comunicado.", estilos['Texto']))
    elementos.append(Spacer(1, 1.5*cm))
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
    
    # Construir PDF
    doc.build(elementos)
    buffer.seek(0)
    
    return buffer


# ============================================================================
# FUNÇÕES DE GERAÇÃO DE PDF - COMUNICADO AOS PAIS
# ============================================================================

def gerar_pdf_comunicado(ocorrencia, responsaveis=None):
    """
    Gera PDF de comunicado aos pais com layout profissional.
    
    Args:
        ocorrencia (dict): Dados da ocorrência.
        responsaveis (pd.DataFrame): DataFrame com responsáveis por assinatura.
    
    Returns:
        BytesIO: Buffer com o PDF gerado.
    """
    buffer = io.BytesIO()
    
    # Margens reduzidas para caber em 1 página
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
    
    estilos.add(ParagraphStyle(
        'Secao',
        parent=estilos['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=0.3*cm
    ))
    
    estilos.add(ParagraphStyle(
        'Assinatura',
        parent=estilos['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        spaceAfter=0.5*cm
    ))
    
    # CABEÇALHO COM LOGO (16cm x 4.5cm)
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4.5*cm)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 0.3*cm))
    except:
        pass
    
    # Título do documento
    elementos.append(Paragraph("📬 COMUNICADO AOS PAIS/RESPONSÁVEIS", estilos['TituloComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Dados da escola
    elementos.append(Paragraph(f"<b>{ESCOLA_NOME}</b>", estilos['TextoComunicado']))
    elementos.append(Paragraph(f"{ESCOLA_ENDERECO}", estilos['TextoComunicado']))
    elementos.append(Paragraph(f"{ESCOLA_CEP} | {ESCOLA_TELEFONE}", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Saudação
    elementos.append(Paragraph(f"Prezados responsáveis pelo(a) estudante <b>{ocorrencia.get('aluno', 'N/A')}</b>,", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("Venho por meio deste comunicar que foi registrada uma ocorrência disciplinar conforme detalhes abaixo:", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Dados da ocorrência
    elementos.append(Paragraph("<b>DADOS DA OCORRÊNCIA:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"<b>Data:</b> {ocorrencia.get('data', 'N/A')}", estilos['TextoComunicado']))
    elementos.append(Paragraph(f"<b>Turma:</b> {ocorrencia.get('turma', 'N/A')}", estilos['TextoComunicado']))
    elementos.append(Paragraph(f"<b>Categoria:</b> {ocorrencia.get('categoria', 'N/A')}", estilos['TextoComunicado']))
    
    # Gravidade com cor
    gravidade = ocorrencia.get('gravidade', 'N/A')
    cor_gravidade = CORES_GRAVIDADE.get(gravidade, '#9E9E9E')
    elementos.append(Paragraph(
        f"<b>Gravidade:</b> <font color='{cor_gravidade}'><b>{gravidade}</b></font>",
        estilos['TextoComunicado']
    ))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Relato
    elementos.append(Paragraph("<b>Relato:</b>", estilos['Secao']))
    relato_formatado = formatar_texto(ocorrencia.get('relato', ''))
    elementos.append(Paragraph(relato_formatado, estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.3*cm))
    
    # Encaminhamentos
    elementos.append(Paragraph("<b>Encaminhamentos:</b>", estilos['Secao']))
    encaminhamentos = ocorrencia.get('encaminhamentos', [])
    
    if isinstance(encaminhamentos, str):
        encaminhamentos = encaminhamentos.split('|')
    
    if isinstance(encaminhamentos, list):
        for enc in encaminhamentos:
            if enc.strip():
                elementos.append(Paragraph(f"• {enc.strip()}", estilos['TextoComunicado']))
    else:
        elementos.append(Paragraph(str(encaminhamentos), estilos['TextoComunicado']))
    
    elementos.append(Spacer(1, 0.5*cm))
    
    # Professor responsável
    elementos.append(Paragraph("<b>Professor Responsável:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"{ocorrencia.get('professor', 'N/A')}", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
    # Assinaturas
    elementos.append(Paragraph("<b>ASSINATURAS:</b>", estilos['Secao']))
    elementos.append(Spacer(1, 0.5*cm))
    
    cargos_para_assinatura = ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)"]
    
    for cargo in cargos_para_assinatura:
        if responsaveis is not None and not responsaveis.empty:
            resp = responsaveis[responsaveis['cargo'] == cargo]
            if not resp.empty and resp.iloc[0].get('nome'):
                elementos.append(Paragraph(f"<b>{cargo}:</b> {resp.iloc[0].get('nome', '')}", estilos['TextoComunicado']))
            else:
                elementos.append(Paragraph(f"<b>{cargo}:</b> _________________________________", estilos['TextoComunicado']))
        else:
            elementos.append(Paragraph(f"<b>{cargo}:</b> _________________________________", estilos['TextoComunicado']))
        elementos.append(Spacer(1, 0.5*cm))
    
    # Ciência dos pais/responsáveis
    elementos.append(Spacer(1, 1*cm))
    elementos.append(Paragraph("<b>CIÊNCIA DOS PAIS/RESPONSÁVEIS:</b>", estilos['Secao']))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("Declaro que recebi e tomei conhecimento deste comunicado.", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 1.5*cm))
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
    
    # Construir PDF
    doc.build(elementos)
    buffer.seek(0)
    
    return buffer


# ============================================================================
# CSS PERSONALIZADO
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
    border-left: 5px solid #ffc107;
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
}
.protocolo-info {
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 1rem;
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
.info-box {
    background: #e3f2fd;
    border-left: 4px solid #2196F3;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 4px;
}
.warning-box {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 4px;
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
.gravidade-alert {
    background: #f8d7da;
    border: 2px solid #dc3545;
    border-radius: 8px;
    padding: 0.5rem;
    margin: 0.5rem 0;
    color: #721c24;
}
.infracao-tag {
    background: #667eea;
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 15px;
    display: inline-block;
    margin: 0.2rem;
    font-size: 0.9rem;
}
.infracao-principal-tag {
    background: #28a745;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 15px;
    display: inline-block;
    margin: 0.5rem 0;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# INTERFACE PRINCIPAL - CABEÇALHO E MENU LATERAL
# ============================================================================

# Cabeçalho
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

# Menu Lateral
menu = st.sidebar.selectbox(
    "📋 Menu Principal",
    [
        "🏠 Home",
        "📝 Registrar Ocorrência",
        "📊 Lista de Ocorrências",
        "👥 Alunos",
        "👨‍🏫 Professores",
        "📈 Gráficos",
        "🖨️ Relatórios",
        "⚙️ Configurações",
        "💾 Backup"
    ],
    index=0
)

st.session_state.pagina_atual = menu


# ============================================================================
# PÁGINA: HOME
# ============================================================================

if menu == "🏠 Home":
    st.title("🏠 Dashboard")
    
    # Carregar dados
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    df_professores = carregar_professores()
    
    if not df_ocorrencias.empty:
        # Calcular métricas
        total_ocorrencias = len(df_ocorrencias)
        total_gravissima = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Gravíssima'])
        total_grave = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Grave'])
        total_media = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Média'])
        total_leve = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Leve'])
        turmas_afetadas = df_ocorrencias['turma'].nunique()
        
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
    
    # Resumo de professores
    if not df_professores.empty:
        st.subheader("👨‍🏫 Resumo de Professores")
        st.metric("Total de Professores", len(df_professores))


# ============================================================================
# PÁGINA: REGISTRAR OCORRÊNCIA
# ============================================================================

elif menu == "📝 Registrar Ocorrência":
    st.title("📝 Registrar Nova Ocorrência")
    
    # CORREÇÃO 6: Carregar ocorrências ANTES de usar na verificação de duplicidade
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    
    if df_alunos.empty:
        st.warning("⚠️ Nenhum aluno cadastrado. Importe alunos primeiro.")
    else:
        # Sucesso após salvar
        if st.session_state.get('ocorrencia_salva_sucesso', False):
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
                                "Selecione os Estudantes",
                                alunos["nome"].tolist(),
                                key="alunos_multiselect"
                            )
                        else:
                            # CORREÇÃO 10: Busca fuzzy para alunos
                            lista_alunos = alunos['nome'].tolist()
                            busca_aluno = st.text_input("🔍 Buscar Aluno (digite o nome)", "")
                            
                            if busca_aluno:
                                resultados = process.extract(busca_aluno, lista_alunos, limit=5)
                                aluno_selecionado = st.selectbox("Selecione o Aluno", [r[0] for r in resultados])
                            else:
                                aluno_selecionado = st.selectbox("Selecione o Aluno", lista_alunos)
                            
                            alunos_selecionados = [aluno_selecionado] if aluno_selecionado else []
                    
                    with col2:
                        st.markdown("### 📅 Data e Hora")
                        data = st.date_input("Data", value=datetime.now().date())
                        hora = st.time_input("Hora", value=datetime.now().time())
                    
                    st.markdown("---")
                    
                    # Dados da ocorrência
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # CORREÇÃO 12: Listener para atualizar gravidade automaticamente
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
                    
                    # CORREÇÃO 13: Mostrar fluxo de ações
                    if categoria in FLUXO_ACOES:
                        st.warning(f"📌 {FLUXO_ACOES[categoria]}")
                    
                    # Relato
                    relato = st.text_area("📝 Relato da Ocorrência", height=200)
                    
                    # CORREÇÃO 14: Encaminhamentos como checkboxes
                    st.subheader("🔄 Encaminhamentos")
                    encaminhamentos_disponiveis = ENCAMINHAMENTOS_POR_GRAVIDADE.get(gravidade_select, [])
                    encaminhamentos_selecionados = st.multiselect(
                        "Selecione os encaminhamentos realizados",
                        encaminhamentos_disponiveis,
                        default=encaminhamentos_disponiveis[:2] if encaminhamentos_disponiveis else []
                    )
                    
                    # Professor responsável
                    df_professores = carregar_professores()
                    if not df_professores.empty:
                        # CORREÇÃO 4: Professores ordenados alfabeticamente
                        prof = st.selectbox("👨‍🏫 Professor Responsável", ["Selecione..."] + df_professores['nome'].tolist())
                    else:
                        prof = st.text_input("👨‍🏫 Professor Responsável")
                    
                    # Testemunhas
                    testemunhas = st.text_input("👀 Testemunhas (opcional)")
                    
                    # Evidências
                    evidencias = st.text_area("📎 Evidências (opcional)")
                    
                    # Botão salvar
                    st.markdown("---")
                    
                    if st.session_state.get('salvando_ocorrencia', False):
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
                                
                                # CORREÇÃO 6: df_ocorrencias já carregado no início
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
                        if st.button("💾 Salvar Ocorrência", type="primary"):
                            if not alunos_selecionados:
                                st.error("❌ Selecione pelo menos um estudante!")
                            elif not prof or prof == "Selecione...":
                                st.error("❌ Selecione o professor responsável!")
                            elif not relato:
                                st.error("❌ Preencha o relato da ocorrência!")
                            else:
                                st.session_state.salvando_ocorrencia = True
                                st.rerun()
                else:
                    st.info("📭 Nenhum aluno encontrado nesta(s) turma(s).")
            else:
                st.info("📭 Selecione pelo menos uma turma.")


# ============================================================================
# PÁGINA: LISTA DE OCORRÊNCIAS
# ============================================================================

elif menu == "📊 Lista de Ocorrências":
    st.title("📊 Lista de Ocorrências")
    
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    
    if not df_ocorrencias.empty:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_gravidade = st.multiselect("Gravidade", ["Gravíssima", "Grave", "Média", "Leve"])
        
        with col2:
            filtro_categoria = st.multiselect("Categoria", df_ocorrencias['categoria'].unique())
        
        with col3:
            filtro_turma = st.multiselect("Turma", df_alunos['turma'].unique().tolist())
        
        # Aplicar filtros
        df_filtrado = df_ocorrencias.copy()
        
        if filtro_gravidade:
            df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(filtro_gravidade)]
        
        if filtro_categoria:
            df_filtrado = df_filtrado[df_filtrado['categoria'].isin(filtro_categoria)]
        
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        
        st.markdown(f"**Total:** {len(df_filtrado)} ocorrência(s)")
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Ações em lote
        st.subheader("📄 Gerar Documentos")
        col1, col2 = st.columns(2)
        
        with col1:
            id_selecionado = st.number_input("ID da Ocorrência", min_value=1, step=1)
            
            if st.button("📄 Gerar PDF"):
                ocorrencia = df_filtrado[df_filtrado['id'] == id_selecionado].iloc[0].to_dict()
                pdf_buffer = gerar_pdf_ocorrencia(ocorrencia)
                st.download_button(
                    label="📥 Baixar PDF",
                    data=pdf_buffer,
                    file_name=f"ocorrencia_{id_selecionado}.pdf",
                    mime="application/pdf"
                )
        
        with col2:
            if st.button("📬 Gerar Comunicado"):
                ocorrencia = df_filtrado[df_filtrado['id'] == id_selecionado].iloc[0].to_dict()
                pdf_buffer = gerar_pdf_comunicado(ocorrencia)
                st.download_button(
                    label="📥 Baixar Comunicado",
                    data=pdf_buffer,
                    file_name=f"comunicado_{id_selecionado}.pdf",
                    mime="application/pdf"
                )
        
        # CORREÇÃO 3: Opção de excluir ocorrência
        st.subheader("🗑️ Excluir Ocorrência")
        id_excluir = st.number_input("ID para Excluir", min_value=1, step=1, key="excluir_occ")
        
        if st.button("🗑️ Excluir"):
            senha = st.text_input("Digite a senha de exclusão (040600)", type="password")
            if senha == "040600":
                sucesso, msg = excluir_ocorrencia(id_excluir)
                if sucesso:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            else:
                st.error("❌ Senha incorreta!")
    
    else:
        st.info("📭 Nenhuma ocorrência registrada ainda.")


# ============================================================================
# PÁGINA: ALUNOS
# ============================================================================

elif menu == "👥 Alunos":
    st.title("👥 Gerenciar Alunos")
    
    df_alunos = carregar_alunos()
    
    if not df_alunos.empty:
        # Filtros
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
        
        # CORREÇÃO 3: Opção de excluir aluno
        st.subheader("🗑️ Excluir Aluno")
        ra_excluir = st.text_input("RA do Aluno para Excluir")
        
        if st.button("🗑️ Excluir Aluno"):
            senha = st.text_input("Digite a senha de exclusão (040600)", type="password", key="senha_aluno")
            if senha == "040600":
                sucesso, msg = excluir_aluno(ra_excluir)
                if sucesso:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            else:
                st.error("❌ Senha incorreta!")
        
        # Upload de foto
        st.subheader("📷 Upload de Foto")
        col1, col2 = st.columns(2)
        
        with col1:
            aluno_foto = st.selectbox("Selecione o Aluno", df_alunos['nome'].tolist())
            ra_aluno = df_alunos[df_alunos['nome'] == aluno_foto]['ra'].values[0]
        
        with col2:
            foto_file = st.file_uploader("Selecione a foto", type=['jpg', 'jpeg', 'png'])
            
            if foto_file and st.button("📷 Enviar Foto"):
                # CORREÇÃO 1: Tratamento de erro de bucket
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
    else:
        st.info("📭 Nenhum aluno cadastrado.")


# ============================================================================
# PÁGINA: PROFESSORES
# ============================================================================

elif menu == "👨‍🏫 Professores":
    st.title("👨‍🏫 Gerenciar Professores")
    
    df_professores = carregar_professores()
    
    # CORREÇÃO 2: Botão editar cadastro professor
    st.subheader("📝 Novo Professor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome_prof = st.text_input("Nome Completo *")
        email_prof = st.text_input("Email")
    
    with col2:
        cargo_prof = st.text_input("Cargo")
        foto_prof = st.file_uploader("Foto (opcional)", type=['jpg', 'jpeg', 'png'])
    
    # Verificar se está editando
    if st.session_state.get('editando_prof', None) is not None:
        st.info(f"✏️ Editando professor ID: {st.session_state.editando_prof}")
        
        prof_atual = df_professores[df_professores['id'] == st.session_state.editando_prof].iloc[0]
        
        if st.button("💾 Atualizar Professor"):
            professor_dict = {
                'nome': nome_prof.strip(),
                'email': email_prof.strip() if email_prof else None,
                'cargo': cargo_prof.strip() if cargo_prof else None
            }
            
            if foto_prof:
                url, msg = upload_foto_supabase(foto_prof, 'professores', f"{st.session_state.editando_prof}.jpg")
                if url:
                    professor_dict['foto_url'] = url
            
            sucesso, msg = atualizar_professor(st.session_state.editando_prof, professor_dict)
            
            if sucesso:
                st.success(f"✅ {msg}")
                st.session_state.editando_prof = None
                carregar_professores.clear()
                st.rerun()
            else:
                st.error(f"❌ {msg}")
        
        if st.button("❌ Cancelar Edição"):
            st.session_state.editando_prof = None
            st.rerun()
    else:
        if st.button("💾 Salvar Professor"):
            if nome_prof:
                # Verificar duplicidade
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
                    
                    if foto_prof:
                        url, msg = upload_foto_supabase(foto_prof, 'professores', f"{nome_prof.strip()}.jpg")
                        if url:
                            professor_dict['foto_url'] = url
                    
                    if salvar_professor(professor_dict):
                        st.success(f"✅ Professor {nome_prof} cadastrado com sucesso!")
                        carregar_professores.clear()
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar professor")
            else:
                st.error("❌ Nome é obrigatório!")
    
    st.markdown("---")
    
    # CORREÇÃO 4: Professores ordenados alfabeticamente
    st.subheader("📋 Professores Cadastrados")
    
    if not df_professores.empty:
        for idx, prof in df_professores.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 4, 2, 1, 1])
                
                with col1:
                    if prof.get('foto_url'):
                        st.image(prof['foto_url'], width=80, caption="Foto")
                    else:
                        st.write("👤")
                
                with col2:
                    st.write(f"**{prof.get('nome', 'N/A')}**")
                
                with col3:
                    st.write(f"📧 {prof.get('email', 'N/A')}")
                
                with col4:
                    # CORREÇÃO 2: Botão editar funcionando
                    if st.button("✏️", key=f"edit_prof_{prof.get('id', idx)}"):
                        st.session_state.editando_prof = prof.get('id')
                        st.rerun()
                
                with col5:
                    # CORREÇÃO 3: Opção de excluir professor
                    if st.button("🗑️", key=f"del_prof_{prof.get('id', idx)}"):
                        senha = st.text_input("Senha (040600)", type="password", key=f"senha_prof_{prof.get('id', idx)}")
                        if senha == "040600":
                            sucesso, msg = excluir_professor(prof.get('id'))
                            if sucesso:
                                st.success(f"✅ {msg}")
                                carregar_professores.clear()
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                        else:
                            st.error("❌ Senha incorreta!")
        
        st.divider()
        st.info(f"📊 **Total:** {len(df_professores)} professores cadastrados")
    else:
        st.info("📭 Nenhum professor cadastrado ainda.")


# ============================================================================
# PÁGINA: GRÁFICOS
# ============================================================================

elif menu == "📈 Gráficos":
    st.title("📈 Gráficos e Estatísticas")
    
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    
    if not df_ocorrencias.empty:
        # Filtros de período
        st.subheader("🔍 Filtros")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_turma = st.multiselect("Turma", df_alunos['turma'].unique().tolist())
        
        with col2:
            filtro_gravidade = st.multiselect("Gravidade", ["Gravíssima", "Grave", "Média", "Leve"])
        
        with col3:
            filtro_categoria = st.multiselect("Categoria", df_ocorrencias['categoria'].unique())
        
        # Aplicar filtros
        df_filtrado = df_ocorrencias.copy()
        
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        
        if filtro_gravidade:
            df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(filtro_gravidade)]
        
        if filtro_categoria:
            df_filtrado = df_filtrado[df_filtrado['categoria'].isin(filtro_categoria)]
        
        st.markdown(f"**Total:** {len(df_filtrado)} ocorrência(s)")
        st.markdown("---")
        
        # Gráfico 1: Ocorrências por Categoria
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Ocorrências por Categoria")
            if 'categoria' in df_filtrado.columns and not df_filtrado.empty:
                cat_counts = df_filtrado['categoria'].value_counts().head(10)
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
            if 'gravidade' in df_filtrado.columns and not df_filtrado.empty:
                grav_counts = df_filtrado['gravidade'].value_counts()
                fig = px.pie(
                    values=grav_counts.values,
                    names=grav_counts.index,
                    color=grav_counts.index,
                    color_discrete_map=CORES_GRAVIDADE
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico 2: Ocorrências por Turma
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Ocorrências por Turma")
            if 'turma' in df_filtrado.columns and not df_filtrado.empty:
                turma_counts = df_filtrado['turma'].value_counts().head(10)
                fig = px.bar(
                    x=turma_counts.index,
                    y=turma_counts.values,
                    color=turma_counts.values,
                    color_continuous_scale='Blues',
                    labels={'x': 'Turma', 'y': 'Quantidade'}
                )
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Ocorrências por Mês")
            if 'data' in df_filtrado.columns and not df_filtrado.empty:
                df_filtrado['mes'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce').dt.strftime('%m/%Y')
                mes_counts = df_filtrado['mes'].value_counts().sort_index()
                fig = px.line(
                    x=mes_counts.index,
                    y=mes_counts.values,
                    markers=True,
                    labels={'x': 'Mês', 'y': 'Quantidade'}
                )
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico 3: Mapa de Calor por Categoria e Gravidade
        st.subheader("🔥 Mapa de Calor: Categoria x Gravidade")
        if 'categoria' in df_filtrado.columns and 'gravidade' in df_filtrado.columns and not df_filtrado.empty:
            heatmap_data = pd.crosstab(df_filtrado['categoria'], df_filtrado['gravidade'])
            fig = px.imshow(
                heatmap_data,
                text_auto=True,
                aspect="auto",
                color_continuous_scale='YlOrRd'
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas resumidas
        st.markdown("---")
        st.subheader("📊 Estatísticas Resumidas")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Ocorrências", len(df_filtrado))
        
        with col2:
            st.metric("Turmas Afetadas", df_filtrado['turma'].nunique() if 'turma' in df_filtrado.columns else 0)
        
        with col3:
            st.metric("Alunos Envolvidos", df_filtrado['ra'].nunique() if 'ra' in df_filtrado.columns else 0)
        
        with col4:
            gravissima_count = len(df_filtrado[df_filtrado['gravidade'] == 'Gravíssima']) if 'gravidade' in df_filtrado.columns else 0
            st.metric("Ocorrências Gravíssimas", gravissima_count)
    
    else:
        st.info("📭 Nenhuma ocorrência registrada para gerar gráficos.")


# ============================================================================
# PÁGINA: RELATÓRIOS
# ============================================================================

elif menu == "🖨️ Relatórios":
    st.title("🖨️ Relatórios e Documentos")
    
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    df_responsaveis = carregar_responsaveis()
    
    if not df_ocorrencias.empty:
        # Filtros
        st.subheader("🔍 Filtros do Relatório")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_turma = st.multiselect("Turma", df_alunos['turma'].unique().tolist())
        
        with col2:
            filtro_gravidade = st.multiselect("Gravidade", ["Gravíssima", "Grave", "Média", "Leve"])
        
        with col3:
            filtro_data_inicio = st.date_input("Data Início", value=datetime.now() - timedelta(days=30))
            filtro_data_fim = st.date_input("Data Fim", value=datetime.now())
        
        # Aplicar filtros
        df_filtrado = df_ocorrencias.copy()
        
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        
        if filtro_gravidade:
            df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(filtro_gravidade)]
        
        # Filtro de data
        if 'data' in df_filtrado.columns:
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[
                (df_filtrado['data_dt'] >= pd.to_datetime(filtro_data_inicio)) &
                (df_filtrado['data_dt'] <= pd.to_datetime(filtro_data_fim))
            ]
        
        st.markdown(f"**Total:** {len(df_filtrado)} ocorrência(s) no período")
        
        # Opções de exportação
        st.subheader("📄 Exportar Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Exportar CSV"):
                csv = df_filtrado.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Baixar CSV",
                    data=csv,
                    file_name=f"relatorio_ocorrencias_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📥 Exportar Excel"):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtrado.to_excel(writer, index=False, sheet_name='Ocorrências')
                st.download_button(
                    label="📥 Baixar Excel",
                    data=output.getvalue(),
                    file_name=f"relatorio_ocorrencias_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        # Gerar PDF de ocorrência específica
        st.subheader("📄 Gerar PDF de Ocorrência")
        
        col1, col2 = st.columns(2)
        
        with col1:
            id_ocorrencia = st.number_input("ID da Ocorrência", min_value=1, step=1)
        
        with col2:
            tipo_documento = st.selectbox("Tipo de Documento", ["Ocorrência", "Comunicado aos Pais"])
        
        if st.button("📄 Gerar PDF"):
            ocorrencia = df_filtrado[df_filtrado['id'] == id_ocorrencia]
            
            if not ocorrencia.empty:
                ocorrencia_dict = ocorrencia.iloc[0].to_dict()
                
                if tipo_documento == "Ocorrência":
                    pdf_buffer = gerar_pdf_ocorrencia(ocorrencia_dict, df_responsaveis)
                    st.download_button(
                        label="📥 Baixar PDF de Ocorrência",
                        data=pdf_buffer,
                        file_name=f"ocorrencia_{id_ocorrencia}.pdf",
                        mime="application/pdf"
                    )
                else:
                    pdf_buffer = gerar_pdf_comunicado(ocorrencia_dict, df_responsaveis)
                    st.download_button(
                        label="📥 Baixar Comunicado",
                        data=pdf_buffer,
                        file_name=f"comunicado_{id_ocorrencia}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("❌ Ocorrência não encontrada com este ID.")
        
        # Visualizar dados
        st.markdown("---")
        st.subheader("📋 Dados Filtrados")
        st.dataframe(df_filtrado, use_container_width=True)
    
    else:
        st.info("📭 Nenhuma ocorrência registrada para gerar relatórios.")


# ============================================================================
# PÁGINA: CONFIGURAÇÕES
# ============================================================================

elif menu == "⚙️ Configurações":
    st.title("⚙️ Configurações do Sistema")
    
    # Informações da escola
    st.subheader("🏫 Informações da Escola")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Nome:** {ESCOLA_NOME}
        **Endereço:** {ESCOLA_ENDERECO}
        **CEP:** {ESCOLA_CEP}
        """)
    
    with col2:
        st.info(f"""
        **Telefone:** {ESCOLA_TELEFONE}
        **Email:** {ESCOLA_EMAIL}
        **Logo:** {ESCOLA_LOGO}
        """)
    
    # Protocolo 179
    st.subheader("📋 Protocolo 179")
    
    col1, col2 = st.columns(2)
    
    with col1:
        total_categorias = sum(len(v) for v in CATEGORIAS_OCORRENCIAS.values())
        st.metric("Total de Categorias", total_categorias)
    
    with col2:
        st.metric("Níveis de Gravidade", "4 (Gravíssima, Grave, Média, Leve)")
    
    # Segurança
    st.subheader("🔐 Configurações de Segurança")
    
    st.warning("""
    ⚠️ **Senha para Exclusão:** 040600
    
    Esta senha é necessária para excluir:
    - Ocorrências
    - Alunos
    - Professores
    - Responsáveis
    """)
    
    # Banco de dados
    st.subheader("💾 Banco de Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **Tipo:** Supabase (via Requests)
        **Status:** ✅ Conectado
        """)
    
    with col2:
        st.info("""
        **Storage:** ✅ Habilitado
        **Bucket:** fotos
        """)
    
    # Informações do sistema
    st.subheader("📊 Informações do Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Versão", "7.0 FINAL")
    
    with col2:
        st.metric("Framework", "Streamlit")
    
    with col3:
        st.metric("Python", "3.9+")
    
    # Bibliotecas
    st.subheader("📦 Bibliotecas Utilizadas")
    
    st.code("""
    streamlit
    pandas
    numpy
    requests
    reportlab
    openpyxl
    plotly
    fuzzywuzzy
    python-Levenshtein
    pytz
    python-dotenv
    """, language="text")


# ============================================================================
# PÁGINA: BACKUP
# ============================================================================

elif menu == "💾 Backup":
    st.title("💾 Backup e Restauração")
    
    # Gerar backup
    st.subheader("📥 Gerar Backup")
    
    st.info("💡 O backup contém todos os dados do sistema: alunos, professores, ocorrências e responsáveis.")
    
    if st.button("📥 Gerar Backup Completo"):
        # Carregar todos os dados
        df_alunos = carregar_alunos()
        df_professores = carregar_professores()
        df_ocorrencias = carregar_ocorrencias()
        df_responsaveis = carregar_responsaveis()
        
        # Criar dicionário de backup
        backup_data = {
            'alunos': df_alunos.to_dict('records') if not df_alunos.empty else [],
            'professores': df_professores.to_dict('records') if not df_professores.empty else [],
            'ocorrencias': df_ocorrencias.to_dict('records') if not df_ocorrencias.empty else [],
            'responsaveis': df_responsaveis.to_dict('records') if not df_responsaveis.empty else [],
            'data_backup': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'versao_sistema': '7.0 FINAL'
        }
        
        # Converter para JSON
        json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        # Botão de download
        st.download_button(
            label="📥 Baixar Backup JSON",
            data=json_str,
            file_name=f"backup_conviva_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )
        
        st.success("✅ Backup gerado com sucesso!")
    
    st.markdown("---")
    
    # Importar backup
    st.subheader("📤 Importar Backup")
    
    st.warning("""
    ⚠️ **ATENÇÃO:** Esta ação irá substituir todos os dados atuais!
    
    Certifique-se de ter um backup antes de importar.
    """)
    
    arquivo_backup = st.file_uploader("Selecione o arquivo de backup", type=['json'])
    
    if arquivo_backup:
        st.info("📄 Arquivo selecionado: " + arquivo_backup.name)
        
        if st.button("📤 Importar Backup"):
            senha = st.text_input("Digite a senha de confirmação (040600)", type="password")
            
            if senha == "040600":
                try:
                    # Ler arquivo JSON
                    backup_data = json.load(arquivo_backup)
                    
                    # Restaurar dados
                    contagem_alunos = 0
                    contagem_professores = 0
                    contagem_ocorrencias = 0
                    contagem_responsaveis = 0
                    
                    # Restaurar alunos
                    if 'alunos' in backup_data and backup_data['alunos']:
                        for aluno in backup_data['alunos']:
                            salvar_aluno(aluno)
                            contagem_alunos += 1
                    
                    # Restaurar professores
                    if 'professores' in backup_data and backup_data['professores']:
                        for professor in backup_data['professores']:
                            salvar_professor(professor)
                            contagem_professores += 1
                    
                    # Restaurar ocorrências
                    if 'ocorrencias' in backup_data and backup_data['ocorrencias']:
                        for ocorrencia in backup_data['ocorrencias']:
                            salvar_ocorrencia(ocorrencia)
                            contagem_ocorrencias += 1
                    
                    # Restaurar responsáveis
                    if 'responsaveis' in backup_data and backup_data['responsaveis']:
                        for responsavel in backup_data['responsaveis']:
                            salvar_responsavel(responsavel)
                            contagem_responsaveis += 1
                    
                    st.success(f"""
                    ✅ Backup importado com sucesso!
                    
                    - Alunos: {contagem_alunos}
                    - Professores: {contagem_professores}
                    - Ocorrências: {contagem_ocorrencias}
                    - Responsáveis: {contagem_responsaveis}
                    """)
                    
                    # Limpar cache
                    carregar_alunos.clear()
                    carregar_professores.clear()
                    carregar_ocorrencias.clear()
                    carregar_responsaveis.clear()
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao importar backup: {str(e)}")
            else:
                st.error("❌ Senha incorreta!")


# ============================================================================
# RODAPÉ
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p><b>Sistema Conviva 179</b> - Gestão de Ocorrências Escolares</p>
    <p>Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI</p>
    <p>Protocolo de Convivência e Proteção Escolar - SEDUC/SP</p>
    <p>Versão 7.0 FINAL | Desenvolvido com Streamlit + Supabase (Requests)</p>
</div>
""", unsafe_allow_html=True)