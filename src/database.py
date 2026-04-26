import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# Carrega variáveis de ambiente
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Variáveis SUPABASE_URL e SUPABASE_KEY não encontradas. Verifique o .env ou Secrets do Streamlit.")

# Inicializa cliente
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_students():
    """Busca todos os alunos"""
    try:
        response = supabase.table("alunos").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Erro ao buscar alunos: {e}")
        return []

def get_teachers():
    """Busca todos os professores"""
    try:
        response = supabase.table("professores").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Erro ao buscar professores: {e}")
        return []

def save_occurrence(student_name, teacher_name, infringements, description, actions):
    """Salva uma nova ocorrência"""
    try:
        data = {
            "nome_aluno": student_name,
            "nome_professor": teacher_name,
            "infracoes": infringements,
            "descricao": description,
            "acoes_tomadas": actions,
            "data_ocorrencia": datetime.now().isoformat()
        }
        print(f"[DEBUG] Tentando salvar ocorrência: {data}")
        response = supabase.table("ocorrencias").insert(data).execute()
        print(f"[DEBUG] Resposta do Supabase: {response}")
        return True
    except Exception as e:
        print(f"Erro ao salvar ocorrência: {e}")
        import streamlit as st
        st.error(f"❌ Erro detalhado: {str(e)}")
        return False

def get_occurrences():
    """Busca todas as ocorrências"""
    try:
        response = supabase.table("ocorrencias").select("*").order("data_ocorrencia", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Erro ao buscar ocorrências: {e}")
        return []