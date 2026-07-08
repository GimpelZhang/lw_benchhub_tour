#!/usr/bin/env bash
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
source /mnt/robot/lerobot_arena_curobo_env.sh
unset CUDA_VISIBLE_DEVICES
export AUTOSIM_LLM_API_KEY=dummy  # stub: cache hit skips the LLM call
python -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__"
python /mnt/robot/stage4_flywheel/scripts/save_franka_smoke_trajectory.py --num_runs=3 --headless
echo "T1_SMOKE_DONE"
