#!/bin/bash
# Phase 1 Task 1.2 wrapper: run ONE SmolVLA closed-loop demo episode.
# Env vars (set by caller): EPISODE_ID, SEED, BAND, MAX_STEPS, OUTPUT_DIR.
# Phase 1 does NOT source lerobot_arena_curobo_env.sh (SmolVLA, no cuRobo).
set +u   # not set -u: keep consistent with v6 runners; cuda-nvcc activate refs unbound vars
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
unset CUDA_VISIBLE_DEVICES

# numpy lock guard (must stay 1.26.0)
python -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__" || { echo "NUMPY LOCK BROKEN"; exit 2; }

EPISODE_ID="${EPISODE_ID:-0}"
SEED="${SEED:-48}"
BAND="${BAND:-original}"
MAX_STEPS="${MAX_STEPS:-1000}"
OUTPUT_DIR="${OUTPUT_DIR:-/mnt/robot/stage4_flywheel/datasets/policy_demos_v3/raw}"
export EPISODE_ID BAND MAX_STEPS

# config_path is relative — must run from lw_benchhub. scene_hard.yml = exact T2 config (scene seed 48, gave 40%).
cd /mnt/robot/lw_benchhub || { echo "cd lw_benchhub failed"; exit 3; }
ls configs/envhub/generated_stage4/scene_hard.yml >/dev/null || { echo "scene_hard.yml missing"; exit 4; }

echo "=== POLICY DEMO EPISODE: ep=${EPISODE_ID} seed=${SEED} band=${BAND} max_steps=${MAX_STEPS} ==="
echo "PWD: $(pwd)  OUTPUT_DIR: ${OUTPUT_DIR}"

python /mnt/robot/stage4_flywheel/scripts/generate_policy_demos.py \
  --policy.path=LightwheelAI/smolvla-double-piper-pnp \
  --env.type=isaaclab_arena \
  --env.hub_path=LightwheelAI/lw_benchhub_env \
  --env.kwargs='{"config_path": "configs/envhub/generated_stage4/scene_hard.yml"}' \
  --rename_map='{"observation.images.left_hand_camera_rgb": "observation.images.left_hand", "observation.images.right_hand_camera_rgb": "observation.images.right_hand", "observation.images.first_person_camera_rgb": "observation.images.first_person"}' \
  --trust_remote_code=true \
  --env.state_keys=joint_pos \
  --env.action_dim=12 \
  --env.state_dim=16 \
  --env.camera_keys=left_hand_camera_rgb,right_hand_camera_rgb,first_person_camera_rgb \
  --env.enable_cameras=true \
  --env.headless=true \
  --env.video=false \
  --policy.device=cuda \
  --eval.batch_size=1 \
  --eval.n_episodes=1 \
  --seed="${SEED}" \
  --output_dir="${OUTPUT_DIR}"
echo "EXIT_CODE=$?"
