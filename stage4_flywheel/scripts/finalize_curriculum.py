"""Finalize the curriculum deliverable: copy per-seed scene ymls into a clean
curriculum/ directory + emit a manifest documenting the even easy/medium/hard
distribution used for the dataset.

Reads the redefined seed_plan.json (bands.<diff>.seeds, reachable >=0.260m).
"""

import json
import shutil
from pathlib import Path

ROOT = Path("/mnt/robot/stage4_flywheel")
RAW = ROOT / "datasets/raw"
CURR = ROOT / "curriculum"
SEED_PLAN = ROOT / "datasets/seed_plan.json"
PROBE = ROOT / "metrics/baseline/seed_probe.json"
DIFFS = ["easy", "medium", "hard"]


def main():
    CURR.mkdir(parents=True, exist_ok=True)
    plan = json.loads(SEED_PLAN.read_text())
    bands = plan.get("bands", {})

    # Build seed -> (dist, bowl_world) lookup from the probe.
    seed_info = {}
    if PROBE.exists():
        for s in json.loads(PROBE.read_text()).get("all", []):
            seed_info[s["seed"]] = (s["dist_to_robot"], s["bowl_world"])

    manifest = {
        "description": "T3 seed-based curriculum for the DoublePiper PnP fine-tuning dataset. "
                       "3 seeds per difficulty band (easy/medium/hard), even 3/3/3 distribution. "
                       "Bands = distance tertiles of REACHABLE seeds (>=0.260m; closer seeds hang/plan-fail).",
        "task": "L90K1PutTheBlackBowlOnThePlate",
        "robot": "DoublePiper-Abs",
        "distribution_target": "3 easy + 3 medium + 3 hard (even)",
        "reachable_threshold_m": plan.get("reachable_threshold_m", 0.260),
        "bands": {},
    }

    for diff in DIFFS:
        band = bands.get(diff, {})
        seeds = band.get("seeds", [])
        manifest["bands"][diff] = {
            "dist_range_m": band.get("dist_range_m", "n/a"),
            "seeds": seeds,
            "seed_details": [
                {"seed": s, "dist_to_robot_m": round(seed_info.get(s, (None, None))[0] or 0, 4)}
                for s in seeds
            ],
        }
        # Copy per-seed ymls from raw/<diff>/scene_seed<seed>.yml -> curriculum/<diff>_seed<seed>.yml
        for seed in seeds:
            src = RAW / diff / f"scene_seed{seed}.yml"
            dst = CURR / f"scene_{diff}_seed{seed}.yml"
            if src.exists():
                shutil.copy2(src, dst)
                print(f"  copied {src.name} -> {dst.name}")
            else:
                print(f"  WARN: {src} missing (episode may not have run yet)")

    # Attach actual episode outcomes from the summaries.
    episodes = []
    for diff in DIFFS:
        for sumf in sorted((RAW / diff).glob("episode_*_summary.json")):
            d = json.loads(sumf.read_text())
            episodes.append({
                "difficulty": d["difficulty"],
                "seed": d["seed"],
                "episode_id": d["episode_id"],
                "n_frames": d["n_frames"],
                "success": d["success"],
                "state_dim": d.get("state_dim"),
                "action_dim": d.get("action_dim"),
            })
    episodes.sort(key=lambda e: (DIFFS.index(e["difficulty"]) if e["difficulty"] in DIFFS else 99, e["episode_id"]))
    manifest["episodes"] = episodes
    manifest["n_successful"] = sum(1 for e in episodes if e["success"] and e["n_frames"] > 0)
    manifest["distribution_actual"] = {
        d: sum(1 for e in episodes if e["difficulty"] == d and e["success"] and e["n_frames"] > 0)
        for d in DIFFS
    }

    out = CURR / "curriculum_manifest.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest: {out}")
    print("Actual distribution:", manifest["distribution_actual"])
    print(f"Successful episodes: {manifest['n_successful']}/{len(episodes)}")


if __name__ == "__main__":
    main()
