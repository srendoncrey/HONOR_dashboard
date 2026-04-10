"""
HONOR Dashboard v5 — Script de refresco completo
==================================================
Ejecuta todo el pipeline: extracción → inyección → validación

USO:
    python3 refresh_dashboard.py Analisis_Honor_2025__v3_.xlsx Horarios_HONOR.xlsx HONOR_Dashboard_v5.html

Esto:
1. Extrae datos del Excel (BBDD + Horarios + Incentivos)
2. Serializa a JSON
3. Inyecta en el HTML del dashboard
4. Valida que todo cuadra
"""

import sys
import os
import re
import shutil
import json

# Import the extraction module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_data_01 import main as extract_main, get_channel_metrics, parse_horarios, parse_incentivos
from extract_data_01 import HORARIOS_SHEETS, HORARIOS_STORE_MAP, INCENTIVOS_SHEETS
import pandas as pd


def refresh(analisis_file, horarios_file, html_file):
    print("=" * 60)
    print("HONOR Dashboard v5 — Refresco completo")
    print("=" * 60)

    # Step 1: Extract
    print("\n📊 PASO 1: Extracción de datos...")
    sys.argv = ['', analisis_file, horarios_file]
    data = extract_main()

    # Step 2: Serialize
    data_json = json.dumps(data, separators=(',',':'))
    print(f"\n📦 PASO 2: JSON generado ({len(data_json):,} chars)")

    # Step 3: Inject into HTML
    print(f"\n💉 PASO 3: Inyectando en {html_file}...")
    with open(html_file) as f:
        html = f.read()

    match = re.search(r'const D=\{.*?\};', html, re.DOTALL)
    if not match:
        print("❌ No se encontró 'const D={...};' en el HTML")
        return False

    old_size = len(match.group())
    html = html.replace(match.group(), f'const D={data_json};')

    # Backup
    backup = html_file + '.bak'
    shutil.copy2(html_file, backup)
    with open(html_file, 'w') as f:
        f.write(html)
    print(f"   Datos: {old_size:,} → {len(data_json)+10:,} chars")
    print(f"   Backup: {backup}")

    # Step 4: Validate
    print(f"\n✅ PASO 4: Validación...")
    df = pd.read_excel(analisis_file, sheet_name='BBDD')
    filt = df[df['Año'] == 2026]
    
    errors = 0
    for ch, fltr in [('SI','SI'),('NO','NO'),('Online','Online'),('ALL',None)]:
        sub = filt if fltr is None else filt[filt['Promotor']==fltr]
        k = data[ch]['kpis']
        real_u = int(sub['Sell Qty'].sum())
        real_r = round(sub['Sales Value'].sum(), 2)
        if k['units'] != real_u:
            print(f"   ❌ {ch} units: {k['units']} vs {real_u}")
            errors += 1
        if abs(k['revenue'] - real_r) > 1:
            print(f"   ❌ {ch} revenue: {k['revenue']} vs {real_r}")
            errors += 1

    if errors == 0:
        print("   ✅ Validación OK — 0 errores")
    else:
        print(f"   ❌ {errors} errores encontrados")

    # Summary
    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    for ch in ['SI','NO','Online','ALL']:
        k = data[ch]['kpis']
        print(f"  {ch:8s}: {k['units']:>5} uds | {k['revenue']:>12.2f} € | TK {k['ticket']:>7.2f} € | {k['stores']} tiendas")
    print(f"\n  Promotores: {len(data.get('promotores',{}))} tiendas")
    print(f"  Incentivos: {len(data.get('incentivos',[]))} registros")
    print(f"\n  Dashboard: {html_file} ({len(html):,} bytes)")
    
    return errors == 0


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("USO: python3 refresh_dashboard.py <analisis.xlsx> <horarios.xlsx> <dashboard.html>")
        print("")
        print("También puedes ejecutar los scripts por separado:")
        print("  python3 01_extract_data.py <analisis.xlsx> <horarios.xlsx>")
        print("  python3 02_inject_data.py dashboard_data.json <dashboard.html>")
        print("  python3 03_validate.py dashboard_data.json <analisis.xlsx>")
        sys.exit(1)

    success = refresh(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.exit(0 if success else 1)
