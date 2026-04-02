# Log de Decisiones del Proyecto

---

## D1: Motor de Base de Datos
- **Fecha**: 2026-02-17
- **Decisión**: Usar DuckDB como motor OLAP local.
- **Razón**: Excelente para análisis, sin necesidad de servidor, compatible con Parquet.
- **Alternativas consideradas**: SQLite (OLTP, no óptimo para análisis), PostgreSQL (requiere servidor).
- **Impacto**: Facilita ETL local reproducible.
---

## D2: Guardar SHA-256 del CSV raw en artifacts

- **Fecha:** 2026-02-17
- **Decisión:** Calcular y persistir el hash SHA-256 del archivo `pscomppars.csv` en cada ejecución, guardándolo en `artifacts/w01b_raw_evidence_*.json`.
- **Razón:** Detectar cambios invisibles en el dato fuente (DDIA Cap. 1 — Reliability / Operability). Si el hash cambia entre ejecuciones sin que nosotros lo hayamos pedido, algo externo modificó el archivo (corrupción, descarga parcial, cambio del catálogo NASA).
- **Alternativas rechazadas:**
  - Confiar solo en el nombre del archivo → no detecta cambios de contenido.
  - Usar solo la fecha de descarga → tampoco detecta corrupción silenciosa.
  - Usar MD5 → colisiones conocidas; SHA-256 es el estándar actual para integridad.
- **Evidencia:** Ver `artifacts/w01b_raw_evidence_*.json` (campos `raw_sha256`, `n_rows`, `n_cols`).

---

## D3: Usar VIEW en lugar de TABLE para el raw

- **Fecha:** 2026-02-17
- **Decisión:** Crear `raw_ps` como `CREATE OR REPLACE VIEW` apuntando al CSV, nunca como TABLE.
- **Razón:** La capa Bronze/Raw NO se modifica (DDIA — trazabilidad). Una VIEW lee el CSV original en cada consulta; una TABLE haría una copia que podría divergir del original sin que lo notemos.
- **Alternativas rechazadas:**
  - `CREATE TABLE raw_ps AS SELECT * FROM read_csv_auto(...)` → crea copia desincronizada.
  - Leer el CSV directamente con `pd.read_csv` cada vez → rompe reproducibilidad en SQL.
- **Evidencia:** Celda 3 del notebook W01B — `CREATE OR REPLACE VIEW raw_ps AS SELECT * FROM read_csv_auto(...)`.

---

## Decisión 4: usar MEDIAN() en lugar de AVG() para el periodo orbital

**Decisión:** reportar `MEDIAN(pl_orbper)` como estadística central en el resumen por método de descubrimiento.

**Razón:** la distribución de periodos orbitales es fuertemente asimétrica, hay planetas con periodos de horas y otros de miles de días. El promedio es arrastrado por esos extremos y no representa al planeta típico de cada método. La mediana es más robusta y honesta como métrica de resumen.

**Evidencia:** para el método Transit, `AVG(pl_orbper)` supera los 30 días arrastrado por outliers, mientras que `MEDIAN(pl_orbper)` ≈ 5.8 días, valor más representativo de los planetas de tránsito conocidos.

---

## D5: Validar cardinalidad antes de un JOIN

- **Fecha:** 2026-02-21
- **Decisión:** Antes de hacer JOIN con cualquier tabla, verificar que la clave de la dimensión sea única (1 fila por clave) usando un conteo de duplicados.
- **Razón:** Si la dimensión tiene filas duplicadas por clave, el JOIN multiplica las filas de la fact table silenciosamente, generando datos falsos que inflan cualquier agregación (sumas, promedios, conteos). Esto es un error difícil de detectar a simple vista.
- **Alternativas rechazadas:**
  - Confiar en que la tabla ya es única sin verificar → no detecta duplicados introducidos en el ETL.
  - Usar `SELECT DISTINCT` directamente en el JOIN sin diagnosticar → oculta el problema en lugar de resolverlo.
- **Evidencia:**

```sql
-- Query de diagnóstico: detecta hostnames duplicados en dim_host_bad
WITH c AS (
    SELECT hostname, COUNT(*) AS cnt
    FROM dim_host_bad
    GROUP BY hostname
)
SELECT * FROM c
WHERE cnt > 1
ORDER BY cnt DESC
LIMIT 10;
```

| hostname   | cnt |
| ---------- | --- |
| KOI-351    | 8   |
| TRAPPIST-1 | 7   |
| HD 110067  | 6   |
| HD 191939  | 6   |
| TOI-178    | 6   |
| HD 10180   | 6   |
| Kepler-20  | 6   |
| Kepler-11  | 6   |
| HIP 41378  | 6   |
| HD 219134  | 6   |

## D6: Selección de 12 columnas para reporte de calidad W04A

- **Fecha:** 2026-03-06
- **Decisión:** Usar las columnas `pl_name`, `hostname`, `disc_year`, `discoverymethod`, `pl_orbper`, `pl_rade`, `pl_bmasse`, `sy_dist`, `ra`, `dec`, `sy_snum`, `sy_pnum` para el reporte de nulos.
- **Razón:** Cubren los 4 grupos clave del dataset (identificación, sistema, órbita y posición). Son las columnas más usadas en JOINs y agregaciones downstream, por lo que tener nulos en ellas tendría el mayor impacto en análisis posteriores.
- **Alternativas rechazadas:**
  - Incluir columnas estelares (`st_teff`, `st_rad`, `st_mass`) → tienen muchos nulos esperados y menos impacto en la granularidad del planeta.
  - Revisar todas las columnas → excede el alcance del reporte mínimo viable.
