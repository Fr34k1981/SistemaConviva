# ============================================================================
# SISTEMA CONVIVA 179 - GESTÃO DE OCORRÊNCIAS ESCOLARES
# ============================================================================
# Escola: Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI
# Endereço: R. Valter Souza Costa, 147 - Jardim Primavera, Ferraz de Vasconcelos - SP
# CEP: 08535-310
# Telefone: (11) 4675-1855
# Email: e918623@educacao.sp.gov.br
# ============================================================================
# Versão: 3.0 - COM EXTRAÇÃO DE FOTOS DE PDF
# ============================================================================
# NOVIDADES VERSÃO 3.0:
# - Extração de fotos de alunos via PDF
# - Exibição de fotos dos alunos
# - Armazenamento de imagens no Supabase
# - Upload de evidências em ocorrências
# ============================================================================

# ============================================================================
# IMPORTAÇÃO DE BIBLIOTECAS E DEPENDÊNCIAS
# ============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from io import BytesIO
import requests
import os
from dotenv import load_dotenv
import pytz
import time
from difflib import SequenceMatcher
import base64
from PIL import Image

# ============================================================================
# TENTAR IMPORTAR PyMuPDF PARA EXTRAÇÃO DE IMAGENS DE PDF
# ============================================================================
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    st.warning("⚠️ PyMuPDF não instalado. Funcionalidade de PDF desativada.")

# ============================================================================
# CARREGAR VARIÁVEIS DE AMBIENTE
# ============================================================================
load_dotenv()

# ============================================================================
# CONFIGURAÇÃO SUPABASE
# ============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Sistema Conviva 179 - E.E. Profª Eliane",
    layout="wide",
    page_icon="🏫",
    initial_sidebar_state="expanded"
)

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
    .card { background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .card-title { font-weight: bold; color: #333; }
    .card-value { font-size: 1.5rem; color: #667eea; }
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
    .metric-value { font-size: 2.5rem; font-weight: bold; }
    .metric-label { font-size: 1rem; opacity: 0.9; }
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
    .error-box {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .student-photo {
        border-radius: 8px;
        border: 2px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DADOS DA ESCOLA
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
# MENU LATERAL
# ============================================================================
menu = st.sidebar.selectbox(
    "Menu",
    [
        "🏠 Início",
        "👨‍ Cadastrar Professores",
        "👤 Cadastrar Responsáveis por Assinatura",
        "📝 Registrar Ocorrência",
        "📄 Comunicado aos Pais",
        "📥 Importar Alunos",
        "📋 Gerenciar Turmas Importadas",
        "👥 Lista de Alunos",
        "📋 Histórico de Ocorrências",
        "📊 Gráficos e Indicadores",
        "🖨️ Imprimir PDF"
    ],
    key="menu_principal"
)

# ============================================================================
# CORES POR GRAVIDADE
# ============================================================================
CORES_GRAVIDADE = {
    "Leve": "#4CAF50",
    "Grave": "#FF9800",
    "Gravíssima": "#F44336"
}

# ============================================================================
# PROTOCOLO 179 COMPLETO
# ============================================================================
PROTOCOLO_179 = {
    "📌 Violência e Agressão": {
        "Agressão Física": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Acionar Orientação Educacional\n✅ Notificar famílias\n✅ Conselho Tutelar (se menor de 18 anos)\n✅ B.O. (se houver lesão corporal)"
        },
        "Agressão Verbal": {
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
        }
    },
    "🔫 Armas e Segurança": {
        "Posse de Arma de Fogo": {
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
        "Invasão": {
            "gravidade": "Grave",
            "encaminhamento": "✅ PM (190) se necessário\n✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Reforçar segurança da escola"
        },
        "Roubo": {
            "gravidade": "Grave",
            "encaminhamento": "✅ B.O. recomendado\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Registrar em ata\n✅ Acionar segurança"
        },
        "Furto": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho Tutelar (se menor)\n✅ Mediação pedagógica"
        },
        "Dano ao Patrimônio": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Reparação do dano\n✅ Trabalho educativo"
        }
    },
    "💊 Drogas e Substâncias": {
        "Posse de Celular": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Retirar dispositivo (conforme regimento)\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Devolver aos responsáveis"
        },
        "Consumo de Álcool e Tabaco": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Registrar em ata\n✅ Acompanhamento psicológico\n✅ Trabalho educativo sobre saúde"
        },
        "Consumo de Substâncias Ilícitas": {
            "gravidade": "Grave",
            "encaminhamento": "✅ SAMU (192) se houver emergência\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. recomendado\n✅ CAPS/CREAS\n✅ Acompanhamento especializado"
        },
        "Envolvimento com Tráfico": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 B.O. OBRIGATÓRIO\n✅ PM (190) se necessário\n✅ Conselho Tutelar\n✅ Não confrontar diretamente\n✅ Sigilo e segurança\n✅ Diretoria de Ensino"
        }
    },
    "🧠 Saúde Mental e Comportamento": {
        "Indisciplina": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Mediação pedagógica\n✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho de Classe\n✅ Acompanhamento pedagógico"
        },
        "Evasão Escolar": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Buscar ativa (visita domiciliar)\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Registrar em ata\n✅ Diretoria de Ensino\n✅ Programa de Busca Ativa"
        },
        "Sinais de Automutilação": {
            "gravidade": "Grave",
            "encaminhamento": "✅ SAMU (192) se houver risco imediato\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ CAPS Infantil/Juvenil\n✅ Acompanhamento psicológico\n✅ Rede de proteção"
        },
        "Tentativa de Suicídio": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 SAMU (192) IMEDIATO\n✅ Hospital de referência\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ CAPS\n✅ Rede de proteção\n✅ Pós-venção"
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
        "Violência Doméstica": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚠️ SIGILO ABSOLUTO\n✅ Conselho Tutelar OBRIGATÓRIO\n✅ CREAS\n✅ DDM (se for o caso)\n✅ B.O.\n✅ Não confrontar agressor\n✅ Rede de proteção"
        },
        "Homicídio": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 PM (190) e SAMU (192)\n✅ B.O. OBRIGATÓRIO\n✅ IML (se for o caso)\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Pós-venção"
        }
    },
    "📋 Infrações Administrativas": {
        "Saída não autorizada": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias URGENTE\n✅ Buscar o estudante\n✅ Conselho Tutelar (se recorrente)\n✅ Reforçar controle de acesso"
        },
        "Ausência não justificada": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Buscar o estudante\n✅ Conselho Tutelar (se recorrente)\n✅ Orientação Educacional\n✅ Verificar situação de vulnerabilidade"
        },
        "Outros": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Avaliar necessidade de outros encaminhamentos\n✅ Conselho Tutelar se necessário"
        }
    },
    "⚠️ Infrações Acadêmicas": {
        "Chegar atrasado": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Conversar com o aluno\n✅ Notificar famílias (se recorrente)\n✅ Verificar motivo dos atrasos\n✅ Orientação Educacional"
        },
        "Copiar atividades / Colar": {
            "gravidade": "Média",
            "encaminhamento": "✅ Registrar em ata\n✅ Aplicar nova avaliação\n✅ Notificar famílias\n✅ Orientação Educacional\n✅ Trabalho educativo sobre honestidade acadêmica\n✅ Conselho de Classe"
        },
        "Falsificar assinatura": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ Diretoria de Ensino\n✅ Acompanhamento psicológico\n✅ B.O. recomendado (crime de falsidade ideológica)"
        }
    }
}

