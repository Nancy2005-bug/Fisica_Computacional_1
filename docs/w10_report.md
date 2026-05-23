# W10 — Reporte: Particionamiento y Partition Pruning

**Fecha:** 2026-05-14  
**Dataset:** NASA Exoplanet Archive — PSCompPars (`silver_planet_v3`)  
**Notebook:** `W10_student.ipynb`

---

## 1. Evidencia de particionamiento

Se particionó `silver_planet_v3` por la columna `disc_era` usando `COPY ... TO` de DuckDB,
generando 1 archivo CSV por era bajo la estructura `artifacts/silver_partitioned/disc_era=<valor>/data.csv`.

```
disc_era=2000s  → 378 filas  → artifacts/silver_partitioned/disc_era=2000s/data.csv
disc_era=2010s  → 3681 filas → artifacts/silver_partitioned/disc_era=2010s/data.csv
disc_era=2020s  → 2012 filas → artifacts/silver_partitioned/disc_era=2020s/data.csv
disc_era=pre-2000 → 30 filas → artifacts/silver_partitioned/disc_era=pre-2000/data.csv
```

## 2. Número de archivos generados

**Total: 4 archivos CSV**, uno por cada valor único de `disc_era`:

```
artifacts\silver_partitioned\disc_era=2000s\data.csv
artifacts\silver_partitioned\disc_era=2010s\data.csv
artifacts\silver_partitioned\disc_era=2020s\data.csv
artifacts\silver_partitioned\disc_era=pre-2000\data.csv
```

## 3. Resumen por partición

| disc_era | n_planets | primer_año | último_año |
|----------|-----------|------------|------------|
| 2000s    | 378       | 2000       | 2009       |
| 2010s    | 3681      | 2010       | 2019       |
| 2020s    | 2012      | 2020       | 2026       |
| pre-2000 | 30        | 1992       | 1999       |
| **Total**| **6101**  | 1992       | 2026       |

La era `2010s` concentra el **60.3%** del total (3681 planetas), reflejo del boom de
descubrimientos del telescopio Kepler (2009-2018). La era `pre-2000` es la más pequeña
con solo 30 planetas — los primeros exoplanetas confirmados.

## 4. Evidencia de pruning

Se ejecutó `EXPLAIN ANALYZE` con el filtro `WHERE disc_era = '2010s'`:

```sql
EXPLAIN ANALYZE
SELECT COUNT(*), AVG(pl_rade)
FROM silver_planet_v3
WHERE disc_era = '2010s';
```

El plan resultante muestra un `SEQ_SCAN` con filtro de predicado sobre `disc_era`,
confirmando que DuckDB aplica el filtro directamente sobre la columna particionada.
El resultado completo se guardó en `artifacts/w10b_explain_analyze_pruning.txt`.

## 5. Archivo de evidencia de pruning

`artifacts/w10b_explain_analyze_pruning.txt` — contiene el output completo de
`EXPLAIN ANALYZE` para la consulta filtrada por `disc_era = '2010s'`.

## 6. Filtro utilizado

Se usó el filtro `WHERE disc_era = '2010s'` porque es la partición más grande
(3681 planetas, 60.3% del total), lo que hace más visible el efecto del pruning:
al consultar solo esa era, el motor evita leer las otras 3 particiones (~2420 filas).

---

## 7. Decisión de partición

La columna elegida para particionar fue **`disc_era`** (clasificación por década de descubrimiento).

## 8. ¿Por qué `disc_era` sí?

`disc_era` es una buena columna de partición por tres razones:

1. **Cardinalidad baja y controlada:** solo 4 valores únicos → 4 particiones, número manejable
2. **Patrón de consulta real:** las preguntas científicas más comunes filtran por período
   temporal ("¿cuántos planetas se descubrieron en la era Kepler?", "¿cómo cambió el radio
   promedio por década?")
3. **Distribución razonablemente balanceada:** las eras `2010s` (3681) y `2020s` (2012)
   dominan, pero ninguna partición está completamente vacía

## 9. Otra columna a evaluar

**`discoverymethod_canon`** sería la siguiente columna a evaluar para particionamiento:
- Cardinalidad baja: 11 valores únicos
- Muy consultada en análisis Gold (`gold_by_discoverymethod`)
- Permite responder preguntas como "¿cuál es el radio promedio de planetas descubiertos
  por tránsito?" sin leer planetas de otros métodos
- **Riesgo:** la distribución es muy desigual — `transit` tiene 4500 planetas mientras
  `disk_kinematics` tiene 1, lo que generaría particiones extremadamente desbalanceadas

## 10. Riesgo de small files encontrado

La partición **`pre-2000`** con solo **30 filas** es un caso claro de _small files problem_:
- Un archivo CSV de 30 filas tiene más overhead de apertura y metadata que datos útiles
- Si el dataset creciera a millones de filas, esta partición seguiría siendo diminuta
- En sistemas de archivos distribuidos (HDFS, S3), abrir un archivo tiene un costo fijo
  independiente de su tamaño — muchos archivos pequeños degradan el throughput global

---

## 11. Reflexión breve

## 12. ¿Cuándo particionar ayuda?

Particionar ayuda cuando:
- Las consultas **filtran frecuentemente** por la columna de partición (alta selectividad)
- Las particiones son de **tamaño balanceado** (evita skew)
- El dataset es **lo suficientemente grande** como para que el overhead de múltiples
  archivos sea menor que el costo de leer datos irrelevantes
- La cardinalidad de la columna es **baja** (< ~100 valores únicos)

## 13. ¿Cuándo particionar empeora el diseño?

Particionar empeora cuando:
- La columna tiene **alta cardinalidad** (ej. `pl_name` → 6101 particiones de 1 fila cada una)
- Las consultas **no filtran** por la columna de partición y deben leer todas las particiones
  de todas formas (full scan sin beneficio de pruning)
- El dataset es **pequeño** (como el nuestro con 6101 filas): el overhead de gestionar
  4 archivos puede superar al beneficio de evitar leer ~2420 filas adicionales
- Las particiones están **muy desbalanceadas** (como `discoverymethod_canon`): la partición
  grande domina el tiempo de ejecución y el pruning no ayuda en el caso más común
