"""
EXEMPLO DE PÁGINA PADRONIZADA - REGISTRO DE OCORRÊNCIAS COM DESIGN SYSTEM
Mostra como usar todos os componentes conforme o design system
Use como referência para integrar no app.py
"""

import streamlit as st
from src.design_system import (
    COLORS, TYPOGRAPHY, SPACING, ICONS, GRAVIDADE_CORES,
    SIZES, get_typography_css, get_gravidade_styling, MENU_ITEMS
)
from src.ui_components import (
    render_header_page, render_card, render_section, render_badge,
    render_success_message, render_error_message, render_warning_message,
    render_info_message, render_divider, render_label,
    apply_global_style, render_stat_card
)


def exemplo_pagina_registro_ocorrencias():
    """
    Exemplo completo de página de registro de ocorrências
    usando todos os componentes do design system
    """
    
    # ===== SETUP =====
    st.set_page_config(
        page_title="Registro de Ocorrências",
        page_icon=ICONS["registro"],
        layout="wide"
    )
    
    # Aplicar estilos globais
    apply_global_style()
    
    # ===== HEADER =====
    render_header_page(
        title="Registro de Ocorrências",
        subtitle="Registre e acompanhe todas as ocorrências da escola",
        icon=ICONS["registro"]
    )
    
    # ===== ESTATÍSTICAS RÁPIDAS =====
    st.markdown(f"<h3 style='{get_typography_css('h3')}'>Resumo do Mês</h3>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_stat_card(
            label="Total de Ocorrências",
            value="124",
            change=8.5,
            icon=ICONS["ocorrencia"],
            variant="primary"
        )
    
    with col2:
        render_stat_card(
            label="Grav. Alta",
            value="23",
            change=2.1,
            icon=ICONS["error"],
            variant="danger"
        )
    
    with col3:
        render_stat_card(
            label="Em Resolução",
            value="15",
            change=-1.3,
            icon=ICONS["loading"],
            variant="warning"
        )
    
    with col4:
        render_stat_card(
            label="Resolvidas",
            value="86",
            change=5.2,
            icon=ICONS["success"],
            variant="success"
        )
    
    render_divider()
    
    # ===== ALERTAS INFORMATIVOS =====
    st.markdown(f"<h3 style='{get_typography_css('h3')}'>Avisos</h3>", unsafe_allow_html=True)
    
    render_info_message(
        title="Dica de Uso",
        message="Preencha todos os campos marcados com asterisco (*) para registrar uma ocorrência."
    )
    
    render_warning_message(
        title="Atenção",
        message="3 ocorrências aguardam resolução há mais de 10 dias. Clique aqui para revisar."
    )
    
    render_divider()
    
    # ===== FORMULÁRIO =====
    render_section(
        title="Novo Registro",
        icon=ICONS["create"]
    )
    
    with st.form("form_ocorrencia_padronizado", clear_on_submit=True):
        # ===== SEÇÃO 1: DADOS DO ALUNO =====
        st.markdown(f"<h4 style='{get_typography_css('h4')}' style='margin-top: 20px;'>👤 Informações do Aluno</h4>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            render_label("Nome do Aluno", required=True, help_text="Selecione o aluno envolvido")
            aluno = st.selectbox(
                "Selecione um aluno",
                ["Ana Silva", "Bruno Costa", "Carla Santos", "Daniel Oliveira", "Elena Martins"],
                label_visibility="collapsed"
            )
        
        with col2:
            render_label("Turma", required=True, help_text="Turma do aluno")
            turma = st.selectbox(
                "Selecione a turma",
                ["6º A", "6º B", "7º A", "7º B", "7º C", "8º A", "8º B", "9º A", "9º B"],
                label_visibility="collapsed"
            )
        
        render_divider()
        
        # ===== SEÇÃO 2: DADOS DA OCORRÊNCIA =====
        st.markdown(f"<h4 style='{get_typography_css('h4')}' style='margin-top: 20px;'>📋 Detalhes da Ocorrência</h4>", unsafe_allow_html=True)
        
        render_label("Data do Fato", required=True)
        data_fato = st.date_input(
            "Quando ocorreu?",
            label_visibility="collapsed"
        )
        
        render_label("Horário", required=True)
        hora_fato = st.time_input(
            "Que hora foi?",
            label_visibility="collapsed"
        )
        
        render_divider()
        
        # ===== SEÇÃO 3: CLASSIFICAÇÃO =====
        st.markdown(f"<h4 style='{get_typography_css('h4')}' style='margin-top: 20px;'>🏷️ Classificação</h4>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            render_label("Tipo de Infração", required=True)
            infracao = st.selectbox(
                "Categoria principal",
                ["Indisciplina", "Agressão Física", "Cabulou Aula", "Bullying", "Outro"],
                label_visibility="collapsed"
            )
        
        with col2:
            render_label("Grupo/Subcategoria", required=True)
            grupo = st.selectbox(
                "Subcategoria",
                ["Desrespeito", "Briga", "Ofensas", "Exclusão", "Desobediência"],
                label_visibility="collapsed"
            )
        
        render_divider()
        
        # ===== SEÇÃO 4: GRAVIDADE =====
        st.markdown(f"<h4 style='{get_typography_css('h4')}' style='margin-top: 20px;'>⚠️ Nível de Gravidade</h4>", unsafe_allow_html=True)
        
        render_label("Gravidade", required=True, help_text="Selecione o nível de severidade")
        
        # Exibir opções de gravidade com visuais
        gravidade_cols = st.columns(len(GRAVIDADE_CORES))
        gravidade_selecionada = None
        
        for idx, (grav_key, grav_data) in enumerate(GRAVIDADE_CORES.items()):
            with gravidade_cols[idx]:
                # Criar botão visual
                if st.button(
                    f"{grav_data['icon']} {grav_data['label']}",
                    key=f"btn_grav_{grav_key}",
                    use_container_width=True
                ):
                    st.session_state.gravidade_selecionada = grav_key
                    gravidade_selecionada = grav_key
        
        # Se já foi selecionada, mostrar novamente
        if "gravidade_selecionada" in st.session_state:
            gravidade_selecionada = st.session_state.gravidade_selecionada
            styling = get_gravidade_styling(gravidade_selecionada)
            
            # Mostrar badge de gravidade selecionada
            st.markdown(f"""
            <div style="
                background-color: {styling['light']};
                border-left: 4px solid {styling['primary']};
                padding: {SPACING['md']};
                border-radius: {SIZES['card_md']['height']};
                margin-top: {SPACING['md']};
            ">
                <strong style="color: {styling['dark']};">
                    {styling['icon']} Selecionado: {styling['label']}
                </strong>
            </div>
            """, unsafe_allow_html=True)
        
        render_divider()
        
        # ===== SEÇÃO 5: DESCRIÇÃO =====
        st.markdown(f"<h4 style='{get_typography_css('h4')}' style='margin-top: 20px;'>📝 Relato</h4>", unsafe_allow_html=True)
        
        render_label(
            "Descrição do Ocorrido",
            required=True,
            help_text="Descreva com detalhes o que aconteceu"
        )
        
        descricao = st.text_area(
            "Detalhe a ocorrência",
            height=150,
            placeholder="Explique o contexto, o que gerou a situação, quem estava presente, etc.",
            label_visibility="collapsed"
        )
        
        render_divider()
        
        # ===== SEÇÃO 6: ENCAMINHAMENTOS =====
        st.markdown(f"<h4 style='{get_typography_css('h4')}' style='margin-top: 20px;'>📤 Encaminhamentos</h4>", unsafe_allow_html=True)
        
        render_label("Ações Tomadas", required=False)
        
        encaminhamentos = st.multiselect(
            "Selecione os encaminhamentos",
            ["Conversa com aluno", "Conversa com responsável", "Orientação", "Repreensão", "Suspensão", "Expulsão", "Outro"],
            label_visibility="collapsed"
        )
        
        render_divider()
        
        # ===== SEÇÃO 7: RESPONSÁVEL =====
        st.markdown(f"<h4 style='{get_typography_css('h4')}' style='margin-top: 20px;'>👨‍🏫 Professor Registrante</h4>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            render_label("Professor", required=True)
            professor = st.selectbox(
                "Quem está registrando?",
                ["Prof. João Silva", "Prof. Maria Santos", "Prof. Pedro Costa"],
                label_visibility="collapsed"
            )
        
        with col2:
            render_label("Disciplina", required=True)
            disciplina = st.selectbox(
                "Em qual aula?",
                ["Português", "Matemática", "Ciências", "História", "Educação Física"],
                label_visibility="collapsed"
            )
        
        render_divider()
        
        # ===== BOTÕES =====
        st.markdown(f"<h4 style='{get_typography_css('h4')}' style='margin-top: 20px;'>Ações</h4>", unsafe_allow_html=True)
        
        btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])
        
        with btn_col1:
            submit = st.form_submit_button(
                f"{ICONS['success']} CONFIRMAR REGISTRO",
                use_container_width=True,
                type="primary"
            )
        
        with btn_col2:
            clear = st.form_submit_button(
                f"{ICONS['close']} LIMPAR",
                use_container_width=True
            )
        
        with btn_col3:
            pass
        
        # ===== PROCESSAMENTO DO FORMULÁRIO =====
        if submit:
            # Validar
            if not all([aluno, turma, infracao, grupo, descricao, professor]):
                render_error_message(
                    "Erro de Validação",
                    "Por favor, preencha todos os campos obrigatórios (*)"
                )
            else:
                # Simular salvamento
                render_success_message(
                    "Registro Salvo!",
                    f"Ocorrência de {aluno} ({turma}) registrada com sucesso. ID: #OC-2024-001234"
                )
                
                # Mostrar resumo
                st.markdown(f"<h4 style='{get_typography_css('h4')}'>📋 Resumo do Registro</h4>", unsafe_allow_html=True)
                
                summary_cols = st.columns(2)
                
                with summary_cols[0]:
                    render_card(
                        title="Informações",
                        content=f"""
                        <strong>Aluno:</strong> {aluno}<br>
                        <strong>Turma:</strong> {turma}<br>
                        <strong>Data/Hora:</strong> {data_fato} - {hora_fato}<br>
                        <strong>Professor:</strong> {professor}
                        """,
                        icon=ICONS["info"],
                        variant="info"
                    )
                
                with summary_cols[1]:
                    render_card(
                        title="Classificação",
                        content=f"""
                        <strong>Tipo:</strong> {infracao}<br>
                        <strong>Grupo:</strong> {grupo}<br>
                        <strong>Disciplina:</strong> {disciplina}
                        """,
                        icon=ICONS["filter"],
                        variant="default"
                    )
        
        elif clear:
            render_info_message(
                "Formulário Limpo",
                "Todos os campos foram resetados. Comece um novo registro."
            )
    
    render_divider()
    
    # ===== SEÇÃO FINAL: HISTÓRICO RECENTE =====
    st.markdown(f"<h3 style='{get_typography_css('h3')}'>📜 Registros Recentes</h3>", unsafe_allow_html=True)
    
    # Exemplo de cartas de registros anteriores
    recent_records = [
        {
            "aluno": "Ana Silva",
            "turma": "7º A",
            "tipo": "Indisciplina",
            "gravidade": "Leve",
            "data": "Hoje • 14:30",
            "status": "success"
        },
        {
            "aluno": "Bruno Costa",
            "turma": "8º B",
            "tipo": "Agressão Física",
            "gravidade": "Agressão Física",
            "data": "Ontem • 11:45",
            "status": "error"
        },
        {
            "aluno": "Carla Santos",
            "turma": "6º A",
            "tipo": "Cabulou Aula",
            "gravidade": "Moderado",
            "data": "2 dias • 09:15",
            "status": "warning"
        }
    ]
    
    for record in recent_records:
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            badge = render_badge(record["gravidade"], variant=record["gravidade"])
            st.markdown(f"""
            <div style="font-weight: bold;">{record['aluno']}</div>
            <div style="font-size: 0.9rem; color: {COLORS['text_secondary']};">{record['turma']} • {record['tipo']}</div>
            {badge}
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="color: {COLORS['text_secondary']};">{record['data']}</div>
            """, unsafe_allow_html=True)
        
        with col3:
            if record["status"] == "success":
                st.markdown(f"<div style='color: {COLORS['success']}; font-weight: bold;'>{ICONS['success']} Resolvido</div>", unsafe_allow_html=True)
            elif record["status"] == "error":
                st.markdown(f"<div style='color: {COLORS['danger']}; font-weight: bold;'>{ICONS['error']} Urgente</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='color: {COLORS['warning']}; font-weight: bold;'>{ICONS['loading']} Pendente</div>", unsafe_allow_html=True)
        
        render_divider()


if __name__ == "__main__":
    exemplo_pagina_registro_ocorrencias()
