# ============================================================================
# SISTEMA CONVIVA 179 - GESTÃO DE OCORRÊNCIAS ESCOLARES
# ============================================================================
# Escola: Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI
# Endereço: R. Valter Souza Costa, 147 - Jardim Primavera, Ferraz de Vasconcelos - SP
# CEP: 08535-310
# Telefone: (11) 4675-1855
# Email: e918623@educacao.sp.gov.br
# ============================================================================
# Versão: 5.0 - Completa com Backup e Fotos
# Desenvolvido para: Streamlit Cloud
# Banco de Dados: Supabase
# ============================================================================
# Funcionalidades Principais:
# 1. Cadastro de Professores
# 2. Cadastro de Responsáveis por Assinatura
# 3. Registro de Ocorrências com Protocolo 179
# 4. Comunicado aos Pais
# 5. Importação de Alunos via CSV
# 6. Gerenciamento de Turmas
# 7. Lista de Alunos
# 8. Histórico de Ocorrências
# 9. Gráficos e Indicadores
# 10. Geração de PDFs
# 11. Backup e Restauração de Dados (NOVO)
# 12. Backup do Código (NOVO)
# 13. Exibição de Fotos dos Alunos (NOVO)
# ============================================================================
# Autor: Sistema Conviva 179
# Data: 2024
# ============================================================================

# ============================================================================
# IMPORTAÇÃO DE BIBLIOTECAS E DEPENDÊNCIAS
# ============================================================================
# Streamlit: Framework para aplicação web
import streamlit as st

# Pandas: Manipulação de dados e DataFrames
import pandas as pd

# Plotly: Gráficos interativos e visualização de dados
import plotly.express as px
import plotly.graph_objects as go

# DateTime: Manipulação de datas e horas
from datetime import datetime, timedelta

# ReportLab: Geração de documentos PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# BytesIO: Manipulação de dados em memória
from io import BytesIO

# Requests: Requisições HTTP para API Supabase
import requests

# OS: Operações do sistema operacional
import os

# Dotenv: Carregamento de variáveis de ambiente
from dotenv import load_dotenv

# Pytz: Fusos horários
import pytz

# Time: Funções de tempo
import time

# SequenceMatcher: Comparação de strings para busca fuzzy
from difflib import SequenceMatcher

# Base64: Codificação de imagens para armazenamento
import base64

# JSON: Manipulação de arquivos JSON para backup
import json

# PIL: Processamento de imagens
from PIL import Image

# ============================================================================
# CARREGAR VARIÁVEIS DE AMBIENTE DO ARQUIVO .ENV
# ============================================================================
# Este comando carrega as variáveis SUPABASE_URL e SUPABASE_KEY do arquivo .env
# Essas variáveis são necessárias para conectar ao banco de dados Supabase
load_dotenv()

# ============================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS SUPABASE
# ============================================================================
# URL da API Supabase - Endpoint principal para conexões
SUPABASE_URL = os.getenv("SUPABASE_URL")

