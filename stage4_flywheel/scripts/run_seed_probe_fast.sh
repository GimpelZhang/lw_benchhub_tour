#!/usr/bin/env bash
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
unset CUDA_VISIBLE_DEVICES
cd /mnt/robot/lw_benchhub
PROBE_N_SEEDS=64 python /mnt/robot/stage4_flywheel/scripts/probe_bowl_seed_inprocess.py
echo "FAST_SEED_PROBE_EXIT=$?"
