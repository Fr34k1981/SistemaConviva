# DECISOES_TECNICAS.md

## 2026-05-02 - Branch de refatoracao

Decisao: criar branch `refatoracao-v2` e backup local antes de continuar.

Motivo: permitir rollback e separar a estabilizacao da linha principal.

## 2026-05-02 - Hotfix antes da refatoracao pesada

Decisao: corrigir cards, Prova Paulista, Mapao e tutoria antes de mover codigo.

Motivo: o usuario reportou erros visuais e funcionais em producao. Corrigir comportamento quebrado reduz risco antes da modularizacao.

## 2026-05-02 - Reduzir app.py com ponte de compatibilidade

Decisao: reduzir `app.py` para um ponto de entrada curto e preservar o corpo atual em `legacy_app.py`.

Motivo: cumprir a Fase 1 sem mover paginas internamente neste mesmo passo. O `app.py` usa `runpy.run_path` para executar `legacy_app.py` a cada rerun do Streamlit, evitando cache de importacao e mantendo o comportamento atual.

Rollback: copiar `legacy_app.py` de volta para `app.py` ou restaurar `data/backups/app_refatoracao_v2_20260502_195306.py`.

## 2026-05-02 - Manter requests no Supabase

Decisao: criar camada inicial `db/supabase_client.py` usando `requests`.

Motivo: a migracao para `supabase-py` fica reservada para fase propria e reversivel.
