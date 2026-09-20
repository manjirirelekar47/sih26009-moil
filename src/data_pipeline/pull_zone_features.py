"""
Build the per-zone feature table that Reserve Mapping (Member 2) trains on.

The Balaghat bounding box is cut into ~1 km grid cells. For each cell we compute the mean of
long-term satellite/terrain layers: NDVI, SAR backscatter, land surface temperature, rainfall,
elevation and slope. Distance to the known mine is added so Member 2 can build the label
(e.g. cells within X km of the mine = positive).

Output: data/processed/zone_features.csv
Run from the repo root:   python -m src.data_pipeline.pull_zone_features

v2: Added ndvi_std and sar_vh_mean to match Member 2's feature contract.
"""
import math

import ee
import numpy as np
import pandas as pd

from config import (BBOX, DATA_PROCESSED, END_DATE, GRID_CELL_DEG, MINE_LAT, MINE_LON, START_DATE)
from src.data_pipeline.pull_timeseries import (
    _end_exclusive, chirps_collection, init_ee, modis_collection, s1_collection, s2_collection,
)

BATCH = 150  # cells per Earth Engine request


def make_cells():
    west, south, east, north = BBOX
    xs = np.arange(west, east - 1e-9, GRID_CELL_DEG)
    ys = np.arange(south, north - 1e-9, GRID_CELL_DEG)
    cells = []
    for r, y in enumerate(ys):
        for c, x in enumerate(xs):
            cells.append(
                ee.Feature(
                    ee.Geometry.Rectangle([float(x), float(y), float(x + GRID_CELL_DEG), float(y + GRID_CELL_DEG)]),
                    {
                        "zone_id": f"r{r:02d}_c{c:02d}",
                        "lon": round(float(x + GRID_CELL_DEG / 2), 5),
                        "lat": round(float(y + GRID_CELL_DEG / 2), 5),
                    },
                )
            )
    return cells


def s1_vh_collection(start, end_excl):
    """Sentinel-1 SAR, VH polarisation."""
    return (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(ee.Geometry.Rectangle(BBOX))
        .filterDate(start, end_excl)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select("VH")
        .map(lambda img: img.rename("sar_vh_mean_db").copyProperties(img, ["system:time_start"]))
    )


def feature_stack():
    end_excl = _end_exclusive(END_DATE)
    years = (pd.Timestamp(END_DATE) - pd.Timestamp(START_DATE)).days / 365.25
    dem = ee.Image("USGS/SRTMGL1_003")

    s2 = s2_collection(START_DATE, end_excl)
    s1_vv = s1_collection(START_DATE, end_excl)
    s1_vh = s1_vh_collection(START_DATE, end_excl)

    return ee.Image.cat(
        [
            s2.median().rename("ndvi_median"),          # NDVI median
            s2.reduce(ee.Reducer.stdDev()).rename("ndvi_std"),  # NDVI std dev
            s1_vv.mean().rename("sar_vv_mean_db"),      # SAR VV mean
            s1_vh.mean().rename("sar_vh_mean_db"),      # SAR VH mean (new)
            modis_collection(START_DATE, end_excl).mean().rename("lst_mean_c"),
            chirps_collection(START_DATE, end_excl).sum().divide(years).rename("rain_mm_per_year"),
            dem.rename("elevation_m"),
            ee.Terrain.slope(dem).rename("slope_deg"),
        ]
    )


def haversine_km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (
        0.5
        - np.cos((lat2 - lat1) * p) / 2
        + np.cos(lat1 * p) * np.cos(lat2 * p) * (1 - np.cos((lon2 - lon1) * p)) / 2
    )
    return 12742 * np.arcsin(np.sqrt(a))


def main():
    init_ee()
    stack = feature_stack()
    cells = make_cells()
    print(f"{len(cells)} grid cells; requesting in batches of {BATCH} ...")
    rows = []
    for i in range(0, len(cells), BATCH):
        fc = ee.FeatureCollection(cells[i : i + BATCH])
        out = stack.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=100, tileScale=4)
        rows += [f["properties"] for f in out.getInfo()["features"]]
        print(f"  {min(i + BATCH, len(cells))}/{len(cells)}", flush=True)

    df = pd.DataFrame(rows)
    df["dist_to_mine_km"] = haversine_km(df["lat"], df["lon"], MINE_LAT, MINE_LON).round(3)
    df = df.sort_values("zone_id").reset_index(drop=True).round(4)
    out_path = DATA_PROCESSED / "zone_features.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {out_path.relative_to(DATA_PROCESSED.parent.parent)}  ({len(df)} zones)")
    print(df.describe().round(2))


if __name__ == "__main__":
    main()
