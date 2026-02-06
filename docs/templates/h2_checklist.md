# H2 — Checklist (Core)

## 1) Tablas / vistas
- [ ] `silver_planet` creada (o equivalente)
- [ ] `dim_host_sk` creada (1 fila por hostname)
- [ ] `fact_planet_sk` creada (FK a dim_host_sk)

## 2) Checks con evidencia
- [ ] Uniqueness dim: `COUNT(*) == COUNT(DISTINCT hostname)`
- [ ] Orphans fact→dim: `orphan_rows == 0`
- [ ] 2 métricas Gold (vistas o tablas):
  - [ ] Por `discoverymethod`
  - [ ] Por `host_id` o `hostname`

## 3) Docs
- [ ] `docs/data_contract.md` actualizado (grain + keys + checks)
- [ ] `docs/decisions_log.md` con al menos 2 decisiones (con evidencia)
- [ ] `docs/w05a_modeling_notes.md` (1 página)

## 4) Artifacts
- [ ] `artifacts/gold_by_discoverymethod.csv`
- [ ] `artifacts/gold_by_host.csv` (o similar)
