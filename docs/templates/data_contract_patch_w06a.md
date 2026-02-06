# Patch sugerido para data_contract.md (W06A)

## Ejecución / Reproducibilidad
- Requisito: `data/raw/pscomppars.csv` presente
- Ejecutar:
  - `python -m src.pipeline.w06_pipeline --mode all`
  - (alternativa) `python src/pipeline/w06_pipeline.py --mode all`
- Modos:
  - `--mode silver`
  - `--mode dims`
  - `--mode gold`
  - `--mode export`
- Outputs:
  - `artifacts/gold_by_discoverymethod.csv`
  - `artifacts/gold_by_host.csv`
