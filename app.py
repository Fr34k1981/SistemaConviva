# ============================================================================
# SISTEMA CONVIVA 179 - GESTÃO DE OCORRÊNCIAS ESCOLARES
# Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI
# Versão: 14.1 FINAL - SUPABASE + ASSINATURAS + SELEÇÃO MÚLTIPLA
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
import pytz
from difflib import SequenceMatcher

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
# CONFIGURAÇÃO DO SUPABASE
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
# PROTOCOLO 179 - CATEGORIAS
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
    "Sinais de Automutilação": "💚 SAÚDE MENTAL. Acionar Psicólogo e Família."
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
# === 🆕 NOVA FUNCIONALIDADE: Session state para edição de responsáveis ===
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
if 'turma_editar' not in st.session_state:
    st.session_state.turma_editar = None
if 'salvando_ocorrencia' not in st.session_state:
    st.session_state.salvando_ocorrencia = False
if 'adicionar_outra_infracao' not in st.session_state:
    st.session_state.adicionar_outra_infracao = False
if 'infracoes_adicionais' not in st.session_state:
    st.session_state.infracoes_adicionais = []
if 'senha_exclusao_validada' not in st.session_state:
    st.session_state.senha_exclusao_validada = False

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
.top-student-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 8px;
    color: white;
    margin: 0.5rem 0;
}
.search-box {
    background: #f0f0f0;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def filtrar_por_periodo(df_ocorrencias, periodo="todos"):
    """Filtra ocorrências por período"""
    if df_ocorrencias.empty:
        return df_ocorrencias
    df_filtrado = df_ocorrencias.copy()
    df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
    hoje = datetime.now()
    if periodo == "ultimo_mes":
        data_limite = hoje - timedelta(days=30)
        df_filtrado = df_filtrado[df_filtrado['data_dt'] >= data_limite]
    elif periodo == "semana_atual":
        data_limite = hoje - timedelta(days=7)
        df_filtrado = df_filtrado[df_filtrado['data_dt'] >= data_limite]
    elif periodo == "semana_passada":
        data_limite_superior = hoje - timedelta(days=7)
        data_limite_inferior = hoje - timedelta(days=14)
        df_filtrado = df_filtrado[
            (df_filtrado['data_dt'] >= data_limite_inferior) & 
            (df_filtrado['data_dt'] < data_limite_superior)
        ]
    if 'data_dt' in df_filtrado.columns:
        df_filtrado = df_filtrado.drop(columns=['data_dt'])
    return df_filtrado

def ordenar_turmas(turmas):
    """Ordena turmas do 6º ano ao 3º ano do médio"""
    if not turmas:
        return []
    def chave_ordenacao(turma):
        turma_str = str(turma).upper().strip()
        numeros = re.findall(r'\d+', turma_str)
        if not numeros:
            return (99, turma_str)
        ano = int(numeros[0])
        if ano >= 6 and ano <= 9:
            tipo = 0
            ano_ord = ano
        elif ano >= 1 and ano <= 3:
            tipo = 1
            ano_ord = ano + 10
        else:
            tipo = 2
            ano_ord = ano
        letras = re.findall(r'[A-Z]', turma_str)
        letra_ord = ord(letras[0]) if letras else 0
        return (tipo, ano_ord, letra_ord, turma_str)
    return sorted(turmas, key=chave_ordenacao)

def get_top_alunos_ocorrencias(df_ocorrencias, df_alunos, top_n=10):
    """Retorna top N alunos com mais ocorrências"""
    if df_ocorrencias.empty:
        return pd.DataFrame()
    contagem = df_ocorrencias.groupby(['ra', 'aluno']).size().reset_index(name='total_ocorrencias')
    contagem = contagem.sort_values('total_ocorrencias', ascending=False).head(top_n)
    if not df_alunos.empty:
        contagem = contagem.merge(df_alunos[['ra', 'turma', 'situacao']].drop_duplicates(), on='ra', how='left')
    return contagem

def get_ocorrencias_por_aluno(df_ocorrencias, ra_aluno):
    """Retorna todas as ocorrências de um aluno específico"""
    if df_ocorrencias.empty:
        return pd.DataFrame()
    return df_ocorrencias[df_ocorrencias['ra'] == ra_aluno].sort_values('data', ascending=False)

def formatar_texto(texto):
    """Formata texto para exibição"""
    if not texto:
        return ""
    return str(texto).replace('<br/>', '\n').replace('<br>', '\n')

def buscar_infracao_fuzzy(busca, protocolo):
    """Busca fuzzy de infrações"""
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

def obter_gravidade_mais_alta(gravidades):
    """Retorna a gravidade mais alta de uma lista"""
    ordem = {"Leve": 1, "Grave": 2, "Gravíssima": 3}
    if not gravidades:
        return "Leve"
    return max(gravidades, key=lambda g: ordem.get(g, 0))

def combinar_encaminhamentos(encaminhamentos_lista):
    """Combina listas de encaminhamentos removendo duplicatas"""
    todos = []
    for encam in encaminhamentos_lista:
        for linha in encam.split('\n'):
            linha = linha.strip()
            if linha and linha not in todos:
                todos.append(linha)
    return '\n'.join(todos)

# ============================================================================
# FUNÇÕES SUPABASE
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
        return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamento', 'envolvidos'])
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/ocorrencias?select=id,data,aluno,ra,turma,categoria,gravidade,relato,professor,encaminhamento,envolvidos&order=id.desc",
            headers=HEADERS
        )
        if response.status_code == 200:
            dados = response.json()
            df = pd.DataFrame(dados)
            if 'envolvidos' not in df.columns:
                df['envolvidos'] = ''
            return df
        else:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/ocorrencias?select=id,data,aluno,ra,turma,categoria,gravidade,relato,professor,encaminhamento&order=id.desc",
                headers=HEADERS
            )
            if response.status_code == 200:
                dados = response.json()
                df = pd.DataFrame(dados)
                df['envolvidos'] = ''
                return df
            else:
                return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamento', 'envolvidos'])
    except Exception as e:
        st.error(f"Erro ao carregar ocorrências: {str(e)}")
        return pd.DataFrame(columns=['id', 'data', 'aluno', 'ra', 'turma', 'categoria', 'gravidade', 'relato', 'professor', 'encaminhamento', 'envolvidos'])

