import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from io import BytesIO
import requests
import os
from dotenv import load_dotenv
import pytz

# --- CARREGAR VARIÁVEIS DE AMBIENTE ---
load_dotenv()

# --- CONFIGURAÇÃO SUPABASE ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Conviva 179 - E.E. Profª Eliane", layout="wide", page_icon="🏫")

# --- CSS PERSONALIZADO ---
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
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-value { font-size: 2.5rem; font-weight: bold; }
    .metric-label { font-size: 1rem; opacity: 0.9; }
    </style>
""", unsafe_allow_html=True)

# --- DADOS DA ESCOLA ---
ESCOLA_NOME = "Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI"
ESCOLA_SUBTITULO = "🌟 Escola dos Sonhos"
ESCOLA_ENDERECO = "R. VALTER DE SOUZA COSTA, 147 - JARDIM PRIMAVERA - FERRAZ DE VASCONCELOS/SP"
ESCOLA_LOGO = "logo.jpg"

# --- MENU LATERAL ---
menu = st.sidebar.selectbox("Menu", [
    "🏠 Início",
    "👨‍ Cadastrar Professores",
    "👤 Cadastrar Responsáveis por Assinatura",
    "📝 Registrar Ocorrência",
    "📥 Importar Alunos",
    "📋 Gerenciar Turmas Importadas",
    "👥 Lista de Alunos",
    "📋 Histórico de Ocorrências",
    "📊 Gráficos e Indicadores",
    "🖨️ Imprimir PDF"
])

# --- CORES PARA TIPOS DE INFRAÇÃO ---
CORES_INFRACOES = {
    "Agressão Física": "#FF6B6B",
    "Agressão Verbal / Conflito Verbal": "#FFE66D",
    "Ameaça": "#FF8E72",
    "Bullying": "#4ECDC4",
    "Cyberbullying": "#45B7D1",
    "Racismo": "#9B59B6",
    "Homofobia": "#E91E63",
    "Transfobia": "#E91E63",
    "Gordofobia": "#FFA726",
    "Xenofobia": "#9B59B6",
    "Capacitismo (Discriminação por Deficiência)": "#BA68C8",
    "Misoginia / Violência de Gênero": "#E91E63",
    "Assédio Moral": "#F06292",
    "Assédio Sexual": "#C2185B",
    "Importunação Sexual / Estupro": "#880E4F",
    "Apologia ao Nazismo": "#4A148C",
    "Posse de Arma de Fogo / Simulacro": "#D32F2F",
    "Posse de Arma Branca": "#B71C1C",
    "Posse de Arma de Brinquedo": "#FFCDD2",
    "Ameaça de Ataque Ativo": "#B71C1C",
    "Ataque Ativo Concretizado": "#880E4F",
    "Invasão": "#F44336",
    "Ocupação de Unidade Escolar": "#FF5722",
    "Roubo": "#FF7043",
    "Furto": "#FFB74D",
    "Dano ao Patrimônio / Vandalismo": "#FFA726",
    "Posse de Celular / Dispositivo Eletrônico": "#4DB6AC",
    "Consumo de Álcool e Tabaco": "#81C784",
    "Consumo de Cigarro Eletrônico": "#66BB6A",
    "Consumo de Substâncias Ilícitas": "#2E7D32",
    "Comercialização de Álcool e Tabaco": "#388E3C",
    "Envolvimento com Tráfico de Drogas": "#1B5E20",
    "Indisciplina": "#64B5F6",
    "Evasão Escolar / Infrequência": "#42A5F5",
    "Sinais de Automutilação": "#5C6BC0",
    "Sinais de Isolamento Social": "#7986CB",
    "Sinais de Alterações Emocionais": "#9FA8DA",
    "Tentativa de Suicídio": "#3949AB",
    "Suicídio Concretizado": "#1A237E",
    "Mal Súbito": "#FFD54F",
    "Óbito": "#424242",
    "Crimes Cibernéticos": "#00BCD4",
    "Fake News / Disseminação de Informações Falsas": "#26C6DA",
    "Violência Doméstica / Maus Tratos": "#D81B60",
    "Vulnerabilidade Familiar / Negligência": "#EC407A",
    "Alerta de Desaparecimento": "#C2185B",
    "Sequestro": "#880E4F",
    "Homicídio / Homicídio Tentado": "#212121",
    "Feminicídio": "#880E4F",
    "Incitamento a Atos Infracionais": "#5D4037",
    "Acidentes e Eventos Inesperados": "#FFB300",
    "Atos Obscenos / Atos Libidinosos": "#F06292",
    "Uso Inadequado de Dispositivos Eletrônicos": "#4DD0E1",
    "Outros": "#9E9E9E"
}

# --- CORES POR GRAVIDADE ---
CORES_GRAVIDADE = {
    "Leve": "#4CAF50",
    "Grave": "#FF9800",
    "Gravíssima": "#F44336"
}

# --- PROTOCOLO 179 COMPLETO ---
PROTOCOLO_179 = {
    "📌 Violência e Agressão": {
        "Agressão Física": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Acionar Orientação Educacional\n✅ Notificar famílias\n✅ Conselho Tutelar (se menor de 18 anos)\n✅ B.O. (se houver lesão corporal)"
        },
        "Agressão Verbal / Conflito Verbal": {
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
        },
        "Capacitismo (Discriminação por Deficiência)": {
            "gravidade": "Grave",
            "encaminhamento": "✅ B.O. recomendado\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ AEE (Atendimento Educacional Especializado)\n✅ Diretoria de Ensino"
        },
        "Misoginia / Violência de Gênero": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚖️ CRIME (Lei Maria da Penha)\n✅ B.O. OBRIGATÓRIO\n✅ DDM (Delegacia da Mulher)\n✅ Conselho Tutelar\n✅ CREAS\n✅ Medidas protetivas"
        },
        "Assédio Moral": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Registrar em ata circunstanciada\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. recomendado\n✅ Acompanhamento psicológico"
        },
        "Assédio Sexual": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 CRIME - NÃO FAZER MEDIAÇÃO\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ DDM (se for o caso)\n✅ Afastamento do agressor\n✅ Acompanhamento psicológico da vítima"
        },
        "Importunação Sexual / Estupro": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 CRIME GRAVÍSSIMO\n✅ B.O. IMEDIATO\n✅ SAMU (se necessário)\n✅ Conselho Tutelar\n✅ IML (se for o caso)\n✅ Não confrontar o agressor\n✅ Preservar provas"
        },
        "Apologia ao Nazismo": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚖️ CRIME (Lei 7.716/89)\n✅ B.O. OBRIGATÓRIO\n✅ Conselho Tutelar\n✅ Diretoria de Ensino\n✅ Medidas disciplinares cabíveis"
        }
    },
    "🔫 Armas e Segurança": {
        "Posse de Arma de Fogo / Simulacro": {
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
        "Ataque Ativo Concretizado": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 EMERGÊNCIA MÁXIMA\n✅ PM (190) e SAMU (192)\n✅ Protocolo de Segurança Escolar\n✅ B.O. OBRIGATÓRIO\n✅ IML (se houver óbito)\n✅ Apoio psicológico emergencial"
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
        "Dano ao Patrimônio / Vandalismo": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Reparação do dano\n✅ Trabalho educativo"
        }
    },
    "💊 Drogas e Substâncias": {
        "Posse de Celular / Dispositivo Eletrônico": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Retirar dispositivo (conforme regimento)\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Devolver aos responsáveis"
        },
        "Consumo de Álcool e Tabaco": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Registrar em ata\n✅ Acompanhamento psicológico\n✅ Trabalho educativo sobre saúde"
        },
        "Consumo de Cigarro Eletrônico": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Registrar em ata\n✅ Acompanhamento psicológico\n✅ Trabalho educativo sobre saúde"
        },
        "Consumo de Substâncias Ilícitas": {
            "gravidade": "Grave",
            "encaminhamento": "✅ SAMU (192) se houver emergência\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ B.O. recomendado\n✅ CAPS/CREAS\n✅ Acompanhamento especializado"
        },
        "Comercialização de Álcool e Tabaco": {
            "gravidade": "Grave",
            "encaminhamento": "✅ B.O. recomendado\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Vigilância Sanitária\n✅ Registrar em ata"
        },
        "Envolvimento com Tráfico de Drogas": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 B.O. OBRIGATÓRIO\n✅ PM (190) se necessário\n✅ Conselho Tutelar\n✅ Não confrontar diretamente\n✅ Sigilo e segurança\n✅ Diretoria de Ensino"
        }
    },
    "🧠 Saúde Mental e Comportamento": {
        "Indisciplina": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Mediação pedagógica\n✅ Registrar em ata\n✅ Notificar famílias\n✅ Conselho de Classe\n✅ Acompanhamento pedagógico"
        },
        "Evasão Escolar / Infrequência": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Buscar ativa (visita domiciliar)\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Registrar em ata\n✅ Diretoria de Ensino\n✅ Programa de Busca Ativa"
        },
        "Sinais de Automutilação": {
            "gravidade": "Grave",
            "encaminhamento": "✅ SAMU (192) se houver risco imediato\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ CAPS Infantil/Juvenil\n✅ Acompanhamento psicológico\n✅ Rede de proteção"
        },
        "Sinais de Isolamento Social": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Acompanhamento psicológico\n✅ Notificar famílias\n✅ Orientação Educacional\n✅ Trabalho em grupo\n✅ Observação contínua"
        },
        "Sinais de Alterações Emocionais": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Acompanhamento psicológico\n✅ Notificar famílias\n✅ Orientação Educacional\n✅ Observação contínua"
        },
        "Tentativa de Suicídio": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 SAMU (192) IMEDIATO\n✅ Hospital de referência\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ CAPS\n✅ Rede de proteção\n✅ Pós-venção"
        },
        "Suicídio Concretizado": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 SAMU/PM/IML\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Diretoria de Ensino\n✅ Apoio psicológico emergencial\n✅ Pós-venção"
        },
        "Mal Súbito": {
            "gravidade": "Grave",
            "encaminhamento": "✅ SAMU (192)\n✅ Hospital de referência\n✅ Notificar famílias URGENTE\n✅ Registrar em ata\n✅ Acompanhamento"
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
        "Fake News / Disseminação de Informações Falsas": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Trabalho educativo sobre informação\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Orientação sobre consequências legais"
        },
        "Violência Doméstica / Maus Tratos": {
            "gravidade": "Gravíssima",
            "encaminhamento": "⚠️ SIGILO ABSOLUTO\n✅ Conselho Tutelar OBRIGATÓRIO\n✅ CREAS\n✅ DDM (se for o caso)\n✅ B.O.\n✅ Não confrontar agressor\n✅ Rede de proteção"
        },
        "Vulnerabilidade Familiar / Negligência": {
            "gravidade": "Grave",
            "encaminhamento": "✅ Conselho Tutelar\n✅ CREAS\n✅ Notificar famílias\n✅ CRAS\n✅ Rede de proteção social"
        },
        "Alerta de Desaparecimento": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 PM (190) IMEDIATO\n✅ Notificar famílias URGENTE\n✅ Conselho Tutelar\n✅ B.O.\n✅ Disseminar informações\n✅ Rede de busca"
        },
        "Sequestro": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 PM (190) IMEDIATO\n✅ Não negociar\n✅ Notificar famílias\n✅ B.O.\n✅ Seguir orientações policiais"
        },
        "Homicídio / Homicídio Tentado": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 PM (190) e SAMU (192)\n✅ B.O. OBRIGATÓRIO\n✅ IML (se for o caso)\n✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Pós-venção"
        },
        "Feminicídio": {
            "gravidade": "Gravíssima",
            "encaminhamento": "🚨 PM (190) e SAMU (192)\n✅ B.O. OBRIGATÓRIO\n✅ DDM\n✅ IML (se for o caso)\n✅ Notificar famílias\n✅ Conselho Tutelar"
        },
        "Incitamento a Atos Infracionais": {
            "gravidade": "Grave",
            "encaminhamento": "✅ B.O. recomendado\n✅ Conselho Tutelar\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Medidas disciplinares"
        }
    },
    "📋 Outros": {
        "Acidentes e Eventos Inesperados": {
            "gravidade": "Grave",
            "encaminhamento": "✅ SAMU (192) se necessário\n✅ Notificar famílias URGENTE\n✅ Registrar em ata\n✅ B.O. se necessário\n✅ Diretoria de Ensino"
        },
        "Atos Obscenos / Atos Libidinosos": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Notificar famílias\n✅ Conselho Tutelar\n✅ Acompanhamento psicológico\n✅ Registrar em ata\n✅ Trabalho educativo"
        },
        "Uso Inadequado de Dispositivos Eletrônicos": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Retirar dispositivo\n✅ Notificar famílias\n✅ Registrar em ata\n✅ Trabalho educativo sobre uso responsável"
        },
        "Outros": {
            "gravidade": "Leve",
            "encaminhamento": "✅ Registrar em ata\n✅ Notificar famílias\n✅ Avaliar necessidade de outros encaminhamentos\n✅ Conselho Tutelar se necessário"
        }
    }
}

# --- FUNÇÕES SUPABASE ---
@st.cache_data(ttl=60)
def carregar_alunos():
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/alunos?select=*", headers=HEADERS)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Erro ao carregar alunos: {str(e)}")
        return pd.DataFrame()

def salvar_aluno(aluno):
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/alunos", json=aluno, headers=HEADERS)
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao salvar aluno: {str(e)}")
        return False

def atualizar_aluno(ra, dados):
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra}", json=dados, headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao atualizar aluno: {str(e)}")
        return False

def excluir_alunos_por_turma(turma):
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/alunos?turma=eq.{turma}", headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao excluir turma: {str(e)}")
        return False

@st.cache_data(ttl=60)
def carregar_professores():
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/professores?select=*", headers=HEADERS)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Erro ao carregar professores: {str(e)}")
        return pd.DataFrame()

def salvar_professor(professor):
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/professores", json=professor, headers=HEADERS)
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao salvar professor: {str(e)}")
        return False

@st.cache_data(ttl=60)
def carregar_responsaveis():
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/responsaveis?select=*&ativo=eq.true", headers=HEADERS)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Erro ao carregar responsáveis: {str(e)}")
        return pd.DataFrame()

def salvar_responsavel(responsavel):
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/responsaveis", json=responsavel, headers=HEADERS)
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao salvar responsável: {str(e)}")
        return False

def atualizar_responsavel(id_resp, dados):
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}", json=dados, headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao atualizar responsável: {str(e)}")
        return False

def carregar_ocorrencias():
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/ocorrencias?select=*&order=id.desc", headers=HEADERS)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Erro ao carregar ocorrências: {str(e)}")
        return pd.DataFrame()

def salvar_ocorrencia(ocorrencia):
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/ocorrencias", json=ocorrencia, headers=HEADERS)
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Erro ao salvar ocorrência: {str(e)}")
        return False

def excluir_ocorrencia(id_ocorrencia):
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}", headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao excluir: {str(e)}")
        return False

def editar_ocorrencia(id_ocorrencia, dados):
    try:
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}", json=dados, headers=HEADERS)
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Erro ao editar: {str(e)}")
        return False

# --- VERIFICAR OCORRÊNCIA DUPLICADA ---
def verificar_ocorrencia_duplicada(ra, categoria, data_str, df_ocorrencias):
    if df_ocorrencias.empty:
        return False
    
    ocorrencias_existentes = df_ocorrencias[
        (df_ocorrencias['ra'] == ra) & 
        (df_ocorrencias['categoria'] == categoria) & 
        (df_ocorrencias['data'] == data_str)
    ]
    
    return not ocorrencias_existentes.empty

# --- OBTER GRAVIDADE MAIS ALTA ---
def obter_gravidade_mais_alta(gravidades):
    ordem = {"Leve": 1, "Grave": 2, "Gravíssima": 3}
    if not gravidades:
        return "Leve"
    max_gravidade = max(gravidades, key=lambda g: ordem.get(g, 0))
    return max_gravidade

# --- COMBINAR ENCAMINHAMENTOS ---
def combinar_encaminhamentos(encaminhamentos_lista):
    todos = []
    for encam in encaminhamentos_lista:
        for linha in encam.split('\n'):
            linha = linha.strip()
            if linha and linha not in todos:
                todos.append(linha)
    return '\n'.join(todos)

# --- FUNÇÃO PDF COM ASSINATURAS ---
def gerar_pdf_ocorrencia(ocorrencia, responsaveis):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elementos = []
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle('Titulo', parent=estilos['Heading1'], fontSize=16, alignment=1, spaceAfter=20)
    elementos.append(Paragraph("REGISTRO DE OCORRÊNCIA ESCOLAR", titulo))
    escola = ParagraphStyle('Escola', parent=estilos['Normal'], fontSize=10, alignment=1, spaceAfter=5)
    elementos.append(Paragraph(ESCOLA_NOME, escola))
    elementos.append(Paragraph(ESCOLA_ENDERECO, escola))
    elementos.append(Spacer(1, 0.5*cm))
    dados = [["Data:", ocorrencia.get("data", "")], ["Aluno:", ocorrencia.get("aluno", "")],
             ["RA:", str(ocorrencia.get("ra", ""))], ["Turma:", ocorrencia.get("turma", "")],
             ["Categoria:", ocorrencia.get("categoria", "")], ["Gravidade:", ocorrencia.get("gravidade", "")],
             ["Professor:", ocorrencia.get("professor", "")]]
    tabela_dados = Table(dados, colWidths=[4*cm, 10*cm])
    tabela_dados.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    elementos.append(tabela_dados)
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("<b>📝 Relato dos Fatos:</b>", estilos['Heading3']))
    elementos.append(Paragraph(str(ocorrencia.get("relato", "")), estilos['Normal']))
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("<b>🔀 Encaminhamentos:</b>", estilos['Heading3']))
    elementos.append(Paragraph(str(ocorrencia.get("encaminhamento", "")), estilos['Normal']))
    elementos.append(Spacer(1, 1.5*cm))
    
    # --- ASSINATURAS ---
    elementos.append(Paragraph("<b>📋 Assinaturas:</b>", estilos['Heading3']))
    elementos.append(Spacer(1, 0.5*cm))
    
    assinaturas = []
    cargos_padrao = ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)", "Professor Responsável"]
    
    for cargo in cargos_padrao:
        if cargo == "Professor Responsável":
            nome = ocorrencia.get("professor", "_____________________________")
        else:
            resp = responsaveis[responsaveis['cargo'] == cargo] if not responsaveis.empty else pd.DataFrame()
            nome = resp['nome'].values[0] if not resp.empty else "_____________________________"
        
        assinaturas.append([f"{cargo}:", nome])
    
    tabela_assinaturas = Table(assinaturas, colWidths=[5*cm, 9*cm])
    tabela_assinaturas.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    elementos.append(tabela_assinaturas)
    
    elementos.append(Spacer(1, 1*cm))
    elementos.append(Paragraph("_" * 60, estilos['Normal']))
    elementos.append(Paragraph("Documento gerado eletronicamente", estilos['Normal']))
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# --- SESSION STATE ---
if 'editando_id' not in st.session_state:
    st.session_state.editando_id = None
if 'dados_edicao' not in st.session_state:
    st.session_state.dados_edicao = None
if 'turma_para_deletar' not in st.session_state:
    st.session_state.turma_para_deletar = None
if 'turma_selecionada' not in st.session_state:
    st.session_state.turma_selecionada = None
if 'salvando_ocorrencia' not in st.session_state:
    st.session_state.salvando_ocorrencia = False
if 'ocorrencia_salva_sucesso' not in st.session_state:
    st.session_state.ocorrencia_salva_sucesso = False
if 'gravidade_alterada' not in st.session_state:
    st.session_state.gravidade_alterada = False
if 'adicionar_outra_infracao' not in st.session_state:
    st.session_state.adicionar_outra_infracao = False
if 'infracoes_adicionais' not in st.session_state:
    st.session_state.infracoes_adicionais = []

# --- CARREGAR DADOS ---
df_alunos = carregar_alunos()
df_ocorrencias = carregar_ocorrencias()
df_professores = carregar_professores()
df_responsaveis = carregar_responsaveis()

# --- 1. HOME ---
if menu == "🏠 Início":
    st.markdown(f"""
        <div class="main-header">
            <img src="https://raw.githubusercontent.com/Fr34k1981/SistemaConviva/main/logo.jpg" 
                 style="max-width: 150px; margin-bottom: 1rem;" alt="Logo da Escola">
            <div class="school-name">🏫 {ESCOLA_NOME}</div>
            <div class="school-subtitle">{ESCOLA_SUBTITULO}</div>
            <div class="school-address">📍 {ESCOLA_ENDERECO}</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("## 📋 Sistema de Gestão de Ocorrências - Protocolo 179")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total de Alunos", len(df_alunos))
    with col2: st.metric("Ocorrências Registradas", len(df_ocorrencias))
    with col3:
        graves = len(df_ocorrencias[df_ocorrencias["gravidade"] == "Gravíssima"]) if not df_ocorrencias.empty else 0
        st.metric("Ocorrências Gravíssimas", graves)
    with col4:
        profs = len(df_professores) if not df_professores.empty else 0
        st.metric("Professores Cadastrados", profs)

