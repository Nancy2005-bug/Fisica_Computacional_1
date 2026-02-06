# W05B — Gold Outputs (H2)

## Gold 1: `gold_by_discoverymethod`
**Pregunta:** ¿qué métodos de descubrimiento dominan el dataset?

SQL (si aplica):
```sql
SELECT * FROM gold_by_discoverymethod ORDER BY n_planets DESC LIMIT 10;
```

Top 10 (pega tabla o captura):

Interpretación (2–3 líneas):

---

## Gold 2: `gold_by_host`
**Pregunta:** ¿qué hosts tienen más planetas? ¿cómo cambia el radio promedio?

SQL (si aplica):
```sql
SELECT * FROM gold_by_host ORDER BY n_planets DESC LIMIT 10;
```

Top 10 (pega tabla o captura):

Interpretación (2–3 líneas):

---

## Export (evidencia)
- `artifacts/gold_by_discoverymethod.csv` ✅
- `artifacts/gold_by_host.csv` ✅

---

## Decisions Log (mínimo 2)
- Decisión 1 (surrogate key + FK): evidencia (conteos, orphan_rows)
- Decisión 2 (Gold outputs): por qué esas métricas
