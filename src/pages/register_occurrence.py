import streamlit as st
from src.config import CATEGORIES, get_infringements_by_category
from src.database import save_occurrence, get_students, get_teachers
from datetime import datetime

def render_register_page():
    st.title("📝 Registrar Ocorrência")
    
    # Colunas para dados básicos
    col1, col2 = st.columns(2)
    with col1:
        students = get_students()
        student_names = [f"{s['nome']} ({s['turma']})" for s in students]
        selected_student = st.selectbox("Aluno", options=student_names if student_names else ["Nenhum aluno cadastrado"])
    
    with col2:
        teachers = get_teachers()
        teacher_names = [t['nome'] for t in teachers]
        selected_teacher = st.selectbox("Professor Relator", options=teacher_names if teacher_names else ["Nenhum professor cadastrado"])

    st.markdown("### 📋 Selecionar Infração(ões)")
    st.info("Clique nos cards abaixo para selecionar uma ou mais infrações.")

    infringements_map = get_infringements_by_category()
    selected_infringements = []

    # Renderização visual por categoria
    for category, items in infringements_map.items():
        config = CATEGORIES[category]
        st.markdown(f"#### {config['icon']} {category}")
        
        cols = st.columns(3) # 3 cards por linha
        for idx, item in enumerate(items):
            with cols[idx % 3]:
                # Card visual usando container e botão
                with st.container():
                    st.markdown(f"""
    <style>
    .card-{category.replace(' ', '-')} {{
        background-color: {config['color']}20;
        border: 1px solid {config['color']};
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.3s;
    }}
    .card-{category.replace(' ', '-')}:hover {{
        background-color: {config['color']}40;
    }}
    </style>
    <div class="card-{category.replace(' ', '-')}">
        <b>{item}</b>
    </div>
    """, unsafe_allow_html=True)
                    
                    if st.button(f"Selecionar", key=f"btn_{item}", use_container_width=True):
                        if item not in selected_infringements:
                            selected_infringements.append(item)
                            st.rerun()
                        else:
                            selected_infringements.remove(item)
                            st.rerun()
    
    # Mostrar selecionados
    if selected_infringements:
        st.success(f"✅ Selecionadas: {', '.join(selected_infringements)}")
    else:
        st.warning("Nenhuma infração selecionada ainda.")

    # Descrição e Ações
    description = st.text_area("Descrição Detalhada dos Fatos", height=150)
    
    # Ações sugeridas baseadas na gravidade
    suggested_actions = []
    for inf in selected_infringements:
        cat = next((c for c, items in infringements_map.items() if inf in items), None)
        if cat:
            suggested_actions.extend(CATEGORIES[cat]['actions'])
    suggested_actions = list(set(suggested_actions)) # Remove duplicatas
    
    final_actions = st.multiselect("Ações Tomadas", options=suggested_actions, default=suggested_actions[:1] if suggested_actions else [])

    if st.button("💾 Salvar Ocorrência", type="primary", use_container_width=True):
        if not selected_infringements:
            st.error("⚠️ Selecione pelo menos uma infração!")
        elif description.strip() == "":
            st.error("⚠️ Preencha a descrição dos fatos!")
        else:
            # Extrair nome do aluno
            student_name = selected_student.split(" (")[0] if selected_student else ""
            
            success = save_occurrence(
                student_name=student_name,
                teacher_name=selected_teacher,
                infringements=selected_infringements,
                description=description,
                actions=final_actions
            )
            
            if success:
                st.success("✅ Ocorrência registrada com sucesso!")
                st.balloons()
                if st.button("Limpar e Nova Ocorrência"):
                    st.rerun()
            else:
                st.error("❌ Erro ao salvar. Verifique a conexão com o banco.")
