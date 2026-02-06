from __future__ import annotations

import argparse
from pathlib import Path
import requests

from src.utils.paths import raw_dir

TAP_SYNC = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

DEFAULT_COLUMNS = [
    "pl_name",
    "hostname",
    "discoverymethod",
    "disc_year",
    "sy_snum",
    "sy_pnum",
    "sy_dist",
    "ra", "dec",
    "pl_orbper",
    "pl_rade",
    "pl_bmasse",
    "pl_eqt",
    "st_teff",
    "st_rad",
    "st_mass"
]


def build_query(columns: list[str], limit: int | None) -> str:
    cols = ", ".join(columns)
    if limit is not None and limit > 0:
        return f"select top {int(limit)} {cols} from pscomppars order by pl_name"
    return f"select {cols} from pscomppars"


def download(fmt: str, out_path: Path, columns: list[str], limit: int | None):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    params = {"query": build_query(columns, limit), "format": fmt}
    r = requests.get(TAP_SYNC, params=params, timeout=180)
    r.raise_for_status()
    out_path.write_bytes(r.content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", choices=["csv", "json"], default="csv")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--full", action="store_true",
                    help="Descarga *todas* las columnas (tabla ancha).")
    args = ap.parse_args()

    columns = ["*"] if args.full else DEFAULT_COLUMNS
    out = raw_dir() / f"pscomppars.{args.format}"
    download(args.format, out, columns, args.limit)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
