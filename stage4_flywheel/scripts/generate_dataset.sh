#!/bin/bash
# Generate the dataset with EVEN 3/3/3 distribution: for each band, try seeds in
# order (primary then fallback) until 3 successful episodes. Per-episode overall
# timeout (900s backstop) + fast hang-killer (kills placement-retry loops in
# ~2-4 min, detected by >HANG_THRESHOLD "scene retry" log lines — successful
# seeds have 0). Resumable (skips successful).
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena

RAW_ROOT=/mnt/robot/stage4_flywheel/datasets/raw
LOG_DIR=/mnt/robot/stage4_flywheel/logs
TARGET=3
TIMEOUT_S=900        # 15 min overall backstop (normal episode ~7 min)
HANG_THRESHOLD=4     # >4 "scene retry" lines = placement-retry hang (successful seeds have 0)

# Seeds per band — REDEFINED to the reachable range (>=0.260m; closer seeds hang/plan-fail).
# 3 tertiles of the reachable range: easy (0.260-0.287), medium (0.287-0.325), hard (0.326-0.385).
# seed 15/63/57/9 etc. (<0.255m) demoted out — too close for the arm to reach.
SEEDS_EASY="13 7 23 52 5 28"
SEEDS_MEDIUM="32 20 51 27 10 30"
SEEDS_HARD="41 39 12 4 36 48"

is_success() {
  [ -f "$1" ] && python3 -c "import json,sys; d=json.load(open('$1')); sys.exit(0 if (d.get('success') and d.get('n_frames',0)>0) else 1)" 2>/dev/null
}

count_success() {
  python3 -c "
import json,glob
ss=glob.glob('$RAW_ROOT/$1/episode_*_summary.json')
print(sum(1 for s in ss if json.load(open(s)).get('success') and json.load(open(s)).get('n_frames',0)>0))
" 2>/dev/null
}

seed_has_success() {
  # True (0) if any successful summary in $1 (diff) already used seed $2.
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

run_episode_with_hangkill() {
  local seed=$1 diff=$2 epid=$3 log=$4
  # Overall timeout backstop (SIGTERM at TIMEOUT_S, SIGKILL 10s later).
  timeout -k 10 "$TIMEOUT_S" bash /mnt/robot/stage4_flywheel/scripts/run_one_episode.sh "$seed" "$diff" "$epid" > "$log" 2>&1 &
  local ep_pid=$!
  # Hang-killer: monitor log for placement-retry loop; kill python if detected.
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

run_band() {
  local diff="$1"; shift
  local seeds=("$@")
  for seed in "${seeds[@]}"; do
    local n=$(count_success "$diff")
    if [ "$n" -ge "$TARGET" ]; then
      echo "[$diff] reached $n/$TARGET successful; done"
      return 0
    fi
    local epid=$n
    local log="$LOG_DIR/dataset_gen_${diff}_s${seed}_ep${epid}.log"
    # Skip seeds already used successfully in this band (avoid duplicate scenes).
    if seed_has_success "$diff" "$seed"; then
      continue
    fi
    if is_success "$RAW_ROOT/$diff/episode_${epid}_summary.json"; then
      continue
    fi
    echo "[$diff] RUN seed=$seed ep=$epid (have $n/$TARGET)"
    rm -f "$RAW_ROOT/$diff/episode_${epid}.h5" "$RAW_ROOT/$diff/episode_${epid}_summary.json"
    run_episode_with_hangkill "$seed" "$diff" "$epid" "$log"
    if is_success "$RAW_ROOT/$diff/episode_${epid}_summary.json"; then
      echo "  -> SUCCESS"
    else
      echo "  -> failed; tail:"
      tail -3 "$log" 2>/dev/null | sed 's/^/     /'
    fi
    pkill -9 -f "[k]it/python" 2>/dev/null
    pkill -9 -f "[i]saacsim" 2>/dev/null
    pkill -9 -f "[r]un_dataset_gen" 2>/dev/null
    sleep 3
  done
  n=$(count_success "$diff")
  echo "[$diff] exhausted seeds; final $n/$TARGET"
}

echo "=== EASY ==="; run_band easy $SEEDS_EASY
echo "=== MEDIUM ==="; run_band medium $SEEDS_MEDIUM
echo "=== HARD ==="; run_band hard $SEEDS_HARD

echo "=== GENERATION COMPLETE ==="
for d in easy medium hard; do
  echo "  $d: $(count_success $d)/$TARGET successful"
done
