#!/usr/bin/env python3
"""
HONOR Dashboard — Multi-Agent Pipeline
========================================
Ejecuta el equipo de agentes E2E para actualizar el dashboard.

USO:
    # Pipeline completo (extrae, insights, build, deploy)
    python3 run_agents.py

    # Sin deploy (solo genera localmente)
    python3 run_agents.py --dry-run

    # Sin insights IA (solo datos)
    python3 run_agents.py --no-insights

    # Con Excels personalizados
    python3 run_agents.py --analisis path/to/analisis.xlsx --horarios path/to/horarios.xlsx

REQUIERE:
    Variable de entorno ANTHROPIC_API_KEY
"""

import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="HONOR Dashboard — Multi-Agent Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="No hacer deploy (solo generar localmente)")
    parser.add_argument("--no-insights", action="store_true", help="Omitir generación de insights con IA")
    parser.add_argument("--analisis", default="", help="Ruta al Excel de análisis")
    parser.add_argument("--horarios", default="", help="Ruta al Excel de horarios")
    args = parser.parse_args()

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key and not args.no_insights:
        print("❌ Variable ANTHROPIC_API_KEY no encontrada.")
        print("")
        print("Opciones:")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        print("  python3 run_agents.py --no-insights  # ejecutar sin insights IA")
        sys.exit(1)

    import anthropic
    from agents.orchestrator import Orchestrator

    print("=" * 60)
    print("HONOR Dashboard — Multi-Agent Pipeline")
    print("=" * 60)
    print(f"  Modo: {'DRY RUN (sin deploy)' if args.dry_run else 'COMPLETO'}")
    print(f"  Insights: {'Desactivados' if args.no_insights else 'Claude IA'}")

    client = anthropic.Anthropic(api_key=api_key) if api_key else None

    orchestrator = Orchestrator(
        client=client,
        skip_deploy=args.dry_run,
        skip_insights=args.no_insights,
    )

    result = orchestrator.run(
        analisis_path=args.analisis,
        horarios_path=args.horarios,
    )

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
