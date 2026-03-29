from supabase import create_client, Client
import os
from datetime import datetime
import pandas as pd

# Inicialização segura (evita erro se não houver variáveis de ambiente ainda)
def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        # Tenta carregar do .env se existir
        try:
            from dotenv import load_dotenv
            load_dotenv()
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
        except:
            pass
    
    if not url or not key:
        raise Exception("Supabase URL e Key não configuradas. Verifique suas variáveis de ambiente.")
    
    return create_client(url, key)

# --- ALUNOS ---
def get_students() -> list:
    try:
        supabase = get_supabase_client()
        response = supabase.table("alunos").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Erro ao buscar alunos: {e}")
        return []

def save_student(data: dict):
    supabase = get_supabase_client()
    supabase.table("alunos").insert(data).execute()

def update_student(student_id: int, data: dict):
    supabase = get_supabase_client()
    supabase.table("alunos").update(data).eq("id", student_id).execute()

def delete_student(student_id: int):
    supabase = get_supabase_client()
    supabase.table("alunos").delete().eq("id", student_id).execute()

# --- PROFESSORES ---
def get_teachers() -> list:
    try:
        supabase = get_supabase_client()
        response = supabase.table("professores").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Erro ao buscar professores: {e}")
        return []

def save_teacher(data: dict):
    supabase = get_supabase_client()
    supabase.table("professores").insert(data).execute()

def update_teacher(teacher_id: int, data: dict):
    supabase = get_supabase_client()
    supabase.table("professores").update(data).eq("id", teacher_id).execute()

def delete_teacher(teacher_id: int):
    supabase = get_supabase_client()
    supabase.table("professores").delete().eq("id", teacher_id).execute()

# --- OCORRÊNCIAS ---
def save_occurrence(data: dict):
    """Salva uma nova ocorrência no banco de dados."""
    try:
        supabase = get_supabase_client()
        # Garante que a data esteja no formato correto
        if 'data_ocorrencia' in data and isinstance(data['data_ocorrencia'], str):
             # Se for string, tenta converter ou deixa como está se já estiver ISO
             pass 
        
        response = supabase.table("ocorrencias").insert(data).execute()
        return response.data
    except Exception as e:
        print(f"Erro ao salvar ocorrência: {e}")
        raise e

def get_occurrences(limit: int = 100) -> list:
    try:
        supabase = get_supabase_client()
        response = supabase.table("ocorrencias").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Erro ao buscar ocorrências: {e}")
        return []

def update_occurrence(occ_id: int, data: dict):
    supabase = get_supabase_client()
    supabase.table("ocorrencias").update(data).eq("id", occ_id).execute()

def delete_occurrence(occ_id: int):
    supabase = get_supabase_client()
    supabase.table("ocorrencias").delete().eq("id", occ_id).execute()

# --- RESPONSÁVEIS ---
def get_guardians() -> list:
    try:
        supabase = get_supabase_client()
        response = supabase.table("responsaveis").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        return []

def save_guardian(data: dict):
    supabase = get_supabase_client()
    supabase.table("responsaveis").insert(data).execute()
