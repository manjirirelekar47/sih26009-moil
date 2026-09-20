"""
Run from repo root: python fix_step4b.py
Patches the vmin/vmax crash when no unknown zones exist in real mode.
"""
path = 'reserve_mapping/step4_make_map.py'
content = open(path, encoding='utf-8').read()

old = '''    vmin = float(unknown["prospectivity_score"].min())
    vmax = float(np.percentile(unknown["prospectivity_score"], COLOR_CLIP_PCT))'''

new = '''    score_pool = unknown if not unknown.empty else gdf
    vmin = float(score_pool["prospectivity_score"].min())
    vmax = float(np.percentile(score_pool["prospectivity_score"], COLOR_CLIP_PCT))'''

if old in content:
    content = content.replace(old, new)
    print("Fix applied")
else:
    print("Pattern not found — check step4_make_map.py manually")

open(path, 'w', encoding='utf-8').write(content)
print("Done")
