#!/usr/bin/env bash
# T3 pipeline run: DoublePiperKitchenPnpPipeline on one curriculum scene.
# Usage: run_t3_pipeline.sh <easy|medium|hard>
# Run AFTER run_t3_prep.sh passes (cuRobo config + sim names verified).
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
source /mnt/robot/lerobot_arena_curobo_env.sh
source /mnt/robot/deepseek_v4pro_env.sh
unset CUDA_VISIBLE_DEVICES
python -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__"

SCENE=${1:-easy}
YML=/mnt/robot/stage4_flywheel/curriculum/scene_${SCENE}.yml
LOG=/mnt/robot/stage4_flywheel/logs/t3_scene_${SCENE}.log
echo "===== T3 pipeline: scene_${SCENE} ====="
python /mnt/robot/AutoDataGen/examples/run_doublepiper_pnp.py \
  --config_path "${YML}" \
  --output_dir /mnt/robot/stage4_flywheel/demos \
  --num_runs 1 --headless 2>&1 | tee "${LOG}"
echo "T3_SCENE_${SCENE}_EXIT=${PIPESTATUS[0]}" >> "${LOG}"
echo "T3_SCENE_${SCENE}_DONE"
