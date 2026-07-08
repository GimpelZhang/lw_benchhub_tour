#!/bin/bash

gpu_id=0

export CUDA_VISIBLE_DEVICES=${gpu_id}
task_config=lerobot_liftobj_state_play

python ./lw_benchhub/scripts/maniskill_ppo/play.py \
    --task_config="$task_config" \
    # --enable_cameras \
    # --headless \
