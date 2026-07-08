#!/bin/bash
set -u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
unset CUDA_VISIBLE_DEVICES

cd /mnt/robot/lw_benchhub  # <-- run from lw_benchhub so relative configs path resolves

echo "=== Environment ==="
echo "PWD: $(pwd)"
echo "PYTHON: $(which python)"
echo "NUMPY: $(python -c 'import numpy; print(numpy.__version__)')"
echo "GPU FREE: $(nvidia-smi --query-gpu=memory.free --format=csv,noheader)"
echo "STARTED: $(date -Iseconds)"
ls configs/envhub/example.yml && echo "CONFIG OK"
echo "===================="

lerobot-eval \
  --policy.path=LightwheelAI/smolvla-double-piper-pnp \
  --env.type=isaaclab_arena \
  --rename_map='{"observation.images.left_hand_camera_rgb": "observation.images.left_hand", "observation.images.right_hand_camera_rgb": "observation.images.right_hand", "observation.images.first_person_camera_rgb": "observation.images.first_person"}' \
  --env.hub_path=LightwheelAI/lw_benchhub_env \
  --env.kwargs='{"config_path": "configs/envhub/example.yml"}' \
  --trust_remote_code=true \
  --env.state_keys=joint_pos \
  --env.action_dim=12 \
  --env.state_dim=16 \
  --env.camera_keys=left_hand_camera_rgb,right_hand_camera_rgb,first_person_camera_rgb \
  --env.enable_cameras=true \
  --env.headless=true \
  --env.video=true \
  --env.video_length=200 \
  --env.video_interval=1 \
  --policy.device=cuda \
  --eval.batch_size=1 \
  --eval.n_episodes=10 \
  --output_dir=/mnt/robot/eval_outputs_pathB_1

echo "EXIT_CODE: $?"
echo "FINISHED: $(date -Iseconds)"
