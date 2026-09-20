"""
run_pipeline.py - One-command runner for the whole Reserve Mapping pipeline
SIH26009 / MOIL (Member 2)

Runs step1 -> step2 -> step3 -> step4 in order, in-process (importing each
step's main logic rather than shelling out), so a failure in any step stops
the run immediately with a clear message instead of silently leaving stale
files from a previous run sitting in data/. Built so the whole reserve-map
demo is a single command on the day of the demo.

Usage:
    python run_pipeline.py                 # demo / synthetic mode (default)
    python run_pipeline.py --mode real --labels data/geological_labels.csv
"""
import argparse
import subprocess
import sys
import time

STEPS = [
    ("step1_build_zones.py", "Build candidate zones + evidence-based labels"),
    ("step2_features.py", "Build / load + clean the feature table"),
    ("step3_train_model.py", "Train + validate + save the prospectivity model"),
    ("step4_make_map.py", "Build the Folium map + Top Exploration Targets"),
]


def run_step(script, description, extra_args):
    print("\n" + "=" * 70)
    print(f"STEP: {script}  -  {description}")
    print("=" * 70)
    t0 = time.time()
    # step1 is the only script that takes CLI args (--mode/--labels); the
    # others always read whatever step1 wrote, so extra_args is a no-op there.
    args = [sys.executable, script] + (extra_args if script == "step1_build_zones.py" else [])
    result = subprocess.run(args)
    dt = time.time() - t0
    if result.returncode != 0:
        print(f"\n*** {script} FAILED (exit code {result.returncode}) after {dt:.1f}s. "
              f"Stopping - later steps would run on stale/missing data. ***")
        sys.exit(result.returncode)
    print(f"--- {script} OK ({dt:.1f}s) ---")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["demo", "real"], default="demo",
                     help="passed through to step1_build_zones.py")
    ap.add_argument("--labels", default="data/geological_labels.csv",
                     help="passed through to step1_build_zones.py (real mode only)")
    a = ap.parse_args()

    extra_args = ["--mode", a.mode, "--labels", a.labels]

    print("#" * 70)
    print(f"# RESERVE MAPPING PIPELINE - mode={a.mode}")
    if a.mode == "demo":
        print("# DEMO / SYNTHETIC run - for testing the software only.")
    print("#" * 70)

    t_start = time.time()
    for script, desc in STEPS:
        run_step(script, desc, extra_args)

    print("\n" + "#" * 70)
    print(f"# PIPELINE COMPLETE in {time.time() - t_start:.1f}s")
    print("# Outputs:")
    print("#   data/prospectivity_map.html       <- open in a browser")
    print("#   data/top_exploration_targets.csv")
    print("#   models/prospectivity_model.joblib <- hand off to Member 6")
    print("#" * 70)


if __name__ == "__main__":
    main()
