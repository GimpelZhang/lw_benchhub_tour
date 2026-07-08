#!/usr/bin/env bash
# T3 prep: validate cuRobo config load (URDF + IK solver) + verify sim joint/body/sensor names (§14).
# Run AFTER T2 (frees GPU). No pipeline run yet — that's interactive after reviewing these results.
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
source /mnt/robot/lerobot_arena_curobo_env.sh
source /mnt/robot/deepseek_v4pro_env.sh
unset CUDA_VISIBLE_DEVICES
python -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__"

echo "===== T3 PREP 1: cuRobo config load test (no env boot) ====="
python /mnt/robot/stage4_flywheel/scripts/test_curobo_config.py 2>&1 | tail -30
echo "CUROBO_CONFIG_TEST_EXIT=$?"

echo ""
echo "===== T3 PREP 2: §14 sim joint/body/sensor name verification (env boot) ====="
DP_VERIFY_YML=/mnt/robot/stage4_flywheel/curriculum/scene_easy.yml \
  python /mnt/robot/stage4_flywheel/scripts/verify_doublepiper_joints.py 2>&1 | tail -30
echo "VERIFY_JOINTS_EXIT=$?"

echo ""
echo "===== T3 PREP DONE ====="
cat /mnt/robot/stage4_flywheel/metrics/doublepiper_joints.json 2>/dev/null
