#!/bin/bash
set +u
N_EPISODES="${N_EPISODES:-3}"
LOG_ROOT="/mnt/robot/pathB_logs_v6"
SCENE_GLOB="/mnt/robot/lw_benchhub/configs/envhub/generated_v6/scene_variation_*.yml"
mkdir -p "$LOG_ROOT"
echo "Stage 2 v6 batch eval started: $(date -Iseconds)" | tee "$LOG_ROOT/run_stage2_v6_all.log"
echo "N_EPISODES=$N_EPISODES" | tee -a "$LOG_ROOT/run_stage2_v6_all.log"

idx=0
for full_path in $SCENE_GLOB; do
  idx=$((idx + 1))
  config_rel="configs/envhub/generated_v6/$(basename $full_path)"
  out_dir="/mnt/robot/eval_outputs_stage2_v6_scene${idx}"
  log_file="$LOG_ROOT/run_stage2_v6_scene${idx}.log"
  echo "===== Scene ${idx}: $config_rel -> $out_dir =====" | tee -a "$LOG_ROOT/run_stage2_v6_all.log"
  N_EPISODES="$N_EPISODES" bash "$LOG_ROOT/run_stage2_v6_scene.sh" "$config_rel" "$out_dir" \
    > "$log_file" 2>&1
  rc=$?
  echo "Scene ${idx} exit=$rc  (log: $log_file)" | tee -a "$LOG_ROOT/run_stage2_v6_all.log"
done
echo "Stage 2 v6 batch eval finished: $(date -Iseconds)" | tee -a "$LOG_ROOT/run_stage2_v6_all.log"
