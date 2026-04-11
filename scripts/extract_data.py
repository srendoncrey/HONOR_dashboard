"""
HONOR Dashboard — Script 1: Extracción de datos
=================================================
Extrae todos los datos del Excel y genera un JSON para inyectar en el dashboard.
Soporta todos los meses del año (auto-detecta hojas disponibles).

USO:
    python3 -m scripts.extract_data data/analisis.xlsx data/horarios.xlsx
    python3 -m scripts.extract_data data/analisis.xlsx data/horarios.xlsx --output output/dashboard_data.json

SALIDA:
    output/dashboard_data.json (por defecto)
"""

import pandas as pd
import json
import sys
import os
import re

# ===== CONFIGURACIÓN =====
STORE_COORDS = {
    'ECI GUADALAJARA': (40.621,-3.162), 'ECI TALAVERA': (39.96,-4.833),
    'ECI PAMPLONA': (42.812,-1.645), 'ECI SAN JOSE VALDERAS': (40.346,-3.851),
    'ECI ZARAGOZA': (41.649,-0.887), 'ECI LA CORUÑA': (43.371,-8.396),
    'ECI PLAZA DEL DUQUE': (37.393,-5.994), 'ECI RONDA DE CORDOBA': (37.884,-4.779),
    'ECI SALAMANCA': (40.965,-5.664), 'ECI LEON': (42.598,-5.567),
    'ECI COSTA LUZ': (36.679,-6.13), 'ECI COSTA MIJAS': (36.595,-4.637),
    'ECI BAHIA MALAGA': (36.695,-4.445), 'ECI CORNELLA': (41.354,2.07),
    'ECI ALCALA DE HENARES': (40.482,-3.364)
}

HORARIOS_STORE_MAP = {
    'ECI A CORUÑA': 'ECI LA CORUÑA',
    'ECI BAHÍA MÁLAGA': 'ECI BAHIA MALAGA',
    'ECI CORNELLÁ': 'ECI CORNELLA',
    'ECI HUELVA': 'ECI COSTA LUZ',
    'ECI LEÓN': 'ECI LEON',
    'ECI RONDA CÓRDOBA': 'ECI RONDA DE CORDOBA',
    'ECI SAN JOSÉ DE VALDERAS': 'ECI SAN JOSE VALDERAS',
    'ECI ZARAGOZA ( SAGASTA)': 'ECI ZARAGOZA',
    'ECI ÁLCALA DE HENARES': 'ECI ALCALA DE HENARES'
}

DIA_ORDER = ['lunes','martes','miércoles','jueves','viernes','sábado','domingo']

MES_ORDER = {
    'enero':1, 'febrero':2, 'marzo':3, 'abril':4, 'mayo':5, 'junio':6,
    'julio':7, 'agosto':8, 'septiembre':9, 'octubre':10, 'noviembre':11, 'diciembre':12
}

# Patrones para auto-detectar hojas de horarios e incentivos
_HORARIO_PATTERN = re.compile(
    r'(ENERO|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)', re.IGNORECASE
)
_INCENTIVO_PATTERN = re.compile(
    r'INCENTIVOS?\s+(ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)',
    re.IGNORECASE
)
_MONTH_ABBR_TO_FULL = {
    'ENERO': 'Enero', 'FEB': 'Febrero', 'MAR': 'Marzo', 'ABR': 'Abril',
    'MAY': 'Mayo', 'JUN': 'Junio', 'JUL': 'Julio', 'AGO': 'Agosto',
    'SEP': 'Septiembre', 'OCT': 'Octubre', 'NOV': 'Noviembre', 'DIC': 'Diciembre',
    'FEBRERO': 'Febrero', 'MARZO': 'Marzo', 'ABRIL': 'Abril', 'MAYO': 'Mayo',
    'JUNIO': 'Junio', 'JULIO': 'Julio', 'AGOSTO': 'Agosto',
    'SEPTIEMBRE': 'Septiembre', 'OCTUBRE': 'Octubre', 'NOVIEMBRE': 'Noviembre',
    'DICIEMBRE': 'Diciembre'
}


