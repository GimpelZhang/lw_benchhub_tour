"""Phase 1 gate evaluator — read all episode summaries and report Gate A / Gate A2 status.

Gate A  (Task 1.2 baseline): >=1 TASK_SUCCESS=True in the first 10 episodes.
Gate A2 (Task 1.3 dataset sufficiency): >=9 total successes (plan §1.3).

Usage:
    python evaluate_phase1_gates.py [RAW_ROOT]
"""
import json
import sys
from pathlib import Path
from collections import Counter

RAW_ROOT = Path(sys.argv[1] if len(sys.argv) > 1
                else "/mnt/robot/stage4_flywheel/datasets/policy_demos_v3/raw")


def main():
    summaries = []
    for band_dir in sorted(RAW_ROOT.iterdir()) if RAW_ROOT.exists() else []:
        if not band_dir.is_dir():
            continue
        for s in sorted(band_dir.glob("episode_*_summary.json"),
                        key=lambda p: int(p.stem.split("_")[1])):
            try:
                d = json.loads(s.read_text())
                d["_band"] = band_dir.name
                summaries.append(d)
            except Exception as e:
                print(f"  WARN: unreadable {s}: {e}")

    if not summaries:
        print(f"NO SUMMARIES FOUND in {RAW_ROOT}")
        sys.exit(2)

    print(f"=== Phase 1 collection summary ({len(summaries)} episodes) ===")
    print(f"{'ep':>3} {'band':>10} {'seed':>6} {'n_frames':>8} {'success':>7}  bowl_pos")
    for d in summaries:
        bowl = d.get("bowl_pos")
        bowl_str = f"[{bowl[0]:.2f},{bowl[1]:.2f},{bowl[2]:.2f}]" if bowl else "n/a"
        print(f"{d['episode_id']:>3} {d['_band']:>10} {d['seed']:>6} "
              f"{d.get('n_frames',0):>8} {str(d['success']):>7}  {bowl_str}")

    n_total = len(summaries)
    n_success = sum(1 for d in summaries if d.get("success"))
    n_fail = n_total - n_success
    seeds = [d["seed"] for d in summaries]
    seed_unique = len(set(seeds))

    print(f"\n=== Totals ===")
    print(f"episodes={n_total}  successes={n_success}  fails={n_fail}")
    print(f"unique seeds={seed_unique}  (seeds: {sorted(set(seeds))[:10]}{'...' if seed_unique>10 else ''})")
    print(f"success rate={n_success/n_total*100:.1f}%")

    # Gate A: first 10 episodes (by episode_id), >=1 success
    first10 = sorted(summaries, key=lambda d: d["episode_id"])[:10]
    first10_succ = sum(1 for d in first10 if d.get("success"))
    gate_a = first10_succ >= 1
    print(f"\n=== Gate A (baseline feasibility, first 10 episodes) ===")
    print(f"successes in first 10 = {first10_succ}/10")
    print(f"Gate A: {'PASS' if gate_a else 'FAIL'} ({'>=1 success -> Phase 1 viable' if gate_a else '0 success -> skip to Phase 2'})")

    # Gate A2: >=9 total successes
    gate_a2 = n_success >= 9
    print(f"\n=== Gate A2 (dataset sufficiency) ===")
    print(f"total successes = {n_success} (target >=9)")
    print(f"Gate A2: {'PASS' if gate_a2 else 'FAIL'}")

    # Band distribution
    band_dist = Counter(d["_band"] for d in summaries if d.get("success"))
    print(f"\nSuccess distribution by band: {dict(band_dist)}")

    # HDF5 count (should equal successes)
    h5_count = sum(1 for d in summaries if d.get("h5_path"))
    print(f"HDF5 files written: {h5_count} (should == successes {n_success})")

    print(f"\n=== Recommendation ===")
    if gate_a2:
        print("Gate A2 PASS -> run build_policy_demos_dataset.py to export LeRobotDataset. Phase 2 optional.")
    elif gate_a:
        print(f"Gate A PASS but Gate A2 FAIL (only {n_success} successes). "
              f"Options: (a) run more episodes (increase MAX_TOTAL); (b) proceed to Phase 2.")
    else:
        print("Gate A FAIL -> SmolVLA not producing successes. Proceed to Phase 2 (descend + collision spheres).")


if __name__ == "__main__":
    main()