# ============================================================================
# FUNÇÕES DE CONEXÃO COM SUPABASE - ALUNOS
# ============================================================================

@st.cache_data(ttl=60)
def carregar_alunos():
    """
    Carrega todos os alunos cadastrados no banco de dados Supabase.
    """
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/alunos?select=*", headers=HEADERS)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Erro ao carregar alunos: {str(e)}")
        return pd.DataFrame()

def salvar_aluno(aluno):
    """
    Salva um novo aluno no banco de dados Supabase.
    """
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/alunos", json=aluno, headers=HEADERS)
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao salvar aluno: {str(e)}")
        return False

def atualizar_aluno(ra, dados):
    """
    Atualiza os dados de um aluno existente no banco de dados.
    """
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra}", json=dados, headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao atualizar aluno: {str(e)}")
        return False

def excluir_alunos_por_turma(turma):
    """
    Exclui todos os alunos de uma turma específica do banco de dados.
    """
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/alunos?turma=eq.{turma}", headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao excluir turma: {str(e)}")
        return False

# ============================================================================
# FUNÇÕES DE CONEXÃO COM SUPABASE - PROFESSORES
# ============================================================================

@st.cache_data(ttl=60)
def carregar_professores():
    """
    Carrega todos os professores cadastrados no banco de dados Supabase.
    """
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/professores?select=*", headers=HEADERS)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Erro ao carregar professores: {str(e)}")
        return pd.DataFrame()

def salvar_professor(professor):
    """
    Salva um novo professor no banco de dados Supabase.
    """
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/professores", json=professor, headers=HEADERS)
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao salvar professor: {str(e)}")
        return False

def atualizar_professor(id_prof, dados):
    """
    Atualiza os dados de um professor existente no banco de dados.
    """
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}", json=dados, headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao atualizar professor: {str(e)}")
        return False

def excluir_professor(id_prof):
    """
    Exclui um professor do banco de dados.
    """
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}", headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao excluir professor: {str(e)}")
        return False

# ============================================================================
# FUNÇÕES DE CONEXÃO COM SUPABASE - RESPONSÁVEIS
# ============================================================================

@st.cache_data(ttl=60)
def carregar_responsaveis():
    """
    Carrega todos os responsáveis ativos cadastrados no banco de dados.
    """
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/responsaveis?select=*&ativo=eq.true", headers=HEADERS)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Erro ao carregar responsáveis: {str(e)}")
        return pd.DataFrame()

def salvar_responsavel(responsavel):
    """
    Salva um novo responsável no banco de dados Supabase.
    """
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/responsaveis", json=responsavel, headers=HEADERS)
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao salvar responsável: {str(e)}")
        return False

def atualizar_responsavel(id_resp, dados):
    """
    Atualiza os dados de um responsável existente no banco de dados.
    """
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}", json=dados, headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao atualizar responsável: {str(e)}")
        return False

def excluir_responsavel(id_resp):
    """
    Exclui um responsável do banco de dados.
    """
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}", headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao excluir responsável: {str(e)}")
        return False

# ============================================================================
# FUNÇÕES DE CONEXÃO COM SUPABASE - OCORRÊNCIAS
# ============================================================================

def carregar_ocorrencias():
    """
    Carrega todas as ocorrências cadastradas no banco de dados.
    """
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/ocorrencias?select=*&order=id.desc", headers=HEADERS)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Erro ao carregar ocorrências: {str(e)}")
        return pd.DataFrame()