# --- 2. CADASTRAR PROFESSORES ---
elif menu == "👨‍ Cadastrar Professores":
    st.header("👨‍🏫 Cadastrar Professores")
    col1, col2 = st.columns(2)
    with col1:
        nome_prof = st.text_input("Nome do Professor *", placeholder="Ex: João da Silva")
        email_prof = st.text_input("E-mail (opcional)", placeholder="Ex: joao@educacao.sp.gov.br")
    with col2:
        st.info("💡 Cadastre todos os professores da escola para facilitar na hora de registrar ocorrências.")
    if st.button("💾 Salvar Professor"):
        if nome_prof:
            novo_prof = {"nome": nome_prof, "email": email_prof if email_prof else None}
            if salvar_professor(novo_prof):
                st.success(f"✅ Professor {nome_prof} cadastrado com sucesso!")
                st.rerun()
        else:
            st.error("❌ O nome do professor é obrigatório!")
    st.markdown("---")
    st.subheader("📋 Professores Cadastrados")
    if not df_professores.empty:
        st.dataframe(df_professores[['nome', 'email']], use_container_width=True)
        st.info(f"Total: {len(df_professores)} professores")
    else:
        st.write("📭 Nenhum professor cadastrado.")

# --- 3. CADASTRAR RESPONSÁVEIS POR ASSINATURA ---
elif menu == "👤 Cadastrar Responsáveis por Assinatura":
    st.header("👤 Cadastrar Responsáveis por Assinatura")
    st.info("💡 Estes nomes aparecerão automaticamente nos PDFs de ocorrência!")
    
    cargos = ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)"]
    
    for cargo in cargos:
        st.subheader(f"📋 {cargo}")
        resp = df_responsaveis[df_responsaveis['cargo'] == cargo] if not df_responsaveis.empty else pd.DataFrame()
        nome_atual = resp['nome'].values[0] if not resp.empty else ""
        id_atual = resp['id'].values[0] if not resp.empty else None
        
        col1, col2 = st.columns([3, 1])
        with col1:
            nome_resp = st.text_input(f"Nome do(a) {cargo}", value=nome_atual, key=f"resp_{cargo}")
        with col2:
            if st.button("💾 Salvar", key=f"btn_{cargo}"):
                if nome_resp:
                    if id_atual:
                        if atualizar_responsavel(id_atual, {"nome": nome_resp}):
                            st.success(f"✅ {cargo} atualizado!")
                            st.rerun()
                    else:
                        if salvar_responsavel({"cargo": cargo, "nome": nome_resp, "ativo": True}):
                            st.success(f"✅ {cargo} cadastrado!")
                            st.rerun()
                else:
                    st.error("❌ Preencha o nome!")
        st.markdown("---")
    
    st.subheader("📋 Resumo dos Responsáveis")
    if not df_responsaveis.empty:
        st.dataframe(df_responsaveis[['cargo', 'nome']], use_container_width=True)
    else:
        st.write("📭 Nenhum responsável cadastrado.")

