# W09 — Reporte: Limpieza Avanzada + Quality Gates

**Fecha:** 2026-05-14  
**Dataset:** NASA Exoplanet Archive — PSCompPars  
**Notebook:** `assignments/W09_assignment_student.ipynb`

***

## Parte A — Limpieza avanzada

### TODO 1: Tabla `method_synonyms`

Se creó una tabla de sinónimos con 11 entradas que mapea formas normalizadas (`LOWER(TRIM(...))`) de los métodos de descubrimiento a sus formas canónicas en `snake_case`.

**Diferencia clave respecto a `method_map` (W08):** en `method_synonyms` la clave `raw_norm` ya está pre-normalizada (todo en minúsculas), lo que simplifica el JOIN en la capa Silver — no se necesita aplicar `LOWER(TRIM(...))` en el lado del mapa porque ya viene normalizado.

| raw_norm | canonical |
|---|---|
| transit | transit |
| radial velocity | radial_velocity |
| imaging | imaging |
| microlensing | microlensing |
| transit timing variations | transit_timing_variations |
| eclipse timing variations | eclipse_timing_variations |
| astrometry | astrometry |
| orbital brightness modulation | orbital_brightness_modulation |
| pulsar timing | pulsar_timing |
| pulsation timing variations | pulsation_timing_variations |
| disk kinematics | disk_kinematics |

Total: **11 entradas** — cubre el 100% de los métodos presentes en `raw_ps`.

***

### TODO 2: Tabla `silver_planet_v3`

**Columnas nuevas respecto a versiones anteriores:**

| columna | transformación | propósito |
|---|---|---|
| `hostname_canon` | `LOWER(TRIM(hostname))` | Estandariza capitalización y espacios |
| `discoverymethod_norm` | `LOWER(TRIM(discoverymethod))` | Forma intermedia para JOIN |
| `discoverymethod_canon` | `COALESCE(s.canonical, discoverymethod_norm)` | Forma canónica final |
| `disc_year_int` | `TRY_CAST(disc_year AS INTEGER)` | Cast seguro — retorna NULL si falla |
| `disc_year_bad` | `CASE` con rango  | Flag booleano de años fuera de rango |

**Resultados de validación:**

| métrica | valor |
|---|---|
| `n_rows` | **6101** |
| `disc_year_bad` (filas con año inválido) | **1** |

El uso de `TRY_CAST` en lugar de `CAST` es fundamental: evita que un valor no numérico en `disc_year` rompa la tabla entera, retornando `NULL` de forma segura. La fila con `disc_year_bad = true` corresponde a un planeta cuyo año de descubrimiento está fuera del rango válido .

***

## Parte B — Quality Gates

### TODO 3: Tabla `quality_events`

Se creó una tabla de auditoría con 4 checks automáticos ejecutados en el momento de la construcción de `silver_planet_v3`.

**Schema:**
```sql
CREATE TABLE quality_events(
    ts_utc       TIMESTAMPTZ,
    check_name   VARCHAR,
    status       VARCHAR,   -- 'PASS', 'WARN', 'FAIL'
    metric_value DOUBLE,
    details      VARCHAR
)
```

**Resultados:**

| check_name | status | metric_value | interpretación |
|---|---|---|---|
| `canonical_method_count` | **PASS** | 11.0 | 11 métodos canónicos únicos  |
| `disc_year_bad_count` | **WARN** | 1.0 | 1 fila con año fuera de rango  |
| `null_hostname_canon` | **PASS** | 0.0 | 0 hosts nulos  |
| `row_count_silver_v3` | **PASS** | 6101.0 | 6101 ≥ 6000  |

**3 PASS, 1 WARN** — el pipeline es aceptable. El WARN en `disc_year_bad_count` indica una fila con año de descubrimiento fuera del rango válido , pero no bloquea el pipeline porque es un caso aislado y el dato puede conservarse para análisis futuros.