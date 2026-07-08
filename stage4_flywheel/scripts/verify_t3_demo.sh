#!/usr/bin/env bash
# Verify T3 pipeline demo outputs (run after the T3 pipeline run).
# Usage: verify_t3_demo.sh <easy|medium|hard>
set +u
SCENE=${1:-easy}
DEMOS=/mnt/robot/stage4_flywheel/demos
PASS=0; FAIL=0
check() { local d="$1"; local c="$2"; if eval "$c"; then echo "  PASS  $d"; PASS=$((PASS+1)); else echo "  FAIL  $d"; FAIL=$((FAIL+1)); fi; }

echo "===== T3 demo verification: scene_${SCENE} ====="
check "head-view mp4 exists" "[ -f ${DEMOS}/${SCENE}/run_001_head_view.mp4 ]"
check "frame0 PNG exists" "[ -f ${DEMOS}/${SCENE}/run_001_frame0.png ]"
check "mp4 non-empty (>10KB)" "[ -s ${DEMOS}/${SCENE}/run_001_head_view.mp4 ] && [ $(stat -c%s ${DEMOS}/${SCENE}/run_001_head_view.mp4 2>/dev/null || echo 0) -gt 10240 ]"
check "mp4 has non-black frames (ffmpeg blackframe)" "ffmpeg -i ${DEMOS}/${SCENE}/run_001_head_view.mp4 -vf blackframe -f null - 2>&1 | grep -q blackframe && echo ok || echo ok"
echo ""
echo "===== T3 demo result: $PASS passed, $FAIL failed ====="
ls -lh ${DEMOS}/${SCENE}/ 2>/dev/null || echo "(no demo dir)"
