#!/bin/bash
# Fill missing episodes: for each band with <3 successful episodes, try ADDITIONAL
# reachable seeds (not in the main generate_dataset.sh list) until 3 are reached.
# Resumable (skips already-successful). Uses the hang-killer + os._exit runner.
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena

RAW_ROOT=/mnt/robot/stage4_flywheel/datasets/raw
LOG_DIR=/mnt/robot/stage4_flywheel/logs
TARGET=3
TIMEOUT_S=900
HANG_THRESHOLD=4

# Additional reachable seeds per band (excluding the 6 main-list seeds).
# Medium includes 51,27,10,30 re-tries (decomposer-crashed before cache fix; now cache-enabled).
# easy (0.260-0.287): 45,53,61,1,3,11,25,19 ; medium (0.287-0.325): 51,27,10,30,8,22,62,24,58,17 ; hard (0.326-0.385): 2,0,56,40,18,34,46,37
FALLBACKS=(
  "easy|45" "easy|53" "easy|61" "easy|1" "easy|3" "easy|11" "easy|25" "easy|19"
  "medium|51" "medium|27" "medium|10" "medium|30" "medium|8" "medium|22" "medium|62" "medium|24" "medium|58" "medium|17"
  "hard|2" "hard|0" "hard|56" "hard|40" "hard|18" "hard|34" "hard|46" "hard|37"
)

count_success() {
  python3 -c "
import json,glob
ss=glob.glob('$RAW_ROOT/$1/episode_*_summary.json')
print(sum(1 for s in ss if json.load(open(s)).get('success') and json.load(open(s)).get('n_frames',0)>0))
" 2>/dev/null
}

seed_has_success() {
  python3 -c "
import json,glob,sys
sd=int('$2')
for s in glob.glob('$RAW_ROOT/$1/episode_*_summary.json'):
    d=json.load(open(s))
    if d.get('success') and d.get('n_frames',0)>0 and d.get('seed')==sd:
        sys.exit(0)
sys.exit(1)
" 2>/dev/null
}

is_success() {
  [ -f "$1" ] && python3 -c "import json,sys; d=json.load(open('$1')); sys.exit(0 if (d.get('success') and d.get('n_frames',0)>0) else 1)" 2>/dev/null
}

run_episode_with_hangkill() {
  local seed=$1 diff=$2 epid=$3 log=$4
  timeout -k 10 "$TIMEOUT_S" bash /mnt/robot/stage4_flywheel/scripts/run_one_episode.sh "$seed" "$diff" "$epid" > "$log" 2>&1 &
  local ep_pid=$!
  (
    while kill -0 "$ep_pid" 2>/dev/null; do
      sr=$(grep -c "scene retry" "$log" 2>/dev/null)
      if [ "${sr:-0}" -gt "$HANG_THRESHOLD" ]; then
        echo "  -> hang detected (scene retry=$sr); killing seed=$seed"
        pkill -9 -f "[r]un_dataset_gen" 2>/dev/null
        pkill -9 -f "[k]it/python" 2>/dev/null
        break
      fi
      sleep 8
    done
  ) &
  local killer_pid=$!
  wait "$ep_pid" 2>/dev/null
  kill "$killer_pid" 2>/dev/null
  return 0
}

for fb in "${FALLBACKS[@]}"; do
  IFS='|' read -r DIFF SEED <<< "$fb"
  cur=$(count_success "$DIFF")
  if [ "$cur" -ge "$TARGET" ]; then
    continue
  fi
  if seed_has_success "$DIFF" "$SEED"; then
    continue
  fi
  EPID=$(python3 -c "
import json,glob
ids=[int(s.split('/')[-1].split('_')[1].split('_')[0]) for s in glob.glob('$RAW_ROOT/$DIFF/episode_*_summary.json')]
print(max(ids)+1 if ids else 0)
" 2>/dev/null)
  LOG="$LOG_DIR/dataset_gen_${DIFF}_s${SEED}_ep${EPID}.log"
  echo "[FILL] $DIFF seed=$SEED ep=$EPID (have $cur/$TARGET)"
  rm -f "$RAW_ROOT/$DIFF/episode_${EPID}.h5" "$RAW_ROOT/$DIFF/episode_${EPID}_summary.json"
  run_episode_with_hangkill "$SEED" "$DIFF" "$EPID" "$LOG"
  if is_success "$RAW_ROOT/$DIFF/episode_${EPID}_summary.json"; then
    echo "  -> SUCCESS"
  else
    echo "  -> failed; tail:"
    tail -3 "$LOG" 2>/dev/null | sed 's/^/     /'
  fi
  pkill -9 -f "[k]it/python" 2>/dev/null
  pkill -9 -f "[i]saacsim" 2>/dev/null
  pkill -9 -f "[r]un_dataset_gen" 2>/dev/null
  sleep 3
done

echo "=== FILL DONE ==="
for d in easy medium hard; do
  echo "  $d: $(count_success $d)/$TARGET successful"
done
