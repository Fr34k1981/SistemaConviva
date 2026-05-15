"""
Página independente para Lista Provisória de Tutoria.

Como usar:
1. Crie uma pasta chamada pages dentro do seu projeto, se ainda não existir.
2. Coloque este arquivo dentro dela:
   pages/Lista_Provisoria_Tutoria.py
3. Rode normalmente o app principal:
   streamlit run app.py

Esta página NÃO altera o app.py, NÃO salva no Supabase e NÃO mexe na Tutoria oficial.
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import unicodedata
import re

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
except Exception:
    colors = None
    A4 = None
    SimpleDocTemplate = None
    Table = None
    TableStyle = None
    Paragraph = None
    Spacer = None
    getSampleStyleSheet = None
    ParagraphStyle = None
    TA_CENTER = None
    TA_LEFT = None

st.set_page_config(
    page_title="Lista Provisória de Tutoria",
    layout="wide",
    page_icon="🧾",
)

st.markdown(
    """
    <style>
    .main .block-container {max-width: 1200px; padding-top: 1.2rem;}
    .aviso {
        background: linear-gradient(90deg, #fff7ed, #ecfeff);
        border: 1px solid #bae6fd;
        border-left: 6px solid #0ea5e9;
        border-radius: 10px;
        padding: 0.9rem 1rem;
        margin: 0.8rem 0 1rem 0;
        color: #0f172a;
    }
    .titulo {
        background: linear-gradient(120deg, #ff9ad5, #ffd97a, #a6f4e7, #8bc7ff, #c99bff);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        color: #17324d;
        margin-bottom: 1rem;
        font-weight: 800;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="titulo">
        <h2 style="margin:0;">🧾 Lista Provisória de Tutoria</h2>
        <p style="margin:.25rem 0 0 0;">Upload, edição e impressão temporária de listas. Não salva no Supabase e não altera a Tutoria oficial.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="aviso">
        <b>Uso emergencial:</b> esta página serve apenas para imprimir listas provisórias.
        Os dados ficam somente nesta sessão e nos arquivos baixados por você.
    </div>
    """,
    unsafe_allow_html=True,
)


def _normalizar_texto(valor):
    if valor is None:
        return ""
    texto = str(valor).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto)
    return texto.upper().strip()


def _limpar_ra(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    texto = re.sub(r"\.0$", "", texto)
    texto = re.sub(r"\D", "", texto)
    return texto


def _ler_arquivo_upload(arquivo):
    nome = arquivo.name.lower()
    if nome.endswith(".csv"):
        raw = arquivo.getvalue()
        for sep in [";", ",", "\t", "|"]:
            for enc in ["utf-8-sig", "latin1", "cp1252"]:
                try:
                    df = pd.read_csv(BytesIO(raw), sep=sep, encoding=enc)
                    if df.shape[1] >= 2:
                        return df
                except Exception:
                    pass
        return pd.read_csv(BytesIO(raw), sep=None, engine="python")
    if nome.endswith((".xlsx", ".xls")):
        return pd.read_excel(arquivo)
    raise ValueError("Formato não aceito. Use CSV, XLS ou XLSX.")


def _detectar_coluna(colunas, candidatos):
    norm = {_normalizar_texto(c): c for c in colunas}
    for cand in candidatos:
        cand_norm = _normalizar_texto(cand)
        for chave, original in norm.items():
            if cand_norm == chave or cand_norm in chave or chave in cand_norm:
                return original
    return None


def _normalizar_lista(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["Nº", "Nome", "RA", "Turma", "Situação/Observação"])

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    col_nome = _detectar_coluna(df.columns, [
        "Nome", "Nome do Aluno", "Aluno", "Estudante", "Nomes", "Nomes:", "Lista de Alunos"
    ])
    col_ra = _detectar_coluna(df.columns, [
        "RA", "R.A", "Registro do Aluno", "NR RA", "Número RA", "Numero RA"
    ])
    col_turma = _detectar_coluna(df.columns, [
        "Turma", "Ano/Série", "Serie", "Série", "Ano Serie", "Ano/Série"
    ])
    col_situacao = _detectar_coluna(df.columns, [
        "Situação", "Situacao", "Situação do Aluno", "Status", "Observação", "Observacao"
    ])
    col_numero = _detectar_coluna(df.columns, [
        "Nº", "N°", "Numero", "Número", "Chamada", "Nº de chamada"
    ])

    base = pd.DataFrame()
    base["Nome"] = df[col_nome].astype(str).str.strip() if col_nome else ""
    base["RA"] = df[col_ra].apply(_limpar_ra) if col_ra else ""
    base["Turma"] = df[col_turma].astype(str).str.strip() if col_turma else ""
    base["Situação/Observação"] = df[col_situacao].astype(str).str.strip() if col_situacao else ""

    if col_numero:
        base["Nº"] = df[col_numero]
    else:
        base["Nº"] = range(1, len(base) + 1)

    base = base[["Nº", "Nome", "RA", "Turma", "Situação/Observação"]]
    base = base.replace({"nan": "", "NaN": "", "None": ""})
    base = base[base["Nome"].astype(str).str.strip() != ""]
    base = base.reset_index(drop=True)
    if base["Nº"].astype(str).str.strip().eq("").all():
        base["Nº"] = range(1, len(base) + 1)
    return base


def _excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Lista Tutoria")
        ws = writer.sheets["Lista Tutoria"]
        for col in ws.columns:
            max_len = 10
            col_letter = col[0].column_letter
            for cell in col:
                try:
                    max_len = max(max_len, len(str(cell.value or "")))
                except Exception:
                    pass
            ws.column_dimensions[col_letter].width = min(max_len + 2, 45)
    output.seek(0)
    return output.getvalue()


def _html_impressao(df, titulo, responsavel, turma, observacoes):
    linhas = ""
    for _, row in df.iterrows():
        linhas += f"""
        <tr>
            <td>{row.get('Nº','')}</td>
            <td>{row.get('Nome','')}</td>
            <td>{row.get('RA','')}</td>
            <td>{row.get('Turma','')}</td>
            <td>{row.get('Situação/Observação','')}</td>
        </tr>
        """

    data = datetime.now().strftime("%d/%m/%Y %H:%M")
    html = f"""
    <!doctype html>
    <html lang="pt-br">
    <head>
    <meta charset="utf-8">
    <title>{titulo}</title>
    <style>
        @page {{ size: A4; margin: 1.2cm; }}
        body {{ font-family: Arial, sans-serif; color: #111827; }}
        .cabecalho {{ text-align: center; border-bottom: 2px solid #111827; padding-bottom: 8px; margin-bottom: 12px; }}
        h1 {{ margin: 0; font-size: 20px; }}
        h2 {{ margin: 4px 0 0 0; font-size: 15px; }}
        .meta {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px 18px; margin: 12px 0; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
        th {{ background: #e5e7eb; border: 1px solid #111827; padding: 5px; text-align: left; }}
        td {{ border: 1px solid #111827; padding: 5px; vertical-align: top; }}
        .assinaturas {{ margin-top: 24px; display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }}
        .linha {{ border-top: 1px solid #111827; text-align: center; padding-top: 4px; font-size: 11px; }}
        .obs {{ margin: 10px 0; font-size: 12px; }}
        .no-print {{ margin: 10px 0 20px 0; }}
        @media print {{ .no-print {{ display: none; }} }}
    </style>
    </head>
    <body>
        <div class="no-print"><button onclick="window.print()">Imprimir</button></div>
        <div class="cabecalho">
            <h1>Prof.ª Eliane Aparecida Dantas da Silva - PEI</h1>
            <h2>{titulo}</h2>
        </div>
        <div class="meta">
            <div><b>Responsável/Tutor(a):</b> {responsavel}</div>
            <div><b>Turma:</b> {turma}</div>
            <div><b>Quantidade:</b> {len(df)} estudante(s)</div>
            <div><b>Data:</b> {data}</div>
        </div>
        <div class="obs"><b>Observações:</b> {observacoes}</div>
        <table>
            <thead>
                <tr>
                    <th style="width:6%;">Nº</th>
                    <th>Nome</th>
                    <th style="width:18%;">RA</th>
                    <th style="width:15%;">Turma</th>
                    <th style="width:22%;">Situação/Observação</th>
                </tr>
            </thead>
            <tbody>{linhas}</tbody>
        </table>
        <div class="assinaturas">
            <div class="linha">Assinatura do(a) responsável</div>
            <div class="linha">Coordenação/Gestão</div>
        </div>
    </body>
    </html>
    """
    return html


def _pdf_bytes(df, titulo, responsavel, turma, observacoes):
    if SimpleDocTemplate is None:
        raise RuntimeError("ReportLab não está disponível no ambiente.")

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=15,
        leading=18,
        spaceAfter=8,
    )
    estilo_sub = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=11,
        spaceAfter=8,
    )
    estilo_normal = ParagraphStyle(
        "NormalPequeno",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
    )

    story = []
    story.append(Paragraph("Prof.ª Eliane Aparecida Dantas da Silva - PEI", estilo_titulo))
    story.append(Paragraph(titulo, estilo_sub))
    story.append(Spacer(1, 8))

    meta = [
        [Paragraph("<b>Responsável/Tutor(a):</b>", estilo_normal), Paragraph(str(responsavel), estilo_normal), Paragraph("<b>Turma:</b>", estilo_normal), Paragraph(str(turma), estilo_normal)],
        [Paragraph("<b>Quantidade:</b>", estilo_normal), Paragraph(str(len(df)), estilo_normal), Paragraph("<b>Data:</b>", estilo_normal), Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), estilo_normal)],
    ]
    tabela_meta = Table(meta, colWidths=[85, 180, 55, 130])
    tabela_meta.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(tabela_meta)
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Observações:</b> {observacoes}", estilo_normal))
    story.append(Spacer(1, 8))

    data = [["Nº", "Nome", "RA", "Turma", "Situação/Observação"]]
    for _, row in df.iterrows():
        data.append([
            str(row.get("Nº", "")),
            Paragraph(str(row.get("Nome", "")), estilo_normal),
            str(row.get("RA", "")),
            str(row.get("Turma", "")),
            Paragraph(str(row.get("Situação/Observação", "")), estilo_normal),
        ])

    tabela = Table(data, colWidths=[28, 190, 85, 70, 150], repeatRows=1)
    tabela.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
    ]))
    story.append(tabela)
    story.append(Spacer(1, 22))
    story.append(Paragraph("__________________________________________&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;__________________________________________", estilo_sub))
    story.append(Paragraph("Assinatura do(a) responsável&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Coordenação/Gestão", estilo_sub))

    doc.build(story)
    output.seek(0)
    return output.getvalue()


col_a, col_b, col_c = st.columns([1.3, 1, 1])
with col_a:
    titulo = st.text_input("Título da lista", value="Lista Provisória de Tutoria")
with col_b:
    responsavel = st.text_input("Responsável/Tutor(a)", value="")
with col_c:
    turma_padrao = st.text_input("Turma", value="")

observacoes = st.text_area("Observações para impressão", value="", height=70)

arquivo = st.file_uploader("Envie a lista provisória", type=["csv", "xls", "xlsx"])

if arquivo:
    try:
        df_raw = _ler_arquivo_upload(arquivo)
        df_base = _normalizar_lista(df_raw)
        if turma_padrao.strip():
            df_base.loc[df_base["Turma"].astype(str).str.strip() == "", "Turma"] = turma_padrao.strip()

        st.success(f"Arquivo carregado com {len(df_base)} estudante(s). Edite abaixo antes de imprimir.")

        editado = st.data_editor(
            df_base,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            height=500,
            key="lista_provisoria_editor",
        )

        editado = editado.copy().replace({pd.NA: "", None: ""})
        editado["Nome"] = editado["Nome"].astype(str).str.strip()
        editado = editado[editado["Nome"] != ""].reset_index(drop=True)

        st.markdown("### Baixar / imprimir")
        c1, c2, c3 = st.columns(3)

        with c1:
            st.download_button(
                "📊 Baixar Excel editado",
                data=_excel_bytes(editado),
                file_name=f"lista_tutoria_provisoria_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        html_doc = _html_impressao(editado, titulo, responsavel, turma_padrao, observacoes)
        with c2:
            st.download_button(
                "🌐 Baixar HTML para impressão",
                data=html_doc.encode("utf-8"),
                file_name=f"lista_tutoria_provisoria_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                mime="text/html",
                use_container_width=True,
            )

        with c3:
            try:
                pdf = _pdf_bytes(editado, titulo, responsavel, turma_padrao, observacoes)
                st.download_button(
                    "🖨️ Baixar PDF",
                    data=pdf,
                    file_name=f"lista_tutoria_provisoria_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"PDF indisponível neste ambiente: {e}")

        with st.expander("Prévia da impressão em HTML"):
            st.components.v1.html(html_doc, height=650, scrolling=True)

    except Exception as e:
        st.error(f"Não foi possível processar o arquivo: {e}")
else:
    st.info("Envie uma lista em CSV, XLS ou XLSX para começar.")