@st.cache_data(ttl=60)
def carregar_responsaveis():
    """Carrega todos os responsáveis do Supabase"""
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
            'encaminhamento': ocorrencia_dict.get('encaminhamento', ''),
            'envolvidos': ocorrencia_dict.get('envolvidos', '')
        }
        if isinstance(ocorrencia_dict_clean['encaminhamento'], list):
            ocorrencia_dict_clean['encaminhamento'] = '| '.join(ocorrencia_dict_clean['encaminhamento'])
        response = requests.post(f"{SUPABASE_URL}/rest/v1/ocorrencias", json=ocorrencia_dict_clean, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Ocorrência salva com sucesso!"
        else:
            if 'envolvidos' in ocorrencia_dict_clean:
                del ocorrencia_dict_clean['envolvidos']
                response = requests.post(f"{SUPABASE_URL}/rest/v1/ocorrencias", json=ocorrencia_dict_clean, headers=HEADERS)
                if response.status_code in [200, 201]:
                    return True, "Ocorrência salva com sucesso!"
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
            'encaminhamento': ocorrencia_dict.get('encaminhamento', ''),
            'envolvidos': ocorrencia_dict.get('envolvidos', '')
        }
        if isinstance(ocorrencia_dict_clean['encaminhamento'], list):
            ocorrencia_dict_clean['encaminhamento'] = '| '.join(ocorrencia_dict_clean['encaminhamento'])
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}", json=ocorrencia_dict_clean, headers=HEADERS)
        if response.status_code in [200, 201]:
            return True, "Ocorrência atualizada com sucesso!"
        else:
            if 'envolvidos' in ocorrencia_dict_clean:
                del ocorrencia_dict_clean['envolvidos']
                response = requests.patch(f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}", json=ocorrencia_dict_clean, headers=HEADERS)
                if response.status_code in [200, 201]:
                    return True, "Ocorrência atualizada com sucesso!"
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

# === 🆕 NOVA FUNCIONALIDADE: Funções CRUD para Responsáveis (Assinaturas) ===
def salvar_responsavel(responsavel_dict):
    """Salva um responsável no Supabase"""
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
    """Atualiza um responsável no Supabase"""
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
    """Exclui um responsável do Supabase"""
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

def verificar_ocorrencia_duplicada(ra, categoria, data_str, df_ocorrencias):
    """Verifica se já existe ocorrência duplicada"""
    if df_ocorrencias.empty:
        return False
    ocorrencias_existentes = df_ocorrencias[
        (df_ocorrencias['ra'] == ra) &
        (df_ocorrencias['categoria'] == categoria) &
        (df_ocorrencias['data'] == data_str)
    ]
    return not ocorrencias_existentes.empty

def verificar_professor_duplicado(nome, df_professores, id_atual=None):
    """Verifica se professor já existe"""
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
# GERAR PDF
# ============================================================================

def gerar_pdf_ocorrencia(ocorrencia, responsaveis=None):
    """Gera PDF de ocorrência"""
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
    envolvidos = ocorrencia.get('envolvidos', '') or ''
    if envolvidos:
        elementos.append(Paragraph(f"<b>Envolvidos/Queixa:</b> {envolvidos}", estilos['Texto']))
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

