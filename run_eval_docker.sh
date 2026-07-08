#!/bin/bash
# Script to run the microwave evaluation inside Docker
# Usage: bash run_eval_docker.sh

set -e

ISAACSIM_PYTHON=/isaac-sim/python.sh

# Patch lerobot for Python compatibility if needed
if [ -d /opt/lerobot ]; then
    cd /opt/lerobot

    # Fix PEP 695 type aliases (Python 3.11 compat)
    if grep -q "type NameOrID = " src/lerobot/motors/motors_bus.py 2>/dev/null; then
        echo "Patching lerobot for Python 3.11 compatibility..."
        sed -i 's/^type NameOrID = str | int$/from typing import Union\nNameOrID = Union[str, int]/' src/lerobot/motors/motors_bus.py
        sed -i 's/^type Value = int | float$/Value = Union[int, float]/' src/lerobot/motors/motors_bus.py
    fi
fi

# Set environment
export HF_HOME=/root/.cache/huggingface
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH

# Run evaluation
echo "Starting microwave task evaluation..."
$ISAACSIM_PYTHON -m lerobot.scripts.eval \
    --policy.path=/models/pi05-microwave \
    --env.type=isaaclab_arena \
    --env.hub_path=nvidia/isaaclab-arena-envs \
    --rename_map='{"observation.images.robot_pov_cam_rgb": "observation.images.robot_pov_cam"}' \
    --policy.device=cuda \
    --env.environment=gr1_microwave \
    --env.embodiment=gr1_pink \
    --env.object=mustard_bottle \
    --env.headless=true \
    --env.enable_cameras=true \
    --env.video=true \
    --env.video_length=200 \
    --env.video_interval=1 \
    --env.state_keys=robot_joint_pos \
    --env.camera_keys=robot_pov_cam_rgb \
    --env.num_envs=1 \
    --trust_remote_code=True \
    --eval.batch_size=1 \
    --output_dir=/eval_outputs

echo "Evaluation complete! Results in /eval_outputs"
