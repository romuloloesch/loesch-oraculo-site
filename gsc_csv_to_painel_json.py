#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GSC CSV → Painel Oracular JSON (Autônomo)
Uso:
  python gsc_csv_to_painel_json.py --csv caminho/para/export.csv --out dados_oraculares.json

Entrada: CSV único (do Search Console) com colunas (case-insensitive):
  date, clicks, impressions, ctr, position, device, country
- device: desktop | mobile | tablet (opcional; se ausente, será assumido 100% desktop)
- country: código ISO-2 (BR, US, AR, etc.) (opcional)

Observações:
- O script é tolerante a ausência de device e country; nesse caso agregará só o que existir.
- CTR pode vir como "8.2%" ou 0.082; detectamos automaticamente.
"""

import argparse, json, sys, math
from datetime import datetime
import pandas as pd

def normalize_columns(df):
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    # Renomeações mínimas
    rename_map = {
        'dates': 'date', 'data': 'date',
        'click': 'clicks', 'cliques':'clicks',
        'impressions':'impressions', 'impressoes':'impressions', 'impressões':'impressions',
        'ctr (%)':'ctr','ctr%':'ctr',
        'posicao':'position','posição':'position'
    }
    df = df.rename(columns={k:v for k,v in rename_map.items() if k in df.columns})
    # Garante colunas essenciais
    missing = [c for c in ['date','clicks','impressions'] if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}. É necessário no mínimo date, clicks, impressions.")
    # Tipos
    df['date'] = pd.to_datetime(df['date']).dt.date
    df['clicks'] = pd.to_numeric(df['clicks'], errors='coerce').fillna(0).astype(int)
    df['impressions'] = pd.to_numeric(df['impressions'], errors='coerce').fillna(0).astype(int)
    if 'ctr' in df.columns:
        # Aceita "8.2%" ou 0.082 ou 8.2
        def parse_ctr(x):
            if pd.isna(x): return None
            s = str(x).strip()
            if s.endswith('%'):
                try: return float(s.replace('%','').replace(',','.'))
                except: return None
            try:
                val = float(s.replace(',','.'))
                # se veio entre 0 e 1, transformar para %
                if 0 <= val <= 1: val *= 100.0
                return val
            except:
                return None
        df['ctr'] = df['ctr'].apply(parse_ctr)
    else:
        df['ctr'] = None
    if 'position' in df.columns:
        df['position'] = pd.to_numeric(df['position'], errors='coerce')
    else:
        df['position'] = None
    if 'device' not in df.columns:
        df['device'] = 'desktop'
    else:
        df['device'] = df['device'].fillna('desktop').str.lower().map({
            'desktop':'desktop','computer':'desktop','pc':'desktop',
            'mobile':'mobile','phone':'mobile','smartphone':'mobile',
            'tablet':'tablet','tab':'tablet'
        }).fillna('desktop')
    if 'country' not in df.columns:
        df['country'] = 'BR'
    else:
        df['country'] = df['country'].fillna('BR').str.upper().str[:2]
    return df

def compute_json(df):
    df = normalize_columns(df)
    # Série diária agregada (por data)
    daily = df.groupby('date').agg(
        clicks=('clicks','sum'),
        impressions=('impressions','sum'),
        ctr=('ctr', lambda s: s.dropna().mean() if s.notna().any() else None),
        position=('position', lambda s: s.dropna().mean() if s.notna().any() else None),
    ).reset_index().sort_values('date')

    # KPIs (todo período do CSV)
    total_clicks = int(daily['clicks'].sum())
    total_impr = int(daily['impressions'].sum())
    ctr_media = float((daily['clicks'].sum()/daily['impressions'].sum()*100.0) if total_impr>0 else 0.0)
    pos_media = float(daily['position'].mean()) if daily['position'].notna().any() else 0.0

    # Deltas placeholders (ajuste futuro se desejar)
    delta_imp = 0.0; delta_clk = 0.0; delta_ctr = 0.0; delta_pos = 0.0

    series = {
        "datas": [d.strftime("%Y-%m-%d") for d in daily['date']],
        "cliques": daily['clicks'].astype(int).tolist(),
        "impressoes": daily['impressions'].astype(int).tolist(),
        "ctr_pct": [round(x,1) if x is not None else None for x in daily['ctr']]
    }

    # Dispositivos (participação por impressões)
    dev = df.groupby('device').agg(impressions=('impressions','sum')).reset_index()
    total_dev = max(int(dev['impressions'].sum()), 1)
    def pct(label):
        return int(round(dev.loc[dev['device']==label,'impressions'].sum()/total_dev*100))
    dispositivos = {"desktop": pct('desktop'), "mobile": pct('mobile'), "tablet": pct('tablet')}

    # Países (top 10 por impressões)
    pais = df.groupby('country').agg(
        impressions=('impressions','sum'),
        clicks=('clicks','sum')
    ).reset_index()
    pais['ctr_pct'] = (pais['clicks']/pais['impressions']*100.0).replace([float('inf')],0).fillna(0.0)
    pais = pais.sort_values('impressions', ascending=False).head(10)

    output = {
        "meta": {
            "fonte": "Search Console (CSV convertido)",
            "ultima_atualizacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "periodo": {
                "inicio": daily['date'].min().strftime("%Y-%m-%d"),
                "fim": daily['date'].max().strftime("%Y-%m-%d")
            }
        },
        "kpis": {
            "impressoes_30d": total_impr,
            "cliques_30d": total_clicks,
            "ctr_medio_pct": round(ctr_media,1),
            "posicao_media": round(pos_media,2) if pos_media else 0.0,
            "delta_impressoes_pct": delta_imp,
            "delta_cliques_pct": delta_clk,
            "delta_ctr_pp": delta_ctr,
            "delta_posicao_pp": delta_pos
        },
        "series": series,
        "dispositivos": dispositivos,
        "paises": [
            {"pais": r['country'], "impressoes": int(r['impressions']), "cliques": int(r['clicks']), "ctr_pct": round(float(r['ctr_pct']),1)}
            for _, r in pais.iterrows()
        ]
    }
    return output

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Converter CSV do GSC para dados_oraculares.json")
    ap.add_argument("--csv", required=True, help="Caminho para o CSV exportado do GSC")
    ap.add_argument("--out", default="dados_oraculares.json", help="Arquivo de saída JSON")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    out = compute_json(df)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON gerado em: {args.out}")
    print(f"Período: {out['meta']['periodo']['inicio']} — {out['meta']['periodo']['fim']}")
    print(f"KPIs: impressoes={out['kpis']['impressoes_30d']}, cliques={out['kpis']['cliques_30d']}, ctr%={out['kpis']['ctr_medio_pct']}")

if __name__ == "__main__":
    main()
