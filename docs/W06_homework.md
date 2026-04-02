# W06A — Diseño relacional mínimo: **PK/FK**, llaves surrogate y “star schema” (DuckDB)

## TODO 2 (estudiante): crea fact_planet_sk con FK a dim_host_sk(host_id)

```python
con.execute("DROP TABLE IF EXISTS fact_planet_sk")

con.execute("""
CREATE TABLE fact_planet_sk (
    pl_name         VARCHAR PRIMARY KEY,
    host_id         INTEGER NOT NULL REFERENCES dim_host_sk(host_id),
    discoverymethod VARCHAR,
    disc_year       INTEGER,
    pl_orbper       DOUBLE,
    pl_rade         DOUBLE,
    pl_bmasse       DOUBLE,
    pl_eqt          DOUBLE
)
""")

con.execute("""
INSERT INTO fact_planet_sk
SELECT
    f.pl_name,
    d.host_id,
    f.discoverymethod,
    f.disc_year,
    f.pl_orbper,
    f.pl_rade,
    f.pl_bmasse,
    f.pl_eqt
FROM fact_planet f
JOIN dim_host_sk d ON f.hostname = d.hostname
""")

con.sql("SELECT COUNT(*) AS n_fact_sk FROM fact_planet_sk").show()

# Check huérfanos — debe dar 0
con.sql("""
SELECT COUNT(*) AS orphan_rows
FROM fact_planet_sk f
LEFT JOIN dim_host_sk d ON f.host_id = d.host_id
WHERE d.host_id IS NULL
""").show()
```

**Resultado:** 

| n_fact_sk |
|-----------|
| 6101      |

| orphan_rows |
|-------------|
| 0           |

## TU TURNO 3: consulta analítica usando el modelo con llaves

**Objetivo:** top 10 métodos de descubrimiento y n_planets.

```sql
SELECT
  discoverymethod,
  COUNT(*) AS n_planets
FROM fact_planet_sk
WHERE discoverymethod IS NOT NULL
GROUP BY discoverymethod
ORDER BY n_planets DESC
LIMIT 10
```

**Resultado:**

| discoverymethod               | n_planets |
|-------------------------------|-----------|
| Transit                       | 4500      |
| Radial Velocity               | 1166      |
| Microlensing                  | 266       |
| Imaging                       | 87        |
| Transit Timing Variations     | 39        |
| Eclipse Timing Variations     | 17        |
| Orbital Brightness Modulation | 9         |
| Pulsar Timing                 | 8         |
| Astrometry                    | 6         |
| Pulsation Timing Variations   | 2         |

# W06B — Gold final + Export a `artifacts/`

## TODO 1 (Gold 1): crea la vista gold_by_discoverymethod

```sql
CREATE VIEW gold_by_discoverymethod AS
SELECT
    discoverymethod,
    COUNT(*)        AS n_planets,
    AVG(pl_rade)    AS avg_radius_earth,
    AVG(pl_bmasse)  AS avg_mass_earth,
    MIN(disc_year)  AS first_year,
    MAX(disc_year)  AS last_year
FROM fact_planet_sk
WHERE discoverymethod IS NOT NULL
GROUP BY discoverymethod
ORDER BY n_planets DESC
```

**Resultado:**

| discoverymethod               | n_planets | avg_radius_earth   | avg_mass_earth     | first_year | last_year |
|-------------------------------|-----------|--------------------|--------------------|------------|-----------|
| Transit                       | 4500      | 4.361876653578571  | 123.46020251712584 | 2002       | 2026      |
| Radial Velocity               | 1166      | 9.759872661948648  | 1035.4051064286605 | 1995       | 2026      |
| Microlensing                  | 266       | 9.850563909774433  | 797.6943019686465  | 2004       | 2026      |
| Imaging                       | 87        | 13.43342457831325  | 4485.179850102737  | 2004       | 2026      |
| Transit Timing Variations     | 39        | 6.493408364210527  | 484.3989013444737  | 2011       | 2025      |
| Eclipse Timing Variations     | 17        | 12.893333333333334 | 2102.722438878823  | 2009       | 2023      |
| Orbital Brightness Modulation | 9         | 9.64504            | 350.3239953666667  | 2011       | 2021      |
| Pulsar Timing                 | 8         | 5.411333333333332  | 278.15552903625    | 1992       | 2024      |
| Astrometry                    | 6         | 12.450000000000001 | 4673.610125018334  | 2013       | 2025      |
| Pulsation Timing Variations   | 2         | 12.75              | 2383.725           | 2007       | 2016      |

## TODO 2 (Gold 2): crea la vista gold_by_host

