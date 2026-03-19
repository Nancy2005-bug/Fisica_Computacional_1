# W04-A

## Turno 1: Nulos en 12 columnas clave

```python
picked = [
  "pl_name","hostname","disc_year","discoverymethod",
  "pl_orbper","pl_rade","pl_bmasse",
  "sy_dist","ra","dec",
  "sy_snum","sy_pnum"
]

parts = [
  f"SELECT '{c}' AS col, COUNT(*) - COUNT({c}) AS nulls FROM raw_ps"
  for c in picked
]
query = " UNION ALL ".join(parts) + " ORDER BY nulls DESC, col ASC"
con.sql(query).show()
```

**Output:**

| **col** (varchar) | **nulls** (int64) |
|:------------------|------------------:|
| pl_orbper         |               323 |
| pl_rade           |                50 |
| pl_bmasse         |                31 |
| sy_dist           |                27 |
| disc_year         |                 1 |
| dec               |                 0 |
| discoverymethod   |                 0 |
| hostname          |                 0 |
| pl_name           |                 0 |
| ra                |                 0 |
| sy_pnum           |                 0 |
| sy_snum           |                 0 |

*12 rows, 2 columns*

## Turno 2: A) pl_rade (radio) en rango didáctico

```python
query = """
SELECT COUNT(*) AS n_bad_pl_rade
FROM raw_ps
WHERE pl_rade IS NOT NULL
  AND (pl_rade <= 0 OR pl_rade > 30)
"""
con.sql(query).show()
```

**Output:**

| n_bad_pl_rade (int64) |
|---------------------:|
|                    6 |

*1 row, 1 column*

**Interpretación:** El check encontró 6 planetas cuyo radio `(pl_rade)` cae fuera del rango didáctico definido como válido: (0,30] radios terrestres.

# W04-B

## 1) Diseño Silver (mínimo viable)

**Contract v1 (Core 16 columnas):**
`pl_name, hostname, discoverymethod, disc_year, sy_snum, sy_pnum, sy_dist, ra, dec, pl_orbper, pl_rade, pl_bmasse, pl_eqt, st_teff, st_rad, st_mass`

**Reglas Silver (hoy):**
- `pl_name` y `hostname` no nulos
- `disc_year` en [1980, 2026] si no es nulo
- rangos didácticos:
  - `pl_rade` > 0 y ≤ 30 si no es nulo
  - `pl_bmasse` > 0 si no es nulo

```python
con.execute("DROP TABLE IF EXISTS silver_planet")

con.execute('''
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
WHERE pl_name  IS NOT NULL
  AND hostname IS NOT NULL
  AND (disc_year IS NULL OR (disc_year >= 1980 AND disc_year <= 2026))
  AND (pl_rade   IS NULL OR (pl_rade > 0 AND pl_rade <= 30))
  AND (pl_bmasse IS NULL OR pl_bmasse > 0)
  AND (pl_orbper IS NULL OR pl_orbper > 0)   -- regla extra elegida
''')

# Validación
con.sql("SELECT COUNT(*) AS n_rows, COUNT(DISTINCT pl_name) AS n_pl FROM silver_planet").show()
```

**Output:**

| n_rows (int64) | n_pl (int64) |
|----------------:|-------------:|
|            6101 |         6101 |

## 2) Dimensiones (1 fila por clave)

Estrategia “mesurada” (sin window functions):
- `GROUP BY hostname`
- para cada columna: `MAX(col)` para consolidar una fila por hostname

```python
con.execute("DROP TABLE IF EXISTS dim_host_full")

con.execute('''
CREATE TABLE dim_host_full AS
SELECT
    hostname,
    MAX(sy_dist)  AS sy_dist,
    MAX(st_teff)  AS st_teff,
    MAX(st_rad)   AS st_rad
FROM silver_planet
GROUP BY hostname
''')

# Validación
con.sql("SELECT COUNT(*) AS n_rows, COUNT(DISTINCT hostname) AS n_keys FROM dim_host_full").show()
```

**Output:**

| n_rows (int64) | n_pl (int64) |
|----------------:|-------------:|
| 4550 | 4550 |

## 3) Fact table (grain: 1 fila ≈ 1 planeta)

Creamos `fact_planet` desde Silver usando `SELECT DISTINCT`.
Si aparecen duplicados por `pl_name`, se documenta como issue de calidad.

```python
con.execute("DROP TABLE IF EXISTS fact_planet")

con.execute('''
CREATE TABLE fact_planet AS
SELECT DISTINCT
    pl_name,
    hostname,
    discoverymethod,
    disc_year,
    sy_snum,
    sy_pnum,
    pl_orbper,
    pl_rade,
    pl_bmasse,
    pl_eqt
FROM silver_planet
''')

# Validación
con.sql("SELECT COUNT(*) AS n_rows, COUNT(DISTINCT pl_name) AS n_pl FROM fact_planet").show()
```

**Output:**

| n_rows (int64) | n_pl (int64) |
|----------------:|-------------:|
|            6101 |         6101 |

## 4) JOINs sanos + 2 vistas Gold
- JOIN sano: `COUNT(join)` ≈ `COUNT(fact)` (no inflar).
- Gold: `gold_by_method` y `gold_by_host`.

