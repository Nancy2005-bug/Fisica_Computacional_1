# W02B — Caso real de JOIN malo (evidencia + fix) — EJEMPLO LLENO

## Contexto
Uní `fact_planet_raw` con una tabla “dimensional” construida desde raw para traer `sy_dist` por `hostname`.

## Evidencia (antes/después)

Fact:
```sql
SELECT COUNT(*) FROM fact_planet_raw;
```
Resultado:
- [(48000,)]

Dim (mal construida, sin dedupe):
```sql
CREATE OR REPLACE TABLE dim_host_bad AS
SELECT hostname, sy_dist
FROM raw_ps
WHERE hostname IS NOT NULL;

SELECT COUNT(*) FROM dim_host_bad;
```
Resultado:
- [(52000,)]

JOIN malo:
```sql
SELECT COUNT(*)
FROM fact_planet_raw f
JOIN dim_host_bad h ON f.hostname = h.hostname;
```
Resultado:
- [(135000,)]

Clave usada: hostname

## Diagnóstico
`dim_host_bad` tiene múltiples filas por `hostname` (raw repite hostname por planeta) → many-to-many accidental.

Evidencia:
```sql
SELECT hostname, COUNT(*) AS c
FROM dim_host_bad
GROUP BY hostname
HAVING COUNT(*) > 1
ORDER BY c DESC
LIMIT 5;
```
Resultado:
- [('TRAPPIST-1', 7), ...]

## Fix (DISTINCT en CTE)
```sql
WITH dim_host_fixed AS (
  SELECT DISTINCT hostname, sy_dist
  FROM dim_host_bad
)
SELECT COUNT(*)
FROM fact_planet_raw f
JOIN dim_host_fixed h ON f.hostname = h.hostname;
```
Resultado:
- [(47000,)]

## Reflexión
- Validación mínima: probar unicidad en la “dimensión” (GROUP BY clave HAVING count>1).
- Prefiero LEFT JOIN cuando quiero auditar no-match y no perder filas del fact.
