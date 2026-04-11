"""Shared tool functions — wrappers around existing scripts."""

import json
import os
import sys
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ANALISIS = os.path.join(ROOT, "data", "Analisis Honor 2025 (v3).xlsx")
DEFAULT_HORARIOS = os.path.join(ROOT, "data", "Horarios HONOR.xlsx")
DEFAULT_HTML = os.path.join(ROOT, "output", "HONOR_Dashboard_v5.html")
DEFAULT_JSON = os.path.join(ROOT, "output", "dashboard_data.json")


def extract_data(analisis_path: str = "", horarios_path: str = "") -> dict:
    """Run extract_data.py and return summary metrics."""
    analisis_path = analisis_path or DEFAULT_ANALISIS
    horarios_path = horarios_path or DEFAULT_HORARIOS

    sys.path.insert(0, ROOT)
    from scripts.extract_data import main as extract_main

    old_argv = sys.argv
    sys.argv = ["", analisis_path, horarios_path, "--output", DEFAULT_JSON]
    try:
        data = extract_main()
    finally:
        sys.argv = old_argv

    summary = {}
    for ch in ["SI", "NO", "Online", "ALL"]:
        if ch in data:
            summary[ch] = data[ch]["kpis"]
    summary["promotores_count"] = len(data.get("promotores", {}))
    summary["incentivos_count"] = len(data.get("incentivos", []))
    summary["json_path"] = DEFAULT_JSON
    return summary


def validate_data(json_path: str = "", analisis_path: str = "") -> dict:
    """Run validate.py and return validation result."""
    json_path = json_path or DEFAULT_JSON
    analisis_path = analisis_path or DEFAULT_ANALISIS

    sys.path.insert(0, ROOT)
    from scripts.validate import validate

    success = validate(json_path, analisis_path)
    return {"valid": success, "json_path": json_path}


def get_data_summary(json_path: str = "") -> dict:
    """Load JSON and return a structured summary for analysis."""
    json_path = json_path or DEFAULT_JSON
    with open(json_path) as f:
        data = json.load(f)

    summary = {}
    for ch in ["SI", "NO", "Online", "ALL"]:
        if ch not in data:
            continue
        d = data[ch]
        k = d["kpis"]
        summary[ch] = {
            "kpis": k,
            "top5_models": d["models"][:5],
            "zonas": d["zonas"],
            "gamas": d["gamas"],
            "meses": d["meses"],
            "top5_tiendas": d["tiendas"][:5],
            "bottom3_tiendas": d["tiendas"][-3:] if len(d["tiendas"]) >= 3 else d["tiendas"],
            "weekly": d["weekly"],
            "dias": d["dias"],
        }

    if "promotores" in data:
        promo = data["promotores"]
        sorted_promo = sorted(promo.items(), key=lambda x: x[1].get("salesPerHour", 0), reverse=True)
        summary["promotores_top3"] = sorted_promo[:3]
        summary["promotores_bottom3"] = sorted_promo[-3:]

    if "incentivos" in data:
        summary["incentivos_sample"] = data["incentivos"][:10]

    return summary


def inject_data(json_path: str = "", html_path: str = "") -> dict:
    """Run inject_data.py to embed JSON data into HTML."""
    json_path = json_path or DEFAULT_JSON
    html_path = html_path or DEFAULT_HTML

    sys.path.insert(0, ROOT)
    from scripts.inject_data import inject

    success = inject(json_path, html_path)
    return {"success": success, "html_path": html_path}


def inject_insights(html_path: str, insights_es: list, insights_en: list) -> dict:
    """Replace the ins:[] arrays in the HTML with new Claude-generated insights."""
    html_path = html_path or DEFAULT_HTML

    with open(html_path) as f:
        html = f.read()

    import re

    def build_ins_js(insights):
        items = []
        for ins in insights:
            tag = ins["tag"].replace("'", "\\'")
            t = ins["t"].replace("'", "\\'")
            p = ins["p"].replace("'", "\\'")
            items.append(f"{{tag:'{tag}',t:'{t}',p:'{p}'}}")
        return "ins:[\n" + ",\n".join(items) + "]"

    # Replace ES insights (first ins:[ block)
    # Replace EN insights (second ins:[ block)
    # Pattern: ins:[\n{...}] up to the next ]
    ins_pattern = re.compile(r'ins:\[\s*\n?\{tag:.*?\}\]', re.DOTALL)
    matches = list(ins_pattern.finditer(html))

    if len(matches) >= 2:
        # Replace in reverse order to preserve offsets
        replacements = [
            (matches[0], build_ins_js(insights_es)),
            (matches[1], build_ins_js(insights_en)),
        ]
        for match, replacement in reversed(replacements):
            html = html[:match.start()] + replacement + html[match.end():]

        with open(html_path, "w") as f:
            f.write(html)
        return {"success": True, "insights_es": len(insights_es), "insights_en": len(insights_en)}

    return {"success": False, "error": f"Found {len(matches)} ins:[] blocks, expected >= 2"}


def verify_html(html_path: str = "") -> dict:
    """Verify that the HTML file exists, has data, and is valid."""
    html_path = html_path or DEFAULT_HTML

    if not os.path.exists(html_path):
        return {"valid": False, "error": "HTML file not found"}

    with open(html_path) as f:
        html = f.read()

    has_data = "const D={" in html
    size = len(html)

    return {
        "valid": has_data and size > 10000,
        "size_bytes": size,
        "has_data_block": has_data,
        "html_path": html_path,
    }


def git_commit_and_push(message: str = "Update dashboard") -> dict:
    """Commit output files and push to origin."""
    try:
        subprocess.run(["git", "add", "output/"], cwd=ROOT, check=True, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=ROOT, capture_output=True, text=True,
        )
        if result.returncode != 0 and "nothing to commit" in result.stdout:
            return {"committed": False, "message": "Nothing to commit"}

        push = subprocess.run(
            ["git", "push", "-u", "origin", "HEAD"],
            cwd=ROOT, capture_output=True, text=True,
        )
        return {
            "committed": True,
            "pushed": push.returncode == 0,
            "message": message,
            "push_output": push.stdout or push.stderr,
        }
    except Exception as e:
        return {"committed": False, "error": str(e)}
