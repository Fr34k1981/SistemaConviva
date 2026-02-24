import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from io import BytesIO
import requests
import os
from dotenv import load_dotenv

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
    </style>
""", unsafe_allow_html=True)

# --- DADOS DA ESCOLA ---
ESCOLA_NOME = "Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI"
ESCOLA_SUBTITULO = "🌟 Escola dos Sonhos"
ESCOLA_ENDERECO = "R. VALTER DE SOUZA COSTA, 147 - JARDIM PRIMAVERA - FERRAZ DE VASCONCELOS/SP"
ESCOLA_LOGO = "logo.jpg"  # ← NOME DO ARQUIVO DA LOGO

# --- MENU LATERAL ---
menu = st.sidebar.selectbox("Menu", [
    "🏠 Início",
    "👨‍ Cadastrar Professores",
    "📝 Registrar Ocorrência",
    "📥 Importar Alunos",
    "📋 Gerenciar Turmas Importadas",
    "👥 Lista de Alunos",
    "📋 Histórico de Ocorrências",
    "📊 Gráficos e Indicadores",
    "🖨️ Imprimir PDF"
])

# --- CATEGORIAS DO PROTOCOLO 179 ---
CATEGORIAS_PROTOCOLO = {
    "📌 Violência e Agressão": {
        "Agressão Física": "Grave", "Agressão Verbal / Conflito Verbal": "Leve",
        "Ameaça": "Grave", "Bullying": "Leve", "Cyberbullying": "Grave",
        "Racismo": "Gravíssima", "Homofobia": "Gravíssima", "Transfobia": "Gravíssima",
        "Gordofobia": "Leve", "Xenofobia": "Gravíssima",
        "Capacitismo (Discriminação por Deficiência)": "Grave",
        "Misoginia / Violência de Gênero": "Gravíssima",
        "Assédio Moral": "Grave", "Assédio Sexual": "Gravíssima",
        "Importunação Sexual / Estupro": "Gravíssima", "Apologia ao Nazismo": "Gravíssima"
    },
    "🔫 Armas e Segurança": {
        "Posse de Arma de Fogo / Simulacro": "Gravíssima",
        "Posse de Arma Branca": "Gravíssima", "Posse de Arma de Brinquedo": "Leve",
        "Ameaça de Ataque Ativo": "Gravíssima", "Ataque Ativo Concretizado": "Gravíssima",
        "Invasão": "Grave", "Ocupação de Unidade Escolar": "Leve",
        "Roubo": "Grave", "Furto": "Leve", "Dano ao Patrimônio / Vandalismo": "Leve"
    },
    "💊 Drogas e Substâncias": {
        "Posse de Celular / Dispositivo Eletrônico": "Leve",
        "Consumo de Álcool e Tabaco": "Leve", "Consumo de Cigarro Eletrônico": "Leve",
        "Consumo de Substâncias Ilícitas": "Grave",
        "Comercialização de Álcool e Tabaco": "Grave",
        "Envolvimento com Tráfico de Drogas": "Gravíssima"
    },
    "🧠 Saúde Mental e Comportamento": {
        "Indisciplina": "Leve", "Evasão Escolar / Infrequência": "Grave",
        "Sinais de Automutilação": "Grave", "Sinais de Isolamento Social": "Leve",
        "Sinais de Alterações Emocionais": "Leve",
        "Tentativa de Suicídio": "Gravíssima", "Suicídio Concretizado": "Gravíssima",
        "Mal Súbito": "Grave", "Óbito": "Gravíssima"
    },
    "🌐 Crimes e Situações Graves": {
        "Crimes Cibernéticos": "Grave",
        "Fake News / Disseminação de Informações Falsas": "Leve",
        "Violência Doméstica / Maus Tratos": "Gravíssima",
        "Vulnerabilidade Familiar / Negligência": "Grave",
        "Alerta de Desaparecimento": "Gravíssima", "Sequestro": "Gravíssima",
        "Homicídio / Homicídio Tentado": "Gravíssima", "Feminicídio": "Gravíssima",
        "Incitamento a Atos Infracionais": "Grave"
    },
    "📋 Outros": {
        "Acidentes e Eventos Inesperados": "Grave",
        "Atos Obscenos / Atos Libidinosos": "Leve",
        "Uso Inadequado de Dispositivos Eletrônicos": "Leve", "Outros": "Leve"
    }
}

# --- FLUXO DE AÇÕES ---
FLUXO_ACOES = {
    "Agressão Física": "⚠️ Registrar B.O. se grave. Acionar Conselho Tutelar.",
    "Racismo": "⚖️ CRIME INAFIANÇÁVEL. Registrar B.O. obrigatório.",
    "Homofobia": "⚖️ CRIME (equiparado ao racismo). Registrar B.O.",
    "Transfobia": "⚖️ CRIME (equiparado ao racismo). Registrar B.O.",
    "Assédio Sexual": "🚨 CRIME. NÃO fazer mediação. Registrar B.O.",
    "Importunação Sexual / Estupro": "🚨 CRIME GRAVÍSSIMO. Registrar B.O. imediatamente.",
    "Posse de Arma de Fogo / Simulacro": "🚨 EMERGÊNCIA. Acionar PM (190).",
    "Ataque Ativo Concretizado": "🚨 EMERGÊNCIA MÁXIMA. Acionar PM (190) e SAMU.",
    "Tentativa de Suicídio": "🚨 EMERGÊNCIA. SAMU (192). Conselho Tutelar.",
    "Suicídio Concretizado": "🚨 GRAVÍSSIMO. PM/SAMU/IML. Pós-venção.",
    "Violência Doméstica / Maus Tratos": "⚠️ SIGILO. Conselho Tutelar. CREAS/DDM.",
    "Indisciplina": "✅ Mediação pedagógica. Registrar em ata.",
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

# --- FUNÇÃO PDF ---
def gerar_pdf_ocorrencia(ocorrencia):
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
    elementos.append(Spacer(1, 2*cm))
    elementos.append(Paragraph("_" * 30, estilos['Normal']))
    elementos.append(Paragraph("Assinatura do Responsável", estilos['Normal']))
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

# --- CARREGAR DADOS ---
df_alunos = carregar_alunos()
df_ocorrencias = carregar_ocorrencias()
df_professores = carregar_professores()

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

# --- 3. IMPORTAR ALUNOS ---
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

# --- 4. GERENCIAR TURMAS IMPORTADAS ---
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

# --- 5. LISTA DE ALUNOS ---
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

# --- 6. REGISTRAR OCORRÊNCIA ---
elif menu == "📝 Registrar Ocorrência":
    st.header("📝 Nova Ocorrência")
    if df_alunos.empty:
        st.warning("⚠️ Importe alunos primeiro.")
    else:
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
                    prof = st.selectbox("Professor 👨‍🏫", ["Selecione..."] + prof_lista)
                    if prof == "Selecione...":
                        prof = st.text_input("Ou digite o nome do professor", placeholder="Nome do professor")
                else:
                    prof = st.text_input("Professor 👨‍", placeholder="Nome do professor")
                data = st.date_input("Data", datetime.now())
                hora = st.time_input("Hora", datetime.now().time())
            with col2:
                grupo = st.selectbox("Grupo", list(CATEGORIAS_PROTOCOLO.keys()))
                cats = CATEGORIAS_PROTOCOLO[grupo]
                cat = st.selectbox("Ocorrência", list(cats.keys()))
                grav_sugerida = cats[cat]
                grav = st.selectbox("Gravidade", ["Leve", "Grave", "Gravíssima"],
                                   index=["Leve", "Grave", "Gravíssima"].index(grav_sugerida))
            st.markdown("---")
            relato = st.text_area("📝 Relato", height=100, key="relato_novo")
            encam = st.text_area("🔀 Encaminhamento", height=100, key="encam_novo")
            st.info(f"🤖 **Ação:** {FLUXO_ACOES.get(cat, 'Padrão')}")
            if st.button("💾 Salvar"):
                if prof and prof != "Selecione..." and relato:
                    nova = {
                        "data": f"{data.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}",
                        "aluno": nome, "ra": ra, "turma": turma_sel,
                        "categoria": cat, "gravidade": grav,
                        "relato": relato, "encaminhamento": encam,
                        "professor": prof
                    }
                    if salvar_ocorrencia(nova):
                        st.success("✅ Salvo!")
                        st.rerun()
                else:
                    st.error("Preencha professor e relato.")

# --- 7. HISTÓRICO ---
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

# --- 8. GRÁFICOS ---
elif menu == "📊 Gráficos e Indicadores":
    st.header("📊 Indicadores")
    if not df_ocorrencias.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Por Categoria")
            st.bar_chart(df_ocorrencias['categoria'].value_counts())
        with col2:
            st.subheader("Por Gravidade")
            st.bar_chart(df_ocorrencias['gravidade'].value_counts())
    else:
        st.write("📭 Sem dados.")

# --- 9. PDF ---
elif menu == "🖨️ Imprimir PDF":
    st.header("🖨️ Gerar PDF de Ocorrência")
    if not df_ocorrencias.empty:
        lista = (df_ocorrencias["id"].astype(str) + " - " + df_ocorrencias["data"] + " - " + df_ocorrencias["aluno"]).tolist()
        occ_sel = st.selectbox("Selecione", lista)
        idx = lista.index(occ_sel)
        occ = df_ocorrencias.iloc[idx]
        st.info(f"**ID:** {occ['id']} | **Aluno:** {occ['aluno']} | **Data:** {occ['data']}")
        if st.button("📄 Gerar PDF"):
            pdf_buffer = gerar_pdf_ocorrencia(occ)
            st.download_button(label="📥 Baixar PDF", data=pdf_buffer,
                              file_name=f"Ocorrencia_{occ['id']}_{occ['aluno']}.pdf", mime="application/pdf")
    else:
        st.write("📭 Nenhuma ocorrência.")