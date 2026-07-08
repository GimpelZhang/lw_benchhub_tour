#!/bin/bash
# Run all 9 dataset-gen episodes (3 easy + 3 medium + 3 hard, interleaved for
# even distribution at every checkpoint). Resumable: skips episodes whose HDF5
# already exists and whose summary marks success. Process-level retry as a
# backstop (the pipeline also does plan-level retry internally).
set +u
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena

EPISODES=(
  # difficulty:seed:episode_id  (interleaved: 1-of-each, then 2-of-each, then 3-of-each)
  "hard:48:0"
  "easy:15:0"
  "medium:1:0"
  "hard:47:1"
  "easy:13:1"
  "medium:8:1"
  "hard:2:2"
  "easy:16:2"
  "medium:17:2"
)
MAX_ATTEMPTS=2

RAW_ROOT=/mnt/robot/stage4_flywheel/datasets/raw
LOG_DIR=/mnt/robot/stage4_flywheel/logs
mkdir -p "$LOG_DIR"

is_success() {
  local sum="$1"
  [ -f "$sum" ] || return 1
  python3 -c "import json,sys; d=json.load(open('$sum')); sys.exit(0 if (d.get('success') and d.get('n_frames',0)>0) else 1)" 2>/dev/null
}

for ep in "${EPISODES[@]}"; do
  IFS=':' read -r DIFF SEED EPID <<< "$ep"
  H5="$RAW_ROOT/$DIFF/episode_$EPID.h5"
  SUM="$RAW_ROOT/$DIFF/episode_$EPID_summary.json"
  LOG="$LOG_DIR/dataset_gen_${DIFF}_s${SEED}_ep${EPID}.log"

  if is_success "$SUM"; then
    NF=$(python3 -c "import json;print(json.load(open('$SUM')).get('n_frames'))" 2>/dev/null)
    echo "[SKIP] $DIFF seed=$SEED ep=$EPID already successful (n_frames=$NF)"
    continue
  fi

  success=0
  for attempt in $(seq 1 $MAX_ATTEMPTS); do
    echo "[RUN]  $DIFF seed=$SEED ep=$EPID attempt=$attempt/$MAX_ATTEMPTS"
    # Remove stale partial outputs before each attempt.
    rm -f "$H5" "$SUM"
    bash /mnt/robot/stage4_flywheel/scripts/run_one_episode.sh "$SEED" "$DIFF" "$EPID" > "$LOG" 2>&1
    if is_success "$SUM"; then
      success=1
      MARK=$(grep "DATASET_GEN_DONE" "$LOG" | tail -1)
      echo "  -> SUCCESS: $MARK"
      break
    fi
    echo "  -> attempt $attempt failed; tail:"
    tail -3 "$LOG" 2>/dev/null | sed 's/^/     /'
    pkill -9 -f "isaacsim\|kit/python" 2>/dev/null || true
    sleep 3
  done

  if [ $success -eq 0 ]; then
    echo "  xxx $DIFF seed=$SEED ep=$EPID FAILED all $MAX_ATTEMPTS attempts"
  fi
done

echo "=== ALL EPISODES ATTEMPTED ==="
echo "=== per-episode summary ==="
for ep in "${EPISODES[@]}"; do
  IFS=':' read -r DIFF SEED EPID <<< "$ep"
  SUM="$RAW_ROOT/$DIFF/episode_$EPID_summary.json"
  if [ -f "$SUM" ]; then
    python3 -c "import json; d=json.load(open('$SUM')); print(f\"  {d['difficulty']:6s} seed={d['seed']:>3} ep={d['episode_id']} n_frames={d['n_frames']:>4} success={d['success']}\")" 2>/dev/null || echo "  $DIFF seed=$SEED ep=$EPID (summary unreadable)"
  else
    echo "  $DIFF seed=$SEED ep=$EPID (no summary)"
  fi
done
echo "=== distribution ==="
for d in easy medium hard; do
  n=$(python3 -c "
import json,glob
ss=glob.glob('$RAW_ROOT/$d/episode_*_summary.json')
print(sum(1 for s in ss if json.load(open(s)).get('success') and json.load(open(s)).get('n_frames',0)>0))
" 2>/dev/null)
  echo "  $d: $n successful"
done
