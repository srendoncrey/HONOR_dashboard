"""Builder Agent — Constructs the final dashboard HTML."""

from agents.base import BaseAgent
from agents import tools

SYSTEM = """Eres el Builder Agent del sistema HONOR Dashboard.
Tu rol es construir el dashboard HTML final:
1. Inyectar los datos JSON en el HTML
2. Inyectar los insights generados por el Insights Agent
3. Verificar que el HTML es válido y tiene datos

Responde en español. Reporta el resultado de cada paso."""

TOOLS = [
    {
        "name": "inject_data",
        "description": "Inyecta el JSON de datos en el HTML del dashboard (reemplaza const D={...};)",
        "input_schema": {
            "type": "object",
            "properties": {
                "json_path": {"type": "string", "description": "Ruta al JSON de datos"},
                "html_path": {"type": "string", "description": "Ruta al HTML del dashboard"},
            },
        },
    },
    {
        "name": "inject_insights",
        "description": "Reemplaza los insights en el HTML con nuevos insights generados por IA",
        "input_schema": {
            "type": "object",
            "properties": {
                "html_path": {"type": "string", "description": "Ruta al HTML"},
                "insights_es": {
                    "type": "array",
                    "description": "Array de insights en español [{tag, t, p}]",
                    "items": {"type": "object"},
                },
                "insights_en": {
                    "type": "array",
                    "description": "Array de insights en inglés [{tag, t, p}]",
                    "items": {"type": "object"},
                },
            },
            "required": ["html_path", "insights_es", "insights_en"],
        },
    },
    {
        "name": "verify_html",
        "description": "Verifica que el HTML es válido, tiene datos embebidos y tamaño razonable",
        "input_schema": {
            "type": "object",
            "properties": {
                "html_path": {"type": "string", "description": "Ruta al HTML"},
            },
        },
    },
]


class BuilderAgent(BaseAgent):
    name = "builder"
    system_prompt = SYSTEM
    tool_definitions = TOOLS

    def __init__(self, client):
        super().__init__(client)
        self.register_tool("inject_data", tools.inject_data)
        self.register_tool("inject_insights", tools.inject_insights)
        self.register_tool("verify_html", tools.verify_html)
