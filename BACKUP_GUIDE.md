# 🛡️ Sistema de Backup Automático - Guia de Uso

## 📋 Visão Geral

O Sistema Conviva inclui um **sistema de backup automático profissional** que:
- ✅ Faz backup automático na inicialização
- ✅ Cria backup antes de salvar dados críticos
- ✅ Remove automaticamente backups com >30 dias
- ✅ Permite restaurar qualquer ponto anterior
- ✅ Oferece interface visual intuitiva

---

## 🚀 Como Usar

### 1️⃣ Acessar o Gerenciador de Backups

1. Abra o Sistema Conviva
2. No menu lateral, clique em **💾 Backups**

### 2️⃣ Criar Backup Manual

Na seção **➕ Criar Backup Manual**:
1. *(Opcional)* Digite um nome customizado (ex: "backup_importantes")
2. Clique em **🔄 Criar Backup Agora**
3. Mensagem de sucesso aparecerá

### 3️⃣ Visualizar Backups

A seção **📋 Backups Disponíveis** mostra:
- **Total de Backups** - Quantidade total
- **Tamanho Total** - Espaço em MB
- **Backup Mais Recente** - Data e hora

Cada backup pode ser expandido para ver opções:
- 🔄 **Restaurar** - Restaura para este ponto
- 📥 **Download** - Baixa o ZIP para guardar
- 📊 **Detalhes** - Lista arquivos contidos
- 🗑️ **Deletar** - Remove o backup

### 4️⃣ Restaurar um Backup

⚠️ **IMPORTANTE:** Faça isto apenas se necessário!

1. Localize o backup desejado
2. Clique em **🔄 Restaurar**
3. Sistema criará "pre_restore" backup (segurança)
4. Dados restaurados
5. Recarregue a página

### 5️⃣ Limpeza Automática

Na seção **🧹 Limpeza Automática**:
1. Ajuste o slider para dias de retenção (padrão: 30)
2. Clique em **Limpar Agora**
3. Backups antigos serão removidos

### 6️⃣ Exportar Dados em Texto

Na seção **📄 Exportar Dados em Texto**:
1. Clique em **📥 Exportar Dados Legíveis (TXT)**
2. Arquivo será baixado
3. Pode visualizar os dados em formato texto

---

## 📊 O Que é Feito Backup

Cada backup contém:
- ✅ `alunos_cadastrados.csv` - Lista de alunos
- ✅ `ocorrencias.csv` - Histórico de ocorrências
- ✅ `turmas/` - CSVs de cada turma

**Formato:** ZIP comprimido (~70% menor tamanho)

---

## 🔄 Quando Backups são Criados

### Automático
- ✅ Ao abrir o app (uma vez por sessão)
- ✅ Antes de salvar ocorrência importante
- ✅ Ao restaurar (cria "pre_restore")

### Manual
- ✅ Quando clica em "Criar Backup Agora"

---

## 🧹 Limpeza Automática

- **Padrão:** 30 dias de retenção
- **Quando:** Ao abrir o app (automático)
- **O que remove:** Backups com mais de 30 dias
- **Customizável:** Ajuste o slider na página

---

## 💡 Cenários de Uso

### Cenário 1: Recuperar de Erro
```
1. Ocorreu um erro que corrompeu dados
2. Acesse 💾 Backups
3. Localize backup anterior ao erro
4. Clique em Restaurar
5. Dados recuperados!
```

### Cenário 2: Backup Seguro em Outro Local
```
1. Acesse 💾 Backups
2. Clique em 📥 Download (no backup desejado)
3. Salve o ZIP em local seguro (Google Drive, Dropbox)
4. Pronto! Backup seguro em nuvem
```

### Cenário 3: Auditoria de Dados
```
1. Acesse 💾 Backups
2. Clique em 📄 Exportar Dados Legíveis
3. Abra o TXT em um editor
4. Revise todos os dados em formato texto
```

---

## ⚠️ Avisos Importantes

### ⚠️ Restauração é IRREVERSÍVEL

Ao restaurar:
- ✅ Um backup de segurança é criado primeiro
- ✅ Mas dados posteriores serão perdidos
- ⚠️ Certifique-se antes de restaurar!

### 💾 Espaço em Disco

- Cada backup consome ~1-5 MB (comprimido)
- Com 30 dias: ~30-150 MB
- Backups antigos removem automaticamente

### 🔒 Segurança

- Backups são armazenados localmente
- Se o disco falhar, backups também são perdidos
- **Recomendação:** Faça download periódico para nuvem

---

## 🔧 Configuração Avançada

### Alterar Diretório de Backups

```python
# Em src/backup_manager.py
bm = BackupManager(backup_dir="outro/diretorio")
```

### Alterar Período de Retenção

Se muda antes de salvar ocorrência:
```python
# No app.py, aumentar para 60 dias
st.session_state.backup_manager.limpar_backups_antigos(dias_retencao=60)
```

---

## 📈 Estatísticas

Você pode visualizar:
- Total de backups criados
- Tamanho total ocupado
- Data do backup mais recente
- Arquivos contidos em cada backup

---

## 🆘 Solução de Problemas

### P: Restauração não funcionou
**R:** 
1. Verifique se o backup está íntegro
2. Tente download e extraia manualmente
3. Copie CSVs para pasta `data/`

### P: Backups não estão sendo criados
**R:**
1. Verifique pasta `data/backups/` existe
2. Verifique permissões de escrita
3. Restart o app

### P: Espaço em disco cheio
**R:**
1. Execute limpeza automática
2. Reduza dias de retenção
3. Delete backups manualmente

---

## 📞 Suporte

Para mais informações:
1. Consulte `DESIGN_GUIDE.md`
2. Veja código em `src/backup_manager.py`
3. Verifique `src/components.py` para UI

---

**✅ Sistema de Backup Profissional Ativo!**
