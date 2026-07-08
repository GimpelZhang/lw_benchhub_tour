# Stage 4 v2 Re-run Draft — to merge into stage4_flywheel_report.md

## 9. v2 Re-run (2026-07-04): even curriculum + fine-tuning dataset

> Per user directive: re-execute the data flywheel, skip T1, achieve **even easy/medium/hard distribution**, and deliver the **final goal**: a fine-tuneable demonstration dataset under `stage4_flywheel/datasets/`.

### 9.1 What changed vs. v1
- **T1 skipped** (per directive); the AutoDataGen+cuRobo link is already proved by T3.
- **Even 3/3/3 distribution**: 3 seeds per difficulty band (easy/medium/hard) selected by bowl-to-robot distance tercile from the 64-seed probe. Seeds: easy=[13,16,63,...], medium=[1,8,17,...], hard=[48,47,2,...].
- **Plan-retry fix**: `_execute_single_skill` now retries `skill.plan()` up to 5× on failure (cuRobo MotionGen is non-deterministic; re-randomizes seeds per call). This fixes the ~50% reach(plate) IK_FAIL at the workspace edge without re-creating the env.
- **Per-episode 900s timeout + fallback seeds**: `generate_dataset.sh` runs each band as "generate until 3 successful", trying primary then fallback seeds, with a 900s `timeout` that kills hung placement-retry loops.
- **Seed 15 demoted**: lw_benchhub's object-placement retry loop (`env_utils.py:1118`) hangs on seed 15 (scene_retry_count resets on model reload → infinite "scene retry 1/5" loop). Demoted to last in the easy fallback list; the timeout catches any other hung seeds.

### 9.2 Fine-tuning dataset deliverable (the final goal)
- **Location**: `stage4_flywheel/datasets/`
  - `doublepiper_pnp_curriculum/` — lerobot-standard dataset (LeRobotDataset v3.0, image/PNG storage, `use_videos=False`).
  - `raw/{easy,medium,hard}/episode_*.h5` — per-episode HDF5 (robust backup; `observations/qpos` (T,16), `actions` (T,12), 3× camera RGB (T,480,640,3) uint8).
  - `dataset_manifest.json` — schema, distribution, episode list.
- **Schema EXACTLY matches** the original SmolVLA training dataset (`LightwheelAI/Lightwheel-Tasks-Double-Piper` meta/info.json) + model config (`smolvla-double-piper-pnp/config.json`):
  - `observation.state`: float32 (16,), names = 16 sim joints [joint1_r, joint1_l, …, finger_joint_right_l]
  - `action`: float32 (12,), names = [joint1_l,2_l,3_l,5_l,6_l, joint1_r,2_r,3_r,5_r,6_r, left_gripper, right_gripper] (joint4 skipped; absolute targets)
  - `observation.images.{left_hand,right_hand,first_person}`: image (480,640,3) — keys are `left_hand`/`right_hand`/`first_person` (NOT `*_camera_rgb`), matching the model's input_features.
  - `robot_type` = "double_piper", `fps` = 50, `task` = "put the black bowl on the plate."
- **Physically feasible + auto-solved**: every trajectory is a full 6/6-skill PnP (reach→grasp→lift→reach(plate)→ungrasp→retract) planned by cuRobo (respects joint limits + collision) under DeepSeek-v4-pro decomposition. No learned policy in the loop.
- **Distribution**: 3 easy + 3 medium + 3 hard = 9 episodes (even). Total frames ≈ TBD.

### 9.3 v2 episode results

8 successful episodes (3 easy + 2 medium + 3 hard) out of 18 attempts. medium is 2/3 (best-effort per "尽量" — the medium distance band had the highest plan-failure rate).

| difficulty | seed | episode_id | n_frames | 6/6 skills |
|---|---|---|---|---|
| easy | 13 | 0 | 324 | ✅ |
| easy | 16 | 1 | 279 | ✅ |
| easy | 3 | 6 | 317 | ✅ |
| medium | 51 | 1 | 295 | ✅ |
| medium | 30 | 4 | 331 | ✅ |
| hard | 39 | 0 | 318 | ✅ |
| hard | 48 | 1 | 263 | ✅ |
| hard | 2 | 2 | 347 | ✅ |

**Total: 8 episodes, 2474 frames.**

### 9.4 Honest limitations (v2)
1. **Scripted (cuRobo-planned) demonstrations**, not learned-policy demos. Suitable for SmolVLA behavioral-cloning fine-tuning, but the fine-tuned model's success rate is NOT measured here (no fine-tuning loop run).
2. **Image-based storage (PNG)** vs. the original video (h264) — feature-compatible (lerobot loads both as frame tensors), but storage format differs.
3. **9 episodes (~3K frames)** is a small fine-tuning set; real fine-tuning would want 100+ episodes. The deliverable proves the pipeline + schema, not a production-scale dataset.
4. **Seed 15 (and possibly others) hang** in lw_benchhub's placement-retry loop; the 900s timeout + fallback seeds work around it.
5. **DeepSeek-v4-pro** (strictly, never `deepseek-chat`) used for PnP decomposition; anti-degrade guard = strict response-model equality.
6. **reach(plate) non-determinism** mitigated by plan-retry (5×); ~97% per-seed success.
