#!/usr/bin/env bash
# Phase 4 T2 §7.5: extract head-view mp4 + frame0 PNG for hard/easy/medium from T2 eval outputs,
# then build a 3-way comparison grid (curriculum_grid.mp4).
set +u
OUT_DIR=/mnt/robot/stage4_flywheel/videos
mkdir -p "$OUT_DIR"

declare -A SCENES=(
  [hard_scene]=/mnt/robot/stage4_flywheel/metrics/hard_scene
  [medium_curriculum]=/mnt/robot/stage4_flywheel/metrics/medium_curriculum
  [easy_curriculum]=/mnt/robot/stage4_flywheel/metrics/easy_curriculum
)

for SCENE in "${!SCENES[@]}"; do
  EVAL_DIR="${SCENES[$SCENE]}"
  VID=$(find "$EVAL_DIR/videos" -name "eval_episode_0.mp4" 2>/dev/null | head -1)
  if [ -z "$VID" ]; then
    echo "WARN: no eval_episode_0.mp4 for ${SCENE} under ${EVAL_DIR}/videos" >&2
    continue
  fi
  cp "$VID" "${OUT_DIR}/${SCENE}_head_view.mp4"
  ffmpeg -y -ss 00:00:00.10 -i "$VID" -frames:v 1 -q:v 2 "${OUT_DIR}/${SCENE}_frame0.png" >/dev/null 2>&1
  echo "extracted ${SCENE}"
done

# Build 3-way grid: hard | medium | easy. Labels whitelisted (^[A-Za-z0-9 ]+$).
H=${OUT_DIR}/hard_scene_head_view.mp4
M=${OUT_DIR}/medium_curriculum_head_view.mp4
E=${OUT_DIR}/easy_curriculum_head_view.mp4
if [ -f "$H" ] && [ -f "$M" ] && [ -f "$E" ]; then
  ffmpeg -y \
    -i "$H" -i "$M" -i "$E" \
    -filter_complex "[0:v]drawtext=text='Hard scene':x=10:y=10:fontsize=24:fontcolor=white[v0]; \
                     [1:v]drawtext=text='Medium curriculum':x=10:y=10:fontsize=24:fontcolor=white[v1]; \
                     [2:v]drawtext=text='Easy curriculum':x=10:y=10:fontsize=24:fontcolor=white[v2]; \
                     [v0][v1][v2]hstack=inputs=3" \
    -shortest "${OUT_DIR}/curriculum_grid.mp4" >/dev/null 2>&1
  echo "built curriculum_grid.mp4"
  ls -lh "${OUT_DIR}/curriculum_grid.mp4"
else
  echo "WARN: missing one or more head-view mp4s; skipping grid"
fi
echo "T2_HEADVIEW_GRID_DONE"
