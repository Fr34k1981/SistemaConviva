# ROLLBACK_PLAN.md

## Rollback Local

1. Parar o Streamlit em execucao.
2. Se a ponte de entrada falhar, copiar `legacy_app.py` de volta para `app.py`.
3. Se for necessario voltar ao estado anterior completo, restaurar `app.py` a partir do backup mais recente em `data/backups/app_refatoracao_v2_*.py`.
4. Rodar:

```bash
python -m py_compile app.py legacy_app.py
```

5. Subir novamente:

```bash
streamlit run app.py
```

## Rollback Git

1. Verificar arquivos alterados:

```bash
git status --short
```

2. Reverter apenas arquivos da alteracao problematica, sem apagar dados locais.
3. Nunca usar `git reset --hard` sem autorizacao explicita.

## Banco/Supabase

Nenhuma alteracao de schema foi executada nesta fase. Se uma futura migracao alterar banco, deve existir script de rollback SQL antes da execucao.
