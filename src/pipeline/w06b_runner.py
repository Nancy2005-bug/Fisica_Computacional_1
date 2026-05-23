"""
W06B Runner — ejecuta w06_pipeline por etapas y mide tiempos.
Guarda artifacts/w06b_run_report.json y artifacts/w06b_stage_timings.csv
"""
from __future__ import annotations
import time, json, csv, sys
from pathlib import Path
import duckdb

# Importa helpers y etapas del pipeline existente
from src.pipeline.w06_pipeline import (
    ensure_dirs, connect, create_raw_view,
    build_silver, build_dims_facts, build_gold, export_artifacts
)

PROJECT_ROOT = Path(".").resolve()
DB_PATH      = PROJECT_ROOT / "data" / "exoplanets.duckdb"
RAW_CSV      = PROJECT_ROOT / "data" / "raw" / "pscomppars.csv"
ARTIFACTS    = PROJECT_ROOT / "artifacts"

STAGES = [
    ("silver", build_silver),
    ("dims",   build_dims_facts),
    ("gold",   build_gold),
]

def main() -> int:
    print("=" * 60)
    print("W06B Runner — midiendo tiempos de etapas")
    print("=" * 60)

    if not RAW_CSV.exists():
        print(f"[ERROR] Falta {RAW_CSV}", file=sys.stderr)
        return 1

    paths = ensure_dirs(PROJECT_ROOT)
    con   = connect(DB_PATH)
    create_raw_view(con, RAW_CSV)

    results = []
    for name, fn in STAGES:
        t0 = time.perf_counter()
        fn(con)
        seconds = round(time.perf_counter() - t0, 4)
        print(f"  [{name}] {seconds}s")
        results.append({"mode": name, "seconds": seconds})

    # etapa export
    t0 = time.perf_counter()
    export_artifacts(con, paths["artifacts"])
    seconds = round(time.perf_counter() - t0, 4)
    results.append({"mode": "export", "seconds": seconds})
    print(f"  [export] {seconds}s")

    con.close()

    # Guardar reporte JSON
    report_path = ARTIFACTS / "w06b_run_report.json"
    report_path.write_text(
        json.dumps({"stages": results}, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # Guardar CSV
    csv_path = ARTIFACTS / "w06b_stage_timings.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["mode", "seconds"])
        writer.writeheader()
        writer.writerows(results)

    slowest = max(results, key=lambda x: x["seconds"])
    print(f"\n>>> Etapa más lenta: {slowest['mode']} ({slowest['seconds']}s)")
    print(f"Reporte: {report_path}")
    print(f"CSV:     {csv_path}")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())