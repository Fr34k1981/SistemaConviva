# ============================================================================
# SISTEMA CONVIVA 179 - GESTÃO DE OCORRÊNCIAS ESCOLARES
# Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI
# Versão: 10.5 SUPER COMPLETA - 2500+ LINHAS
# Desenvolvido para SEDUC/SP - Protocolo de Convivência e Proteção Escolar
# ============================================================================

# ============================================================================
# IMPORTAÇÃO DE BIBLIOTECAS - PARTE 1
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
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
DIRETORA = "Coordenadoria Geral de Proteção à Gestão"

# ============================================================================
# ✅ PROTOCOLO 179 COMPLETO - CATEGORIAS REORGANIZADAS
# ============================================================================
CATEGORIAS_OCORRENCIAS = {
    "🔴 Violência Física": {
        "Agressão Física": "Grave",
        "Briga / Discussão": "Média",
        "Ameaça": "Grave",
        "Intimidação": "Grave",
        "Lesão Corporal": "Gravíssima",
        "Socos ou Chutes": "Grave",
        "Puxão de Cabelo": "Média",
        "Empurrão": "Leve"
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
        "Apologia ao Nazismo": "Gravíssima",
        "Insultos": "Média",
        "Assédio Moral": "Grave"
    },
    "🟡 Violência Sexual": {
        "Assédio Sexual": "Gravíssima",
        "Importunação Sexual": "Gravíssima",
        "Estupro": "Gravíssima",
        "Atos Libidinosos": "Gravíssima",
        "Abuso Sexual": "Gravíssima",
        "Exploração Sexual": "Gravíssima",
        "Exposição de Genitais": "Gravíssima",
        "Beijos Forçados": "Grave"
    },
    "🟢 Armas e Segurança": {
        "Posse de Arma de Fogo / Simulacro": "Gravíssima",
        "Posse de Arma Branca": "Gravíssima",
        "Posse de Arma de Brinquedo": "Leve",
        "Ameaça de Ataque Ativo": "Gravíssima",
        "Porte de Objeto Perfurocortante": "Grave",
        "Explosivos": "Gravíssima",
        "Artefato Incendiário": "Gravíssima"
    },
    "💊 Drogas e Substâncias": {
        "Posse de Drogas": "Gravíssima",
        "Tráfico de Drogas": "Gravíssima",
        "Uso de Substâncias": "Grave",
        "Posse de Bebida Alcoólica": "Média",
        "Cigarro / Tabaco": "Leve",
        "Maconha": "Gravíssima",
        "Cocaína / Crack": "Gravíssima"
    },
    "📚 Infrequência e Evasão": {
        "Ausência não justificada / Cabular aula": "Leve",
        "Evasão Escolar / Infrequência": "Média",
        "Saída não autorizada": "Média",
        "Chegar atrasado": "Leve",
        "Aula de Reforço não frequentada": "Leve",
        "Deixar a sala sem permissão": "Leve"
    },
    "💔 Saúde Mental": {
        "Sinais de Automutilação": "Gravíssima",
        "Sinais de Isolamento Social": "Grave",
        "Sinais de Alterações Emocionais": "Grave",
        "Tentativa de Suicídio": "Gravíssima",
        "Suicídio Concretizado": "Gravíssima",
        "Mal Súbito": "Média",
        "Óbito": "Gravíssima",
        "Transtorno de Ansiedade": "Grave",
        "Depressão": "Grave"
    },
    "🌐 Crimes Cibernéticos": {
        "Crimes Cibernéticos": "Grave",
        "Fake News / Disseminação de Informações Falsas": "Grave",
        "Violação de Dados": "Grave",
        "Uso Inadequado de Dispositivos Eletrônicos": "Leve",
        "Compartilhamento de Conteúdo Impróprio": "Média",
        "Acesso a Conteúdo Adulto": "Leve",
        "Phishing / Golpes Online": "Média"
    },
    "📋 Infrações Administrativas e Disciplinares": {
        "Copiar atividades / Colar em avaliações": "Leve",
        "Falsificar assinatura de responsáveis": "Média",
        "Indisciplina": "Leve",
        "Comportamento inadequado para o espaço": "Leve",
        "Dormir em sala de aula": "Leve",
        "Não realizar atividades": "Leve",
        "Outros": "Leve",
        "Desrespeito ao professor": "Média",
        "Bagunça em sala": "Leve",
        "Uso de celular em aula": "Leve"
    },
    "👨‍👩‍👧‍👦 Família e Vulnerabilidade": {
        "Violência Doméstica / Maus Tratos": "Gravíssima",
        "Vulnerabilidade Familiar / Negligência": "Gravíssima",
        "Alerta de Desaparecimento": "Gravíssima",
        "Sequestro": "Gravíssima",
        "Homicídio / Homicídio Tentado": "Gravíssima",
        "Feminicídio": "Gravíssima",
        "Incitamento a Atos Infracionais": "Grave",
        "Abandono": "Gravíssima",
        "Maus Tratos Psicológicos": "Grave"
    }
}

