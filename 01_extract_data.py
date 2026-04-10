"""
HONOR Dashboard v5 — Script 1: Extracción de datos
===================================================
Extrae todos los datos del Excel y genera un JSON para inyectar en el dashboard.

USO:
    python3 01_extract_data.py Analisis_Honor_2025__v3_.xlsx Horarios_HONOR.xlsx

SALIDA:
    dashboard_data.json
"""

import pandas as pd
import json
import sys
import os

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

HORARIOS_SHEETS = ['ENERO 26', 'FEB 2026', 'MAR 2026']
INCENTIVOS_SHEETS = [('INCENTIVOS ENERO ', 'Enero'), ('INCENTIVOS FEBRERO', 'Febrero'), ('INCENTIVOS MARZO', 'Marzo')]
DIA_ORDER = ['lunes','martes','miércoles','jueves','viernes','sábado','domingo']
MES_ORDER = {'enero':1,'febrero':2,'marzo':3}


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
    """Parsea una hoja de incentivos."""
    inc = pd.read_excel(xls_a, sheet_name=sheet, header=None)
    results = []
    for r in range(5, inc.shape[0]):
        tienda = inc.iloc[r, 0]
        if pd.isna(tienda) or 'TOTAL' in str(tienda).upper():
            continue
        tgt = inc.iloc[r, 1]
        if pd.isna(tgt) or not isinstance(tgt, (int, float)):
            continue
        if month == 'Marzo':
            so = inc.iloc[r, 6] if pd.notna(inc.iloc[r, 6]) else 0
            pct = inc.iloc[r, 7] if pd.notna(inc.iloc[r, 7]) else 0
        else:
            e_so = inc.iloc[r, 7] if 7 < inc.shape[1] and pd.notna(inc.iloc[r, 7]) else 0
            m_so = inc.iloc[r, 11] if 11 < inc.shape[1] and pd.notna(inc.iloc[r, 11]) else 0
            h_so = inc.iloc[r, 15] if 15 < inc.shape[1] and pd.notna(inc.iloc[r, 15]) else 0
            so = sum(v for v in [e_so, m_so, h_so] if isinstance(v, (int, float)))
            pct = so / tgt if tgt > 0 else 0
        results.append({
            'store': str(tienda).strip(), 'month': month,
            'target': int(tgt), 'so': int(so) if isinstance(so,(int,float)) else 0,
            'pct': round(float(pct), 3) if isinstance(pct,(int,float)) else 0
        })
    return results


def main():
    if len(sys.argv) < 3:
        print("USO: python3 01_extract_data.py <analisis_honor.xlsx> <horarios.xlsx>")
        print("     Genera dashboard_data.json")
        sys.exit(1)

    analisis_file = sys.argv[1]
    horarios_file = sys.argv[2]

    print(f"Leyendo {analisis_file}...")
    df = pd.read_excel(analisis_file, sheet_name='BBDD')
    filt = df[df['Año'] == 2026].copy()
    print(f"  {len(filt)} registros 2026")

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
    h_all = []
    for s in HORARIOS_SHEETS:
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
    inc_all = []
    for sheet, month in INCENTIVOS_SHEETS:
        inc_all.extend(parse_incentivos(xls_a, sheet, month))
    data['incentivos'] = inc_all
    print(f"  {len(inc_all)} registros de incentivos")

    # ===== GUARDAR =====
    output = 'dashboard_data.json'
    with open(output, 'w') as f:
        json.dump(data, f, separators=(',',':'))
    
    print(f"\n✅ Datos guardados en {output} ({os.path.getsize(output):,} bytes)")
    return data


if __name__ == '__main__':
    main()