# ============================================================================
# INTERFACE PRINCIPAL
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

# === ✏️ MODIFICADO: Adicionado novo item "👥 Responsáveis" no menu ===
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
        "👥 Responsáveis",  # === 🆕 NOVO ITEM: Gestão de responsáveis pelas assinaturas ===
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
    
    # FILTRO DE PERÍODO
    st.subheader("🔍 Filtro de Período")
    col1, col2 = st.columns(2)
    with col1:
        periodo_selecionado = st.selectbox(
            "Selecione o período:",
            ["Todos", "Último Mês (30 dias)", "Semana Atual (7 dias)", "Semana Passada"],
            key="sel_periodo_home"
        )
    
    mapa_periodo = {
        "Todos": "todos",
        "Último Mês (30 dias)": "ultimo_mes",
        "Semana Atual (7 dias)": "semana_atual",
        "Semana Passada": "semana_passada"
    }
    
    periodo_filtro = mapa_periodo.get(periodo_selecionado, "todos")
    df_filtrado_periodo = filtrar_por_periodo(df_ocorrencias, periodo_filtro)
    
    if not df_filtrado_periodo.empty:
        total_ocorrencias = len(df_filtrado_periodo)
        total_gravissima = len(df_filtrado_periodo[df_filtrado_periodo['gravidade'] == 'Gravíssima']) if 'gravidade' in df_filtrado_periodo.columns else 0
        total_grave = len(df_filtrado_periodo[df_filtrado_periodo['gravidade'] == 'Grave']) if 'gravidade' in df_filtrado_periodo.columns else 0
        total_media = len(df_filtrado_periodo[df_filtrado_periodo['gravidade'] == 'Média']) if 'gravidade' in df_filtrado_periodo.columns else 0
        total_leve = len(df_filtrado_periodo[df_filtrado_periodo['gravidade'] == 'Leve']) if 'gravidade' in df_filtrado_periodo.columns else 0
        turmas_afetadas = df_filtrado_periodo['turma'].nunique() if 'turma' in df_filtrado_periodo.columns else 0
        
        st.info(f"📅 Período: **{periodo_selecionado}** - Total: **{total_ocorrencias} ocorrências**")
        
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
            if 'categoria' in df_filtrado_periodo.columns:
                cat_counts = df_filtrado_periodo['categoria'].value_counts().head(10)
                fig = px.bar(x=cat_counts.values, y=cat_counts.index, orientation='h', color=cat_counts.values, color_continuous_scale='Reds')
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("📊 Ocorrências por Gravidade")
            if 'gravidade' in df_filtrado_periodo.columns:
                grav_counts = df_filtrado_periodo['gravidade'].value_counts()
                fig = px.pie(values=grav_counts.values, names=grav_counts.index, color=grav_counts.index, color_discrete_map=CORES_GRAVIDADE)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📋 Últimas Ocorrências do Período")
        st.dataframe(df_filtrado_periodo.head(10), use_container_width=True)
    else:
        st.info("📭 Nenhuma ocorrência registrada no período selecionado.")
    
    if not df_turmas.empty:
        st.markdown("---")
        st.subheader("🏫 Resumo Geral da Escola")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Turmas", len(df_turmas))
        with col2:
            st.metric("Total de Alunos", len(df_alunos))
    
    if not df_professores.empty:
        st.subheader("👨‍🏫 Resumo de Professores")
        st.metric("Total de Professores", len(df_professores))

# ============================================================================
# PÁGINA: IMPORTAR ALUNOS
# ============================================================================

elif menu == "📥 Importar Alunos":
    st.title("📥 Importar Alunos por Turma")
    
    st.info("""
    💡 **Como importar:**
    1. Digite o nome da turma (Ex: 6º Ano A, 7º Ano B)
    2. Selecione o arquivo **CSV da SEDUC** (separador `;`, UTF-8)
    3. O sistema mapeia as colunas automaticamente
    4. Clique em "🚀 Importar Alunos"
    """)

    turma_alunos = st.text_input(
        "🏫 Qual a TURMA destes alunos?",
        placeholder="Ex: 6º Ano A, 7º Ano B, 8º Ano C",
        key="turma_import_input"
    )
    
    arquivo_upload = st.file_uploader(
        "Selecione o arquivo CSV da SEDUC",
        type=["csv"],
        key="arquivo_csv_upload"
    )

    if arquivo_upload is not None:
        try:
            df_import = pd.read_csv(arquivo_upload, sep=';', encoding='utf-8-sig')
            st.success(f"✅ Arquivo lido com sucesso! {len(df_import)} linhas encontradas.")
            
            st.write("### 👁️ Pré-visualização do CSV (5 primeiras linhas)")
            st.dataframe(df_import.head())
            
            colunas_csv = df_import.columns.tolist()
            st.write("### 📋 Colunas encontradas:")
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

            st.write("### 🔍 Mapeamento encontrado:")
            st.write(f"- **RA:** `{col_ra}`")
            st.write(f"- **Nome:** `{col_nome}`")
            st.write(f"- **Nascimento:** `{col_nascimento}`")
            st.write(f"- **Situação:** `{col_situacao}`")

            colunas_necessarias = [col_ra, col_nome, col_nascimento, col_situacao]
            faltantes = [c for c in colunas_necessarias if c is None]
            
            if faltantes:
                st.error(f"❌ Colunas não encontradas: {faltantes}")
            else:
                st.success("✅ Todas as colunas foram encontradas!")
                
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
                                
                                aluno = {
                                    'ra': ra_str,
                                    'nome': nome_val,
                                    'data_nascimento': nasc_val,
                                    'situacao': sit_val,
                                    'turma': turma_alunos
                                }
                                
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
        st.info("📭 Nenhuma turma cadastrada. Use a opção 'Importar Alunos'.")