def salvar_ocorrencia(ocorrencia):
    """
    Salva uma nova ocorrência no banco de dados Supabase.
    """
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/ocorrencias", json=ocorrencia, headers=HEADERS)
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao salvar ocorrência: {str(e)}")
        return False

def excluir_ocorrencia(id_ocorrencia):
    """
    Exclui uma ocorrência do banco de dados.
    """
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}", headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao excluir: {str(e)}")
        return False

def editar_ocorrencia(id_ocorrencia, dados):
    """
    Edita uma ocorrência existente no banco de dados.
    """
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}", json=dados, headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao editar: {str(e)}")
        return False

# ============================================================================
# FUNÇÕES DE VALIDAÇÃO E VERIFICAÇÃO
# ============================================================================

def verificar_ocorrencia_duplicada(ra, categoria, data_str, df_ocorrencias):
    """
    Verifica se já existe uma ocorrência igual para o mesmo aluno.
    """
    if df_ocorrencias.empty:
        return False
    ocorrencias_existentes = df_ocorrencias[
        (df_ocorrencias['ra'] == ra) & 
        (df_ocorrencias['categoria'] == categoria) & 
        (df_ocorrencias['data'] == data_str)
    ]
    return not ocorrencias_existentes.empty

def verificar_professor_duplicado(nome, df_professores, id_atual=None):
    """
    Verifica se já existe um professor com o mesmo nome cadastrado.
    """
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
# FUNÇÕES DE EXTRAÇÃO DE IMAGENS DE PDF (NOVIDADE v3.0)
# ============================================================================

def extrair_imagens_do_pdf(pdf_path, pasta_destino):
    """
    Extrai todas as imagens de um arquivo PDF e salva em uma pasta.
    
    Args:
        pdf_path (str): Caminho completo do arquivo PDF.
        pasta_destino (str): Pasta onde as imagens serão salvas.
    
    Returns:
        list: Lista com os nomes das imagens extraídas.
    """
    if not PDF_SUPPORT:
        st.error("❌ PyMuPDF não está instalado. Instale com: pip install PyMuPDF")
        return []
    
    try:
        imagens_salvas = []
        os.makedirs(pasta_destino, exist_ok=True)
        
        doc = fitz.open(pdf_path)
        
        for pagina_num in range(len(doc)):
            pagina = doc.load_page(pagina_num)
            imagens = pagina.get_images(full=True)
            
            for img_index, img in enumerate(imagens):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                nome_imagem = f"pagina_{pagina_num+1}_img_{img_index}.{image_ext}"
                caminho_imagem = os.path.join(pasta_destino, nome_imagem)
                
                with open(caminho_imagem, "wb") as f:
                    f.write(image_bytes)
                
                imagens_salvas.append(nome_imagem)
        
        doc.close()
        return imagens_salvas
    
    except Exception as e:
        st.error(f"Erro ao extrair imagens: {str(e)}")
        return []

def associar_foto_ao_aluno(ra, imagem_path):
    """
    Associa uma imagem/foto a um aluno pelo seu RA.
    
    Args:
        ra (str): RA do aluno.
        imagem_path (str): Caminho da imagem a ser associada.
    
    Returns:
        bool: True se sucesso, False se erro.
    """
    try:
        with open(imagem_path, "rb") as f:
            imagem_bytes = f.read()
        
        imagem_base64 = base64.b64encode(imagem_bytes).decode('utf-8')
        
        dados = {"foto": imagem_base64}
        return atualizar_aluno(ra, dados)
    
    except Exception as e:
        st.error(f"Erro ao associar foto: {str(e)}")
        return False

def exibir_foto_aluno(ra, df_alunos):
    """
    Exibe a foto de um aluno se estiver cadastrada.
    
    Args:
        ra (str): RA do aluno.
        df_alunos (pd.DataFrame): DataFrame com dados dos alunos.
    """
    try:
        aluno = df_alunos[df_alunos['ra'] == ra]
        
        if not aluno.empty and 'foto' in aluno.columns:
            foto_base64 = aluno['foto'].values[0]
            
            if foto_base64:
                imagem_bytes = base64.b64decode(foto_base64)
                st.image(imagem_bytes, width=150, caption=f"RA: {ra}")
            else:
                st.info("📷 Sem foto")
        else:
            st.info("📷 Sem foto")
    
    except Exception as e:
        st.info("📷 Sem foto")

# ============================================================================
# FUNÇÕES DE GERAÇÃO DE PDF
# ============================================================================

