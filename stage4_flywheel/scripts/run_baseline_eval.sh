#!/usr/bin/env bash
# Phase 1-2 §5.3-5.4: write hard_scene.yml from best_seed, run SmolVLA baseline eval.
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
unset CUDA_VISIBLE_DEVICES
python -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__"

PROBE=/mnt/robot/stage4_flywheel/metrics/baseline/seed_probe.json
HARD_SEED=$(python3 -c "import json;print(json.load(open('$PROBE'))['best_seed'])")
echo "best_seed=${HARD_SEED}"
sed "s/^seed:.*/seed: ${HARD_SEED}/" /mnt/robot/lw_benchhub/configs/envhub/example.yml > /mnt/robot/stage4_flywheel/configs/hard_scene.yml
mkdir -p /mnt/robot/lw_benchhub/configs/envhub/generated_stage4
cp /mnt/robot/stage4_flywheel/configs/hard_scene.yml /mnt/robot/lw_benchhub/configs/envhub/generated_stage4/hard_scene.yml
echo "wrote hard_scene.yml (seed=${HARD_SEED}) + copy to generated_stage4/"
grep '^seed:' /mnt/robot/stage4_flywheel/configs/hard_scene.yml

cd /mnt/robot/lw_benchhub || exit 1
LOG=/mnt/robot/stage4_flywheel/metrics/baseline/hard_scene_eval.log
OUT=/mnt/robot/stage4_flywheel/metrics/baseline/hard_scene_run
REN='{"observation.images.left_hand_camera_rgb":"observation.images.left_hand","observation.images.right_hand_camera_rgb":"observation.images.right_hand","observation.images.first_person_camera_rgb":"observation.images.first_person"}'
lerobot-eval \
  --policy.path=LightwheelAI/smolvla-double-piper-pnp \
  --env.type=isaaclab_arena \
  --env.hub_path=LightwheelAI/lw_benchhub_env \
  --rename_map="${REN}" \
  --trust_remote_code=true \
  --env.state_keys=joint_pos --env.state_dim=16 --env.action_dim=12 \
  --env.camera_keys=left_hand_camera_rgb,right_hand_camera_rgb,first_person_camera_rgb \
  --env.enable_cameras=true --env.headless=true --env.video=true \
  --env.video_length=1100 --env.video_interval=1 \
  --env.kwargs='{"config_path": "configs/envhub/generated_stage4/hard_scene.yml"}' \
  --policy.device=cuda --eval.batch_size=1 --eval.n_episodes=5 \
  --output_dir=${OUT} 2>&1 | tee ${LOG}
echo "EXIT_CODE: ${PIPESTATUS[0]}" >> ${LOG}
echo "BASELINE_EVAL_DONE exit=${PIPESTATUS[0]}"