# --- 4. REGISTRAR OCORRÊNCIA ---
elif menu == "📝 Registrar Ocorrência":
    st.header("📝 Nova Ocorrência")
    
    # Mostrar mensagem de sucesso se ocorreu
    if st.session_state.ocorrencia_salva_sucesso:
        st.markdown('<div class="success-box">✅ OCORRÊNCIA REGISTRADA COM SUCESSO!</div>', unsafe_allow_html=True)
        st.session_state.ocorrencia_salva_sucesso = False
        st.session_state.salvando_ocorrencia = False
        st.session_state.gravidade_alterada = False
        st.session_state.adicionar_outra_infracao = False
        st.session_state.infracoes_adicionais = []
    
    if df_alunos.empty:
        st.warning("⚠️ Importe alunos primeiro.")
    else:
        # HORARIO DE SAO PAULO
        tz_sp = pytz.timezone('America/Sao_Paulo')
        data_hora_sp = datetime.now(tz_sp)
        
        turmas = df_alunos["turma"].unique().tolist()
        turma_sel = st.selectbox("🏫 Turma", turmas)
        alunos = df_alunos[df_alunos["turma"] == turma_sel]
        if len(alunos) > 0:
            col1, col2 = st.columns(2)
            with col1:
                nome = st.selectbox("Aluno", alunos["nome"].tolist())
                ra = alunos[alunos["nome"] == nome]["ra"].values[0]
                if not df_professores.empty:
                    prof_lista = df_professores["nome"].tolist()
                    prof = st.selectbox("Professor 👨‍", ["Selecione..."] + prof_lista)
                    if prof == "Selecione...":
                        prof = st.text_input("Ou digite o nome do professor", placeholder="Nome do professor")
                else:
                    prof = st.text_input("Professor 👨‍", placeholder="Nome do professor")
                data = st.date_input("Data", data_hora_sp.date())
                hora = st.time_input("Hora", data_hora_sp.time())
            with col2:
                # INFRAÇÃO PRINCIPAL (DROPDOWN)
                st.subheader("📋 Infração Principal (Protocolo 179)")
                grupo = st.selectbox("Grupo", list(PROTOCOLO_179.keys()), key="grupo_principal")
                cats = PROTOCOLO_179[grupo]
                infracao_principal = st.selectbox("Ocorrência Principal", list(cats.keys()), key="infracao_principal")
                
                # Dados da infração principal
                gravidade_principal = cats[infracao_principal]["gravidade"]
                encam_principal = cats[infracao_principal]["encaminhamento"]
                
                # Tag da infração principal
                st.markdown(f'<span class="infracao-principal-tag">🎯 Principal: {infracao_principal}</span>', unsafe_allow_html=True)
                
                # PERGUNTAR SE QUER ADICIONAR OUTRA INFRAÇÃO
                st.markdown("---")
                st.subheader("➕ Infrações Adicionais (Opcional)")
                
                adicionar_outra = st.radio(
                    "Deseja adicionar outra infração relacionada?",
                    ["Não, apenas a principal", "Sim, adicionar infração adicional"],
                    key="radio_adicionar_infracao",
                    index=0
                )
                
                infracoes_adicionais = []
                if adicionar_outra == "Sim, adicionar infração adicional":
                    for i in range(4):
                        st.markdown(f"**Infração Adicional {i+1}:**")
                        grupo_add = st.selectbox(f"Grupo {i+1}", list(PROTOCOLO_179.keys()), key=f"grupo_add_{i}")
                        cats_add = PROTOCOLO_179[grupo_add]
                        infracao_add = st.selectbox(f"Ocorrência {i+1}", list(cats_add.keys()), key=f"infracao_add_{i}")
                        infracoes_adicionais.append(infracao_add)
                        
                        if i < 3:
                            adicionar_mais = st.checkbox(f"Adicionar mais uma após esta?", key=f"mais_{i}")
                            if not adicionar_mais:
                                break
                        st.markdown("---")
                
                st.session_state.infracoes_adicionais = infracoes_adicionais
                
                # CALCULAR GRAVIDADE E ENCAMINHAMENTOS TOTAIS
                todas_infracoes = [infracao_principal] + infracoes_adicionais
                gravidades = []
                encaminhamentos_lista = []
                
                for inf in todas_infracoes:
                    for grupo_nome, cats in PROTOCOLO_179.items():
                        if inf in cats:
                            gravidades.append(cats[inf]["gravidade"])
                            encaminhamentos_lista.append(cats[inf]["encaminhamento"])
                            break
                
                gravidade_protocolo = obter_gravidade_mais_alta(gravidades)
                encam_sugerido = combinar_encaminhamentos(encaminhamentos_lista)
                
                # Mostrar informações do protocolo
                st.markdown("---")
                st.info(f"""
                    **📋 Protocolo 179 - {len(todas_infracoes)} infração(ões)**
                    
                    **Infração Principal:** {infracao_principal}
                    
                    {'**Infrações Adicionais:** ' + ', '.join(infracoes_adicionais) if infracoes_adicionais else ''}
                    
                    **Gravidade (mais alta):** {gravidade_protocolo}
                    
                    **Encaminhamentos Sugeridos (combinados):**
                """)
                
                # Mostrar encaminhamentos formatados (LINHA POR LINHA)
                for linha in encam_sugerido.split('\n'):
                    if linha.strip():
                        st.write(linha)
                
                # Mostrar tags das infrações
                if todas_infracoes:
                    st.markdown("---")
                    st.markdown("**Infrações registradas:**")
                    tags_html = f'<span class="infracao-principal-tag">🎯 {infracao_principal}</span>'
                    for inf in infracoes_adicionais:
                        tags_html += f'<span class="infracao-tag">{inf}</span>'
                    st.markdown(tags_html, unsafe_allow_html=True)
                
                # Gravidade com aviso se alterar
                gravidade = st.selectbox("Gravidade", ["Leve", "Grave", "Gravíssima"],
                                        index=["Leve", "Grave", "Gravíssima"].index(gravidade_protocolo),
                                        key="gravidade_select")
                
                # Aviso se mudar a gravidade do protocolo
                if gravidade != gravidade_protocolo:
                    if not st.session_state.gravidade_alterada:
                        st.error(f"""
                            ⚠️ **ATENÇÃO:** Você está alterando a gravidade sugerida pelo Protocolo 179!
                            
                            **A gravidade oficial para estas infrações é {gravidade_protocolo}.**
                            
                            Certifique-se de que há justificativa para esta alteração.
                        """)
                        st.session_state.gravidade_alterada = True
                else:
                    st.session_state.gravidade_alterada = False
            
            st.markdown("---")
            relato = st.text_area("📝 Relato", height=100, key="relato_novo", 
                                 placeholder="Descreva os fatos de forma clara e objetiva...")
            
            # ENCAMINHAMENTO AUTOMÁTICO DO PROTOCOLO 179
            encam = st.text_area("🔀 Encaminhamento (preenchido automaticamente pelo Protocolo 179)", 
                                value=encam_sugerido, height=200, key="encam_novo")
            
            st.info(f"🤖 **Encaminhamentos sugeridos pelo Protocolo 179 foram preenchidos automaticamente acima.**")
            
            # --- MEDIDAS DISCIPLINARES (NOVO CAMPO) ---
            st.markdown("---")
            st.subheader("⚖️ Medidas Disciplinares (Protocolo 179)")

            st.info("""
                **📋 Orientações do Protocolo 179:**
                
                • Suspensão total é MEDIDA EXCEPCIONAL
                • Priorizar medidas educativas e restaurativas
                • Aluno não pode ser privado de educação
                • Envolvimento da família é essencial
            """)

            # Medidas sugeridas baseadas na gravidade
            medidas_sugeridas = {
                "Leve": [
                    "✅ Mediação de conflitos",
                    "✅ Registro em ata",
                    "✅ Notificação aos pais",
                    "✅ Atividades de reflexão",
                    "✅ Termo de compromisso"
                ],
                "Grave": [
                    "✅ Ata circunstanciada",
                    "✅ Conselho Tutelar",
                    "✅ Mudança de turma",
                    "✅ Acompanhamento psicológico",
                    "✅ Reunião com pais",
                    "⚠️ Afastamento temporário (1-3 dias)"
                ],
                "Gravíssima": [
                    "✅ B.O. obrigatório",
                    "✅ Conselho Tutelar",
                    "✅ Diretoria de Ensino",
                    "✅ Medidas protetivas",
                    "✅ Acompanhamento especializado",
                    "⚠️ Afastamento da sala (temporário)",
                    "⚠️ Transferência de escola (último recurso)"
                ]
            }

            # Mostrar medidas sugeridas
            if gravidade in medidas_sugeridas:
                st.markdown(f"**📋 Medidas Sugeridas para Gravidade {gravidade}:**")
                for medida in medidas_sugeridas[gravidade]:
                    st.write(medida)

            # Checkbox para selecionar medidas aplicadas
            st.markdown("**📝 Medidas Aplicadas (marque as que foram usadas):**")

            medidas_opcoes = [
                "Mediação de conflitos",
                "Registro em ata",
                "Notificação aos pais",
                "Atividades de reflexão",
                "Termo de compromisso",
                "Ata circunstanciada",
                "Conselho Tutelar acionado",
                "Mudança de turma",
                "Acompanhamento psicológico",
                "Reunião com pais",
                "Afastamento temporário",
                "B.O. registrado",
                "Diretoria de Ensino comunicada",
                "Medidas protetivas",
                "Transferência de escola"
            ]

            medidas_aplicadas = []
            for medida in medidas_opcoes:
                if st.checkbox(medida, key=f"medida_{medida}"):
                    medidas_aplicadas.append(medida)

            # Campo para observações sobre as medidas
            medidas_obs = st.text_area(
                "📝 Observações sobre as medidas disciplinares aplicadas",
                placeholder="Descreva detalhes das medidas, prazos, acompanhamentos...",
                height=100,
                key="medidas_obs"
            )
            
            st.info(f"🤖 **Encaminhamentos sugeridos pelo Protocolo 179 foram preenchidos automaticamente acima.**")
            
            # Botão de salvar com prevenção de múltiplos cliques
            if st.session_state.salvando_ocorrencia:
                st.button("💾 Salvando...", disabled=True, type="primary")
                st.info("⏳ Aguarde, registrando ocorrência...")
            else:
                if st.button("💾 Salvar Ocorrência", type="primary"):
                    if prof and prof != "Selecione..." and relato:
                        # Verificar duplicação
                        data_str = f"{data.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}"
                        categoria_str = infracao_principal
                        if infracoes_adicionais:
                            categoria_str += " | " + " | ".join(infracoes_adicionais)
                        
                        if verificar_ocorrencia_duplicada(ra, categoria_str, data_str, df_ocorrencias):
                            st.error(f"❌ JÁ EXISTE UMA OCORRÊNCIA IGUAL PARA ESTE ALUNO!\n\nAluno: {nome}\nCategoria: {categoria_str}\nData: {data_str}")
                        else:
                            st.session_state.salvando_ocorrencia = True
                            
                            nova = {
                                "data": data_str,
                                "aluno": nome, "ra": ra, "turma": turma_sel,
                                "categoria": categoria_str, "gravidade": gravidade,
                                "relato": relato, "encaminhamento": encam,
                                "professor": prof,
                                "medidas_aplicadas": " | ".join(medidas_aplicadas),
                                "medidas_obs": medidas_obs
                            }
                            if salvar_ocorrencia(nova):
                                st.session_state.ocorrencia_salva_sucesso = True
                                st.rerun()
                            else:
                                st.session_state.salvando_ocorrencia = False
                                st.error("❌ Erro ao salvar ocorrência. Tente novamente.")
                    else:
                        st.error("❌ Preencha professor e relato obrigatoriamente!")

