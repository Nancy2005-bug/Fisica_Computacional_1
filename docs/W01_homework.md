# W01A — Introducción (DDIA Cap. 1) + Entorno local + Evidencia

## Reflexión (DDIA Cap.1)
**¿Qué haría que tu sistema sea “no confiable” aunque el código corra?**

* Datos sin hash (no detectaría corrupciones).
* Sin documentación (nadie podría reproducirlo).
* Sin checks de calidad (basura entra, basura sale).

**¿Qué documento te gustaría encontrar si heredas el proyecto de otro equipo?**

* README con instrucciones claras de ejecución.
* Log de decisiones con justificaciones.
* Glosario para entender el dominio.

---

# W01B — Bronze/Raw: ingesta + trazabilidad + sanity checks (DDIA Cap. 1)

## Sanity Checks

### Check 1: Conteo de filas y columnas.

```python
# Check 1
n_rows = con.execute("SELECT COUNT(*) FROM raw_ps").fetchone()[0]
n_cols = con.execute("SELECT COUNT(*) FROM pragma_table_info('raw_ps')").fetchone()[0]
n_rows, n_cols
```

**Respuesta:** (6107, 16)

### Check 2: Nulos en columna clave

```python
# 2) nulos en una columna clave típica
con.execute("SELECT COUNT(*) AS null_pl_name FROM raw_ps WHERE pl_name IS NULL").fetchall()
```

**Respuesta:** [(0,)]

### Check 3: Muestra de filas

```python
# Check 3
con.execute("SELECT pl_name, hostname, discoverymethod, disc_year FROM raw_ps WHERE pl_name IS NOT NULL LIMIT 10").fetchall()
```

**Respuesta:** 

[('11 Com b', '11 Com', 'Radial Velocity', 2007),
 ('11 UMi b', '11 UMi', 'Radial Velocity', 2009),
 ('14 And b', '14 And', 'Radial Velocity', 2008),
 ('14 Her b', '14 Her', 'Radial Velocity', 2002),
 ('16 Cyg B b', '16 Cyg B', 'Radial Velocity', 1996),
 ('17 Sco b', '17 Sco', 'Radial Velocity', 2020),
 ('18 Del b', '18 Del', 'Radial Velocity', 2008),
 ('1RXS J160929.1-210524 b', '1RXS J160929.1-210524', 'Imaging', 2008),
 ('24 Boo b', '24 Boo', 'Radial Velocity', 2018),
 ('24 Sex b', '24 Sex', 'Radial Velocity', 2010)]

### Check Extra: Años fuera de rango (ej. < 1980 o > año actual)

```sql
SELECT
    COUNT(*) FILTER (WHERE disc_year < 1989)  AS before_1989,
    COUNT(*) FILTER (WHERE disc_year > 2026)  AS after_2026,
    COUNT(*) FILTER (WHERE disc_year IS NULL) AS null_year
FROM raw_ps
```

**Respuesta:** [(0, 0, 1)]

**Interpretación:** El primer exoplaneta fue confirmado en 1989 (PSR 1257+12). Cualquier año menor es un error de ingesta.