def detect_horario_sheets(xls):
    """Auto-detecta hojas de horarios en el Excel.
    Si hay variantes de un mismo mes (e.g. DICIEMBRE V1, V2), usa la ultima."""
    by_month = {}
    for name in xls.sheet_names:
        upper = name.upper()
        if _HORARIO_PATTERN.search(name) and 'INCENTIVO' not in upper and 'PREVISION' not in upper:
            order = _sheet_month_order(name)
            # Si ya hay una hoja para este mes, quedarse con la ultima (V2 > V1)
            if order not in by_month or name > by_month[order]:
                by_month[order] = name
    return [by_month[k] for k in sorted(by_month.keys())]


def detect_incentivo_sheets(xls):
    """Auto-detecta hojas de incentivos en el Excel.
    Excluye hojas de PREVISION y si hay duplicados por mes, usa la primera."""
    by_month = {}
    for name in xls.sheet_names:
        upper = name.upper()
        if 'PREVISION' in upper:
            continue
        m = _INCENTIVO_PATTERN.search(name)
        if m:
            month_full = _MONTH_ABBR_TO_FULL.get(m.group(1).upper(), m.group(1).capitalize())
            order = MES_ORDER.get(month_full.lower(), 99)
            if order not in by_month:
                by_month[order] = (name, month_full)
    return [by_month[k] for k in sorted(by_month.keys())]


def _sheet_month_order(sheet_name):
    """Devuelve el orden numerico del mes de una hoja."""
    upper = sheet_name.upper()
    for abbr, full in _MONTH_ABBR_TO_FULL.items():
        if abbr in upper:
            return MES_ORDER.get(full.lower(), 99)
    return 99


