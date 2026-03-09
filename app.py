# ============================================================================
# SISTEMA CONVIVA 179 - GESTÃO DE OCORRÊNCIAS ESCOLARES
# Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI
# Versão: 8.5 FINAL - COLUNAS DO BANCO CORRIGIDAS
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

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Sistema Conviva 179",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
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
# DADOS COMPLETOS DA ESCOLA
# ============================================================================
ESCOLA_NOME = "Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI"
ESCOLA_SUBTITULO = "🌟 Escola dos Sonhos"
ESCOLA_ENDERECO = "R. Valter Souza Costa, 147 - Jardim Primavera, Ferraz de Vasconcelos - SP"
ESCOLA_CEP = "CEP: 08535-310"
ESCOLA_TELEFONE = "(11) 4675-1855"
ESCOLA_EMAIL = "e918623@educacao.sp.gov.br"
ESCOLA_LOGO = "eliane_dantas.png"
SENHA_EXCLUSAO = "040600"

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
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES DE CARREGAMENTO DE DADOS DO SUPABASE (VIA REQUESTS)
# ============================================================================

@st.cache_data(ttl=60)
def carregar_alunos():
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
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['id', 'nome', 'email', 'cargo', 'foto_url'])
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/professores?select=*", headers=HEADERS)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            if not df.empty:
                df = df.sort_values('nome')
            return df
        else:
            return pd.DataFrame(columns=['id', 'nome', 'email', 'cargo', 'foto_url'])
    except Exception as e:
        st.error(f"Erro ao carregar professores: {str(e)}")
        return pd.DataFrame(columns=['id', 'nome', 'email', 'cargo', 'foto_url'])


@st.cache_data(ttl=60)
def carregar_ocorrencias():
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamento'])
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/ocorrencias?select=*&order=id.desc", headers=HEADERS)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamento'])
    except Exception as e:
        st.error(f"Erro ao carregar ocorrências: {str(e)}")
        return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamento'])


