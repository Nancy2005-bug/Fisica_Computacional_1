# W02 – SQL esencial I en DuckDB (SELECT/WHERE/GROUP BY/NULLs)

### Q1: ¿Cuántos planetas hay por año? (top 15 años con más planetas)

**SQL:**

```sql
SELECT disc_year, COUNT(*) AS n_planets
FROM raw_ps
WHERE disc_year IS NOT NULL
GROUP BY disc_year
ORDER BY n_planets DESC
LIMIT 15
```

**Respuesta:** 

[(2016, 1496),
 (2014, 869),
 (2021, 564),
 (2022, 369),
 (2023, 324),
 (2018, 315),
 (2024, 259),
 (2025, 240),
 (2020, 234),
 (2019, 196),
 (2015, 155),
 (2017, 152),
 (2012, 139),
 (2011, 135),
 (2013, 128)]

### Q2: Top 10 sistemas (hostname) con más planetas.

**SQL:**

```sql
SELECT hostname, COUNT(*) AS n_planets
FROM raw_ps
WHERE hostname IS NOT NULL
GROUP BY hostname
ORDER BY n_planets DESC
LIMIT 10
```

**Respuesta:**

[('KOI-351', 8),
 ('TRAPPIST-1', 7),
 ('TOI-178', 6),
 ('HD 191939', 6),
 ('HIP 41378', 6),
 ('TOI-1136', 6),
 ('Kepler-11', 6),
 ('Kepler-80', 6),
 ('K2-138', 6),
 ('HD 110067', 6)]

### Q3: ¿Qué fracción de filas tiene `pl_bmasse` nulo?

**SQL:**

```sql
SELECT
    COUNT(*) AS total,
    COUNT(pl_bmasse) AS non_null,
    COUNT(*) - COUNT(pl_bmasse) AS nulls,
    ROUND((COUNT(*) - COUNT(pl_bmasse))::DOUBLE / COUNT(*), 4) AS frac_null
FROM raw_ps
```

**Respuesta:** [(6107, 6076, 31, 0.0051)]

### Q4: 10 planetas con mayor radio (pl_rade) (evita NULL).

**SQL:**

```sql
SELECT pl_name, hostname, pl_rade
FROM raw_ps
WHERE pl_rade IS NOT NULL
ORDER BY pl_rade DESC
LIMIT 10
```

**Respuesta:** 

[('V2376 Ori b', 'V2376 Ori', 87.20586985),
 ('HD 100546 b', 'HD 100546', 77.3421),
 ('GQ Lup b', 'GQ Lup', 33.6),
 ('Kepler-297 d', 'Kepler-297', 32.6),
 ('PDS 70 b', 'PDS 70', 30.48848),
 ('DH Tau b', 'DH Tau', 30.2643),
 ('Kepler-1979 b', 'Kepler-1979', 29.33),
 ('TOI-1408 b', 'TOI-1408', 25.0),
 ('CT Cha b', 'CT Cha', 24.66),
 ('HAT-P-67 b', 'HAT-P-67', 23.9872187)]

### Q5: Compara `COUNT(*)` vs `COUNT(disc_year)` por método.

**SQL:**

```sql
SELECT
    discoverymethod,
    COUNT(*) AS total,
    COUNT(disc_year) AS non_null_year,
    COUNT(*) - COUNT(disc_year) AS null_year
FROM raw_ps
GROUP BY discoverymethod
ORDER BY total DESC
```

**Respuesta:**

[('Transit', 4501, 4500, 1),
 ('Radial Velocity', 1166, 1166, 0),
 ('Microlensing', 266, 266, 0),
 ('Imaging', 92, 92, 0),
 ('Transit Timing Variations', 39, 39, 0),
 ('Eclipse Timing Variations', 17, 17, 0),
 ('Orbital Brightness Modulation', 9, 9, 0),
 ('Pulsar Timing', 8, 8, 0),
 ('Astrometry', 6, 6, 0),
 ('Pulsation Timing Variations', 2, 2, 0),
 ('Disk Kinematics', 1, 1, 0)]

### Q6: Resumen: por método, n_planets y mediana de periodo orbital.

**SQL:**

```sql
SELECT
    discoverymethod,
    COUNT(*) AS n_planets,
    MEDIAN(pl_orbper) AS median_period_days
FROM raw_ps
WHERE pl_orbper IS NOT NULL
GROUP BY discoverymethod
ORDER BY n_planets DESC
```

**Respuesta:**

[('Transit', 4501, 8.15872),
 ('Radial Velocity', 1166, 298.895),
 ('Transit Timing Variations', 39, 30.0),
 ('Imaging', 25, 33000.0),
 ('Eclipse Timing Variations', 17, 3160.0),
 ('Microlensing', 12, 3142.5),
 ('Orbital Brightness Modulation', 9, 0.81161),
 ('Pulsar Timing', 7, 25.262),
 ('Astrometry', 6, 334.76),
 ('Pulsation Timing Variations', 2, 1005.0)]

## Consultas de Calidad

### Calidad 1: ¿Hay planetas con pl_rade < 0 o pl_orbper <= 0 (valores físicamente imposibles)?