def get_channel_metrics(d):
    """Calcula todas las métricas para un subset de datos (canal)."""
    total_u = int(d['Sell Qty'].sum())
    total_r = round(d['Sales Value'].sum(), 2)
    tiendas = int(d['Tienda Honor'].nunique())
    vp = d[d['Sell Qty'] > 0]
    modelos = int(vp['modelo'].nunique())
    # IMPORTANTE: ticket = facturación / unidades (NO promediar columna Ticket Medio)
    ticket = round(total_r / total_u, 2) if total_u > 0 else 0
    semanas = int(d['Semana'].nunique())
    media_sem = round(total_u / semanas) if semanas > 0 else 0

    # Modelos
    m = d.groupby('modelo').agg(u=('Sell Qty','sum'), f=('Sales Value','sum')).sort_values('u', ascending=False)
    m = m[m['u'] != 0]
    models = [{'n': str(name), 'u': int(r['u']), 'f': round(r['f'])} for name, r in m.iterrows()]

    # Zonas
    z = d.groupby('Zona').agg(u=('Sell Qty','sum'), f=('Sales Value','sum')).sort_values('u', ascending=False)
    zonas = [{'n': name, 'u': int(r['u']), 'f': round(r['f'])} for name, r in z.iterrows()]

    # Gamas (usar str() para comparación — gamA puede ser int 400 o string)
    g = d.groupby('gamA').agg(u=('Sell Qty','sum'), f=('Sales Value','sum')).sort_values('u', ascending=False)
    g = g[g['u'] > 0]
    gamas = [{'n': str(name), 'u': int(r['u']), 'f': round(r['f'])} for name, r in g.iterrows()]

    # Categorías
    c = d.groupby('Categoria Honor').agg(u=('Sell Qty','sum'), f=('Sales Value','sum')).sort_values('u', ascending=False)
    c = c[c['u'] > 0]
    cats = [{'n': str(name), 'u': int(r['u']), 'f': round(r['f'])} for name, r in c.iterrows()]

    # Meses (ordenados)
    me = d.groupby('Mes').agg(u=('Sell Qty','sum'), f=('Sales Value','sum'))
    me['ord'] = me.index.map(MES_ORDER)
    me = me.sort_values('ord')
    meses = [{'n': name.capitalize(), 'u': int(r['u']), 'f': round(r['f'])} for name, r in me.iterrows()]

    # Tiendas
    t = d.groupby('Tienda Honor').agg(u=('Sell Qty','sum'), f=('Sales Value','sum')).sort_values('u', ascending=False)
    zona_map = d.drop_duplicates('Tienda Honor')[['Tienda Honor','Zona']].set_index('Tienda Honor')['Zona'].to_dict()
    tiendas_list = [{'n': name, 'z': zona_map.get(name,''), 'u': int(r['u']), 'f': round(r['f'])} for name, r in t.iterrows()]

    # Semanal
    s = d.groupby('Semana')['Sell Qty'].sum().sort_index()
    weekly = {int(k): int(v) for k, v in s.items()}
    sr = d.groupby('Semana')['Sales Value'].sum().sort_index()
    weekly_rev = {int(k): round(v) for k, v in sr.items()}

    # Semana × Zona
    sz = d.pivot_table(index='Semana', columns='Zona', values='Sell Qty', aggfunc='sum', fill_value=0)
    sem_zona = {col: [int(v) for v in sz[col].tolist()] for col in sz.columns}

    # Semana × Gama
    sg = d.pivot_table(index='Semana', columns='gamA', values='Sell Qty', aggfunc='sum', fill_value=0)
    sem_gama = {str(col): [int(v) for v in sg[col].tolist()] for col in sg.columns if sg[col].sum() > 5}

    # Días de la semana
    dd = d.groupby('dia')['Sell Qty'].sum()
    dias = [{'n': dia.capitalize(), 'u': int(dd.get(dia, 0))} for dia in DIA_ORDER]

    # Mapa (coordenadas)
    map_data = []
    for item in tiendas_list:
        coords = STORE_COORDS.get(item['n'], (40.4, -3.7))
        map_data.append({**item, 'lat': coords[0], 'lon': coords[1]})

    # Semana × Tienda
    st = d.pivot_table(index='Semana', columns='Tienda Honor', values='Sell Qty', aggfunc='sum', fill_value=0)
    sem_tienda = {col: {int(k): int(v) for k,v in st[col].items()} for col in st.columns}
    st_r = d.pivot_table(index='Semana', columns='Tienda Honor', values='Sales Value', aggfunc='sum', fill_value=0)
    sem_tienda_rev = {col: {int(k): round(v) for k,v in st_r[col].items()} for col in st_r.columns}

    return {
        'kpis': {'units': total_u, 'revenue': total_r, 'stores': tiendas, 'models': modelos,
                 'ticket': ticket, 'weeks': semanas, 'avgWeek': media_sem},
        'models': models, 'zonas': zonas, 'gamas': gamas, 'cats': cats,
        'meses': meses, 'tiendas': tiendas_list, 'weekly': weekly, 'weeklyRev': weekly_rev,
        'semZona': sem_zona, 'semGama': sem_gama, 'dias': dias, 'map': map_data,
        'semTienda': sem_tienda, 'semTiendaRev': sem_tienda_rev
    }


def parse_horarios(xls_h, sheet_name):
    """Parsea una hoja de horarios y devuelve registros por tienda y día."""
    h = pd.read_excel(xls_h, sheet_name=sheet_name, header=None)
    records = []
    current_week = None
    dates_row = None
    for r in range(h.shape[0]):
        row = h.iloc[r]
        val0 = str(row[0]) if pd.notna(row[0]) else ''
        if val0.startswith('W') or val0.startswith('w'):
            current_week = val0.strip()
            continue
        if pd.notna(row[1]) and ('Lunes' in str(row[1]) or '2026' in str(row[1]) or '2025' in str(row[1])):
            dates_row = [row[c] if c < len(row) and pd.notna(row[c]) else None for c in [1,3,5,7,9,11]]
            continue
        store = str(row[0]).strip() if pd.notna(row[0]) else ''
        if store.startswith('ECI') and dates_row:
            for i, c_s in enumerate([1,3,5,7,9,11]):
                c_h = c_s + 1
                if c_s < len(row) and c_h < len(row):
                    sched = str(row[c_s]) if pd.notna(row[c_s]) else ''
                    hours = float(row[c_h]) if pd.notna(row[c_h]) else 0
                    is_working = sched not in ['LIBRE','VACACIONES','nan','','FESTIVO','FESTIVO (cierre)'] and hours > 0
                    records.append({'store': store, 'day_idx': i, 'hours': hours, 'working': is_working})
    return records


