#!/bin/bash
# Phase 1 Task 1.3 verification — check the exported LeRobotDataset + curriculum not overwritten.
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena

LEROBOT_DIR="/mnt/robot/stage4_flywheel/datasets/policy_demos_v3/policy_demos_v3_lerobot"
CURRICULUM_DIR="/mnt/robot/stage4_flywheel/datasets/doublepiper_pnp_curriculum"

echo "===== 1. LeRobotDataset non-empty ====="
if [ -d "$LEROBOT_DIR/data" ]; then
  n=$(ls "$LEROBOT_DIR/data" | wc -l)
  echo "data/ files: $n"
  ls "$LEROBOT_DIR/data" | head -5
else
  echo "FAIL: $LEROBOT_DIR/data missing"
fi

echo ""
echo "===== 2. schema check ====="
python - <<'PY'
from pathlib import Path
try:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    ds = LeRobotDataset(repo_id="policy_demos_v3",
        root=Path("/mnt/robot/stage4_flywheel/datasets/policy_demos_v3/policy_demos_v3_lerobot"))
    print(f"episodes: {ds.num_episodes}, frames: {ds.num_frames}")
    for k in ("observation.state","action","observation.images.left_hand","observation.images.right_hand","observation.images.first_person"):
        feat = ds.features.get(k)
        if feat is None:
            print(f"  {k}: MISSING")
        else:
            shape = feat.get("shape") if isinstance(feat, dict) else getattr(feat, "shape", None)
            print(f"  {k}: shape={shape}")
    assert ds.num_episodes >= 1, "no episodes"
    print("SCHEMA OK")
except Exception as e:
    print(f"SCHEMA CHECK FAILED: {e!r}")
PY

echo ""
echo "===== 3. original curriculum NOT overwritten ====="
if [ -d "$CURRICULUM_DIR" ]; then
  echo "ORIGINAL CURRICULUM STILL EXISTS: $CURRICULUM_DIR"
  ls "$CURRICULUM_DIR" | head -3
else
  echo "WARN: curriculum dir missing (was it never created?)"
fi

echo ""
echo "===== 4. manifest ====="
cat /mnt/robot/stage4_flywheel/datasets/policy_demos_v3/policy_demos_v3_manifest.json 2>/dev/null | python -c "import json,sys; d=json.load(sys.stdin); print('n_episodes:',d['n_episodes'],'n_frames:',d['n_frames_total'],'dist:',d['distribution'])" 2>/dev/null || echo "no manifest"
