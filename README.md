# Física Computacional 1: Ingeniería de Datos I (Fundamentos) 
## Docente: Ph.D. Santiago  Echeverri Arteaga

Este es el primer curso de la línea de Física Computacional del programa de física:

1. Física Computacional 1: Ingeniería de Datos I — Fundamentos (local, sin “infraestructura pesada”)

2. Física Computacional 2: Ingeniería de Datos II — Big Data con Spark (ZTF DR23 Objects+Lightcurves)

3. Física Computacional 3: Ciencia de Datos / ML en Big Data (feature engineering a escala + entrenamiento reproducible)

4. Física Computacional 4: Deep Learning en Big Data (pipelines de datos para DL + entrenamiento/inferencia a escala)

Objetivo: formar base sólida (SQL + diseño + calidad + ETL reproducible) sin Docker ni Spark.

Dataset: NASA Exoplanet Archive (TAP) – tabla `pscomppars` (PSCompPars).

Pipeline: **raw → silver → gold** (local), con checks de calidad y SQL reproducible.

## Quickstart

### 1) Entorno
```bash
python -m venv .venv
# Linux/Mac:
source .venv/bin/activate
# Windows PowerShell:
# .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) Descargar datos (raw)
```bash
python -m src.ingest.download_exoplanets --format csv
```

### 3) Construir SILVER
```bash
python -m src.pipelines.raw_to_silver
```

### 4) Construir GOLD
```bash
python -m src.pipelines.silver_to_gold
```

## Notas
- `data/` no se versiona (está en `.gitignore`).
- DuckDB usa un archivo persistente: `data/exoplanets.duckdb`.
- Durante el curso se pondrán tareas de forma secuencial y se irá dando estructura al repositorio de cada uno. No es necesario que se construya SILVER y GOLD desde el inicio.

## Entregables por hitos (proyecto)

H0 (sem 1): repo + estructura + script de descarga + bitácora técnica

H1 (sem 3): profiling + data contract v1 + preguntas de negocio/ciencia

H2 (sem 5): modelo relacional (normalizado) + carga a DuckDB + 10 queries

H3 (sem 8): pipeline reproducible raw→silver + checks automatizados

H4 (sem 16): gold + informe técnico + demo final

## Plan semana a semana (A/B)

A: qué es ingeniería de datos + ciclo de vida + evidencia | B: Git/venv/estructura + descarga pscomppars

A: SQL básico (DuckDB) | B: SQL joins + CTEs (sobre pscomppars)

A: modelado relacional (keys/constraints) | B: descomponer pscomppars en tablas (host/planet/discovery)

A: calidad de datos (reglas mínimas) | B: implementar checks (nulos, rangos físicos, unicidad, consistencia)

A: ETL en Python (sin Pandas) | B: raw→silver (tipos, columnas canónicas, limpieza mínima)

A: Parquet + particionado local | B: medir tamaños/lecturas y justificar partición

A: SQL analítico (ventanas útiles) | B: construir métricas “gold” (por año/método/facilidad)

A: evaluación 1 (demo H3) | B: refactor/reproducibilidad + revisión por pares

A: trazabilidad (data contract v2 + changelog de schema) | B: versionado de datos y “por qué cambió”

A: performance de queries (EXPLAIN en DuckDB) | B: 2 optimizaciones con evidencia

A: diseño de interfaces (CLI con argparse) | B: “make run”/scripts reproducibles

A: mini “arquitectura” (batch vs serving, trade-offs) | B: consulta guiada (lectura corta + aplicación al proyecto)

A: opcional introducción a Docker (conceptual) | B: opcional Postgres local o Docker (solo si van bien)

A: serving queries (si usan Postgres) | B: índices + EXPLAIN (muy pragmático)

A: preparar demo final | B: ensayo + checklist de evidencia

A: demo final | B: defensa + puente a Spark/Big Data

## Bibliografía mínima recomendada (y por qué)

- Martin Kleppmann, Designing Data-Intensive Applications (DDIA): marco conceptual de sistemas de datos y trade-offs. 

- DuckDB Documentation: SQL, import/export, planes y pragmas. 

- NASA Exoplanet Archive: TAP + PSCompPars (semántica y cálculos). 

- Kimball Group (técnicas): star schema/facts/dims (solo lo esencial)