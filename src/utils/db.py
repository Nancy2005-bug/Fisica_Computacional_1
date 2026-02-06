from __future__ import annotations
import duckdb
from .paths import duckdb_path

def connect() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(duckdb_path()))
