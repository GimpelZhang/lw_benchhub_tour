#!/bin/bash
# Stage 2 single-scene runner. Usage:
#   run_stage2_scene.sh <config_rel_path> <output_dir>
#   $1 例如 configs/envhub/generated/scene_variation_1.yml
#   $2 例如 /mnt/robot/eval_outputs_stage2_scene1
# 环境变量 N_EPISODES 控制 episode 数（默认 3）
set -u
CONFIG_REL="$1"
OUTPUT_DIR="$2"
N_EPISODES="${N_EPISODES:-3}"

source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
unset CUDA_VISIBLE_DEVICES

# 清理残留（CLAUDE.md §8.5）
pkill -9 -f "isaacsim\|lerobot-eval\|kit/python" 2>/dev/null || true
sleep 2
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

cd /mnt/robot/lw_benchhub   # env.kwargs 用相对路径（CLAUDE.md §5）

echo "=== Stage 2 scene run ==="
echo "CONFIG: $CONFIG_REL"
echo "OUTPUT: $OUTPUT_DIR"
echo "N_EPISODES: $N_EPISODES"
echo "PWD: $(pwd)"
echo "NUMPY: $(python -c 'import numpy; print(numpy.__version__)')"
echo "GPU FREE: $(nvidia-smi --query-gpu=memory.free --format=csv,noheader)"
echo "STARTED: $(date -Iseconds)"
ls "$CONFIG_REL" && echo "CONFIG OK"
echo "========================="

lerobot-eval \
  --policy.path=LightwheelAI/smolvla-double-piper-pnp \
  --env.type=isaaclab_arena \
  --rename_map='{"observation.images.left_hand_camera_rgb": "observation.images.left_hand", "observation.images.right_hand_camera_rgb": "observation.images.right_hand", "observation.images.first_person_camera_rgb": "observation.images.first_person"}' \
  --env.hub_path=LightwheelAI/lw_benchhub_env \
  --env.kwargs="{\"config_path\": \"$CONFIG_REL\"}" \
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
  --eval.n_episodes="$N_EPISODES" \
  --output_dir="$OUTPUT_DIR"

EXIT=$?
echo "EXIT_CODE: $EXIT"
echo "FINISHED: $(date -Iseconds)"
exit $EXIT