# ============================================================================
# CORES E CONFIGURAÇÕES VISUAIS
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
    "Importunação Sexual": "🚨 CRIME GRAVÍSSIMO. Registrar B.O. imediatamente.",
    "Estupro": "🚨 CRIME GRAVÍSSIMO. Registrar B.O. imediatamente.",
    "Posse de Arma de Fogo / Simulacro": "🚨 EMERGÊNCIA. Acionar PM (190).",
    "Ameaça de Ataque Ativo": "🚨 EMERGÊNCIA. Acionar PM (190) e Direção.",
    "Tentativa de Suicídio": "🚨 SAÚDE. Acionar SAMU (192) e Família.",
    "Sinais de Automutilação": "💚 SAÚDE MENTAL. Acionar Psicólogo e Família.",
    "Posse de Drogas": "⚖️ CRIME. Registrar B.O. e Conselho Tutelar.",
    "Tráfico de Drogas": "⚖️ CRIME. Registrar B.O. e Conselho Tutelar.",
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
        "Encaminhamento à Coordenação",
        "Reunião com Responsáveis",
        "Trabalho Comunitário"
    ],
    "Grave": [
        "Orientação ao Estudante",
        "Comunicação aos Pais/Responsáveis",
        "Registro em Ata de Ocorrência",
        "Encaminhamento à Coordenação",
        "Encaminhamento à Direção",
        "Acompanhamento Pedagógico",
        "Medidas Disciplinares",
        "Suspensão Temporária",
        "Restrição de Atividades"
    ],
    "Gravíssima": [
        "Orientação ao Estudante",
        "Comunicação aos Pais/Responsáveis",
        "Registro em Ata de Ocorrência",
        "Encaminhamento à Coordenação",
        "Encaminhamento à Direção",
        "Acompanhamento Pedagógico",
        "Acompanhamento Psicopedagógico",
        "Acompanhamento Psicológico",
        "Acompanhamento com Assistente Social",
        "Encaminhamento ao Conselho Tutelar",
        "Registro de B.O.",
        "Suspensão de Atividades",
        "Remoção Compulsória",
        "Acompanhamento com Polícia"
    ]
}

# ============================================================================
# INICIALIZAÇÃO DO SESSION STATE - PARTE 2
# ============================================================================
def inicializar_session_state():
    """Inicializa todas as variáveis do session state"""
    vars_iniciais = {
        'editando_id': None,
        'dados_edicao': None,
        'editando_prof': None,
        'editando_resp': None,
        'pagina_atual': "Home",
        'ocorrencia_salva_sucesso': False,
        'turma_para_deletar': None,
        'turma_selecionada': None,
        'turma_editar': None,
        'ocorrencia_excluida_sucesso': False,
        'ocorrencia_editada_sucesso': False,
        'gravidade_alterada': False,
        'professor_adicionado_sucesso': False,
        'responsavel_adicionado_sucesso': False,
        'aluno_adicionado_sucesso': False,
        'filtro_ativo': False,
        'modo_edicao': False,
        'senha_confirmada': False
    }
    
    for key, value in vars_iniciais.items():        
        if key not in st.session_state:
            st.session_state[key] = value

