"""
Run from repo root: python fix_step4c.py
Patches Layer 1 and Layer 2 in step4_make_map.py to use all zones
when no unknown zones exist (real mode with proximity labels).
"""
path = 'reserve_mapping/step4_make_map.py'
content = open(path, encoding='utf-8').read()

# Fix: use all mineralized zones for display when unknown is empty
old = '''    # Layer 1: prospectivity score for zones WITHOUT validated evidence
    fg_zones = folium.FeatureGroup(
        name="Prospectivity score (zones without validated evidence)", show=True)
    folium.GeoJson(
        unknown[["zone_id", "prospectivity_score", "evidence", "geometry"]],'''

new = '''    # Layer 1: prospectivity score — use unknown zones or all zones in real mode
    display_zones = unknown if not unknown.empty else gdf
    fg_zones = folium.FeatureGroup(
        name="Prospectivity score (all zones)", show=True)
    folium.GeoJson(
        display_zones[["zone_id", "prospectivity_score", "evidence", "geometry"]],'''

if old in content:
    content = content.replace(old, new)
    print("Fix 1 applied — Layer 1")
else:
    print("Fix 1 NOT found")

# Fix Layer 2 heatmap — same issue
old2 = '''    HeatMap(unknown[["lat", "lon", "prospectivity_score"]].values.tolist(),'''
new2 = '''    heat_src = unknown if not unknown.empty else gdf
    HeatMap(heat_src[["lat", "lon", "prospectivity_score"]].values.tolist(),'''

if old2 in content:
    content = content.replace(old2, new2)
    print("Fix 2 applied — Layer 2 heatmap")
else:
    print("Fix 2 NOT found")

open(path, 'w', encoding='utf-8').write(content)
print("Done — run: cd reserve_mapping && python run_pipeline.py --mode real && cd ..")
