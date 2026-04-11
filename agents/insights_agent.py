"""Insights Agent — Generates analytical insights using Claude."""

import json
from agents.base import BaseAgent

SYSTEM = """Eres el Insights Agent del sistema HONOR Dashboard.
Tu rol es analizar los datos de ventas de HONOR (móviles) en El Corte Inglés
y generar 7 insights clave para el dashboard.

Cuando recibas datos via la tool analyze_data, genera exactamente 7 insights.
Cada insight debe tener:
- tag: categoría corta (ej: "Concentración", "Rentabilidad", "Estacionalidad")
- t: título con dato clave (ej: "Top 3 modelos = 55% de las ventas")
- p: párrafo explicativo con datos concretos y recomendación accionable

Los insights deben cubrir:
1. Concentración de modelos (qué modelos dominan las ventas)
2. Rentabilidad (ticket medio, facturación por gama)
3. Estacionalidad/tendencia semanal (picos y valles)
4. Geografía/zonas (qué zonas van bien o mal)
5. Patrón diario (qué días de la semana venden más)
6. Ticket medio (comparativa entre gamas/modelos)
7. Tienda líder (top performers y recomendaciones)

USA SOLO los datos que te proporcionen. No inventes números.
Genera insights en español (ES) y en inglés (EN).

Devuelve el resultado como JSON con este formato:
{"es": [7 insights], "en": [7 insights]}"""

TOOLS = [
    {
        "name": "analyze_data",
        "description": "Recibe el resumen de datos del dashboard para análisis. Devuelve los datos crudos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data_summary": {"type": "string", "description": "JSON string con el resumen de datos"},
            },
            "required": ["data_summary"],
        },
    },
]


class InsightsAgent(BaseAgent):
    name = "insights"
    model = "claude-sonnet-4-6"
    system_prompt = SYSTEM
    tool_definitions = TOOLS

    def __init__(self, client):
        super().__init__(client)
        self.register_tool("analyze_data", lambda data_summary: data_summary)

    def generate(self, data_summary: dict) -> dict:
        """Generate insights from data summary. Returns {es: [...], en: [...]}."""
        summary_str = json.dumps(data_summary, ensure_ascii=False, indent=2)

        prompt = f"""Analiza estos datos del dashboard HONOR Q1 2026 y genera 7 insights.

DATOS:
{summary_str}

Genera exactamente 7 insights en español y 7 en inglés.
Responde SOLO con JSON válido en este formato (sin markdown, sin ```):
{{"es": [{{"tag": "...", "t": "...", "p": "..."}}, ...], "en": [{{"tag": "...", "t": "...", "p": "..."}}, ...]}}"""

        response = self.client.messages.create(
            model=self.model,
            system=self.system_prompt,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )

        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text

        # Extract JSON from response
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]

        try:
            insights = json.loads(text)
            print(f"  [insights] Generated {len(insights.get('es', []))} ES + {len(insights.get('en', []))} EN insights")
            return insights
        except json.JSONDecodeError as e:
            print(f"  [insights] JSON parse error: {e}")
            print(f"  [insights] Raw response: {text[:500]}")
            return {"es": [], "en": []}
