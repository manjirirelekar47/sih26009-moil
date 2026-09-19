"""Shared settings for every module. Change values HERE, not inside individual scripts."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_DEMO = ROOT / "data" / "demo"

# --- Google Earth Engine ---------------------------------------------------
# Your Google Cloud project ID (registered for Earth Engine, non-commercial use).
# Either edit this string or set the environment variable EE_PROJECT.
GEE_PROJECT = os.environ.get("EE_PROJECT", "serious-citron-317703")

# --- Study area: Balaghat, Madhya Pradesh ------------------------------------
# [west, south, east, north] in degrees (~33 km x 33 km around the mine cluster)
BBOX = [80.05, 21.65, 80.35, 21.95]
MINE_LAT, MINE_LON = 21.80, 80.19       # approx. centre of the Balaghat mine

# --- Time window (3 complete years) -------------------------------------------
START_DATE = "2023-01-01"
END_DATE = "2025-12-31"                 # inclusive

# --- Synthetic production anchor ----------------------------------------------
# MOIL's reported annual production scale (from the project report).
# NOTE: this is a company-wide figure across ~10 mines. If the dashboard shows a
# single mine, replace with a mine-level figure once you have a source for it.
ANNUAL_TARGET_TONNES = 1_100_000
TARGET_ACHIEVEMENT = 0.97               # average actual / planned over the period
RANDOM_SEED = 42

# --- Reserve-mapping grid -------------------------------------------------------
GRID_CELL_DEG = 0.01                    # ~1.1 km cells
