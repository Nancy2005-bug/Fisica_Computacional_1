#!/usr/bin/env python
"""
W06A — DuckDB pipeline runner (idempotent)

Run from project root (where data/, docs/, artifacts/ live):

1) As module (recommended, requires src/__init__.py):
   python -m src.pipeline.w06_pipeline --mode all

2) As script (works even if python -m fails):
   python src/pipeline/w06_pipeline.py --mode all
"""

from __future__ import annotations

from pathlib import Path
import argparse
from datetime import datetime, timezone
import duckdb
import sys


# ------------------------
# Helpers
# ------------------------
def log(msg: str) -> None:
    # Python 3.14+: utcnow() deprecated → timezone-aware UTC
    print(f"[{datetime.now(timezone.utc).isoformat()}] {msg}")


def sql_quote(s: str) -> str:
    """Single-quote SQL string literal."""
    return "'" + s.replace("'", "''") + "'"


def sql_path(p: Path) -> str:
    """
    DuckDB is happiest with forward slashes even on Windows.
    We also wrap as SQL string literal.
    """
    return sql_quote(p.resolve().as_posix())


def ensure_dirs(project_root: Path) -> dict[str, Path]:
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    art_dir = project_root / "artifacts"
    docs_dir = project_root / "docs"

    raw_dir.mkdir(parents=True, exist_ok=True)
    art_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    return {"data": data_dir, "raw": raw_dir, "artifacts": art_dir, "docs": docs_dir}


def connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute("PRAGMA threads=4")
    return con