# ============================================================================
# PÁGINA: REGISTRAR OCORRÊNCIA
# === ✏️ MODIFICADO: Adicionada seleção múltipla de turmas, alunos e categorias ===
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
        # === 🆕 NOVA FUNCIONALIDADE: Seleção múltipla de turmas ===
        st.subheader("🏫 Selecionar Turma(s)")
        turmas = ordenar_turmas(df_alunos["turma"].unique().tolist())
        turmas_selecionadas = st.multiselect(
            "Selecione uma ou mais turmas",
            turmas,
            key="multi_turma_reg"
        )
        
        # Filtrar alunos das turmas selecionadas
        if turmas_selecionadas:
            alunos_filtrados = df_alunos[df_alunos["turma"].isin(turmas_selecionadas)].copy()
        else:
            alunos_filtrados = df_alunos.copy()
        
        # === 🆕 NOVA FUNCIONALIDADE: Seleção múltipla de estudantes ===
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 👥 Selecionar Estudante(s)")
            lista_alunos = alunos_filtrados['nome'].tolist()
            alunos_selecionados = st.multiselect(
                "Selecione um ou mais alunos",
                lista_alunos,
                key="multi_aluno_reg"
            )
        with col2:
            st.markdown("### 📅 Data e Hora")
            data = st.date_input("Data", value=datetime.now().date(), key="data_input_occ_reg")
            hora = st.time_input("Hora", value=datetime.now().time(), key="hora_input_occ_reg")
        
        st.markdown("---")
        
        # === 🆕 NOVA FUNCIONALIDADE: Seleção múltipla de categorias ===
        st.subheader("📋 Selecionar Infração(ões)")
        categorias_selecionadas = []
        categorias_gravidades = {}
        
        col1, col2 = st.columns(2)
        with col1:
            for grupo, categorias in CATEGORIAS_OCORRENCIAS.items():
                if st.checkbox(f"{grupo}", key=f"chk_grupo_{grupo}_reg"):
                    for cat, grav in categorias.items():
                        if st.checkbox(f"  └ {cat} ({grav})", key=f"chk_cat_{cat}_reg"):
                            categorias_selecionadas.append(cat)
                            categorias_gravidades[cat] = grav
        
        with col2:
            if categorias_selecionadas:
                st.markdown("### ⚡ Definir Gravidade")
                for cat in categorias_selecionadas:
                    grav_default = categorias_gravidades.get(cat, "Leve")
                    grav_select = st.selectbox(
                        f"{cat}",
                        ["Gravíssima", "Grave", "Média", "Leve"],
                        index=["Gravíssima", "Grave", "Média", "Leve"].index(grav_default),
                        key=f"sel_grav_{cat}_reg"
                    )
                    categorias_gravidades[cat] = grav_select
        
        # Fluxo de Ações (para a primeira categoria selecionada)
        if categorias_selecionadas:
            primeira_cat = categorias_selecionadas[0]
            if primeira_cat in FLUXO_ACOES:
                st.markdown(f"""<div class="fluxo-alert"><b>📌 Fluxo de Ações - Protocolo 179:</b><br>{FLUXO_ACOES[primeira_cat]}</div>""", unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("👥 Envolvidos / Quem Fez a Queixa")
        envolvidos = st.text_area(
            "Descreva os envolvidos ou quem fez a queixa:",
            placeholder="Ex: Professor João Silva (queixa), Aluno Pedro Santos (envolvido)...",
            height=80,
            key="txt_envolvidos_reg"
        )
        
        st.subheader("🔄 Encaminhamentos")
        # Usa a gravidade da primeira categoria para definir encaminhamentos
        gravidade_ref = categorias_gravidades[categorias_selecionadas[0]] if categorias_selecionadas else "Leve"
        encaminhamentos_disponiveis = ENCAMINHAMENTOS_POR_GRAVIDADE.get(gravidade_ref, [])
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
        
        relato = st.text_area("📝 Relato da Ocorrência", height=200, key="txt_relato_reg")
        
        st.markdown("---")
        
        # === 🆕 NOVA FUNCIONALIDADE: Botão salva múltiplas ocorrências (loop) ===
        if st.button("💾 Salvar Ocorrência(s)", type="primary", key="btn_salvar_ocorrencia_reg"):
            if not alunos_selecionados:
                st.error("❌ Selecione pelo menos um estudante!")
            elif not prof or prof == "Selecione...":
                st.error("❌ Selecione o professor responsável!")
            elif not relato:
                st.error("❌ Preencha o relato da ocorrência!")
            elif not categorias_selecionadas:
                st.error("❌ Selecione pelo menos uma infração!")
            else:
                data_str = f"{data.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}"
                contagem_sucesso = 0
                contagem_erro = 0
                
                # Loop para cada aluno selecionado
                for aluno_nome in alunos_selecionados:
                    aluno_info = alunos_filtrados[alunos_filtrados["nome"] == aluno_nome]
                    if not aluno_info.empty:
                        ra_aluno = str(aluno_info["ra"].values[0])
                        turma_aluno = str(aluno_info["turma"].values[0])
                        
                        # Loop para cada categoria selecionada
                        for categoria in categorias_selecionadas:
                            ocorrencia_dict = {
                                'data': data_str,
                                'aluno': aluno_nome,
                                'ra': ra_aluno,
                                'turma': turma_aluno,
                                'categoria': categoria,
                                'gravidade': categorias_gravidades[categoria],
                                'relato': relato,
                                'professor': prof,
                                'encaminhamento': encaminhamento_str,
                                'envolvidos': envolvidos
                            }
                            
                            sucesso, mensagem = salvar_ocorrencia(ocorrencia_dict)
                            if sucesso:
                                contagem_sucesso += 1
                            else:
                                contagem_erro += 1
                                st.error(f"❌ Erro com {aluno_nome} - {categoria}: {mensagem}")
                
                if contagem_sucesso > 0:
                    st.success(f"✅ {contagem_sucesso} ocorrência(s) registrada(s) com sucesso!")
                    st.session_state.ocorrencia_salva_sucesso = True
                    carregar_ocorrencias.clear()
                    st.rerun()
                if contagem_erro > 0:
                    st.warning(f"⚠️ {contagem_erro} ocorrência(s) não puderam ser salvas")

# ============================================================================
# PÁGINA: LISTA DE OCORRÊNCIAS
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
        
        # EDITAR OCORRÊNCIA
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
                        'encaminhamento': ocorrencia.get('encaminhamento', ''),
                        'envolvidos': ocorrencia.get('envolvidos', '')
                    }
                    st.success(f"✅ Ocorrência {id_editar} carregada para edição!")
        
        if st.session_state.editando_id is not None and st.session_state.dados_edicao:
            st.markdown("---")
            st.subheader(f"✏️ Editando Ocorrência ID: {st.session_state.editando_id}")
            dados = st.session_state.dados_edicao
            st.info(f"**Protocolo (ID):** {dados.get('id', 'N/A')} (NÃO PODE SER ALTERADO)")
            col1, col2 = st.columns(2)
            with col1:
                edit_relato = st.text_area("📝 Relato", value=str(dados.get("relato", "")), height=150, key="txt_edit_relato_list")
            with col2:
                edit_grav = st.selectbox("⚡ Gravidade", ["Gravíssima", "Grave", "Média", "Leve"], index=["Gravíssima", "Grave", "Média", "Leve"].index(str(dados.get("gravidade", "Leve"))) if str(dados.get("gravidade", "Leve")) in ["Gravíssima", "Grave", "Média", "Leve"] else 3, key="sel_edit_grav_list")
            edit_envolvidos = st.text_area("👥 Envolvidos/Queixa", value=str(dados.get("envolvidos", "")), height=80, key="txt_edit_envolvidos_list")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar Alterações", type="primary", key="btn_salvar_edicao_list"):
                    dados_atualizados = {
                        'data': dados.get('data', ''),
                        'aluno': dados.get('aluno', ''),
                        'ra': dados.get('ra', ''),
                        'turma': dados.get('turma', ''),
                        'categoria': dados.get('categoria', ''),
                        'gravidade': edit_grav,
                        'relato': edit_relato,
                        'professor': dados.get('professor', ''),
                        'encaminhamento': dados.get('encaminhamento', ''),
                        'envolvidos': edit_envolvidos
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
        
        # EXCLUIR OCORRÊNCIA
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
        
        # GERAR PDF
        st.markdown("---")
        st.subheader("📄 Gerar PDF")
        id_selecionado = st.number_input("ID da Ocorrência", min_value=1, step=1, key="num_id_pdf_list")
        if st.button("📄 Gerar PDF", key="btn_gerar_pdf_list"):
            ocorrencia_row = df_filtrado[df_filtrado['id'] == id_selecionado]
            if not ocorrencia_row.empty:
                ocorrencia = ocorrencia_row.iloc[0].to_dict()
                pdf_buffer = gerar_pdf_ocorrencia(ocorrencia)
                st.download_button(label="📥 Baixar PDF", data=pdf_buffer, file_name=f"ocorrencia_{id_selecionado}.pdf", mime="application/pdf")
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
                    if st.button("✏️", key=f"btn_edit_prof_{prof.get('id', idx)}"):
                        st.session_state.editando_prof = prof.get('id')
                        st.rerun()
                with col5:
                    if st.button("🗑️", key=f"btn_del_prof_{prof.get('id', idx)}"):
                        senha = st.text_input("Senha (040600)", type="password", key=f"txt_senha_prof_{prof.get('id', idx)}")
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
# === 🆕 NOVA PÁGINA: RESPONSÁVEIS (GESTÃO DE ASSINATURAS) ===
# ============================================================================

elif menu == "👥 Responsáveis":
    st.title("👥 Gerenciar Responsáveis pelas Assinaturas")
    st.info("💡 Cadastre Diretor(a), Vice-Diretor(a) e Coordenador(a) para aparecerem nos PDFs")
    
    df_responsaveis = carregar_responsaveis()
    
    # === NOVO RESPONSÁVEL ===
    st.subheader("📝 Novo Responsável")
    col1, col2 = st.columns(2)
    with col1:
        nome_resp = st.text_input("Nome Completo *", key="txt_nome_resp_page")
    with col2:
        cargo_resp = st.selectbox(
            "Cargo *",
            ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)", "Outro"],
            key="sel_cargo_resp_page"
        )
        if cargo_resp == "Outro":
            cargo_resp = st.text_input("Especificar Cargo", key="txt_outro_cargo_page")
    
    if st.session_state.get('editando_resp', None) is not None:
        st.info(f"✏️ Editando responsável ID: {st.session_state.editando_resp}")
        if st.button("💾 Atualizar Responsável", key="btn_atualizar_resp_page"):
            if nome_resp and cargo_resp:
                resp_dict = {'nome': nome_resp.strip(), 'cargo': cargo_resp.strip()}
                sucesso, msg = atualizar_responsavel(st.session_state.editando_resp, resp_dict)
                if sucesso:
                    st.success(f"✅ {msg}")
                    st.session_state.editando_resp = None
                    carregar_responsaveis.clear()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            else:
                st.error("❌ Nome e Cargo são obrigatórios!")
        if st.button("❌ Cancelar Edição", key="btn_cancelar_resp_page"):
            st.session_state.editando_resp = None
            st.rerun()
    else:
        if st.button("💾 Salvar Responsável", key="btn_salvar_resp_page"):
            if nome_resp and cargo_resp:
                resp_dict = {'nome': nome_resp.strip(), 'cargo': cargo_resp.strip()}
                sucesso, msg = salvar_responsavel(resp_dict)
                if sucesso:
                    st.success(f"✅ {msg}")
                    carregar_responsaveis.clear()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            else:
                st.error("❌ Nome e Cargo são obrigatórios!")
    
    st.markdown("---")
    
    # === LISTA DE RESPONSÁVEIS ===
    st.subheader("📋 Responsáveis Cadastrados")
    if not df_responsaveis.empty:
        for idx, resp in df_responsaveis.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 4, 3, 1, 1])
                with col1:
                    st.write("👤")
                with col2:
                    st.write(f"**{resp.get('nome', 'N/A')}**")
                with col3:
                    st.write(f"📋 {resp.get('cargo', 'N/A')}")
                with col4:
                    if st.button("✏️", key=f"btn_edit_resp_{resp.get('id', idx)}"):
                        st.session_state.editando_resp = resp.get('id')
                        st.rerun()
                with col5:
                    if st.button("🗑️", key=f"btn_del_resp_{resp.get('id', idx)}"):
                        senha = st.text_input("Senha (040600)", type="password", key=f"txt_senha_resp_{resp.get('id', idx)}")
                        if senha == SENHA_EXCLUSAO:
                            sucesso, msg = excluir_responsavel(resp.get('id'))
                            if sucesso:
                                st.success(f"✅ {msg}")
                                carregar_responsaveis.clear()
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                        else:
                            st.error("❌ Senha incorreta!")
        st.divider()
        st.info(f"📊 **Total:** {len(df_responsaveis)} responsável(eis) cadastrado(s)")
    else:
        st.info("📭 Nenhum responsável cadastrado ainda.")

