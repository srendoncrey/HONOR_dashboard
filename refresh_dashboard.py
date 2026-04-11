"""
HONOR Dashboard — Pipeline completo de refresco
=================================================
Ejecuta todo el pipeline: extracción → inyección → validación

USO:
    python3 refresh_dashboard.py

    Con rutas por defecto:
      - Analisis: data/Analisis Honor 2025 (v3).xlsx
      - Horarios: data/Horarios HONOR.xlsx
      - Dashboard: output/HONOR_Dashboard_v5.html

    O con rutas personalizadas:
    python3 refresh_dashboard.py <analisis.xlsx> <horarios.xlsx> <dashboard.html>
"""

import sys
import os
import json

# Asegurar que el directorio raíz del proyecto está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.extract_data import main as extract_main
from scripts.inject_data import inject
from scripts.validate import validate

# Rutas por defecto
DEFAULT_ANALISIS = os.path.join('data', 'Analisis Honor 2025 (v3).xlsx')
DEFAULT_HORARIOS = os.path.join('data', 'Horarios HONOR.xlsx')
DEFAULT_DASHBOARD = os.path.join('output', 'HONOR_Dashboard_v5.html')
DEFAULT_JSON = os.path.join('output', 'dashboard_data.json')


def refresh(analisis_file, horarios_file, html_file):
    print("=" * 60)
    print("HONOR Dashboard — Refresco completo")
    print("=" * 60)

    # Step 1: Extract
    print("\n📊 PASO 1: Extracción de datos...")
    sys.argv = ['', analisis_file, horarios_file, '--output', DEFAULT_JSON]
    data = extract_main()

    # Step 2: Inject into HTML
    print(f"\n💉 PASO 2: Inyectando en {html_file}...")
    inject(DEFAULT_JSON, html_file)

    # Step 3: Validate
    print(f"\n🔍 PASO 3: Validación...")
    success = validate(DEFAULT_JSON, analisis_file)

    # Summary
    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    for ch in ['SI','NO','Online','ALL']:
        k = data[ch]['kpis']
        print(f"  {ch:8s}: {k['units']:>5} uds | {k['revenue']:>12.2f} € | TK {k['ticket']:>7.2f} € | {k['stores']} tiendas")
    print(f"\n  Promotores: {len(data.get('promotores',{}))} tiendas")
    print(f"  Incentivos: {len(data.get('incentivos',[]))} registros")
    print(f"\n  Dashboard: {html_file}")

    return success


if __name__ == '__main__':
    if len(sys.argv) >= 4:
        analisis = sys.argv[1]
        horarios = sys.argv[2]
        dashboard = sys.argv[3]
    elif len(sys.argv) == 1:
        analisis = DEFAULT_ANALISIS
        horarios = DEFAULT_HORARIOS
        dashboard = DEFAULT_DASHBOARD
    else:
        print("USO: python3 refresh_dashboard.py [<analisis.xlsx> <horarios.xlsx> <dashboard.html>]")
        print("")
        print("Sin argumentos usa rutas por defecto:")
        print(f"  Analisis:  {DEFAULT_ANALISIS}")
        print(f"  Horarios:  {DEFAULT_HORARIOS}")
        print(f"  Dashboard: {DEFAULT_DASHBOARD}")
        print("")
        print("También puedes ejecutar los scripts por separado:")
        print("  python3 -m scripts.extract_data <analisis.xlsx> <horarios.xlsx>")
        print("  python3 -m scripts.inject_data <data.json> <dashboard.html>")
        print("  python3 -m scripts.validate <data.json> <analisis.xlsx>")
        sys.exit(1)

    for f in [analisis, horarios, dashboard]:
        if not os.path.exists(f):
            print(f"❌ Archivo no encontrado: {f}")
            sys.exit(1)

    success = refresh(analisis, horarios, dashboard)
    sys.exit(0 if success else 1)
