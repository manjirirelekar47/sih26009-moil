"""
Generate proximity-based geological labels for reserve mapping real mode.
Zones within 5km of MOIL Balaghat mine = mineralized (35% Mn proxy)
Zones 5-10km = mineralized (15% Mn proxy)
Zones >10km = barren
Run from repo root: python make_real_labels.py
"""
import pandas as pd

df = pd.read_csv('data/processed/zone_features.csv')
rows = []
for i, row in df.iterrows():
    d = row['dist_to_mine_km']
    if d <= 5.0:
        label, mn = 'mineralized', 35.0
    elif d <= 10.0:
        label, mn = 'mineralized', 15.0
    else:
        label, mn = 'barren', 0.0
    rows.append({
        'obs_id':        f'OBS_{i:04d}',
        'lat':           row['lat'],
        'lon':           row['lon'],
        'label_class':   label,
        'evidence_type': 'proximity',
        'source':        'MOIL_mine_centroid_Balaghat',
        'mn_pct':        mn,
        'notes':         f'dist_to_mine={d:.2f}km',
    })

out = pd.DataFrame(rows)
out.to_csv('reserve_mapping/data/geological_labels.csv', index=False)
print(f"Done: {len(out[out['label_class']=='mineralized'])} mineralized, "
      f"{len(out[out['label_class']=='barren'])} barren")