def parse_incentivos(xls_a, sheet, month):
    """Parsea una hoja de incentivos.

    Detecta dinámicamente el formato de la hoja:
    - 'total_mes': hay columna 'TOTAL MES' en fila 3 → SO y % en esa columna
    - 'tiered': formato Entry/Mid/High → suma SOs de cols 7, 11, 15

    Deduplica por tienda: si la hoja tiene dos bloques de datos (ej. FEBRERO),
    conserva el último registro de cada tienda (datos más actualizados).
    """
    inc = pd.read_excel(xls_a, sheet_name=sheet, header=None)
    fmt, so_col = _detect_incentivo_format(inc)
    seen = {}  # store -> record (first valid occurrence wins)
    for r in range(5, inc.shape[0]):
        tienda = inc.iloc[r, 0]
        if pd.isna(tienda) or 'TOTAL' in str(tienda).upper():
            continue
        tienda = str(tienda).strip()
        if not tienda.startswith('ECI'):
            continue
        tgt = inc.iloc[r, 1]
        if pd.isna(tgt) or not isinstance(tgt, (int, float)):
            continue
        if fmt == 'total_mes':
            so = inc.iloc[r, so_col] if so_col < inc.shape[1] and pd.notna(inc.iloc[r, so_col]) else 0
            pct = inc.iloc[r, so_col + 1] if (so_col + 1) < inc.shape[1] and pd.notna(inc.iloc[r, so_col + 1]) else 0
        else:
            # Tiered: sum all individual SO columns
            so_vals = []
            for c in so_col:
                v = inc.iloc[r, c] if c < inc.shape[1] and pd.notna(inc.iloc[r, c]) else 0
                if isinstance(v, (int, float)):
                    so_vals.append(v)
            so = sum(so_vals)
            pct = so / float(tgt) if tgt > 0 else 0
        # Keep first valid occurrence (block 1 has complete data)
        if tienda in seen:
            continue
        seen[tienda] = {
            'store': tienda, 'month': month,
            'target': int(tgt), 'so': int(so) if isinstance(so, (int, float)) else 0,
            'pct': round(float(pct), 3) if isinstance(pct, (int, float)) else 0
        }
    return list(seen.values())


def _detect_incentivo_format(inc):
    """Detecta el formato y columna SO de una hoja de incentivos.

    Si la fila 3 tiene cabeceras 'Entry'/'Mid'/'High' → tiered (suma SOs individuales).
    Si NO tiene tiers y tiene 'TOTAL' con 'SO' debajo → total_mes (SO directo).
    Devuelve ('total_mes', so_col) o ('tiered', so_cols_list).
    """
    if inc.shape[0] <= 3:
        return ('tiered', [7, 11, 15])

    # Check for tiered headers (Entry/Mid/High)
    has_tiers = False
    for c in range(inc.shape[1]):
        cell = str(inc.iloc[3, c]).strip().upper()
        if cell in ('ENTRY', 'MID', 'HIGH'):
            has_tiers = True
            break

    if has_tiers:
        # Find ALL individual SO columns (row 4 = 'SO', row 3 != 'TOTAL')
        so_cols = []
        for c in range(inc.shape[1]):
            r4 = str(inc.iloc[4, c]).strip().upper() if inc.shape[0] > 4 else ''
            r3 = str(inc.iloc[3, c]).strip().upper()
            if r4 == 'SO' and 'TOTAL' not in r3:
                so_cols.append(c)
        return ('tiered', so_cols if so_cols else [7, 11, 15])

    # No tiers → look for TOTAL MES format
    for c in range(inc.shape[1]):
        cell = str(inc.iloc[3, c]).strip().upper()
        if 'TOTAL' in cell and 'PREVISION' not in cell:
            if inc.shape[0] > 4 and 'SO' in str(inc.iloc[4, c]).upper():
                return ('total_mes', c)

    return ('tiered', [7, 11, 15])


