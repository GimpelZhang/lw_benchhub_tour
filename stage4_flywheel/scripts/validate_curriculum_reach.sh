#!/usr/bin/env bash
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
source /mnt/robot/lerobot_arena_curobo_env.sh
unset CUDA_VISIBLE_DEVICES
for lvl in easy medium; do
  echo "===== reach gate ${lvl} ====="
  python /mnt/robot/validate_scene_objects_reach_v5.py \
    /mnt/robot/stage4_flywheel/configs/${lvl}_curriculum.yml \
    --threshold 0.50 \
    --report-json /mnt/robot/stage4_flywheel/metrics/curriculum/reach_report_${lvl}.json
  echo "REACH_GATE_${lvl}_EXIT=$?"
done
echo "CURRICULUM_VALIDATE_DONE"