def gerar_pdf_ocorrencia(ocorrencia, responsaveis):
    """
    Gera um documento PDF de registro de ocorrência escolar.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elementos = []
    estilos = getSampleStyleSheet()
    
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4*cm)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 0.1*cm))
    except:
        pass
    
    elementos.append(Paragraph("_" * 75, estilos['Normal']))
    elementos.append(Spacer(1, 0.15*cm))
    
    protocolo = f"PROTOCOLO: {ocorrencia.get('id', 'N/A')}/{datetime.now().strftime('%Y')}"
    elementos.append(Paragraph(f"<b>{protocolo}</b>", ParagraphStyle('Protocolo', parent=estilos['Normal'], fontSize=9, alignment=2)))
    elementos.append(Spacer(1, 0.15*cm))
    elementos.append(Paragraph("REGISTRO DE OCORRÊNCIA", ParagraphStyle('TituloDoc', parent=estilos['Heading1'], fontSize=12, alignment=1)))
    elementos.append(Spacer(1, 0.2*cm))
    
    dados = [
        ["Data:", ocorrencia.get("data", "")],
        ["Aluno:", ocorrencia.get("aluno", "")],
        ["RA:", str(ocorrencia.get("ra", ""))],
        ["Turma:", ocorrencia.get("turma", "")],
        ["Categoria:", ocorrencia.get("categoria", "")],
        ["Gravidade:", ocorrencia.get("gravidade", "")],
        ["Professor:", ocorrencia.get("professor", "")]
    ]
    tabela_dados = Table(dados, colWidths=[3*cm, 12*cm])
    tabela_dados.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#4A90E2')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elementos.append(tabela_dados)
    elementos.append(Spacer(1, 0.2*cm))
    
    elementos.append(Paragraph("<b>📝 RELATO:</b>", ParagraphStyle('Secao', parent=estilos['Normal'], fontSize=9)))
    elementos.append(Paragraph(str(ocorrencia.get("relato", "")), ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=8)))
    elementos.append(Spacer(1, 0.15*cm))
    
    elementos.append(Paragraph("<b>🔀 ENCAMINHAMENTOS:</b>", ParagraphStyle('Secao', parent=estilos['Normal'], fontSize=9)))
    elementos.append(Paragraph(str(ocorrencia.get("encaminhamento", "")).replace('\n', '<br/>'), ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=8)))
    elementos.append(Spacer(1, 0.5*cm))
    
    elementos.append(Paragraph("<b>ASSINATURAS:</b>", ParagraphStyle('Secao', parent=estilos['Normal'], fontSize=9)))
    elementos.append(Spacer(1, 0.2*cm))
    
    cargos = ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)", "Professor Responsável"]
    for cargo in cargos:
        if cargo == "Professor Responsável":
            nome = ocorrencia.get("professor", "")
            if nome:
                elementos.append(Paragraph(f"<b>{cargo}:</b> {nome}", ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=8)))
        else:
            resp_cargo = responsaveis[responsaveis['cargo'] == cargo] if not responsaveis.empty else pd.DataFrame()
            if not resp_cargo.empty:
                for idx, resp in resp_cargo.iterrows():
                    elementos.append(Paragraph(f"<b>{cargo}:</b> {resp['nome']}", ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=8)))
    
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ParagraphStyle('Rodape', parent=estilos['Normal'], fontSize=6, alignment=1)))
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

def gerar_pdf_comunicado(aluno_data, ocorrencia_data, medidas_aplicadas, observacoes, responsaveis):
    """
    Gera um documento PDF de comunicado aos pais/responsáveis.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elementos = []
    estilos = getSampleStyleSheet()
    
    try:
        if os.path.exists(ESCOLA_LOGO):
            logo = Image(ESCOLA_LOGO, width=16*cm, height=4*cm)
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 0.1*cm))
    except:
        pass
    
    elementos.append(Paragraph("_" * 75, estilos['Normal']))
    elementos.append(Spacer(1, 0.15*cm))
    
    protocolo = f"PROTOCOLO: {ocorrencia_data.get('id', 'N/A')}/{datetime.now().strftime('%Y')}"
    elementos.append(Paragraph(f"<b>{protocolo}</b>", ParagraphStyle('Protocolo', parent=estilos['Normal'], fontSize=9, alignment=2)))
    elementos.append(Spacer(1, 0.15*cm))
    elementos.append(Paragraph("COMUNICADO AOS PAIS/RESPONSÁVEIS", ParagraphStyle('TituloDoc', parent=estilos['Heading1'], fontSize=12, alignment=1)))
    elementos.append(Spacer(1, 0.2*cm))
    
    dados_aluno = [
        ["Nome:", aluno_data.get("nome", "")],
        ["RA:", str(aluno_data.get("ra", ""))],
        ["Turma:", aluno_data.get("turma", "")],
        ["Total Ocorrências:", str(aluno_data.get("total_ocorrencias", 0))]
    ]
    tabela_aluno = Table(dados_aluno, colWidths=[3*cm, 12*cm])
    tabela_aluno.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#4A90E2')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elementos.append(tabela_aluno)
    elementos.append(Spacer(1, 0.2*cm))
    
    dados_ocorrencia = [
        ["Data:", ocorrencia_data.get("data", "")],
        ["Categoria:", ocorrencia_data.get("categoria", "")],
        ["Gravidade:", ocorrencia_data.get("gravidade", "")],
        ["Professor:", ocorrencia_data.get("professor", "")]
    ]
    tabela_ocorrencia = Table(dados_ocorrencia, colWidths=[3*cm, 12*cm])
    tabela_ocorrencia.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#4A90E2')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elementos.append(tabela_ocorrencia)
    elementos.append(Spacer(1, 0.2*cm))
    
    elementos.append(Paragraph("<b>📝 RELATO:</b>", ParagraphStyle('Secao', parent=estilos['Normal'], fontSize=9)))
    elementos.append(Paragraph(str(ocorrencia_data.get("relato", "")), ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=8)))
    elementos.append(Spacer(1, 0.15*cm))
    
    if medidas_aplicadas:
        elementos.append(Paragraph("<b>⚖️ MEDIDAS:</b>", ParagraphStyle('Secao', parent=estilos['Normal'], fontSize=9)))
        for medida in medidas_aplicadas.split(' | '):
            if medida.strip():
                elementos.append(Paragraph(f"• {medida}", ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=8)))
        elementos.append(Spacer(1, 0.15*cm))
    
    if observacoes:
        elementos.append(Paragraph("<b>📌 OBSERVAÇÕES:</b>", ParagraphStyle('Secao', parent=estilos['Normal'], fontSize=9)))
        elementos.append(Paragraph(str(observacoes), ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=8)))
        elementos.append(Spacer(1, 0.15*cm))
    
    elementos.append(Paragraph("<b>🔀 ENCAMINHAMENTOS:</b>", ParagraphStyle('Secao', parent=estilos['Normal'], fontSize=9)))
    for linha in str(ocorrencia_data.get("encaminhamento", "")).split('\n'):
        if linha.strip():
            elementos.append(Paragraph(f"• {linha}", ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=8)))
    
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("<b>CIÊNCIA DOS PAIS:</b>", ParagraphStyle('Secao', parent=estilos['Normal'], fontSize=9)))
    elementos.append(Spacer(1, 0.2*cm))
    elementos.append(Paragraph("Declaro ciência deste comunicado.", ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=8)))
    elementos.append(Spacer(1, 1*cm))
    elementos.append(Paragraph("_" * 40, estilos['Normal']))
    elementos.append(Paragraph("Assinatura do Responsável", ParagraphStyle('Assinatura', parent=estilos['Normal'], fontSize=7, alignment=1)))
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ParagraphStyle('Rodape', parent=estilos['Normal'], fontSize=6, alignment=1)))
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# ============================================================================
# SESSION STATE
# ============================================================================