inicializar_session_state()

# ============================================================================
# CSS PERSONALIZADO - PARTE 3
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
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
.error-box {
    background: #f8d7da;
    border: 2px solid #dc3545;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    text-align: center;
    font-weight: bold;
    color: #721c24;
}
.warning-box {
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    color: #856404;
}
.info-box {
    background: #d1ecf1;
    border: 2px solid #17a2b8;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    color: #0c5460;
}
.card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid #667eea;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.card-title {
    font-weight: bold;
    color: #333;
}
.card-value {
    font-size: 1.5rem;
    color: #667eea;
    margin-top: 0.5rem;
}
.fluxo-alert {
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    border-left: 4px solid #ffc107;
}
.gravidade-alert {
    background: #f8d7da;
    border: 2px solid #dc3545;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    color: #721c24;
    border-left: 4px solid #dc3545;
}
.tabs {
    display: flex;
    border-bottom: 2px solid #e0e0e0;
    margin-bottom: 1rem;
}
.tab {
    padding: 0.75rem 1.5rem;
    cursor: pointer;
    border-bottom: 3px solid transparent;
    font-weight: 500;
}
.tab.active {
    border-bottom-color: #667eea;
    color: #667eea;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES DE CARREGAMENTO DE DADOS - PARTE 4
# ============================================================================

@st.cache_data(ttl=60)
def carregar_alunos():
    """Carrega lista de alunos do Supabase"""
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['nome', 'ra', 'turma', 'data_nascimento', 'responsavel', 'telefone', 'foto_url', 'situacao'])
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/alunos?select=*", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            if not df.empty:
                df = df.sort_values('nome')
            return df
        else:
            return pd.DataFrame(columns=['nome', 'ra', 'turma', 'data_nascimento', 'responsavel', 'telefone', 'foto_url', 'situacao'])
    except Exception as e:
        st.error(f"Erro ao carregar alunos: {str(e)}")
        return pd.DataFrame(columns=['nome', 'ra', 'turma', 'data_nascimento', 'responsavel', 'telefone', 'foto_url', 'situacao'])


@st.cache_data(ttl=60)
def carregar_professores():
    """Carrega lista de professores do Supabase"""
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['id', 'nome', 'email', 'cargo', 'foto_url'])
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/professores?select=*", headers=HEADERS, timeout=10)
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
    """Carrega lista de ocorrências do Supabase"""
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamento'])
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/ocorrencias?select=id,data,aluno,ra,turma,categoria,gravidade,relato,professor,encaminhamento&order=id.desc",
            headers=HEADERS,
            timeout=10
        )
        if response.status_code == 200:
            dados = response.json()
            df = pd.DataFrame(dados)
            return df
        else:
            return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamento'])
    except Exception as e:
        st.error(f"Erro ao carregar ocorrências: {str(e)}")
        return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamento'])


@st.cache_data(ttl=60)
def carregar_responsaveis():
    """Carrega lista de responsáveis do Supabase"""
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['id', 'nome', 'cargo'])
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/responsaveis?select=*", headers=HEADERS, timeout=10)
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
    """Carrega lista de turmas únicas"""
    df_alunos = carregar_alunos()
    if not df_alunos.empty and 'turma' in df_alunos.columns:
        turmas_info = df_alunos.groupby('turma').agg({
            'nome': 'count'
        }).reset_index()
        turmas_info.columns = ['turma', 'total_alunos']
        return turmas_info.sort_values('turma')
    return pd.DataFrame(columns=['turma', 'total_alunos'])


