#!/usr/bin/env python3
"""Probe which seed places akita_black_bowl farthest from the robot base.
Spawns one subprocess per seed (robust: each gets a fresh Isaac Sim process)."""
import json, os, re, subprocess, sys
from pathlib import Path

BASE_YML = Path("/mnt/robot/lw_benchhub/configs/envhub/example.yml")
TMP_YML = Path("/mnt/robot/stage4_flywheel/configs/_probe_seed.yml")
PARTIAL = Path("/mnt/robot/stage4_flywheel/metrics/baseline/_probe_partial")
OUT = Path("/mnt/robot/stage4_flywheel/metrics/baseline/seed_probe.json")
PARTIAL.mkdir(parents=True, exist_ok=True)

N = int(os.environ.get("PROBE_N_SEEDS", "64"))
base_text = BASE_YML.read_text(encoding="utf-8")
assert re.search(r"^seed:\s*\d+", base_text, re.M), "example.yml has no seed line"

candidates = []
robot_base_anchor = None
for seed in range(N):
    text = re.sub(r"^seed:\s*\d+", f"seed: {seed}", base_text, count=1, flags=re.M)
    TMP_YML.write_text(text, encoding="utf-8")
    out_json = PARTIAL / f"seed_{seed}.json"
    if out_json.is_file():
        out_json.unlink()
    cmd = [sys.executable, "/mnt/robot/stage4_flywheel/scripts/_probe_one_seed.py",
           "--config", str(TMP_YML), "--out", str(out_json), "--seed", str(seed)]
    env = os.environ.copy()
    env.pop("CUDA_VISIBLE_DEVICES", None)
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        print(f"seed {seed}: TIMEOUT", file=sys.stderr, flush=True); continue
    if r.returncode != 0 or not out_json.is_file():
        print(f"seed {seed}: FAIL rc={r.returncode} stderr={r.stderr[-400:]}", file=sys.stderr, flush=True)
        continue
    d = json.loads(out_json.read_text())
    candidates.append(d)
    if seed == 0:
        robot_base_anchor = d["robot_world"]
    print(f"seed {seed:3d}: dist={d['dist_to_robot']:.3f} bowl={[round(x,3) for x in d['bowl_world']]}", flush=True)

if not candidates:
    print("ERROR: no seeds probed successfully", file=sys.stderr); sys.exit(1)
best = max(candidates, key=lambda x: x["dist_to_robot"])
OUT.write_text(json.dumps({"robot_base_anchor": robot_base_anchor,
                           "best_seed": best["seed"], "best": best,
                           "all": candidates, "n_probed": len(candidates)}, indent=2), encoding="utf-8")
print(json.dumps({"best_seed": best["seed"], "dist_to_robot": best["dist_to_robot"],
                  "n_probed": len(candidates)}, indent=2))