if 'editando_id' not in st.session_state:
    st.session_state.editando_id = None
if 'dados_edicao' not in st.session_state:
    st.session_state.dados_edicao = None
if 'editando_prof' not in st.session_state:
    st.session_state.editando_prof = None
if 'editando_resp' not in st.session_state:
    st.session_state.editando_resp = None
if 'turma_para_deletar' not in st.session_state:
    st.session_state.turma_para_deletar = None
if 'turma_selecionada' not in st.session_state:
    st.session_state.turma_selecionada = None
if 'ocorrencia_salva_sucesso' not in st.session_state:
    st.session_state.ocorrencia_salva_sucesso = False

# ============================================================================
# CARREGAR DADOS
# ============================================================================

df_alunos = carregar_alunos()
df_ocorrencias = carregar_ocorrencias()
df_professores = carregar_professores()
df_responsaveis = carregar_responsaveis()

# ============================================================================
# 1. HOME
# ============================================================================
if menu == "🏠 Início":
    st.markdown(f"""
        <div class="main-header">
            <img src="https://raw.githubusercontent.com/Fr34k1981/SistemaConviva/main/logo.jpg" style="max-width: 150px; margin-bottom: 1rem;" alt="Logo">
            <div class="school-name">🏫 {ESCOLA_NOME}</div>
            <div class="school-subtitle">{ESCOLA_SUBTITULO}</div>
            <div class="school-address">📍 {ESCOLA_ENDERECO}</div>
            <div class="school-contact">{ESCOLA_CEP} • {ESCOLA_TELEFONE} • {ESCOLA_EMAIL}</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("## 📋 Sistema de Gestão de Ocorrências - Protocolo 179")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total de Alunos", len(df_alunos))
    with col2: st.metric("Ocorrências Registradas", len(df_ocorrencias))
    with col3: st.metric("Gravíssimas", len(df_ocorrencias[df_ocorrencias["gravidade"] == "Gravíssima"]) if not df_ocorrencias.empty else 0)
    with col4: st.metric("Professores", len(df_professores))

# ============================================================================
# 2. CADASTRAR PROFESSORES
# ============================================================================
elif menu == "👨‍ Cadastrar Professores":
    st.header("👨‍🏫 Cadastrar Professores")
    col1, col2 = st.columns(2)
    with col1:
        nome_prof = st.text_input("Nome *", key="novo_nome_prof")
        email_prof = st.text_input("E-mail (opcional)", key="novo_email_prof")
    with col2:
        if st.button("💾 Salvar", type="primary"):
            if nome_prof and not verificar_professor_duplicado(nome_prof, df_professores):
                if salvar_professor({"nome": nome_prof, "email": email_prof or None}):
                    st.success("✅ Salvo!")
                    st.rerun()
            else:
                st.error("❌ Nome obrigatório ou já existe!")
    st.markdown("---")
    if not df_professores.empty:
        for idx, prof in df_professores.iterrows():
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1: st.markdown(f"**{prof['nome']}**")
            with col2:
                if st.button("✏️", key=f"edit_{prof['id']}"):
                    st.session_state.editando_prof = prof['id']
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_{prof['id']}"):
                    if excluir_professor(prof['id']):
                        st.success("✅ Excluído!")
                        st.rerun()

# ============================================================================
# 3. CADASTRAR RESPONSÁVEIS
# ============================================================================
elif menu == "👤 Cadastrar Responsáveis por Assinatura":
    st.header("👤 Responsáveis por Assinatura")
    cargos = ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)"]
    for cargo in cargos:
        st.subheader(f"📌 {cargo}")
        resp_cargo = df_responsaveis[df_responsaveis['cargo'] == cargo] if not df_responsaveis.empty else pd.DataFrame()
        nome_atual = resp_cargo['nome'].values[0] if not resp_cargo.empty else ""
        id_atual = resp_cargo['id'].values[0] if not resp_cargo.empty else None
        col1, col2 = st.columns([3, 1])
        with col1:
            nome_resp = st.text_input("Nome", value=nome_atual, key=f"resp_{cargo}")
        with col2:
            if st.button("💾", key=f"btn_{cargo}"):
                if nome_resp:
                    if id_atual:
                        atualizar_responsavel(id_atual, {"nome": nome_resp})
                    else:
                        salvar_responsavel({"cargo": cargo, "nome": nome_resp, "ativo": True})
                    st.success("✅ Salvo!")
                    st.rerun()
        st.markdown("")

# ============================================================================
# 4. REGISTRAR OCORRÊNCIA
# ============================================================================
elif menu == "📝 Registrar Ocorrência":
    st.header("📝 Nova Ocorrência")
    
    if st.session_state.ocorrencia_salva_sucesso:
        st.markdown('<div class="success-box">✅ OCORRÊNCIA(S) REGISTRADA(S)!</div>', unsafe_allow_html=True)
        st.session_state.ocorrencia_salva_sucesso = False
    
    if df_alunos.empty:
        st.warning("⚠️ Importe alunos primeiro.")
    else:
        tz_sp = pytz.timezone('America/Sao_Paulo')
        data_hora_sp = datetime.now(tz_sp)
        
        st.markdown("### 🏫 Selecionar Aluno(s)")
        modo_multi_turmas = st.checkbox("📚 Selecionar de múltiplas turmas", key="modo_multi_turmas")
        alunos_selecionados = []
        
        if modo_multi_turmas:
            turmas = df_alunos["turma"].unique().tolist()
            turmas_selecionadas = st.multiselect("Turmas:", turmas, key="turmas_multi")
            for turma in turmas_selecionadas:
                st.subheader(f"📚 {turma}")
                alunos_turma = df_alunos[df_alunos["turma"] == turma]["nome"].tolist()
                alunos_sel = st.multiselect(f"Alunos:", alunos_turma, key=f"alunos_{turma}")
                for nome in alunos_sel:
                    ra = df_alunos[(df_alunos["nome"] == nome) & (df_alunos["turma"] == turma)]["ra"].values[0]
                    alunos_selecionados.append({"nome": nome, "ra": str(ra), "turma": turma})
        else:
            turmas = df_alunos["turma"].unique().tolist()
            turma_sel = st.selectbox("Turma", turmas, key="turma_unica")
            alunos = df_alunos[df_alunos["turma"] == turma_sel]
            if len(alunos) > 0:
                modo_multiplo = st.checkbox("👥 Múltiplos alunos", key="modo_multiplo")
                if modo_multiplo:
                    nomes = st.multiselect("Alunos:", alunos["nome"].tolist(), key="alunos_multiplos")
                    for nome in nomes:
                        ra = alunos[alunos["nome"] == nome]["ra"].values[0]
                        alunos_selecionados.append({"nome": nome, "ra": str(ra), "turma": turma_sel})
                else:
                    nome = st.selectbox("Aluno", alunos["nome"].tolist(), key="aluno_unico")
                    if nome:
                        ra = alunos[alunos["nome"] == nome]["ra"].values[0]
                        alunos_selecionados.append({"nome": nome, "ra": str(ra), "turma": turma_sel})
        
        st.markdown("---")
        st.markdown("### 📅 Data e Hora do Fato")
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("📅 Data", value=data_hora_sp.date(), key="data_fato")
        with col2:
            hora = st.time_input("⏰ Hora", value=data_hora_sp.time(), key="hora_fato")
        
        st.markdown("---")
        st.markdown("### 👨‍🏫 Professor")
        if not df_professores.empty:
            prof_lista = df_professores["nome"].tolist()
            prof = st.selectbox("Selecione:", ["Selecione..."] + prof_lista, key="prof_select")
            if prof == "Selecione...":
                prof = st.text_input("Ou digite:", placeholder="Nome", key="prof_text")
        else:
            prof = st.text_input("Nome do Professor", placeholder="Nome", key="prof_text")
        
        st.markdown("---")
        st.markdown("### 📋 Selecionar Infração")
        
        grupo_selecionado = st.selectbox("1️⃣ Selecione o Grupo:", list(PROTOCOLO_179.keys()), key="grupo_select")
        
        st.markdown(f"**2️⃣ Infrações disponíveis em '{grupo_selecionado}':**")
        cats = PROTOCOLO_179[grupo_selecionado]
        
        opcoes_infracoes = []
        for nome_infracao, dados in cats.items():
            opcoes_infracoes.append(f"{nome_infracao} ({dados['gravidade']})")
        
        infracao_selecionada = st.selectbox("Selecione a Infração:", opcoes_infracoes, key="infracao_select")
        nome_infracao = infracao_selecionada.split(" (")[0]
        
        dados_infracao = cats[nome_infracao]
        gravidade_sugerida = dados_infracao["gravidade"]
        encam_sugerido = dados_infracao["encaminhamento"]
        
        st.markdown("---")
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown(f"""
            **📋 Informações da Infração Selecionada:**
            
            **Infração:** {nome_infracao}
            
            **Gravidade Sugerida:** {gravidade_sugerida}
            
            **Encaminhamentos Sugeridos:**
            {encam_sugerido}
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        gravidade = st.selectbox("Gravidade (confirme ou altere):", 
                                ["Leve", "Grave", "Gravíssima"],
                                index=["Leve", "Grave", "Gravíssima"].index(gravidade_sugerida),
                                key="gravidade_select")
        
        encam = st.text_area("Encaminhamentos (confirme ou edite):", 
                            value=encam_sugerido, 
                            height=150, 
                            key="encam_select")
        
        st.markdown("---")
        relato = st.text_area("📝 Relato dos Fatos", height=100, key="relato_novo", placeholder="Descreva os fatos...")
        
        if st.button("💾 Salvar Ocorrência(s)", type="primary"):
            if prof and prof != "Selecione..." and relato and alunos_selecionados:
                data_str = f"{data.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}"
                contagem_salvas = 0
                contagem_duplicadas = 0
                
                for aluno_info in alunos_selecionados:
                    if verificar_ocorrencia_duplicada(aluno_info['ra'], nome_infracao, data_str, df_ocorrencias):
                        contagem_duplicadas += 1
                    else:
                        nova = {
                            "data": data_str,
                            "aluno": aluno_info['nome'],
                            "ra": aluno_info['ra'],
                            "turma": aluno_info['turma'],
                            "categoria": nome_infracao,
                            "gravidade": gravidade,
                            "relato": relato,
                            "encaminhamento": encam,
                            "professor": prof,
                            "medidas_aplicadas": "",
                            "medidas_obs": ""
                        }
                        if salvar_ocorrencia(nova):
                            contagem_salvas += 1
                
                if contagem_salvas > 0:
                    st.success(f"✅ {contagem_salvas} ocorrência(s) registrada(s)!")
                    st.session_state.ocorrencia_salva_sucesso = True
                    st.rerun()
                if contagem_duplicadas > 0:
                    st.warning(f"⚠️ {contagem_duplicadas} já existiam")
            else:
                st.error("❌ Preencha todos os campos obrigatórios!")

# ============================================================================
# 5. COMUNICADO AOS PAIS
# ============================================================================
elif menu == "📄 Comunicado aos Pais":
    st.header("📄 Comunicado")
    if df_alunos.empty or df_ocorrencias.empty:
        st.warning("⚠️ Cadastre alunos e ocorrências primeiro.")
    else:
        busca = st.text_input("🔍 Buscar aluno:", placeholder="Nome ou RA")
        if busca:
            df_filtrado = df_alunos[(df_alunos['nome'].str.contains(busca, case=False, na=False)) | (df_alunos['ra'].astype(str).str.contains(busca, na=False))]
        else:
            df_filtrado = df_alunos
        if not df_filtrado.empty:
            aluno_sel = st.selectbox("Aluno", df_filtrado['nome'].tolist(), key="comunicado_aluno")
            aluno_info = df_alunos[df_alunos['nome'] == aluno_sel].iloc[0]
            ra_aluno = aluno_info['ra']
            ocorrencias_aluno = df_ocorrencias[df_ocorrencias['ra'] == ra_aluno] if not df_ocorrencias.empty else pd.DataFrame()
            if not ocorrencias_aluno.empty:
                occ_sel = st.selectbox("Ocorrência", (ocorrencias_aluno['id'].astype(str) + " - " + ocorrencias_aluno['data'] + " - " + ocorrencias_aluno['categoria']).tolist())
                idx = (ocorrencias_aluno['id'].astype(str) + " - " + ocorrencias_aluno['data'] + " - " + ocorrencias_aluno['categoria']).tolist().index(occ_sel)
                occ_info = ocorrencias_aluno.iloc[idx]
                medidas_opcoes = ["Mediação", "Registro em ata", "Notificação", "Conselho Tutelar", "B.O."]
                medidas_aplicadas = [m for m in medidas_opcoes if st.checkbox(m, key=f"med_{m}")]
                if st.button("🖨️ Gerar", type="primary"):
                    pdf_buffer = gerar_pdf_comunicado(
                        {"nome": aluno_info['nome'], "ra": ra_aluno, "turma": aluno_info['turma'], "total_ocorrencias": len(ocorrencias_aluno)},
                        {"data": occ_info['data'], "categoria": occ_info['categoria'], "gravidade": occ_info['gravidade'], "professor": occ_info['professor'], "relato": occ_info['relato'], "encaminhamento": occ_info['encaminhamento']},
                        " | ".join(medidas_aplicadas), "", df_responsaveis
                    )
                    st.download_button(label="📥 Baixar", data=pdf_buffer, file_name=f"Comunicado_{ra_aluno}.pdf", mime="application/pdf")

# ============================================================================
# 6. IMPORTAR ALUNOS (COM EXTRAÇÃO DE FOTOS)
# ============================================================================
elif menu == "📥 Importar Alunos":
    st.header("📥 Importar Alunos")
    turma_alunos = st.text_input("Turma:", placeholder="Ex: 6º Ano A")
    arquivo_csv = st.file_uploader("CSV dos Alunos", type=["csv"])
    
    # ✅ NOVO: Upload do PDF com fotos
    if PDF_SUPPORT:
        arquivo_fotos = st.file_uploader("📷 PDF com Fotos (opcional)", type=["pdf"])
    else:
        arquivo_fotos = None
        st.info("ℹ️ Instale PyMuPDF para extrair fotos: pip install PyMuPDF")
    
    if arquivo_csv and turma_alunos and st.button("🚀 Importar"):
        df_import = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8-sig')
        contagem = 0
        for idx, row in df_import.iterrows():
            ra = str(row.get('ra', '')).strip()
            if ra and ra != 'nan':
                aluno = {"ra": ra, "nome": str(row.get('nome', '')).strip(), "turma": turma_alunos, "data_nascimento": "", "situacao": ""}
                if salvar_aluno(aluno):
                    contagem += 1
        st.success(f"✅ {contagem} alunos importados!")
        
        # ✅ NOVO: Extrair fotos do PDF
        if arquivo_fotos and PDF_SUPPORT:
            with st.spinner("📷 Extraindo fotos dos alunos..."):
                pdf_temp = os.path.join("uploads", "fotos_temp.pdf")
                os.makedirs("uploads", exist_ok=True)
                
                with open(pdf_temp, "wb") as f:
                    f.write(arquivo_fotos.getbuffer())
                
                fotos_extraidas = extrair_imagens_do_pdf(pdf_temp, "fotos_alunos")
                st.success(f"✅ {len(fotos_extraidas)} fotos extraídas!")
                
                # Associar fotos aos alunos (lógica simplificada)
                if fotos_extraidas:
                    st.info("ℹ️ Fotos extraídas. Associação manual necessária.")
        st.rerun()

# ============================================================================
# 7. GERENCIAR TURMAS
# ============================================================================
elif menu == "📋 Gerenciar Turmas Importadas":
    st.header("📋 Turmas")
    if not df_alunos.empty:
        for turma in df_alunos['turma'].unique():
            col1, col2 = st.columns([3, 1])
            with col1: st.markdown(f"**{turma}** - {len(df_alunos[df_alunos['turma'] == turma])} alunos")
            with col2:
                if st.button(f"🗑️ {turma}", key=f"del_{turma}"):
                    if excluir_alunos_por_turma(turma):
                        st.success(f"✅ {turma} excluída!")
                        st.rerun()

# ============================================================================
# 8. LISTA DE ALUNOS (COM FOTOS)
# ============================================================================
elif menu == "👥 Lista de Alunos":
    st.header("👥 Alunos")
    if not df_alunos.empty:
        # ✅ NOVO: Exibir com fotos
        for idx, aluno in df_alunos.iterrows():
            col1, col2, col3 = st.columns([1, 3, 2])
            with col1:
                exibir_foto_aluno(aluno['ra'], df_alunos)
            with col2:
                st.markdown(f"**{aluno['nome']}**")
                st.write(f"RA: {aluno['ra']} | Turma: {aluno['turma']}")
            with col3:
                st.button("📝 Editar", key=f"edit_{aluno['ra']}")
    else:
        st.write("📭 Nenhum aluno cadastrado.")

# ============================================================================
# 9. HISTÓRICO DE OCORRÊNCIAS
# ============================================================================
elif menu == "📋 Histórico de Ocorrências":
    st.header("📋 Histórico")
    if not df_ocorrencias.empty:
        st.dataframe(df_ocorrencias, use_container_width=True)
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            id_excluir = st.selectbox("ID para excluir", df_ocorrencias["id"].tolist(), key="select_excluir")
            senha = st.text_input("🔒 Senha:", type="password", key="senha_excluir")
            if st.button("🗑️ Excluir"):
                if senha == SENHA_EXCLUSAO:
                    if excluir_ocorrencia(id_excluir):
                        st.success("✅ Excluído!")
                        st.rerun()
                else:
                    st.error("❌ Senha incorreta!")
        with col2:
            id_editar = st.selectbox("ID para editar", df_ocorrencias["id"].tolist(), key="select_editar")
            if st.button("✏️ Carregar"):
                occ = df_ocorrencias[df_ocorrencias["id"] == id_editar].iloc[0].to_dict()
                st.session_state.editando_id = id_editar
                st.session_state.dados_edicao = occ
        if st.session_state.editando_id:
            dados = st.session_state.dados_edicao
            edit_relato = st.text_area("Relato", value=str(dados.get("relato", "")), height=100, key="edit_relato")
            edit_grav = st.selectbox("Gravidade", ["Leve", "Grave", "Gravíssima"], index=["Leve", "Grave", "Gravíssima"].index(str(dados.get("gravidade", "Leve"))), key="edit_grav")
            if st.button("💾 Salvar"):
                if editar_ocorrencia(st.session_state.editando_id, {"relato": edit_relato, "gravidade": edit_grav}):
                    st.session_state.editando_id = None
                    st.success("✅ Salvo!")
                    st.rerun()

# ============================================================================
# 10. GRÁFICOS E INDICADORES
# ============================================================================
elif menu == "📊 Gráficos e Indicadores":
    st.header("📊 Dashboard")
    if not df_ocorrencias.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Por Gravidade")
            st.bar_chart(df_ocorrencias['gravidade'].value_counts())
        with col2:
            st.subheader("Por Categoria")
            st.bar_chart(df_ocorrencias['categoria'].value_counts().head(10))

# ============================================================================
# 11. IMPRIMIR PDF
# ============================================================================
elif menu == "🖨️ Imprimir PDF":
    st.header("🖨️ Gerar PDF")
    if not df_ocorrencias.empty:
        occ_sel = st.selectbox("Selecione", (df_ocorrencias["id"].astype(str) + " - " + df_ocorrencias["aluno"]).tolist())
        idx = (df_ocorrencias["id"].astype(str) + " - " + df_ocorrencias["aluno"]).tolist().index(occ_sel)
        occ = df_ocorrencias.iloc[idx]
        if st.button("📄 Gerar"):
            pdf_buffer = gerar_pdf_ocorrencia(occ, df_responsaveis)
            st.download_button(label="📥 Baixar", data=pdf_buffer, file_name=f"Ocorrencia_{occ['id']}.pdf", mime="application/pdf")

# ============================================================================
# FIM DO CÓDIGO - SISTEMA CONVIVA 179 v3.0
# ============================================================================