```sql
CREATE VIEW gold_by_host AS
SELECT
    d.hostname,
    COUNT(*)        AS n_planets,
    AVG(f.pl_rade)  AS avg_radius_earth,
    AVG(f.pl_bmasse) AS avg_mass_earth,
    d.sy_dist,
    d.ra,
    d.dec
FROM fact_planet_sk f
JOIN dim_host_sk d ON f.host_id = d.host_id
GROUP BY d.hostname, d.sy_dist, d.ra, d.dec
ORDER BY n_planets DESC
```

**Resultado:**

| hostname   | n_planets | avg_radius_earth   | avg_mass_earth     | sy_dist     | ra          | dec         |
|------------|-----------|--------------------|--------------------|-------------|-------------|-------------|
| KOI-351    | 8         | 3.9000000000000004 | 31.14875           | 848.254     | 284.4334642 | 49.3051239  |
| TRAPPIST-1 | 7         | 0.9785714285714286 | 0.921142857142857  | 12.42988881 | 346.6263919 | -5.0434618  |
| HD 191939  | 6         | 6.59               | 176.97430202666666 | 53.6089     | 302.0256247 | 66.8503014  |
| HIP 41378  | 6         | 4.253666666666667  | 7.815              | 106.289     | 126.6158279 | 10.0803708  |
| Kepler-20  | 6         | 2.2926666666666664 | 9.386666666666667  | 282.563     | 287.6979913 | 42.3385782  |
| K2-138     | 6         | 2.584333333333333  | 6.041666666666667  | 202.585     | 348.9490311 | -10.8497391 |
| Kepler-80  | 6         | 1.8133333333333332 | 747.3908333333334  | 369.451     | 296.1125759 | 39.9787451  |
| Kepler-11  | 6         | 2.966666666666667  | 7.849999999999999  | 646.346     | 297.1150949 | 41.9091092  |
| HD 10180   | 6         | 6.676666666666667  | 1587.7010169516668 | 38.9607     | 24.4731133  | -60.5114881 |
| TOI-178    | 6         | 2.2176666666666667 | 4.051666666666667  | 62.699      | 7.3020115   | -30.4541159 |

---

# Gold Report

## gold_by_discoverymethod

### ¿Qué es?
Vista Gold que agrupa los planetas confirmados por método de descubrimiento. Calcula el conteo total, el radio y masa promedio de los planetas encontrados, y el rango temporal de descubrimientos para cada método.

### Columnas
| Columna           | Descripción                                      |
|-------------------|--------------------------------------------------|
| `discoverymethod` | Nombre del método de detección                   |
| `n_planets`       | Número total de planetas descubiertos            |
| `avg_radius_earth`| Radio promedio en radios terrestres              |
| `avg_mass_earth`  | Masa promedio en masas terrestres                |
| `first_year`      | Primer año de descubrimiento con ese método      |
| `last_year`       | Año más reciente de descubrimiento               |

### Interpretación científica
El método Transit domina con 4500 planetas descubiertos, lo cual refleja el impacto de misiones como Kepler y TESS. Los planetas encontrados por tránsito son en promedio pequeños (radio ~4.4 R⊕), mientras que Imaging y Astrometry detectan principalmente gigantes (radio >12 R⊕), ya que estos métodos favorecen planetas masivos a grandes separaciones orbitales.

---

## gold_by_host

### ¿Qué es?
Vista Gold que agrupa los planetas por estrella anfitriona, combinando métricas planetarias de `fact_planet_sk` con atributos estelares de `dim_host_sk`. Permite identificar los sistemas planetarios más ricos y su ubicación en el cielo.

### Columnas
| Columna           | Descripción                                         |
|-------------------|-----------------------------------------------------|
| `hostname`        | Nombre de la estrella anfitriona                    |
| `n_planets`       | Número de planetas confirmados en el sistema        |
| `avg_radius_earth`| Radio promedio de los planetas del sistema          |
| `avg_mass_earth`  | Masa promedio de los planetas del sistema           |
| `sy_dist`         | Distancia del sistema en parsecs                    |
| `ra`              | Ascensión recta (posición en el cielo)              |
| `dec`             | Declinación (posición en el cielo)                  |

### Interpretación científica
KOI-351 encabeza la lista con 8 planetas, seguido de TRAPPIST-1 con 7. TRAPPIST-1 es el sistema más cercano del top (12.4 pc) y sus planetas son notablemente pequeños y livianos (radio ~0.98 R⊕, masa ~0.92 M⊕), lo que lo convierte en uno de los sistemas más relevantes para la búsqueda de planetas potencialmente habitables.