# --- 5. IMPORTAR ALUNOS ---
elif menu == "📥 Importar Alunos":
    st.header("📥 Importar Alunos (CSV da SED)")
    
    turma_alunos = st.text_input("🏫 Qual a TURMA destes alunos?", placeholder="Ex: 6º Ano A")
    arquivo_upload = st.file_uploader("Selecione o arquivo CSV da SED", type=["csv"])
    
    if arquivo_upload is not None:
        try:
            df_import = pd.read_csv(arquivo_upload, sep=';', encoding='utf-8-sig')
            st.success("✅ Arquivo lido com sucesso!")
            st.info(f"📋 **Colunas encontradas:** {', '.join(df_import.columns.tolist())}")
            st.write(f"📊 **Total de linhas no arquivo:** {len(df_import)}")
            
            st.write("🔍 **Prévia dos dados (primeiras 3 linhas):**")
            st.dataframe(df_import.head(3))
            
            mapeamento = {}
            for col in df_import.columns:
                col_lower = col.lower().strip()
                if col_lower == 'ra':
                    mapeamento['ra'] = col
                elif 'nome' in col_lower:
                    mapeamento['nome'] = col
                elif 'nascimento' in col_lower or 'nasc' in col_lower:
                    mapeamento['data_nascimento'] = col
                elif 'situação' in col_lower or 'situacao' in col_lower:
                    mapeamento['situacao'] = col
            
            st.write("🔍 **Mapeamento encontrado:**")
            st.json(mapeamento)
            
            colunas_necessarias = ['ra', 'nome', 'data_nascimento', 'situacao']
            faltantes = [c for c in colunas_necessarias if c not in mapeamento]
            
            if faltantes:
                st.error(f"❌ Colunas não encontradas: {', '.join(faltantes)}")
            else:
                turmas_existentes = df_alunos['turma'].unique().tolist() if not df_alunos.empty else []
                if turma_alunos in turmas_existentes:
                    st.warning(f"⚠️ A turma **{turma_alunos}** já existe no sistema!")
                    st.info("💡 Se importar novamente, os alunos serão **atualizados** (não duplicados).")
                
                if st.button("🚀 Importar Alunos"):
                    if not turma_alunos:
                        st.error("❌ Preencha o nome da turma!")
                    else:
                        contagem_novos = 0
                        contagem_atualizados = 0
                        erros = 0
                        
                        for idx, row in df_import.iterrows():
                            try:
                                ra_valor = row[mapeamento['ra']]
                                ra_str = str(ra_valor).strip()
                                
                                if not ra_str or ra_str == 'nan':
                                    erros += 1
                                    continue
                                
                                aluno_existente = df_alunos[df_alunos['ra'] == ra_str]
                                
                                aluno = {
                                    "ra": ra_str,
                                    "nome": str(row[mapeamento['nome']]).strip(),
                                    "data_nascimento": str(row[mapeamento['data_nascimento']]).strip(),
                                    "situacao": str(row[mapeamento['situacao']]).strip(),
                                    "turma": turma_alunos
                                }
                                
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
                        st.rerun()
                
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo: {str(e)}")

