# ============================================================================
# SISTEMA CONVIVA 179 - GESTÃO DE OCORRÊNCIAS ESCOLARES
# Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI
# Versão: 10.2 FINAL - CATEGORIAS REORGANIZADAS + TODAS FUNCIONALIDADES
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
# ✅ PROTOCOLO 179 COMPLETO - CATEGORIAS REORGANIZADAS
# ============================================================================
CATEGORIAS_OCORRENCIAS = {
    "🔴 Violência Física": {
        "Agressão Física": "Grave",
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
        "Uso Inadequado de Dispositivos Eletrônicos": "Leve"
    },
    "📋 Infrações Administrativas e Disciplinares": {
        "Copiar atividades / Colar em avaliações": "Leve",
        "Falsificar assinatura de responsáveis": "Média",
        "Indisciplina": "Leve",
        "Comportamento inadequado para o espaço": "Leve",
        "Dormir em sala de aula": "Leve",
        "Não realizar atividades": "Leve",
        "Outros": "Leve"
    },
    "👨‍👩‍👧‍👦 Família e Vulnerabilidade": {
        "Violência Doméstica / Maus Tratos": "Gravíssima",
        "Vulnerabilidade Familiar / Negligência": "Gravíssima",
        "Alerta de Desaparecimento": "Gravíssima",
        "Sequestro": "Gravíssima",
        "Homicídio / Homicídio Tentado": "Gravíssima",
        "Feminicídio": "Gravíssima",
        "Incitamento a Atos Infracionais": "Grave"
    }
}

# ============================================================================
# CORES POR CATEGORIA PARA GRÁFICOS
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
    "📋 Infrações Administrativas e Disciplinares": "#9E9E9E",
    "👨‍👩‍👧‍👦 Família e Vulnerabilidade": "#EC407A"
}

# ============================================================================
# CORES POR GRAVIDADE
# ============================================================================
CORES_GRAVIDADE = {
    "Gravíssima": "#D32F2F",
    "Grave": "#F57C00",
    "Média": "#FFB300",
    "Leve": "#4CAF50"
}

# ============================================================================
# FLUXO DE AÇÕES - SEMPRE VISÍVEL QUANDO HOUVER INDICAÇÃO
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
    "Homicídio / Homicídio Tentado": "⚖️ CRIME HEDIONDO. Registrar B.O.",
    "Crimes Cibernéticos": "🔒 B.O. (Delegacia de Crimes Digitais). Preservar provas (prints, URLs).",
    "Fake News / Disseminação de Informações Falsas": "📰 Trabalho educativo. Notificar famílias. Registrar em ata.",
    "Violação de Dados": "🔒 B.O. Preservar provas. Notificar afetados.",
    "Copiar atividades / Colar em avaliações": "📝 Registro em ata. Comunicação aos pais. Medidas pedagógicas.",
    "Falsificar assinatura de responsáveis": "⚠️ Comunicação urgente aos pais. Registro em ata. Orientação.",
    "Indisciplina": "📋 Registro em ata. Orientação ao estudante. Comunicação aos pais."
}

# ============================================================================
# ENCAMINHAMENTOS AUTOMÁTICOS POR GRAVIDADE (PROTOCOLO 179)
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
        "Registro em Ata de Ocorrência",
        "Encaminhamento à Coordenação"
    ],
    "Grave": [
        "Orientação ao Estudante",
        "Comunicação aos Pais/Responsáveis",
        "Registro em Ata de Ocorrência",
        "Encaminhamento à Coordenação",
        "Encaminhamento à Direção",
        "Acompanhamento Pedagógico"
    ],
    "Gravíssima": [
        "Orientação ao Estudante",
        "Comunicação aos Pais/Responsáveis",
        "Registro em Ata de Ocorrência",
        "Encaminhamento à Coordenação",
        "Encaminhamento à Direção",
        "Acompanhamento Pedagógico",
        "Acompanhamento Psicopedagógico",
        "Registro de B.O.",
        "Acionamento Conselho Tutelar"
    ]
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
if 'turma_para_deletar' not in st.session_state:
    st.session_state.turma_para_deletar = None
if 'turma_selecionada' not in st.session_state:
    st.session_state.turma_selecionada = None
if 'ocorrencia_excluida_sucesso' not in st.session_state:
    st.session_state.ocorrencia_excluida_sucesso = False
if 'ocorrencia_editada_sucesso' not in st.session_state:
    st.session_state.ocorrencia_editada_sucesso = False
