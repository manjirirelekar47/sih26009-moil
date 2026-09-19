"""
Pull regional-mean satellite time series for the Balaghat bounding box (Google Earth Engine).

Outputs
  data/raw/sentinel2_ndvi.csv      date, ndvi        (vegetation health)
  data/raw/sentinel1_vv.csv        date, sar_vv_db   (radar backscatter; near-surface soil-moisture proxy)
  data/raw/modis_lst.csv           date, lst_c       (land surface temperature, daytime, deg C)
  data/raw/chirps_rain.csv         date, rainfall_mm (daily rainfall)
  data/processed/weekly_features.csv   one row per Monday-start week, all four merged

Run from the repo root:   python -m src.data_pipeline.pull_timeseries
"""
import ee
import pandas as pd

from config import BBOX, DATA_PROCESSED, DATA_RAW, END_DATE, GEE_PROJECT, START_DATE


# ----------------------------------------------------------------------------
# Earth Engine helpers
# ----------------------------------------------------------------------------
def init_ee():
    """Initialise Earth Engine; run the browser login the first time only."""
    try:
        ee.Initialize(project=GEE_PROJECT)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=GEE_PROJECT)


def region():
    return ee.Geometry.Rectangle(BBOX)


def _end_exclusive(end_date: str) -> str:
    """Earth Engine's filterDate() excludes the end date, so add one day."""
    return (pd.Timestamp(end_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")


# ----------------------------------------------------------------------------
# Collections (each returns an ImageCollection with a single named band)
# ----------------------------------------------------------------------------
def s2_collection(start, end_excl):
    """Sentinel-2 surface reflectance -> cloud-masked NDVI."""

    def to_ndvi(img):
        scl = img.select("SCL")  # scene classification layer
        bad = scl.eq(3).Or(scl.gte(8).And(scl.lte(11)))  # shadow, cloud, cirrus, snow
        return (
            img.normalizedDifference(["B8", "B4"])
            .rename("ndvi")
            .updateMask(bad.Not())
            .copyProperties(img, ["system:time_start"])
        )

    return (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region())
        .filterDate(start, end_excl)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
        .map(to_ndvi)
    )


def s1_collection(start, end_excl):
    """Sentinel-1 SAR, VV polarisation (already in dB in Earth Engine)."""
    return (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(region())
        .filterDate(start, end_excl)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .select("VV")
        .map(lambda img: img.rename("sar_vv_db").copyProperties(img, ["system:time_start"]))
    )


def modis_collection(start, end_excl):
    """MODIS 8-day land surface temperature (daytime), converted to deg C."""

    def to_celsius(img):
        return (
            img.select("LST_Day_1km")
            .multiply(0.02)  # scale factor -> Kelvin
            .subtract(273.15)
            .rename("lst_c")
            .copyProperties(img, ["system:time_start"])
        )

    return (
        ee.ImageCollection("MODIS/061/MOD11A2")
        .filterBounds(region())
        .filterDate(start, end_excl)
        .map(to_celsius)
    )


def chirps_collection(start, end_excl):
    """CHIRPS daily rainfall (mm/day)."""
    return (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterBounds(region())
        .filterDate(start, end_excl)
        .select("precipitation")
        .map(lambda img: img.rename("rainfall_mm").copyProperties(img, ["system:time_start"]))
    )


# ----------------------------------------------------------------------------
# Reduce each image to one regional mean and download as a table
# ----------------------------------------------------------------------------
def _year_chunks(start, end):
    """Split the window into calendar years so each Earth Engine request stays small."""
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    for year in range(s.year, e.year + 1):
        a = max(s, pd.Timestamp(year, 1, 1))
        b = min(e, pd.Timestamp(year, 12, 31))
        yield a.strftime("%Y-%m-%d"), (b + pd.Timedelta(days=1)).strftime("%Y-%m-%d")


def _means_per_image(col, band, scale):
    geom = region()

    def reduce_one(img):
        val = img.select(band).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom, scale=scale, maxPixels=1e9, bestEffort=True
        ).get(band)
        return ee.Feature(None, {"date": img.date().format("YYYY-MM-dd"), band: val})

    fc = col.map(reduce_one).filter(ee.Filter.notNull([band]))
    rows = [f["properties"] for f in fc.getInfo()["features"]]
    return pd.DataFrame(rows, columns=["date", band])


def pull_dataset(name, builder, band, scale):
    frames = []
    for a, b_excl in _year_chunks(START_DATE, END_DATE):
        print(f"  {name}: {a} -> {b_excl} ...", flush=True)
        frames.append(_means_per_image(builder(a, b_excl), band, scale))
    df = pd.concat(frames, ignore_index=True)
    df = df.groupby("date", as_index=False)[band].mean()  # merge overlapping tiles on one date
    out = DATA_RAW / f"{name}.csv"
    df.to_csv(out, index=False)
    print(f"  saved {out.relative_to(DATA_RAW.parent.parent)}  ({len(df)} rows)")
    return df


# ----------------------------------------------------------------------------
# Weekly merge (this is the file the other team members will use)
# ----------------------------------------------------------------------------
def build_weekly(rain, ndvi, vv, lst):
    def series(df, col):
        return df.set_index(pd.to_datetime(df["date"]))[col].sort_index()

    r = series(rain, "rainfall_mm")
    weekly = pd.DataFrame(
        {
            "rainfall_mm": r.resample("W-MON", label="left", closed="left").sum(min_count=1),
            "days_in_week": r.resample("W-MON", label="left", closed="left").count(),
        }
    )
    for df, col in [(ndvi, "ndvi"), (vv, "sar_vv_db"), (lst, "lst_c")]:
        weekly[col] = series(df, col).resample("W-MON", label="left", closed="left").mean()

    weekly = weekly[weekly["days_in_week"] == 7].drop(columns="days_in_week")  # drop partial weeks
    # Satellite passes are every 5-16 days, so fill short gaps by linear interpolation.
    for col in ["ndvi", "sar_vv_db", "lst_c"]:
        weekly[col] = weekly[col].interpolate(limit=3, limit_direction="both")
    weekly.index.name = "week_start"
    weekly = weekly.reset_index()
    num = ["rainfall_mm", "ndvi", "sar_vv_db", "lst_c"]
    weekly[num] = weekly[num].round(4)
    return weekly


def main():
    init_ee()
    print("Pulling satellite time series for Balaghat ...")
    ndvi = pull_dataset("sentinel2_ndvi", s2_collection, "ndvi", scale=100)
    vv = pull_dataset("sentinel1_vv", s1_collection, "sar_vv_db", scale=100)
    lst = pull_dataset("modis_lst", modis_collection, "lst_c", scale=1000)
    rain = pull_dataset("chirps_rain", chirps_collection, "rainfall_mm", scale=5566)

    weekly = build_weekly(rain, ndvi, vv, lst)
    out = DATA_PROCESSED / "weekly_features.csv"
    weekly.to_csv(out, index=False)
    print(f"\nSaved {out.relative_to(DATA_PROCESSED.parent.parent)}  ({len(weekly)} weeks)")
    print(weekly.describe().round(2))


if __name__ == "__main__":
    main()
