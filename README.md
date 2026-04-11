# HONOR Dashboard — Scripts de Generacion

Pipeline para generar dashboards de ventas HONOR (El Corte Ingles) a partir de datos Excel.
Auto-detecta todos los meses disponibles en los archivos de entrada.

## Estructura

```
HONOR_dashboard/
├── data/                              # Archivos Excel de entrada
│   ├── Analisis Honor 2025 (v3).xlsx  # BBDD ventas + incentivos
│   └── Horarios HONOR.xlsx            # Horarios promotores
├── scripts/                           # Modulos Python
│   ├── extract_data.py                # Extrae datos del Excel → JSON
│   ├── inject_data.py                 # Inyecta JSON en el HTML del dashboard
│   └── validate.py                    # Valida datos JSON vs Excel original
├── output/                            # Archivos generados
│   └── HONOR_Dashboard_v5.html        # Dashboard HTML
├── refresh_dashboard.py               # Pipeline completo (un solo comando)
├── requirements.txt
└── .gitignore
```

## Uso rapido (refresco completo)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar pipeline completo (usa rutas por defecto)
python3 refresh_dashboard.py
```

Esto ejecuta:
1. Lee BBDD, Horarios e Incentivos del Excel (auto-detecta meses)
2. Serializa a JSON
3. Inyecta en el HTML (con backup automatico .bak)
4. Valida que todos los datos cuadran

Con rutas personalizadas:
```bash
python3 refresh_dashboard.py <analisis.xlsx> <horarios.xlsx> <dashboard.html>
```

## Uso paso a paso

### Paso 1: Extraer datos
```bash
python3 -m scripts.extract_data "data/Analisis Honor 2025 (v3).xlsx" "data/Horarios HONOR.xlsx"
# → Genera output/dashboard_data.json
```

### Paso 2: Inyectar en HTML
```bash
python3 -m scripts.inject_data output/dashboard_data.json output/HONOR_Dashboard_v5.html
# → Actualiza el HTML in-place (backup .bak)
```

### Paso 3: Validar
```bash
python3 -m scripts.validate output/dashboard_data.json "data/Analisis Honor 2025 (v3).xlsx"
# → Comprueba que todos los datos cuadran
```

## Dependencias

```bash
pip install -r requirements.txt
```

Requiere: `pandas >= 2.0`, `openpyxl >= 3.1`

## Reglas de datos importantes

| Regla | Detalle |
|-------|---------|
| **Ticket medio** | Siempre `facturacion / unidades`, NUNCA promediar la columna Ticket Medio |
| **Gama (gamA)** | Usar `str()` para comparaciones — puede ser int 400 o string '400' |
| **Horarios → BBDD** | Mapeo de nombres obligatorio (ver `HORARIOS_STORE_MAP` en extract_data.py) |
| **Meses** | Se auto-detectan las hojas disponibles en los Excel (soporta todo el ano) |

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
    "weekly": { "1": 302, "2": 256 },
    "weeklyRev": { "1": 92000 },
    "semZona": { "Centro": [110, 76] },
    "semGama": { "400": [179, 152] },
    "dias": [{ "n": "Lunes", "u": 362 }],
    "map": [{ "n", "z", "u", "f", "lat", "lon" }],
    "semTienda": { "ECI STORE": { "1": 20 } },
    "semTiendaRev": { "ECI STORE": { "1": 6000 } }
  },
  "NO": {},
  "Online": {},
  "ALL": {},
  "promotores": {
    "ECI STORE": { "workDays", "totalDays", "hours", "sales", "revenue", "salesPerWorkDay", "salesPerHour" }
  },
  "incentivos": [
    { "store", "month", "target", "so", "pct" }
  ]
}
```
