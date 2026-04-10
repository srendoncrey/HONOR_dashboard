# HONOR Dashboard v5 — Scripts de Generación

## Estructura

```
honor_scripts/
├── 01_extract_data.py      # Extrae datos del Excel → JSON
├── 02_inject_data.py       # Inyecta JSON en el HTML del dashboard
├── 03_validate.py          # Valida datos JSON vs Excel original
├── refresh_dashboard.py    # Pipeline completo (1+2+3 en un solo comando)
└── README.md               # Este archivo
```

## Uso rápido (refresco completo)

```bash
python3 refresh_dashboard.py \
    Analisis_Honor_2025__v3_.xlsx \
    Horarios_HONOR.xlsx \
    HONOR_Dashboard_v5.html
```

Esto ejecuta todo el pipeline:
1. Lee BBDD, Horarios e Incentivos del Excel
2. Serializa a JSON
3. Inyecta en el HTML (con backup automático .bak)
4. Valida que todos los datos cuadran

## Uso paso a paso

### Paso 1: Extraer datos
```bash
python3 01_extract_data.py Analisis_Honor_2025__v3_.xlsx Horarios_HONOR.xlsx
# → Genera dashboard_data.json
```

### Paso 2: Inyectar en HTML
```bash
python3 02_inject_data.py dashboard_data.json HONOR_Dashboard_v5.html
# → Actualiza el HTML in-place (backup .bak)
```

### Paso 3: Validar
```bash
python3 03_validate.py dashboard_data.json Analisis_Honor_2025__v3_.xlsx
# → Comprueba que todos los datos cuadran
```

## Dependencias

```bash
pip install pandas openpyxl
```

## Reglas de datos importantes

| Regla | Detalle |
|-------|---------|
| **Ticket medio** | Siempre `facturación / unidades`, NUNCA promediar la columna Ticket Medio |
| **Gama (gamA)** | Usar `str()` para comparaciones — puede ser int 400 o string '400' |
| **Horarios → BBDD** | Mapeo de nombres obligatorio (ver `HORARIOS_STORE_MAP` en el script) |
| **BBDD vs SEGUIMIENTO** | BBDD puede tener semana parcial. SEGUIMIENTO tiene datos más completos |

## Estructura del JSON generado

```json
{
  "SI": {
    "kpis": { "units", "revenue", "stores", "models", "ticket", "weeks", "avgWeek" },
    "models": [{ "n", "u", "f" }],
    "zonas": [{ "n", "u", "f" }],
    "gamas": [{ "n", "u", "f" }],
    "cats": [{ "n", "u", "f" }],
    "meses": [{ "n", "u", "f" }],
    "tiendas": [{ "n", "z", "u", "f" }],
    "weekly": { "1": 302, "2": 256, ... },
    "weeklyRev": { "1": 92000, ... },
    "semZona": { "Centro": [110, 76, ...], ... },
    "semGama": { "400": [179, 152, ...], ... },
    "dias": [{ "n": "Lunes", "u": 362 }, ...],
    "map": [{ "n", "z", "u", "f", "lat", "lon" }],
    "semTienda": { "ECI STORE": { "1": 20, ... } },
    "semTiendaRev": { "ECI STORE": { "1": 6000, ... } }
  },
  "NO": { ... },
  "Online": { ... },
  "ALL": { ... },
  "promotores": {
    "ECI STORE": { "workDays", "totalDays", "hours", "sales", "revenue", "salesPerWorkDay", "salesPerHour" }
  },
  "incentivos": [
    { "store", "month", "target", "so", "pct" }
  ]
}
```
