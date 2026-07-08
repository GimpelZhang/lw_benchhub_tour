#!/bin/bash
# Sequentially evaluate all generated scenes (serial to avoid VRAM contention)
set -u
N_EPISODES="${N_EPISODES:-3}"
LOG_ROOT="/mnt/robot/pathB_logs"
SCENE_GLOB="/mnt/robot/lw_benchhub/configs/envhub/generated/scene_variation_*.yml"

mkdir -p "$LOG_ROOT"
echo "Stage 2 batch eval started: $(date -Iseconds)" | tee "$LOG_ROOT/run_stage2_all.log"
echo "N_EPISODES=$N_EPISODES" | tee -a "$LOG_ROOT/run_stage2_all.log"

idx=0
for full_path in $SCENE_GLOB; do
  idx=$((idx + 1))
  config_rel="configs/envhub/generated/$(basename $full_path)"
  out_dir="/mnt/robot/eval_outputs_stage2_scene${idx}"
  log_file="$LOG_ROOT/run_stage2_scene${idx}.log"

  echo "===== Scene ${idx}: $config_rel -> $out_dir =====" | tee -a "$LOG_ROOT/run_stage2_all.log"
  N_EPISODES="$N_EPISODES" bash "$LOG_ROOT/run_stage2_scene.sh" "$config_rel" "$out_dir" \
    > "$log_file" 2>&1
  rc=$?
  echo "Scene ${idx} exit=$rc  (log: $log_file)" | tee -a "$LOG_ROOT/run_stage2_all.log"
done

echo "Stage 2 batch eval finished: $(date -Iseconds)" | tee -a "$LOG_ROOT/run_stage2_all.log"
