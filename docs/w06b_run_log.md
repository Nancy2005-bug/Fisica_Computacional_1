# W06B — Run Log

## Comando
```bash
python -m src.pipeline.w06b_runner
```

## Stdout — Corrida 1
```text
============================================================
W06B Runner — midiendo tiempos de etapas
============================================================
[2026-05-14T04:27:57.215109+00:00] Stage SILVER: building silver_planet
[2026-05-14T04:27:57.274203+00:00] silver_planet rows=6101
  [silver] 0.0592s
[2026-05-14T04:28:00.806108+00:00] Stage DIMS: building dim_host_full, fact_planet, dim_host_sk, fact_planet_sk
[2026-05-14T04:28:00.871493+00:00] dim_host_sk uniqueness rows=4550, keys=4550
[2026-05-14T04:28:00.871713+00:00] fact_planet rows=6101, fact_planet_sk rows=6101
  [dims] 3.5974s
[2026-05-14T04:28:00.877261+00:00] Stage GOLD: building views gold_by_discoverymethod and gold_by_host
[2026-05-14T04:28:00.884955+00:00] gold views created
  [gold] 0.0132s
[2026-05-14T04:28:00.885037+00:00] Stage EXPORT: writing artifacts CSV
[2026-05-14T04:28:00.910955+00:00] Wrote gold_by_discoverymethod.csv
[2026-05-14T04:28:00.911028+00:00] Wrote gold_by_host.csv
  [export] 0.026s

>>> Etapa más lenta: dims (3.5974s)
============================================================
```

## Stdout — Corrida 2
```text
============================================================
W06B Runner — midiendo tiempos de etapas
============================================================
[2026-05-14T04:49:12.674002+00:00] Stage SILVER: building silver_planet
[2026-05-14T04:49:12.788746+00:00] silver_planet rows=6101
  [silver] 0.1148s
[2026-05-14T04:49:13.771691+00:00] Stage DIMS: building dim_host_full, fact_planet, dim_host_sk, fact_planet_sk
[2026-05-14T04:49:13.866550+00:00] dim_host_sk uniqueness rows=4550, keys=4550
[2026-05-14T04:49:13.866604+00:00] fact_planet rows=6101, fact_planet_sk rows=6101
  [dims] 1.0778s
[2026-05-14T04:49:13.873510+00:00] Stage GOLD: building views gold_by_discoverymethod and gold_by_host
[2026-05-14T04:49:13.881029+00:00] gold views created
  [gold] 0.0144s
[2026-05-14T04:49:13.881097+00:00] Stage EXPORT: writing artifacts CSV
[2026-05-14T04:49:13.911426+00:00] Wrote gold_by_discoverymethod.csv
[2026-05-14T04:49:13.911475+00:00] Wrote gold_by_host.csv
  [export] 0.0304s

>>> Etapa más lenta: dims (1.0778s)
============================================================
```

## Tiempos por etapa — Comparación

| etapa  | corrida 1 (s) | corrida 2 (s) | diferencia (s) | reducción |
|--------|---------------|---------------|----------------|-----------|
| silver | 0.0592        | 0.1148        | +0.0556        | ~igual (ruido) |
| dims   | 3.5974        | 1.0778        | -2.5196        | 70% más rápido |
| gold   | 0.0132        | 0.0144        | +0.0012        | ~igual |
| export | 0.0260        | 0.0304        | +0.0044        | ~igual |
|total | 3.7958 | 1.2374 | -2.5584 | 67% más rápido |

## Interpretación — ¿Qué etapa fue la más lenta?

En ambas corridas la etapa más lenta fue **`dims`**:

- Corrida 1: **3.5974s**
- Corrida 2: **1.0778s**

`dims` es la etapa más costosa porque reconstruye 4 tablas en secuencia:

1. `dim_host_full` — agrega atributos por estrella (4550 hosts)
2. `fact_planet` — extrae planetas únicos (6101 filas)
3. `dim_host_sk` — asigna surrogate keys (`host_id`)
4. `fact_planet_sk` — hace el JOIN entre planetas y estrellas para asociar `host_id`

El JOIN es el paso más costoso en I/O y tiempo de cómputo.

## ¿Por qué cambian los tiempos entre corridas?

La segunda corrida fue mucho más rápida en `dims` porque:

1. **Caché del sistema operativo (page cache):** en la primera corrida, Windows lee los bloques del archivo `exoplanets.duckdb` desde disco. En la segunda corrida, muchos de esos bloques ya están en memoria RAM, por lo que el acceso es más rápido.
2. **DuckDB ya tiene el archivo y el esquema “calientes”:** en la segunda ejecución disminuye el overhead de apertura del archivo y de inicialización interna del motor.

Las etapas `gold` y `export` casi no cambian porque trabajan con vistas en memoria y archivos pequeños. La variación de `silver` es mínima y puede interpretarse como ruido normal de medición a esta escala.