# ============================================================================
# PÁGINA: GRÁFICOS
# ============================================================================

elif menu == "📈 Gráficos":
    st.title("📈 Gráficos e Estatísticas")
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    if not df_ocorrencias.empty:
        st.subheader("🔍 Filtro de Período")
        col1, col2 = st.columns(2)
        with col1:
            periodo_selecionado = st.selectbox(
                "Selecione o período:",
                ["Todos", "Último Mês (30 dias)", "Semana Atual (7 dias)", "Semana Passada"],
                key="sel_periodo_graficos"
            )
        with col2:
            filtro_turma = st.multiselect("Turma", df_alunos['turma'].unique().tolist(), key="multi_graf_turma_page")
        
        mapa_periodo = {
            "Todos": "todos",
            "Último Mês (30 dias)": "ultimo_mes",
            "Semana Atual (7 dias)": "semana_atual",
            "Semana Passada": "semana_passada"
        }
        
        periodo_filtro = mapa_periodo.get(periodo_selecionado, "todos")
        df_filtrado_periodo = filtrar_por_periodo(df_ocorrencias, periodo_filtro)
        
        if filtro_turma:
            df_filtrado_periodo = df_filtrado_periodo[df_filtrado_periodo['turma'].isin(filtro_turma)]
        
        st.info(f"📅 Período: **{periodo_selecionado}** - Total: **{len(df_filtrado_periodo)} ocorrências**")
        st.markdown("---")
        
        if not df_filtrado_periodo.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 Ocorrências por Categoria")
                if 'categoria' in df_filtrado_periodo.columns:
                    cat_counts = df_filtrado_periodo['categoria'].value_counts().head(10)
                    fig = px.bar(x=cat_counts.values, y=cat_counts.index, orientation='h', color=cat_counts.values, color_continuous_scale='Reds')
                    fig.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.subheader("📊 Ocorrências por Gravidade")
                if 'gravidade' in df_filtrado_periodo.columns:
                    grav_counts = df_filtrado_periodo['gravidade'].value_counts()
                    fig = px.pie(values=grav_counts.values, names=grav_counts.index, color=grav_counts.index, color_discrete_map=CORES_GRAVIDADE)
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 Ocorrências por Turma")
                if 'turma' in df_filtrado_periodo.columns:
                    turma_counts = df_filtrado_periodo['turma'].value_counts().head(10)
                    fig = px.bar(x=turma_counts.index, y=turma_counts.values, color=turma_counts.values, color_continuous_scale='Blues')
                    fig.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.subheader("📊 Ocorrências por Mês")
                if 'data' in df_filtrado_periodo.columns:
                    df_filtrado_periodo['mes'] = pd.to_datetime(df_filtrado_periodo['data'], format='%d/%m/%Y %H:%M', errors='coerce').dt.strftime('%m/%Y')
                    mes_counts = df_filtrado_periodo['mes'].value_counts().sort_index()
                    fig = px.line(x=mes_counts.index, y=mes_counts.values, markers=True)
                    fig.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("🔥 Mapa de Calor: Categoria x Gravidade")
            if 'categoria' in df_filtrado_periodo.columns and 'gravidade' in df_filtrado_periodo.columns:
                heatmap_data = pd.crosstab(df_filtrado_periodo['categoria'], df_filtrado_periodo['gravidade'])
                fig = px.imshow(heatmap_data, text_auto=True, aspect="auto", color_continuous_scale='YlOrRd')
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.subheader("📊 Estatísticas Resumidas")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total de Ocorrências", len(df_filtrado_periodo))
            with col2:
                st.metric("Turmas Afetadas", df_filtrado_periodo['turma'].nunique() if 'turma' in df_filtrado_periodo.columns else 0)
            with col3:
                st.metric("Alunos Envolvidos", df_filtrado_periodo['ra'].nunique() if 'ra' in df_filtrado_periodo.columns else 0)
            with col4:
                gravissima_count = len(df_filtrado_periodo[df_filtrado_periodo['gravidade'] == 'Gravíssima']) if 'gravidade' in df_filtrado_periodo.columns else 0
                st.metric("Ocorrências Gravíssimas", gravissima_count)
        else:
            st.info("📭 Nenhuma ocorrência registrada no período selecionado.")
    else:
        st.info("📭 Nenhuma ocorrência registrada para gerar gráficos.")

