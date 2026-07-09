#!/bin/bash
# Phase 1 collection v2: run N_EPISODES SmolVLA closed-loop demos in ONE process.
# (One-process is required to match lerobot-eval's sequential RNG state — resample_objects_placement_on_reset
#  uses env RNG that accumulates across episodes; one-episode-per-process gives different placements.)
#
# Env vars: N_EPISODES (default 30), START_EPISODE_ID (0), TARGET_SUCCESSES (10), BAND (original),
#           MAX_STEPS (1000), SEED (1000, start seed; incremented per episode).
# Phase 1 does NOT source lerobot_arena_curobo_env.sh (SmolVLA, no cuRobo).
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
unset CUDA_VISIBLE_DEVICES

python -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__" || { echo "NUMPY LOCK BROKEN"; exit 2; }

N_EPISODES="${N_EPISODES:-30}"
START_EPISODE_ID="${START_EPISODE_ID:-0}"
TARGET_SUCCESSES="${TARGET_SUCCESSES:-10}"
BAND="${BAND:-original}"
MAX_STEPS="${MAX_STEPS:-1000}"
SEED="${SEED:-1000}"
OUTPUT_DIR="${OUTPUT_DIR:-/mnt/robot/stage4_flywheel/datasets/policy_demos_v3/raw}"
export N_EPISODES START_EPISODE_ID TARGET_SUCCESSES BAND MAX_STEPS

cd /mnt/robot/lw_benchhub || { echo "cd lw_benchhub failed"; exit 3; }
ls configs/envhub/generated_stage4/scene_hard.yml >/dev/null || { echo "scene_hard.yml missing"; exit 4; }

echo "=== POLICY DEMO COLLECTION v2 (one process): n=${N_EPISODES} start_seed=${SEED} target=${TARGET_SUCCESSES} ==="
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
