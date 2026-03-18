# ============================================================================
# SISTEMA CONVIVA 179 - GESTÃO DE OCORRÊNCIAS ESCOLARES
# Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI
# Versão: 12.0 FINAL - GRÁFICOS AVANÇADOS + TOP 10 ALUNOS + EDIÇÃO COMPLETA
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
import os
import re
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import plotly.express as px
import plotly.graph_objects as go

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
# DADOS DA ESCOLA
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
# PROTOCOLO 179 - CATEGORIAS COMPLETAS
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
        "Uso Inadequado de Dispositivos Eletrônicos": "Leve"
    },
    "📋 Indisciplina e Descumprimento de Normas": {
        "Indisciplina": "Leve",
        "Descumprimento de Normas Escolares": "Leve",
        "Comportamento Inadequado em Sala": "Leve",
        "Desrespeito a Funcionário": "Grave",
        "Desrespeito a Colega": "Média",
        "Recusa em Realizar Atividades": "Leve",
        "Uso Indevido de Material Escolar": "Leve",
        "Danos ao Patrimônio": "Grave",
        "Saída não Autorizada da Sala": "Média",
        "Atraso Frequente": "Média",
        "Ausência sem Justificativa": "Leve",
        "Uso de Celular em Sala": "Leve",
        "Alimentação em Sala de Aula": "Leve",
        "Perturbação do Ambiente Escolar": "Média",
        "Outros": "Leve"
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

CORES_CATEGORIAS = {
    "🔴 Violência Física": "#D32F2F",
    "🟠 Violência Verbal/Psicológica": "#F57C00",
    "🟡 Violência Sexual": "#C2185B",
    "🟢 Armas e Segurança": "#388E3C",
    "💊 Drogas e Substâncias": "#7B1FA2",
    "📚 Infrequência e Evasão": "#FFA726",
    "💔 Saúde Mental": "#5C6BC0",
    "🌐 Crimes Cibernéticos": "#00BCD4",
    "📋 Indisciplina e Descumprimento de Normas": "#9E9E9E",
    "📋 Infrações Administrativas e Disciplinares": "#757575",
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
    "Indisciplina": "📋 Registro em ata. Orientação ao estudante. Comunicação aos pais.",
    "Desrespeito a Funcionário": "⚠️ Registro em ata. Comunicação URGENTE aos pais. Encaminhamento à Coordenação.",
    "Danos ao Patrimônio": "⚠️ Registro em ata. Comunicação aos pais. Reparação do dano.",
    "Uso de Celular em Sala": "📋 Registro em ata. Retirada do aparelho. Devolução aos pais."
}

ENCAMINHAMENTOS_POR_GRAVIDADE = {
    "Leve": ["Orientação ao Estudante", "Comunicação aos Pais/Responsáveis", "Registro em Ata de Ocorrência"],
    "Média": ["Orientação ao Estudante", "Comunicação aos Pais/Responsáveis", "Registro em Ata de Ocorrência", "Encaminhamento à Coordenação"],
    "Grave": ["Orientação ao Estudante", "Comunicação aos Pais/Responsáveis", "Registro em Ata de Ocorrência", "Encaminhamento à Coordenação", "Encaminhamento à Direção", "Acompanhamento Pedagógico"],
    "Gravíssima": ["Orientação ao Estudante", "Comunicação aos Pais/Responsáveis", "Registro em Ata de Ocorrência", "Encaminhamento à Coordenação", "Encaminhamento à Direção", "Acompanhamento Pedagógico", "Acompanhamento Psicopedagógico", "Registro de B.O.", "Acionamento Conselho Tutelar"]
}

# ============================================================================
# SESSION STATE
# ============================================================================
if 'editando_id' not in st.session_state:
    st.session_state.editando_id = None
if 'dados_edicao' not in st.session_state:
    st.session_state.dados_edicao = None
if 'editando_prof' not in st.session_state:
    st.session_state.editando_prof = None
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
if 'turma_editar' not in st.session_state:
    st.session_state.turma_editar = None
if 'validar_nome_data' not in st.session_state:
    st.session_state.validar_nome_data = True

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
.school-name { font-size: 2rem; font-weight: bold; margin-bottom: 0.5rem; }
.school-subtitle { font-size: 1.2rem; font-style: italic; opacity: 0.9; }
.school-address { font-size: 0.9rem; margin-top: 1rem; opacity: 0.8; }
.school-contact { font-size: 0.85rem; margin-top: 0.5rem; opacity: 0.9; }
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 10px;
    color: white;
    text-align: center;
}
.metric-value { font-size: 2.5rem; font-weight: bold; }
.metric-label { font-size: 1rem; opacity: 0.9; }
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
.card-title { font-weight: bold; color: #333; }
.card-value { font-size: 1.5rem; color: #667eea; }
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
.alert-multi-turma {
    background: #cce5ff;
    border: 2px solid #007bff;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    color: #004085;
}
.top-student-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 8px;
    color: white;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNÇÃO: ORDENAR TURMAS (6º AO 3º ANO)
# ============================================================================

def ordenar_turmas(turmas):
    """
    ✅ NOVO: Ordena turmas do 6º ano ao 3º ano do médio
    Fundamental: 6º, 7º, 8º, 9º ano
    Médio: 1º, 2º, 3º ano
    """
    if not turmas:
        return []
    
    def chave_ordenacao(turma):
        turma_str = str(turma).upper().strip()
        
        # Extrair número do ano
        numeros = re.findall(r'\d+', turma_str)
        if not numeros:
            return (99, turma_str)  # Turmas sem número vão para o final
        
        ano = int(numeros[0])
        
        # Identificar se é Fundamental ou Médio
        if '6º' in turma_str or '7º' in turma_str or '8º' in turma_str or '9º' in turma_str or (ano >= 6 and ano <= 9):
            tipo = 0  # Fundamental
            ano_ord = ano
        elif '1º' in turma_str or '2º' in turma_str or '3º' in turma_str or (ano >= 1 and ano <= 3):
            tipo = 1  # Médio
            ano_ord = ano + 10  # Médio vem depois do fundamental
        else:
            tipo = 2  # Outros
            ano_ord = ano
        
        # Extrair letra da turma (A, B, C...)
        letras = re.findall(r'[A-Z]', turma_str)
        letra_ord = ord(letras[0]) if letras else 0
        
        return (tipo, ano_ord, letra_ord, turma_str)
    
    return sorted(turmas, key=chave_ordenacao)

# ============================================================================
# FUNÇÕES DE CARREGAMENTO
# ============================================================================

@st.cache_data(ttl=60)
def carregar_alunos():
    if not SUPABASE_URL:
        return pd.DataFrame(columns=['nome', 'ra', 'turma', 'data_nascimento', 'responsavel', 'telefone', 'foto_url', 'situacao'])
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/alunos?select=*", headers=HEADERS)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            if not df.empty:
                if 'nascimento' in df.columns and 'data_nascimento' not in df.columns:
                    df = df.rename(columns={'nascimento': 'data_nascimento'})
                df = df.sort_values('nome', na_position='last')
            return df
        else:
            return pd.DataFrame(columns=['nome', 'ra', 'turma', 'data_nascimento', 'responsavel', 'telefone', 'foto_url', 'situacao'])
    except Exception as e:
        st.error(f"Erro ao carregar alunos: {str(e)}")
        return pd.DataFrame(columns=['nome', 'ra', 'turma', 'data_nascimento', 'responsavel', 'telefone', 'foto_url', 'situacao'])


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
    df_alunos = carregar_alunos()
    if not df_alunos.empty and 'turma' in df_alunos.columns:
        turmas_info = df_alunos.groupby('turma').size().reset_index(name='total_alunos')
        return turmas_info
    return pd.DataFrame(columns=['turma', 'total_alunos'])


# ============================================================================
# FUNÇÃO: TOP 10 ALUNOS COM MAIS OCORRÊNCIAS
# ============================================================================

def get_top_alunos_ocorrencias(df_ocorrencias, df_alunos, top_n=10):
    """
    ✅ NOVO: Retorna top N alunos com mais ocorrências
    """
    if df_ocorrencias.empty:
        return pd.DataFrame()
    
    # Conta ocorrências por RA
    contagem = df_ocorrencias.groupby(['ra', 'aluno']).size().reset_index(name='total_ocorrencias')
    contagem = contagem.sort_values('total_ocorrencias', ascending=False).head(top_n)
    
    # Junta com dados dos alunos
    if not df_alunos.empty:
        contagem = contagem.merge(df_alunos[['ra', 'turma', 'situacao']].drop_duplicates(), on='ra', how='left')
    
    return contagem


# ============================================================================
# FUNÇÃO: OCORRÊNCIAS POR ALUNO
# ============================================================================

def get_ocorrencias_por_aluno(df_ocorrencias, ra_aluno):
    """
    ✅ NOVO: Retorna todas as ocorrências de um aluno específico
    """
    if df_ocorrencias.empty:
        return pd.DataFrame()
    
    return df_ocorrencias[df_ocorrencias['ra'] == ra_aluno].sort_values('data', ascending=False)


# ============================================================================
# FUNÇÕES DE SALVAMENTO
# ============================================================================

def salvar_ocorrencia(ocorrencia_dict):
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


def excluir_alunos_por_turma(turma):
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
# UPLOAD DE FOTOS
# ============================================================================

def upload_foto_supabase(file, folder, filename):
    if not SUPABASE_URL:
        return None, "Supabase não configurado"
    try:
        file_bytes = file.getvalue()
        storage_url = SUPABASE_URL.replace("/rest/v1", "/storage/v1")
        upload_headers = HEADERS.copy()
        upload_headers["Content-Type"] = file.type
        response = requests.post(f"{storage_url}/object/fotos/{folder}/{filename}", data=file_bytes, headers=upload_headers)
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
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra_aluno}", json={'foto_url': foto_url}, headers=HEADERS)
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
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}", json={'foto_url': foto_url}, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Foto atualizada com sucesso!"
        else:
            return False, f"Erro ao atualizar: {response.text}"
    except Exception as e:
        st.error(f"Erro ao atualizar foto do professor: {str(e)}")
        return False, f"Erro ao atualizar: {str(e)}"