```sql
SELECT COUNT(*) AS outliers
FROM raw_ps
WHERE pl_rade < 0 OR pl_orbper <= 0
```

**Respuesta:** [(0,)]

### Calidad 2: Duplicados por nombre de planeta

```sql
SELECT 
    pl_name,
    COUNT(*) AS n_duplicates,
    COUNT(DISTINCT hostname) AS n_different_hosts
FROM raw_ps
WHERE pl_name IS NOT NULL
GROUP BY pl_name
HAVING COUNT(*) > 1
ORDER BY n_duplicates DESC
```

**Respuesta:** []

## Consultas Científicas

### Científica 1: Zonas Habitables.

```sql
SELECT 
    pl_name,
    hostname,
    pl_eqt AS temp_equilibrium,
    pl_rade AS radius_earth,
    sy_dist AS distance_parsec,
    ABS(pl_eqt - 288) AS temp_diff_from_earth
FROM raw_ps
WHERE pl_eqt BETWEEN 200 AND 350  
    AND pl_rade BETWEEN 0.5 AND 2.0  
    AND pl_eqt IS NOT NULL
ORDER BY temp_diff_from_earth ASC
LIMIT 20
```

**Respuesta:**

[('Kepler-438 b', 'Kepler-438', 288.0, 1.12, 195.94287175, 0.0),
 ('TOI-1266 d', 'TOI-1266', 288.0, 1.74, 36.0118, 0.0),
 ('TRAPPIST-1 d', 'TRAPPIST-1', 286.2, 0.788, 12.42988881, 1.8000000000000114),
 ('Kepler-1410 b', 'Kepler-1410', 290.0, 1.78, 367.0, 2.0),
 ('L 98-59 f', 'L 98-59', 285.0, 1.48, 10.6194, 3.0),
 ('Kepler-138 e', 'Kepler-138', 292.0, 0.797, 66.8624, 4.0),
 ('Proxima Cen d', 'Proxima Cen', 282.0, 0.692, 1.30119, 6.0),
 ('K2-133 e', 'K2-133', 296.0, 1.73, 75.1703, 8.0),
 ('TOI-2095 c', 'TOI-2095', 297.0, 1.33, 41.9176, 9.0),
 ('Kepler-737 b', 'Kepler-737', 298.0, 1.96, 205.118, 10.0),
 ('Kepler-560 b', 'Kepler-560', 298.0, 1.72, 109.308, 10.0),
 ('Kepler-69 c', 'Kepler-69', 299.0, 1.71, 730.625, 11.0),
 ("Teegarden's Star b", "Teegarden's Star", 277.0, 1.05, 3.83078, 11.0),
 ('Kepler-1389 b', 'Kepler-1389', 300.0, 1.77, 497.093, 12.0),
 ('GJ 1132 c', 'GJ 1132', 300.0, 1.43, 12.613, 12.0),
 ('Ross 128 b', 'Ross 128', 301.0, 1.11, 3.37454, 13.0),
 ('Kepler-296 f', 'Kepler-296', 274.0, 1.8, 167.0, 14.0),
 ('TOI-700 e', 'TOI-700', 272.9, 0.953, 31.1265, 15.100000000000023),
 ('LP 890-9 c', 'LP 890-9', 272.0, 1.367, 32.4298, 16.0),
 ('Kepler-1638 b', 'Kepler-1638', 304.0, 1.87, 1525.52, 16.0)]

**Interpretación:** Los planetas encontrados tienen temperaturas entre 200-350K y radios similares a la Tierra, lo que sugiere condiciones potencialmente habitables.


### Científica 2: ¿Los planetas más masivos tienen periodos orbitales más largos?

```sql
SELECT
    CASE
        WHEN pl_bmasse < 10   THEN 'Terrestre (<10)'
        WHEN pl_bmasse < 100  THEN 'Neptuniano (10-100)'
        ELSE 'Gigante (>100)'
    END AS mass_class,
    COUNT(*) AS n,
    MEDIAN(pl_orbper) AS median_period_days
FROM raw_ps
WHERE pl_bmasse IS NOT NULL AND pl_orbper IS NOT NULL
GROUP BY 1
ORDER BY median_period_days
```

**Respuesta:**

[('Terrestre (<10)', 3124, 9.22686525),
 ('Neptuniano (10-100)', 1071, 16.537944),
 ('Gigante (>100)', 1561, 42.6318)]

**Interpretación:** los gigantes tienden a tener periodos más largos (orbitan más lejos).

## Reflexión (Bitácora)

### ¿Qué consulta te pareció más difícil y por qué?

La consulta Q3 (fracción de nulos) fue la más compleja porque requiere entender la diferencia entre COUNT(*) y COUNT(columna), y además hacer la división correctamente para obtener un decimal.

### Si el dataset creciera 100×, ¿qué consultas empeoran más?
Las consultas con ORDER BY sobre columnas no indexadas (Q1, Q2, Q4) serían las más afectadas porque requieren ordenar millones de registros. Las agregaciones con GROUP BY (Q5, Q6) también serían más lentas pero menos que los ordenamientos globales.