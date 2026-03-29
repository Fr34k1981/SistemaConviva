# Configurações do Sistema Conviva - Protocolo 179
CATEGORIES = {
    "GRAVÍSSIMA": {"color": "#d32f2f", "icon": "🚨", "actions": ["Encaminhamento ao Conselho Tutelar", "Suspensão Temporária", "Transferência"]},
    "GRAVE": {"color": "#f57c00", "icon": "⚠️", "actions": ["Suspensão Temporária", "Retenção em Sala"]},
    "MÉDIA": {"color": "#fbc02d", "icon": "⚖️", "actions": ["Retenção em Sala", "Prestação de Serviços"]},
    "LEVE": {"color": "#388e3c", "icon": "ℹ️", "actions": ["Advertência Verbal", "Advertência Escrita"]}
}

INFRINGEMENTS = {
    "Agressão física": "GRAVÍSSIMA",
    "Ameaça": "GRAVÍSSIMA",
    "Porte de arma": "GRAVÍSSIMA",
    "Uso de drogas": "GRAVÍSSIMA",
    "Tráfico de drogas": "GRAVÍSSIMA",
    "Atos libidinosos": "GRAVÍSSIMA",
    "Furto qualificado": "GRAVÍSSIMA",
    "Dano grave ao patrimônio": "GRAVÍSSIMA",
    
    "Desobediência reiterada": "GRAVE",
    "Bullying": "GRAVE",
    "Discriminação": "GRAVE",
    "Falta grave à autoridade": "GRAVE",
    "Incitação à violência": "GRAVE",
    
    "Conflito verbal": "MÉDIA",
    "Perturbação de aula": "MÉDIA",
    "Uso indevido de celular": "MÉDIA",
    "Saída não autorizada": "MÉDIA",
    "Dano leve ao patrimônio": "MÉDIA",
    
    "Atraso": "LEVE",
    "Uniforme incompleto": "LEVE",
    "Material esquecido": "LEVE",
    "Conversa paralela": "LEVE"
}

def get_infringements_by_category():
    result = {cat: [] for cat in CATEGORIES.keys()}
    for inf, cat in INFRINGEMENTS.items():
        result[cat].append(inf)
    return result
