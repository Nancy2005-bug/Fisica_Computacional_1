# W02B — JOINs + CTEs + cardinalidad — EJEMPLO LLENO

## Evidencia de cardinalidad
- n_fact = 48000
- n_join_good = 47000
- n_join_bad = 135000
- n_join_fixed = 47000
Interpretación:
- `dim_host_bad` no era 1 fila por hostname → el JOIN multiplicó filas.
- Al deduplicar, el conteo vuelve a la escala del fact.

## TODO 1 — LEFT JOIN (no-match)
SQL:
```sql
SELECT COUNT(*) AS no_match
FROM fact_planet_raw f
LEFT JOIN dim_host h
  ON f.hostname = h.hostname
WHERE f.hostname IS NOT NULL AND h.hostname IS NULL;
```
Resultado:
- [(120,)]

## TODO 2 — CTE + window (top método por año)
SQL:
```sql
WITH counts AS (
  SELECT disc_year, discoverymethod, COUNT(*) AS n
  FROM fact_planet_raw
  WHERE disc_year IS NOT NULL AND discoverymethod IS NOT NULL
  GROUP BY disc_year, discoverymethod
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY disc_year ORDER BY n DESC) AS rn
  FROM counts
)
SELECT disc_year, discoverymethod, n
FROM ranked
WHERE rn = 1
ORDER BY disc_year DESC
LIMIT 20;
```
Resultado (ejemplo):
- [(2024,'Transit',410), (2023,'Transit',390), ...]

## TODO 3 — Validación de duplicados en dim_discovery
SQL:
```sql
SELECT discoverymethod, disc_year, COUNT(*) AS c
FROM dim_discovery
GROUP BY discoverymethod, disc_year
HAVING COUNT(*) > 1
ORDER BY c DESC
LIMIT 10;
```
Resultado:
- []  (si no hay duplicados)

## TODO 4 — JOIN + agregación
SQL:
```sql
SELECT f.discoverymethod, AVG(h.st_teff) AS avg_teff, COUNT(*) AS n
FROM fact_planet_raw f
JOIN dim_host h ON f.hostname = h.hostname
WHERE f.discoverymethod IS NOT NULL AND h.st_teff IS NOT NULL
GROUP BY f.discoverymethod
ORDER BY n DESC;
```
Resultado:
- [('Transit', 5400.1, 18000), ...]

## Extras
### Extra 1 (JOIN)
SQL:
```sql
SELECT h.sy_snum, COUNT(*) AS n_planets
FROM fact_planet_raw f
JOIN dim_host h ON f.hostname = h.hostname
WHERE h.sy_snum IS NOT NULL
GROUP BY h.sy_snum
ORDER BY n_planets DESC;
```
Resultado:
- [(1, 42000), (2, 5200), ...]

### Extra 2 (CTE)
SQL:
```sql
WITH per_host AS (
  SELECT hostname, COUNT(*) AS n
  FROM fact_planet_raw
  WHERE hostname IS NOT NULL
  GROUP BY hostname
)
SELECT
  CASE WHEN n >= 5 THEN '>=5'
       WHEN n >= 3 THEN '3-4'
       WHEN n = 2 THEN '2'
       ELSE '1' END AS bucket,
  COUNT(*) AS n_systems
FROM per_host
GROUP BY bucket
ORDER BY bucket;
```
Resultado:
- [('1', 12000), ('2', 1800), ('3-4', 400), ('>=5', 50)]