# ============================================================================
# PÁGINA: RELATÓRIOS
# ============================================================================

elif menu == "🖨️ Relatórios":
    st.title("🖨️ Relatórios e Top 10 Alunos")
    
    df_ocorrencias = carregar_ocorrencias()
    df_alunos = carregar_alunos()
    df_responsaveis = carregar_responsaveis()
    
    if not df_ocorrencias.empty:
        st.subheader("🏆 Top 10 Estudantes com Mais Ocorrências")
        top_alunos = get_top_alunos_ocorrencias(df_ocorrencias, df_alunos, top_n=10)
        
        if not top_alunos.empty:
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
            
            st.markdown("---")
            st.subheader("🔍 Pesquisar Ocorrências por Estudante")
            
            busca_aluno = st.text_input("Digite o nome do estudante:", key="txt_busca_aluno_rel")
            
            if busca_aluno:
                df_alunos_filtrado = df_alunos[df_alunos['nome'].str.contains(busca_aluno, case=False, na=False)]
                
                if not df_alunos_filtrado.empty:
                    aluno_selecionado = st.selectbox("Selecione o aluno:", df_alunos_filtrado['nome'].tolist(), key="sel_aluno_rel")
                    aluno_info = df_alunos_filtrado[df_alunos_filtrado['nome'] == aluno_selecionado].iloc[0]
                    ra_aluno = aluno_info['ra']
                    
                    ocorrencias_aluno = get_ocorrencias_por_aluno(df_ocorrencias, ra_aluno)
                    
                    if not ocorrencias_aluno.empty:
                        st.info(f"**Total de Ocorrências:** {len(ocorrencias_aluno)}")
                        st.dataframe(ocorrencias_aluno[['id', 'data', 'categoria', 'gravidade', 'professor', 'turma']], use_container_width=True)
                        
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
                                    'encaminhamento': ocorrencia.get('encaminhamento', ''),
                                    'envolvidos': ocorrencia.get('envolvidos', '')
                                }
                                st.success(f"✅ Ocorrência {id_editar} carregada! Vá em 'Lista de Ocorrências' para editar.")
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
                pdf_buffer = gerar_pdf_ocorrencia(ocorrencia, df_responsaveis)
                nome_arquivo = f"ocorrencia_{id_selecionado}_{ocorrencia.get('aluno', 'aluno')}.pdf"
                st.download_button(label="📥 Baixar PDF", data=pdf_buffer, file_name=nome_arquivo, mime="application/pdf")
                st.success("✅ PDF gerado com sucesso!")
            else:
                st.error("❌ Ocorrência não encontrada.")
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
        st.info(f"**Nome:** {ESCOLA_NOME}\n**Endereço:** {ESCOLA_ENDERECO}\n**CEP:** {ESCOLA_CEP}")
    with col2:
        st.info(f"**Telefone:** {ESCOLA_TELEFONE}\n**Email:** {ESCOLA_EMAIL}\n**Logo:** {ESCOLA_LOGO}")
    st.subheader("🔐 Configurações de Segurança")
    st.warning("**Senha para Exclusão:** 040600")
    st.subheader("📊 Informações do Sistema")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Versão", "14.1 FINAL - Supabase")
    with col2:
        st.metric("Framework", "Streamlit")
    with col3:
        st.metric("Banco", "Supabase")

