# How we work in Git

1. Work only inside **your own folder** (see the table in README). This keeps merges conflict-free.
2. Never commit to `main`. Create your branch:
   ```
   git checkout main
   git pull
   git checkout -b feat/<your-module>      # e.g. feat/reserve-mapping
   ```
3. Commit small and often, with clear messages:
   ```
   git add src/reserve_mapping
   git commit -m "reserve_mapping: train RF on zone_features"
   git push -u origin feat/<your-module>
   ```
4. When your deliverable works, open a **Pull Request** into `main` on GitHub and tag the repo owner.
5. Need a change in `config.py` or `docs/DATA_CONTRACT.md`? Message the owner first - other modules depend on them.
6. Before starting new work: `git checkout main && git pull`.
7. Never commit passwords, API keys or Earth Engine credentials. Small CSVs are fine; large rasters (`.tif`) are not.
