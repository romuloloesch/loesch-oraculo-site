
GSC CSV → JSON do Painel Oracular v1 (Autônomo)

1) Exporte um CSV do Google Search Console com as colunas (case-insensitive):
   date, clicks, impressions, ctr, position, device, country
   - Pode exportar "Desempenho" e incluir Dimensões: Data, Dispositivo e País.
   - Se "device" ou "country" não estiverem presentes, o conversor funciona mesmo assim.

2) Rode o conversor (Linux):
   python3 gsc_csv_to_painel_json.py --csv gsc_export.csv --out dados_oraculares.json

3) Copie o arquivo gerado (dados_oraculares.json) para a pasta do painel e abra:
   painel_oracular_v1.html  → botão "Atualizar Base de Dados" → selecione o JSON.

Arquivos neste pacote:
- gsc_csv_to_painel_json.py
- gsc_export_template.csv (modelo com colunas/linhas)