@st.cache_data(ttl=60)
def carregar_responsaveis():
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
    ✅ COLUNAS CORRETAS: Apenas colunas que existem no banco
    """
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        # ✅ Converter lista para string (encaminhamento singular)
        if 'encaminhamento' in ocorrencia_dict and isinstance(ocorrencia_dict['encaminhamento'], list):
            ocorrencia_dict['encaminhamento'] = '| '.join(ocorrencia_dict['encaminhamento'])
        
        # ✅ REMOVER colunas que não existem no banco
        ocorrencia_dict_clean = {
            'data': ocorrencia_dict.get('data', ''),
            'aluno': ocorrencia_dict.get('aluno', ''),
            'ra': ocorrencia_dict.get('ra', ''),
            'turma': ocorrencia_dict.get('turma', ''),
            'categoria': ocorrencia_dict.get('categoria', ''),
            'gravidade': ocorrencia_dict.get('gravidade', ''),
            'relato': ocorrencia_dict.get('relato', ''),
            'professor': ocorrencia_dict.get('professor', ''),
            'encaminhamento': ocorrencia_dict.get('encaminhamento', '')
        }
        
        response = requests.post(f"{SUPABASE_URL}/rest/v1/ocorrencias", json=ocorrencia_dict_clean, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Ocorrência salva com sucesso!"
        else:
            return False, f"Erro ao salvar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao salvar ocorrência: {str(e)}")
        return False, f"Erro ao salvar: {str(e)}"


def atualizar_ocorrencia(id_ocorrencia, ocorrencia_dict):
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        if 'encaminhamento' in ocorrencia_dict and isinstance(ocorrencia_dict['encaminhamento'], list):
            ocorrencia_dict['encaminhamento'] = '| '.join(ocorrencia_dict['encaminhamento'])
        
        ocorrencia_dict_clean = {
            'data': ocorrencia_dict.get('data', ''),
            'aluno': ocorrencia_dict.get('aluno', ''),
            'ra': ocorrencia_dict.get('ra', ''),
            'turma': ocorrencia_dict.get('turma', ''),
            'categoria': ocorrencia_dict.get('categoria', ''),
            'gravidade': ocorrencia_dict.get('gravidade', ''),
            'relato': ocorrencia_dict.get('relato', ''),
            'professor': ocorrencia_dict.get('professor', ''),
            'encaminhamento': ocorrencia_dict.get('encaminhamento', '')
        }
        
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}", json=ocorrencia_dict_clean, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Ocorrência atualizada com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao atualizar ocorrência: {str(e)}")
        return False, f"Erro ao atualizar: {str(e)}"


def excluir_ocorrencia(id_ocorrencia):
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
    if not SUPABASE_URL:
        return None, "Supabase não configurado"
    try:
        file_bytes = file.getvalue()
        storage_url = SUPABASE_URL.replace("/rest/v1", "/storage/v1")
        upload_headers = HEADERS.copy()
        upload_headers["Content-Type"] = file.type
        
        response = requests.post(
            f"{storage_url}/object/fotos/{folder}/{filename}",
            data=file_bytes,
            headers=upload_headers
        )
        
        if response.status_code in [200, 201]:
            public_url = f"{storage_url}/object/public/fotos/{folder}/{filename}"
            return public_url, "Foto enviada com sucesso!"
        else:
            return None, f"Erro ao enviar foto: {response.text}"
    except Exception as e:
        st.error(f"Erro ao enviar foto: {str(e)}")
        return None, f"Erro ao enviar foto: {str(e)}"


def atualizar_foto_aluno(ra_aluno, foto_url):
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
    if df_ocorrencias is None or df_ocorrencias.empty:
        return False
    try:
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
    if not texto:
        return ""
    texto_formatado = str(texto).replace('<br/>', '\n').replace('<br>', '\n').replace('\n', '\n')
    return texto_formatado


def remover_duplicatas_encaminhamentos(encaminhamentos):
    if not encaminhamentos:
        return ""
    todos = []
    for linha in str(encaminhamentos).split('|'):
        linha = linha.strip()
        if linha and linha not in todos:
            todos.append(linha)
    return '| '.join(todos)


# ============================================================================
# FUNÇÕES DE GERAÇÃO DE PDF - OCORRÊNCIA
# ============================================================================

def gerar_pdf_ocorrencia(ocorrencia, responsaveis=None):
    buffer = io.BytesIO()
    
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
    
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4*cm)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 0.3*cm))
    except:
        pass
    
    elementos.append(Paragraph("📋 REGISTRO DE OCORRÊNCIA DISCIPLINAR", estilos['Titulo']))
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph("<b>DADOS DO(A) ESTUDANTE:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"<b>Nome:</b> {ocorrencia.get('aluno', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>RA:</b> {ocorrencia.get('ra', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Turma:</b> {ocorrencia.get('turma', 'N/A')}", estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>DADOS DA OCORRÊNCIA:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"<b>Data:</b> {ocorrencia.get('data', 'N/A')}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Categoria:</b> {ocorrencia.get('categoria', 'N/A')}", estilos['Texto']))
    
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
    
    elementos.append(Paragraph("<b>Encaminhamento:</b>", estilos['Secao']))
    encaminhamento = ocorrencia.get('encaminhamento', '')
    
    if isinstance(encaminhamento, str):
        for enc in encaminhamento.split('|'):
            if enc.strip():
                elementos.append(Paragraph(f"• {enc.strip()}", estilos['Texto']))
    else:
        elementos.append(Paragraph(str(encaminhamento), estilos['Texto']))
    
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph("<b>Professor Responsável:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"{ocorrencia.get('professor', 'N/A')}", estilos['Texto']))
    elementos.append(Spacer(1, 0.5*cm))
    
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
    
    elementos.append(Spacer(1, 0.5*cm))
    estilo_rodape = ParagraphStyle(
        'Rodape',
        parent=estilos['Normal'],
        fontSize=6,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
    
    doc.build(elementos)
    buffer.seek(0)
    
    return buffer


def gerar_pdf_comunicado(ocorrencia, responsaveis=None):
    buffer = io.BytesIO()
    
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
    
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4*cm)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 0.3*cm))
    except:
        pass
    
    elementos.append(Paragraph("📬 COMUNICADO AOS PAIS/RESPONSÁVEIS", estilos['TituloComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph(f"Prezados responsáveis pelo(a) estudante <b>{ocorrencia.get('aluno', 'N/A')}</b>,", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("Venho por meio deste comunicar que foi registrada uma ocorrência disciplinar conforme detalhes abaixo:", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph("<b>DADOS DA OCORRÊNCIA:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"<b>Data:</b> {ocorrencia.get('data', 'N/A')}", estilos['TextoComunicado']))
    elementos.append(Paragraph(f"<b>Turma:</b> {ocorrencia.get('turma', 'N/A')}", estilos['TextoComunicado']))
    elementos.append(Paragraph(f"<b>Categoria:</b> {ocorrencia.get('categoria', 'N/A')}", estilos['TextoComunicado']))
    
    gravidade = ocorrencia.get('gravidade', 'N/A')
    cor_gravidade = CORES_GRAVIDADE.get(gravidade, '#9E9E9E')
    elementos.append(Paragraph(
        f"<b>Gravidade:</b> <font color='{cor_gravidade}'><b>{gravidade}</b></font>",
        estilos['TextoComunicado']
    ))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>Relato:</b>", estilos['Secao']))
    relato_formatado = formatar_texto(ocorrencia.get('relato', ''))
    elementos.append(Paragraph(relato_formatado, estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>Encaminhamento:</b>", estilos['Secao']))
    encaminhamento = ocorrencia.get('encaminhamento', '')
    
    if isinstance(encaminhamento, str):
        for enc in encaminhamento.split('|'):
            if enc.strip():
                elementos.append(Paragraph(f"• {enc.strip()}", estilos['TextoComunicado']))
    else:
        elementos.append(Paragraph(str(encaminhamento), estilos['TextoComunicado']))
    
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph("<b>Professor Responsável:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"{ocorrencia.get('professor', 'N/A')}", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
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
    
    elementos.append(Spacer(1, 0.5*cm))
    estilo_rodape = ParagraphStyle(
        'Rodape',
        parent=estilos['Normal'],
        fontSize=6,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
    
    doc.build(elementos)
    buffer.seek(0)
    
    return buffer


# ============================================================================
# INTERFACE PRINCIPAL - CABEÇALHO E MENU LATERAL
# ============================================================================

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
    
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    df_professores = carregar_professores()
    
    if not df_ocorrencias.empty:
        total_ocorrencias = len(df_ocorrencias)
        total_gravissima = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Gravíssima'])
        total_grave = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Grave'])
        total_media = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Média'])
        total_leve = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Leve'])
        turmas_afetadas = df_ocorrencias['turma'].nunique()
        
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
        
        st.subheader("📋 Últimas Ocorrências")
        st.dataframe(df_ocorrencias.head(10), use_container_width=True)
    
    else:
        st.info("📭 Nenhuma ocorrência registrada ainda.")
    
    if not df_alunos.empty:
        st.subheader("👥 Resumo de Alunos")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Alunos", len(df_alunos))
        with col2:
            st.metric("Total de Turmas", df_alunos['turma'].nunique())
    
    if not df_professores.empty:
        st.subheader("👨‍🏫 Resumo de Professores")
        st.metric("Total de Professores", len(df_professores))


# ============================================================================
# PÁGINA: REGISTRAR OCORRÊNCIA (COLUNAS CORRIGIDAS)
# ============================================================================

elif menu == "📝 Registrar Ocorrência":
    st.title("📝 Registrar Nova Ocorrência")
    
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    
    if st.session_state.get('ocorrencia_salva_sucesso', False):
        st.markdown('<div class="success-box">✅ OCORRÊNCIA(S) REGISTRADA(S) COM SUCESSO!</div>', unsafe_allow_html=True)
        st.session_state.ocorrencia_salva_sucesso = False
    
    if df_alunos.empty:
        st.warning("⚠️ Nenhum aluno cadastrado. Importe alunos primeiro.")
    else:
        st.subheader("🏫 Selecionar Turma(s)")
        modo_multiplas_turmas = st.checkbox("📚 Registrar para múltiplas turmas", key="modo_multiplas_turmas")
        turmas = df_alunos["turma"].unique().tolist()
        
        if modo_multiplas_turmas:
            turmas_selecionadas = st.multiselect("Selecione as Turmas", turmas, key="turmas_multi")
        else:
            turma_selecionada = st.selectbox("Selecione a Turma", turmas, key="turma_unica")
            turmas_selecionadas = [turma_selecionada] if turma_selecionada else []
        
        if turmas_selecionadas:
            alunos = df_alunos[df_alunos["turma"].isin(turmas_selecionadas)].copy()
            
            if len(alunos) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 👥 Selecionar Estudante(s)")
                    modo_multiplo = st.checkbox("👥 Múltiplos estudantes", key="modo_multiplo")
                    
                    if modo_multiplo:
                        alunos_selecionados = st.multiselect(
                            "Selecione os Estudantes",
                            alunos["nome"].tolist(),
                            key="alunos_multiselect"
                        )
                    else:
                        lista_alunos = alunos['nome'].tolist()
                        aluno_selecionado = st.selectbox("Selecione o Aluno", lista_alunos, key="aluno_unico")
                        alunos_selecionados = [aluno_selecionado] if aluno_selecionado else []
                
                with col2:
                    st.markdown("### 📅 Data e Hora")
                    data = st.date_input("Data", value=datetime.now().date(), key="data_input")
                    hora = st.time_input("Hora", value=datetime.now().time(), key="hora_input")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    categoria_grupo = st.selectbox("📁 Categoria", list(CATEGORIAS_OCORRENCIAS.keys()), key="cat_grupo")
                    categorias_grupo = list(CATEGORIAS_OCORRENCIAS[categoria_grupo].keys())
                    categoria = st.selectbox("📋 Ocorrência", categorias_grupo, key="cat_ocorr")
                
                with col2:
                    gravidade = CATEGORIAS_OCORRENCIAS[categoria_grupo].get(categoria, "Leve")
                    gravidade_select = st.selectbox(
                        "⚡ Gravidade",
                        ["Gravíssima", "Grave", "Média", "Leve"],
                        index=["Gravíssima", "Grave", "Média", "Leve"].index(gravidade),
                        key="grav_select"
                    )
                
                if categoria in FLUXO_ACOES:
                    st.warning(f"📌 {FLUXO_ACOES[categoria]}")
                
                relato = st.text_area("📝 Relato da Ocorrência", height=200, key="relato_input")
                
                st.subheader("🔄 Encaminhamento")
                encaminhamentos_disponiveis = ENCAMINHAMENTOS_POR_GRAVIDADE.get(gravidade_select, [])
                encaminhamentos_selecionados = st.multiselect(
                    "Selecione os encaminhamentos",
                    encaminhamentos_disponiveis,
                    default=encaminhamentos_disponiveis[:2] if encaminhamentos_disponiveis else [],
                    key="encam_select"
                )
                
                # ✅ Converter lista para string (singular)
                encaminhamento_str = '| '.join(encaminhamentos_selecionados) if encaminhamentos_selecionados else ''
                
                df_professores = carregar_professores()
                if not df_professores.empty:
                    prof = st.selectbox("👨‍🏫 Professor Responsável", ["Selecione..."] + df_professores['nome'].tolist(), key="prof_select")
                else:
                    prof = st.text_input("👨‍🏫 Professor Responsável", key="prof_input")
                
                st.markdown("---")
                
                if st.button("💾 Salvar Ocorrência", type="primary", key="btn_salvar"):
                    if not alunos_selecionados:
                        st.error("❌ Selecione pelo menos um estudante!")
                    elif not prof or prof == "Selecione...":
                        st.error("❌ Selecione o professor responsável!")
                    elif not relato:
                        st.error("❌ Preencha o relato da ocorrência!")
                    else:
                        data_str = f"{data.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}"
                        categoria_str = categoria
                        
                        contagem_salvas = 0
                        contagem_duplicadas = 0
                        erros = 0
                        
                        for nome_aluno in alunos_selecionados:
                            aluno_info = alunos[alunos["nome"] == nome_aluno]
                            
                            if not aluno_info.empty:
                                ra_aluno = str(aluno_info["ra"].values[0])
                                turma_aluno = str(aluno_info["turma"].values[0])
                                
                                if verificar_ocorrencia_duplicada(ra_aluno, categoria_str, data_str, df_ocorrencias):
                                    contagem_duplicadas += 1
                                else:
                                    # ✅ COLUNAS CORRETAS - APENAS O QUE EXISTE NO BANCO
                                    ocorrencia_dict = {
                                        'data': data_str,
                                        'aluno': nome_aluno,
                                        'ra': ra_aluno,
                                        'turma': turma_aluno,
                                        'categoria': categoria_str,
                                        'gravidade': gravidade_select,
                                        'relato': relato,
                                        'professor': prof,
                                        'encaminhamento': encaminhamento_str  # ✅ SINGULAR, SEM 'evidencias' ou 'testemunhas'
                                    }
                                    
                                    sucesso, mensagem = salvar_ocorrencia(ocorrencia_dict)
                                    
                                    if sucesso:
                                        contagem_salvas += 1
                                    else:
                                        erros += 1
                                        st.error(f"Erro para {nome_aluno}: {mensagem}")
                        
                        if contagem_salvas > 0:
                            st.success(f"✅ {contagem_salvas} ocorrência(s) registrada(s) com sucesso!")
                        if contagem_duplicadas > 0:
                            st.warning(f"⚠️ {contagem_duplicadas} ocorrência(s) já existiam (ignorado)")
                        if erros > 0:
                            st.error(f"❌ {erros} erro(s) ao salvar")
                        
                        if contagem_salvas > 0:
                            st.session_state.ocorrencia_salva_sucesso = True
                            carregar_ocorrencias.clear()
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
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_gravidade = st.multiselect("Gravidade", ["Gravíssima", "Grave", "Média", "Leve"])
        
        with col2:
            filtro_categoria = st.multiselect("Categoria", df_ocorrencias['categoria'].unique())
        
        with col3:
            filtro_turma = st.multiselect("Turma", df_alunos['turma'].unique().tolist())
        
        df_filtrado = df_ocorrencias.copy()
        
        if filtro_gravidade:
            df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(filtro_gravidade)]
        
        if filtro_categoria:
            df_filtrado = df_filtrado[df_filtrado['categoria'].isin(filtro_categoria)]
        
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        
        st.markdown(f"**Total:** {len(df_filtrado)} ocorrência(s)")
        st.dataframe(df_filtrado, use_container_width=True)
        
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
        
        st.subheader("🗑️ Excluir Ocorrência")
        id_excluir = st.number_input("ID para Excluir", min_value=1, step=1, key="excluir_occ")
        
        if st.button("🗑️ Excluir"):
            senha = st.text_input("Digite a senha de exclusão (040600)", type="password")
            if senha == SENHA_EXCLUSAO:
                sucesso, msg = excluir_ocorrencia(id_excluir)
                if sucesso:
                    st.success(f"✅ {msg}")
                    carregar_ocorrencias.clear()
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
        
        st.subheader("🗑️ Excluir Aluno")
        ra_excluir = st.text_input("RA do Aluno para Excluir")
        
        if st.button("🗑️ Excluir Aluno"):
            senha = st.text_input("Digite a senha de exclusão (040600)", type="password", key="senha_aluno")
            if senha == SENHA_EXCLUSAO:
                sucesso, msg = excluir_aluno(ra_excluir)
                if sucesso:
                    st.success(f"✅ {msg}")
                    carregar_alunos.clear()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            else:
                st.error("❌ Senha incorreta!")
        
        st.subheader("📷 Upload de Foto")
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
    
    st.subheader("📝 Novo Professor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome_prof = st.text_input("Nome Completo *", key="nome_prof_input")
        email_prof = st.text_input("Email", key="email_prof_input")
    
    with col2:
        cargo_prof = st.text_input("Cargo", key="cargo_prof_input")
        foto_prof = st.file_uploader("Foto (opcional)", type=['jpg', 'jpeg', 'png'], key="foto_prof_input")
    
    if st.session_state.get('editando_prof', None) is not None:
        st.info(f"✏️ Editando professor ID: {st.session_state.editando_prof}")
        
        prof_atual = df_professores[df_professores['id'] == st.session_state.editando_prof].iloc[0]
        
        if st.button("💾 Atualizar Professor", key="btn_atualizar_prof"):
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
        
        if st.button("❌ Cancelar Edição", key="btn_cancelar_prof"):
            st.session_state.editando_prof = None
            st.rerun()
    else:
        if st.button("💾 Salvar Professor", key="btn_salvar_prof"):
            if nome_prof:
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
                    if st.button("✏️", key=f"edit_prof_{prof.get('id', idx)}"):
                        st.session_state.editando_prof = prof.get('id')
                        st.rerun()
                
                with col5:
                    if st.button("🗑️", key=f"del_prof_{prof.get('id', idx)}"):
                        senha = st.text_input("Senha (040600)", type="password", key=f"senha_prof_{prof.get('id', idx)}")
                        if senha == SENHA_EXCLUSAO:
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
        st.subheader("🔍 Filtros")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_turma = st.multiselect("Turma", df_alunos['turma'].unique().tolist())
        
        with col2:
            filtro_gravidade = st.multiselect("Gravidade", ["Gravíssima", "Grave", "Média", "Leve"])
        
        with col3:
            filtro_categoria = st.multiselect("Categoria", df_ocorrencias['categoria'].unique())
        
        df_filtrado = df_ocorrencias.copy()
        
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        
        if filtro_gravidade:
            df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(filtro_gravidade)]
        
        if filtro_categoria:
            df_filtrado = df_filtrado[df_filtrado['categoria'].isin(filtro_categoria)]
        
        st.markdown(f"**Total:** {len(df_filtrado)} ocorrência(s)")
        st.markdown("---")
        
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
    st.title("🖨️ Imprimir PDF de Ocorrência")
    
    df_ocorrencias = carregar_ocorrencias()
    df_responsaveis = carregar_responsaveis()
    
    if not df_ocorrencias.empty:
        df_ocorrencias_sorted = df_ocorrencias.sort_values('id', ascending=False)
        
        opcoes_ocorrencias = []
        for idx, occ in df_ocorrencias_sorted.iterrows():
            opcao = f"ID {occ['id']} | {occ['data']} | {occ['aluno']} | {occ['categoria']}"
            opcoes_ocorrencias.append(opcao)
        
        ocorrencia_selecionada = st.selectbox(
            "📋 Selecione a Ocorrência para Imprimir",
            opcoes_ocorrencias,
            help="Selecione a ocorrência desejada na lista abaixo"
        )
        
        if ocorrencia_selecionada:
            id_selecionado = int(ocorrencia_selecionada.split(' | ')[0].replace('ID ', ''))
            ocorrencia = df_ocorrencias[df_ocorrencias['id'] == id_selecionado].iloc[0].to_dict()
            
            st.markdown("### 📄 Preview da Ocorrência")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**ID:** {ocorrencia.get('id', 'N/A')}")
                st.info(f"**Data:** {ocorrencia.get('data', 'N/A')}")
                st.info(f"**Aluno:** {ocorrencia.get('aluno', 'N/A')}")
            with col2:
                st.info(f"**Turma:** {ocorrencia.get('turma', 'N/A')}")
                st.info(f"**Categoria:** {ocorrencia.get('categoria', 'N/A')}")
                st.info(f"**Gravidade:** {ocorrencia.get('gravidade', 'N/A')}")
            
            tipo_documento = st.selectbox(
                "📄 Tipo de Documento",
                ["Ocorrência", "Comunicado aos Pais"],
                help="Escolha o tipo de documento a ser gerado"
            )
            
            if st.button("🖨️ Gerar PDF", type="primary"):
                if tipo_documento == "Ocorrência":
                    pdf_buffer = gerar_pdf_ocorrencia(ocorrencia, df_responsaveis)
                    nome_arquivo = f"ocorrencia_{id_selecionado}_{ocorrencia.get('aluno', 'aluno')}.pdf"
                else:
                    pdf_buffer = gerar_pdf_comunicado(ocorrencia, df_responsaveis)
                    nome_arquivo = f"comunicado_{id_selecionado}_{ocorrencia.get('aluno', 'aluno')}.pdf"
                
                st.download_button(
                    label="📥 Baixar PDF",
                    data=pdf_buffer,
                    file_name=nome_arquivo,
                    mime="application/pdf"
                )
                st.success("✅ PDF gerado com sucesso! Clique em Baixar para salvar.")
    else:
        st.info("📭 Nenhuma ocorrência registrada para imprimir.")


# ============================================================================
# PÁGINA: CONFIGURAÇÕES
# ============================================================================

elif menu == "⚙️ Configurações":
    st.title("⚙️ Configurações do Sistema")
    
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
    
    st.subheader("📋 Protocolo 179")
    
    col1, col2 = st.columns(2)
    
    with col1:
        total_categorias = sum(len(v) for v in CATEGORIAS_OCORRENCIAS.values())
        st.metric("Total de Categorias", total_categorias)
    
    with col2:
        st.metric("Níveis de Gravidade", "4 (Gravíssima, Grave, Média, Leve)")
    
    st.subheader("🔐 Configurações de Segurança")
    
    st.warning("""
    ⚠️ **Senha para Exclusão:** 040600
    
    Esta senha é necessária para excluir:
    - Ocorrências
    - Alunos
    - Professores
    - Responsáveis
    """)
    
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
    
    st.subheader("📊 Informações do Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Versão", "8.5 FINAL")
    
    with col2:
        st.metric("Framework", "Streamlit")
    
    with col3:
        st.metric("Python", "3.9+")


# ============================================================================
# PÁGINA: BACKUP
# ============================================================================

elif menu == "💾 Backup":
    st.title("💾 Backup e Restauração")
    
    st.subheader("📥 Gerar Backup")
    
    st.info("💡 O backup contém todos os dados do sistema: alunos, professores, ocorrências e responsáveis.")
    
    if st.button("📥 Gerar Backup Completo"):
        df_alunos = carregar_alunos()
        df_professores = carregar_professores()
        df_ocorrencias = carregar_ocorrencias()
        df_responsaveis = carregar_responsaveis()
        
        backup_data = {
            'alunos': df_alunos.to_dict('records') if not df_alunos.empty else [],
            'professores': df_professores.to_dict('records') if not df_professores.empty else [],
            'ocorrencias': df_ocorrencias.to_dict('records') if not df_ocorrencias.empty else [],
            'responsaveis': df_responsaveis.to_dict('records') if not df_responsaveis.empty else [],
            'data_backup': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'versao_sistema': '8.5 FINAL'
        }
        
        json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        st.download_button(
            label="📥 Baixar Backup JSON",
            data=json_str,
            file_name=f"backup_conviva_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )
        
        st.success("✅ Backup gerado com sucesso!")
    
    st.markdown("---")
    
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
            
            if senha == SENHA_EXCLUSAO:
                try:
                    backup_data = json.load(arquivo_backup)
                    
                    contagem_alunos = 0
                    contagem_professores = 0
                    contagem_ocorrencias = 0
                    contagem_responsaveis = 0
                    
                    if 'alunos' in backup_data and backup_data['alunos']:
                        for aluno in backup_data['alunos']:
                            salvar_aluno(aluno)
                            contagem_alunos += 1
                    
                    if 'professores' in backup_data and backup_data['professores']:
                        for professor in backup_data['professores']:
                            salvar_professor(professor)
                            contagem_professores += 1
                    
                    if 'ocorrencias' in backup_data and backup_data['ocorrencias']:
                        for ocorrencia in backup_data['ocorrencias']:
                            salvar_ocorrencia(ocorrencia)
                            contagem_ocorrencias += 1
                    
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
    <p>Versão 8.5 FINAL | Desenvolvido com Streamlit + Supabase (Requests)</p>
</div>
""", unsafe_allow_html=True)