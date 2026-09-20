# Data contract (who produces what, in which columns)

Keep these column names exactly. If you must change one, tell everyone.
All dates are `YYYY-MM-DD`. Weekly data uses **Monday** as `week_start`.

## Member 1 -> everyone (real satellite data; produced by Earth Engine)

**`data/processed/weekly_features.csv`** - Balaghat regional means, one row per week
| column | meaning |
|---|---|
| week_start | Monday of the week |
| rainfall_mm | CHIRPS rainfall summed over the week |
| ndvi | Sentinel-2 vegetation index (higher = greener) |
| sar_vv_db | Sentinel-1 VV backscatter in dB - near-surface soil-moisture proxy (higher = wetter) |
| lst_c | MODIS daytime land surface temperature, deg C |

**`data/processed/zone_features.csv`** -> Member 2. One row per ~1 km grid cell
`zone_id, lon, lat, ndvi_median, sar_vv_mean_db, lst_mean_c, rain_mm_per_year, elevation_m, slope_deg, dist_to_mine_km`

## Member 1 -> Members 3, 5, 6 (SYNTHETIC, driven by the real rainfall above)

**`data/processed/synthetic_production_weekly.csv`**
`week_start, rainfall_mm, planned_tonnes, actual_tonnes, shortfall_pct, shortfall_flag, fleet_downtime_pct, blast_delay_days`

**`data/processed/synthetic_equipment_downtime_weekly.csv`**
`week_start, equipment_id, equipment_type, age_years, scheduled_hours, downtime_hours, breakdown_events`

**`data/processed/equipment_risk.csv`** (Equipment Health -> Member 5, 6)
`week_start, equipment_id, equipment_type, age_years, downtime_pct_8w, breakdowns_8w, c_downtime, c_breakdown, c_age, risk_score, risk_band, main_driver`

## Proposed hand-offs between the other modules (agree or edit these)

- Member 3 -> 5, 6: `data/processed/forecast.csv` with `week_start, yhat, yhat_lower, yhat_upper, planned_tonnes, shortfall_risk (0-1), is_anomaly`
- Member 4 -> 5, 6: a function `get_weather_alerts(rain_mm_48h, soil_moisture_vv_db) -> list[dict]` returning `{type, level, message}`
- Member 5 -> 6: a function `recommend(shortfall_risk, alerts, downtime_risk) -> list[dict]` returning `{action, reason, priority}`
- Member 2 -> 6: `models/reserve_model.pkl` and `data/processed/reserve_probability.csv` (`zone_id, lon, lat, probability`)

## Honesty note for the jury
`synthetic_*` files are simulated. Only the rainfall driving them (and everything in `weekly_features.csv`
and `zone_features.csv`) is real satellite data. Say so on the slide.
