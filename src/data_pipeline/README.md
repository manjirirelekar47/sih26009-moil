# data_pipeline (Member 1)
Run in this order, from the repo root:
1. `python -m src.data_pipeline.pull_timeseries`      -> data/raw/*.csv + data/processed/weekly_features.csv
2. `python -m src.data_pipeline.pull_zone_features`   -> data/processed/zone_features.csv
3. `python -m src.data_pipeline.generate_synthetic`   -> data/processed/synthetic_*.csv
Test 3 without Earth Engine: `python -m src.data_pipeline.generate_synthetic --demo` (writes to data/demo/, git-ignored).