# --- 6. GERENCIAR TURMAS IMPORTADAS ---
elif menu == "📋 Gerenciar Turmas Importadas":
    st.header("📋 Gerenciar Turmas Importadas")
    
    if not df_alunos.empty:
        turmas_info = df_alunos.groupby('turma').agg({
            'ra': 'count',
            'nome': 'first'
        }).reset_index()
        turmas_info.columns = ['turma', 'total_alunos', 'exemplo_nome']
        
        st.subheader("📊 Resumo das Turmas")
        
        for idx, row in turmas_info.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
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
                if st.button("🗑️ Deletar Turma", key=f"del_{row['turma']}", type="secondary"):
                    st.session_state.turma_para_deletar = row['turma']
        
        if 'turma_para_deletar' in st.session_state:
            st.warning(f"⚠️ Tem certeza que deseja deletar a turma **{st.session_state.turma_para_deletar}**?")
            st.info("Isso removerá TODOS os alunos desta turma!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Exclusão"):
                    if excluir_alunos_por_turma(st.session_state.turma_para_deletar):
                        st.success(f"✅ Turma {st.session_state.turma_para_deletar} excluída!")
                        del st.session_state.turma_para_deletar
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    del st.session_state.turma_para_deletar
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
        st.write("📭 Nenhuma turma importada.")

