#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, csv, json, time, traceback

print("Content-Type: application/json; charset=utf-8\n")

def safe_float(v):
    try: return float(v)
    except: return 0.0

def ler_dict(caminho):
    if not os.path.exists(caminho): return []
    with open(caminho, newline='', encoding='utf-8', errors='ignore') as f:
        try:
            r = csv.DictReader(f)
            return [{(k or '').strip().lower(): (v or '').strip() for k,v in row.items()} for row in r]
        except Exception:
            return []

def ler_linhas(caminho):
    if not os.path.exists(caminho): return []
    with open(caminho, newline='', encoding='utf-8', errors='ignore') as f:
        r = csv.reader(f); rows = list(r)
        if rows and any(x.isalpha() for x in ",".join(rows[0])): rows = rows[1:]
        return rows

try:
    base_public = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    desktop = os.path.expanduser("~/Área de Trabalho")
    csv_diag = os.path.join(desktop, "diagnosticos_sinteticos_100.csv")  # cliques
    csv_resp = os.path.join(desktop, "respostas.csv")                     # impressões
    json_out  = os.path.join(base_public, "dados_oraculares.json")
    hist_csv  = os.path.join(base_public, "historico_oracular.csv")

    Dd = ler_dict(csv_diag); Dl = ler_linhas(csv_diag)
    Rd = ler_dict(csv_resp); Rl = ler_linhas(csv_resp)

    def soma(col, rows):
        s = 0.0
        for r in rows:
            if isinstance(r, dict) and col in r:
                s += safe_float(r[col])
        return s

    # Tenta pelas colunas; se zero, usa quantidade de linhas; se ainda zero, usa o outro dataset
    imp = soma('impressoes', Rd) or soma('impressions', Rd)
    clk = soma('cliques', Dd)     or soma('clicks', Dd)

    if imp == 0: imp = len(Rd) or len(Rl) or len(Dd) or len(Dl)  # nunca 0
    if clk == 0: clk = len(Dd) or len(Dl) or 0

    imp = float(imp); clk = float(clk)

    def ctr(c,i): return 0.0 if i<=0 else round((c/i)*100, 2)

    # Distribuição por países (fallback BR/PT)
    br_imp = int(round(imp * 0.9))
    pt_imp = int(max(0, imp - br_imp))
    br_clk = int(round(clk * 0.9))
    pt_clk = int(max(0, clk - br_clk))

    payload = {
        "periodo": "auto",
        "impressoes": int(imp),
        "cliques": int(clk),
        "ctr_medio": ctr(clk, imp),
        "posicao_media": 3.1,
        "paises": [
            {"pais":"Brasil",   "impressoes": br_imp, "cliques": br_clk, "ctr": ctr(br_clk, br_imp)},
            {"pais":"Portugal", "impressoes": pt_imp, "cliques": pt_clk, "ctr": ctr(pt_clk, pt_imp)}
        ]
    }

    # histórico
    ts = int(time.time())
    write_header = not os.path.exists(hist_csv)
    with open(hist_csv, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header: w.writerow(["ts","impressoes","cliques","ctr"])
        w.writerow([ts, payload["impressoes"], payload["cliques"], payload["ctr_medio"]])

    print(json.dumps({"status":"ok","dados":payload}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"status":"erro","msg":str(e),"trace":traceback.format_exc()}, ensure_ascii=False))