# ============================================================================
# FUNÇÕES DE SALVAMENTO - PARTE 5
# ============================================================================

def salvar_ocorrencia(ocorrencia_dict):
    """Salva uma nova ocorrência no Supabase"""
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
        
        response = requests.post(f"{SUPABASE_URL}/rest/v1/ocorrencias", json=ocorrencia_dict_clean, headers=HEADERS, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Ocorrência salva com sucesso!"
        else:
            return False, f"Erro ao salvar: {response.text}"
    except Exception as e:
        return False, f"Erro ao salvar: {str(e)}"


def atualizar_ocorrencia(id_ocorrencia, ocorrencia_dict):
    """Atualiza uma ocorrência existente"""
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
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return True, "Ocorrência atualizada com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        return False, f"Erro ao atualizar: {str(e)}"


def excluir_ocorrencia(id_ocorrencia):
    """Exclui uma ocorrência"""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}", headers=HEADERS, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Ocorrência excluída com sucesso!"
        else:
            return False, f"Erro ao excluir: {response.text}"
    except Exception as e:
        return False, f"Erro ao excluir: {str(e)}"


def salvar_aluno(aluno_dict):
    """Salva um novo aluno"""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/alunos", json=aluno_dict, headers=HEADERS, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Aluno salvo com sucesso!"
        else:
            return False, f"Erro ao salvar: {response.text}"
    except Exception as e:
        return False, f"Erro ao salvar: {str(e)}"


def atualizar_aluno(ra_aluno, aluno_dict):
    """Atualiza dados de um aluno"""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra_aluno}", json=aluno_dict, headers=HEADERS, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Aluno atualizado com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        return False, f"Erro ao atualizar: {str(e)}"


def excluir_aluno(ra_aluno):
    """Exclui um aluno"""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra_aluno}", headers=HEADERS, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Aluno excluído com sucesso!"
        else:
            return False, f"Erro ao excluir: {response.text}"
    except Exception as e:
        return False, f"Erro ao excluir: {str(e)}"


def excluir_alunos_por_turma(turma):
    """Exclui todos os alunos de uma turma"""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/alunos?turma=eq.{turma}", headers=HEADERS, timeout=10)
        if response.status_code in [200, 201]:
            return True, f"Turma {turma} excluída com sucesso!"
        else:
            return False, f"Erro ao excluir turma: {response.text}"
    except Exception as e:
        return False, f"Erro ao excluir: {str(e)}"


def salvar_professor(professor_dict):
    """Salva um novo professor"""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/professores", json=professor_dict, headers=HEADERS, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Professor salvo com sucesso!"
        else:
            return False, f"Erro ao salvar: {response.text}"
    except Exception as e:
        return False, f"Erro ao salvar: {str(e)}"


def atualizar_professor(id_prof, professor_dict):
    """Atualiza dados de um professor"""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}", json=professor_dict, headers=HEADERS, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Professor atualizado com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        return False, f"Erro ao atualizar: {str(e)}"


def excluir_professor(id_prof):
    """Exclui um professor"""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}", headers=HEADERS, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Professor excluído com sucesso!"
        else:
            return False, f"Erro ao excluir: {response.text}"
    except Exception as e:
        return False, f"Erro ao excluir: {str(e)}"


def salvar_responsavel(responsavel_dict):
    """Salva um novo responsável"""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/responsaveis", json=responsavel_dict, headers=HEADERS, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Responsável salvo com sucesso!"
        else:
            return False, f"Erro ao salvar: {response.text}"
    except Exception as e:
        return False, f"Erro ao salvar: {str(e)}"


def atualizar_responsavel(id_resp, responsavel_dict):
    """Atualiza dados de um responsável"""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}", json=responsavel_dict, headers=HEADERS, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Responsável atualizado com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        return False, f"Erro ao atualizar: {str(e)}"