def must_exist(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def drop_if_exists(con: duckdb.DuckDBPyConnection, obj_type: str, name: str) -> None:
    """
    Drop TABLE/VIEW if it exists.

    IMPORTANT: If there are foreign-key relationships, always drop dependent tables first.
    DuckDB will refuse dropping a primary-key table referenced by another table.
    """
    obj_type = obj_type.upper()
    if obj_type not in {"TABLE", "VIEW"}:
        raise ValueError("obj_type must be TABLE or VIEW")
    con.execute(f"DROP {obj_type} IF EXISTS {name}")


def create_raw_view(con: duckdb.DuckDBPyConnection, raw_csv: Path) -> None:
    # View over raw CSV (Bronze-lite). Literal path avoids prepared-parameter issues.
    drop_if_exists(con, "VIEW", "raw_ps")
    con.execute(f"""
    CREATE VIEW raw_ps AS
    SELECT * FROM read_csv_auto({sql_path(raw_csv)})
    """)


def require_table(con: duckdb.DuckDBPyConnection, table: str, hint: str) -> None:
    q = """
    SELECT COUNT(*) 
    FROM information_schema.tables
    WHERE table_schema='main' AND table_name=?
    """
    exists = con.execute(q, [table]).fetchone()[0] == 1
    if not exists:
        raise RuntimeError(f"Missing table '{table}'. {hint}")


# ------------------------
# Stages
# ------------------------
def build_silver(con: duckdb.DuckDBPyConnection) -> None:
    """
    Silver: cleaned+subset schema (Core 16 columns).
    Idempotent: drops and recreates.
    """
    log("Stage SILVER: building silver_planet")
    drop_if_exists(con, "TABLE", "silver_planet")

    con.execute("""
    CREATE TABLE silver_planet AS
    SELECT
      pl_name,
      hostname,
      discoverymethod,
      disc_year,
      sy_snum,
      sy_pnum,
      sy_dist,
      ra,
      dec,
      pl_orbper,
      pl_rade,
      pl_bmasse,
      pl_eqt,
      st_teff,
      st_rad,
      st_mass
    FROM raw_ps
    WHERE pl_name IS NOT NULL
      AND hostname IS NOT NULL
      AND (disc_year IS NULL OR (disc_year BETWEEN 1980 AND 2026))
      AND (pl_rade  IS NULL OR (pl_rade  > 0 AND pl_rade  <= 30))
      AND (pl_bmasse IS NULL OR (pl_bmasse > 0))
    """)

    n = con.execute("SELECT COUNT(*) FROM silver_planet").fetchone()[0]
    log(f"silver_planet rows={n}")


def build_dims_facts(con: duckdb.DuckDBPyConnection) -> None:
    """
    Build:
    - dim_host_full (1 row per hostname, using MAX as simple dedupe)
    - fact_planet (distinct planet rows)
    - dim_host_sk (surrogate key)
    - fact_planet_sk (fact referencing host_id)

    NOTE (Windows error you saw):
    If a previous version created fact_planet_sk with a FOREIGN KEY referencing dim_host_sk,
    DuckDB will refuse dropping dim_host_sk while fact_planet_sk exists.
    Therefore: DROP dependent tables FIRST.
    """
    require_table(con, "silver_planet",
                  "Run --mode silver first (or --mode all).")

    log("Stage DIMS: building dim_host_full, fact_planet, dim_host_sk, fact_planet_sk")

    # 1) DROP dependents first (FK-safe)
    drop_if_exists(con, "TABLE", "fact_planet_sk")
    drop_if_exists(con, "TABLE", "fact_planet")
    drop_if_exists(con, "TABLE", "dim_host_sk")
    drop_if_exists(con, "TABLE", "dim_host_full")

    # 2) Rebuild
    con.execute("""
    CREATE TABLE dim_host_full AS
    SELECT
      hostname,
      MAX(sy_dist)  AS sy_dist,
      MAX(ra)       AS ra,
      MAX(dec)      AS dec,
      MAX(st_teff)  AS st_teff,
      MAX(st_rad)   AS st_rad,
      MAX(st_mass)  AS st_mass
    FROM silver_planet
    GROUP BY hostname
    """)

    con.execute("""
    CREATE TABLE fact_planet AS
    SELECT DISTINCT
      pl_name,
      hostname,
      discoverymethod,
      disc_year,
      pl_orbper,
      pl_rade,
      pl_bmasse,
      pl_eqt
    FROM silver_planet
    """)

    con.execute("""
    CREATE TABLE dim_host_sk AS
    SELECT
      ROW_NUMBER() OVER (ORDER BY hostname) AS host_id,
      hostname,
      sy_dist, ra, dec, st_teff, st_rad, st_mass
    FROM dim_host_full
    """)

    # Create as CTAS to stay within "what we've taught" (no FK syntax required)
    con.execute("""
    CREATE TABLE fact_planet_sk AS
    SELECT
      f.pl_name,
      d.host_id,
      f.discoverymethod,
      f.disc_year,
      f.pl_orbper,
      f.pl_rade,
      f.pl_bmasse,
      f.pl_eqt
    FROM fact_planet f
    JOIN dim_host_sk d
      ON f.hostname = d.hostname
    """)

    # Evidence checks
    dim_rows, dim_keys = con.execute(
        "SELECT COUNT(*) AS rows, COUNT(DISTINCT hostname) AS keys FROM dim_host_sk"
    ).fetchone()
    fact_rows = con.execute("SELECT COUNT(*) FROM fact_planet").fetchone()[0]
    join_rows = con.execute(
        "SELECT COUNT(*) FROM fact_planet_sk").fetchone()[0]

    log(f"dim_host_sk uniqueness rows={dim_rows}, keys={dim_keys}")
    log(f"fact_planet rows={fact_rows}, fact_planet_sk rows={join_rows}")


def build_gold(con: duckdb.DuckDBPyConnection) -> None:
    require_table(con, "fact_planet_sk",
                  "Run --mode dims first (or --mode all).")
    require_table(con, "dim_host_sk", "Run --mode dims first (or --mode all).")

    log("Stage GOLD: building views gold_by_discoverymethod and gold_by_host")

    drop_if_exists(con, "VIEW", "gold_by_discoverymethod")
    con.execute("""
    CREATE VIEW gold_by_discoverymethod AS
    SELECT
      discoverymethod,
      COUNT(*) AS n_planets,
      AVG(pl_rade)   AS avg_radius_earth,
      AVG(pl_bmasse) AS avg_mass_earth,
      MIN(disc_year) AS first_year,
      MAX(disc_year) AS last_year
    FROM fact_planet_sk
    WHERE discoverymethod IS NOT NULL
    GROUP BY discoverymethod
    ORDER BY n_planets DESC
    """)

    drop_if_exists(con, "VIEW", "gold_by_host")
    con.execute("""
    CREATE VIEW gold_by_host AS
    SELECT
      d.hostname,
      COUNT(*) AS n_planets,
      AVG(f.pl_rade)   AS avg_radius_earth,
      AVG(f.pl_bmasse) AS avg_mass_earth,
      MAX(d.sy_dist) AS sy_dist,
      MAX(d.ra) AS ra,
      MAX(d.dec) AS dec
    FROM fact_planet_sk f
    JOIN dim_host_sk d
      ON f.host_id = d.host_id
    GROUP BY d.hostname
    ORDER BY n_planets DESC, avg_radius_earth DESC NULLS LAST
    """)

    log("gold views created")


def export_artifacts(con: duckdb.DuckDBPyConnection, artifacts_dir: Path) -> None:
    log("Stage EXPORT: writing artifacts CSV")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Ensure views exist
    q = """
    SELECT COUNT(*) 
    FROM information_schema.views
    WHERE table_schema='main' AND table_name=?
    """
    has1 = con.execute(q, ["gold_by_discoverymethod"]).fetchone()[0] == 1
    has2 = con.execute(q, ["gold_by_host"]).fetchone()[0] == 1
    if not (has1 and has2):
        raise RuntimeError(
            "Missing gold views. Run --mode gold first (or --mode all).")

    out1 = artifacts_dir / "gold_by_discoverymethod.csv"
    out2 = artifacts_dir / "gold_by_host.csv"

    con.execute(
        f"COPY (SELECT * FROM gold_by_discoverymethod) TO {sql_path(out1)} (HEADER, DELIMITER ',')")
    con.execute(
        f"COPY (SELECT * FROM gold_by_host) TO {sql_path(out2)} (HEADER, DELIMITER ',')")

    log(f"Wrote {out1.name}")
    log(f"Wrote {out2.name}")


# ------------------------
# CLI
# ------------------------
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="W06A — DuckDB pipeline runner (idempotent)")
    p.add_argument("--project-root", default=".",
                   help="Project root (contains data/, docs/, artifacts/)")
    p.add_argument("--db-path", default="data/exoplanets.duckdb",
                   help="DuckDB path relative to project root")
    p.add_argument("--raw-csv", default="data/raw/pscomppars.csv",
                   help="Raw CSV path relative to project root")
    p.add_argument(
        "--mode", choices=["silver", "dims", "gold", "export", "all"], default="all")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = Path(args.project_root).resolve()
    paths = ensure_dirs(project_root)

    db_path = (project_root / args.db_path).resolve()
    raw_csv = (project_root / args.raw_csv).resolve()

    try:
        must_exist(raw_csv, "raw CSV")
        con = connect(db_path)
        create_raw_view(con, raw_csv)

        if args.mode in ("silver", "all"):
            build_silver(con)
        if args.mode in ("dims", "all"):
            build_dims_facts(con)
        if args.mode in ("gold", "all"):
            build_gold(con)
        if args.mode in ("export", "all"):
            export_artifacts(con, paths["artifacts"])

        log("DONE")
        con.close()
        return 0

    except Exception as e:
        print("\n[ERROR]", str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
