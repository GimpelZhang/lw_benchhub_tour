#!/bin/bash
# Run one dataset-gen episode with full env setup. Args: seed difficulty episode_id
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
source /mnt/robot/lerobot_arena_curobo_env.sh
source /mnt/robot/deepseek_v4pro_env.sh
unset CUDA_VISIBLE_DEVICES

# numpy lock guard (must stay 1.26.0)
python -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__"

SEED=${1:?seed required}
DIFF=${2:?difficulty required}
EPID=${3:?episode_id required}
EXTRA=${4:-""}

cd /mnt/robot
python /mnt/robot/stage4_flywheel/scripts/run_dataset_gen.py \
    --seed "$SEED" --difficulty "$DIFF" --episode_id "$EPID" \
    --headless $EXTRA
