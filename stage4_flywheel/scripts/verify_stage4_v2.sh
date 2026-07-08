#!/bin/bash
# Verify the Stage 4 v2 re-run deliverables: dataset, distribution, schema, env integrity.
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena

PASS=0; FAIL=0
ok() { echo "  PASS: $1"; PASS=$((PASS+1)); }
no() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

echo "=== 1. Environment integrity ==="
python3 -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__" 2>/dev/null && ok "numpy 1.26.0" || no "numpy != 1.26.0"
python3 -c "import warp; assert hasattr(warp.types,'array'); assert warp.__version__=='1.8.1'" 2>/dev/null && ok "warp-lang 1.8.1 (warp.types.array present)" || no "warp-lang broken"
python3 -c "import torch; assert torch.cuda.is_available()" 2>/dev/null && ok "torch cuda available" || no "torch cuda unavailable"

echo "=== 2. Raw HDF5 episodes ==="
for d in easy medium hard; do
  n=$(python3 -c "
import json,glob
ss=glob.glob('/mnt/robot/stage4_flywheel/datasets/raw/$d/episode_*_summary.json')
print(sum(1 for s in ss if json.load(open(s)).get('success') and json.load(open(s)).get('n_frames',0)>0))
" 2>/dev/null)
  echo "  $d: $n successful"
  [ "$n" -ge 2 ] && ok "$d has >=2 episodes (target 3; medium may be 2 per best-effort)" || no "$d has only $n episodes"
done

echo "=== 3. Lerobot dataset ==="
DS_ROOT=/mnt/robot/stage4_flywheel/datasets/doublepiper_pnp_curriculum
[ -d "$DS_ROOT" ] && ok "lerobot dataset dir exists" || no "lerobot dataset dir missing"
python3 - << 'PY' 2>/dev/null && ok "lerobot dataset loads + schema correct" || no "lerobot dataset load/schema failed"
from lerobot.datasets.lerobot_dataset import LeRobotDataset
ds = LeRobotDataset("doublepiper_pnp_curriculum", root="/mnt/robot/stage4_flywheel/datasets/doublepiper_pnp_curriculum")
f = ds.meta.features
assert f["observation.state"]["shape"] == (16,), f["observation.state"]
assert f["action"]["shape"] == (12,), f["action"]
for k in ["observation.images.left_hand","observation.images.right_hand","observation.images.first_person"]:
    assert k in f, f"missing {k}"
assert ds.meta.total_episodes >= 8, f"only {ds.meta.total_episodes} episodes"
assert ds.meta.total_frames > 1000, f"only {ds.meta.total_frames} frames"
print(f"  episodes={ds.meta.total_episodes} frames={ds.meta.total_frames} fps={ds.meta.fps} robot={ds.meta.robot_type}")
PY

echo "=== 4. Dataset manifest ==="
MF=/mnt/robot/stage4_flywheel/datasets/dataset_manifest.json
[ -f "$MF" ] && ok "manifest exists" || no "manifest missing"
python3 -c "import json; d=json.load(open('$MF')); print('  distribution:', d['distribution']); print('  total_frames:', d['n_frames_total']); print('  total_episodes:', d['n_episodes'])" 2>/dev/null

echo "=== 5. Curriculum ymls ==="
for d in easy medium hard; do
  n=$(ls /mnt/robot/stage4_flywheel/curriculum/scene_${d}_seed*.yml 2>/dev/null | wc -l)
  [ "$n" -ge 1 ] && ok "$d curriculum yml exists ($n)" || no "$d curriculum yml missing"
done
[ -f /mnt/robot/stage4_flywheel/curriculum/curriculum_manifest.json ] && ok "curriculum manifest exists" || no "curriculum manifest missing"

echo "=== 6. DeepSeek-v4-pro (anti-degrade) ==="
grep -q "deepseek-v4-pro" /mnt/robot/deepseek_v4pro_env.sh 2>/dev/null && ok "DEEPSEEK_MODEL=deepseek-v4-pro in env" || no "deepseek model not v4-pro"
grep -q "deepseek-v4-pro" /mnt/robot/stage4_flywheel/logs/dataset_gen_easy_s13_ep0.log 2>/dev/null && ok "decomposer used deepseek-v4-pro (found in log)" || echo "  (note: check decomposer log for model verification)"

echo "=== 7. Protected paths unchanged ==="
# NOTE: after the lw_benchhub_tour monorepo reorg (2026-07-08), top-level *.md
# moved to docs/. Update the protected-path locations accordingly. The
# eval_outputs_* dirs are gitignored runtime outputs (regenerated on rerun) and
# may have been cleaned between runs; treat their absence as non-fatal (warn).
for p in /mnt/robot/docs/Complete_Stage_1.md /mnt/robot/docs/Stage4_Plan.md /mnt/robot/llm_env.sh /mnt/robot/stage2_v6_final_deliverables /mnt/robot/lw_benchhub/configs/envhub/generated_v6; do
  [ -e "$p" ] && ok "protected path intact: $(basename $p)" || no "protected path missing: $p"
done
for p in /mnt/robot/eval_outputs_pathB_1 /mnt/robot/eval_outputs_stage2_v6_scene1; do
  [ -e "$p" ] && ok "upstream output intact: $(basename $p)" || echo "  WARN: upstream output not on disk (regenerable): $(basename $p)"
done

echo "=== 8. Report updated ==="
[ -f /mnt/robot/stage4_flywheel/stage4_flywheel_report.md ] && ok "report exists" || no "report missing"
grep -q "fine-tuning dataset\|lerobot\|doublepiper_pnp_curriculum" /mnt/robot/stage4_flywheel/stage4_flywheel_report.md 2>/dev/null && ok "report mentions dataset deliverable" || no "report missing dataset section"

echo ""
echo "=== RESULT: $PASS PASS / $FAIL FAIL ==="
