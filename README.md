# Física Computacional 1: Ingeniería de Datos I (Fundamentos) 
### Docente: Ph.D. Santiago  Echeverri Arteaga

### Estudiante: Nancy Camacho Santos

Objetivo: formar base sólida (SQL + diseño + calidad + ETL reproducible) sin Docker ni Spark.

Dataset: NASA Exoplanet Archive (TAP) – tabla `pscomppars` (PSCompPars).

Pipeline: **raw → silver → gold** (local), con checks de calidad y SQL reproducible.

---

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
---

## Entregables Realizados

**W01:**

* :white_check_mark: W01B — Bronze/Raw: ingesta + trazabilidad + sanity checks (DDIA Cap. 1)

* :white_check_mark: W01B — Bronze/Raw: ingesta + trazabilidad + sanity checks (DDIA Cap. 1)

---

## Notas
- `data/` no se versiona (está en `.gitignore`).
- DuckDB usa un archivo persistente: `data/exoplanets.duckdb`.
- Durante el curso se pondrán tareas de forma secuencial y se irá dando estructura al repositorio de cada uno. No es necesario que se construya SILVER y GOLD desde el inicio.

---

## Bibliografía mínima recomendada (y por qué)

- Martin Kleppmann, Designing Data-Intensive Applications (DDIA): marco conceptual de sistemas de datos y trade-offs. 

- DuckDB Documentation: SQL, import/export, planes y pragmas. 

- NASA Exoplanet Archive: TAP + PSCompPars (semántica y cálculos). 

- Kimball Group (técnicas): star schema/facts/dims (solo lo esencial)

El libro de Martin Kleppmann y otros 9 que conplementan muy bien el contenido del curso los encuentran en el [LINK](https://drive.google.com/drive/folders/1mALy-WvMivcfmxSqoFAgTbKzgHA-NJhP?usp=sharing)
