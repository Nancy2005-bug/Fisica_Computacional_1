# Data Contract — Exoplanets Pipeline
**Versión:** v2 (W06)  
**Fecha:** 2026-03-20  
**Fuente:** NASA Exoplanet Archive — PSCompPars (`pscomppars.csv`)

---

## Tablas y Grain

| Tabla / Vista              | Grain                        | Tipo  |
|----------------------------|------------------------------|-------|
| `silver_planet`            | 1 fila por `pl_name`         | Table |
| `dim_host_full`            | 1 fila por `hostname`        | Table |
| `fact_planet`              | 1 fila por `pl_name`         | Table |
| `dim_host_sk`              | 1 fila por `hostname`        | Table |
| `fact_planet_sk`           | 1 fila por `pl_name`         | Table |
| `gold_by_discoverymethod`  | 1 fila por `discoverymethod` | View  |
| `gold_by_host`             | 1 fila por `hostname`        | View  |

---

## Keys y Constraints

### dim_host_sk
| Columna    | Tipo    | Constraint           |
|------------|---------|----------------------|
| `host_id`  | INTEGER | PRIMARY KEY          |
| `hostname` | VARCHAR | NOT NULL, UNIQUE     |
| `sy_dist`  | DOUBLE  | —                    |
| `ra`       | DOUBLE  | —                    |
| `dec`      | DOUBLE  | —                    |
| `st_teff`  | DOUBLE  | —                    |
| `st_rad`   | DOUBLE  | —                    |
| `st_mass`  | DOUBLE  | —                    |

### fact_planet_sk
| Columna           | Tipo    | Constraint                              |
|-------------------|---------|-----------------------------------------|
| `pl_name`         | VARCHAR | PRIMARY KEY                             |
| `host_id`         | INTEGER | NOT NULL, FK → `dim_host_sk(host_id)`   |
| `discoverymethod` | VARCHAR | —                                       |
| `disc_year`       | INTEGER | —                                       |
| `pl_orbper`       | DOUBLE  | —                                       |
| `pl_rade`         | DOUBLE  | —                                       |
| `pl_bmasse`       | DOUBLE  | —                                       |
| `pl_eqt`          | DOUBLE  | —                                       |

---

## Reglas de Calidad (Silver)

| Columna     | Regla                              |
|-------------|------------------------------------|
| `pl_name`   | NOT NULL                           |
| `hostname`  | NOT NULL                           |
| `disc_year` | NULL o entre 1980 y 2026           |
| `pl_rade`   | NULL o > 0 y ≤ 30 (radios terrestres) |
| `pl_bmasse` | NULL o > 0                         |

---

## Checks Mínimos

| Check | Query | Condición esperada |
|---|---|---|
| Uniqueness dim | `SELECT COUNT(*), COUNT(DISTINCT hostname) FROM dim_host_sk` | `n_rows == n_keys` |
| Integridad referencial | `orphan_rows` en `fact_planet_sk` LEFT JOIN `dim_host_sk` | `orphan_rows == 0` |

## Pipeline

```
pscomppars.csv
    → raw_ps          (VIEW)
    → silver_planet   (TABLE)
    → dim_host_full   (TABLE)
    → fact_planet     (TABLE)
    → dim_host_sk     (TABLE, PK/SK)
    → fact_planet_sk  (TABLE, FK)
    → gold_by_discoverymethod  (VIEW)
    → gold_by_host             (VIEW)
```
