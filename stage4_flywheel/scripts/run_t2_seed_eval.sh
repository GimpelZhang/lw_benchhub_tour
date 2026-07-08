#!/usr/bin/env bash
# T2 seed-based variant: SmolVLA eval on the T3 seed-based curriculum
# (scene_{easy,medium,hard}.yml — preserves each seed's full bowl+plate placement,
# unlike the bowl-only fix_object_pose_cfg curriculum). For a cleaner gradient if
# the bowl-only T2 gradient is inverted.
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
unset CUDA_VISIBLE_DEVICES
python -c "import numpy; assert numpy.__version__=='1.26.0'"
cd /mnt/robot/lw_benchhub || exit 1
mkdir -p /mnt/robot/stage4_flywheel/{metrics/seed_curriculum,logs/seed_curriculum}
REN='{"observation.images.left_hand_camera_rgb":"observation.images.left_hand","observation.images.right_hand_camera_rgb":"observation.images.right_hand","observation.images.first_person_camera_rgb":"observation.images.first_person"}'
for SCENE in scene_easy scene_medium scene_hard; do
  echo "=== seed-curriculum ${SCENE} ==="
  lerobot-eval \
    --policy.path=LightwheelAI/smolvla-double-piper-pnp \
    --env.type=isaaclab_arena --env.hub_path=LightwheelAI/lw_benchhub_env \
    --rename_map="${REN}" --trust_remote_code=true \
    --env.state_keys=joint_pos --env.state_dim=16 --env.action_dim=12 \
    --env.camera_keys=left_hand_camera_rgb,right_hand_camera_rgb,first_person_camera_rgb \
    --env.enable_cameras=true --env.headless=true --env.video=true \
    --env.video_length=1100 --env.video_interval=1 \
    --env.kwargs="{\"config_path\":\"configs/envhub/generated_stage4/${SCENE}.yml\"}" \
    --policy.device=cuda --eval.batch_size=1 --eval.n_episodes=10 \
    --output_dir=/mnt/robot/stage4_flywheel/metrics/seed_curriculum/${SCENE} \
    > /mnt/robot/stage4_flywheel/logs/seed_curriculum/${SCENE}.log 2>&1
  echo "EXIT_CODE: $?" >> /mnt/robot/stage4_flywheel/logs/seed_curriculum/${SCENE}.log
  python -c "import numpy; assert numpy.__version__=='1.26.0'"
done
echo "T2_SEED_CURRICULUM_DONE"