```python
# Agrega estadísticas por estrella huésped (cuántos planetas tiene, sus tamaños, etc.)
con.execute("DROP VIEW IF EXISTS gold_by_host")
con.execute('''
CREATE VIEW gold_by_host AS
SELECT
    f.hostname,
    COUNT(*)            AS n_planets,
    AVG(f.pl_rade)      AS avg_pl_rade,
    AVG(f.pl_bmasse)    AS avg_pl_bmasse,
    AVG(f.pl_orbper)    AS avg_orbper,
    MAX(d.sy_dist)      AS sy_dist,
    MAX(d.st_teff)      AS st_teff
FROM fact_planet f
LEFT JOIN dim_host_full d ON f.hostname = d.hostname
GROUP BY f.hostname
ORDER BY n_planets DESC
''')

con.sql("SELECT * FROM gold_by_host LIMIT 10").show()
```

**Output:**

| hostname (varchar) | n_planets (int64) | avg_pl_rade (double) | avg_pl_bmasse (double) | avg_orbper (double) | sy_dist (double) | st_teff (double) |
|:---|---:|---:|---:|---:|---:|---:|
| KOI-351 | 8 | 3.9 | 31.14875 | 106.13811824999999 | 848.254 | 6080.0 |
| TRAPPIST-1 | 7 | 0.9785714285714285 | 0.9211428571428569 | 7.7736924285714295 | 12.42988881 | 2566.0 |
| K2-138 | 6 | 2.5843333333333334 | 6.041666666666667 | 12.384155000000002 | 202.585 | 5356.3 |
| Kepler-11 | 6 | 2.966666666666667 | 7.8500000000000005 | 40.513600000000004 | 646.346 | 5663.0 |
| HIP 41378 | 6 | 4.253666666666667 | 7.815 | 216.46327666666664 | 106.289 | 6320.0 |
| Kepler-20 | 6 | 2.292666666666667 | 9.386666666666667 | 25.46307558333333 | 282.563 | 5495.0 |
| Kepler-80 | 6 | 1.8133333333333332 | 747.3908333333333 | 6.654247883333333 | 369.451 | 4540.0 |
| TOI-1136 | 6 | 3.051819136666666 | 6.59 | 17.93616666666667 | 84.5362 | 5770.0 |
| HD 219134 | 6 | 3.668833333333333 | 25.23973666666667 | 403.43891766666667 | 6.53127 | 4913.0 |
| HD 191939 | 6 | 6.590000000000001 | 176.97430202666666 | 559.8221842666666 | 53.6089 | 5348.0 |

*10 rows, 7 columns*

```python
gold_csv = ART_DIR / "gold_by_host.csv"
con.execute(
    f"COPY (SELECT * FROM gold_by_host) TO {sql_quote(str(gold_csv))} (HEADER, DELIMITER ',')"
)
print("Exporté:", gold_csv)
```

*Guardado en docs/*

## Reflexión (bitácora)
- ¿Qué evidencia mínima te convence de que tu JOIN es sano?

> Que COUNT(fact_planet) sea igual al COUNT del resultado del JOIN entre fact_planet y dim_host_full. Si los números coinciden, el JOIN no infló filas, lo que confirma que hostname es clave única en dim_host_full y que cada planeta se enlazó con exactamente una estrella.

- ¿Qué trade-off hay entre “limpiar mucho” vs “no perder datos”?

> Limpiar mucho produce datos más confiables, pero puede descartar planetas válidos que simplemente tienen columnas incompletas. No limpiar conserva más registros, pero arriesga que valores erróneos distorsionen métricas y modelos posteriores. La solución adoptada en Silver es conservadora: solo se filtran valores físicamente imposibles (radios negativos, períodos orbitales ≤ 0), mientras que los nulos se toleran para no perder cobertura innecesariamente.

## Turno 3: Materializa un reporte (tabla) y expórtalo

```python
run_ts = datetime.now(timezone.utc).isoformat()

sql = f"""
CREATE TABLE quality_w04 AS

  SELECT {sql_quote(run_ts)} AS run_ts,
         'nulls_pl_name'     AS check_name,
         (COUNT(*) - COUNT(pl_name))::BIGINT AS metric_value
  FROM raw_ps

UNION ALL

  SELECT {sql_quote(run_ts)},
         'nulls_hostname',
         (COUNT(*) - COUNT(hostname))::BIGINT
  FROM raw_ps

UNION ALL

  SELECT {sql_quote(run_ts)},
         'bad_pl_rade_range',
         COUNT(*)::BIGINT
  FROM raw_ps
  WHERE pl_rade IS NOT NULL
    AND (pl_rade <= 0 OR pl_rade > 30)
"""

con.execute("DROP TABLE IF EXISTS quality_w04")
con.execute(sql)
con.sql("SELECT * FROM quality_w04").show()

# Exportar CSV a artifacts/
out_csv = ART_DIR / f"w04_quality_{run_ts.replace(':','-')}.csv"
con.execute(
    f"COPY (SELECT * FROM quality_w04) TO {sql_quote(str(out_csv))} (HEADER, DELIMITER ',')"
)
print("Exporté:", out_csv)
```

*Exportado en docs/*

## Reflexión (bitácora)
- ¿Qué check te sorprendió más y por qué?

> El check bad_pl_rade_range fue el más sorprendente. Aunque el catálogo NASA es una fuente oficial, encontramos 6 planetas con radios mayores a 30 radios terrestres (como V2376 Ori b con pl_rade = 87.2), lo que demuestra que incluso datos de fuentes confiables requieren validación antes de analizar.

- ¿Qué consecuencias tendría para W02B (JOINs) que `pl_name` o `hostname` tuviera muchos nulos/duplicados?

> Nulos en hostname harían que planetas quedaran sin estrella asociada en el JOIN, perdiendo filas o generando resultados incompletos. Duplicados en pl_name inflarían filas al hacer el JOIN, corrompiendo métricas como promedios de radio o conteos por método de descubrimiento.