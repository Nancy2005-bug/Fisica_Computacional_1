# W08 — Reporte: SQL Limpieza + Many-to-Many

**Fecha:** 2026-05-14  
**Dataset:** NASA Exoplanet Archive — PSCompPars (`pscomppars.csv`)  
**Filas raw:** 6107

***

## Parte A — Limpieza Raw → Silver v2

### A1: Tabla `method_map`

Se creó una tabla de mapeo con 10 entradas que normaliza los nombres crudos de métodos de descubrimiento a un formato canónico (`snake_case` en minúsculas).

| raw_method | canonical_method |
|---|---|
| Transit | transit |
| Radial Velocity | radial_velocity |
| Imaging | imaging |
| Microlensing | microlensing |
| Transit Timing Variations | transit_timing_variations |
| Eclipse Timing Variations | eclipse_timing_variations |
| Astrometry | astrometry |
| Orbital Brightness Modulation | orbital_brightness_modulation |
| Pulsar Timing | pulsar_timing |
| Pulsation Timing Variations | pulsation_timing_variations |

**Método no mapeado:** `Disk Kinematics` (1 planeta) → queda como `disk kinematics` vía el `LOWER(TRIM(...))` del fallback `COALESCE`.

***

### A2: Tabla `silver_planet_v2`

**Resultados de validación:**

| métrica | valor |
|---|---|
| `n_rows` | **6101** |
| `n_null_hosts` | **0**  |
| métodos únicos | **11** |

**Distribución por `discoverymethod_clean`:**

| discoverymethod_clean | n |
|---|---|
| transit | 4500 |
| radial_velocity | 1166 |
| microlensing | 266 |
| imaging | 87 |
| transit_timing_variations | 39 |
| eclipse_timing_variations | 17 |
| orbital_brightness_modulation | 9 |
| pulsar_timing | 8 |
| astrometry | 6 |
| pulsation_timing_variations | 2 |
| disk kinematics | 1 |

**Columnas nuevas añadidas respecto a `silver_planet`:**

- `hostname_clean` = `LOWER(TRIM(hostname))` — estandariza mayúsculas y espacios
- `discoverymethod_norm` = `LOWER(TRIM(discoverymethod))` — forma intermedia antes del mapeo
- `discoverymethod_clean` = `COALESCE(canonical_method, discoverymethod_norm)` — forma final normalizada
- `disc_era` = clasificación por década:
  - `'pre-2000'` → antes del año 2000
  - `'2000s'` → 2000–2009
  - `'2010s'` → 2010–2019
  - `'2020s'` → 2020 en adelante

***

## Parte B — Many-to-Many (toy schema)

### DDL: esquema M:N con link table y PK/FK

```sql
CREATE TABLE planet_demo(
    planet_id INTEGER PRIMARY KEY,
    name      VARCHAR NOT NULL
);

CREATE TABLE method_demo(
    method_id   INTEGER PRIMARY KEY,
    method_name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE planet_method_demo(
    planet_id INTEGER NOT NULL,
    method_id INTEGER NOT NULL,
    PRIMARY KEY (planet_id, method_id),
    FOREIGN KEY (planet_id) REFERENCES planet_demo(planet_id),
    FOREIGN KEY (method_id) REFERENCES method_demo(method_id)
);
```

### Datos insertados

**4 planetas:**

| planet_id | name |
|---|---|
| 1 | Kepler-22b |
| 2 | HD 209458 b |
| 3 | 51 Peg b |
| 4 | TRAPPIST-1b |

**3 métodos:**

| method_id | method_name |
|---|---|
| 10 | transit |
| 20 | radial_velocity |
| 30 | imaging |

**6 relaciones M:N** (Kepler-22b y HD 209458 b tienen 2 métodos cada uno):

| planet_id | method_id |
|---|---|
| 1 | 10 |
| 1 | 20 |
| 2 | 10 |
| 2 | 20 |
| 3 | 20 |
| 4 | 10 |

***

### Q1: Planetas por método

```sql
SELECT m.method_name, COUNT(DISTINCT pm.planet_id) AS n_planets
FROM planet_method_demo pm
JOIN method_demo m ON pm.method_id = m.method_id
GROUP BY m.method_name
ORDER BY n_planets DESC;
```

| method_name | n_planets |
|---|---|
| transit | 3 |
| radial_velocity | 3 |

***

### Q2: Métodos por planeta

```sql
SELECT p.name, COUNT(DISTINCT pm.method_id) AS n_methods
FROM planet_method_demo pm
JOIN planet_demo p ON pm.planet_id = p.planet_id
GROUP BY p.name
ORDER BY n_methods DESC;
```

| name | n_methods |
|---|---|
| Kepler-22b | 2 |
| HD 209458 b | 2 |
| TRAPPIST-1b | 1 |
| 51 Peg b | 1 |

***

### B2: Check de duplicados en la link table

```sql
SELECT planet_id, method_id, COUNT(*) AS c
FROM planet_method_demo
GROUP BY planet_id, method_id
HAVING COUNT(*) > 1;
```

**Resultado: 0 filas**  — la PK compuesta `(planet_id, method_id)` garantiza integridad y bloquea duplicados correctamente.

***

## Conclusión

- `silver_planet_v2` produce 6101 filas con 0 hosts nulos, incorporando normalización de métodos y clasificación por era de descubrimiento.
- El esquema M:N demuestra que una link table con PK compuesta y FK a ambas dimensiones es la forma correcta de modelar relaciones muchos-a-muchos en SQL.
- El check `HAVING COUNT(*) > 1` retorna 0 filas, confirmando integridad referencial correcta.