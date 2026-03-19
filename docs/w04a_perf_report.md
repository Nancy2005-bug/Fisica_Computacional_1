# # W04A — Cómo “piensa” el motor: **EXPLAIN**, cardinalidad y performance (DuckDB)

## Plan 1: Consulta métrica (WHERE + GROUP BY)

```sql
SELECT
    discoverymethod,
    disc_year,
    COUNT(*) AS n_planets
FROM fact_planet
WHERE disc_year >= 2010
GROUP BY discoverymethod, disc_year
ORDER BY disc_year, n_planets DESC
```

**Resultado:**

### EXPLAIN ANALYZE (plan real)

```
Total Time: 0.0040s

TABLE_SCAN fact_planet
  Projections: disc_year, discoverymethod
  Filters:     disc_year >= 2010
  Real: 5,692 rows  (0.00s)

HASH_GROUP_BY (Groups: discoverymethod, disc_year | count_star())
  Real: 104 rows  (0.01s)  ← operador más costoso

ORDER_BY disc_year ASC, n_planets DESC
  Real: 104 rows  (0.00s)

PROJECTION (decompress disc_year)
  Real: 104 rows  (0.00s)
```

**Conclusión 1: Dónde está el costo?**
El operador más costoso es el HASH_GROUP_BY (0.01s): recibe 5,692 filas reales y las colapsa en 104 grupos únicos de discoverymethod × disc_year. El estimador subestimó la cardinalidad del SCAN en ~4.7× (1,220 estimado vs 5,692 real), aunque el plan sigue siendo eficiente.

**Conclusión 2: Qué está bien y qué mejoraría?**
El filter pushdown funciona correctamente: `disc_year >= 2010` se aplica directamente en el SCAN, y solo se leen 2 columnas (`disc_year`, `discoverymethod`) en lugar de las 8 que tiene `fact_planet` (`pl_name`, `hostname`, `discoverymethod`, `disc_year`, `pl_orbper`, `pl_rade`, `pl_bmasse`, `pl_eqt`). Si el dataset creciera 100×, el `HASH_GROUP_BY` con ~570,000 filas sería el cuello de botella por consumo de memoria; la mejora sería acotar más el rango de años o pre-filtrar en una CTE materializada antes del GROUP BY.

## Plan 2: SELECT * vs SELECT skinny

```sql
-- Plan A
SELECT * FROM fact_planet WHERE disc_year >= 2015

-- Plan B
SELECT pl_name, hostname, disc_year FROM fact_planet WHERE disc_year >= 2015
```

### Comparación de proyecciones en el SCAN

| | Plan A (SELECT *) | Plan B (SELECT skinny) |
|---|---|---|
| Columnas en SCAN | disc_year, pl_name, hostname, discoverymethod, pl_orbper, pl_rade, pl_bmasse, pl_eqt | disc_year, pl_name, hostname |
| Total columnas leídas | 8 | 3 |
| Cardinalidad estimada | ~1,220 | ~1,220 |

### Conclusión — Por qué importa en almacenamiento columnar
Ambos planes tienen exactamente la misma estructura (`SEQ_SCAN` → `PROJECTION`) y la misma cardinalidad estimada (~1,220 filas), porque el filtro `disc_year >= 2015` es idéntico. La diferencia está únicamente en las columnas que el SCAN lee de disco: Plan A carga 8 columnas, Plan B solo 3 (~62% menos I/O). En DuckDB (almacenamiento columnar), cada columna se almacena y lee de forma independiente, por lo que `SELECT *` tiene un costo de lectura proporcional al número de columnas. Con un dataset 100× mayor, esta diferencia sería directamente observable en el tiempo de ejecución.


## Plan 3: JOIN fact_planet + dim_host_full

```sql
SELECT
    f.hostname,
    d.st_teff,
    COUNT(f.pl_name) AS n_planets
FROM fact_planet f
LEFT JOIN dim_host_full d USING (hostname)
GROUP BY f.hostname, d.st_teff
ORDER BY n_planets DESC
LIMIT 20
```

### Plan (EXPLAIN)
```
SEQ_SCAN fact_planet
  Projections: hostname, pl_name
  ~6,101 rows

SEQ_SCAN dim_host_full
  Projections: hostname, st_teff
  ~4,550 rows

HASH_JOIN (LEFT) ON hostname = hostname
  ~6,101 rows

HASH_GROUP_BY (Groups: hostname, st_teff | count_star())
  ~6,099 rows

TOP_N 20 ORDER BY n_planets DESC
```

### Evidencia de JOIN sano
| Métrica | Valor |
|---|---|
| n_fact | 6,101 |
| n_join | 6,101 |
| ¿Infla? | ✅ No — cardinalidad idéntica |

### Conclusión — JOIN sano
`n_fact == n_join` (6,101 = 6,101): el LEFT JOIN no infla la cardinalidad porque `dim_host_full` tiene exactamente 1 fila por `hostname` (fue construida con `GROUP BY hostname`). El motor usa un `HASH_JOIN`, típico en analítica OLAP. Si `dim_host_full` tuviera duplicados en `hostname`, `n_join > n_fact` y todas las métricas agregadas posteriores serían incorrectas.

## Reflexión (bitácora)

**¿Qué parte del plan te costó más interpretar?**
Los nodos `PROJECTION __internal_compress_integral_utinyint` fueron los más confusos al inicio, ya que aparecen múltiples veces sin ser parte del costo real. Una vez entendido que son optimizaciones internas de DuckDB para comprimir enteros (codificación delta de `disc_year` respecto al año base 2010), resultó claro que no representan operaciones costosas y pueden ignorarse en el análisis de performance.

**Si el dataset creciera 100×, ¿qué operador empeora primero y por qué?**
El `HASH_GROUP_BY` empeora primero. Actualmente recibe 5,692 filas y las colapsa en 104 grupos usando una hash table en memoria. Con 100× de datos (~570,000 filas), la hash table podría exceder la memoria disponible y forzar spill a disco, aumentando el tiempo drásticamente. El `TABLE_SCAN` también escalaría, pero al leer solo 2 columnas en almacenamiento columnar su crecimiento sería más lineal y controlable.
