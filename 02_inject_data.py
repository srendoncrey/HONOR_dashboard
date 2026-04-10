"""
HONOR Dashboard v5 — Script 2: Inyección de datos en HTML
==========================================================
Reemplaza el bloque const D={...}; en el dashboard HTML con datos nuevos.

USO:
    python3 02_inject_data.py dashboard_data.json HONOR_Dashboard_v5.html

SALIDA:
    Actualiza el HTML in-place (hace backup .bak)
"""

import re
import sys
import shutil
import json


def main():
    if len(sys.argv) < 3:
        print("USO: python3 02_inject_data.py <data.json> <dashboard.html>")
        sys.exit(1)

    data_file = sys.argv[1]
    html_file = sys.argv[2]

    # Leer datos
    with open(data_file) as f:
        new_data = f.read()

    # Validar JSON
    try:
        d = json.loads(new_data)
        print(f"✅ JSON válido: {len(new_data):,} chars")
        for ch in ['SI', 'NO', 'Online', 'ALL']:
            if ch in d:
                k = d[ch]['kpis']
                print(f"   {ch:8s}: {k['units']:>5} uds | {k['revenue']:>12.2f} € | TK {k['ticket']:>7.2f}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON inválido: {e}")
        sys.exit(1)

    # Leer HTML
    with open(html_file) as f:
        html = f.read()

    # Buscar y reemplazar const D={...};
    match = re.search(r'const D=\{.*?\};', html, re.DOTALL)
    if not match:
        print("❌ No se encontró 'const D={...};' en el HTML")
        sys.exit(1)

    old_size = len(match.group())
    html = html.replace(match.group(), f'const D={new_data};')

    # Backup
    backup = html_file + '.bak'
    shutil.copy2(html_file, backup)

    # Guardar
    with open(html_file, 'w') as f:
        f.write(html)

    print(f"\n✅ Dashboard actualizado!")
    print(f"   Datos anteriores: {old_size:,} chars")
    print(f"   Datos nuevos:     {len(new_data)+10:,} chars")
    print(f"   Backup en:        {backup}")
    print(f"   HTML total:       {len(html):,} chars")


if __name__ == '__main__':
    main()
