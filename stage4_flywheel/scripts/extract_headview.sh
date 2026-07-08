#!/usr/bin/env bash
# Extract first_person_camera head-view mp4 + frame0 PNG from a lerobot-eval output dir.
# Usage: extract_headview.sh <scene_name> <eval_output_dir>
# e.g. extract_headview.sh hard_scene /mnt/robot/stage4_flywheel/metrics/baseline/hard_scene_run
set -e
SCENE=$1
EVAL_DIR=$2
VID_DIR="${EVAL_DIR}/videos"
OUT_DIR=/mnt/robot/stage4_flywheel/videos
mkdir -p "$OUT_DIR"
VID=$(find "$VID_DIR" -name "eval_episode_0.mp4" 2>/dev/null | head -1)
if [ -z "$VID" ]; then
  echo "ERROR: no eval_episode_0.mp4 under ${VID_DIR}" >&2
  find "$VID_DIR" -name "*.mp4" 2>/dev/null | head -5
  exit 1
fi
cp "$VID" "${OUT_DIR}/${SCENE}_head_view.mp4"
ffmpeg -y -ss 00:00:00.10 -i "$VID" -frames:v 1 -q:v 2 "${OUT_DIR}/${SCENE}_frame0.png" >/dev/null 2>&1
echo "extracted ${SCENE}: ${OUT_DIR}/${SCENE}_head_view.mp4 + ${SCENE}_frame0.png"
ls -lh "${OUT_DIR}/${SCENE}_head_view.mp4" "${OUT_DIR}/${SCENE}_frame0.png"
