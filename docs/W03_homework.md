# W03 – SQL esencial II (JOINs + CTEs) y cardinalidad práctica

## DEMOS

### DEMO 3: JOIN correcto (many-to-one)
`fact_planet_raw` → `dim_host` debería ser muchos-a-uno. Si `dim_host` tiene hostname único, **no debe multiplicar filas**.

```python
n_fact = con.execute("SELECT count(*) FROM fact_planet_raw").fetchone()[0]
n_join = con.execute("""
SELECT count(*)
FROM fact_planet_raw f
JOIN dim_host_ra h
  ON f.hostname = h.hostname
""").fetchone()[0]
n_fact, n_join
```

**Resultado:** (6107, 6107)

**Interpretación:** `dim_host_ra` tiene hostname único gracias al GROUP BY, por lo que
cada planeta encontró exactamente un host y no se generaron filas extra.

### DEMO 4: JOIN “malo” (duplica filas)
Error común: unirse a una tabla que **no es dimensión** (llave no única). Fabricamos una “dimensión mala” a propósito.

```python
# DEMO 3: una "dimensión" MAL construida (violando 1 fila por hostname)
# Aquí NO deduplicamos: tendrá múltiples filas por hostname.
con.execute("""
CREATE OR REPLACE TABLE dim_host_bad AS
SELECT hostname, ra
FROM raw_ps
WHERE hostname IS NOT NULL
""")

# Evidencia sin HAVING (solo CTE + WHERE)
con.sql("""
WITH c AS (
  SELECT hostname, COUNT(*) AS cnt
  FROM dim_host_bad
  GROUP BY hostname
)
SELECT * FROM c
WHERE cnt > 1
ORDER BY cnt DESC
LIMIT 10
""").show()
```

**Respuesta:**

| hostname   | cnt |
| ---------- | --- |
| KOI-351    | 8   |
| TRAPPIST-1 | 7   |
| K2-138     | 6   |
| HD 110067  | 6   |
| HD 10180   | 6   |
| TOI-1136   | 6   |
| HD 191939  | 6   |
| Kepler-80  | 6   |
| TOI-178    | 6   |
| Kepler-20  | 6   |

```python
n_join_bad = con.execute("""
SELECT count(*)
FROM fact_planet_raw f
JOIN dim_host_bad h
  ON f.hostname = h.hostname
""").fetchone()[0]

n_fact, n_join_bad
```

**Respuesta:** (6107, 10779)

**Interpretación:** `dim_host_bad` tiene múltiples filas por hostname porque no se deduplicó.
Al hacer JOIN, cada planeta se multiplicó por el número de veces que aparece su host en la dimensión. Esto genera filas falsas que inflarían cualquier agregación (sumas, promedios, conteos).

### DEMO 5: arreglar JOIN malo con CTE (deduplicación)

```python
n_join_fixed = con.execute("""
WITH dim_host_fixed AS (
  SELECT DISTINCT hostname
  FROM dim_host_bad
)
SELECT count(*)
FROM fact_planet_raw f
JOIN dim_host_fixed h
  ON f.hostname = h.hostname
""").fetchone()[0]
n_fact, n_join_fixed
```

**Respuesta:** (6107, 6107)

**Interpretación:** Al envolver dim_host_bad en un CTE con SELECT DISTINCT, se elimina la duplicidad de hostnames antes del JOIN. El conteo vuelve al original, confirmando que el problema estaba en la dimensión y no en la fact table. La solución definitiva es corregirlo en el ETL; el CTE es un parche temporal.

## To Do

### 1) LEFT JOIN y no-match: ¿cuántas filas quedan sin match en dim_host?

```sql
SELECT
    COUNT(*) AS total,
    COUNT(CASE WHEN h.hostname IS NULL THEN 1 END) AS no_match
FROM fact_planet_raw f
LEFT JOIN dim_host_ra h
    ON f.hostname = h.hostname
```

**Respuesta:**

| total int64 | no_match int64 |
| --------- | --------------- |
| 6107      | 0   |

### 2) CTE + ranking: por año, método #1 (más planetas)

```sql
WITH counts AS (
    SELECT
        disc_year,
        discoverymethod,
        COUNT(*) AS n
    FROM fact_planet_raw
    WHERE disc_year IS NOT NULL AND discoverymethod IS NOT NULL
    GROUP BY disc_year, discoverymethod
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY disc_year ORDER BY n DESC) AS rn
    FROM counts
)
SELECT disc_year, discoverymethod, n
FROM ranked
WHERE rn = 1
ORDER BY disc_year
```

**Respuesta:**

| disc_year | discoverymethod | n   |
| --------- | --------------- | --- |
| 1992      | Pulsar Timing   | 2   |
| 1994      | Pulsar Timing   | 1   |
| 1995      | Radial Velocity | 1   |
| 1996      | Radial Velocity | 6   |
| 1997      | Radial Velocity | 1   |
| 1998      | Radial Velocity | 6   |
| 1999      | Radial Velocity | 13  |
| 2000      | Radial Velocity | 16  |
| 2001      | Radial Velocity | 12  |
| 2002      | Radial Velocity | 28  |
| ...       | ...             | ... |
| 2017      | Transit         | 87  |
| 2018      | Transit         | 242 |
| 2019      | Transit         | 107 |
| 2020      | Transit         | 165 |
| 2021      | Transit         | 457 |
| 2022      | Transit         | 191 |
| 2023      | Transit         | 224 |
| 2024      | Transit         | 187 |
| 2025      | Transit         | 141 |
| 2026      | Transit         | 10  |

### 3) Validación de cardinalidad: ¿hay duplicados en (discoverymethod, disc_year) en dim_discovery?

```sql
SELECT discoverymethod, disc_year, COUNT(*) AS cnt
FROM dim_discovery
GROUP BY discoverymethod, disc_year
HAVING COUNT(*) > 1
```

**Respuesta:** []

### 4) JOIN + agregación: promedio de RA del host por método

```sql
SELECT
    f.discoverymethod,
    COUNT(*)    AS n_planets,
    AVG(h.ra)   AS avg_ra
FROM fact_planet_raw f
JOIN dim_host_ra h
    ON f.hostname = h.hostname
WHERE f.discoverymethod IS NOT NULL
  AND h.ra IS NOT NULL
GROUP BY f.discoverymethod
ORDER BY n_planets DESC
```

**Respuesta:**

| discoverymethod               | n_planets | avg_ra   |
| ----------------------------- | --------- | -------- |
| Transit                       | 4501      | 246.80305021544166 |
| Radial Velocity               | 1166      | 175.8875730628643 |
| Microlensing                  | 266       | 267.3047892255641 |
| Imaging                       | 92        | 182.8550375684783 |
| Transit Timing Variations     | 39        | 250.08277321538475 |
| Eclipse Timing Variations     | 17        | 223.4641836764706 |
| Orbital Brightness Modulation | 9         | 292.9125022444444 |
| Pulsar Timing                 | 8         | 218.743126825 |
| Astrometry                    | 6         | 235.42183843333336 |
| Pulsation Timing Variations   | 2         | 315.24251065 |
| Disk Kinematics               | 1         | 167.0133422 |