# --- 7. LISTA DE ALUNOS ---
elif menu == "👥 Lista de Alunos":
    st.header("👥 Alunos Cadastrados")
    if not df_alunos.empty:
        turmas = df_alunos["turma"].unique().tolist()
        filtro = st.selectbox("Filtrar por Turma", ["Todas"] + turmas)
        df_exibir = df_alunos[df_alunos["turma"] == filtro] if filtro != "Todas" else df_alunos
        st.dataframe(df_exibir, use_container_width=True)
        st.info(f"Total: {len(df_exibir)} alunos")
    else:
        st.write("📭 Nenhum aluno cadastrado.")

# --- 8. HISTÓRICO ---
elif menu == "📋 Histórico de Ocorrências":
    st.header("📋 Histórico de Ocorrências")
    if not df_ocorrencias.empty:
        st.dataframe(df_ocorrencias, use_container_width=True)
        st.markdown("---")
        st.subheader("🛠️ Ações")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🗑️ Excluir")
            ids = df_ocorrencias["id"].tolist()
            id_excluir = st.selectbox("ID para excluir", ids, key="select_excluir")
            if st.button("🗑️ Excluir", key="btn_excluir"):
                if excluir_ocorrencia(id_excluir):
                    st.success(f"✅ Ocorrência {id_excluir} excluída!")
                    st.rerun()
        with col2:
            st.markdown("### ✏️ Editar")
            id_editar = st.selectbox("ID para editar", ids, key="select_editar")
            if st.button("✏️ Carregar", key="btn_carregar"):
                occ = df_ocorrencias[df_ocorrencias["id"] == id_editar].iloc[0].to_dict()
                st.session_state.editando_id = id_editar
                st.session_state.dados_edicao = occ
                st.success(f"✅ Ocorrência {id_editar} carregada!")
        if st.session_state.editando_id is not None:
            st.markdown("---")
            st.subheader(f"✏️ Editando ID: {st.session_state.editando_id}")
            dados = st.session_state.dados_edicao
            edit_relato = st.text_area("📝 Relato", value=str(dados.get("relato", "")), height=100, key="edit_relato")
            edit_encam = st.text_area("🔀 Encaminhamento", value=str(dados.get("encaminhamento", "")), height=100, key="edit_encam")
            edit_grav = st.selectbox("Gravidade", ["Leve", "Grave", "Gravíssima"],
                                    index=["Leve", "Grave", "Gravíssima"].index(str(dados.get("gravidade", "Leve"))), key="edit_grav")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar Alterações"):
                    if editar_ocorrencia(st.session_state.editando_id,
                                        {"relato": edit_relato, "encaminhamento": edit_encam, "gravidade": edit_grav}):
                        st.session_state.editando_id = None
                        st.success("✅ Alterações salvas!")
                        st.rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    st.session_state.editando_id = None
                    st.rerun()
    else:
        st.write("📭 Nenhuma ocorrência.")