if 'gravidade_alterada' not in st.session_state:
    st.session_state.gravidade_alterada = False

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
.card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid #667eea;
}
.card-title {
    font-weight: bold;
    color: #333;
}
.card-value {
    font-size: 1.5rem;
    color: #667eea;
}
.fluxo-alert {
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}
.gravidade-alert {
    background: #f8d7da;
    border: 2px solid #dc3545;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    color: #721c24;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES DE CARREGAMENTO DE DADOS DO SUPABASE (VIA REQUESTS)
# ============================================================================

@st.cache_data(ttl=60)
def carregar_alunos():
    """Carrega todos os alunos do banco de dados Supabase."""
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['nome', 'ra', 'turma', 'nascimento', 'responsavel', 'telefone', 'foto_url', 'situacao'])
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/alunos?select=*", headers=HEADERS)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            if not df.empty:
                df = df.sort_values('nome')
            return df
        else:
            return pd.DataFrame(columns=['nome', 'ra', 'turma', 'nascimento', 'responsavel', 'telefone', 'foto_url', 'situacao'])
    except Exception as e:
        st.error(f"Erro ao carregar alunos: {str(e)}")
        return pd.DataFrame(columns=['nome', 'ra', 'turma', 'nascimento', 'responsavel', 'telefone', 'foto_url', 'situacao'])


@st.cache_data(ttl=60)
def carregar_professores():
    """Carrega todos os professores do banco de dados Supabase."""
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
    """Carrega todas as ocorrências do banco de dados Supabase."""
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamento'])
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/ocorrencias?select=id,data,aluno,ra,turma,categoria,gravidade,relato,professor,encaminhamento&order=id.desc",
            headers=HEADERS
        )
        if response.status_code == 200:
            dados = response.json()
            df = pd.DataFrame(dados)
            return df
        else:
            st.error(f"Erro ao carregar: {response.text}")
            return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamento'])
    except Exception as e:
        st.error(f"Erro ao carregar ocorrências: {str(e)}")
        return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamento'])


@st.cache_data(ttl=60)
def carregar_responsaveis():
    """Carrega todos os responsáveis do banco de dados Supabase."""
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


@st.cache_data(ttl=60)
def carregar_turmas():
    """Carrega todas as turmas únicas do banco de dados."""
    df_alunos = carregar_alunos()
    if not df_alunos.empty and 'turma' in df_alunos.columns:
        turmas_info = df_alunos.groupby('turma').size().reset_index(name='total_alunos')
        return turmas_info
    return pd.DataFrame(columns=['turma', 'total_alunos'])


# ============================================================================
# FUNÇÕES DE SALVAMENTO DE DADOS NO SUPABASE (VIA REQUESTS)
# ============================================================================

def salvar_ocorrencia(ocorrencia_dict):
    """Salva uma ocorrência no banco de dados Supabase."""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
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
        
        if isinstance(ocorrencia_dict_clean['encaminhamento'], list):
            ocorrencia_dict_clean['encaminhamento'] = '| '.join(ocorrencia_dict_clean['encaminhamento'])
        
        response = requests.post(f"{SUPABASE_URL}/rest/v1/ocorrencias", json=ocorrencia_dict_clean, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Ocorrência salva com sucesso!"
        else:
            return False, f"Erro ao salvar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao salvar ocorrência: {str(e)}")
        return False, f"Erro ao salvar: {str(e)}"


def atualizar_ocorrencia(id_ocorrencia, ocorrencia_dict):
    """Atualiza uma ocorrência existente no banco de dados Supabase."""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
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
        
        if isinstance(ocorrencia_dict_clean['encaminhamento'], list):
            ocorrencia_dict_clean['encaminhamento'] = '| '.join(ocorrencia_dict_clean['encaminhamento'])
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}",
            json=ocorrencia_dict_clean,
            headers=HEADERS
        )
        
        if response.status_code in [200, 201]:
            return True, "Ocorrência atualizada com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao atualizar ocorrência: {str(e)}")
        return False, f"Erro ao atualizar: {str(e)}"


def excluir_ocorrencia(id_ocorrencia):
    """Exclui uma ocorrência do banco de dados Supabase."""
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
    """Salva um aluno no banco de dados Supabase."""
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
    """Atualiza um aluno existente no banco de dados Supabase."""
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
    """Exclui um aluno do banco de dados Supabase."""
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


