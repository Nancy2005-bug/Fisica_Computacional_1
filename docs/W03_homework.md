# W03 – SQL esencial II (JOINs + CTEs) y cardinalidad práctica

## DEMOS

### DEMO 3: JOIN correcto (many-to-one)
`fact_planet_raw` → `dim_host` debería ser muchos-a-uno. Si `dim_host` tiene hostname único, no debe multiplicar filas.

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

**Interpretación:** `dim_host_ra` tiene hostname único gracias al GROUP BY, por lo que cada planeta encontró exactamente un host y no se generaron filas extra.

### DEMO 4: JOIN “malo” (duplica filas)
Error común: unirse a una tabla que no es dimensión (llave no única). Fabricamos una “dimensión mala” a propósito.

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

**Interpretación:** `dim_host_bad` tiene múltiples filas por hostname porque no se deduplicó. Al hacer JOIN, cada planeta se multiplicó por el número de veces que aparece su host en la dimensión. Esto genera filas falsas que inflarían cualquier agregación (sumas, promedios, conteos).

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

## Tarea 

### Caso real de JOIN malo

Se construyó `dim_discovery_bad` seleccionando `discoverymethod` y `disc_year`
directamente desde `raw_ps` sin deduplicar. Como `raw_ps` tiene múltiples
planetas por combinación de método+año, la tabla quedó con miles de filas
duplicadas por clave, violando el principio de 1 fila por clave en una dimensión.

### Se crea la dimensión mala (sin deduplicar)

```sql
CREATE OR REPLACE TABLE dim_discovery_bad AS
SELECT discoverymethod, disc_year
FROM raw_ps
WHERE discoverymethod IS NOT NULL
```

**Respuesta:** [(6107,)]



### Evidencia: conteos antes/después

```sql
SELECT count(*) FROM fact_planet_raw f
JOIN dim_discovery_bad d
    ON f.discoverymethod = d.discoverymethod
    AND f.disc_year = d.disc_year
```

**Respuesta:** (6107, 3246616), el JOIN multiplicó las filas por los duplicados
de la dimensión, generando más de 3 millones de filas falsas.

### Diagnóstico

La clave compuesta (discoverymethod, disc_year) no era única. El siguiente query evidencia los duplicados:

```sql
WITH c AS (
    SELECT discoverymethod, disc_year, COUNT(*) AS cnt
    FROM dim_discovery_bad
    GROUP BY discoverymethod, disc_year
)
SELECT * FROM c WHERE cnt > 1
ORDER BY cnt DESC LIMIT 10
```

**Respuesta:**

| discoverymethod | disc_year | cnt  |
| --------------- | --------- | ---- |
| Transit         | 2016      | 1432 |
| Transit         | 2014      | 798  |
| Transit         | 2021      | 457  |
| Transit         | 2018      | 242  |
| Transit         | 2023      | 224  |
| Transit         | 2022      | 191  |
| Transit         | 2024      | 187  |
| Transit         | 2020      | 165  |
| Transit         | 2025      | 141  |
| Radial Velocity | 2022      | 118  |

### Fix deduplicar con SELECT DISTINCT en un CTE

```sql
WITH dim_discovery_fixed AS (
    SELECT DISTINCT discoverymethod, disc_year
    FROM dim_discovery_bad
)
SELECT count(*)
FROM fact_planet_raw f
JOIN dim_discovery_fixed d
    ON f.discoverymethod = d.discoverymethod
    AND f.disc_year = d.disc_year
```

**Respuesta:** (6107, 6106)

## Consultas

### Consulta con JOIN: radio promedio y RA del host por método de descubrimiento

Para cada método de descubrimiento, contar planetas, calcular el radio promedio y el promedio de ascensión recta (RA) de su estrella host.

```sql
SELECT
    f.discoverymethod,
    COUNT(f.pl_name)  AS n_planets,
    AVG(f.pl_rade)    AS avg_radius,
    AVG(h.ra)         AS avg_ra_host
FROM fact_planet_raw f
JOIN dim_host_ra h
    ON f.hostname = h.hostname
WHERE f.pl_rade IS NOT NULL
GROUP BY f.discoverymethod
ORDER BY n_planets DESC
```

**Respuesta:**

| discoverymethod               | n_planets | avg_radius | avg_ra_host |
| ----------------------------- | --------- | ---------- | ----------- |
| Transit                       | 4500      | 4.3681517920999795     | 246.7852594702449    |
| Radial Velocity               | 1129      | 9.759872661948618     | 175.17889449716594    |
| Microlensing                  | 266       | 9.85056390977442     | 267.304789225564    |
| Imaging                       | 88        | 15.612215793749998    | 187.85226858863635    |
| Transit Timing Variations     | 38        | 6.493408364210527     | 249.09091006315788    |
| Eclipse Timing Variations     | 15        | 12.893333333333338    | 246.07681240666668    |
| Astrometry                    | 6         | 12.450000000000001    | 235.42183843333336    |
| Orbital Brightness Modulation | 6         | 9.64504     | 295.67413796666665    |
| Pulsar Timing                 | 6         | 5.411333333333334     | 205.80759890000002    |
| Pulsation Timing Variations   | 2         | 12.75    | 315.24251065    |
| Disk Kinematics               | 1         | 13.3    | 167.0133422    |

### Consulta con CTE: sistemas con 4 o más planetas

Identificar los sistemas estelares con al menos 4 planetas conocidos y mostrar su posición en el cielo (RA).

```sql
WITH sistemas_grandes AS (
    SELECT hostname, COUNT(*) AS n_planetas
    FROM fact_planet_raw
    WHERE hostname IS NOT NULL
    GROUP BY hostname
    HAVING COUNT(*) >= 4
)
SELECT
    s.hostname,
    s.n_planetas,
    h.ra
FROM sistemas_grandes s
JOIN dim_host_ra h
    ON s.hostname = h.hostname
ORDER BY n_planetas DESC
LIMIT 15
```

| hostname   | n_planetas | ra       |
| ---------- | ---------- | -------- |
| KOI-351    | 8          | 284.4334642 |
| TRAPPIST-1 | 7          | 346.6263919 |
| Kepler-11  | 6          | 297.1150949 |
| TOI-1136   | 6          | 192.1848981 |
| HIP 41378  | 6          | 126.6158279 |
| HD 10180   | 6          | 24.4731133  |
| TOI-178    | 6          | 7.3020115   |
| Kepler-80  | 6          | 296.1125759 |
| HD 34445   | 6          | 79.4207483  |
| HD 110067  | 6          | 189.8392243 |
| K2-138     | 6          | 348.9490311 |
| Kepler-20  | 6          | 287.6979913 |
| HD 191939  | 6          | 302.0256247 |
| HD 219134  | 6          | 348.3372026 |
| GJ 667 C   | 5          | 259.7510609 |