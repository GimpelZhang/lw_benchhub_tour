#!/usr/bin/env bash
# Phase 3: reach-gate on hard scene -> diagnose -> DeepSeek-v4-pro curriculum -> reach-gate validate.
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
source /mnt/robot/lerobot_arena_curobo_env.sh   # reach gate needs cuRobo
source /mnt/robot/deepseek_v4pro_env.sh          # curriculum gen needs DeepSeek
unset CUDA_VISIBLE_DEVICES
python -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__"
mkdir -p /mnt/robot/stage4_flywheel/metrics/curriculum

echo "===== 3.1 reach gate on hard_scene.yml ====="
python /mnt/robot/validate_scene_objects_reach.py \
  /mnt/robot/stage4_flywheel/configs/hard_scene.yml \
  --threshold 0.50 \
  --report-json /mnt/robot/stage4_flywheel/metrics/baseline/reach_report.json
echo "REACH_GATE_HARD_EXIT=$?"

echo "===== 3.2 diagnose failure ====="
python /mnt/robot/stage4_flywheel/scripts/diagnose_failure.py
echo "DIAGNOSE_EXIT=$?"

echo "===== 3.3 generate curriculum (DeepSeek-v4-pro) ====="
python /mnt/robot/stage4_flywheel/scripts/generate_curriculum.py
echo "CURRICULUM_GEN_EXIT=$?"

echo "===== 3.4 reach-gate validate easy + medium ====="
for lvl in easy medium; do
  echo "--- reach gate ${lvl} ---"
  python /mnt/robot/validate_scene_objects_reach.py \
    /mnt/robot/stage4_flywheel/configs/${lvl}_curriculum.yml \
    --threshold 0.50 \
    --report-json /mnt/robot/stage4_flywheel/metrics/curriculum/reach_report_${lvl}.json
  echo "REACH_GATE_${lvl}_EXIT=$?"
done
echo "PHASE3_DONE"
