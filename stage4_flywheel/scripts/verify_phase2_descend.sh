#!/bin/bash
# Phase 2 (Stage4_Patch_01 §4.3 方案二) - verify the collision-spheres + activation_distance patch.
#
# NOTE on scope: the original Phase 2 plan included 方案一 (Cartesian descend skill) + 方案二
# (collision spheres). Investigation on seed 48 showed (a) the +0.109m bowl-push does NOT occur
# on seed 48 (bowl stays at [2.288,-2.085,0.792] through the whole pre-patch episode), so 方案一's
# descend solves a non-problem here, and (b) the descend's multiple sequential cuRobo plan_batch
# calls crash the subsequent lift skill (MotionGen copy_idx shape mismatch). So 方案一 was dropped
# and only 方案二 (gripper collision_spheres + collision_activation_distance=0.07) is kept.
#
# This script verifies 方案二: the full 6-skill PnP chain runs without crashing and the sphere
# collision model loads. TASK_SUCCESS is expected False on seed 48 (grasp closes on empty space -
# a separate failure mode unrelated to bowl-pushing; see memory stage4-phase2-descend-investigation).
#
# Usage: bash verify_phase2_descend.sh [log_path]
#   default log: /mnt/robot/stage4_flywheel/logs/phase2/dataset_gen_hard_s48_ep0_final.log
set +u
LOG="${1:-/mnt/robot/stage4_flywheel/logs/phase2/dataset_gen_hard_s48_ep0_final.log}"

if [ ! -f "$LOG" ]; then
  echo "FAIL: log not found: $LOG"
  exit 2
fi

echo "=== Phase 2 方案二 verification (collision spheres + activation_distance) ==="
echo "log: $LOG"
echo ""

echo "--- [1] full 6-skill chain executed (no crash) ---"
LIFT=$(grep -c "Skill lift executed successfully" "$LOG")
REACH=$(grep -c "Skill reach executed successfully" "$LOG")
GRASP=$(grep -c "Skill grasp executed successfully" "$LOG")
echo "  reach: $REACH, grasp: $GRASP, lift: $LIFT"
if [ "$LIFT" -ge 1 ] && [ "$GRASP" -ge 1 ]; then
  echo "  PASS: skill chain ran through lift (no cuRobo plan_batch crash)"
else
  echo "  FAIL: skill chain did not complete"
fi

echo ""
echo "--- [2] bowl not displaced by the approach ---"
grep -E "after (reach_hover|reach|grasp)|bowl-plate dist" "$LOG" || echo "  (no position markers found)"

echo ""
echo "--- [3] TASK_SUCCESS (expected False on seed 48: grasp closes on empty space) ---"
grep -E "TASK_SUCCESS" "$LOG" || echo "  (no TASK_SUCCESS marker)"

echo ""
echo "--- [4] errors / aborts ---"
grep -E "Traceback|RuntimeError|shape mismatch|pipeline.run\(\) raised" "$LOG" || echo "  PASS: no errors (no cuRobo crash)"

echo ""
echo "=== summary file ==="
SUMMARY=$(ls /mnt/robot/stage4_flywheel/datasets/raw/hard/episode_0_summary.json 2>/dev/null)
if [ -f "$SUMMARY" ]; then
  grep -E '"success"|"error"|"n_frames"' "$SUMMARY"
else
  echo "  (no summary file - episode may not have completed)"
fi