def excluir_alunos_por_turma(turma):
    """Exclui todos os alunos de uma turma específica."""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/alunos?turma=eq.{turma}", headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, f"Turma {turma} excluída com sucesso!"
        else:
            return False, f"Erro ao excluir turma: {response.text}"
    except Exception as e:
        st.error(f"Erro ao excluir turma: {str(e)}")
        return False, f"Erro ao excluir: {str(e)}"


def salvar_professor(professor_dict):
    """Salva um professor no banco de dados Supabase."""
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
    """Atualiza um professor existente no banco de dados Supabase."""
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
    """Exclui um professor do banco de dados Supabase."""
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
    """Salva um responsável no banco de dados Supabase."""
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
    """Atualiza um responsável existente no banco de dados Supabase."""
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
    """Exclui um responsável do banco de dados Supabase."""
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
    """Faz upload de foto para o Supabase Storage."""
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
    """Atualiza a URL da foto de um aluno no banco de dados."""
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
    """Atualiza a URL da foto de um professor no banco de dados."""
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
    """Verifica se já existe uma ocorrência igual para o mesmo aluno na mesma data."""
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
    """Formata texto para exibição no PDF, convertendo quebras de linha."""
    if not texto:
        return ""
    texto_formatado = str(texto).replace('<br/>', '\n').replace('<br>', '\n').replace('\n', '\n')
    return texto_formatado


