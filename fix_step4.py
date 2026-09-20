"""
Run from repo root: python fix_step4.py
Patches reserve_mapping/step4_make_map.py to handle real mode
where all zones have labels (no 'unknown' zones exist).
"""
path = 'reserve_mapping/step4_make_map.py'
content = open(path, encoding='utf-8').read()

# Fix 1: pick_targets — fall back to all zones if no unknown ones exist
old1 = '''    pool = df[df["label_class"] == "unknown"].sort_values(
        "prospectivity_score", ascending=False)'''
new1 = '''    pool = df[df["label_class"] == "unknown"].sort_values(
        "prospectivity_score", ascending=False)
    if pool.empty:
        # Real mode: no unknown zones — pick top scoring mineralized zones instead
        pool = df[df["label_class"] == "mineralized"].sort_values(
            "prospectivity_score", ascending=False)
    if pool.empty:
        pool = df.sort_values("prospectivity_score", ascending=False)'''

# Fix 2: pick_targets output — handle empty chosen list
old2 = '''    out = pd.DataFrame([c[2] for c in chosen])[
        ["zone_id", "lat", "lon", "prospectivity_score"]].reset_index(drop=True)'''
new2 = '''    if not chosen:
        return pd.DataFrame(columns=["rank","zone_id","lat","lon",
                                      "prospectivity_score","dist_to_reference_mine_km"])
    rows = [c[2] for c in chosen]
    available_cols = rows[0].index.tolist()
    keep = [c for c in ["zone_id","lat","lon","prospectivity_score"] if c in available_cols]
    out = pd.DataFrame(rows)[keep].reset_index(drop=True)'''

if old1 in content:
    content = content.replace(old1, new1)
    print("Fix 1 applied")
else:
    print("Fix 1 NOT found — already patched or different version")

if old2 in content:
    content = content.replace(old2, new2)
    print("Fix 2 applied")
else:
    print("Fix 2 NOT found — already patched or different version")

open(path, 'w', encoding='utf-8').write(content)
print("Done — run: cd reserve_mapping && python run_pipeline.py --mode real && cd ..")