# ============================================================================
# FUNÇÕES AUXILIARES
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
    return str(texto).replace('<br/>', '\n').replace('<br>', '\n').replace('\n', '\n')


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
# GERAR PDF
# ============================================================================

def gerar_pdf_ocorrencia(ocorrencia, responsaveis=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elementos = []
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle('Titulo', parent=estilos['Heading1'], fontSize=14, alignment=TA_CENTER, spaceAfter=0.5*cm, textColor=colors.HexColor('#667eea')))
    estilos.add(ParagraphStyle('Secao', parent=estilos['Normal'], fontSize=10, textColor=colors.HexColor('#667eea'), spaceAfter=0.3*cm))
    estilos.add(ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=9, alignment=TA_JUSTIFY, spaceAfter=0.2*cm))
    estilos.add(ParagraphStyle('Assinatura', parent=estilos['Normal'], fontSize=8, alignment=TA_CENTER, spaceAfter=0.5*cm))
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
    elementos.append(Paragraph(f"<b>Gravidade:</b> <font color='{cor_gravidade}'><b>{gravidade}</b></font>", estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("<b>Relato:</b>", estilos['Secao']))
    elementos.append(Paragraph(formatar_texto(ocorrencia.get('relato', 'N/A') or 'N/A'), estilos['Texto']))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("<b>Encaminhamento:</b>", estilos['Secao']))
    encaminhamento = ocorrencia.get('encaminhamento', '') or ''
    if isinstance(encaminhamento, str) and encaminhamento:
        for enc in encaminhamento.split('|'):
            if enc.strip():
                elementos.append(Paragraph(f"• {enc.strip()}", estilos['Texto']))
    else:
        elementos.append(Paragraph("Nenhum encaminhamento registrado", estilos['Texto']))
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("<b>Professor Responsável:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"{ocorrencia.get('professor', 'N/A') or 'N/A'}", estilos['Texto']))
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
    estilo_rodape = ParagraphStyle('Rodape', parent=estilos['Normal'], fontSize=6, alignment=TA_CENTER, textColor=colors.grey)
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
    doc.build(elementos)
    buffer.seek(0)
    return buffer


def gerar_pdf_comunicado(ocorrencia, responsaveis=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elementos = []
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle('TituloComunicado', parent=estilos['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=1*cm))
    estilos.add(ParagraphStyle('TextoComunicado', parent=estilos['Normal'], fontSize=11, alignment=TA_JUSTIFY, spaceAfter=0.3*cm, leading=14))
    estilos.add(ParagraphStyle('Secao', parent=estilos['Normal'], fontSize=10, textColor=colors.HexColor('#667eea'), spaceAfter=0.3*cm))
    estilos.add(ParagraphStyle('Assinatura', parent=estilos['Normal'], fontSize=8, alignment=TA_CENTER, spaceAfter=0.5*cm))
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
    elementos.append(Paragraph(f"<b>Gravidade:</b> <font color='{cor_gravidade}'><b>{gravidade}</b></font>", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("<b>Relato:</b>", estilos['Secao']))
    elementos.append(Paragraph(formatar_texto(ocorrencia.get('relato', 'N/A') or 'N/A'), estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("<b>Encaminhamento:</b>", estilos['Secao']))
    encaminhamento = ocorrencia.get('encaminhamento', '') or ''
    if isinstance(encaminhamento, str) and encaminhamento:
        for enc in encaminhamento.split('|'):
            if enc.strip():
                elementos.append(Paragraph(f"• {enc.strip()}", estilos['TextoComunicado']))
    else:
        elementos.append(Paragraph("Nenhum encaminhamento registrado", estilos['TextoComunicado']))
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("<b>Professor Responsável:</b>", estilos['Secao']))
    elementos.append(Paragraph(f"{ocorrencia.get('professor', 'N/A') or 'N/A'}", estilos['TextoComunicado']))
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
    estilo_rodape = ParagraphStyle('Rodape', parent=estilos['Normal'], fontSize=6, alignment=TA_CENTER, textColor=colors.grey)
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
    doc.build(elementos)
    buffer.seek(0)
    return buffer


# ============================================================================
# INTERFACE PRINCIPAL - CABEÇALHO E MENU (REORGANIZADO)
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

# ✅ MENU REORGANIZADO - REGISTRAR OCORRÊNCIA EM PRIMEIRO LUGAR
menu = st.sidebar.selectbox(
    "📋 Menu Principal",
    [
        "🏠 Home",
        "📝 Registrar Ocorrência",
        "👥 Alunos",
        "👨‍🏫 Professores",
        "📊 Lista de Ocorrências",
        "📈 Gráficos",
        "🖨️ Relatórios",
        "📋 Gerenciar Turmas",
        "🔍 Alunos em Múltiplas Turmas",
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
            st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, #D32F2F 0%, #B71C1C 100%);"><div class="metric-value">{total_gravissima}</div><div class="metric-label">Gravíssimas</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, #F57C00 0%, #E65100 100%);"><div class="metric-value">{total_grave}</div><div class="metric-label">Graves</div></div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, #FFB300 0%, #FF8F00 100%);"><div class="metric-value">{total_media}</div><div class="metric-label">Médias</div></div>""", unsafe_allow_html=True)
        with col4:
            st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);"><div class="metric-value">{total_leve}</div><div class="metric-label">Leves</div></div>""", unsafe_allow_html=True)
        with col5:
            st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);"><div class="metric-value">{turmas_afetadas}</div><div class="metric-label">Turmas Afetadas</div></div>""", unsafe_allow_html=True)
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Ocorrências por Categoria")
            if 'categoria' in df_ocorrencias.columns:
                cat_counts = df_ocorrencias['categoria'].value_counts().head(10)
                fig = px.bar(x=cat_counts.values, y=cat_counts.index, orientation='h', color=cat_counts.values, color_continuous_scale='Reds', labels={'x': 'Quantidade', 'y': 'Categoria'})
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("📊 Ocorrências por Gravidade")
            if 'gravidade' in df_ocorrencias.columns:
                grav_counts = df_ocorrencias['gravidade'].value_counts()
                fig = px.pie(values=grav_counts.values, names=grav_counts.index, color=grav_counts.index, color_discrete_map=CORES_GRAVIDADE)
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
# PÁGINA: REGISTRAR OCORRÊNCIA
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
        modo_multiplas_turmas = st.checkbox("📚 Registrar para múltiplas turmas", key="chk_multiplas_turmas_reg")
        
        # ✅ TURMAS ORDENADAS (6º AO 3º ANO)
        turmas = ordenar_turmas(df_alunos["turma"].unique().tolist())
        
        if modo_multiplas_turmas:
            turmas_selecionadas = st.multiselect("Selecione as Turmas", turmas, key="multi_turmas_reg")
        else:
            turma_selecionada = st.selectbox("Selecione a Turma", turmas, key="sel_turma_unica_reg")
            turmas_selecionadas = [turma_selecionada] if turma_selecionada else []
        
        if turmas_selecionadas:
            alunos = df_alunos[df_alunos["turma"].isin(turmas_selecionadas)].copy()
            if len(alunos) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 👥 Selecionar Estudante(s)")
                    modo_multiplo = st.checkbox("👥 Múltiplos estudantes", key="chk_multiplas_alunos_reg")
                    if modo_multiplo:
                        alunos_selecionados = st.multiselect("Selecione os Estudantes", alunos["nome"].tolist(), key="multi_alunos_sel_reg")
                    else:
                        lista_alunos = alunos['nome'].tolist()
                        aluno_selecionado = st.selectbox("Selecione o Aluno", lista_alunos, key="sel_aluno_unico_reg")
                        alunos_selecionados = [aluno_selecionado] if aluno_selecionado else []
                with col2:
                    st.markdown("### 📅 Data e Hora")
                    data = st.date_input("Data", value=datetime.now().date(), key="data_input_occ_reg")
                    hora = st.time_input("Hora", value=datetime.now().time(), key="hora_input_occ_reg")
                
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    categoria_grupo = st.selectbox("📁 Grupo da Categoria", list(CATEGORIAS_OCORRENCIAS.keys()), key="sel_grupo_cat_reg")
                    categorias_grupo = list(CATEGORIAS_OCORRENCIAS[categoria_grupo].keys())
                    categoria = st.selectbox("📋 Tipo de Ocorrência", categorias_grupo, key="sel_tipo_ocorr_reg", on_change=lambda: st.session_state.update({'gravidade_alterada': False}))
                with col2:
                    gravidade_protocolo = CATEGORIAS_OCORRENCIAS[categoria_grupo].get(categoria, "Leve")
                    gravidade_select = st.selectbox("⚡ Gravidade", ["Gravíssima", "Grave", "Média", "Leve"], index=["Gravíssima", "Grave", "Média", "Leve"].index(gravidade_protocolo), key="sel_gravidade_reg")
                
                if categoria in FLUXO_ACOES:
                    st.markdown(f"""<div class="fluxo-alert"><b>📌 Fluxo de Ações - Protocolo 179:</b><br>{FLUXO_ACOES[categoria]}</div>""", unsafe_allow_html=True)
                
                if gravidade_select != gravidade_protocolo:
                    if not st.session_state.gravidade_alterada:
                        st.markdown(f"""<div class="gravidade-alert">⚠️ <b>ATENÇÃO:</b> Você está alterando a gravidade sugerida pelo Protocolo 179!<br>A gravidade oficial para "{categoria}" é <b>{gravidade_protocolo}</b>.</div>""", unsafe_allow_html=True)
                        st.session_state.gravidade_alterada = True
                else:
                    st.session_state.gravidade_alterada = False
                
                relato = st.text_area("📝 Relato da Ocorrência", height=200, key="txt_relato_reg")
                st.subheader("🔄 Encaminhamentos Sugeridos (Protocolo 179)")
                encaminhamentos_disponiveis = ENCAMINHAMENTOS_POR_GRAVIDADE.get(gravidade_select, [])
                col1, col2 = st.columns(2)
                metade = len(encaminhamentos_disponiveis) // 2
                with col1:
                    st.markdown("**Coluna 1:**")
                    for i, enc in enumerate(encaminhamentos_disponiveis[:metade]):
                        st.checkbox(enc, value=True, key=f"chk_enc_{i}_reg")
                with col2:
                    st.markdown("**Coluna 2:**")
                    for i, enc in enumerate(encaminhamentos_disponiveis[metade:], start=metade):
                        st.checkbox(enc, value=True, key=f"chk_enc_{i}_reg2")
                
                encaminhamentos_selecionados = [enc for enc in encaminhamentos_disponiveis if st.session_state.get(f"chk_enc_{encaminhamentos_disponiveis.index(enc)}_reg", True) or st.session_state.get(f"chk_enc_{encaminhamentos_disponiveis.index(enc)}_reg2", True)]
                encaminhamento_str = '| '.join(encaminhamentos_selecionados) if encaminhamentos_selecionados else ''
                
                df_professores = carregar_professores()
                if not df_professores.empty:
                    prof = st.selectbox("👨‍🏫 Professor Responsável", ["Selecione..."] + df_professores['nome'].tolist(), key="sel_professor_reg")
                else:
                    prof = st.text_input("👨‍🏫 Professor Responsável", key="txt_professor_reg")
                
                st.markdown("---")
                if st.button("💾 Salvar Ocorrência", type="primary", key="btn_salvar_ocorrencia_reg"):
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
                                    ocorrencia_dict = {'data': data_str, 'aluno': nome_aluno, 'ra': ra_aluno, 'turma': turma_aluno, 'categoria': categoria_str, 'gravidade': gravidade_select, 'relato': relato, 'professor': prof, 'encaminhamento': encaminhamento_str}
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
# PÁGINA: ALUNOS
# ============================================================================

elif menu == "👥 Alunos":
    st.title("👥 Gerenciar Alunos")
    df_alunos = carregar_alunos()
    if not df_alunos.empty:
        col1, col2 = st.columns(2)
        with col1:
            filtro_turma = st.multiselect("Filtrar por Turma", df_alunos['turma'].unique().tolist(), key="multi_filtro_turma_alunos_page")
        with col2:
            busca_nome = st.text_input("🔍 Buscar por Nome", key="txt_busca_nome_aluno_page")
        df_filtrado = df_alunos.copy()
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        if busca_nome:
            df_filtrado = df_filtrado[df_filtrado['nome'].str.contains(busca_nome, case=False, na=False)]
        st.dataframe(df_filtrado, use_container_width=True)
        if st.button("📥 Exportar Lista (CSV)", key="btn_exportar_csv_alunos_page"):
            csv = df_filtrado.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(label="📥 Baixar CSV", data=csv, file_name=f"alunos_lista_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
        st.subheader("🗑️ Excluir Aluno")
        ra_excluir = st.text_input("RA do Aluno para Excluir", key="txt_ra_excluir_page")
        if st.button("🗑️ Excluir Aluno", key="btn_excluir_aluno_page"):
            senha = st.text_input("Digite a senha de exclusão (040600)", type="password", key="txt_senha_excluir_aluno_page")
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
            aluno_foto = st.selectbox("Selecione o Aluno", df_alunos['nome'].tolist(), key="sel_aluno_foto_page")
            ra_aluno = df_alunos[df_alunos['nome'] == aluno_foto]['ra'].values[0]
        with col2:
            foto_file = st.file_uploader("Selecione a foto", type=['jpg', 'jpeg', 'png'], key="file_foto_aluno_page")
            if foto_file and st.button("📷 Enviar Foto", key="btn_enviar_foto_aluno_page"):
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
        nome_prof = st.text_input("Nome Completo *", key="txt_nome_prof_page")
        email_prof = st.text_input("Email", key="txt_email_prof_page")
    with col2:
        cargo_prof = st.text_input("Cargo", key="txt_cargo_prof_page")
        foto_prof = st.file_uploader("Foto (opcional)", type=['jpg', 'jpeg', 'png'], key="file_foto_prof_page")
    
    if st.session_state.get('editando_prof', None) is not None:
        st.info(f"✏️ Editando professor ID: {st.session_state.editando_prof}")
        prof_atual = df_professores[df_professores['id'] == st.session_state.editando_prof].iloc[0]
        if st.button("💾 Atualizar Professor", key="btn_atualizar_prof_page"):
            professor_dict = {'nome': nome_prof.strip(), 'email': email_prof.strip() if email_prof else None, 'cargo': cargo_prof.strip() if cargo_prof else None}
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
        if st.button("❌ Cancelar Edição", key="btn_cancelar_prof_page"):
            st.session_state.editando_prof = None
            st.rerun()
    else:
        if st.button("💾 Salvar Professor", key="btn_salvar_prof_page"):
            if nome_prof:
                nomes_existentes = [n.lower().strip() for n in df_professores['nome'].tolist()]
                if nome_prof.lower().strip() in nomes_existentes:
                    st.error("❌ Já existe um professor com este nome cadastrado!")
                else:
                    professor_dict = {'nome': nome_prof.strip(), 'email': email_prof.strip() if email_prof else None, 'cargo': cargo_prof.strip() if cargo_prof else None, 'foto_url': None}
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
                    if st.button("✏️", key=f"btn_edit_prof_{prof.get('id', idx)}_page"):
                        st.session_state.editando_prof = prof.get('id')
                        st.rerun()
                with col5:
                    if st.button("🗑️", key=f"btn_del_prof_{prof.get('id', idx)}_page"):
                        senha = st.text_input("Senha (040600)", type="password", key=f"txt_senha_prof_{prof.get('id', idx)}_page")
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
# PÁGINA: LISTA DE OCORRÊNCIAS (COM EDITAR/EXCLUIR)
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
            filtro_gravidade = st.multiselect("Gravidade", ["Gravíssima", "Grave", "Média", "Leve"], key="multi_filtro_grav_list")
        with col2:
            filtro_categoria = st.multiselect("Categoria", df_ocorrencias['categoria'].unique(), key="multi_filtro_cat_list")
        with col3:
            filtro_turma = st.multiselect("Turma", df_alunos['turma'].unique().tolist() if not df_alunos.empty else [], key="multi_filtro_turma_list")
        
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
        
        # ✅ EDITAR OCORRÊNCIA
        st.subheader("✏️ Editar Ocorrência")
        ids_disponiveis = df_filtrado['id'].tolist() if not df_filtrado.empty else []
        if ids_disponiveis:
            id_editar = st.selectbox("Selecione o ID para editar", ids_disponiveis, key="sel_id_editar_list")
            if st.button("✏️ Carregar para Edição", type="primary", key="btn_carregar_edicao_list"):
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
            st.info(f"**Protocolo (ID):** {dados.get('id', 'N/A')} (NÃO PODE SER ALTERADO)\n\n**Dados Atuais:**\n- Aluno: {dados.get('aluno', 'N/A')}\n- RA: {dados.get('ra', 'N/A')}\n- Turma: {dados.get('turma', 'N/A')}\n- Data: {dados.get('data', 'N/A')}")
            col1, col2 = st.columns(2)
            with col1:
                edit_relato = st.text_area("📝 Relato", value=str(dados.get("relato", "")), height=150, key="txt_edit_relato_list")
                edit_categoria = st.selectbox("📋 Categoria", list(CATEGORIAS_OCORRENCIAS.keys()), key="sel_edit_categoria_list")
            with col2:
                edit_encam = st.text_area("🔀 Encaminhamento", value=str(dados.get("encaminhamento", "")), height=150, key="txt_edit_encam_list")
                edit_grav = st.selectbox("⚡ Gravidade", ["Gravíssima", "Grave", "Média", "Leve"], index=["Gravíssima", "Grave", "Média", "Leve"].index(str(dados.get("gravidade", "Leve"))) if str(dados.get("gravidade", "Leve")) in ["Gravíssima", "Grave", "Média", "Leve"] else 3, key="sel_edit_grav_list")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Salvar Alterações", type="primary", key="btn_salvar_edicao_list"):
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
                if st.button("❌ Cancelar Edição", key="btn_cancelar_edicao_occ_list"):
                    st.session_state.editando_id = None
                    st.session_state.dados_edicao = None
                    st.rerun()
        
        # ✅ EXCLUIR OCORRÊNCIA
        st.markdown("---")
        st.subheader("🗑️ Excluir Ocorrência")
        if ids_disponiveis:
            id_excluir = st.selectbox("Selecione o ID para excluir", ids_disponiveis, key="sel_id_excluir_list")
            senha = st.text_input("Digite a senha (040600)", type="password", key="txt_senha_excluir_list")
            if st.button("🗑️ Excluir Ocorrência", type="secondary", key="btn_excluir_occ_list"):
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
        
        # ✅ GERAR PDF
        st.markdown("---")
        st.subheader("📄 Gerar Documentos")
        col1, col2 = st.columns(2)
        with col1:
            id_selecionado = st.number_input("ID da Ocorrência", min_value=1, step=1, key="num_id_pdf_list")
            if st.button("📄 Gerar PDF", key="btn_gerar_pdf_list"):
                ocorrencia_row = df_filtrado[df_filtrado['id'] == id_selecionado]
                if not ocorrencia_row.empty:
                    ocorrencia = ocorrencia_row.iloc[0].to_dict()
                    pdf_buffer = gerar_pdf_ocorrencia(ocorrencia)
                    st.download_button(label="📥 Baixar PDF", data=pdf_buffer, file_name=f"ocorrencia_{id_selecionado}.pdf", mime="application/pdf")
                else:
                    st.error("❌ Ocorrência não encontrada")
        with col2:
            if st.button("📬 Gerar Comunicado", key="btn_gerar_comunicado_list"):
                ocorrencia_row = df_filtrado[df_filtrado['id'] == id_selecionado]
                if not ocorrencia_row.empty:
                    ocorrencia = ocorrencia_row.iloc[0].to_dict()
                    pdf_buffer = gerar_pdf_comunicado(ocorrencia)
                    st.download_button(label="📥 Baixar Comunicado", data=pdf_buffer, file_name=f"comunicado_{id_selecionado}.pdf", mime="application/pdf")
                else:
                    st.error("❌ Ocorrência não encontrada")
    else:
        st.info("📭 Nenhuma ocorrência registrada ainda.")


# ============================================================================
# PÁGINA: GRÁFICOS (COM NOVOS GRÁFICOS SOLICITADOS)
# ============================================================================

elif menu == "📈 Gráficos":
    st.title("📈 Gráficos e Estatísticas")
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    
    if not df_ocorrencias.empty:
        st.subheader("🔍 Filtros")
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_turma = st.multiselect("Turma", df_alunos['turma'].unique().tolist(), key="multi_graf_turma_page")
        with col2:
            filtro_gravidade = st.multiselect("Gravidade", ["Gravíssima", "Grave", "Média", "Leve"], key="multi_graf_grav_page")
        with col3:
            filtro_categoria = st.multiselect("Categoria", df_ocorrencias['categoria'].unique(), key="multi_graf_cat_page")
        
        df_filtrado = df_ocorrencias.copy()
        if filtro_turma:
            df_filtrado = df_filtrado[df_filtrado['turma'].isin(filtro_turma)]
        if filtro_gravidade:
            df_filtrado = df_filtrado[df_filtrado['gravidade'].isin(filtro_gravidade)]
        if filtro_categoria:
            df_filtrado = df_filtrado[df_filtrado['categoria'].isin(filtro_categoria)]
        
        st.markdown(f"**Total:** {len(df_filtrado)} ocorrência(s)")
        st.markdown("---")
        
        # ✅ GRÁFICOS TRADICIONAIS
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Ocorrências por Categoria")
            if 'categoria' in df_filtrado.columns and not df_filtrado.empty:
                cat_counts = df_filtrado['categoria'].value_counts().head(10)
                fig = px.bar(x=cat_counts.values, y=cat_counts.index, orientation='h', color=cat_counts.values, color_continuous_scale='Reds')
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("📊 Ocorrências por Gravidade")
            if 'gravidade' in df_filtrado.columns and not df_filtrado.empty:
                grav_counts = df_filtrado['gravidade'].value_counts()
                fig = px.pie(values=grav_counts.values, names=grav_counts.index, color=grav_counts.index, color_discrete_map=CORES_GRAVIDADE)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # ✅ NOVOS GRÁFICOS SOLICITADOS
        st.markdown("---")
        st.subheader("📊 Indicadores Avançados")
        
        col1, col2 = st.columns(2)
        
        # ✅ GRÁFICO 1: ALUNO COM MAIS OCORRÊNCIAS
        with col1:
            st.subheader("👤 Top 10 Alunos com Mais Ocorrências")
            if not df_filtrado.empty:
                top_alunos = df_filtrado.groupby(['ra', 'aluno']).size().reset_index(name='total')
                top_alunos = top_alunos.sort_values('total', ascending=False).head(10)
                fig = px.bar(top_alunos, x='total', y='aluno', orientation='h', color='total', color_continuous_scale='Reds')
                fig.update_layout(height=400, showlegend=False, xaxis_title="Ocorrências", yaxis_title="Aluno")
                st.plotly_chart(fig, use_container_width=True)
        
        # ✅ GRÁFICO 2: PROFESSOR QUE MAIS REGISTRA
        with col2:
            st.subheader("👨‍🏫 Professores que Mais Registram")
            if 'professor' in df_filtrado.columns and not df_filtrado.empty:
                prof_counts = df_filtrado['professor'].value_counts().head(10)
                fig = px.bar(x=prof_counts.values, y=prof_counts.index, orientation='h', color=prof_counts.values, color_continuous_scale='Blues')
                fig.update_layout(height=400, showlegend=False, xaxis_title="Ocorrências", yaxis_title="Professor")
                st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        # ✅ GRÁFICO 3: TURMA COM MAIS OCORRÊNCIAS
        with col1:
            st.subheader("🏫 Turmas com Mais Ocorrências")
            if 'turma' in df_filtrado.columns and not df_filtrado.empty:
                turma_counts = df_filtrado['turma'].value_counts().head(10)
                fig = px.bar(x=turma_counts.index, y=turma_counts.values, color=turma_counts.values, color_continuous_scale='Oranges')
                fig.update_layout(height=400, showlegend=False, xaxis_title="Turma", yaxis_title="Ocorrências")
                st.plotly_chart(fig, use_container_width=True)
        
        # ✅ GRÁFICO 4: OCORRÊNCIA MAIS REGISTRADA
        with col2:
            st.subheader("📋 Ocorrências Mais Registradas")
            if 'categoria' in df_filtrado.columns and not df_filtrado.empty:
                cat_counts = df_filtrado['categoria'].value_counts().head(10)
                fig = px.pie(values=cat_counts.values, names=cat_counts.index, color=cat_counts.values, color_continuous_scale='YlOrRd')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # ✅ ESTATÍSTICAS RESUMIDAS
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
# PÁGINA: RELATÓRIOS (TOP 10 ALUNOS + PESQUISA)
# ============================================================================

elif menu == "🖨️ Relatórios":
    st.title("🖨️ Relatórios e Top 10 Alunos")
    
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    df_responsaveis = carregar_responsaveis()
    
    if not df_ocorrencias.empty:
        # ✅ TOP 10 ALUNOS COM MAIS OCORRÊNCIAS
        st.subheader("🏆 Top 10 Estudantes com Mais Ocorrências")
        top_alunos = get_top_alunos_ocorrencias(df_ocorrencias, df_alunos, top_n=10)
        
        if not top_alunos.empty:
            # Exibir em cards
            for idx, row in top_alunos.iterrows():
                st.markdown(f"""
                <div class="top-student-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 1.5rem; font-weight: bold;">#{idx + 1}</span>
                            <span style="font-size: 1.2rem; margin-left: 1rem;">{row['aluno']}</span>
                        </div>
                        <div style="font-size: 2rem; font-weight: bold;">{row['total_ocorrencias']} 📋</div>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem;">
                        RA: {row['ra']} | Turma: {row.get('turma', 'N/A')} | Situação: {row.get('situacao', 'N/A')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # ✅ PESQUISA POR ALUNO
            st.markdown("---")
            st.subheader("🔍 Pesquisar Ocorrências por Estudante")
            
            busca_aluno = st.text_input("Digite o nome do estudante para localizar suas ocorrências:", key="txt_busca_aluno_rel")
            
            if busca_aluno:
                df_alunos_filtrado = df_alunos[df_alunos['nome'].str.contains(busca_aluno, case=False, na=False)]
                
                if not df_alunos_filtrado.empty:
                    aluno_selecionado = st.selectbox("Selecione o aluno:", df_alunos_filtrado['nome'].tolist(), key="sel_aluno_rel")
                    aluno_info = df_alunos_filtrado[df_alunos_filtrado['nome'] == aluno_selecionado].iloc[0]
                    ra_aluno = aluno_info['ra']
                    
                    # ✅ OCORRÊNCIAS DO ALUNO
                    ocorrencias_aluno = get_ocorrencias_por_aluno(df_ocorrencias, ra_aluno)
                    
                    if not ocorrencias_aluno.empty:
                        st.info(f"**Total de Ocorrências:** {len(ocorrencias_aluno)}")
                        st.dataframe(ocorrencias_aluno[['id', 'data', 'categoria', 'gravidade', 'professor', 'turma']], use_container_width=True)
                        
                        # ✅ AÇÕES (EDITAR/EXCLUIR)
                        st.subheader("🛠️ Ações")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            id_editar = st.selectbox("ID para Editar", ocorrencias_aluno['id'].tolist(), key="sel_id_editar_rel")
                            if st.button("✏️ Editar", key="btn_editar_rel"):
                                ocorrencia = ocorrencias_aluno[ocorrencias_aluno['id'] == id_editar].iloc[0].to_dict()
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
                                st.success(f"✅ Ocorrência {id_editar} carregada para edição! Vá em 'Lista de Ocorrências' para editar.")
                        
                        with col2:
                            id_excluir = st.selectbox("ID para Excluir", ocorrencias_aluno['id'].tolist(), key="sel_id_excluir_rel")
                            senha = st.text_input("Senha (040600)", type="password", key="txt_senha_excluir_rel")
                            if st.button("🗑️ Excluir", key="btn_excluir_rel"):
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
                        st.info("📭 Nenhuma ocorrência registrada para este aluno.")
                else:
                    st.info("📭 Nenhum aluno encontrado com este nome.")
        else:
            st.info("📭 Nenhuma ocorrência registrada.")
        
        # ✅ GERAR PDF
        st.markdown("---")
        st.subheader("📄 Gerar PDF de Ocorrência")
        col1, col2 = st.columns(2)
        with col1:
            id_selecionado = st.number_input("ID da Ocorrência", min_value=1, step=1, key="num_id_pdf_rel")
        with col2:
            tipo_documento = st.selectbox("Tipo de Documento", ["Ocorrência", "Comunicado aos Pais"], key="sel_tipo_doc_rel")
        
        if st.button("🖨️ Gerar PDF", type="primary", key="btn_gerar_pdf_rel"):
            ocorrencia_row = df_ocorrencias[df_ocorrencias['id'] == id_selecionado]
            if not ocorrencia_row.empty:
                ocorrencia = ocorrencia_row.iloc[0].to_dict()
                if tipo_documento == "Ocorrência":
                    pdf_buffer = gerar_pdf_ocorrencia(ocorrencia, df_responsaveis)
                    nome_arquivo = f"ocorrencia_{id_selecionado}_{ocorrencia.get('aluno', 'aluno')}.pdf"
                else:
                    pdf_buffer = gerar_pdf_comunicado(ocorrencia, df_responsaveis)
                    nome_arquivo = f"comunicado_{id_selecionado}_{ocorrencia.get('aluno', 'aluno')}.pdf"
                st.download_button(label="📥 Baixar PDF", data=pdf_buffer, file_name=nome_arquivo, mime="application/pdf")
                st.success("✅ PDF gerado com sucesso!")
            else:
                st.error("❌ Ocorrência não encontrada.")
    else:
        st.info("📭 Nenhuma ocorrência registrada para imprimir.")


# ============================================================================
# PÁGINA: GERENCIAR TURMAS
# ============================================================================

elif menu == "📋 Gerenciar Turmas":
    st.title("📋 Gerenciar Turmas Importadas")
    df_alunos = carregar_alunos()
    
    if not df_alunos.empty:
        st.subheader("📊 Resumo das Turmas")
        turmas_info = df_alunos.groupby('turma').agg({'ra': 'count', 'nome': 'first'}).reset_index()
        turmas_info.columns = ['turma', 'total_alunos', 'exemplo_nome']
        
        for idx, row in turmas_info.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                with col1:
                    st.markdown(f"""<div class="card"><div class="card-title">🏫 {row['turma']}</div><div class="card-value">{row['total_alunos']} alunos</div></div>""", unsafe_allow_html=True)
                with col2:
                    if st.button("👁️ Ver", key=f"btn_ver_turma_{idx}"):
                        st.session_state.turma_selecionada = row['turma']
                with col3:
                    if st.button("✏️ Editar", key=f"btn_edit_turma_{idx}"):
                        st.session_state.turma_editar = row['turma']
                with col4:
                    if st.button("🗑️ Excluir", key=f"btn_del_turma_{idx}", type="secondary"):
                        st.session_state.turma_para_deletar = row['turma']
                st.markdown("---")
        
        if st.session_state.turma_para_deletar:
            st.warning(f"⚠️ Tem certeza que deseja deletar a turma **{st.session_state.turma_para_deletar}?**")
            st.info("Isso removerá TODOS os alunos desta turma!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão", type="primary", key="btn_confirma_exclui_turma"):
                    sucesso, msg = excluir_alunos_por_turma(st.session_state.turma_para_deletar)
                    if sucesso:
                        st.success(f"✅ {msg}")
                        st.session_state.turma_para_deletar = None
                        carregar_alunos.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            with col2:
                if st.button("❌ Cancelar", key="btn_cancela_exclui_turma"):
                    st.session_state.turma_para_deletar = None
                    st.rerun()
        
        if st.session_state.turma_editar:
            st.info(f"✏️ Editando turma: **{st.session_state.turma_editar}**")
            novo_nome = st.text_input("Novo nome da turma", value=st.session_state.turma_editar, key="input_novo_nome_turma")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar Alteração", type="primary", key="btn_salva_edit_turma"):
                    df_alunos_turma = df_alunos[df_alunos['turma'] == st.session_state.turma_editar]
                    contagem = 0
                    for idx, aluno in df_alunos_turma.iterrows():
                        aluno_dict = {'ra': aluno['ra'], 'nome': aluno['nome'], 'data_nascimento': aluno.get('data_nascimento', ''), 'situacao': aluno.get('situacao', ''), 'turma': novo_nome}
                        if atualizar_aluno(aluno['ra'], aluno_dict):
                            contagem += 1
                    st.success(f"✅ {contagem} aluno(s) atualizados para a turma {novo_nome}")
                    st.session_state.turma_editar = None
                    carregar_alunos.clear()
                    st.rerun()
            with col2:
                if st.button("❌ Cancelar", key="btn_cancela_edit_turma"):
                    st.session_state.turma_editar = None
                    st.rerun()
        
        if st.session_state.turma_selecionada:
            st.markdown("---")
            st.subheader(f"👥 Alunos da Turma: {st.session_state.turma_selecionada}")
            alunos_turma = df_alunos[df_alunos['turma'] == st.session_state.turma_selecionada]
            st.dataframe(alunos_turma[['ra', 'nome', 'situacao']], use_container_width=True)
            if st.button("❌ Fechar Visualização", key="btn_fecha_view_turma"):
                st.session_state.turma_selecionada = None
                st.rerun()
        
        st.markdown("---")
        st.info(f"💡 **Total de turmas:** {len(turmas_info)} | **Total de alunos:** {len(df_alunos)}")
    else:
        st.info("📭 Nenhuma turma cadastrada. Use a opção 'Importar Alunos (Turmas)'.")


# ============================================================================
# PÁGINA: ALUNOS EM MÚLTIPLAS TURMAS
# ============================================================================

elif menu == "🔍 Alunos em Múltiplas Turmas":
    st.title("🔍 Alunos com Status Ativo em Múltiplas Turmas")
    st.info("💡 Este relatório mostra alunos com status 'Ativo' cadastrados em mais de uma turma.")
    
    df_alunos = carregar_alunos()
    
    if not df_alunos.empty:
        status_filtro = st.selectbox("Filtrar por Status", ["Ativo", "Transferido", "Desligado", "Todos"], index=0)
        
        if st.button("🔍 Verificar Alunos", type="primary", key="btn_verificar_multi"):
            if status_filtro == "Todos":
                df_multi = verificar_alunos_multi_turmas(df_alunos, status_filtro=None)
            else:
                df_multi = verificar_alunos_multi_turmas(df_alunos, status_filtro)
            
            if not df_multi.empty:
                st.success(f"✅ Encontrados **{len(df_multi['ra'].unique())} aluno(s)** em múltiplas turmas!")
                st.markdown("### 📋 Lista de Alunos:")
                st.dataframe(df_multi[['ra', 'nome', 'turma', 'situacao', 'total_turmas']], use_container_width=True)
                
                st.markdown("### 📊 Resumo:")
                resumo = df_multi.groupby('ra').agg({
                    'nome': 'first',
                    'turma': lambda x: ', '.join(sorted(x.unique())),
                    'total_turmas': 'first',
                    'situacao': 'first'
                }).reset_index()
                st.dataframe(resumo, use_container_width=True)
            else:
                st.info("📭 Nenhum aluno encontrado em múltiplas turmas com o status selecionado.")
    else:
        st.info("📭 Nenhum aluno cadastrado no sistema.")


# ============================================================================
# PÁGINA: IMPORTAR ALUNOS (TURMAS)
# ============================================================================

elif menu == "📥 Importar Alunos":
    st.title("📥 Importar Alunos por Turma")
    st.info("""
    💡 **Como importar:**
    1. Digite o nome da turma (Ex: 1º A, 6º Ano A, 7º Ano B)
    2. Selecione o arquivo **CSV da SEDUC** (separador `;`, UTF-8)
    3. Mapeie as colunas
    4. Clique em "🚀 Importar Alunos"
    """)

    turma_alunos = st.text_input("🏫 Qual a TURMA destes alunos?", placeholder="Ex: 1º A, 6º Ano A, 7º Ano B, 8º Ano C", key="turma_import_input")
    arquivo_upload = st.file_uploader("Selecione o arquivo CSV da SEDUC", type=["csv"], key="arquivo_csv_upload")

    if arquivo_upload is not None:
        try:
            df_import = pd.read_csv(arquivo_upload, sep=';', encoding='utf-8-sig')
            st.success(f"✅ Arquivo lido com sucesso! {len(df_import)} alunos encontrados.")
            st.write("### 👁️ Pré-visualização do CSV (5 linhas)")
            st.dataframe(df_import.head())
            colunas_csv = df_import.columns.tolist()
            st.write("### Colunas encontradas:")
            st.info(f"`{colunas_csv}`")

            col_ra = None
            col_nome = None
            col_nascimento = None
            col_situacao = None

            for col in colunas_csv:
                col_lower = col.lower().strip()
                if 'ra' in col_lower and 'dig' not in col_lower and 'uf' not in col_lower:
                    col_ra = col
                if 'nome' in col_lower and 'aluno' in col_lower:
                    col_nome = col
                if 'data' in col_lower and 'nascimento' in col_lower:
                    col_nascimento = col
                if 'situa' in col_lower:
                    col_situacao = col

            st.write("### Mapeamento encontrado:")
            st.write(f"- **RA:** {col_ra}")
            st.write(f"- **Nome:** {col_nome}")
            st.write(f"- **Nascimento:** {col_nascimento}")
            st.write(f"- **Situação:** {col_situacao}")

            if col_ra and col_nome and col_nascimento and col_situacao:
                st.success("✅ Todas as colunas foram encontradas automaticamente!")
                st.write("### 📋 Prévia dos dados (3 primeiros alunos):")
                preview_df = df_import[[col_ra, col_nome, col_nascimento, col_situacao]].head(3)
                st.dataframe(preview_df)

                if st.button("🚀 Importar Alunos", type="primary", key="btn_importar_alunos"):
                    if not turma_alunos:
                        st.error("❌ Preencha o nome da turma!")
                    else:
                        contagem_novos = 0
                        contagem_atualizados = 0
                        erros = 0
                        df_existentes = carregar_alunos()

                        for idx, row in df_import.iterrows():
                            try:
                                ra_str = str(row[col_ra]).strip()
                                if not ra_str or ra_str.lower() == 'nan':
                                    erros += 1
                                    continue
                                nome_val = str(row[col_nome]).strip()
                                nasc_val = str(row[col_nascimento]).strip()
                                sit_val = str(row[col_situacao]).strip()
                                aluno = {'ra': ra_str, 'nome': nome_val, 'data_nascimento': nasc_val, 'situacao': sit_val, 'turma': turma_alunos}
                                if not df_existentes.empty:
                                    aluno_existente = df_existentes[df_existentes['ra'] == ra_str]
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
                                else:
                                    if salvar_aluno(aluno):
                                        contagem_novos += 1
                                    else:
                                        erros += 1
                            except Exception as e:
                                erros += 1
                                st.error(f"Erro na linha {idx + 1}: {str(e)}")

                        st.success("✅ **Importação concluída!**")
                        st.info(f"🆕 **Novos alunos:** {contagem_novos}")
                        st.info(f"🔄 **Atualizados:** {contagem_atualizados}")
                        if erros > 0:
                            st.warning(f"⚠️ **Erros:** {erros}")
                        carregar_alunos.clear()
                        st.rerun()
            else:
                st.error("❌ Não foi possível encontrar todas as colunas obrigatórias!")
                if not col_ra:
                    st.error("- Falta coluna de **RA**")
                if not col_nome:
                    st.error("- Falta coluna de **Nome do Aluno**")
                if not col_nascimento:
                    st.error("- Falta coluna de **Data de Nascimento**")
                if not col_situacao:
                    st.error("- Falta coluna de **Situação do Aluno**")
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo: {str(e)}")
            st.info("💡 Tente salvar o CSV com encoding UTF-8 e separador ponto e vírgula (;)")
    else:
        st.info("📁 Selecione um arquivo CSV para importar.")


# ============================================================================
# PÁGINA: CONFIGURAÇÕES
# ============================================================================

elif menu == "⚙️ Configurações":
    st.title("⚙️ Configurações do Sistema")
    st.subheader("🏫 Informações da Escola")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Nome:** {ESCOLA_NOME}\n**Endereço:** {ESCOLA_ENDERECO}\n**CEP:** {ESCOLA_CEP}")
    with col2:
        st.info(f"**Telefone:** {ESCOLA_TELEFONE}\n**Email:** {ESCOLA_EMAIL}\n**Logo:** {ESCOLA_LOGO}")
    st.subheader("📋 Protocolo 179")
    col1, col2 = st.columns(2)
    with col1:
        total_categorias = sum(len(v) for v in CATEGORIAS_OCORRENCIAS.values())
        st.metric("Total de Categorias", total_categorias)
    with col2:
        st.metric("Níveis de Gravidade", "4 (Gravíssima, Grave, Média, Leve)")
    st.subheader("🔐 Configurações de Segurança")
    st.warning("**Senha para Exclusão:** 040600\n\nEsta senha é necessária para excluir:\n- Ocorrências\n- Alunos\n- Professores\n- Responsáveis")
    st.subheader("💾 Banco de Dados")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**Tipo:** Supabase (via Requests)\n**Status:** ✅ Conectado")
    with col2:
        st.info("**Storage:** ✅ Habilitado\n**Bucket:** fotos")
    st.subheader("📊 Informações do Sistema")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Versão", "12.0 FINAL")
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
    if st.button("📥 Gerar Backup Completo", key="btn_gerar_backup_page"):
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
            'versao_sistema': '12.0 FINAL'
        }
        json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
        st.download_button(label="📥 Baixar Backup JSON", data=json_str, file_name=f"backup_conviva_{datetime.now().strftime('%Y%m%d_%H%M')}.json", mime="application/json")
        st.success("✅ Backup gerado com sucesso!")
    
    st.markdown("---")
    st.subheader("📤 Importar Backup")
    st.warning("**ATENÇÃO:** Esta ação irá substituir todos os dados atuais!\n\nCertifique-se de ter um backup antes de importar.")
    arquivo_backup = st.file_uploader("Selecione o arquivo de backup", type=['json'], key="file_backup_import_page")
    if arquivo_backup:
        st.info("📄 Arquivo selecionado: " + arquivo_backup.name)
        if st.button("📤 Importar Backup", key="btn_importar_backup_page"):
            senha = st.text_input("Digite a senha de confirmação (040600)", type="password", key="txt_senha_backup_page")
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
                    st.success(f"**Backup importado com sucesso!**\n\n- Alunos: {contagem_alunos}\n- Professores: {contagem_professores}\n- Ocorrências: {contagem_ocorrencias}\n- Responsáveis: {contagem_responsaveis}")
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
    <p>Versão 12.0 FINAL | Desenvolvido com Streamlit + Supabase (Requests)</p>
</div>
""", unsafe_allow_html=True)