#!/bin/bash
task_config=lerobot_liftobj_state

python ./lw_benchhub/scripts/maniskill_ppo/train.py \
    --task_config="$task_config" \
    --headless \

