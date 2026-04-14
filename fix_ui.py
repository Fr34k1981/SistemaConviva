import re

# Ler o app.py
with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Adicionar imports necessários se não existirem
imports_needed = [
    "from src.config import CATEGORIAS_INFRACOES, CORES_CATEGORIAS",
    "import src.pages.register_occurrence as reg_page"
]

for imp in imports_needed:
    if imp not in content:
        # Inserir após os outros imports
        content = content.replace("import streamlit as st", f"import streamlit as st\n{imp}")

# 2. Substituir a lógica antiga de seleção por uma chamada à nova função
# Procuramos onde começa a seção de registrar ocorrência
if "st.subheader('📋 Selecionar Infração(ões)')" in content:
    print("Detectada interface antiga. Substituindo...")
    # Estratégia: Comentar a parte visual antiga e chamar a nova função
    # Como o código é complexo, vamos injetar a chamada da nova função logo após o título da página
    
    # Definir o código da nova interface (simplificado para injeção)
    nova_chamada = """
    st.markdown("### 📋 Selecione as Infrações")
    st.info("Clique nos cards abaixo para selecionar/deselecionar.")
    
    # Chama a função modularizada que contém a UI de Cards
    infracoes_selecionadas = reg_page.render_infracoes_cards()
    
    if infracoes_selecionadas:
        st.success(f"{len(infracoes_selecionadas)} infração(ões) selecionada(s).")
    """
    
    # Vamos tentar substituir o bloco específico de seleção
    # Nota: Esta é uma substituição direta baseada em marcadores comuns
    old_pattern = r"st\.subheader\('📋 Selecionar Infração\(ões\)'\).*?(?=\n\s*st\.subheader|\n\s*if col\d\.button)"
    
    # Se a regex falhar por complexidade, faremos uma inserção segura
    if re.search(old_pattern, content, re.DOTALL):
        content = re.sub(old_pattern, nova_chamada.strip(), content, flags=re.DOTALL)
    else:
        # Fallback: Apenas avisa que precisa de ajuste manual se não achar o padrão exato
        print("Padrão exato não encontrado. Verifique o app.py manualmente na seção de registro.")

# Salvar
with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Script de atualização executado. Verifique se há erros ao rodar o app.")
