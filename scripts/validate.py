"""
HONOR Dashboard — Script 3: Validación de datos
=================================================
Cruza los datos del JSON contra el Excel original para verificar que todo cuadra.

USO:
    python3 -m scripts.validate output/dashboard_data.json data/Analisis\ Honor\ 2025\ \(v3\).xlsx
"""

import pandas as pd
import json
import sys


def validate(data_file, excel_file):
    """Valida JSON vs Excel. Retorna True si no hay errores."""
    with open(data_file) as f:
        D = json.load(f)

    df = pd.read_excel(excel_file, sheet_name='BBDD')
    filt = df[df['Año'] == 2026].copy()

    errors = []

    for ch_name, ch_filter in [('SI','SI'),('NO','NO'),('Online','Online'),('ALL',None)]:
        sub = filt if ch_filter is None else filt[filt['Promotor']==ch_filter]
        d = D[ch_name]
        k = d['kpis']

        real_u = int(sub['Sell Qty'].sum())
        real_r = round(sub['Sales Value'].sum(), 2)
        real_stores = int(sub['Tienda Honor'].nunique())
        real_models = int(sub[sub['Sell Qty']>0]['modelo'].nunique())
        real_tk = round(real_r / real_u, 2) if real_u else 0

        if k['units'] != real_u: errors.append(f"{ch_name} units: {k['units']} vs {real_u}")
        if abs(k['revenue'] - real_r) > 1: errors.append(f"{ch_name} revenue: {k['revenue']} vs {real_r}")
        if k['stores'] != real_stores: errors.append(f"{ch_name} stores: {k['stores']} vs {real_stores}")
        if k['models'] != real_models: errors.append(f"{ch_name} models: {k['models']} vs {real_models}")
        if abs(k['ticket'] - real_tk) > 0.1: errors.append(f"{ch_name} ticket: {k['ticket']} vs {real_tk}")

        # Top 5 models
        real_top = sub.groupby('modelo')['Sell Qty'].sum().sort_values(ascending=False)
        real_top = real_top[real_top != 0].head(5)
        dash_models = {m['n']: m['u'] for m in d['models'][:5]}
        for name, val in real_top.items():
            dv = dash_models.get(name)
            if dv is None: errors.append(f"{ch_name} model '{name}' missing")
            elif dv != int(val): errors.append(f"{ch_name} model '{name}': {dv} vs {int(val)}")

        # Zonas
        real_z = sub.groupby('Zona')['Sell Qty'].sum()
        dash_z = {z['n']: z['u'] for z in d['zonas']}
        for name, val in real_z.items():
            dv = dash_z.get(name)
            if dv is not None and dv != int(val):
                errors.append(f"{ch_name} zona '{name}': {dv} vs {int(val)}")

        # Weekly
        real_w = sub.groupby('Semana')['Sell Qty'].sum().sort_index()
        for sem, val in real_w.items():
            dv = d['weekly'].get(str(int(sem)))
            if dv is not None and dv != int(val):
                errors.append(f"{ch_name} S{int(sem)}: {dv} vs {int(val)}")

        # Gamas (str comparison)
        real_g = sub.groupby('gamA')['Sell Qty'].sum()
        real_g = real_g[real_g > 0]
        dash_g = {g['n']: g['u'] for g in d['gamas']}
        for name, val in real_g.items():
            dv = dash_g.get(str(name))
            if dv is not None and dv != int(val):
                errors.append(f"{ch_name} gama '{name}': {dv} vs {int(val)}")

    print("=" * 50)
    if errors:
        print(f"❌ {len(errors)} ERRORES ENCONTRADOS:")
        for e in errors:
            print(f"   {e}")
    else:
        print("✅ TODOS LOS DATOS CORRECTOS — 0 errores")
    print("=" * 50)

    for ch in ['SI','NO','Online','ALL']:
        k = D[ch]['kpis']
        print(f"  {ch:8s}: {k['units']:>5} uds | {k['revenue']:>12.2f} € | TK {k['ticket']:>7.2f}")

    return len(errors) == 0


def main():
    if len(sys.argv) < 3:
        print("USO: python3 -m scripts.validate <data.json> <analisis.xlsx>")
        sys.exit(1)

    success = validate(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
