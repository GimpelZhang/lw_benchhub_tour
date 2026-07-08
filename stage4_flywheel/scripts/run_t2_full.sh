#!/usr/bin/env bash
# Phase 4 T2 full: curriculum-gradient SmolVLA eval (hard/easy/medium, 10 ep each)
# then head-view extraction + 3-way comparison grid.
set +u
echo "===== T2: curriculum-gradient eval ====="
bash /mnt/robot/stage4_flywheel/scripts/run_curriculum_eval.sh
echo "T2_EVAL_DONE exit=$?"
echo ""
echo "===== T2: parse success rates ====="
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
python3 - <<'PY'
import json, re, pathlib
base = pathlib.Path("/mnt/robot/stage4_flywheel/logs")
out = {}
for scene in ("hard_scene", "easy_curriculum", "medium_curriculum"):
    log = base / f"{scene}.log"
    sr = None; rc = None
    if log.is_file():
        t = log.read_text(errors="ignore")
        m = re.search(r"running_success_rate[=:]\s*([0-9.]+)", t)
        if m: sr = float(m.group(1))
        m2 = re.search(r"EXIT_CODE:\s*(-?\d+)", t)
        if m2: rc = int(m2.group(1))
    out[scene] = {"exit_code": rc, "success_rate_pct": sr}
    print(f"{scene}: exit={rc} success_rate={sr}%")
pathlib.Path("/mnt/robot/stage4_flywheel/metrics/curriculum_gradient.json").write_text(json.dumps(out, indent=2))
PY
echo ""
echo "===== T2: head-view extraction + grid ====="
bash /mnt/robot/stage4_flywheel/scripts/run_t2_headview_grid.sh
echo "T2_FULL_DONE"