# Chave de API Supabase - Credencial para autenticação nas requisições
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Headers padrão para todas as requisições HTTP à API Supabase
# Inclui autenticação, tipo de conteúdo e preferência de retorno
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ============================================================================
# Configurações da página da aplicação web
# page_title: Título que aparece na aba do navegador
# layout: Layout amplo (wide) para melhor visualização
# page_icon: Ícone da página (emoji de escola)
# initial_sidebar_state: Barra lateral expandida por padrão
st.set_page_config(
    page_title="Sistema Conviva 179 - E.E. Profª Eliane",
    layout="wide",
    page_icon="🏫",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS PERSONALIZADO PARA ESTILIZAÇÃO DA INTERFACE
# ============================================================================
# Este CSS personaliza a aparência da aplicação Streamlit
# Inclui estilos para cabeçalho, cards, métricas, boxes de informação, etc.
st.markdown("""
<style>
/* Cabeçalho principal com gradiente */
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}

/* Nome da escola em destaque */
.school-name {
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

/* Subtítulo da escola em itálico */
.school-subtitle {
    font-size: 1.2rem;
    font-style: italic;
    opacity: 0.9;
}

/* Endereço da escola */
.school-address {
    font-size: 0.9rem;
    margin-top: 1rem;
    opacity: 0.8;
}

/* Contatos da escola */
.school-contact {
    font-size: 0.85rem;
    margin-top: 0.5rem;
    opacity: 0.9;
}

/* Cards de informação */
.card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}

/* Título do card */
.card-title {
    font-weight: bold;
    color: #333;
}

/* Valor do card em destaque */
.card-value {
    font-size: 1.5rem;
    color: #667eea;
}

/* Box de sucesso (verde) */
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

/* Box de informação do protocolo */
.protocolo-info {
    background: #fff3cd;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}

/* Cards de métricas */
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 10px;
    color: white;
    text-align: center;
}

/* Valor da métrica em destaque */
.metric-value {
    font-size: 2.5rem;
    font-weight: bold;
}

/* Label da métrica */
.metric-label {
    font-size: 1rem;
    opacity: 0.9;
}

/* Box de informação (azul) */
.info-box {
    background: #e3f2fd;
    border-left: 4px solid #2196F3;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 4px;
}

/* Box de aviso (amarelo) */
.warning-box {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 4px;
}

/* Box de erro (vermelho) */
.error-box {
    background: #f8d7da;
    border-left: 4px solid #dc3545;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 4px;
}

/* Foto do aluno */
.student-photo {
    border-radius: 8px;
    border: 2px solid #667eea;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DADOS DE IDENTIFICAÇÃO DA ESCOLA
# ============================================================================
# Estas variáveis armazenam as informações da escola que serão exibidas
# em toda a aplicação, incluindo cabeçalhos, PDFs e relatórios
# ============================================================================

# Nome completo da escola conforme registro oficial
ESCOLA_NOME = "Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI"

# Subtítulo ou nome fantasia da escola
ESCOLA_SUBTITULO = "🌟 Escola dos Sonhos"

# Endereço completo da escola
ESCOLA_ENDERECO = "R. Valter Souza Costa, 147 - Jardim Primavera, Ferraz de Vasconcelos - SP"

# Código de Endereçamento Postal (CEP)
ESCOLA_CEP = "CEP: 08535-310"

# Número de telefone para contato
ESCOLA_TELEFONE = "Telefone: (11) 4675-1855"

# Endereço de e-mail institucional
ESCOLA_EMAIL = "Email: e918623@educacao.sp.gov.br"

# Nome do arquivo da logo da escola (deve estar na mesma pasta do app.py)
ESCOLA_LOGO = "eliane_dantas.png"

# Senha de segurança para exclusão de registros
# Esta senha é necessária para excluir ocorrências do sistema
SENHA_EXCLUSAO = "040600"

# ============================================================================
# MENU LATERAL DE NAVEGAÇÃO
# ============================================================================
# Lista de todas as seções disponíveis na aplicação
# O usuário pode navegar entre elas através do menu lateral
# Cada opção corresponde a uma funcionalidade específica do sistema
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
        "🖨️ Imprimir PDF",
        "💾 Backup e Restauração"
    ],
    key="menu_principal"
)

# ============================================================================
# CORES PARA CLASSIFICAÇÃO POR GRAVIDADE
# ============================================================================
# Dicionário que mapeia níveis de gravidade para cores específicas
# Usado em gráficos, indicadores e visualizações
# Estas cores seguem padrões internacionais de semáforo de risco
# ============================================================================
CORES_GRAVIDADE = {
    "Leve": "#4CAF50",      # Verde - ocorrências de menor impacto
    "Grave": "#FF9800",     # Laranja - ocorrências de médio impacto
    "Gravíssima": "#F44336" # Vermelho - ocorrências de alto impacto
}

# ============================================================================
# PROTOCOLO 179 - CATÁLOGO COMPLETO DE INFRAÇÕES
# ============================================================================
# Este dicionário contém todas as infrações previstas no Protocolo 179
# Cada infração possui:
# - gravidade: Nível de severidade (Leve, Grave, Gravíssima)
# - encaminhamento: Lista de ações recomendadas a serem tomadas
#
# As infrações estão organizadas por categorias/grupos temáticos
# Esta estrutura permite busca e filtragem eficiente
# ============================================================================
PROTOCOLO_179 = {
    # =========================================================================
    # GRUPO 1: VIOLÊNCIA E AGRESSÃO
    # =========================================================================
    # Este grupo inclui todas as formas de violência física e verbal
    # entre estudantes, ou envolvendo membros da comunidade escolar
    # =========================================================================
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
    
    # =========================================================================
    # GRUPO 2: ARMAS E SEGURANÇA
    # =========================================================================
    # Este grupo inclui situações envolvendo armas, invasões e riscos
    # à segurança da comunidade escolar
    # =========================================================================
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
        "Ameaça de Ataque Ativo": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 EMERGÊNCIA MÁXIMA\n✅ PM (190) e SAMU (192)\n✅ Protocolo de Segurança Escolar\n✅ Evacuação se necessário\n✅ B.O. OBRIGATÓRIO\n✅ Diretoria de Ensino"
        },
        "Invasão": {
            "gravidade": "Grave",
            "encaminhamento": "✅ PM (190) se necessário\n✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Reforçar segurança da escola"
        },
        "Ocupação de Unidade Escolar": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Dialogar com estudantes\n✅ Notificar famílias\n✅ Diretoria de Ensino\n✅ Registrar em ata\n✅ Buscar mediação"
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
    
    # =========================================================================
    # GRUPO 3: DROGAS E SUBSTÂNCIAS
    # =========================================================================
    # Este grupo inclui situações envolvendo uso, posse ou comércio
    # de substâncias ilícitas ou proibidas no ambiente escolar
    # =========================================================================
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
    
    # =========================================================================
    # GRUPO 4: SAÚDE MENTAL E COMPORTAMENTO
    # =========================================================================
    # Este grupo inclui situações relacionadas à saúde mental dos estudantes
    # e comportamentos que indicam necessidade de apoio psicológico
    # =========================================================================
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
    
    # =========================================================================
    # GRUPO 5: CRIMES E SITUAÇÕES GRAVES
    # =========================================================================
    # Este grupo inclui crimes e situações de alta gravidade que exigem
    # intervenção de órgãos externos e autoridades competentes
    # =========================================================================
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
    
    # =========================================================================
    # GRUPO 6: INFRAÇÕES ADMINISTRATIVAS
    # =========================================================================
    # Este grupo inclui infrações de natureza administrativa e disciplinar
    # relacionadas ao funcionamento da escola e frequência dos alunos
    # =========================================================================
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
    
    # =========================================================================
    # GRUPO 7: INFRAÇÕES ACADÊMICAS
    # =========================================================================
    # Este grupo inclui infrações relacionadas à vida acadêmica dos alunos
    # incluindo frequência, honestidade acadêmica e comportamento em sala
    # =========================================================================
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
    
    Esta função faz uma requisição GET à API do Supabase para recuperar
    todos os registros da tabela 'alunos'. Os dados são cacheados por
    60 segundos para melhorar a performance da aplicação.
    
    Returns:
        pd.DataFrame: DataFrame contendo todos os alunos cadastrados.
                     Retorna DataFrame vazio em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição POST à API do Supabase para criar
    um novo registro na tabela 'alunos'.
    
    Args:
        aluno (dict): Dicionário contendo os dados do aluno a ser salvo.
                     Deve incluir: ra, nome, turma, data_nascimento, situacao.
    
    Returns:
        bool: True se o aluno foi salvo com sucesso (status 200 ou 201),
              False em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição PATCH à API do Supabase para atualizar
    os dados de um aluno identificado pelo seu RA (Registro Acadêmico).
    
    Args:
        ra (str): RA do aluno a ser atualizado.
        dados (dict): Dicionário contendo os campos e valores a serem atualizados.
    
    Returns:
        bool: True se a atualização foi bem-sucedida (status 200 ou 204),
              False em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição DELETE à API do Supabase para remover
    todos os registros de alunos pertencentes a uma determinada turma.
    
    Args:
        turma (str): Nome da turma cujos alunos serão excluídos.
    
    Returns:
        bool: True se a exclusão foi bem-sucedida (status 200 ou 204),
              False em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição GET à API do Supabase para recuperar
    todos os registros da tabela 'professores'. Os dados são cacheados
    por 60 segundos para melhorar a performance.
    
    Returns:
        pd.DataFrame: DataFrame contendo todos os professores cadastrados.
                     Retorna DataFrame vazio em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição POST à API do Supabase para criar
    um novo registro na tabela 'professores'.
    
    Args:
        professor (dict): Dicionário contendo os dados do professor.
                         Deve incluir: nome, email (opcional).
    
    Returns:
        bool: True se o professor foi salvo com sucesso (status 200 ou 201),
              False em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição PATCH à API do Supabase para atualizar
    os dados de um professor identificado pelo seu ID.
    
    Args:
        id_prof (int): ID do professor a ser atualizado.
        dados (dict): Dicionário contendo os campos e valores a serem atualizados.
    
    Returns:
        bool: True se a atualização foi bem-sucedida (status 200 ou 204),
              False em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição DELETE à API do Supabase para remover
    um registro de professor identificado pelo seu ID.
    
    Args:
        id_prof (int): ID do professor a ser excluído.
    
    Returns:
        bool: True se a exclusão foi bem-sucedida (status 200 ou 204),
              False em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição GET à API do Supabase para recuperar
    todos os registros da tabela 'responsaveis' onde ativo=TRUE.
    Os dados são cacheados por 60 segundos.
    
    Returns:
        pd.DataFrame: DataFrame contendo todos os responsáveis ativos.
                     Retorna DataFrame vazio em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição POST à API do Supabase para criar
    um novo registro na tabela 'responsaveis'.
    
    Args:
        responsavel (dict): Dicionário contendo os dados do responsável.
                           Deve incluir: cargo, nome, ativo.
    
    Returns:
        bool: True se o responsável foi salvo com sucesso (status 200 ou 201),
              False em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição PATCH à API do Supabase para atualizar
    os dados de um responsável identificado pelo seu ID.
    
    Args:
        id_resp (int): ID do responsável a ser atualizado.
        dados (dict): Dicionário contendo os campos e valores a serem atualizados.
    
    Returns:
        bool: True se a atualização foi bem-sucedida (status 200 ou 204),
              False em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição DELETE à API do Supabase para remover
    um registro de responsável identificado pelo seu ID.
    
    Args:
        id_resp (int): ID do responsável a ser excluído.
    
    Returns:
        bool: True se a exclusão foi bem-sucedida (status 200 ou 204),
              False em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição GET à API do Supabase para recuperar
    todos os registros da tabela 'ocorrencias', ordenados por ID descendente.
    Não utiliza cache para garantir dados sempre atualizados.
    
    Returns:
        pd.DataFrame: DataFrame contendo todas as ocorrências cadastradas.
                     Retorna DataFrame vazio em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição POST à API do Supabase para criar
    um novo registro na tabela 'ocorrencias'.
    
    Args:
        ocorrencia (dict): Dicionário contendo os dados da ocorrência.
                          Deve incluir: data, aluno, ra, turma, categoria,
                          gravidade, relato, encaminhamento, professor.
    
    Returns:
        bool: True se a ocorrência foi salva com sucesso (status 200 ou 201),
              False em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição DELETE à API do Supabase para remover
    um registro de ocorrência identificado pelo seu ID.
    
    Args:
        id_ocorrencia (int): ID da ocorrência a ser excluída.
    
    Returns:
        bool: True se a exclusão foi bem-sucedida (status 200 ou 204),
              False em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função faz uma requisição PATCH à API do Supabase para atualizar
    os dados de uma ocorrência identificada pelo seu ID.
    
    Args:
        id_ocorrencia (int): ID da ocorrência a ser editada.
        dados (dict): Dicionário contendo os campos e valores a serem atualizados.
    
    Returns:
        bool: True se a edição foi bem-sucedida (status 200 ou 204),
              False em caso de erro.
    
    Raises:
        Exception: Erros de conexão com a API são capturados e exibidos
                  como mensagem de erro na interface.
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
    
    Esta função verifica se já existe um registro de ocorrência com o mesmo
    RA do aluno, mesma categoria e mesma data/hora. Isso previne registros
    duplicados acidentais.
    
    Args:
        ra (str): RA do aluno a ser verificado.
        categoria (str): Categoria da ocorrência a ser verificada.
        data_str (str): Data e hora da ocorrência no formato 'DD/MM/YYYY HH:MM'.
        df_ocorrencias (pd.DataFrame): DataFrame com todas as ocorrências.
    
    Returns:
        bool: True se existir ocorrência duplicada, False caso contrário.
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
    
    Esta função verifica se já existe um registro de professor com o mesmo
    nome (ignorando diferenças de maiúsculas/minúsculas e espaços).
    
    Args:
        nome (str): Nome do professor a ser verificado.
        df_professores (pd.DataFrame): DataFrame com todos os professores.
        id_atual (int, optional): ID do professor sendo editado (para não
                                 considerar o próprio registro como duplicado).
    
    Returns:
        bool: True se existir professor duplicado, False caso contrário.
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
# FUNÇÕES DE BACKUP E RESTAURAÇÃO (NOVIDADE v5.0)
# ============================================================================

def criar_backup_dados():
    """
    Cria backup de todos os dados do sistema em formato JSON.
    
    Esta função exporta todos os dados do sistema (alunos, professores,
    responsáveis e ocorrências) para um arquivo JSON que pode ser
    armazenado e restaurado posteriormente.
    
    Returns:
        str: JSON string contendo todos os dados do sistema, ou None em caso de erro.
    """
    try:
        backup = {
            "data_backup": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "versao": "5.0",
            "alunos": df_alunos.to_dict('records') if not df_alunos.empty else [],
            "professores": df_professores.to_dict('records') if not df_professores.empty else [],
            "responsaveis": df_responsaveis.to_dict('records') if not df_responsaveis.empty else [],
            "ocorrencias": df_ocorrencias.to_dict('records') if not df_ocorrencias.empty else []
        }
        return json.dumps(backup, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Erro ao criar backup: {str(e)}")
        return None

def restaurar_backup_dados(backup_json):
    """
    Restaura dados a partir de um backup JSON.
    
    Esta função importa dados de um arquivo JSON de backup e os insere
    no banco de dados Supabase.
    
    Args:
        backup_json (str): JSON string contendo os dados do backup.
    
    Returns:
        bool: True se a restauração foi bem-sucedida, False em caso de erro.
    """
    try:
        backup = json.loads(backup_json)
        
        # Restaurar alunos
        if 'alunos' in backup and backup['alunos']:
            for aluno in backup['alunos']:
                salvar_aluno(aluno)
        
        # Restaurar professores
        if 'professores' in backup and backup['professores']:
            for prof in backup['professores']:
                salvar_professor(prof)
        
        # Restaurar responsáveis
        if 'responsaveis' in backup and backup['responsaveis']:
            for resp in backup['responsaveis']:
                salvar_responsavel(resp)
        
        # Restaurar ocorrências
        if 'ocorrencias' in backup and backup['ocorrencias']:
            for occ in backup['ocorrencias']:
                salvar_ocorrencia(occ)
        
        return True
    except Exception as e:
        st.error(f"Erro ao restaurar backup: {str(e)}")
        return False

def criar_backup_codigo():
    """
    Cria backup do código fonte app.py.
    
    Esta função lê o arquivo app.py atual e o retorna como string
    para que possa ser baixado como backup.
    
    Returns:
        str: Conteúdo do arquivo app.py, ou None em caso de erro.
    """
    try:
        if os.path.exists("app.py"):
            with open("app.py", "r", encoding="utf-8") as f:
                return f.read()
        return None
    except Exception as e:
        st.error(f"Erro ao criar backup do código: {str(e)}")
        return None

# ============================================================================
# FUNÇÕES DE EXIBIÇÃO DE FOTOS (NOVIDADE v5.0)
# ============================================================================

def exibir_foto_aluno(ra, df_alunos):
    """
    Exibe a foto de um aluno se estiver cadastrada.
    
    Esta função busca a foto do aluno no DataFrame, decodifica de base64
    e exibe na interface Streamlit.
    
    Args:
        ra (str): RA do aluno.
        df_alunos (pd.DataFrame): DataFrame com dados dos alunos.
    
    Returns:
        None: Exibe a imagem na interface Streamlit.
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
    
    Esta função cria um documento PDF formatado contendo todos os dados
    de uma ocorrência, incluindo informações do aluno, categoria, gravidade,
    relato, encaminhamentos e assinaturas dos responsáveis.
    
    Args:
        ocorrencia (dict): Dicionário contendo os dados da ocorrência.
        responsaveis (pd.DataFrame): DataFrame com os responsáveis cadastrados.
    
    Returns:
        BytesIO: Objeto BytesIO contendo o PDF gerado em memória.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    elementos = []
    estilos = getSampleStyleSheet()
    
    # Cabeçalho com logo da escola
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
    encam_texto = str(ocorrencia.get("encaminhamento", "")).replace('\n', '<br/>')
    elementos.append(Paragraph(encam_texto, ParagraphStyle('Texto', parent=estilos['Normal'], fontSize=8)))
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
    
    Esta função cria um documento PDF formatado contendo informações sobre
    uma ocorrência específica para ser enviado aos pais ou responsáveis
    do aluno.
    
    Args:
        aluno_data (dict): Dicionário com dados do aluno (nome, ra, turma, total).
        ocorrencia_data (dict): Dicionário com dados da ocorrência.
        medidas_aplicadas (str): String com medidas aplicadas separadas por '|'.
        observacoes (str): Observações adicionais sobre a ocorrência.
        responsaveis (pd.DataFrame): DataFrame com responsáveis cadastrados.
    
    Returns:
        BytesIO: Objeto BytesIO contendo o PDF gerado em memória.
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
# SESSION STATE - GERENCIAMENTO DE ESTADO DA APLICAÇÃO
# ============================================================================
# O Session State do Streamlit permite persistir dados entre interações
# do usuário com a aplicação. Estas variáveis armazenam o estado atual
# de edições, seleções e operações em andamento.
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
# CARREGAMENTO INICIAL DE DADOS
# ============================================================================
# Carrega todos os dados do banco de dados ao iniciar a aplicação
# Estes DataFrames são usados em toda a aplicação para exibir e
# manipular informações de alunos, professores, responsáveis e ocorrências
# ============================================================================

df_alunos = carregar_alunos()
df_ocorrencias = carregar_ocorrencias()
df_professores = carregar_professores()
df_responsaveis = carregar_responsaveis()

# ============================================================================
# 1. PÁGINA INICIAL - DASHBOARD PRINCIPAL
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
# 3. CADASTRAR RESPONSÁVEIS POR ASSINATURA
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
        st.markdown("### 🏫 Selecionar Aluno")
        turmas = df_alunos["turma"].unique().tolist()
        turma_sel = st.selectbox("Turma", turmas, key="turma_unica")
        alunos = df_alunos[df_alunos["turma"] == turma_sel]
        if len(alunos) > 0:
            nome = st.selectbox("Aluno", alunos["nome"].tolist(), key="aluno_unico")
            ra = alunos[alunos["nome"] == nome]["ra"].values[0]
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
        grupo_selecionado = st.selectbox("1️⃣ Grupo:", list(PROTOCOLO_179.keys()), key="grupo_select")
        cats = PROTOCOLO_179[grupo_selecionado]
        lista_infracoes = list(cats.keys())
        nome_infracao = st.selectbox("2️⃣ Infração:", lista_infracoes, key="infracao_select")
        if nome_infracao in cats:
            gravidade_sugerida = cats[nome_infracao]["gravidade"]
            encam_sugerido = cats[nome_infracao]["encaminhamento"]
            st.markdown("---")
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown(f"""
                **📋 Informações da Infração:**
                
                **Infração:** {nome_infracao}
                
                **Gravidade Sugerida:** {gravidade_sugerida}
                
                **Encaminhamentos:**
            """)
            for linha in encam_sugerido.split('\n'):
                if linha.strip():
                    st.write(linha)
            st.markdown('</div>', unsafe_allow_html=True)
        gravidade = st.selectbox("Gravidade:",
                                ["Leve", "Grave", "Gravíssima"],
                                index=["Leve", "Grave", "Gravíssima"].index(gravidade_sugerida) if gravidade_sugerida in ["Leve", "Grave", "Gravíssima"] else 0,
                                key="gravidade_select")
        encam = st.text_area("Encaminhamentos:",
                            value=encam_sugerido,
                            height=150,
                            key="encam_select")
        st.markdown("---")
        relato = st.text_area("📝 Relato dos Fatos", height=100, key="relato_novo", placeholder="Descreva os fatos...")
        if st.button("💾 Salvar", type="primary"):
            if prof and prof != "Selecione..." and relato and nome:
                data_str = f"{data.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}"
                if verificar_ocorrencia_duplicada(ra, nome_infracao, data_str, df_ocorrencias):
                    st.warning("⚠️ Já existe ocorrência igual para este aluno!")
                else:
                    nova = {
                        "data": data_str,
                        "aluno": nome,
                        "ra": str(ra),
                        "turma": turma_sel,
                        "categoria": nome_infracao,
                        "gravidade": gravidade,
                        "relato": relato,
                        "encaminhamento": encam,
                        "professor": prof,
                        "medidas_aplicadas": "",
                        "medidas_obs": ""
                    }
                    if salvar_ocorrencia(nova):
                        st.success("✅ Ocorrência registrada!")
                        st.session_state.ocorrencia_salva_sucesso = True
                        st.rerun()
            else:
                st.error("❌ Preencha todos os campos!")

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
# 6. IMPORTAR ALUNOS
# ============================================================================
elif menu == "📥 Importar Alunos":
    st.header("📥 Importar Alunos")
    turma_alunos = st.text_input("Turma:", placeholder="Ex: 6º Ano A")
    arquivo = st.file_uploader("CSV", type=["csv"])
    if arquivo and turma_alunos and st.button("🚀 Importar"):
        df_import = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig')
        contagem = 0
        for idx, row in df_import.iterrows():
            ra = str(row.get('ra', '')).strip()
            if ra and ra != 'nan':
                aluno = {"ra": ra, "nome": str(row.get('nome', '')).strip(), "turma": turma_alunos, "data_nascimento": "", "situacao": ""}
                if salvar_aluno(aluno):
                    contagem += 1
        st.success(f"✅ {contagem} alunos importados!")
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
# 8. LISTA DE ALUNOS (COM FOTOS - NOVIDADE v5.0)
# ============================================================================
elif menu == "👥 Lista de Alunos":
    st.header("👥 Alunos")
    if not df_alunos.empty:
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
# 10. GRÁFICOS E INDICADORES (COLORIDOS - NOVIDADE v5.0)
# ============================================================================
elif menu == "📊 Gráficos e Indicadores":
    st.header("📊 Dashboard")
    if not df_ocorrencias.empty:
        cor_leve = "#4CAF50"
        cor_grave = "#FF9800"
        cor_gravissima = "#F44336"
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Por Gravidade")
            contagem_grav = df_ocorrencias['gravidade'].value_counts()
            fig_grav = go.Figure(data=[
                go.Bar(
                    x=contagem_grav.index,
                    y=contagem_grav.values,
                    marker_color=[cor_leve if x == 'Leve' else cor_grave if x == 'Grave' else cor_gravissima for x in contagem_grav.index],
                    text=contagem_grav.values,
                    textposition='auto'
                )
            ])
            fig_grav.update_layout(
                title='Ocorrências por Gravidade',
                xaxis_title='Gravidade',
                yaxis_title='Quantidade',
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig_grav, use_container_width=True)
        with col2:
            st.subheader("Por Categoria")
            contagem_cat = df_ocorrencias['categoria'].value_counts().head(10)
            fig_cat = px.bar(
                x=contagem_cat.values,
                y=contagem_cat.index,
                orientation='h',
                color=contagem_cat.values,
                color_continuous_scale='Viridis',
                text=contagem_cat.values
            )
            fig_cat.update_layout(
                title='Top 10 Categorias',
                xaxis_title='Quantidade',
                yaxis_title='Categoria',
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        st.subheader("Distribuição por Gravidade")
        fig_pizza = px.pie(
            values=contagem_grav.values,
            names=contagem_grav.index,
            color=contagem_grav.index,
            color_discrete_map={'Leve': cor_leve, 'Grave': cor_grave, 'Gravíssima': cor_gravissima},
            hole=0.3
        )
        fig_pizza.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pizza, use_container_width=True)

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
# 12. BACKUP E RESTAURAÇÃO (NOVIDADE v5.0)
# ============================================================================
elif menu == "💾 Backup e Restauração":
    st.header("💾 Backup e Restauração de Dados")
    st.markdown("### 📥 Criar Backup")
    st.info("Cria um arquivo com todos os dados do sistema (alunos, professores, responsáveis, ocorrências)")
    if st.button("📥 Gerar Backup dos Dados"):
        backup_json = criar_backup_dados()
        if backup_json:
            st.download_button(
                label="📥 Baixar Backup JSON",
                data=backup_json,
                file_name=f"backup_conviva_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
    st.markdown("---")
    st.markdown("### 📤 Restaurar Backup")
    st.warning("⚠️ Isso irá adicionar dados do backup ao sistema atual")
    arquivo_backup = st.file_uploader("Selecione o arquivo de backup (.json)", type=["json"])
    if arquivo_backup and st.button("📤 Restaurar Backup"):
        try:
            backup_json = arquivo_backup.read().decode('utf-8')
            if restaurar_backup_dados(backup_json):
                st.success("✅ Backup restaurado com sucesso!")
                st.info("🔄 Recarregue a página para ver os dados")
            else:
                st.error("❌ Erro ao restaurar backup")
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
    st.markdown("---")
    st.markdown("### 💾 Backup do Código")
    st.info("Cria uma cópia do código fonte atual (app.py)")
    if st.button("💾 Gerar Backup do Código"):
        codigo = criar_backup_codigo()
        if codigo:
            st.download_button(
                label="📥 Baixar Código (app.py)",
                data=codigo,
                file_name=f"app_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.py",
                mime="text/x-python"
            )

# ============================================================================
# FIM DO CÓDIGO - SISTEMA CONVIVA 179 v5.0
# ============================================================================