# --- 9. GRÁFICOS E INDICADORES AVANÇADOS ---
elif menu == "📊 Gráficos e Indicadores":
    st.header("📊 Dashboard de Ocorrências - Protocolo 179")
    
    if df_ocorrencias.empty:
        st.warning("⚠️ Nenhuma ocorrência registrada ainda.")
    else:
        # --- FILTROS AVANÇADOS ---
        st.subheader("🔍 Filtros Avançados")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filtro_periodo = st.selectbox("📅 Período", 
                                         ["Todos", "Hoje", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Este ano", "Personalizado"])
        
        with col2:
            turmas_disponiveis = ["Todas"] + df_ocorrencias['turma'].unique().tolist()
            filtro_turma = st.selectbox("🏫 Turma", turmas_disponiveis)
        
        with col3:
            gravidades_disponiveis = ["Todas"] + df_ocorrencias['gravidade'].unique().tolist()
            filtro_gravidade = st.selectbox("⚖️ Gravidade", gravidades_disponiveis)
        
        with col4:
            todas_infracoes = []
            for cat in df_ocorrencias['categoria'].unique():
                todas_infracoes.extend(cat.split(' | '))
            infracoes_unicas = list(set([i.strip() for i in todas_infracoes]))
            infracoes_disponiveis = ["Todas"] + sorted(infracoes_unicas)
            filtro_infracao = st.selectbox("📋 Infração", infracoes_disponiveis)
        
        if filtro_periodo == "Personalizado":
            col_data1, col_data2 = st.columns(2)
            with col_data1:
                data_inicio = st.date_input("Data Início", value=datetime.now() - timedelta(days=30))
            with col_data2:
                data_fim = st.date_input("Data Fim", value=datetime.now())
        
        # --- APLICAR FILTROS ---
        df_filtrado = df_ocorrencias.copy()
        
        if filtro_periodo == "Hoje":
            hoje = datetime.now().strftime('%d/%m/%Y')
            df_filtrado = df_filtrado[df_filtrado['data'].str.contains(hoje)]
        elif filtro_periodo == "Últimos 7 dias":
            data_limite = datetime.now() - timedelta(days=7)
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[df_filtrado['data_dt'] >= data_limite]
        elif filtro_periodo == "Últimos 30 dias":
            data_limite = datetime.now() - timedelta(days=30)
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[df_filtrado['data_dt'] >= data_limite]
        elif filtro_periodo == "Este mês":
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[(df_filtrado['data_dt'].dt.month == mes_atual) & (df_filtrado['data_dt'].dt.year == ano_atual)]
        elif filtro_periodo == "Este ano":
            ano_atual = datetime.now().year
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[df_filtrado['data_dt'].dt.year == ano_atual]
        elif filtro_periodo == "Personalizado":
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado = df_filtrado[(df_filtrado['data_dt'] >= pd.Timestamp(data_inicio)) & 
                                      (df_filtrado['data_dt'] <= pd.Timestamp(data_fim) + pd.Timedelta(days=1))]
        
        if filtro_turma != "Todas":
            df_filtrado = df_filtrado[df_filtrado['turma'] == filtro_turma]
        
        if filtro_gravidade != "Todas":
            df_filtrado = df_filtrado[df_filtrado['gravidade'] == filtro_gravidade]
        
        if filtro_infracao != "Todas":
            df_filtrado = df_filtrado[df_filtrado['categoria'].str.contains(filtro_infracao, na=False)]
        
        # --- INDICADORES PRINCIPAIS ---
        st.subheader("📈 Indicadores Principais")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total_ocorrencias = len(df_filtrado)
        total_graves = len(df_filtrado[df_filtrado['gravidade'] == 'Gravíssima'])
        total_grave = len(df_filtrado[df_filtrado['gravidade'] == 'Grave'])
        total_leve = len(df_filtrado[df_filtrado['gravidade'] == 'Leve'])
        turmas_afetadas = df_filtrado['turma'].nunique()
        
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_ocorrencias}</div>
                    <div class="metric-label">Total de Ocorrências</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, #F44336 0%, #D32F2F 100%);">
                    <div class="metric-value">{total_graves}</div>
                    <div class="metric-label">Gravíssimas</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);">
                    <div class="metric-value">{total_grave}</div>
                    <div class="metric-label">Graves</div>
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
        
        # --- GRÁFICOS ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Ocorrências por Categoria")
            
            if not df_filtrado.empty:
                todas_cats = []
                for cat in df_filtrado['categoria']:
                    todas_cats.extend([c.strip() for c in cat.split('|')])
                
                df_cats = pd.DataFrame({'Categoria': todas_cats})
                contagem_cats = df_cats['Categoria'].value_counts().head(10)
                
                st.bar_chart(contagem_cats)
        
        with col2:
            st.subheader("⚖️ Ocorrências por Gravidade")
            
            if not df_filtrado.empty:
                contagem_grav = df_filtrado['gravidade'].value_counts()
                st.bar_chart(contagem_grav)
        
        st.markdown("---")
        
        # --- GRÁFICO DE LINHA (EVOLUÇÃO TEMPORAL) ---
        st.subheader("📈 Evolução Temporal das Ocorrências")
        
        if not df_filtrado.empty:
            df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado['data_apenas'] = df_filtrado['data_dt'].dt.date
            
            evolucao = df_filtrado.groupby('data_apenas').size().reset_index(name='Quantidade')
            evolucao = evolucao.sort_values('data_apenas')
            
            st.line_chart(evolucao.set_index('data_apenas'))
        
        # --- TOP TURMAS ---
        st.subheader("🏫 Top 10 Turmas com Mais Ocorrências")
        
        if not df_filtrado.empty:
            top_turmas = df_filtrado['turma'].value_counts().head(10)
            st.bar_chart(top_turmas)
        
        # --- TABELA DE DADOS FILTRADOS ---
        st.subheader("📋 Dados Filtrados")
        
        if not df_filtrado.empty:
            st.dataframe(df_filtrado[['data', 'aluno', 'turma', 'categoria', 'gravidade', 'professor']], 
                        use_container_width=True)
            
            csv = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button(
                label="📥 Baixar Dados Filtrados (CSV)",
                data=csv,
                file_name=f"ocorrencias_filtradas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

# --- 10. PDF ---
elif menu == "🖨️ Imprimir PDF":
    st.header("🖨️ Gerar PDF de Ocorrência")
    if not df_ocorrencias.empty:
        lista = (df_ocorrencias["id"].astype(str) + " - " + df_ocorrencias["data"] + " - " + df_ocorrencias["aluno"]).tolist()
        occ_sel = st.selectbox("Selecione", lista)
        idx = lista.index(occ_sel)
        occ = df_ocorrencias.iloc[idx]
        st.info(f"**ID:** {occ['id']} | **Aluno:** {occ['aluno']} | **Data:** {occ['data']}")
        if st.button("📄 Gerar PDF"):
            pdf_buffer = gerar_pdf_ocorrencia(occ, df_responsaveis)
            st.download_button(label="📥 Baixar PDF", data=pdf_buffer,
                              file_name=f"Ocorrencia_{occ['id']}_{occ['aluno']}.pdf", mime="application/pdf")
    else:
        st.write("📭 Nenhuma ocorrência.")