def excluir_responsavel(id_resp):
    """Exclui um responsável"""
    if not SUPABASE_URL:
        return False, "Supabase não configurado"
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}", headers=HEADERS, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Responsável excluído com sucesso!"
        else:
            return False, f"Erro ao excluir: {response.text}"
    except Exception as e:
        return False, f"Erro ao excluir: {str(e)}"


# ============================================================================
# FUNÇÕES AUXILIARES - PARTE 6
# ============================================================================

def verificar_ocorrencia_duplicada(ra_aluno, categoria, data, df_ocorrencias):
    """Verifica se já existe uma ocorrência idêntica"""
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
        return False


def formatar_texto(texto):
    """Formata texto para exibição"""
    if not texto:
        return ""
    return str(texto).replace('<br/>', '\n').replace('<br>', '\n')


def obter_cor_gravidade(gravidade):
    """Retorna a cor baseada na gravidade"""
    return CORES_GRAVIDADE.get(gravidade, '#9E9E9E')


def calcular_idade(data_nascimento_str):
    """Calcula a idade a partir da data de nascimento"""
    try:
        data_nasc = pd.to_datetime(data_nascimento_str)
        hoje = pd.Timestamp.now()
        idade = (hoje - data_nasc).days // 365
        return idade
    except:
        return None


def gerar_relatorio_json(df_ocorrencias):
    """Gera um JSON com o relatório de ocorrências"""
    try:
        relatorio = {
            'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'total_ocorrencias': len(df_ocorrencias),
            'ocorrencias': df_ocorrencias.to_dict('records')
        }
        return json.dumps(relatorio, ensure_ascii=False, indent=2)
    except:
        return None


def exportar_csv(df, nome_arquivo):
    """Exporta um DataFrame para CSV"""
    try:
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        return csv, nome_arquivo
    except:
        return None, None


# ============================================================================
# FUNÇÕES DE GERAÇÃO DE PDF - PARTE 7
# ============================================================================

