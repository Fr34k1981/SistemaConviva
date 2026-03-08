
# ============================================================================
# SISTEMA CONVIVA 179 - GESTÃO DE OCORRÊNCIAS ESCOLARES
# Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI
# Versão: 6.0 FINAL COMPLETA - 2436 LINHAS
# ============================================================================
# ============================================================================
# IMPORTAÇÃO DE BIBLIOTECAS
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
from difflib import SequenceMatcher
import json
import base64
# ============================================================================
# CARREGAR VARIÁVEIS DE AMBIENTE
# ============================================================================
load_dotenv()
# ============================================================================
# CONFIGURAÇÃO SUPABASE
# ============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SENHA_EXCLUSAO = os.getenv("SENHA_EXCLUSAO", "040600")
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
 page_icon="■"
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
 border-left: 4px solid #667eea;
 margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)
# ============================================================================
# DADOS COMPLETOS DA ESCOLA
# ============================================================================
ESCOLA_NOME = "Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI"
ESCOLA_SUBTITULO = "■ Escola dos Sonhos"
ESCOLA_ENDERECO = "R. Valter Souza Costa, 147 - Jardim Primavera, Ferraz de Vasconcelos - SP"
ESCOLA_CEP = "CEP: 08535-310"
ESCOLA_TELEFONE = "Telefone: (11) 4675-1855"
ESCOLA_EMAIL = "Email: e918623@educacao.sp.gov.br"
ESCOLA_LOGO = "eliane_dantas.png"
# ============================================================================
# MENU LATERAL (12 OPÇÕES)
# ============================================================================
menu = st.sidebar.selectbox("Menu", [
 "■ Início",
 "■■■ Cadastrar Professores",
 "■ Cadastrar Responsáveis por Assinatura",
 "■ Registrar Ocorrência",
 "■ Comunicado aos Pais",
 "■ Importar Alunos",
 "■ Gerenciar Turmas Importadas",
 "■ Lista de Alunos",
 "■ Histórico de Ocorrências",
 "■ Gráficos e Indicadores",
 "■■ Imprimir PDF",
 "■ Backup de Dados"
])
# ============================================================================
# CORES PARA TIPOS DE INFRAÇÃO
# ============================================================================
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
 "Saída não autorizada": "#FF9800",
 "Ausência não justificada / Cabular aula": "#FF9800",
 "Chegar atrasado": "#FFB74D",
 "Copiar atividades / Colar em avaliações": "#FFA726",
 "Falsificar assinatura de responsáveis": "#EF5350"
}
# ============================================================================
# CORES POR GRAVIDADE
# ============================================================================
CORES_GRAVIDADE = {
 "Leve": "#4CAF50",
 "Grave": "#FF9800",
 "Gravíssima": "#F44336"
}
# ============================================================================
# ENCAMINHAMENTOS DISPONÍVEIS (PARA CHECKBOX - 4 COLUNAS)
# ============================================================================
ENCAMINHAMENTOS_OPCOES = [
 "■ Registrar em ata",
 "■ Registrar em ata circunstanciada",
 "■ Acionar Orientação Educacional",
 "■ Notificar famílias",
 "■ Conselho Tutelar",
 "■ B.O.",
 "■ B.O. OBRIGATÓRIO",
 "■ Diretoria de Ensino",
 "■ Medidas disciplinares cabíveis",
 "■ Acompanhamento psicológico",
 "■ Mediação pedagógica",
 "■ Afastamento do agressor",
 "■ Medidas protetivas",
 "■ SAMU (192)",
 "■ PM (190)",
 "■ CREAS",
 "■ CRAS",
 "■ CAPS",
 "■ AEE (Atendimento Educacional Especializado)",
 "■ Busca ativa",
 "■ Reparação do dano",
 "■ Trabalho educativo",
 "■ Reunião com pais",
 "■ Termo de compromisso",
 "■ Mudança de turma",
 "■ Transferência de escola"
]
# ============================================================================
# PROTOCOLO 179 COMPLETO
# ============================================================================
PROTOCOLO_179 = {
 "■ Violência e Agressão": {
 "Agressão Física": {
 "gravidade": "Grave",
 "encaminhamento": "■ Registrar em ata circunstanciada\n■ Acionar Orientação Educacional\n■  },
 "Agressão Verbal / Conflito Verbal": {
 "gravidade": "Leve",
 "encaminhamento": "■ Mediação pedagógica\n■ Registrar em ata\n■ Acionar Orientação Educacio },
 "Ameaça": {
 "gravidade": "Grave",
 "encaminhamento": "■ Registrar em ata circunstanciada\n■ Notificar famílias\n■ Conselho Tut },
 "Bullying": {
 "gravidade": "Leve",
 "encaminhamento": "■ Programa de Mediação de Conflitos\n■ Acompanhamento pedagógico\n■ Noti },
 "Cyberbullying": {
 "gravidade": "Grave",
 "encaminhamento": "■ Registrar em ata circunstanciada\n■ Notificar famílias\n■ Conselho Tut },
 "Racismo": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■■ CRIME INAFIANÇÁVEL (Lei 7.716/89)\n■ B.O. OBRIGATÓRIO\n■ Conselho Tut },
 "Homofobia": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■■ CRIME (equiparado ao racismo - STF)\n■ B.O. OBRIGATÓRIO\n■ Conselho T },
 "Transfobia": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■■ CRIME (equiparado ao racismo - STF)\n■ B.O. OBRIGATÓRIO\n■ Conselho T },
 "Gordofobia": {
 "gravidade": "Leve",
 "encaminhamento": "■ Mediação pedagógica\n■ Acompanhamento psicológico\n■ Notificar família },
 "Xenofobia": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■■ CRIME INAFIANÇÁVEL\n■ B.O. OBRIGATÓRIO\n■ Conselho Tutelar\n■ Notifi },
 "Capacitismo (Discriminação por Deficiência)": {
 "gravidade": "Grave",
 "encaminhamento": "■ B.O. recomendado\n■ Conselho Tutelar\n■ Notificar famílias\n■ AEE (Ate },
 "Misoginia / Violência de Gênero": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■■ CRIME (Lei Maria da Penha)\n■ B.O. OBRIGATÓRIO\n■ DDM (Delegacia da M },
 "Assédio Moral": {
 "gravidade": "Grave",
 "encaminhamento": "■ Registrar em ata circunstanciada\n■ Notificar famílias\n■ Conselho Tut },
 "Assédio Sexual": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ CRIME - NÃO FAZER MEDIAÇÃO\n■ B.O. OBRIGATÓRIO\n■ Conselho Tutelar\n■  },
 "Importunação Sexual / Estupro": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ CRIME GRAVÍSSIMO\n■ B.O. IMEDIATO\n■ SAMU (se necessário)\n■ Conselho  },
 "Apologia ao Nazismo": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■■ CRIME (Lei 7.716/89)\n■ B.O. OBRIGATÓRIO\n■ Conselho Tutelar\n■ Dire }
 },
 "■ Armas e Segurança": {
 "Posse de Arma de Fogo / Simulacro": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ EMERGÊNCIA - ACIONAR PM (190)\n■ Isolar área\n■ Não tocar no objeto\n■ },
 "Posse de Arma Branca": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ ACIONAR PM (190)\n■ Isolar área\n■ B.O. OBRIGATÓRIO\n■ Conselho Tutela },
 "Posse de Arma de Brinquedo": {
 "gravidade": "Leve",
 "encaminhamento": "■ Retirar o objeto\n■ Notificar famílias\n■ Registrar em ata\n■ Trabalho },
 "Ameaça de Ataque Ativo": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ EMERGÊNCIA MÁXIMA\n■ PM (190) e SAMU (192)\n■ Protocolo de Segurança E },
 "Ataque Ativo Concretizado": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ EMERGÊNCIA MÁXIMA\n■ PM (190) e SAMU (192)\n■ Protocolo de Segurança E },
 "Invasão": {
 "gravidade": "Grave",
 "encaminhamento": "■ PM (190) se necessário\n■ Registrar em ata\n■ Notificar famílias\n■ Co },
 "Ocupação de Unidade Escolar": {
 "gravidade": "Leve",
 "encaminhamento": "■ Dialogar com estudantes\n■ Notificar famílias\n■ Diretoria de Ensino\n },
 "Roubo": {
 "gravidade": "Grave",
 "encaminhamento": "■ B.O. recomendado\n■ Notificar famílias\n■ Conselho Tutelar\n■ Registra },
 "Furto": {
 "gravidade": "Leve",
 "encaminhamento": "■ Registrar em ata\n■ Notificar famílias\n■ Conselho Tutelar (se menor)\ },
 "Dano ao Patrimônio / Vandalismo": {
 "gravidade": "Leve",
 "encaminhamento": "■ Registrar em ata\n■ Notificar famílias\n■ Conselho Tutelar\n■ Reparaçã }
 },
 "■ Drogas e Substâncias": {
 "Posse de Celular / Dispositivo Eletrônico": {
 "gravidade": "Leve",
 "encaminhamento": "■ Retirar dispositivo (conforme regimento)\n■ Notificar famílias\n■ Regi },
 "Consumo de Álcool e Tabaco": {
 "gravidade": "Leve",
 "encaminhamento": "■ Notificar famílias\n■ Conselho Tutelar\n■ Registrar em ata\n■ Acompanh },
 "Consumo de Cigarro Eletrônico": {
 "gravidade": "Leve",
 "encaminhamento": "■ Notificar famílias\n■ Conselho Tutelar\n■ Registrar em ata\n■ Acompanh },
 "Consumo de Substâncias Ilícitas": {
 "gravidade": "Grave",
 "encaminhamento": "■ SAMU (192) se houver emergência\n■ Notificar famílias\n■ Conselho Tute },
 "Comercialização de Álcool e Tabaco": {
 "gravidade": "Grave",
 "encaminhamento": "■ B.O. recomendado\n■ Notificar famílias\n■ Conselho Tutelar\n■ Vigilânc },
 "Envolvimento com Tráfico de Drogas": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ B.O. OBRIGATÓRIO\n■ PM (190) se necessário\n■ Conselho Tutelar\n■ Não  }
 },
 "■ Saúde Mental e Comportamento": {
 "Indisciplina": {
 "gravidade": "Leve",
 "encaminhamento": "■ Mediação pedagógica\n■ Registrar em ata\n■ Notificar famílias\n■ Conse },
 "Evasão Escolar / Infrequência": {
 "gravidade": "Grave",
 "encaminhamento": "■ Buscar ativa (visita domiciliar)\n■ Notificar famílias\n■ Conselho Tut },
 "Sinais de Automutilação": {
 "gravidade": "Grave",
 "encaminhamento": "■ SAMU (192) se houver risco imediato\n■ Notificar famílias URGENTE\n■ C },
 "Sinais de Isolamento Social": {
 "gravidade": "Leve",
 "encaminhamento": "■ Acompanhamento psicológico\n■ Notificar famílias\n■ Orientação Educaci },
 "Sinais de Alterações Emocionais": {
 "gravidade": "Leve",
 "encaminhamento": "■ Acompanhamento psicológico\n■ Notificar famílias\n■ Orientação Educaci },
 "Tentativa de Suicídio": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ SAMU (192) IMEDIATO\n■ Hospital de referência\n■ Notificar famílias UR },
 "Suicídio Concretizado": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ SAMU/PM/IML\n■ Notificar famílias\n■ Conselho Tutelar\n■ Diretoria de  },
 "Mal Súbito": {
 "gravidade": "Grave",
 "encaminhamento": "■ SAMU (192)\n■ Hospital de referência\n■ Notificar famílias URGENTE\n■  },
 "Óbito": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ SAMU/PM/IML\n■ Notificar famílias\n■ Conselho Tutelar\n■ Diretoria de  }
 },
 "■ Crimes e Situações Graves": {
 "Crimes Cibernéticos": {
 "gravidade": "Grave",
 "encaminhamento": "■ B.O. (Delegacia de Crimes Digitais)\n■ Preservar provas (prints, URLs) },
 "Fake News / Disseminação de Informações Falsas": {
 "gravidade": "Leve",
 "encaminhamento": "■ Trabalho educativo sobre informação\n■ Notificar famílias\n■ Registrar },
 "Violência Doméstica / Maus Tratos": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■■ SIGILO ABSOLUTO\n■ Conselho Tutelar OBRIGATÓRIO\n■ CREAS\n■ DDM (se  },
 "Vulnerabilidade Familiar / Negligência": {
 "gravidade": "Grave",
 "encaminhamento": "■ Conselho Tutelar\n■ CREAS\n■ Notificar famílias\n■ CRAS\n■ Rede de pr
 },
 "Alerta de Desaparecimento": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ PM (190) IMEDIATO\n■ Notificar famílias URGENTE\n■ Conselho Tutelar\n■ },
 "Sequestro": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ PM (190) IMEDIATO\n■ Não negociar\n■ Notificar famílias\n■ B.O.\n■ Se },
 "Homicídio / Homicídio Tentado": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ PM (190) e SAMU (192)\n■ B.O. OBRIGATÓRIO\n■ IML (se for o caso)\n■ No },
 "Feminicídio": {
 "gravidade": "Gravíssima",
 "encaminhamento": "■ PM (190) e SAMU (192)\n■ B.O. OBRIGATÓRIO\n■ DDM\n■ IML (se for o caso },
 "Incitamento a Atos Infracionais": {
 "gravidade": "Grave",
 "encaminhamento": "■ B.O. recomendado\n■ Conselho Tutelar\n■ Notificar famílias\n■ Registra }
 },
 "■ Infrações Administrativas e Disciplinares": {
 "Acidentes e Eventos Inesperados": {
 "gravidade": "Grave",
 "encaminhamento": "■ SAMU (192) se necessário\n■ Notificar famílias URGENTE\n■ Registrar em },
 "Atos Obscenos / Atos Libidinosos": {
 "gravidade": "Leve",
 "encaminhamento": "■ Notificar famílias\n■ Conselho Tutelar\n■ Acompanhamento psicológico\n },
 "Uso Inadequado de Dispositivos Eletrônicos": {
 "gravidade": "Leve",
 "encaminhamento": "■ Retirar dispositivo\n■ Notificar famílias\n■ Registrar em ata\n■ Traba },
 "Saída não autorizada": {
 "gravidade": "Grave",
 "encaminhamento": "■ Registrar em ata\n■ Notificar famílias URGENTE\n■ Buscar o estudante\n },
 "Ausência não justificada / Cabular aula": {
 "gravidade": "Grave",
 "encaminhamento": "■ Registrar em ata\n■ Notificar famílias\n■ Buscar o estudante\n■ Consel },
 "Outros": {
 "gravidade": "Leve",
 "encaminhamento": "■ Registrar em ata\n■ Notificar famílias\n■ Avaliar necessidade de outro }
 },
 "■■ Infrações Acadêmicas e de Pontualidade": {
 "Chegar atrasado": {
 "gravidade": "Leve",
 "encaminhamento": "■ Registrar em ata\n■ Conversar com o aluno\n■ Notificar famílias (se re },
 "Copiar atividades / Colar em avaliações": {
 "gravidade": "Média",
 "encaminhamento": "■ Registrar em ata\n■ Aplicar nova avaliação\n■ Notificar famílias\n■ Or },
 "Falsificar assinatura de responsáveis": {
 "gravidade": "Grave",
 "encaminhamento": "■ Registrar em ata circunstanciada\n■ Notificar famílias URGENTE\n■ Cons }
 }
}
# ============================================================================
# FUNÇÃO DE BUSCA FUZZY
# ============================================================================
def buscar_infracao_fuzzy(busca, protocolo):
 """
 Função de busca fuzzy para encontrar infrações relacionadas ao termo buscado.

 Args:
 busca: Termo de busca do usuário
 protocolo: Dicionário do Protocolo 179

 Returns:
 Dicionário com grupos e infrações encontradas
 """
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
# ============================================================================
# FUNÇÕES SUPABASE
# ============================================================================
@st.cache_data(ttl=60)
def carregar_alunos():
 """
 Carrega todos os alunos do banco de dados Supabase.

 Returns:
 DataFrame com dados dos alunos ou DataFrame vazio em caso de erro
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
 Salva um novo aluno no banco de dados.

 Args:
 aluno: Dicionário com dados do aluno

 Returns:
 True se salvo com sucesso, False caso contrário
 """
 try:
 response = requests.post(f"{SUPABASE_URL}/rest/v1/alunos", json=aluno, headers=HEADERS)
 return response.status_code in [200, 201]
 except Exception as e:
 st.error(f"Erro ao salvar aluno: {str(e)}")
 return False
def atualizar_aluno(ra, dados):
 """
 Atualiza dados de um aluno existente.

 Args:
 ra: RA do aluno
 dados: Dicionário com dados a atualizar

 Returns:
 True se atualizado com sucesso, False caso contrário
 """
 try:
 response = requests.patch(f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra}", json=dados, headers=HEADE return response.status_code in [200, 204]
 except Exception as e:
 st.error(f"Erro ao atualizar aluno: {str(e)}")
 return False
def excluir_alunos_por_turma(turma):
 """
 Exclui todos os alunos de uma turma específica.

 Args:
 turma: Nome da turma

 Returns:
 True se excluído com sucesso, False caso contrário
 """
 try:
 response = requests.delete(f"{SUPABASE_URL}/rest/v1/alunos?turma=eq.{turma}", headers=HEADERS)
 return response.status_code in [200, 204]
 except Exception as e:
 st.error(f"Erro ao excluir turma: {str(e)}")
 return False
@st.cache_data(ttl=60)
def carregar_professores():
 """
 Carrega todos os professores do banco de dados.

 Returns:
 DataFrame com dados dos professores ou DataFrame vazio em caso de erro
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
 Salva um novo professor no banco de dados.

 Args:
 professor: Dicionário com dados do professor

 Returns:
 True se salvo com sucesso, False caso contrário
 """
 try:
 response = requests.post(f"{SUPABASE_URL}/rest/v1/professores", json=professor, headers=HEADERS) return response.status_code in [200, 201]
 except Exception as e:
 st.error(f"Erro ao salvar professor: {str(e)}")
 return False
def atualizar_professor(id_prof, dados):
 """
 Atualiza dados de um professor existente.

 Args:
 id_prof: ID do professor
 dados: Dicionário com dados a atualizar

 Returns:
 True se atualizado com sucesso, False caso contrário
 """
 try:
 response = requests.patch(f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}", json=dados, hea return response.status_code in [200, 204]
 except Exception as e:
 st.error(f"Erro ao atualizar professor: {str(e)}")
 return False
def excluir_professor(id_prof):
 """
 Exclui um professor do banco de dados.

 Args:
 id_prof: ID do professor

 Returns:
 True se excluído com sucesso, False caso contrário
 """
 try:
 response = requests.delete(f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}", headers=HEADER return response.status_code in [200, 204]
 except Exception as e:
 st.error(f"Erro ao excluir professor: {str(e)}")
 return False
@st.cache_data(ttl=60)
def carregar_responsaveis():
 """
 Carrega todos os responsáveis ativos do banco de dados.

 Returns:
 DataFrame com dados dos responsáveis ou DataFrame vazio em caso de erro
 """
 try:
 response = requests.get(f"{SUPABASE_URL}/rest/v1/responsaveis?select=*&ativo=eq.true", headers=H response.raise_for_status()
 return pd.DataFrame(response.json())
 except Exception as e:
 st.error(f"Erro ao carregar responsáveis: {str(e)}")
 return pd.DataFrame()
def salvar_responsavel(responsavel):
 """
 Salva um novo responsável no banco de dados.

 Args:
 responsavel: Dicionário com dados do responsável

 Returns:
 True se salvo com sucesso, False caso contrário
 """
 try:
 response = requests.post(f"{SUPABASE_URL}/rest/v1/responsaveis", json=responsavel, headers=HEADE return response.status_code in [200, 201]
 except Exception as e:
 st.error(f"Erro ao salvar responsável: {str(e)}")
 return False
def atualizar_responsavel(id_resp, dados):
 """
 Atualiza dados de um responsável existente.

 Args:
 id_resp: ID do responsável
 dados: Dicionário com dados a atualizar

 Returns:
 True se atualizado com sucesso, False caso contrário
 """
 try:
 response = requests.patch(f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}", json=dados, he return response.status_code in [200, 204]
 except Exception as e:
 st.error(f"Erro ao atualizar responsável: {str(e)}")
 return False
def excluir_responsavel(id_resp):
 """
 Exclui um responsável do banco de dados.

 Args:
 id_resp: ID do responsável

 Returns:
 True se excluído com sucesso, False caso contrário
 """
 try:
 response = requests.delete(f"{SUPABASE_URL}/rest/v1/responsaveis?id=eq.{id_resp}", headers=HEADE return response.status_code in [200, 204]
 except Exception as e:
 st.error(f"Erro ao excluir responsável: {str(e)}")
 return False
def carregar_ocorrencias():
 """
 Carrega todas as ocorrências do banco de dados.

 Returns:
 DataFrame com dados das ocorrências ou DataFrame vazio em caso de erro
 """
 try:
 response = requests.get(f"{SUPABASE_URL}/rest/v1/ocorrencias?select=*&order=id.desc", headers=HE response.raise_for_status()
 return pd.DataFrame(response.json())
 except Exception as e:
 st.error(f"Erro ao carregar ocorrências: {str(e)}")
 return pd.DataFrame()
def salvar_ocorrencia(ocorrencia):
 """
 Salva uma nova ocorrência no banco de dados.

 Args:
 ocorrencia: Dicionário com dados da ocorrência

 Returns:
 True se salvo com sucesso, False caso contrário
 """
 try:
 response = requests.post(f"{SUPABASE_URL}/rest/v1/ocorrencias", json=ocorrencia, headers=HEADERS return response.status_code in [200, 201]
 except Exception as e:
 st.error(f"Erro ao salvar ocorrência: {str(e)}")
 return False
def excluir_ocorrencia(id_ocorrencia):
 """
 Exclui uma ocorrência do banco de dados.

 Args:
 id_ocorrencia: ID da ocorrência

 Returns:
 True se excluído com sucesso, False caso contrário
 """
 try:
 response = requests.delete(f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}", headers= return response.status_code in [200, 204]
 except Exception as e:
 st.error(f"Erro ao excluir: {str(e)}")
 return False
def editar_ocorrencia(id_ocorrencia, dados):
 """
 Edita uma ocorrência existente.

 Args:
 id_ocorrencia: ID da ocorrência
 dados: Dicionário com dados a atualizar

 Returns:
 True se editado com sucesso, False caso contrário
 """
 try:
 response = requests.patch(f"{SUPABASE_URL}/rest/v1/ocorrencias?id=eq.{id_ocorrencia}", json=dado return response.status_code in [200, 204]
 except Exception as e:
 st.error(f"Erro ao editar: {str(e)}")
 return False
def verificar_ocorrencia_duplicada(ra, categoria, data_str, df_ocorrencias):
 """
 Verifica se já existe uma ocorrência duplicada.

 Args:
 ra: RA do aluno
 categoria: Categoria da infração
 data_str: Data da ocorrência
 df_ocorrencias: DataFrame com ocorrências

 Returns:
 True se duplicada, False caso contrário
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
 Verifica se já existe um professor com o mesmo nome.

 Args:
 nome: Nome do professor
 df_professores: DataFrame com professores
 id_atual: ID do professor sendo editado (para exclusão na verificação)

 Returns:
 True se duplicado, False caso contrário
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
# FUNÇÕES DE FOTO - PROFESSORES E ALUNOS
# ============================================================================
def associar_foto_ao_professor(id_prof, imagem_bytes):
 """
 Associa foto ao professor via base64 no Supabase.

 Args:
 id_prof: ID do professor
 imagem_bytes: Bytes da imagem

 Returns:
 True se associado com sucesso, False caso contrário
 """
 try:
 imagem_base64 = base64.b64encode(imagem_bytes).decode('utf-8')
 dados = {"foto": imagem_base64}
 response = requests.patch(f"{SUPABASE_URL}/rest/v1/professores?id=eq.{id_prof}", json=dados, hea if response.status_code in [200, 204]:
 carregar_professores.clear()
 return True
 return False
 except Exception as e:
 st.error(f"■ Erro ao associar foto: {str(e)}")
 return False
def associar_foto_ao_aluno(ra, imagem_bytes):
 """
 Associa foto ao aluno via base64 no Supabase.

 Args:
 ra: RA do aluno
 imagem_bytes: Bytes da imagem

 Returns:
 True se associado com sucesso, False caso contrário
 """
 try:
 imagem_base64 = base64.b64encode(imagem_bytes).decode('utf-8')
 dados = {"foto": imagem_base64}
 response = requests.patch(f"{SUPABASE_URL}/rest/v1/alunos?ra=eq.{ra}", json=dados, headers=HEADE if response.status_code in [200, 204]:
 carregar_alunos.clear()
 return True
 return False
 except Exception as e:
 st.error(f"■ Erro ao associar foto: {str(e)}")
 return False
def exibir_foto_professor(id_prof, df_professores):
 """
 Exibe foto do professor se existir.

 Args:
 id_prof: ID do professor
 df_professores: DataFrame com professores

 Returns:
 True se exibiu foto, False caso contrário
 """
 try:
 prof = df_professores[df_professores['id'] == id_prof]
 if prof.empty:
 st.info("■ Sem foto")
 return False
 if 'foto' not in prof.columns:
 st.warning("■■ Coluna 'foto' não existe")
 return False
 foto_base64 = prof['foto'].values[0]
 if not foto_base64 or str(foto_base64) == 'nan' or not str(foto_base64).strip():
 st.info("■ Sem foto")
 return False
 imagem_bytes = base64.b64decode(foto_base64)
 st.image(imagem_bytes, width=120, caption="■■■ Foto")
 return True
 except:
 st.info("■ Sem foto")
 return False
def exibir_foto_aluno(ra, df_alunos):
 """
 Exibe foto do aluno se existir.

 Args:
 ra: RA do aluno
 df_alunos: DataFrame com alunos

 Returns:
 True se exibiu foto, False caso contrário
 """
 try:
 aluno = df_alunos[df_alunos['ra'] == ra]
 if aluno.empty:
 st.info("■ Sem foto")
 return False
 if 'foto' not in aluno.columns:
 st.warning("■■ Coluna 'foto' não existe")
 return False
 foto_base64 = aluno['foto'].values[0]
 if not foto_base64 or str(foto_base64) == 'nan' or not str(foto_base64).strip():
 st.info("■ Sem foto")
 return False
 imagem_bytes = base64.b64decode(foto_base64)
 st.image(imagem_bytes, width=120, caption="■ Foto")
 return True
 except:
 st.info("■ Sem foto")
 return False
# ============================================================================
# FUNÇÕES DE BACKUP
# ============================================================================
def criar_backup_dados(df_alunos, df_professores, df_responsaveis, df_ocorrencias):
 """
 Cria um backup de todos os dados do sistema em formato JSON.

 Args:
 df_alunos: DataFrame com alunos
 df_professores: DataFrame com professores
 df_responsaveis: DataFrame com responsáveis
 df_ocorrencias: DataFrame com ocorrências

 Returns:
 BytesIO com o arquivo JSON do backup
 """
 try:
 backup_data = {
 "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
 "alunos": df_alunos.to_dict('records') if not df_alunos.empty else [],
 "professores": df_professores.to_dict('records') if not df_professores.empty else [],
 "responsaveis": df_responsaveis.to_dict('records') if not df_responsaveis.empty else [],
 "ocorrencias": df_ocorrencias.to_dict('records') if not df_ocorrencias.empty else []
 }

 json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
 buffer = BytesIO()
 buffer.write(json_str.encode('utf-8'))
 buffer.seek(0)
 return buffer
 except Exception as e:
 st.error(f"Erro ao criar backup: {str(e)}")
 return None
def baixar_backup_codigo():
 """
 Cria um backup do código fonte atual.

 Returns:
 BytesIO com o arquivo de código
 """
 try:
 with open(__file__, 'r', encoding='utf-8') as f:
 codigo = f.read()

 buffer = BytesIO()
 buffer.write(codigo.encode('utf-8'))
 buffer.seek(0)
 return buffer
 except Exception as e:
 st.error(f"Erro ao baixar código: {str(e)}")
 return None
# ============================================================================
# FUNÇÃO PARA GERAR PDF DE OCORRÊNCIA
# ============================================================================
def gerar_pdf_ocorrencia(ocorrencia, responsaveis):
 """
 Gera um PDF com os detalhes de uma ocorrência.

 Args:
 ocorrencia: Dicionário com dados da ocorrência
 responsaveis: DataFrame com responsáveis

 Returns:
 BytesIO com o arquivo PDF
 """
 buffer = BytesIO()
 doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bo elementos = []
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
 estilo_protocolo = ParagraphStyle('Protocolo', parent=estilos['Normal'],
 fontSize=9, alignment=2, spaceAfter=0.15*cm, textColor=colors.dar elementos.append(Paragraph(f"<b>{protocolo}</b>", estilo_protocolo))
 elementos.append(Spacer(1, 0.15*cm))

 estilo_titulo = ParagraphStyle('TituloDoc', parent=estilos['Heading1'],
 fontSize=12, alignment=1, spaceAfter=0.3*cm, textColor=colors.darkbl elementos.append(Paragraph("REGISTRO DE OCORRÊNCIA", estilo_titulo))
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
 ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
 ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
 ('FONTSIZE', (0, 0), (-1, -1), 8),
 ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
 ('TOPPADDING', (0, 0), (-1, -1), 4),
 ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F5F5F5')),
 ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
 ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
 ]))
 elementos.append(tabela_dados)
 elementos.append(Spacer(1, 0.2*cm))

 estilo_secao = ParagraphStyle('Secao', parent=estilos['Normal'],
 fontSize=9, textColor=colors.darkblue, spaceAfter=0.1*cm)
 estilo_texto = ParagraphStyle('Texto', parent=estilos['Normal'],
 fontSize=8, alignment=0, spaceAfter=0.15*cm, leading=10)

 elementos.append(Paragraph("<b>■ RELATO:</b>", estilo_secao))
 elementos.append(Paragraph(str(ocorrencia.get("relato", "")), estilo_texto))
 elementos.append(Spacer(1, 0.15*cm))

 elementos.append(Paragraph("<b>■ ENCAMINHAMENTOS:</b>", estilo_secao))
 encam_texto = str(ocorrencia.get("encaminhamento", "")).replace('\n', '<br/>')
 elementos.append(Paragraph(encam_texto, estilo_texto))
 elementos.append(Spacer(1, 0.5*cm))

 elementos.append(Paragraph("<b>ASSINATURAS:</b>", estilo_secao))
 elementos.append(Spacer(1, 0.2*cm))

 cargos = ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)", "Professor Responsável"]
 for cargo in cargos:
 if cargo == "Professor Responsável":
 nome = ocorrencia.get("professor", "")
 if nome:
 elementos.append(Paragraph(f"<b>{cargo}:</b> {nome}", estilo_texto))
 else:
 resp_cargo = responsaveis[responsaveis['cargo'] == cargo] if not responsaveis.empty else pd if not resp_cargo.empty:
 for idx, resp in resp_cargo.iterrows():
 elementos.append(Paragraph(f"<b>{cargo}:</b> {resp['nome']}", estilo_texto))

 elementos.append(Spacer(1, 0.5*cm))

 estilo_rodape = ParagraphStyle('Rodape', parent=estilos['Normal'],
 fontSize=6, alignment=1, textColor=colors.grey)
 elementos.append(Paragraph("_" * 75, estilos['Normal']))
 elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
 doc.build(elementos)
 buffer.seek(0)
 return buffer
# ============================================================================
# FUNÇÃO PARA GERAR PDF DE COMUNICADO
# ============================================================================
def gerar_pdf_comunicado(aluno_data, ocorrencia_data, medidas_aplicadas, observacoes, responsaveis):
 """
 Gera um PDF de comunicado aos pais/responsáveis.

 Args:
 aluno_data: Dicionário com dados do aluno
 ocorrencia_data: Dicionário com dados da ocorrência
 medidas_aplicadas: String com medidas aplicadas
 observacoes: String com observações
 responsaveis: DataFrame com responsáveis

 Returns:
 BytesIO com o arquivo PDF
 """
 buffer = BytesIO()
 doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bo elementos = []
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
 estilo_protocolo = ParagraphStyle('Protocolo', parent=estilos['Normal'],
 fontSize=9, alignment=2, spaceAfter=0.15*cm, textColor=colors.dar elementos.append(Paragraph(f"<b>{protocolo}</b>", estilo_protocolo))
 elementos.append(Spacer(1, 0.15*cm))

 estilo_titulo = ParagraphStyle('TituloDoc', parent=estilos['Heading1'],
 fontSize=12, alignment=1, spaceAfter=0.3*cm, textColor=colors.darkbl elementos.append(Paragraph("COMUNICADO AOS PAIS/RESPONSÁVEIS", estilo_titulo))
 elementos.append(Spacer(1, 0.2*cm))

 estilo_secao = ParagraphStyle('Secao', parent=estilos['Normal'],
 fontSize=9, textColor=colors.darkblue, spaceAfter=0.1*cm)
 estilo_texto = ParagraphStyle('Texto', parent=estilos['Normal'],
 fontSize=8, alignment=0, spaceAfter=0.15*cm, leading=10)

 elementos.append(Paragraph("<b>DADOS DO ALUNO:</b>", estilo_secao))
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
 ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
 ]))
 elementos.append(tabela_aluno)
 elementos.append(Spacer(1, 0.2*cm))

 elementos.append(Paragraph("<b>DADOS DA OCORRÊNCIA:</b>", estilo_secao))
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
 ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
 ]))
 elementos.append(tabela_ocorrencia)
 elementos.append(Spacer(1, 0.2*cm))

 elementos.append(Paragraph("<b>■ RELATO:</b>", estilo_secao))
 elementos.append(Paragraph(str(ocorrencia_data.get("relato", "")), estilo_texto))
 elementos.append(Spacer(1, 0.15*cm))
 if medidas_aplicadas:
 elementos.append(Paragraph("<b>■■ MEDIDAS:</b>", estilo_secao))
 for medida in medidas_aplicadas.split(' | '):
 if medida.strip():
 elementos.append(Paragraph(f"• {medida}", estilo_texto))
 elementos.append(Spacer(1, 0.15*cm))

 if observacoes:
 elementos.append(Paragraph("<b>■ OBSERVAÇÕES:</b>", estilo_secao))
 elementos.append(Paragraph(str(observacoes), estilo_texto))
 elementos.append(Spacer(1, 0.15*cm))

 elementos.append(Paragraph("<b>■ ENCAMINHAMENTOS:</b>", estilo_secao))
 encam = ocorrencia_data.get("encaminhamento", "")
 for linha in encam.split('\n'):
 if linha.strip():
 elementos.append(Paragraph(f"• {linha}", estilo_texto))
 elementos.append(Spacer(1, 0.5*cm))

 elementos.append(Paragraph("<b>CIÊNCIA DOS PAIS:</b>", estilo_secao))
 elementos.append(Spacer(1, 0.2*cm))
 elementos.append(Paragraph("Declaro ciência deste comunicado.", estilo_texto))
 elementos.append(Spacer(1, 1*cm))
 elementos.append(Paragraph("_" * 40, estilos['Normal']))
 elementos.append(Paragraph("Assinatura do Responsável", ParagraphStyle('Assinatura', parent=estilos
 estilo_rodape = ParagraphStyle('Rodape', parent=estilos['Normal'],
 fontSize=6, alignment=1, textColor=colors.grey)
 elementos.append(Spacer(1, 0.5*cm))
 elementos.append(Paragraph("_" * 75, estilos['Normal']))
 elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_rodape))
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
if 'senha_exclusao_validada' not in st.session_state:
 st.session_state.senha_exclusao_validada = False
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
if menu == "■ Início":
 st.markdown(f"""
 <div class="main-header">
 <img src="https://raw.githubusercontent.com/Fr34k1981/SistemaConviva/main/logo.jpg"
 style="max-width: 150px; margin-bottom: 1rem;" alt="Logo da Escola">
 <div class="school-name">■ {ESCOLA_NOME}</div>
 <div class="school-subtitle">{ESCOLA_SUBTITULO}</div>
 <div class="school-address">■ {ESCOLA_ENDERECO}</div>
 <div class="school-contact">
 {ESCOLA_CEP} • {ESCOLA_TELEFONE} • {ESCOLA_EMAIL}
 </div>
 </div>
 """, unsafe_allow_html=True)

 st.markdown("## ■ Sistema de Gestão de Ocorrências - Protocolo 179")

 col1, col2, col3, col4 = st.columns(4)
 with col1:
 st.metric("Total de Alunos", len(df_alunos))
 with col2:
 st.metric("Ocorrências Registradas", len(df_ocorrencias))
 with col3:
 graves = len(df_ocorrencias[df_ocorrencias["gravidade"] == "Gravíssima"]) if not df_ocorrencias st.metric("Ocorrências Gravíssimas", graves)
 with col4:
 profs = len(df_professores) if not df_professores.empty else 0
 st.metric("Professores Cadastrados", profs)
# ============================================================================
# 2. CADASTRAR PROFESSORES (COM FOTO + ORDEM ALFABÉTICA)
# ============================================================================
elif menu == "■■■ Cadastrar Professores":
 st.header("■■■ Cadastrar Professores")

 with st.expander("■ Importar Professores em Massa", expanded=False):
 st.info("■ Cole uma lista de nomes de professores (um por linha)")
 texto_professores = st.text_area("Cole os nomes dos professores aqui:",
 height=150, placeholder="Alnei Maria De Moura Nogueira\nAna Pa
 if st.button("■ Importar Professores"):
 if texto_professores:
 nomes = [nome.strip() for nome in texto_professores.split('\n') if nome.strip()]
 contagem = 0
 duplicados = 0

 for nome_prof in nomes:
 if verificar_professor_duplicado(nome_prof, df_professores):
 duplicados += 1
 else:
 novo_prof = {"nome": nome_prof, "email": None}
 if salvar_professor(novo_prof):
 contagem += 1

 if contagem > 0:
 st.success(f"■ {contagem} professores importados com sucesso!")
 if duplicados > 0:
 st.warning(f"■■ {duplicados} professores já existiam (ignorado)")
 if contagem > 0 or duplicados > 0:
 st.rerun()
 else:
 st.error("■ Cole os nomes dos professores!")

 st.markdown("---")

 if st.session_state.editando_prof:
 st.subheader("✏■ Editar Professor")
 prof_edit = df_professores[df_professores['id'] == st.session_state.editando_prof].iloc[0]
 nome_prof = st.text_input("Nome do Professor *", value=prof_edit['nome'], key="edit_nome_prof")
 email_prof = st.text_input("E-mail (opcional)", value=prof_edit.get('email', ''), key="edit_emai
 # ■ UPLOAD DE FOTO DO PROFESSOR
 st.markdown("**■ Foto do Professor:**")
 foto_upload = st.file_uploader(
 "Enviar foto",
 type=["png", "jpg", "jpeg"],
 key=f"foto_prof_{st.session_state.editando_prof}"
 )
 if foto_upload:
 if associar_foto_ao_professor(st.session_state.editando_prof, foto_upload.read()):
 st.success("■ Foto associada com sucesso!")
 st.rerun()

 col1, col2 = st.columns(2)
 with col1:
 if st.button("■ Salvar Alterações", type="primary"):
 if nome_prof:
 if verificar_professor_duplicado(nome_prof, df_professores, st.session_state.editand
 st.error("■ Já existe um professor com este nome cadastrado!")
 else:
 if atualizar_professor(st.session_state.editando_prof, {"nome": nome_prof, "emai st.success("■ Professor atualizado com sucesso!")
 st.session_state.editando_prof = None
 st.rerun()
 with col2:
 if st.button("■ Cancelar"):
 st.session_state.editando_prof = None
 st.rerun()
 else:
 col1, col2 = st.columns(2)
 with col1:
 nome_prof = st.text_input("Nome do Professor *", placeholder="Ex: João da Silva", key="novo_ email_prof = st.text_input("E-mail (opcional)", placeholder="Ex: joao@educacao.sp.gov.br", k with col2:
 st.info("■ Cadastre todos os professores da escola.")

 if st.button("■ Salvar Professor", type="primary"):
 if nome_prof:
 if verificar_professor_duplicado(nome_prof, df_professores):
 st.error("■ Já existe um professor com este nome cadastrado!")
 else:
 novo_prof = {"nome": nome_prof, "email": email_prof if email_prof else None}
 if salvar_professor(novo_prof):
 st.success(f"■ Professor {nome_prof} cadastrado com sucesso!")
 st.rerun()
 else:
 st.error("■ Nome é obrigatório!")

 st.markdown("---")
 st.subheader("■ Professores Cadastrados")

 if not df_professores.empty:
 # ■ ORDENAR PROFESSORES ALFABETICAMENTE
 df_professores_ordenados = df_professores.sort_values('nome').reset_index(drop=True)

 for idx, prof in df_professores_ordenados.iterrows():
 col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
 with col1:
 # Exibir foto do professor
 exibir_foto_professor(prof['id'], df_professores)
 with col2:
 st.markdown(f"**{prof['nome']}**" + (f" - {prof['email']}" if prof.get('email') else "") with col3:
 if st.button("✏■ Editar", key=f"edit_prof_{prof['id']}"):
 st.session_state.editando_prof = prof['id']
 st.rerun()
 with col4:
 if st.button("■■ Excluir", key=f"del_prof_{prof['id']}"):
 if excluir_professor(prof['id']):
 st.success("■ Professor excluído com sucesso!")
 st.rerun()
 st.info(f"Total: {len(df_professores)} professores")
 else:
 st.write("■ Nenhum professor cadastrado.")
# ============================================================================
# 3. CADASTRAR RESPONSÁVEIS
# ============================================================================
elif menu == "■ Cadastrar Responsáveis por Assinatura":
 st.header("■ Cadastrar Responsáveis por Assinatura")
 st.info("■ Pode haver múltiplos responsáveis por cargo (ex: 2 Vice-Diretoras)")

 if st.session_state.editando_resp:
 st.subheader("✏■ Editar Responsável")
 resp_edit = df_responsaveis[df_responsaveis['id'] == st.session_state.editando_resp].iloc[0]
 cargo_edit = resp_edit['cargo']
 nome_resp = st.text_input("Nome", value=resp_edit['nome'], key="edit_nome_resp")

 col1, col2 = st.columns(2)
 with col1:
 if st.button("■ Salvar Alterações", type="primary"):
 if nome_resp:
 if atualizar_responsavel(st.session_state.editando_resp, {"nome": nome_resp}):
 st.success("■ Responsável atualizado com sucesso!")
 st.session_state.editando_resp = None
 st.rerun()
 with col2:
 if st.button("■ Cancelar"):
 st.session_state.editando_resp = None
 st.rerun()
 else:
 st.subheader("■ Novo Responsável")
 cargos = ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)"]
 cargo = st.selectbox("Cargo", cargos, key="novo_cargo")
 nome_resp = st.text_input("Nome do Responsável *", placeholder="Ex: Maria Silva", key="novo_nome
 if st.button("■ Cadastrar", type="primary"):
 if nome_resp:
 if salvar_responsavel({"cargo": cargo, "nome": nome_resp, "ativo": True}):
 st.success(f"■ {cargo} cadastrado com sucesso!")
 st.rerun()
 else:
 st.error("■ Nome é obrigatório!")

 st.markdown("---")
 st.subheader("■ Responsáveis Cadastrados")

 if not df_responsaveis.empty:
 for cargo in ["Diretor(a)", "Vice-Diretor(a)", "CGPG / Coordenador(a)"]:
 resp_cargo = df_responsaveis[df_responsaveis['cargo'] == cargo]
 if not resp_cargo.empty:
 st.markdown(f"**■ {cargo}:**")
 for idx, resp in resp_cargo.iterrows():
 col1, col2, col3 = st.columns([4, 1, 1])
 with col1:
 st.markdown(f"• {resp['nome']}")
 with col2:
 if st.button("✏■", key=f"edit_resp_{resp['id']}"):
 st.session_state.editando_resp = resp['id']
 st.rerun()
 with col3:
 if st.button("■■", key=f"del_resp_{resp['id']}"):
 if excluir_responsavel(resp['id']):
 st.success("■ Excluído com sucesso!")
 st.rerun()
 st.markdown("")
 else:
 st.write("■ Nenhum responsável cadastrado.")
# ============================================================================
# 4. REGISTRAR OCORRÊNCIA (COM 4 COLUNAS PARA ENCAMINHAMENTOS - VISUAL MELHORADO)
# ============================================================================
elif menu == "■ Registrar Ocorrência":
 st.header("■ Nova Ocorrência")

 if st.session_state.ocorrencia_salva_sucesso:
 st.markdown('<div class="success-box">■ OCORRÊNCIA(S) REGISTRADA(S) COM SUCESSO!</div>', unsafe_ st.session_state.ocorrencia_salva_sucesso = False
 st.session_state.salvando_ocorrencia = False
 st.session_state.gravidade_alterada = False
 st.session_state.adicionar_outra_infracao = False
 st.session_state.infracoes_adicionais = []

 if df_alunos.empty:
 st.warning("■■ Importe alunos primeiro.")
 else:
 tz_sp = pytz.timezone('America/Sao_Paulo')
 data_hora_sp = datetime.now(tz_sp)

 turmas = df_alunos["turma"].unique().tolist()
 turma_sel = st.selectbox("■ Turma", turmas)

 alunos = df_alunos[df_alunos["turma"] == turma_sel]

 if len(alunos) > 0:
 col1, col2 = st.columns(2)

 with col1:
 st.markdown("### ■ Selecionar Estudante(s)")
 st.info("■ Selecione um ou mais estudantes envolvidos na mesma ocorrência")

 modo_multiplo = st.checkbox("■ Registrar para múltiplos estudantes", key="modo_multiplo
 if modo_multiplo:
 alunos_selecionados = st.multiselect(
 "Selecione os estudantes:",
 alunos["nome"].tolist(),
 key="alunos_multiplos"
 )
 else:
 aluno_unico = st.selectbox("Aluno", alunos["nome"].tolist(), key="aluno_unico")
 alunos_selecionados = [aluno_unico] if aluno_unico else []

 if not df_professores.empty:
 prof_lista = df_professores["nome"].tolist()
 prof = st.selectbox("Professor ■■■", ["Selecione..."] + prof_lista)
 if prof == "Selecione...":
 prof = st.text_input("Ou digite o nome do professor", placeholder="Nome do profe else:
 prof = st.text_input("Professor ■■■", placeholder="Nome do professor")

 # ■ DATA E HORA EDITÁVEIS
 data = st.date_input("■ Data do Fato", value=data_hora_sp.date(), key="data_fato")
 hora = st.time_input("■ Hora do Fato", value=data_hora_sp.time(), key="hora_fato")

 with col2:
 st.subheader("■ Infração Principal (Protocolo 179)")
 st.markdown('<div class="search-box">', unsafe_allow_html=True)

 busca_infracao = st.text_input("■ Buscar infração (busca inteligente):",
 placeholder="Ex: celular, bullying, atraso, colar...",
 key="busca_infracao")

 if busca_infracao:
 grupos_filtrados = buscar_infracao_fuzzy(busca_infracao, PROTOCOLO_179)
 if grupos_filtrados:
 total_encontradas = sum(len(v) for v in grupos_filtrados.values())
 st.success(f"■ Encontradas {total_encontradas} infração(ões) relacionadas")
 grupo = st.selectbox("Grupo", list(grupos_filtrados.keys()), key="grupo_principa cats = grupos_filtrados[grupo]
 else:
 st.warning("■■ Nenhuma infração encontrada. Mostrando todas...")
 grupo = st.selectbox("Grupo", list(PROTOCOLO_179.keys()), key="grupo_principal") cats = PROTOCOLO_179[grupo]
 else:
 grupo = st.selectbox("Grupo", list(PROTOCOLO_179.keys()), key="grupo_principal")
 cats = PROTOCOLO_179[grupo]

 st.markdown('</div>', unsafe_allow_html=True)

 infracao_principal = st.selectbox("Ocorrência Principal", list(cats.keys()), key="infrac
 if infracao_principal in cats:
 gravidade_protocolo = cats[infracao_principal]["gravidade"]
 encam_protocolo = cats[infracao_principal]["encaminhamento"]
 else:
 gravidade_protocolo = "Leve"
 encam_protocolo = "■ Registrar em ata\n■ Notificar famílias"

 st.markdown(f'<span class="infracao-principal-tag">■ {infracao_principal}</span>', unsa
 st.markdown("---")
 cor_gravidade = CORES_GRAVIDADE.get(gravidade_protocolo, "#9E9E9E")
 st.markdown(f"""
 <div style="background:#fff3cd;border:2px solid #ffc107;border-radius:8px;padding:1rem;m <b>■ Protocolo 179 - Preenchimento Automático</b><br><br>
 <b>Infração:</b> {infracao_principal}<br>
 <b>Gravidade sugerida:</b> <span style="color:{cor_gravidade};font-weight:bold">{gra <b>Encaminhamentos sugeridos:</b>
 </div>
 """, unsafe_allow_html=True)

 for linha in encam_protocolo.split('\n'):
 if linha.strip():
 st.write(linha)

 # ■ GRAVIDADE COMEÇA VAZIA
 gravidade_opcoes = ["Selecione...", "Leve", "Grave", "Gravíssima"]
 gravidade = st.selectbox("Gravidade (obrigatório selecionar)", gravidade_opcoes, index=0
 if gravidade != "Selecione..." and gravidade != gravidade_protocolo:
 st.warning(f"■■ Você alterou a gravidade de **{gravidade_protocolo}** para **{gravi
 # ■ ENCAMINHAMENTOS EM CHECKBOX - 4 COLUNAS COM VISUAL MELHORADO (ALINHADO À ESQUERDA)
 st.markdown("### ■ Encaminhamentos (selecione os aplicáveis)")
 encaminhamentos_selecionados = []
 encam_sugeridos_lista = [e.strip() for e in encam_protocolo.split('\n') if e.strip()]

 # ■ Container com borda para melhor visual (ALINHADO À ESQUERDA)
 with st.container():
 st.markdown('<div class="encam-container">', unsafe_allow_html=True)
 # ■ 4 COLUNAS PARA MELHOR VISUALIZAÇÃO
 cols = st.columns(4)
 for i, encam_opcao in enumerate(ENCAMINHAMENTOS_OPCOES):
 col_idx = i % 4
 marcado = encam_opcao in encam_sugeridos_lista
 if cols[col_idx].checkbox(encam_opcao, value=marcado, key=f"encam_{i}"):
 encaminhamentos_selecionados.append(encam_opcao)

 st.markdown('</div>', unsafe_allow_html=True)

 encam = '\n'.join(encaminhamentos_selecionados) if encaminhamentos_selecionados else ""

 st.markdown("---")

 relato = st.text_area("■ Relato dos Fatos", height=100, key="relato_novo",
 placeholder="Descreva os fatos de forma clara e objetiva...")

 if st.session_state.salvando_ocorrencia:
 st.button("■ Salvando...", disabled=True, type="primary")
 st.info("■ Aguarde, registrando ocorrência(s)...")
 else:
 if st.button("■ Salvar Ocorrência(s)", type="primary"):
 if prof and prof != "Selecione..." and relato and alunos_selecionados and gravidade  data_str = f"{data.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}"
 categoria_str = infracao_principal
 contagem_salvas = 0
 contagem_duplicadas = 0
 erros = 0

 for nome_aluno in alunos_selecionados:
 ra_aluno = alunos[alunos["nome"] == nome_aluno]["ra"].values[0]

 if verificar_ocorrencia_duplicada(ra_aluno, categoria_str, data_str, df_ocor contagem_duplicadas += 1
 else:
 nova = {
 "data": data_str,
 "aluno": nome_aluno,
 "ra": ra_aluno,
 "turma": turma_sel,
 "categoria": categoria_str,
 "gravidade": gravidade,
 "relato": relato,
 "encaminhamento": encam,
 "professor": prof,
 "medidas_aplicadas": "",
 "medidas_obs": ""
 }
 if salvar_ocorrencia(nova):
 contagem_salvas += 1
 else:
 erros += 1

 if contagem_salvas > 0:
 st.success(f"■ {contagem_salvas} ocorrência(s) registrada(s) com sucesso!")
 if contagem_duplicadas > 0:
 st.warning(f"■■ {contagem_duplicadas} ocorrência(s) já existiam (ignorado)" if erros > 0:
 st.error(f"■ {erros} erro(s) ao salvar")

 if contagem_salvas > 0:
 st.session_state.ocorrencia_salva_sucesso = True
 st.rerun()
 else:
 if not alunos_selecionados:
 st.error("■ Selecione pelo menos um estudante!")
 elif gravidade == "Selecione...":
 st.error("■ Selecione a gravidade!")
 else:
 st.error("■ Preencha professor e relato obrigatoriamente!")
# ============================================================================
# 5. COMUNICADO AOS PAIS
# ============================================================================
elif menu == "■ Comunicado aos Pais":
 st.header("■ Comunicado aos Pais/Responsáveis")
 st.info("■ Gere um comunicado simples para envio aos pais com as medidas aplicadas.")

 if df_alunos.empty or df_ocorrencias.empty:
 st.warning("■■ Cadastre alunos e ocorrências primeiro.")
 else:
 st.subheader("■ Selecionar Aluno")
 busca = st.text_input("■ Buscar por nome ou RA", placeholder="Digite nome ou RA do aluno")

 if busca:
 df_filtrado = df_alunos[
 (df_alunos['nome'].str.contains(busca, case=False, na=False)) |
 (df_alunos['ra'].astype(str).str.contains(busca, na=False))
 ]
 else:
 df_filtrado = df_alunos

 if not df_filtrado.empty:
 aluno_sel = st.selectbox("Selecione o Aluno", df_filtrado['nome'].tolist(), key="comunicado_ aluno_info = df_alunos[df_alunos['nome'] == aluno_sel].iloc[0]
 ra_aluno = aluno_info['ra']
 turma_aluno = aluno_info['turma']

 # Exibir foto do aluno
 exibir_foto_aluno(ra_aluno, df_alunos)

 ocorrencias_aluno = df_ocorrencias[df_ocorrencias['ra'] == ra_aluno] if not df_ocorrencias.e total_ocorrencias = len(ocorrencias_aluno)

 st.markdown(f"""
 <div class="card">
 <b>■ Resumo do Aluno:</b><br>
 • Nome: {aluno_info['nome']}<br>
 • RA: {ra_aluno}<br>
 • Turma: {turma_aluno}<br>
 • ■ Total de Ocorrências: <b>{total_ocorrencias}</b>
 </div>
 """, unsafe_allow_html=True)

 if not ocorrencias_aluno.empty:
 st.subheader("■ Selecionar Ocorrência para Comunicado")
 ocorrencias_lista = (ocorrencias_aluno['id'].astype(str) + " - " +
 ocorrencias_aluno['data'] + " - " +
 ocorrencias_aluno['categoria']).tolist()
 occ_sel = st.selectbox("Selecione a ocorrência", ocorrencias_lista)
 idx = ocorrencias_lista.index(occ_sel)
 occ_info = ocorrencias_aluno.iloc[idx]

 st.markdown(f"""
 <div class="protocolo-info">
 <b>■ Dados da Ocorrência:</b><br>
 • Data: {occ_info['data']}<br>
 • Categoria: {occ_info['categoria']}<br>
 • Gravidade: {occ_info['gravidade']}<br>
 • Professor: {occ_info['professor']}
 </div>
 """, unsafe_allow_html=True)

 st.subheader("■■ Medidas Aplicadas")
 medidas_opcoes = [
 "Mediação de conflitos", "Registro em ata", "Notificação aos pais",
 "Atividades de reflexão", "Termo de compromisso", "Ata circunstanciada",
 "Conselho Tutelar", "Mudança de turma", "Acomp. psicológico",
 "Reunião com pais", "Afastamento temporário", "B.O. registrado",
 "Diretoria de Ensino", "Medidas protetivas", "Transferência de escola"
 ]

 cols = st.columns(3)
 medidas_aplicadas = []
 for i, medida in enumerate(medidas_opcoes):
 col_idx = i % 3
 with cols[col_idx]:
 if st.checkbox(medida, key=f"medida_comm_{medida}"):
 medidas_aplicadas.append(medida)

 observacoes = st.text_area("■ Observações adicionais",
 placeholder="Descreva detalhes das medidas, prazos, acompanh height=80, key="obs_comunicado")

 if st.button("■■ Gerar Comunicado para os Pais", type="primary"):
 aluno_data_dict = {
 "nome": aluno_info['nome'],
 "ra": ra_aluno,
 "turma": turma_aluno,
 "total_ocorrencias": total_ocorrencias
 }
 ocorrencia_data_dict = {
 "data": occ_info['data'],
 "categoria": occ_info['categoria'],
 "gravidade": occ_info['gravidade'],
 "professor": occ_info['professor'],
 "relato": occ_info['relato'],
 "encaminhamento": occ_info['encaminhamento']
 }
 medidas_str = " | ".join(medidas_aplicadas)

 pdf_buffer = gerar_pdf_comunicado(aluno_data_dict, ocorrencia_data_dict, medidas_str
 st.download_button(
 label="■ Baixar Comunicado (PDF)",
 data=pdf_buffer,
 file_name=f"Comunicado_{ra_aluno}_{datetime.now().strftime('%Y%m%d')}.pdf",
 mime="application/pdf"
 )
 st.success("■ Comunicado gerado! Imprima e envie com o aluno para assinatura dos pa else:
 st.info("■■ Este aluno ainda não tem ocorrências registradas.")
 else:
 st.warning("■■ Nenhum aluno encontrado com esta busca.")
# ============================================================================
# 6. IMPORTAR ALUNOS
# ============================================================================
elif menu == "■ Importar Alunos":
 st.header("■ Importar Alunos (CSV da SED)")

 turma_alunos = st.text_input("■ Qual a TURMA destes alunos?", placeholder="Ex: 6º Ano A")
 arquivo_upload = st.file_uploader("Selecione o arquivo CSV da SED", type=["csv"])

 if arquivo_upload is not None:
 try:
 df_import = pd.read_csv(arquivo_upload, sep=';', encoding='utf-8-sig')
 st.success("■ Arquivo lido com sucesso!")
 st.info(f"■ **Colunas encontradas:** {', '.join(df_import.columns.tolist())}")
 st.write(f"■ **Total de linhas no arquivo:** {len(df_import)}")
 st.write("■ **Prévia dos dados (primeiras 3 linhas):**")
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

 st.write("■ **Mapeamento encontrado:**")
 st.json(mapeamento)

 colunas_necessarias = ['ra', 'nome', 'data_nascimento', 'situacao']
 faltantes = [c for c in colunas_necessarias if c not in mapeamento]

 if faltantes:
 st.error(f"■ Colunas não encontradas: {', '.join(faltantes)}")
 else:
 turmas_existentes = df_alunos['turma'].unique().tolist() if not df_alunos.empty else []

 if turma_alunos in turmas_existentes:
 st.warning(f"■■ A turma **{turma_alunos}** já existe no sistema!")
 st.info("■ Se importar novamente, os alunos serão **atualizados** (não duplicados).
 if st.button("■ Importar Alunos"):
 if not turma_alunos:
 st.error("■ Preencha o nome da turma!")
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

 st.success(f"■ **Importação concluída!**")
 st.info(f"■ **Novos alunos:** {contagem_novos}")
 st.info(f"■ **Atualizados:** {contagem_atualizados}")
 if erros > 0:
 st.warning(f"■■ **Erros:** {erros}")
 st.rerun()
 except Exception as e:
 st.error(f"■ Erro ao ler arquivo: {str(e)}")
# ============================================================================
# 7. GERENCIAR TURMAS
# ============================================================================
elif menu == "■ Gerenciar Turmas Importadas":
 st.header("■ Gerenciar Turmas Importadas")

 if not df_alunos.empty:
 turmas_info = df_alunos.groupby('turma').agg({'ra': 'count', 'nome': 'first'}).reset_index()
 turmas_info.columns = ['turma', 'total_alunos', 'exemplo_nome']

 st.subheader("■ Resumo das Turmas")

 for idx, row in turmas_info.iterrows():
 col1, col2, col3 = st.columns([3, 1, 1])
 with col1:
 st.markdown(f"""
 <div class="card">
 <div class="card-title">■ {row['turma']}</div>
 <div class="card-value">{row['total_alunos']} alunos</div>
 </div>
 """, unsafe_allow_html=True)
 with col2:
 if st.button("■■ Ver", key=f"ver_{row['turma']}"):
 st.session_state.turma_selecionada = row['turma']
 with col3:
 if st.button("■■ Deletar Turma", key=f"del_{row['turma']}", type="secondary"):
 st.session_state.turma_para_deletar = row['turma']

 if 'turma_para_deletar' in st.session_state:
 st.warning(f"■■ Tem certeza que deseja deletar a turma **{st.session_state.turma_para_delet st.info("Isso removerá TODOS os alunos desta turma!")

 col1, col2 = st.columns(2)
 with col1:
 if st.button("■ Confirmar Exclusão"):
 if excluir_alunos_por_turma(st.session_state.turma_para_deletar):
 st.success(f"■ Turma {st.session_state.turma_para_deletar} excluída!")
 del st.session_state.turma_para_deletar
 st.rerun()
 with col2:
 if st.button("■ Cancelar"):
 del st.session_state.turma_para_deletar
 st.rerun()

 if 'turma_selecionada' in st.session_state:
 st.markdown("---")
 st.subheader(f"■ Alunos da Turma: {st.session_state.turma_selecionada}")
 alunos_turma = df_alunos[df_alunos['turma'] == st.session_state.turma_selecionada]
 st.dataframe(alunos_turma[['ra', 'nome', 'situacao']], use_container_width=True)

 if st.button("■ Fechar Visualização"):
 del st.session_state.turma_selecionada
 st.rerun()

 st.markdown("---")
 st.info(f"■ **Total de turmas:** {len(turmas_info)} | **Total de alunos:** {len(df_alunos)}")
 else:
 st.write("■ Nenhuma turma importada.")
# ============================================================================
# 8. LISTA DE ALUNOS (COM FOTOS)
# ============================================================================
elif menu == "■ Lista de Alunos":
 st.header("■ Alunos Cadastrados")

 if not df_alunos.empty:
 turmas = df_alunos["turma"].unique().tolist()
 filtro = st.selectbox("Filtrar por Turma", ["Todas"] + turmas)

 df_exibir = df_alunos[df_alunos["turma"] == filtro] if filtro != "Todas" else df_alunos

 # ■ EXIBIR COM FOTOS
 for idx, aluno in df_exibir.iterrows():
 col1, col2, col3 = st.columns([1, 3, 2])
 with col1:
 exibir_foto_aluno(aluno['ra'], df_alunos)
 with col2:
 st.markdown(f"**{aluno['nome']}**")
 st.write(f"RA: {aluno['ra']} | Turma: {aluno['turma']}")
 with col3:
 # Upload de foto para este aluno
 foto_upload = st.file_uploader(
 "■ Foto",
 type=["png", "jpg", "jpeg"],
 key=f"foto_aluno_{aluno['ra']}"
 )
 if foto_upload:
 if associar_foto_ao_aluno(aluno['ra'], foto_upload.read()):
 st.success("■")
 st.rerun()

 st.info(f"Total: {len(df_exibir)} alunos")
 else:
 st.write("■ Nenhum aluno cadastrado.")
# ============================================================================
# 9. HISTÓRICO DE OCORRÊNCIAS
# ============================================================================
elif menu == "■ Histórico de Ocorrências":
 st.header("■ Histórico de Ocorrências")

 if not df_ocorrencias.empty:
 st.dataframe(df_ocorrencias, use_container_width=True)

 st.markdown("---")
 st.subheader("■■ Ações")

 col1, col2 = st.columns(2)

 with col1:
 st.markdown("### ■■ Excluir")
 ids = df_ocorrencias["id"].tolist()
 id_excluir = st.selectbox("ID para excluir", ids, key="select_excluir")

 senha = st.text_input("■ Digite a senha para excluir:", type="password", key="senha_excluir
 if st.button("■■ Excluir", key="btn_excluir"):
 if senha == SENHA_EXCLUSAO:
 if excluir_ocorrencia(id_excluir):
 st.success(f"■ Ocorrência {id_excluir} excluída!")
 st.session_state.senha_exclusao_validada = False
 st.rerun()
 else:
 st.error("■ Senha incorreta!")

 with col2:
 st.markdown("### ✏■ Editar")
 id_editar = st.selectbox("ID para editar", ids, key="select_editar")

 if st.button("✏■ Carregar", key="btn_carregar"):
 occ = df_ocorrencias[df_ocorrencias["id"] == id_editar].iloc[0].to_dict()
 st.session_state.editando_id = id_editar
 st.session_state.dados_edicao = occ
 st.success(f"■ Ocorrência {id_editar} carregada!")

 if st.session_state.editando_id is not None:
 st.markdown("---")
 st.subheader(f"✏■ Editando ID: {st.session_state.editando_id}")
 dados = st.session_state.dados_edicao

 edit_relato = st.text_area("■ Relato", value=str(dados.get("relato", "")), height=100, key= edit_encam = st.text_area("■ Encaminhamento", value=str(dados.get("encaminhamento", "")), h edit_grav = st.selectbox("Gravidade", ["Leve", "Grave", "Gravíssima"],
 index=["Leve", "Grave", "Gravíssima"].index(str(dados.get("gravida
 col1, col2 = st.columns(2)
 with col1:
 if st.button("■ Salvar Alterações"):
 if editar_ocorrencia(st.session_state.editando_id,
 {"relato": edit_relato, "encaminhamento": edit_encam, "gravida st.session_state.editando_id = None
 st.success("■ Alterações salvas!")
 st.rerun()
 with col2:
 if st.button("■ Cancelar"):
 st.session_state.editando_id = None
 st.rerun()
 else:
 st.write("■ Nenhuma ocorrência.")
# ============================================================================
# 10. GRÁFICOS E INDICADORES (COLORIDOS)
# ============================================================================
elif menu == "■ Gráficos e Indicadores":
 st.header("■ Dashboard de Ocorrências - Protocolo 179")

 if df_ocorrencias.empty:
 st.warning("■■ Nenhuma ocorrência registrada ainda.")
 else:
 st.subheader("■ Filtros Avançados")

 col1, col2, col3, col4 = st.columns(4)

 with col1:
 filtro_periodo = st.selectbox("■ Período", ["Todos", "Hoje", "Últimos 7 dias", "Últimos 30 
 with col2:
 turmas_disponiveis = ["Todas"] + df_ocorrencias['turma'].unique().tolist()
 filtro_turma = st.selectbox("■ Turma", turmas_disponiveis)

 with col3:
 gravidades_disponiveis = ["Todas"] + df_ocorrencias['gravidade'].unique().tolist()
 filtro_gravidade = st.selectbox("■■ Gravidade", gravidades_disponiveis)

 with col4:
 todas_infracoes = []
 for cat in df_ocorrencias['categoria'].unique():
 todas_infracoes.extend(cat.split(' | '))
 infracoes_unicas = list(set([i.strip() for i in todas_infracoes]))
 infracoes_disponiveis = ["Todas"] + sorted(infracoes_unicas)
 filtro_infracao = st.selectbox("■ Infração", infracoes_disponiveis)

 if filtro_periodo == "Personalizado":
 col_data1, col_data2 = st.columns(2)
 with col_data1:
 data_inicio = st.date_input("Data Início", value=datetime.now() - timedelta(days=30))
 with col_data2:
 data_fim = st.date_input("Data Fim", value=datetime.now())

 df_filtrado = df_ocorrencias.copy()

 if filtro_periodo == "Hoje":
 hoje = datetime.now().strftime('%d/%m/%Y')
 df_filtrado = df_filtrado[df_filtrado['data'].str.contains(hoje)]
 elif filtro_periodo == "Últimos 7 dias":
 data_limite = datetime.now() - timedelta(days=7)
 df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors
 df_filtrado = df_filtrado[df_filtrado['data_dt'] >= data_limite]
 elif filtro_periodo == "Últimos 30 dias":
 data_limite = datetime.now() - timedelta(days=30)
 df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors df_filtrado = df_filtrado[df_filtrado['data_dt'] >= data_limite]
 elif filtro_periodo == "Este mês":
 mes_atual = datetime.now().month
 ano_atual = datetime.now().year
 df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors df_filtrado = df_filtrado[(df_filtrado['data_dt'].dt.month == mes_atual) & (df_filtrado['dat elif filtro_periodo == "Este ano":
 ano_atual = datetime.now().year
 df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors df_filtrado = df_filtrado[df_filtrado['data_dt'].dt.year == ano_atual]
 elif filtro_periodo == "Personalizado":
 df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors df_filtrado = df_filtrado[(df_filtrado['data_dt'] >= pd.Timestamp(data_inicio)) &
 (df_filtrado['data_dt'] <= pd.Timestamp(data_fim) + pd.Timedelta
 if filtro_turma != "Todas":
 df_filtrado = df_filtrado[df_filtrado['turma'] == filtro_turma]
 if filtro_gravidade != "Todas":
 df_filtrado = df_filtrado[df_filtrado['gravidade'] == filtro_gravidade]
 if filtro_infracao != "Todas":
 df_filtrado = df_filtrado[df_filtrado['categoria'].str.contains(filtro_infracao, na=False)]

 st.subheader("■ Indicadores Principais")

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
 <div class="metric-card" style="background: linear-gradient(135deg, #F44336 0%, #D32F2F 100% <div class="metric-value">{total_graves}</div>
 <div class="metric-label">Gravíssimas</div>
 </div>
 """, unsafe_allow_html=True)

 with col3:
 st.markdown(f"""
 <div class="metric-card" style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100% <div class="metric-value">{total_grave}</div>
 <div class="metric-label">Graves</div>
 </div>
 """, unsafe_allow_html=True)

 with col4:
 st.markdown(f"""
 <div class="metric-card" style="background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100% <div class="metric-value">{total_leve}</div>
 <div class="metric-label">Leves</div>
 </div>
 """, unsafe_allow_html=True)

 with col5:
 st.markdown(f"""
 <div class="metric-card" style="background: linear-gradient(135deg, #2196F3 0%, #1976D2 100% <div class="metric-value">{turmas_afetadas}</div>
 <div class="metric-label">Turmas Afetadas</div>
 </div>
 """, unsafe_allow_html=True)

 st.markdown("---")

 col1, col2 = st.columns(2)

 with col1:
 st.subheader("■ Ocorrências por Categoria (COLORIDO)")
 if not df_filtrado.empty:
 todas_cats = []
 for cat in df_filtrado['categoria']:
 todas_cats.extend([c.strip() for c in cat.split('|')])
 df_cats = pd.DataFrame({'Categoria': todas_cats})
 contagem_cats = df_cats['Categoria'].value_counts().head(10)

 fig_barras = px.bar(
 contagem_cats,
 x=contagem_cats.index,
 y='count',
 title='Top 10 Categorias',
 color=contagem_cats.index,
 color_discrete_sequence=px.colors.qualitative.Set3,
 labels={'count': 'Quantidade', 'Categoria': 'Categoria'}
 )
 fig_barras.update_layout(showlegend=False, xaxis_tickangle=-45)
 st.plotly_chart(fig_barras, use_container_width=True)

 with col2:
 st.subheader("■ Ocorrências por Categoria (PIZZA)")
 if not df_filtrado.empty:
 fig_pizza = px.pie(
 contagem_cats,
 values='count',
 names=contagem_cats.index,
 title='Distribuição por Categoria (%)',
 color_discrete_sequence=px.colors.qualitative.Set3,
 hole=0.3
 )
 fig_pizza.update_traces(textposition='inside', textinfo='percent+label')
 st.plotly_chart(fig_pizza, use_container_width=True)

 st.markdown("---")

 col1, col2 = st.columns(2)

 with col1:
 st.subheader("■■ Ocorrências por Gravidade (COLORIDO)")
 if not df_filtrado.empty:
 contagem_grav = df_filtrado['gravidade'].value_counts()

 fig_grav = px.bar(
 contagem_grav,
 x=contagem_grav.index,
 y=contagem_grav.values,
 title='Por Gravidade',
 color=contagem_grav.index,
 color_discrete_map={'Leve': '#4CAF50', 'Grave': '#FF9800', 'Gravíssima': '#F44336'}, labels={'y': 'Quantidade', 'x': 'Gravidade'}
 )
 fig_grav.update_layout(showlegend=False)
 st.plotly_chart(fig_grav, use_container_width=True)

 with col2:
 st.subheader("■ Ocorrências por Gravidade (PIZZA)")
 if not df_filtrado.empty:
 fig_pizza_grav = px.pie(
 values=contagem_grav.values,
 names=contagem_grav.index,
 title='Distribuição por Gravidade (%)',
 color_discrete_map={'Leve': '#4CAF50', 'Grave': '#FF9800', 'Gravíssima': '#F44336'}, hole=0.3
 )
 fig_pizza_grav.update_traces(textposition='inside', textinfo='percent+label')
 st.plotly_chart(fig_pizza_grav, use_container_width=True)

 st.markdown("---")

 st.subheader("■ Evolução Temporal das Ocorrências")
 if not df_filtrado.empty:
 df_filtrado['data_dt'] = pd.to_datetime(df_filtrado['data'], format='%d/%m/%Y %H:%M', errors df_filtrado['data_apenas'] = df_filtrado['data_dt'].dt.date
 evolucao = df_filtrado.groupby('data_apenas').size().reset_index(name='Quantidade')
 evolucao = evolucao.sort_values('data_apenas')

 fig_evolucao = px.line(
 evolucao,
 x='data_apenas',
 y='Quantidade',
 title='Evolução Temporal',
 markers=True
 )
 fig_evolucao.update_traces(line=dict(color='#667eea', width=3), marker=dict(size=8))
 st.plotly_chart(fig_evolucao, use_container_width=True)

 st.subheader("■ Top 10 Turmas com Mais Ocorrências (COLORIDO)")
 if not df_filtrado.empty:
 top_turmas = df_filtrado['turma'].value_counts().head(10)

 fig_turmas = px.bar(
 top_turmas,
 x=top_turmas.index,
 y=top_turmas.values,
 title='Top 10 Turmas',
 color=top_turmas.values,
 color_continuous_scale='Viridis',
 labels={'y': 'Quantidade', 'x': 'Turma'}
 )
 fig_turmas.update_layout(showlegend=False, xaxis_tickangle=-45)
 st.plotly_chart(fig_turmas, use_container_width=True)

 st.subheader("■ Dados Filtrados")
 if not df_filtrado.empty:
 st.dataframe(df_filtrado[['data', 'aluno', 'turma', 'categoria', 'gravidade', 'professor']],
 csv = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig')
 st.download_button(
 label="■ Baixar Dados Filtrados (CSV)",
 data=csv,
 file_name=f"ocorrencias_filtradas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
 mime="text/csv"
 )
# ============================================================================
# 11. IMPRIMIR PDF
# ============================================================================
elif menu == "■■ Imprimir PDF":
 st.header("■■ Gerar PDF de Ocorrência")

 if not df_ocorrencias.empty:
 lista = (df_ocorrencias["id"].astype(str) + " - " + df_ocorrencias["data"] + " - " + df_ocorrenc occ_sel = st.selectbox("Selecione", lista)
 idx = lista.index(occ_sel)
 occ = df_ocorrencias.iloc[idx]

 st.info(f"**ID:** {occ['id']} | **Aluno:** {occ['aluno']} | **Data:** {occ['data']}")

 if st.button("■ Gerar PDF"):
 pdf_buffer = gerar_pdf_ocorrencia(occ, df_responsaveis)
 st.download_button(
 label="■ Baixar PDF",
 data=pdf_buffer,
 file_name=f"Ocorrencia_{occ['id']}_{occ['aluno']}.pdf",
 mime="application/pdf"
 )
 else:
 st.write("■ Nenhuma ocorrência.")
# ============================================================================
# 12. BACKUP DE DADOS
# ============================================================================
elif menu == "■ Backup de Dados":
 st.header("■ Backup e Restauração de Dados")

 st.info("■ Faça backup regular dos dados do sistema para evitar perda de informações.")

 st.subheader("■ Download de Backup")

 col1, col2 = st.columns(2)

 with col1:
 st.markdown("### Backup de Dados (JSON)")
 st.write("Baixe todos os dados do sistema em formato JSON.")

 if st.button("■ Baixar Backup de Dados", type="primary"):
 backup_buffer = criar_backup_dados(df_alunos, df_professores, df_responsaveis, df_ocorrencia if backup_buffer:
 st.download_button(
 label="■ Download Backup",
 data=backup_buffer,
 file_name=f"backup_sistema_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
 mime="application/json"
 )
 st.success("■ Backup gerado com sucesso!")

 with col2:
 st.markdown("### Backup do Código Fonte")
 st.write("Baixe o código fonte atual do sistema.")

 if st.button("■ Baixar Código Fonte", type="secondary"):
 codigo_buffer = baixar_backup_codigo()
 if codigo_buffer:
 st.download_button(
 label="■ Download Código",
 data=codigo_buffer,
 file_name=f"codigo_sistema_{datetime.now().strftime('%Y%m%d_%H%M')}.py",
 mime="text/x-python"
 )
 st.success("■ Código baixado com sucesso!")

 st.markdown("---")

 st.subheader("■ Restaurar Backup")
 st.warning("■■ Atenção: Restaurar um backup irá sobrescrever os dados atuais!")

 arquivo_backup = st.file_uploader("Selecione o arquivo de backup JSON", type=["json"])

 if arquivo_backup is not None:
 try:
 backup_data = json.load(arquivo_backup)
 st.success("■ Arquivo de backup lido com sucesso!")

 st.write(f"**Timestamp do Backup:** {backup_data.get('timestamp', 'N/A')}")
 st.write(f"**Alunos:** {len(backup_data.get('alunos', []))}")
 st.write(f"**Professores:** {len(backup_data.get('professores', []))}")
 st.write(f"**Responsáveis:** {len(backup_data.get('responsaveis', []))}")
 st.write(f"**Ocorrências:** {len(backup_data.get('ocorrencias', []))}")

 if st.button("■ Restaurar Dados", type="primary"):
 st.warning("■■ Esta ação não pode ser desfeita! Confirme que deseja restaurar.")
 st.info("■ Para restauração completa, contate o administrador do sistema.")
 st.write("Os dados do backup estão prontos para importação manual se necessário.")
 except Exception as e:
 st.error(f"■ Erro ao ler arquivo de backup: {str(e)}")

 st.markdown("---")
 st.subheader("■ Informações de Backup")
 st.write("""
 - **Frequência Recomendada:** Semanal
 - **Formato:** JSON
 - **Armazenamento:** Guarde em local seguro (Google Drive, OneDrive, etc.)
 - **Criptografia:** Os dados não são criptografados no backup
 """)
# ============================================================================
# FIM DO CÓDIGO - SISTEMA CONVIVA 179 v6.0
# ============================================================================