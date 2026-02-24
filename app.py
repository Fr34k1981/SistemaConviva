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
    .alert-critical { background: #fee; border-left: 5px solid #e74c3c; padding: 1rem; border-radius: 5px; margin: 1rem 0; }
    .alert-warning { background: #fff3cd; border-left: 5px solid #f39c12; padding: 1rem; border-radius: 5px; margin: 1rem 0; }
    .alert-success { background: #d4edda; border-left: 5px solid #27ae60; padding: 1rem; border-radius: 5px; margin: 1rem 0; }
    </style>
""", unsafe_allow_html=True)

# --- DADOS DA ESCOLA ---
ESCOLA_NOME = "Escola Estadual PROFESSORA ELIANE APARECIDA DANTAS DA SILVA - PEI"
ESCOLA_SUBTITULO = "🌟 Escola dos Sonhos"
ESCOLA_ENDERECO = "R. VALTER DE SOUZA COSTA, 147 - JARDIM PRIMAVERA - FERRAZ DE VASCONCELOS/SP"

# --- MENU LATERAL ---
menu = st.sidebar.selectbox("Menu", [
    "🏠 Início",
    "👨‍ Cadastrar Professores",
    "📝 Registrar Ocorrência",
    "📥 Importar Alunos",
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

# --- FUNÇÕES SUPABASE (USANDO REQUESTS) ---
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

# --- CARREGAR DADOS ---
df_alunos = carregar_alunos()
df_ocorrencias = carregar_ocorrencias()
df_professores = carregar_professores()

# --- 1. HOME ---
if menu == "🏠 Início":
    st.markdown(f"""
        <div class="main-header">
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
elif menu == "👨‍🏫 Cadastrar Professores":
    st.header("👨‍🏫 Cadastrar Professores")
    
    col1, col2 = st.columns(2)
    with col1:
        nome_prof = st.text_input("Nome do Professor *", placeholder="Ex: João da Silva")
        email_prof = st.text_input("E-mail (opcional)", placeholder="Ex: joao@educacao.sp.gov.br")
    
    with col2:
        st.info("💡 **Dica:** Cadastre todos os professores da escola para facilitar na hora de registrar ocorrências.")
    
    if st.button("💾 Salvar Professor"):
        if nome_prof:
            novo_prof = {
                "nome": nome_prof,
                "email": email_prof if email_prof else None
            }
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
            # Lê o arquivo
            df_import = pd.read_csv(arquivo_upload, sep=';', encoding='utf-8-sig')
            
            st.success("✅ Arquivo lido com sucesso!")
            st.info(f"📋 **Colunas encontradas:** {', '.join(df_import.columns.tolist())}")
            st.write(f"📊 **Total de linhas:** {len(df_import)}")
            
            # Mostra prévia dos dados
            st.write("🔍 **Prévia dos dados (primeiras 3 linhas):**")
            st.dataframe(df_import.head(3))
            
            # Mapeamento FLEXÍVEL para formato SED
            mapeamento = {}
            
            for col in df_import.columns:
                col_lower = col.lower().strip()
                
                # RA (exclui Dig. RA e UF RA)
                if col_lower == 'ra':
                    mapeamento['ra'] = col
                # Nome do Aluno
                elif 'nome' in col_lower:
                    mapeamento['nome'] = col
                # Data de Nascimento
                elif 'nascimento' in col_lower or 'nasc' in col_lower:
                    mapeamento['data_nascimento'] = col
                # Situação do Aluno
                elif 'situação' in col_lower or 'situacao' in col_lower:
                    mapeamento['situacao'] = col
            
            st.write("🔍 **Mapeamento encontrado:**")
            st.json(mapeamento)
            
            # Verifica se todas as colunas foram encontradas
            colunas_necessarias = ['ra', 'nome', 'data_nascimento', 'situacao']
            faltantes = [c for c in colunas_necessarias if c not in mapeamento]
            
            if faltantes:
                st.error(f"❌ Colunas não encontradas: {', '.join(faltantes)}")
                st.info("💡 Verifique os nomes exatos das colunas no CSV.")
            else:
                if st.button("🚀 Importar Alunos"):
                    if not turma_alunos:
                        st.error("❌ Preencha o nome da turma!")
                    else:
                        contagem = 0
                        erros = 0
                        for idx, row in df_import.iterrows():
                            try:
                                ra_valor = row[mapeamento['ra']]
                                ra_str = str(ra_valor).strip()
                                
                                if not ra_str or ra_str == 'nan':
                                    erros += 1
                                    continue
                                
                                aluno = {
                                    "ra": ra_str,
                                    "nome": str(row[mapeamento['nome']]).strip(),
                                    "data_nascimento": str(row[mapeamento['data_nascimento']]).strip(),
                                    "situacao": str(row[mapeamento['situacao']]).strip(),
                                    "turma": turma_alunos
                                }
                                if salvar_aluno(aluno):
                                    contagem += 1
                                else:
                                    erros += 1
                            except Exception as e:
                                erros += 1
                                continue
                        
                        st.success(f"✅ {contagem} alunos importados com sucesso!")
                        if erros > 0:
                            st.warning(f"⚠️ {erros} alunos não puderam ser importados.")
                        st.rerun()
                
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo: {str(e)}")
            st.info("💡 Tente salvar o CSV com encoding UTF-8 e separador ponto e vírgula (;)")

# --- 4. LISTA DE ALUNOS ---
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

# --- 5. REGISTRAR OCORRÊNCIA ---
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
                    prof = st.text_input("Professor 👨‍🏫", placeholder="Nome do professor")
                
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

# --- 6. HISTÓRICO ---
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

# --- 7. GRÁFICOS ---
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

# --- 8. PDF ---
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