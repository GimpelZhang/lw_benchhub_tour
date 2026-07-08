#!/usr/bin/env bash
set +u   # conda cuda-nvcc references unbound NVCC_PREPEND_FLAGS
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
unset CUDA_VISIBLE_DEVICES
python -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__"
cd /mnt/robot/lw_benchhub || exit 1
mkdir -p /mnt/robot/stage4_flywheel/{metrics,logs,videos}
REN='{"observation.images.left_hand_camera_rgb":"observation.images.left_hand","observation.images.right_hand_camera_rgb":"observation.images.right_hand","observation.images.first_person_camera_rgb":"observation.images.first_person"}'
for SCENE in hard_scene easy_curriculum medium_curriculum; do
  echo "=== ${SCENE} ==="
  lerobot-eval \
    --policy.path=LightwheelAI/smolvla-double-piper-pnp \
    --env.type=isaaclab_arena --env.hub_path=LightwheelAI/lw_benchhub_env \
    --rename_map="${REN}" \
    --trust_remote_code=true \
    --env.state_keys=joint_pos --env.state_dim=16 --env.action_dim=12 \
    --env.camera_keys=left_hand_camera_rgb,right_hand_camera_rgb,first_person_camera_rgb \
    --env.enable_cameras=true --env.headless=true --env.video=true \
    --env.video_length=1100 --env.video_interval=1 \
    --env.kwargs="{\"config_path\":\"configs/envhub/generated_stage4/${SCENE}.yml\"}" \
    --policy.device=cuda --eval.batch_size=1 --eval.n_episodes=10 \
    --output_dir=/mnt/robot/stage4_flywheel/metrics/${SCENE} \
    > /mnt/robot/stage4_flywheel/logs/${SCENE}.log 2>&1
  echo "EXIT_CODE: $?" >> /mnt/robot/stage4_flywheel/logs/${SCENE}.log
  python -c "import numpy; assert numpy.__version__=='1.26.0'"
done