# ============================================================================
# PÁGINA: BACKUP
# ============================================================================

elif menu == "💾 Backup":
    st.title("💾 Backup e Restauração")
    st.subheader("📥 Gerar Backup")
    st.info("💡 O backup contém todos os dados do sistema.")
    if st.button("📥 Gerar Backup Completo", key="btn_gerar_backup_page"):
        df_alunos = carregar_alunos()
        df_professores = carregar_professores()
        df_ocorrencias = carregar_ocorrencias()
        backup_data = {
            'alunos': df_alunos.to_dict('records') if not df_alunos.empty else [],
            'professores': df_professores.to_dict('records') if not df_professores.empty else [],
            'ocorrencias': df_ocorrencias.to_dict('records') if not df_ocorrencias.empty else [],
            'data_backup': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'versao_sistema': '14.1 FINAL - Supabase'
        }
        json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
        st.download_button(label="📥 Baixar Backup JSON", data=json_str, file_name=f"backup_conviva_{datetime.now().strftime('%Y%m%d_%H%M')}.json", mime="application/json")
        st.success("✅ Backup gerado com sucesso!")
    
    st.markdown("---")
    st.subheader("📤 Importar Backup")
    st.warning("**ATENÇÃO:** Esta ação irá substituir todos os dados atuais!")
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
                    st.success(f"**Backup importado!**\n- Alunos: {contagem_alunos}\n- Professores: {contagem_professores}\n- Ocorrências: {contagem_ocorrencias}")
                    carregar_alunos.clear()
                    carregar_professores.clear()
                    carregar_ocorrencias.clear()
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
    <p>Versão 14.1 FINAL | Desenvolvido com Streamlit + Supabase</p>
</div>
""", unsafe_allow_html=True)