- **Evidencia:** Output de TU TURNO 1 en W04A — tabla de nulos ordenada por `nulls DESC`. `pl_name` y `hostname` resultaron con 0 nulos ✅; columnas como `pl_bmasse` y `sy_dist` mostraron los mayores porcentajes de nulos.

---

## D7: Reglas Silver aplicadas en `silver_planet`

- **Fecha:** 2026-03-06
- **Decisión:** Aplicar las siguientes reglas de filtrado al construir `silver_planet` desde `raw_ps`:
  1. `pl_name IS NOT NULL`
  2. `hostname IS NOT NULL`
  3. `disc_year` en [1980, 2026] si no es nulo
  4. `pl_rade` en (0, 30] si no es nulo
  5. `pl_bmasse > 0` si no es nulo
  6. `pl_orbper > 0` si no es nulo *(regla extra v1.0.1)*
- **Razón:** Solo se filtran valores **físicamente imposibles** (negativos o cero) y años fuera de rango. Los nulos se toleran para no perder cobertura innecesariamente — un nulo es "dato desconocido", no un dato erróneo.
- **Alternativas rechazadas:**
  - Filtrar filas con cualquier nulo → eliminaría la mayoría del dataset dado el alto porcentaje de nulos en `pl_bmasse` y `sy_dist`.
  - No filtrar nada → los 6 planetas con `pl_rade > 30` distorsionarían promedios en la capa Gold.
- **Evidencia:** `SELECT COUNT(*) AS n_rows, COUNT(DISTINCT pl_name) AS n_pl FROM silver_planet` confirma que `n_rows ≈ n_pl` (sin duplicados) y que las filas filtradas corresponden exactamente a los 6 detectados en el check `bad_pl_rade_range`.

---

## D8: Reescritura de consulta para reducir costo de lectura

- **Fecha:** 2026-03-19
- **Decisión:** Reemplazar `SELECT *` por `SELECT pl_name, hostname, disc_year` en consultas de filtrado sobre `fact_planet`.
- **Razón:** En almacenamiento columnar (DuckDB), cada columna se lee de forma   independiente desde disco. `SELECT *` obliga al motor a leer las 8 columnas de `fact_planet`, aunque la consulta solo necesite 3. Reducir las columnas proyectadas reduce directamente el I/O sin cambiar la lógica ni la cardinalidad.
- **Alternativas rechazadas:**
  - Mantener `SELECT *` por comodidad → costo de lectura innecesariamente alto, escalaría mal con datasets grandes.
  - Crear una vista pre-filtrada → agrega complejidad innecesaria para este caso.
- **Evidencia:** Comparación de planes `EXPLAIN` (TU TURNO 2, W04A):

| | Plan A (`SELECT *`) | Plan B (`SELECT skinny`) |
|---|---|---|
| Columnas leídas en SCAN | 8 | 3 |
| Cardinalidad estimada | ~1,220 | ~1,220 |
| Reducción de I/O | — | ~62% menos columnas |

Ambos planes tienen estructura idéntica (`SEQ_SCAN → PROJECTION`) y la misma
cardinalidad, confirmando que la diferencia es exclusivamente de ancho de banda
de lectura, no de filas procesadas.

---

## D9: Surrogate key + FK en modelo dim/fact

- **Fecha:** 2026-03-20
- **Decisión:** Usar `host_id` (entero generado con `ROW_NUMBER() OVER (ORDER BY hostname)`) como clave primaria en `dim_host_sk` y como Foreign Key en `fact_planet_sk`, en lugar de usar `hostname` directamente como clave de join.
- **Razón:** El surrogate key es un entero pequeño, nunca cambia y es más eficiente para índices y joins que un VARCHAR largo. Permite evolucionar el modelo (ej. renombrar una estrella) sin romper la integridad referencial. Es el estándar en modelado dimensional (Kimball).
- **Alternativas rechazadas:**
  - Usar `hostname` como FK directamente → el VARCHAR es más costoso en joins y si el nombre cambia, requiere actualizar todas las filas de la fact table.
  - No usar FK y confiar en el JOIN → no hay garantía de integridad referencial; planetas huérfanos podrían aparecer silenciosamente.
- **Evidencia:**
  - `COUNT(*) == COUNT(DISTINCT hostname)` en `dim_host_sk` ✅
  - `orphan_rows == 0` en `fact_planet_sk` ✅

---

## D10: Gold outputs y selección de métricas

- **Fecha:** 2026-03-20
- **Decisión:** Crear dos vistas Gold: `gold_by_discoverymethod` y `gold_by_host`, con las métricas `n_planets`, `avg_radius_earth`, `avg_mass_earth`, `first_year`/`last_year` (para método) y `sy_dist`, `ra`, `dec` (para host).
- **Razón:** Las dos vistas responden las preguntas científicas centrales del dataset: ¿qué métodos dominan el descubrimiento de exoplanetas? y ¿qué estrellas tienen más planetas y dónde están? Las métricas de radio y masa permiten comparar qué tipo de planeta encuentra cada método; `sy_dist`, `ra` y `dec` habilitan análisis espaciales por estrella.
- **Alternativas rechazadas:**
  - Un solo Gold agregado por ambas dimensiones → mezcla grains distintos y dificulta la interpretación.
  - Usar tablas en lugar de vistas → las vistas son más livianas y siempre reflejan el estado actual de `fact_planet_sk`; no hay necesidad de materializar para este volumen.
- **Evidencia:**
  - `artifacts/gold_by_discoverymethod.csv` exportado.
  - `artifacts/gold_by_host.csv` exportado.

---