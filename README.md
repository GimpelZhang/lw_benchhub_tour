# lw_benchhub_tour

End-to-end VLA (Vision-Language-Action) closed-loop simulation pipeline built on
**光轮科技 LW-BenchHub + NVIDIA IsaacLab-Arena + HuggingFace lerobot**.

This monorepo aggregates the full project: SmolVLA dual-arm (DoublePiper)
closed-loop simulation, LLM-driven scene generation with cuRobo reachability
gating, and a SmolVLA self-filtering demonstration-data flywheel.

> **Status** — Stage 1 ✅ (40% closed-loop success), Stage 2 v6 ✅ (live cuRobo
> reach gate + SmolVLA closed loop), Stage 4 ✅ (10-episode fine-tuneable
> LeRobotDataset via SmolVLA self-filtering). Stage 3 (3DGS scene reconstruction)
> is planned, see `docs/Stage3_Plan.md`.

---

## Repository layout

```
lw_benchhub_tour/
├── docs/                     # consolidated markdown (LOCAL ONLY - gitignored, not committed)
├── lw_benchhub/              # Lightwheel BenchHub (patched for IsaacLab v2.3.x) [absorbed]
├── IsaacLab/                 # Isaac Lab v2.3.2 source [absorbed, was git submodule]
├── IsaacLab-Arena/           # IsaacLab-Arena release/0.1.1 [absorbed]
├── lerobot/                  # HuggingFace lerobot 0.5.1 (+ Stage4 diagnostics) [absorbed]
├── AutoDataGen/              # LightwheelAI AutoDataGen (+ cuRobo/IsaacLab deps) [absorbed]
├── stage4_flywheel/          # Stage 4 data-flywheel scripts, configs, curriculum
├── *.sh / *.py               # top-level Stage 1/2 entry scripts + env shims
├── piper_curobo.yml          # Piper single-arm cuRobo kinematics config
├── *.env.sh.example          # env-shim templates (real *.env.sh are gitignored secrets)
└── .gitignore
```

The five subproject directories (`IsaacLab`, `IsaacLab-Arena`, `lerobot`,
`AutoDataGen`, `lw_benchhub`) were originally independent git repositories with
local commits carrying Stage 1/2/4 patches. They have been **absorbed as plain
subdirectories** (their `.git` directories were backed up to `_git_backups/`
before removal, kept on disk only — gitignored). This preserves both committed
and uncommitted local modifications, and keeps the directory layout identical so
all absolute paths in the code (`/mnt/robot/...`) and configs continue to
resolve when the repo is checked out at `/mnt/robot`.

## Documentation

The project's detailed documentation lives in `docs/` **on disk only** (it is
gitignored per the repo spec - not committed). Authoritative reproduction guides:

| Doc (in `docs/`) | Covers |
|---|---|
| `Complete_Stage_1.md` | Stage 1: SmolVLA DoublePiper closed-loop (9 pitfalls, golden path) |
| `Complete_Stage_2.md` | Stage 2 v6: LLM scene gen + live cuRobo reach gate + SmolVLA closed loop |
| `Complete_Stage_4.md` | Stage 4: SmolVLA closed-loop self-filtering demo-data flywheel (Phase 1, 5 pitfalls) |
| `CLAUDE.md` | Project handoff doc (component versions, patched source, troubleshooting) |

Other `docs/*.md` are historical plans (`Stage*_Plan*.md`), patch records
(`Stage1_Patch.md`, `Stage4_Patch_01*.md`), and investigation reports.

## Quick start

### Environment (one-time)

```bash
conda activate lerobot-arena          # Python 3.11, the ONLY working env
cp headless_env.sh.example headless_env.sh   # fill in HF_TOKEN, chmod 600
cp llm_env.sh.example llm_env.sh             # fill in DeepSeek key (Stage 2)
cp deepseek_v4pro_env.sh.example deepseek_v4pro_env.sh  # (Stage 4)
source headless_env.sh
unset CUDA_VISIBLE_DEVICES             # else Isaac Sim camera render segfaults
python -c "import numpy; assert numpy.__version__=='1.26.0'"   # MUST be 1.26.0
```

See `docs/CLAUDE.md` §9 for a full healthcheck.

### Stage 1 (closed-loop baseline)

```bash
cd /mnt/robot/lw_benchhub              # config_path is relative to this cwd
bash /mnt/robot/pathB_logs/run_pathB.sh
```
Expected: ~40% success on `L90K1PutTheBlackBowlOnThePlate`. Full guide:
`docs/Complete_Stage_1.md`.

### Stage 2 (LLM scene gen + reach gate + closed loop)

```bash
source /mnt/robot/lerobot_arena_curobo_env.sh
source /mnt/robot/llm_env.sh
python /mnt/robot/generate_scenes_with_live_reach.py   # LLM gen + live IK gate
N_EPISODES=3 bash /mnt/robot/stage2_logs/run_stage2_all.sh
python /mnt/robot/verify_stage2.py
```
Full guide: `docs/Complete_Stage_2.md`.

### Stage 4 (demo-data flywheel)

```bash
N_EPISODES=30 bash /mnt/robot/stage4_flywheel/scripts/run_policy_demo_collection.sh
python /mnt/robot/stage4_flywheel/scripts/evaluate_phase1_gates.py
python /mnt/robot/stage4_flywheel/scripts/build_policy_demos_dataset.py
bash /mnt/robot/stage4_flywheel/scripts/verify_stage4.sh
```
Delivers a 10-episode / 6527-frame fine-tuneable LeRobotDataset. Full guide
(5 documented pitfalls): `docs/Complete_Stage_4.md` §12.

## Important notes

- **`docs/` is gitignored** (kept on disk only, not committed) per the repo spec;
  it holds the markdown reference material.
- **Secrets**: `headless_env.sh`, `llm_env.sh`, `deepseek_v4pro_env.sh` contain
  real API tokens and are **gitignored**. Use the `.example` templates. No API
  keys are committed anywhere in this repo.
- **Superseded code** lives in `_legacy/` (gitignored, on-disk only). See
  `_legacy/README.md` for the canonical replacement of each archived file.
- **numpy MUST stay at 1.26.0** (Isaac Sim 5.1 C-extension hard-binding).
  Re-lock after any `pip install`: `pip install --no-deps numpy==1.26.0`.
- The original nested-repo `.git` history is backed up under `_git_backups/`
  (gitignored, on-disk only) for reversibility.

## License / attribution

Component repos retain their upstream licenses (IsaacLab, IsaacLab-Arena,
lerobot, AutoDataGen, lw_benchhub, cuRobo). Project-specific patches and the
Stage 4 flywheel tooling are under this repo's own terms unless the upstream
file states otherwise.
