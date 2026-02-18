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