def main():
    if len(sys.argv) < 3:
        print("USO: python3 -m scripts.extract_data <analisis_honor.xlsx> <horarios.xlsx> [--output FILE]")
        print("     Genera output/dashboard_data.json por defecto")
        sys.exit(1)

    analisis_file = sys.argv[1]
    horarios_file = sys.argv[2]
    output = 'output/dashboard_data.json'
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output = sys.argv[idx + 1]

    print(f"Leyendo {analisis_file}...")
    df = pd.read_excel(analisis_file, sheet_name='BBDD')
    # Usar el año más reciente disponible en el BBDD
    latest_year = int(df['Año'].max())
    filt = df[df['Año'] == latest_year].copy()
    print(f"  {len(filt)} registros {latest_year}")

    # ===== CANALES =====
    channels = {
        'SI': filt[filt['Promotor']=='SI'],
        'NO': filt[filt['Promotor']=='NO'],
        'Online': filt[filt['Promotor']=='Online']
    }

    data = {}
    for ch_name, subset in channels.items():
        data[ch_name] = get_channel_metrics(subset)
        k = data[ch_name]['kpis']
        print(f"  {ch_name:8s}: {k['units']:>5} uds | {k['revenue']:>12.2f} € | TK {k['ticket']:>7.2f}")

    data['ALL'] = get_channel_metrics(filt)
    k = data['ALL']['kpis']
    print(f"  {'ALL':8s}: {k['units']:>5} uds | {k['revenue']:>12.2f} € | TK {k['ticket']:>7.2f}")

    # ===== HORARIOS =====
    print(f"\nLeyendo {horarios_file}...")
    xls_h = pd.ExcelFile(horarios_file)
    horario_sheets = detect_horario_sheets(xls_h)
    print(f"  Hojas de horarios detectadas: {horario_sheets}")
    h_all = []
    for s in horario_sheets:
        h_all.extend(parse_horarios(xls_h, s))
    horarios_df = pd.DataFrame(h_all)
    horarios_df['bbdd_store'] = horarios_df['store'].map(lambda x: HORARIOS_STORE_MAP.get(x, x))

    si = filt[filt['Promotor'] == 'SI']
    promo_data = {}
    for store_b in si['Tienda Honor'].unique():
        h_store = horarios_df[horarios_df['bbdd_store'] == store_b]
        working_days = int(h_store['working'].sum())
        total_days = len(h_store)
        total_hours = float(h_store['hours'].sum())
        store_sales = si[si['Tienda Honor'] == store_b]
        total_sales = int(store_sales['Sell Qty'].sum())
        total_rev = round(store_sales['Sales Value'].sum())
        promo_data[store_b] = {
            'workDays': working_days, 'totalDays': total_days, 'hours': round(total_hours),
            'sales': total_sales, 'revenue': total_rev,
            'salesPerWorkDay': round(total_sales / working_days, 1) if working_days > 0 else 0,
            'salesPerHour': round(total_sales / total_hours, 2) if total_hours > 0 else 0
        }
    data['promotores'] = promo_data
    print(f"  {len(promo_data)} tiendas promotor procesadas")

    # ===== INCENTIVOS =====
    print("Procesando incentivos...")
    xls_a = pd.ExcelFile(analisis_file)
    incentivo_sheets = detect_incentivo_sheets(xls_a)
    print(f"  Hojas de incentivos detectadas: {[(s, m) for s, m in incentivo_sheets]}")
    inc_all = []
    # Only include months from the latest year (skip Nov/Dec from previous year)
    meses_2026 = {'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                  'Julio', 'Agosto', 'Septiembre', 'Octubre'}
    for sheet, month in incentivo_sheets:
        if month in meses_2026:
            inc_all.extend(parse_incentivos(xls_a, sheet, month))
    data['incentivos'] = inc_all
    print(f"  {len(inc_all)} registros de incentivos")

    # ===== GUARDAR =====
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, 'w') as f:
        json.dump(data, f, separators=(',',':'))

    print(f"\n✅ Datos guardados en {output} ({os.path.getsize(output):,} bytes)")
    return data


if __name__ == '__main__':
    main()
