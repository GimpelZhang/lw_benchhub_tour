#!/usr/bin/env bash
# Post-baseline: parse metrics, extract head-view, write meta. (No GPU.)
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
echo "===== parse baseline metrics ====="
python /mnt/robot/stage4_flywheel/scripts/parse_baseline_metrics.py
echo ""
echo "===== extract head-view (hard_scene) ====="
bash /mnt/robot/stage4_flywheel/scripts/extract_headview.sh \
  hard_scene /mnt/robot/stage4_flywheel/metrics/baseline/hard_scene_run || echo "head-view extract failed"
echo ""
echo "===== write hard_scene_meta.json ====="
python /mnt/robot/stage4_flywheel/scripts/write_hard_meta.py
echo ""
echo "POST_BASELINE_DONE"
