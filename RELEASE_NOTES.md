# RELEASE_NOTES.md

## Refatoracao v2 - trabalho inicial

- Criada branch `refatoracao-v2`.
- Criado backup local de `app.py`.
- Criada documentacao tecnica inicial.
- Criada estrutura modular inicial.
- `app.py` reduzido para ponto de entrada com ponte para `legacy_app.py`.
- Corrigidos cards transparentes do Dashboard com classe dedicada.
- Removido botao de IA do Dashboard.
- Organizado box de plataformas no Dashboard.
- Restaurada separacao entre Mapao e Mapa da Sala.
- Adicionado fallback de leitura XLSX sem `openpyxl` para Prova Paulista, Mapao e Conselho.
- Top 10 da Prova Paulista passa a aparecer no Dashboard sem depender de ocorrencias.
- Inserida referencia de espacos de tutoria por professor.
