"""Data Agent — Extracts and validates data from Excel files."""

from agents.base import BaseAgent
from agents import tools

SYSTEM = """Eres el Data Agent del sistema HONOR Dashboard.
Tu rol es extraer datos de los archivos Excel y validarlos.

Flujo:
1. Usa extract_data para procesar los Excel y generar el JSON
2. Usa validate_data para verificar que los datos son correctos
3. Usa get_data_summary para obtener un resumen estructurado
4. Devuelve el resumen al orquestador

Responde siempre en español. Sé conciso y reporta métricas clave."""

TOOLS = [
    {
        "name": "extract_data",
        "description": "Extrae datos del Excel de análisis y horarios, genera dashboard_data.json",
        "input_schema": {
            "type": "object",
            "properties": {
                "analisis_path": {"type": "string", "description": "Ruta al Excel de análisis (opcional, usa default)"},
                "horarios_path": {"type": "string", "description": "Ruta al Excel de horarios (opcional, usa default)"},
            },
        },
    },
    {
        "name": "validate_data",
        "description": "Valida el JSON generado contra el Excel original",
        "input_schema": {
            "type": "object",
            "properties": {
                "json_path": {"type": "string", "description": "Ruta al JSON (opcional)"},
                "analisis_path": {"type": "string", "description": "Ruta al Excel (opcional)"},
            },
        },
    },
    {
        "name": "get_data_summary",
        "description": "Carga el JSON y devuelve resumen estructurado con KPIs, top modelos, zonas, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "json_path": {"type": "string", "description": "Ruta al JSON (opcional)"},
            },
        },
    },
]


class DataAgent(BaseAgent):
    name = "data"
    system_prompt = SYSTEM
    tool_definitions = TOOLS

    def __init__(self, client):
        super().__init__(client)
        self.register_tool("extract_data", tools.extract_data)
        self.register_tool("validate_data", tools.validate_data)
        self.register_tool("get_data_summary", tools.get_data_summary)
