#!/bin/bash
# Fallback diagnostic: run the ACTUAL lerobot-eval on scene_hard.yml for N episodes,
# to compare success rate against generate_policy_demos.py. Use ONLY if Phase 1 collection v3
# does NOT reproduce T2's 40% (i.e., ep 1 seed 1001 fails in my script but should succeed per T2).
#
# This is the GROUND TRUTH (lerobot-eval = T2's exact tool). If this gets ~40% but my script gets 0%,
# my script has a bug. If this also gets 0%, the config/placement is the issue.
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
unset CUDA_VISIBLE_DEVICES
python -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__" || exit 2
cd /mnt/robot/lw_benchhub || exit 3

N="${N_EPISODES:-3}"
SEED="${SEED:-1000}"
OUT="/mnt/robot/stage4_flywheel/metrics/lerobot_eval_compare_s${SEED}_n${N}"
mkdir -p "$OUT"

echo "=== lerobot-eval ground truth: scene_hard.yml, n=$N, start_seed=$SEED ==="
lerobot-eval \
  --policy.path=LightwheelAI/smolvla-double-piper-pnp \
  --env.type=isaaclab_arena \
  --env.hub_path=LightwheelAI/lw_benchhub_env \
  --env.kwargs='{"config_path": "configs/envhub/generated_stage4/scene_hard.yml"}' \
  --rename_map='{"observation.images.left_hand_camera_rgb": "observation.images.left_hand", "observation.images.right_hand_camera_rgb": "observation.images.right_hand", "observation.images.first_person_camera_rgb": "observation.images.first_person"}' \
  --trust_remote_code=true \
  --env.state_keys=joint_pos --env.state_dim=16 --env.action_dim=12 \
  --env.camera_keys=left_hand_camera_rgb,right_hand_camera_rgb,first_person_camera_rgb \
  --env.enable_cameras=true --env.headless=true --env.video=false \
  --policy.device=cuda --eval.batch_size=1 --eval.n_episodes="$N" \
  --seed="$SEED" --output_dir="$OUT"
echo "EXIT_CODE=$?"
echo "=== success rate ==="
grep -oE "running_success_rate=[0-9.]+%" /mnt/robot/stage4_flywheel/logs/policy_demos/lerobot_eval_compare.log 2>/dev/null | tail -1
