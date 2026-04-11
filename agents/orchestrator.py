"""Orchestrator Agent — Coordinates the full E2E pipeline."""

import json
import anthropic

from agents.data_agent import DataAgent
from agents.insights_agent import InsightsAgent
from agents.builder_agent import BuilderAgent
from agents.deploy_agent import DeployAgent
from agents import tools


class Orchestrator:
    """Coordinates Data → Insights → Builder → Deploy agents."""

    def __init__(self, client: anthropic.Anthropic, skip_deploy: bool = False, skip_insights: bool = False):
        self.client = client
        self.skip_deploy = skip_deploy
        self.skip_insights = skip_insights
        self.data_agent = DataAgent(client)
        self.insights_agent = InsightsAgent(client)
        self.builder_agent = BuilderAgent(client)
        self.deploy_agent = DeployAgent(client)

    def run(self, analisis_path: str = "", horarios_path: str = "") -> dict:
        """Execute the full E2E pipeline."""
        result = {"steps": [], "success": False}

        # ===== STEP 1: Extract & Validate Data =====
        print("\n" + "=" * 60)
        print("PASO 1: Extracción y validación de datos")
        print("=" * 60)

        extraction = tools.extract_data(analisis_path, horarios_path)
        result["steps"].append({"step": "extract", "result": extraction})
        print(f"  Extracción OK: {extraction.get('ALL', {}).get('units', '?')} uds totales")

        validation = tools.validate_data()
        result["steps"].append({"step": "validate", "result": validation})
        if not validation["valid"]:
            print("  ❌ Validación FALLIDA — abortando pipeline")
            return result
        print("  ✅ Validación OK")

        # ===== STEP 2: Generate Insights =====
        print("\n" + "=" * 60)
        print("PASO 2: Generación de insights con IA")
        print("=" * 60)

        if self.skip_insights:
            print("  ⏭️  Insights omitidos (--no-insights)")
            insights = None
        else:
            data_summary = tools.get_data_summary()
            insights = self.insights_agent.generate(data_summary)
            result["steps"].append({"step": "insights", "count_es": len(insights.get("es", [])), "count_en": len(insights.get("en", []))})

        # ===== STEP 3: Build Dashboard =====
        print("\n" + "=" * 60)
        print("PASO 3: Construcción del dashboard")
        print("=" * 60)

        inject_result = tools.inject_data()
        result["steps"].append({"step": "inject_data", "result": inject_result})

        if insights and insights.get("es") and insights.get("en"):
            ins_result = tools.inject_insights(
                html_path=tools.DEFAULT_HTML,
                insights_es=insights["es"],
                insights_en=insights["en"],
            )
            result["steps"].append({"step": "inject_insights", "result": ins_result})
            print(f"  Insights inyectados: {ins_result}")
        else:
            print("  Insights no disponibles, se mantienen los existentes")

        verify = tools.verify_html()
        result["steps"].append({"step": "verify", "result": verify})
        if not verify["valid"]:
            print(f"  ❌ HTML inválido: {verify}")
            return result
        print(f"  ✅ HTML válido ({verify['size_bytes']:,} bytes)")

        # ===== STEP 4: Deploy =====
        print("\n" + "=" * 60)
        print("PASO 4: Deploy a GitHub")
        print("=" * 60)

        if self.skip_deploy:
            print("  ⏭️  Deploy omitido (--dry-run)")
            result["success"] = True
        else:
            deploy = tools.git_commit_and_push("Auto-refresh dashboard con insights IA")
            result["steps"].append({"step": "deploy", "result": deploy})
            if deploy.get("committed") and deploy.get("pushed"):
                print("  ✅ Push exitoso")
                result["success"] = True
            elif not deploy.get("committed"):
                print("  ℹ️  Nada que commitear (sin cambios)")
                result["success"] = True
            else:
                print(f"  ⚠️  Push falló: {deploy.get('push_output', '')}")
                result["success"] = True  # Data still processed OK

        # ===== SUMMARY =====
        print("\n" + "=" * 60)
        print("RESUMEN FINAL")
        print("=" * 60)
        for ch in ["SI", "NO", "Online", "ALL"]:
            kpis = extraction.get(ch, {})
            if kpis:
                print(f"  {ch:8s}: {kpis.get('units', 0):>5} uds | {kpis.get('revenue', 0):>12.2f} € | TK {kpis.get('ticket', 0):>7.2f}")
        print(f"\n  Promotores: {extraction.get('promotores_count', 0)} tiendas")
        print(f"  Incentivos: {extraction.get('incentivos_count', 0)} registros")
        if insights and insights.get("es"):
            print(f"  Insights: {len(insights['es'])} generados por IA")
        print(f"  Dashboard: {tools.DEFAULT_HTML}")

        return result
