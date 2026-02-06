# W02A — SQL esencial (práctica) — EJEMPLO LLENO

> Nota: los números exactos pueden variar según el snapshot del catálogo.

## Q1 — Muestra básica
SQL:
```sql
SELECT pl_name, hostname, discoverymethod, disc_year
FROM raw_ps
WHERE pl_name IS NOT NULL
LIMIT 10;
```
Resultado (ejemplo):
- [('Kepler-10 b','Kepler-10','Transit',2011), ('Kepler-10 c','Kepler-10','Transit',2011), ...]

## Q2 — Años más recientes (no nulos)
SQL:
```sql
SELECT pl_name, disc_year
FROM raw_ps
WHERE disc_year IS NOT NULL
ORDER BY disc_year DESC
LIMIT 10;
```
Resultado:
- [('TOI-XXXX b', 2024), ...]

## Q3 — Conteo por método
SQL:
```sql
SELECT discoverymethod, COUNT(*) AS n
FROM raw_ps
WHERE discoverymethod IS NOT NULL
GROUP BY discoverymethod
ORDER BY n DESC
LIMIT 10;
```
Resultado:
- [('Transit', 25000), ('Radial Velocity', 9000), ...]

## Q4 — Top 10 hostnames por número de planetas
SQL:
```sql
SELECT hostname, COUNT(*) AS n
FROM raw_ps
WHERE hostname IS NOT NULL
GROUP BY hostname
ORDER BY n DESC
LIMIT 10;
```
Resultado:
- [('TRAPPIST-1', 7), ...]

## Q5 — Calidad: nulos en pl_rade
SQL:
```sql
SELECT
  COUNT(*) AS total,
  SUM(CASE WHEN pl_rade IS NULL THEN 1 ELSE 0 END) AS nulls_pl_rade
FROM raw_ps;
```
Resultado:
- [(50000, 12000)]

## Q6 — Calidad: radios <= 0
SQL:
```sql
SELECT COUNT(*) AS bad_radius
FROM raw_ps
WHERE pl_rade IS NOT NULL AND pl_rade <= 0;
```
Resultado:
- [(0,)]

## Q7 — 3 conceptos: WHERE + GROUP BY + ORDER BY
SQL:
```sql
SELECT disc_year, COUNT(*) AS n
FROM raw_ps
WHERE disc_year IS NOT NULL
GROUP BY disc_year
ORDER BY n DESC
LIMIT 15;
```
Resultado:
- [(2016, 3200), (2014, 2900), ...]

## Q8 — Agregación + WHERE: promedio radio por método
SQL:
```sql
SELECT discoverymethod, AVG(pl_rade) AS avg_r
FROM raw_ps
WHERE discoverymethod IS NOT NULL AND pl_rade IS NOT NULL
GROUP BY discoverymethod
ORDER BY avg_r DESC
LIMIT 10;
```
Resultado:
- [('Imaging', 12.3), ('Microlensing', 6.8), ...]

## Q9 — “Pregunta científica”: dominante por década
SQL:
```sql
SELECT (disc_year/10)*10 AS decade, discoverymethod, COUNT(*) AS n
FROM raw_ps
WHERE disc_year IS NOT NULL AND discoverymethod IS NOT NULL
GROUP BY decade, discoverymethod
ORDER BY decade DESC, n DESC
LIMIT 30;
```
Resultado:
- [(2010,'Transit',18000), (2010,'Radial Velocity',2500), ...]
Interpretación:
- En 2010s domina Transit (era Kepler/TESS).

## Q10 — “Pregunta científica”: tendencia anual
SQL:
```sql
SELECT disc_year, COUNT(*) AS n
FROM raw_ps
WHERE disc_year IS NOT NULL
GROUP BY disc_year
ORDER BY disc_year ASC;
```
Resultado:
- [(1995, 5), (1996, 8), ..., (2016, 3200), ...]
Interpretación:
- Crecimiento fuerte en 2010+.

## Reflexión
- Más difícil: Q9 (GROUP BY doble).
- Si creciera 100×: Q10 y Q9 por escaneo + agregación; conviene pre-agregar o particionar por año.
