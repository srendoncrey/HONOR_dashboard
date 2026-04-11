"""Deploy Agent — Commits and pushes dashboard to GitHub."""

from agents.base import BaseAgent
from agents import tools

SYSTEM = """Eres el Deploy Agent del sistema HONOR Dashboard.
Tu rol es subir el dashboard actualizado a GitHub:
1. Commit de los archivos de output
2. Push al remote
3. Reportar el resultado

Responde en español. Indica si el push fue exitoso o si hubo errores."""

TOOLS = [
    {
        "name": "git_commit_and_push",
        "description": "Hace git add output/, commit y push al remote",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Mensaje del commit"},
            },
        },
    },
    {
        "name": "verify_html",
        "description": "Verifica que el HTML existe y tiene datos antes del deploy",
        "input_schema": {
            "type": "object",
            "properties": {
                "html_path": {"type": "string", "description": "Ruta al HTML"},
            },
        },
    },
]


class DeployAgent(BaseAgent):
    name = "deploy"
    system_prompt = SYSTEM
    tool_definitions = TOOLS

    def __init__(self, client):
        super().__init__(client)
        self.register_tool("git_commit_and_push", tools.git_commit_and_push)
        self.register_tool("verify_html", tools.verify_html)