def gerar_pdf_ocorrencia(ocorrencia, responsaveis=None):
    """Gera PDF da ocorrência"""
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
        spaceAfter=0.3*cm,
        fontName='Helvetica-Bold'
    ))
    
    estilos.add(ParagraphStyle(
        'Texto',
        parent=estilos['Normal'],
        fontSize=9,
        alignment=TA_JUSTIFY,
        spaceAfter=0.2*cm
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
    
    elementos.append(Paragraph(f"<b>Escola:</b> {ESCOLA_NOME}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Endereço:</b> {ESCOLA_ENDERECO}", estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>DADOS DO(A) ESTUDANTE:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"<b>Nome:</b> {ocorrencia.get('aluno', 'N/A') or 'N/A'}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>RA:</b> {ocorrencia.get('ra', 'N/A') or 'N/A'}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Turma:</b> {ocorrencia.get('turma', 'N/A') or 'N/A'}", estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>DADOS DA OCORRÊNCIA:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"<b>Data:</b> {ocorrencia.get('data', 'N/A') or 'N/A'}", estilos['Texto']))
    elementos.append(Paragraph(f"<b>Categoria:</b> {ocorrencia.get('categoria', 'N/A') or 'N/A'}", estilos['Texto']))
    
    gravidade = ocorrencia.get('gravidade', 'N/A') or 'N/A'
    cor_gravidade = obter_cor_gravidade(gravidade)
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
    """Gera PDF do comunicado aos pais"""
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
        spaceAfter=1*cm,
        textColor=colors.HexColor('#667eea')
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
        spaceAfter=0.3*cm,
        fontName='Helvetica-Bold'
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
    cor_gravidade = obter_cor_gravidade(gravidade)
    elementos.append(Paragraph(
        f"<b>Gravidade:</b> <font color='{cor_gravidade}'><b>{gravidade}</b></font>",
        estilos['TextoComunicado']
    ))
    elementos.append(Spacer(1, 0.3*cm))
    
    elementos.append(Paragraph("<b>Relato:</b>", estilos['Secao']))
    relato = ocorrencia.get('relato', 'N/A') ou 'N/A'
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
    
    elementos.append(Paragraph(f"Atenciosamente,<br/><br/>{DIRETORA}<br/>{ESCOLA_NOME}", estilos['TextoComunicado']))
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
# CABEÇALHO E MENU PRINCIPAL - PARTE 8
# ============================================================================

st.markdown(f"""
<div class="main-header">
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
        "📥 Importar Alunos",
        "📋 Gerenciar Turmas",
        "📝 Registrar Ocorrência",
        "📊 Lista de Ocorrências",
        "👥 Alunos",
        "👨‍🏫 Professores",
        "📄 Responsáveis",
        "📈 Gráficos",
        "🖨️ Relatórios",
        "📋 Consultas Avançadas",
        "⚙️ Configurações",
        "💾 Backup"
    ],
    index=0
)

st.session_state.pagina_atual = menu


# ============================================================================
# PÁGINA: HOME - DASHBOARD - PARTE 9
# ============================================================================

if menu == "🏠 Home":
    st.title("🏠 Dashboard - Painel Geral")
    
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    df_professores = carregar_professores()
    df_turmas = carregar_turmas()
    
    # Métricas principais
    if not df_ocorrencias.empty:
        total_ocorrencias = len(df_ocorrencias)
        total_gravissima = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Gravíssima'])
        total_grave = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Grave'])
        total_media = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Média'])
        total_leve = len(df_ocorrencias[df_ocorrencias['gravidade'] == 'Leve'])
        turmas_afetadas = df_ocorrencias['turma'].nunique() if 'turma' in df_ocorrencias.columns else 0
        alunos_envolvidos = df_ocorrencias['ra'].nunique() if 'ra' in df_ocorrencias.columns else 0
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("Total", total_ocorrencias)
        with col2:
            st.metric("Gravíssimas", total_gravissima)
        with col3:
            st.metric("Graves", total_grave)
        with col4:
            st.metric("Médias", total_media)
        with col5:
            st.metric("Leves", total_leve)
        with col6:
            st.metric("Alunos", alunos_envolvidos)
        
        st.markdown("---")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Ocorrências por Categoria")
            if 'categoria' in df_ocorrencias.columns and not df_ocorrencias.empty:
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
            if 'gravidade' in df_ocorrencias.columns and not df_ocorrencias.empty:
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
        st.dataframe(df_ocorrencias.head(10), use_container_width=True, height=400)
    
    else:
        st.info("📭 Nenhuma ocorrência registrada ainda.")
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Turmas", len(df_turmas))
    with col2:
        st.metric("Alunos", len(df_alunos))
    with col3:
        st.metric("Professores", len(df_professores))
    with col4:
        st.metric("Data Atual", datetime.now().strftime("%d/%m/%Y"))


# ============================================================================
# PÁGINA: REGISTRAR OCORRÊNCIA - PARTE 10 - ✅ COM CORREÇÃO
# ============================================================================

elif menu == "📝 Registrar Ocorrência":
    st.title("📝 Registrar Nova Ocorrência")
    
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    
    if st.session_state.get('ocorrencia_salva_sucesso', False):
        st.markdown('<div class="success-box">✅ OCORRÊNCIA(S) REGISTRADA(S) COM SUCESSO!</div>', unsafe_allow_html=True)
        st.session_state.ocorrencia_salva_sucesso = False
        st.rerun()
    
    if df_alunos.empty:
        st.warning("⚠️ Nenhum aluno cadastrado. Importe alunos primeiro.")
    else:
        st.subheader("🏫 Selecionar Turma(s)")
        modo_multiplas_turmas = st.checkbox("📚 Registrar para múltiplas turmas",