def remover_duplicatas_encaminhamentos(encaminhamentos):
    """Remove encaminhamentos duplicados de uma lista."""
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
    """Gera PDF de ocorrência com layout profissional."""
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
    
    # CABEÇALHO COM LOGO - 16cm x 4cm
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
    elementos.append(Paragraph(f"<b>Nome:</b> {ocorrencia.get('aluno', 'N/A') or 'N/A'}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>RA:</b> {ocorrencia.get('ra', 'N/A') or 'N/A'}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Turma:</b> {ocorrencia.get('turma', 'N/A') or 'N/A'}", estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>DADOS DA OCORRÊNCIA:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"<b>Data:</b> {ocorrencia.get('data', 'N/A') or 'N/A'}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Categoria:</b> {ocorrencia.get('categoria', 'N/A') or 'N/A'}", estilos['Texto']))
    
    gravidade = ocorrencia.get('gravidade', 'N/A') or 'N/A'
    cor_gravidade = CORES_GRAVIDADE.get(gravidade, '#9E9E9E')
    elementos.append(Paragraph(
        f"<b>Gravidade:</b> <font color='{cor_gravidade}'><b>{gravidade}</b></font>",
        estilos['Texto']
    ))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>Relato:</b>", estilos['Secao']))
    relato = ocorrencia.get('relato', 'N/A') or 'N/A'
    relato_formatado = formatar_texto(relato)
    elementos.append(Paragraph(relato_formatado, estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>Encaminhamento:</b>", estilos['Secao']))
    encaminhamento = ocorrencia.get('encaminhamento', '') or ''
    
    if isinstance(encaminhamento, str) and encaminhamento:
        for enc in encaminhamento.split('|'):
            if enc.strip():
                elementos.append(Paragraph(f"• {enc.strip()}", estilos['Texto']))
    elif isinstance(encaminhamento, list):
        for enc in encaminhamento:
            if enc.strip():
                elementos.append(Paragraph(f"• {enc.strip()}", estilos['Texto']))
    else:
        elementos.append(Paragraph("Nenhum encaminhamento registrado", estilos['Texto']))
    
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph("<b>Professor Responsável:</b>", estilos['Secao']))
    professor = ocorrencia.get('professor', 'N/A') or 'N/A'
    elementos.append(Paragraph(f"{professor}", estilos['Texto']))
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
    """Gera PDF de comunicado aos pais com layout profissional."""
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
    
    elementos.append(Paragraph(f"Prezados responsáveis pelo(a) estudante <b>{ocorrencia.get('aluno', 'N/A') or 'N/A'}</b>,", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("Venho por meio deste comunicar que foi registrada uma ocorrência disciplinar conforme detalhes abaixo:", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph("<b>DADOS DA OCORRÊNCIA:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"<b>Data:</b> {ocorrencia.get('data', 'N/A') or 'N/A'}", estilos['TextoComunicado']))
    elementos.append(Paragraph(f"<b>Turma:</b> {ocorrencia.get('turma', 'N/A') or 'N/A'}", estilos['TextoComunicado']))
    elementos.append(Paragraph(f"<b>Categoria:</b> {ocorrencia.get('categoria', 'N/A') or 'N/A'}", estilos['TextoComunicado']))
    
    gravidade = ocorrencia.get('gravidade', 'N/A') or 'N/A'
    cor_gravidade = CORES_GRAVIDADE.get(gravidade, '#9E9E9E')
    elementos.append(Paragraph(
        f"<b>Gravidade:</b> <font color='{cor_gravidade}'><b>{gravidade}</b></font>",
        estilos['TextoComunicado']
    ))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>Relato:</b>", estilos['Secao']))
    relato = ocorrencia.get('relato', 'N/A') or 'N/A'
    relato_formatado = formatar_texto(relato)
    elementos.append(Paragraph(relato_formatado, estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>Encaminhamento:</b>", estilos['Secao']))
    encaminhamento = ocorrencia.get('encaminhamento', '') or ''
    
    if isinstance(encaminhamento, str) and encaminhamento:
        for enc in encaminhamento.split('|'):
            if enc.strip():
                elementos.append(Paragraph(f"• {enc.strip()}", estilos['TextoComunicado']))
    elif isinstance(encaminhamento, list):
        for enc in encaminhamento:
            if enc.strip():
                elementos.append(Paragraph(f"• {enc.strip()}", estilos['TextoComunicado']))
    else:
        elementos.append(Paragraph("Nenhum encaminhamento registrado", estilos['TextoComunicado']))
    
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph("<b>Professor Responsável:</b>", estilos['Secao']))
    professor = ocorrencia.get('professor', 'N/A') or 'N/A'
    elementos.append(Paragraph(f"{professor}", estilos['TextoComunicado']))
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
        "📥 Importar Alunos (Turmas)",
        "📋 Gerenciar Turmas",
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
    df_turmas = carregar_turmas()
    
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
    
    if not df_turmas.empty:
        st.subheader("🏫 Resumo de Turmas")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Turmas", len(df_turmas))
        with col2:
            st.metric("Total de Alunos", len(df_alunos))
    
    if not df_professores.empty:
        st.subheader("👨‍🏫 Resumo de Professores")
        st.metric("Total de Professores", len(df_professores))


# ============================================================================
# PÁGINA: IMPORTAR ALUNOS (TURMAS)
# ============================================================================

elif menu == "📥 Importar Alunos (Turmas)":
    st.title("📥 Importar Alunos por Turma")
    
    st.info("""
    💡 **Como importar:**
    1. Digite o nome da turma (Ex: 6º Ano A, 7º Ano B)
    2. Selecione o arquivo CSV da SEDUC
    3. Clique em "🚀 Importar Alunos"
    
    **Colunas necessárias no CSV:**
    - RA
    - Nome do Aluno
    - Data de Nascimento
    - Situação do Aluno
    """)
    
    turma_alunos = st.text_input(
        "🏫 Qual a TURMA destes alunos?",
        placeholder="Ex: 6º Ano A, 7º Ano B, 8º Ano C",
        key="turma_import"
    )
    
    arquivo_upload = st.file_uploader(
        "Selecione o arquivo CSV da SEDUC",
        type=["csv"],
        key="arquivo_csv"
    )
    
    if arquivo_upload is not None:
        try:
            df_import = pd.read_csv(arquivo_upload, sep=';', encoding='utf-8-sig')
            st.success(f"✅ Arquivo lido com sucesso! {len(df_import)} alunos encontrados.")
            st.write("### Pré-visualização:")
            st.dataframe(df_import.head())
            
            colunas_csv = df_import.columns.tolist()
            st.write("### 🔍 Mapeamento de Colunas")
            
            col1, col2 = st.columns(2)
            with col1:
                mapeamento_ra = st.selectbox("Coluna do RA", colunas_csv, index=colunas_csv.index("RA") if "RA" in colunas_csv else 0)
                mapeamento_nome = st.selectbox("Coluna do Nome", colunas_csv, index=colunas_csv.index("Nome do Aluno") if "Nome do Aluno" in colunas_csv else 0)
            with col2:
                mapeamento_nascimento = st.selectbox("Coluna da Data de Nascimento", colunas_csv, index=colunas_csv.index("Data de Nascimento") if "Data de Nascimento" in colunas_csv else 0)
                mapeamento_situacao = st.selectbox("Coluna da Situação", colunas_csv, index=colunas_csv.index("Situação do Aluno") if "Situação do Aluno" in colunas_csv else 0)
            
            colunas_necessarias = [mapeamento_ra, mapeamento_nome, mapeamento_nascimento, mapeamento_situacao]
            faltantes = [c for c in colunas_necessarias if c not in colunas_csv]
            
            if faltantes:
                st.error(f"❌ Colunas não encontradas: {', '.join(faltantes)}")
            else:
                df_alunos = carregar_alunos()
                turmas_existentes = df_alunos['turma'].unique().tolist() if not df_alunos.empty else []
                
                if turma_alunos in turmas_existentes:
                    st.warning(f"⚠️ A turma **{turma_alunos}** já existe no sistema!")
                    st.info("💡 Se importar novamente, os alunos serão **atualizados** (não duplicados).")
                
                if st.button("🚀 Importar Alunos", type="primary"):
                    if not turma_alunos:
                        st.error("❌ Preencha o nome da turma!")
                    else:
                        contagem_novos = 0
                        contagem_atualizados = 0
                        erros = 0
                        
                        for idx, row in df_import.iterrows():
                            try:
                                ra_str = str(row[mapeamento_ra]).strip()
                                if not ra_str or ra_str == 'nan':
                                    erros += 1
                                    continue
                                
                                aluno = {
                                    'ra': ra_str,
                                    'nome': str(row[mapeamento_nome]).strip(),
                                    'data_nascimento': str(row[mapeamento_nascimento]).strip(),
                                    'situacao': str(row[mapeamento_situacao]).strip(),
                                    'turma': turma_alunos
                                }
                                
                                aluno_existente = df_alunos[df_alunos['ra'] == ra_str]
                                
                                if not aluno_existente.empty:
                                    if atualizar_aluno(ra_str, aluno):
                                        contagem_atualizados += 1
                                    else:
                                        erros += 1
                                else:
                                    if salvar_aluno(aluno):
                                        contagem_novos += 1
                                    else:
                                        erros += 1
                            except Exception as e:
                                erros += 1
                                continue
                        
                        st.success(f"✅ **Importação concluída!**")
                        st.info(f"🆕 **Novos alunos:** {contagem_novos}")
                        st.info(f"🔄 **Atualizados:** {contagem_atualizados}")
                        if erros > 0:
                            st.warning(f"⚠️ **Erros:** {erros}")
                        
                        carregar_alunos.clear()
                        st.rerun()
                        
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo: {str(e)}")
            st.info("💡 Tente salvar o CSV com encoding UTF-8 e separador ponto e vírgula (;)")
    
    else:
        st.info("📁 Selecione um arquivo CSV para importar.")


# ============================================================================
# PÁGINA: GERENCIAR TURMAS
# ============================================================================

elif menu == "📋 Gerenciar Turmas":
    st.title("📋 Gerenciar Turmas Importadas")
    
    df_alunos = carregar_alunos()
    
    if not df_alunos.empty:
        st.subheader("📊 Resumo das Turmas")
        
        turmas_info = df_alunos.groupby('turma').agg({
            'ra': 'count',
            'nome': 'first'
        }).reset_index()
        turmas_info.columns = ['turma', 'total_alunos', 'exemplo_nome']
        
        for idx, row in turmas_info.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                
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
                        st.session_state.turma_editar = row['turma']
                
                with col4:
                    if st.button("🗑️ Excluir", key=f"del_{row['turma']}", type="secondary"):
                        st.session_state.turma_para_deletar = row['turma']
                
                st.markdown("---")
        
        if 'turma_para_deletar' in st.session_state:
            st.warning(f"⚠️ Tem certeza que deseja deletar a turma **{st.session_state.turma_para_deletar}?**")
            st.info("Isso removerá TODOS os alunos desta turma!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão", type="primary"):
                    sucesso, msg = excluir_alunos_por_turma(st.session_state.turma_para_deletar)
                    if sucesso:
                        st.success(f"✅ {msg}")
                        del st.session_state.turma_para_deletar
                        carregar_alunos.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            with col2:
                if st.button("❌ Cancelar"):
                    del st.session_state.turma_para_deletar
                    st.rerun()
        
        if 'turma_editar' in st.session_state:
            st.info(f"✏️ Editando turma: **{st.session_state.turma_editar}**")
            
            novo_nome = st.text_input(
                "Novo nome da turma",
                value=st.session_state.turma_editar,
                key="novo_nome_turma"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar Alteração", type="primary"):
                    df_alunos_turma = df_alunos[df_alunos['turma'] == st.session_state.turma_editar]
                    contagem = 0
                    for idx, aluno in df_alunos_turma.iterrows():
                        aluno_dict = {
                            'ra': aluno['ra'],
                            'nome': aluno['nome'],
                            'data_nascimento': aluno.get('data_nascimento', ''),
                            'situacao': aluno.get('situacao', ''),
                            'turma': novo_nome
                        }
                        if atualizar_aluno(aluno['ra'], aluno_dict):
                            contagem += 1
                    
                    st.success(f"✅ {contagem} aluno(s) atualizados para a turma {novo_nome}")
                    del st.session_state.turma_editar
                    carregar_alunos.clear()
                    st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    del st.session_state.turma_editar
                    st.rerun()
        
        if 'turma_selecionada' in st.session_state:
            st.markdown("---")
            st.subheader(f"👥 Alunos da Turma: {st.session_state.turma_selecionada}")
            
            alunos_turma = df_alunos[df_alunos['turma'] == st.session_state.turma_selecionada]
            st.dataframe(alunos_turma[['ra', 'nome', 'situacao']], use_container_width=True)
            
            if st.button("❌ Fechar Visualização"):
                del st.session_state.turma_selecionada
                st.rerun()
        
        st.markdown("---")
        st.info(f"💡 **Total de turmas:** {len(turmas_info)} | **Total de alunos:** {len(df_alunos)}")
    
    else:
        st.info("📭 Nenhuma turma cadastrada. Use a opção 'Importar Alunos (Turmas)'.")


# ============================================================================
# PÁGINA: REGISTRAR OCORRÊNCIA (✅ PROTOCOLO 179 COMPLETO)
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
                
                # ✅ CLASSIFICAÇÃO DA OCORRÊNCIA COM GRAVIDADE AUTOMÁTICA
                st.subheader("📋 Classificação da Ocorrência (Protocolo 179)")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    categoria_grupo = st.selectbox(
                        "📁 Grupo da Categoria",
                        list(CATEGORIAS_OCORRENCIAS.keys()),
                        key="cat_grupo_select"
                    )
                    
                    categorias_grupo = list(CATEGORIAS_OCORRENCIAS[categoria_grupo].keys())
                    categoria = st.selectbox(
                        "📋 Tipo de Ocorrência",
                        categorias_grupo,
                        key="cat_tipo_select",
                        on_change=lambda: st.session_state.update({'gravidade_alterada': False})
                    )
                
                with col2:
                    gravidade_protocolo = CATEGORIAS_OCORRENCIAS[categoria_grupo].get(categoria, "Leve")
                    
                    gravidade_select = st.selectbox(
                        "⚡ Gravidade",
                        ["Gravíssima", "Grave", "Média", "Leve"],
                        index=["Gravíssima", "Grave", "Média", "Leve"].index(gravidade_protocolo),
                        key="grav_select"
                    )
                
                # ✅ FLUXO DE AÇÕES - SEMPRE VISÍVEL QUANDO HOUVER INDICAÇÃO
                if categoria in FLUXO_ACOES:
                    st.markdown(f"""
                    <div class="fluxo-alert">
                        <b>📌 Fluxo de Ações - Protocolo 179:</b><br>
                        {FLUXO_ACOES[categoria]}
                    </div>
                    """, unsafe_allow_html=True)
                
                # ✅ ALERTA SE ALTERAR GRAVIDADE DO PROTOCOLO
                if gravidade_select != gravidade_protocolo:
                    if not st.session_state.gravidade_alterada:
                        st.markdown(f"""
                        <div class="gravidade-alert">
                            ⚠️ <b>ATENÇÃO:</b> Você está alterando a gravidade sugerida pelo Protocolo 179!<br>
                            A gravidade oficial para "{categoria}" é <b>{gravidade_protocolo}</b>.<br>
                            Certifique-se de que há justificativa para esta alteração.
                        </div>
                        """, unsafe_allow_html=True)
                        st.session_state.gravidade_alterada = True
                else:
                    st.session_state.gravidade_alterada = False
                
                relato = st.text_area("📝 Relato da Ocorrência", height=200, key="relato_input")
                
                st.subheader("🔄 Encaminhamentos Sugeridos (Protocolo 179)")
                encaminhamentos_disponiveis = ENCAMINHAMENTOS_POR_GRAVIDADE.get(gravidade_select, [])
                
                col1, col2 = st.columns(2)
                metade = len(encaminhamentos_disponiveis) // 2
                
                with col1:
                    st.markdown("**Coluna 1:**")
                    for i, enc in enumerate(encaminhamentos_disponiveis[:metade]):
                        st.checkbox(enc, value=True, key=f"enc_{i}")
                
                with col2:
                    st.markdown("**Coluna 2:**")
                    for i, enc in enumerate(encaminhamentos_disponiveis[metade:], start=metade):
                        st.checkbox(enc, value=True, key=f"enc_{i}")
                
                encaminhamentos_selecionados = [
                    enc for enc in encaminhamentos_disponiveis 
                    if st.session_state.get(f"enc_{encaminhamentos_disponiveis.index(enc)}", True)
                ]
                
                encaminhamento_str = '| '.join(encaminhamentos_selecionados) if encaminhamentos_selecionados else ''
                
                df_professores = carregar_professores()
                if not df_professores.empty:
                    prof = st.selectbox(
                        "👨‍🏫 Professor Responsável",
                        ["Selecione..."] + df_professores['nome'].tolist(),
                        key="prof_select"
                    )
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
                                    ocorrencia_dict = {
                                        'data': data_str,
                                        'aluno': nome_aluno,
                                        'ra': ra_aluno,
                                        'turma': turma_aluno,
                                        'categoria': categoria_str,
                                        'gravidade': gravidade_select,
                                        'relato': relato,
                                        'professor': prof,
                                        'encaminhamento': encaminhamento_str
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
# PÁGINA: LISTA DE OCORRÊNCIAS (COM EDITAR E EXCLUIR)
# ============================================================================

elif menu == "📊 Lista de Ocorrências":
    st.title("📊 Lista de Ocorrências")
    
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    
    if st.session_state.get('ocorrencia_excluida_sucesso', False):
        st.markdown('<div class="success-box">✅ OCORRÊNCIA EXCLUÍDA COM SUCESSO!</div>', unsafe_allow_html=True)
        st.session_state.ocorrencia_excluida_sucesso = False
    
    if st.session_state.get('ocorrencia_editada_sucesso', False):
        st.markdown('<div class="success-box">✅ OCORRÊNCIA EDITADA COM SUCESSO!</div>', unsafe_allow_html=True)
        st.session_state.ocorrencia_editada_sucesso = False
    
    if not df_ocorrencias.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_gravidade = st.multiselect("Gravidade", ["Gravíssima", "Grave", "Média", "Leve"])
        
        with col2:
            filtro_categoria = st.multiselect("Categoria", df_ocorrencias['categoria'].unique())
        
        with col3:
            filtro_turma = st.multiselect("Turma", df_alunos['turma'].unique().tolist() if not df_alunos.empty else [])
        
        df_filtrado = df_ocorrencias.copy()
        
        if filtro_gravidade:
            df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(filtro_gravidade)]
        
        if filtro_categoria:
            df_filtrado = df_filtrado[df_filtrado['categoria'].isin(filtro_categoria)]
        
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        
        st.markdown(f"**Total:** {len(df_filtrado)} ocorrência(s)")
        st.dataframe(df_filtrado, use_container_width=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🗑️ Excluir Ocorrência")
            ids_disponiveis = df_filtrado['id'].tolist() if not df_filtrado.empty else []
            
            if ids_disponiveis:
                id_excluir = st.selectbox("Selecione o ID para excluir", ids_disponiveis, key="select_excluir")
                senha = st.text_input("Digite a senha (040600)", type="password", key="senha_excluir")
                
                if st.button("🗑️ Excluir Ocorrência", type="secondary"):
                    if senha == SENHA_EXCLUSAO:
                        sucesso, msg = excluir_ocorrencia(id_excluir)
                        if sucesso:
                            st.session_state.ocorrencia_excluida_sucesso = True
                            carregar_ocorrencias.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                    else:
                        st.error("❌ Senha incorreta!")
            else:
                st.info("📭 Nenhuma ocorrência para excluir")
        
        with col2:
            st.subheader("✏️ Editar Ocorrência")
            
            if ids_disponiveis:
                id_editar = st.selectbox("Selecione o ID para editar", ids_disponiveis, key="select_editar")
                
                if st.button("✏️ Carregar para Edição", type="primary"):
                    ocorrencia_row = df_filtrado[df_filtrado['id'] == id_editar]
                    
                    if not ocorrencia_row.empty:
                        ocorrencia = ocorrencia_row.iloc[0].to_dict()
                        
                        st.session_state.editando_id = id_editar
                        st.session_state.dados_edicao = {
                            'id': ocorrencia.get('id', id_editar),
                            'data': ocorrencia.get('data', ''),
                            'aluno': ocorrencia.get('aluno', ''),
                            'ra': ocorrencia.get('ra', ''),
                            'turma': ocorrencia.get('turma', ''),
                            'categoria': ocorrencia.get('categoria', ''),
                            'gravidade': ocorrencia.get('gravidade', ''),
                            'relato': ocorrencia.get('relato', ''),
                            'professor': ocorrencia.get('professor', ''),
                            'encaminhamento': ocorrencia.get('encaminhamento', '')
                        }
                        
                        st.success(f"✅ Ocorrência {id_editar} carregada para edição!")
                    else:
                        st.error("❌ Ocorrência não encontrada!")
        
        if st.session_state.editando_id is not None and st.session_state.dados_edicao:
            st.markdown("---")
            st.subheader(f"✏️ Editando Ocorrência ID: {st.session_state.editando_id}")
            
            dados = st.session_state.dados_edicao
            
            st.info(f"""
            **Dados Atuais:**
            - Aluno: {dados.get('aluno', 'N/A')}
            - RA: {dados.get('ra', 'N/A')}
            - Turma: {dados.get('turma', 'N/A')}
            - Data: {dados.get('data', 'N/A')}
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                edit_relato = st.text_area(
                    "📝 Relato",
                    value=str(dados.get("relato", "")),
                    height=150,
                    key="edit_relato"
                )
                edit_categoria = st.selectbox(
                    "📋 Categoria",
                    list(CATEGORIAS_OCORRENCIAS.keys()),
                    key="edit_categoria"
                )
            
            with col2:
                edit_encam = st.text_area(
                    "🔀 Encaminhamento",
                    value=str(dados.get("encaminhamento", "")),
                    height=150,
                    key="edit_encam"
                )
                edit_grav = st.selectbox(
                    "⚡ Gravidade",
                    ["Gravíssima", "Grave", "Média", "Leve"],
                    index=["Gravíssima", "Grave", "Média", "Leve"].index(str(dados.get("gravidade", "Leve"))) if str(dados.get("gravidade", "Leve")) in ["Gravíssima", "Grave", "Média", "Leve"] else 3,
                    key="edit_grav"
                )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Salvar Alterações", type="primary", key="btn_salvar_edicao"):
                    dados_atualizados = {
                        'data': dados.get('data', ''),
                        'aluno': dados.get('aluno', ''),
                        'ra': dados.get('ra', ''),
                        'turma': dados.get('turma', ''),
                        'categoria': edit_categoria,
                        'gravidade': edit_grav,
                        'relato': edit_relato,
                        'professor': dados.get('professor', ''),
                        'encaminhamento': edit_encam
                    }
                    
                    sucesso, msg = atualizar_ocorrencia(st.session_state.editando_id, dados_atualizados)
                    
                    if sucesso:
                        st.success(f"✅ {msg}")
                        st.session_state.ocorrencia_editada_sucesso = True
                        st.session_state.editando_id = None
                        st.session_state.dados_edicao = None
                        carregar_ocorrencias.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            
            with col2:
                if st.button("❌ Cancelar Edição", key="btn_cancelar_edicao"):
                    st.session_state.editando_id = None
                    st.session_state.dados_edicao = None
                    st.rerun()
        
        st.markdown("---")
        
        st.subheader("📄 Gerar Documentos")
        col1, col2 = st.columns(2)
        
        with col1:
            id_selecionado = st.number_input("ID da Ocorrência", min_value=1, step=1, key="id_pdf")
            
            if st.button("📄 Gerar PDF"):
                ocorrencia_row = df_filtrado[df_filtrado['id'] == id_selecionado]
                if not ocorrencia_row.empty:
                    ocorrencia = ocorrencia_row.iloc[0].to_dict()
                    pdf_buffer = gerar_pdf_ocorrencia(ocorrencia)
                    st.download_button(
                        label="📥 Baixar PDF",
                        data=pdf_buffer,
                        file_name=f"ocorrencia_{id_selecionado}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("❌ Ocorrência não encontrada")
        
        with col2:
            if st.button("📬 Gerar Comunicado"):
                ocorrencia_row = df_filtrado[df_filtrado['id'] == id_selecionado]
                if not ocorrencia_row.empty:
                    ocorrencia = ocorrencia_row.iloc[0].to_dict()
                    pdf_buffer = gerar_pdf_comunicado(ocorrencia)
                    st.download_button(
                        label="📥 Baixar Comunicado",
                        data=pdf_buffer,
                        file_name=f"comunicado_{id_selecionado}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("❌ Ocorrência não encontrada")
    
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
        st.metric("Versão", "10.2 FINAL")
    
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
            'versao_sistema': '10.2 FINAL'
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
    <p>Versão 10.2 FINAL | Desenvolvido com Streamlit + Supabase (Requests)</p>
</div>
""", unsafe_allow_html=True)