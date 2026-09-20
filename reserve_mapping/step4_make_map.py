"""
Step 4 - Prospectivity map + Top Exploration Targets in Folium (Member 2)
SIH26009 / MOIL - Reserve Mapping

The score shown is a PROSPECTIVITY SCORE: a relative exploration indicator, not
a reserve probability and not an official reserve estimate.

Needs: data/zones.geojson (step 1), data/zone_scores.csv (step 3)
Run:   python step4_make_map.py
Writes:
  data/prospectivity_map.html       <- open in any browser / embed in dashboard
  data/top_exploration_targets.csv  <- ranked targets (zones WITHOUT validated evidence)

Exploration targets are picked only from UNKNOWN zones: zones that already have
validated mineralized/barren evidence are not "targets" (and their scores are
in-sample, since the model trained on them).

If label_source is DEMO_SYNTHETIC the map carries a red DEMO banner and the
evidence zones are labelled as synthetic.

Embed in Streamlit (Member 6) without extra packages:
    import streamlit.components.v1 as components
    from step4_make_map import build_prospectivity_map
    m, targets = build_prospectivity_map()
    components.html(m.get_root().render(), height=650)
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import HeatMap
import branca.colormap as cm

# ----------------------------- CONFIG ---------------------------------------
ZONES_GEOJSON = "data/zones.geojson"
SCORES_CSV = "data/zone_scores.csv"
OUT_HTML = "data/prospectivity_map.html"
OUT_TARGETS = "data/top_exploration_targets.csv"

# Reference point / map centre ONLY (MOIL Balaghat mine, approx.). Not a label.
MINE_LAT, MINE_LON = 21.80, 80.19
TOP_N = 10                          # number of exploration targets to mark
MIN_SEPARATION_KM = 3.0             # targets must be this far apart
COLOR_CLIP_PCT = 99                 # colour scale tops out at this percentile
DEMO_TAG = "DEMO_SYNTHETIC"
# -----------------------------------------------------------------------------


def _km_offsets(lat, lon):
    """Approximate km east/north of the reference point (fine at ~60 km scale)."""
    dx = (np.asarray(lon) - MINE_LON) * 111.32 * np.cos(np.radians(MINE_LAT))
    dy = (np.asarray(lat) - MINE_LAT) * 110.57
    return dx, dy


def load_scored_zones():
    gdf = gpd.read_file(ZONES_GEOJSON)[["zone_id", "geometry"]]
    scores = pd.read_csv(SCORES_CSV)
    gdf = gdf.merge(scores, on="zone_id", how="left")
    if gdf["prospectivity_score"].isna().any():
        raise ValueError("Some zones have no score - rerun steps 1-3")
    is_demo = gdf["label_source"].iloc[0] == DEMO_TAG
    prefix = "DEMO/SYNTHETIC " if is_demo else ""
    n_obs = gdf["n_mineralized_obs"] + gdf["n_barren_obs"]
    gdf["evidence"] = np.where(
        gdf["label_class"] == "unknown", "No validated evidence (unknown)",
        prefix + gdf["label_class"] + " zone (" + n_obs.astype(str) + " obs)")
    return gdf, is_demo


def pick_targets(df, top_n=TOP_N, min_sep_km=MIN_SEPARATION_KM):
    """Top-N UNKNOWN zones by prospectivity score, with a minimum spacing so the
    list gives distinct sites instead of neighbouring cells of one blob."""
    pool = df[df["label_class"] == "unknown"].sort_values(
        "prospectivity_score", ascending=False)
    if pool.empty:
        # Real mode: no unknown zones — pick top scoring mineralized zones instead
        pool = df[df["label_class"] == "mineralized"].sort_values(
            "prospectivity_score", ascending=False)
    if pool.empty:
        pool = df.sort_values("prospectivity_score", ascending=False)
    chosen = []
    for _, r in pool.iterrows():
        x, y = _km_offsets(r["lat"], r["lon"])
        if all(np.hypot(x - cx, y - cy) >= min_sep_km for cx, cy, _ in chosen):
            chosen.append((x, y, r))
        if len(chosen) == top_n:
            break
    if not chosen:
        return pd.DataFrame(columns=["rank","zone_id","lat","lon",
                                      "prospectivity_score","dist_to_reference_mine_km"])
    rows = [c[2] for c in chosen]
    available_cols = rows[0].index.tolist()
    keep = [c for c in ["zone_id","lat","lon","prospectivity_score"] if c in available_cols]
    out = pd.DataFrame(rows)[keep].reset_index(drop=True)
    out.insert(0, "rank", np.arange(1, len(out) + 1))
    dx, dy = _km_offsets(out["lat"], out["lon"])
    out["dist_to_reference_mine_km"] = np.hypot(dx, dy).round(1)  # info only
    out["prospectivity_score"] = out["prospectivity_score"].round(4)
    return out


def build_prospectivity_map(top_n=TOP_N):
    gdf, is_demo = load_scored_zones()
    unknown = gdf[gdf["label_class"] == "unknown"].copy()
    evidence = gdf[gdf["label_class"] != "unknown"].copy()   # trained on -> in-sample
    targets = pick_targets(gdf, top_n=top_n)

    # colour scale (clipped so a few extreme zones don't wash out the rest)
    score_pool = unknown if not unknown.empty else gdf
    vmin = float(score_pool["prospectivity_score"].min())
    vmax = float(np.percentile(score_pool["prospectivity_score"], COLOR_CLIP_PCT))
    cmap = cm.LinearColormap(
        ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"],
        vmin=vmin, vmax=vmax,
        caption="Prospectivity score (relative exploration indicator, "
                "not a reserve probability)")

    m = folium.Map(location=[MINE_LAT, MINE_LON], zoom_start=11,
                   tiles="OpenStreetMap", control_scale=True)
    folium.TileLayer(
        tiles=("https://server.arcgisonline.com/ArcGIS/rest/services/"
               "World_Imagery/MapServer/tile/{z}/{y}/{x}"),
        attr="Esri World Imagery", name="Satellite", show=False).add_to(m)

    # Layer 1: prospectivity score — use unknown zones or all zones in real mode
    display_zones = unknown if not unknown.empty else gdf
    fg_zones = folium.FeatureGroup(
        name="Prospectivity score (all zones)", show=True)
    folium.GeoJson(
        display_zones[["zone_id", "prospectivity_score", "evidence", "geometry"]],
        style_function=lambda f: {
            "fillColor": cmap(min(max(f["properties"]["prospectivity_score"], vmin), vmax)),
            "color": "none", "weight": 0, "fillOpacity": 0.65},
        tooltip=folium.GeoJsonTooltip(
            fields=["zone_id", "prospectivity_score", "evidence"],
            aliases=["Zone", "Prospectivity score", "Evidence status"], localize=True),
    ).add_to(fg_zones)
    fg_zones.add_to(m)

    # Layer 2: smoothed heatmap (off by default)
    fg_heat = folium.FeatureGroup(name="Smoothed heatmap", show=False)
    heat_src = unknown if not unknown.empty else gdf
    HeatMap(heat_src[["lat", "lon", "prospectivity_score"]].values.tolist(),
            radius=18, blur=22, min_opacity=0.25).add_to(fg_heat)
    fg_heat.add_to(m)

    # Layer 3: zones with validated evidence (the training labels)
    ev_name = ("DEMO/SYNTHETIC evidence zones (training labels)" if is_demo
               else "Validated evidence zones (training labels)")
    fg_ev = folium.FeatureGroup(name=ev_name, show=True)
    folium.GeoJson(
        evidence[["zone_id", "label_class", "evidence", "geometry"]],
        style_function=lambda f: {
            "fillColor": "#6a3d9a" if f["properties"]["label_class"] == "mineralized"
                         else "#1f78b4",
            "color": "black", "weight": 1.5, "fillOpacity": 0.55},
        tooltip=folium.GeoJsonTooltip(fields=["zone_id", "evidence"],
                                      aliases=["Zone", "Evidence"]),
    ).add_to(fg_ev)
    fg_ev.add_to(m)

    # Layer 4: reference mine marker (NOT a label)
    fg_ref = folium.FeatureGroup(name="Reference: MOIL Balaghat mine (approx.)", show=True)
    folium.Marker([MINE_LAT, MINE_LON],
                  tooltip="Reference: MOIL Balaghat mine (approx.) - not used as a label",
                  icon=folium.Icon(color="black", icon="star")).add_to(fg_ref)
    fg_ref.add_to(m)

    # Layer 5: ranked exploration targets
    fg_t = folium.FeatureGroup(name=f"Top {len(targets)} Exploration Targets", show=True)
    for _, r in targets.iterrows():
        html = (f'<div style="background:#1f4e79;color:white;border-radius:50%;'
                f'width:24px;height:24px;line-height:24px;text-align:center;'
                f'font-weight:bold;border:2px solid white;">{int(r["rank"])}</div>')
        folium.Marker(
            [r["lat"], r["lon"]], icon=folium.DivIcon(html=html),
            tooltip=(f"Exploration target #{int(r['rank'])} - score "
                     f"{r['prospectivity_score']:.3f}"),
            popup=folium.Popup(
                f"<b>Exploration target #{int(r['rank'])}</b><br>Zone {r['zone_id']}<br>"
                f"Prospectivity score: {r['prospectivity_score']:.3f}<br>"
                f"{r['lat']:.4f}, {r['lon']:.4f}<br>"
                f"<i>Indicator for follow-up survey, not a reserve estimate.</i>",
                max_width=240)).add_to(fg_t)
    fg_t.add_to(m)

    cmap.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    # title + honesty banner
    if is_demo:
        banner = ("DEMO / SYNTHETIC DATA - simulated labels and features, "
                  "not real manganese evidence")
        colour = "#b00020"
    else:
        banner = "Exploration indicator - not a reserve estimate"
        colour = "#444"
    m.get_root().html.add_child(folium.Element(
        f'<div style="position:fixed;top:10px;left:50px;z-index:9999;'
        f'background:white;padding:6px 12px;border:2px solid #444;border-radius:6px;'
        f'font:14px Arial;"><b>MOIL Balaghat - Mineral Prospectivity</b><br>'
        f'<span style="color:{colour};">{banner}</span></div>'))

    b = gdf.total_bounds  # minx, miny, maxx, maxy
    m.fit_bounds([[b[1], b[0]], [b[3], b[2]]])
    return m, targets


if __name__ == "__main__":
    m, targets = build_prospectivity_map()
    m.save(OUT_HTML)
    targets.to_csv(OUT_TARGETS, index=False)
    print(f"Saved {OUT_HTML} and {OUT_TARGETS}\n")
    print("Top Exploration Targets (zones without validated evidence):")
    print(targets.to_string(index=False))
