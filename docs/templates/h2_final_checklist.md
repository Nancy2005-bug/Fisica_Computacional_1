# H2 — Checklist Final (Core)

## Tablas / vistas
- [ ] `silver_planet`
- [ ] `dim_host_sk` (host_id PK, hostname UNIQUE)
- [ ] `fact_planet_sk` (pl_name PK, host_id FK)
- [ ] `gold_by_discoverymethod`
- [ ] `gold_by_host`

## Checks (con evidencia)
- [ ] `COUNT(*) == COUNT(DISTINCT hostname)` en `dim_host_sk`
- [ ] `orphan_rows == 0` en `fact_planet_sk`
- [ ] `gold_by_*` se consulta sin errores

## Exports
- [ ] `artifacts/gold_by_discoverymethod.csv`
- [ ] `artifacts/gold_by_host.csv`

## Docs
- [ ] `docs/data_contract.md` actualizado (grain+keys+checks)
- [ ] `docs/decisions_log.md` con >= 2 decisiones (con evidencia)
- [ ] `docs/w05b_gold_report.md` completo
