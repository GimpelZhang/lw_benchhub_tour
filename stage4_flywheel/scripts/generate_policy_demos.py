"""Phase 1 Task 1.1 — SmolVLA closed-loop demo generation with _check_task_success self-filter.

Runs N_EPISODES episodes in ONE process (matching lerobot-eval's sequential RNG state, which
is required because `resample_objects_placement_on_reset` uses env RNG state that accumulates
across episodes — running one-episode-per-process gives DIFFERENT placements than lerobot-eval
for the same seed, breaking reproducibility of the 40% rate).

Per episode:
  - PRE-step recording of (state[16], action[12], 3 cameras) — lerobot training convention
  - _check_task_success() at episode end via wrapped_env._env (same condition as env `terminated`)
  - HDF5 saved ONLY if TASK_SUCCESS=True (self-filtering); summary JSON always written
Stops early when TARGET_SUCCESSES reached. os._exit(0) at end (simulation_app.close() hangs).

Env vars: N_EPISODES, START_EPISODE_ID, BAND, MAX_STEPS, TARGET_SUCCESSES.
DO NOT source lerobot_arena_curobo_env.sh (Phase 1 = SmolVLA, no cuRobo).
"""
import os
import json
import h5py
import numpy as np
import torch
from pathlib import Path

N_EPISODES = int(os.environ.get("N_EPISODES", "1"))
START_EPISODE_ID = int(os.environ.get("START_EPISODE_ID", "0"))
BAND = os.environ.get("BAND", "original")
MAX_STEPS = int(os.environ.get("MAX_STEPS", "1000"))
TARGET_SUCCESSES = int(os.environ.get("TARGET_SUCCESSES", "0"))  # 0 = no early stop

from lerobot.configs import parser
from lerobot.configs.eval import EvalPipelineConfig
from lerobot.envs.factory import make_env, make_env_pre_post_processors
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.envs.utils import preprocess_observation, add_envs_task
from lerobot.utils.constants import ACTION
from lerobot.utils.device_utils import get_safe_torch_device
from lerobot.utils.random_utils import set_seed

CAM_KEYS = ("left_hand_camera_rgb", "right_hand_camera_rgb", "first_person_camera_rgb")


def check_task_success(env, env_id: int = 0):
    """Call the env's task-success condition (bowl_in_plate & gripper_obj_far). T3-verified."""
    raw_env = getattr(env, "_env", env)
    task_success = False
    bowl_pos = plate_pos = None
    try:
        arena_env = raw_env.cfg.isaaclab_arena_env
        success_tensor = arena_env.task.check_success_caller(raw_env)
        task_success = bool(success_tensor[env_id].item())
    except Exception as e:
        print(f"[generate_policy_demos] check_success_caller failed: {e!r}; marking task failed.")
        task_success = False
    try:
        bowl_pos = raw_env.scene["akita_black_bowl"].data.root_pos_w[env_id][:3].cpu().tolist()
        plate_pos = raw_env.scene["plate"].data.root_pos_w[env_id][:3].cpu().tolist()
        dist = float(torch.linalg.norm(
            raw_env.scene["akita_black_bowl"].data.root_pos_w[env_id][:3]
            - raw_env.scene["plate"].data.root_pos_w[env_id][:3]
        ))
        print(f"[generate_policy_demos] TASK_SUCCESS={task_success}; "
              f"bowl={[round(x, 3) for x in bowl_pos]}; "
              f"plate={[round(x, 3) for x in plate_pos]}; bowl-plate dist={dist:.4f} m")
    except Exception as e:
        print(f"[generate_policy_demos] TASK_SUCCESS={task_success} (position diagnostic unavailable: {e!r})")
    return task_success, bowl_pos, plate_pos


def capture_camera_frame(cam_obs, cam_key):
    """Extract one (H, W, 3) uint8 frame from the raw isaaclab arena camera_obs dict."""
    frame = cam_obs.get(cam_key) if isinstance(cam_obs, dict) else None
    if frame is None:
        return None
    if isinstance(frame, torch.Tensor):
        frame = frame.detach().cpu().numpy()
    if frame.ndim == 4:
        frame = frame[0]
    if frame.ndim == 3 and frame.shape[-1] == 4:
        frame = frame[..., :3]
    if frame.dtype != np.uint8:
        frame = np.clip(frame, 0, 255).astype(np.uint8)
    return np.ascontiguousarray(frame)


def run_one_episode(env, policy, preprocessor, postprocessor, env_preprocessor, env_postprocessor,
                    ep_seed, ep_id, max_steps, out_dir):
    """Run one SmolVLA closed-loop episode; save HDF5 iff TASK_SUCCESS; always write summary."""
    policy.reset()
    observation, info = env.reset(seed=ep_seed)

    states, actions = [], []
    cam_buffers = {k: [] for k in CAM_KEYS}

    step = 0
    done = False
    last_terminated = False
    while not done and step < max_steps:
        cam_obs = observation.get("camera_obs", {}) if isinstance(observation, dict) else {}
        for cam_key in CAM_KEYS:
            frame = capture_camera_frame(cam_obs, cam_key)
            if frame is None:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cam_buffers[cam_key].append(frame)

        observation = preprocess_observation(observation)
        observation = add_envs_task(env, observation)
        observation = env_preprocessor(observation)
        observation = preprocessor(observation)
        state = observation["observation.state"][0].detach().cpu().numpy()

        with torch.inference_mode():
            action = policy.select_action(observation)
        action = postprocessor(action)
        action_transition = {ACTION: action}
        action_transition = env_postprocessor(action_transition)
        action = action_transition[ACTION]
        action_numpy = action.to("cpu").numpy()  # (1, 12)

        states.append(np.asarray(state, dtype=np.float32).copy())
        actions.append(np.asarray(action_numpy[0], dtype=np.float32).copy())

        observation, reward, terminated, truncated, info = env.step(action_numpy)
        last_terminated = bool(terminated[0])
        done = bool(terminated[0] | truncated[0])
        step += 1
        if step % 100 == 0:
            print(f"[generate_policy_demos] ep{ep_id} step={step} done={done}", flush=True)

    print(f"[generate_policy_demos] ep{ep_id} ended at step={step} terminated={last_terminated}", flush=True)
    # Success flag: use the env's `terminated` (success term, computed DURING the step).
    # NOTE: check_success_caller(raw_env) AFTER the loop reads the AUTO-RESET state (gymnasium
    # VectorEnv auto-resets terminated envs), so it returns False even for genuine successes.
    # last_terminated is the reliable success indicator. (T3's _check_task_success worked because
    # the scripted pipeline drives the raw env directly without the lerobot wrapper's auto-reset.)
    # check_task_success is kept only for position diagnostics (bowl_pos/plate_pos may reflect the
    # reset state, not the episode's final state).
    diag_success, bowl_pos, plate_pos = check_task_success(env)
    task_success = last_terminated
    if task_success and not diag_success:
        print(f"[generate_policy_demos] ep{ep_id} SUCCESS via terminated flag "
              f"(check_task_success diag={diag_success} — expected: post-auto-reset state)", flush=True)
    n_frames = len(states)

    state_dim = int(np.asarray(states[0]).shape[0]) if n_frames > 0 else 0
    action_dim = int(np.asarray(actions[0]).shape[0]) if n_frames > 0 else 0

    h5_path = None
    if task_success and n_frames > 0:
        h5_path = out_dir / f"episode_{ep_id}.h5"
        with h5py.File(h5_path, "w") as h5:
            h5.create_dataset("observations/qpos", data=np.stack(states).astype(np.float32))
            h5.create_dataset("actions", data=np.stack(actions).astype(np.float32))
            for cam_key, frames in cam_buffers.items():
                arr = np.stack(frames)
                h5.create_dataset(f"observations/{cam_key}", data=arr)
            meta = h5.create_group("meta")
            meta.attrs["seed"] = int(ep_seed)
            meta.attrs["band"] = BAND
            meta.attrs["episode_id"] = ep_id
            meta.attrs["n_frames"] = n_frames
            meta.attrs["state_dim"] = state_dim
            meta.attrs["action_dim"] = action_dim
            meta.attrs["fps"] = 50
            meta.attrs["task"] = "L90K1PutTheBlackBowlOnThePlate"
            meta.attrs["robot"] = "DoublePiper-Abs"
            meta.attrs["success"] = 1
        print(f"[generate_policy_demos] SAVED {h5_path} ({n_frames} frames)", flush=True)
    else:
        print(f"[generate_policy_demos] DISCARDED ep{ep_id} (success={task_success}, n_frames={n_frames})", flush=True)

    summary = {
        "band": BAND, "seed": int(ep_seed), "episode_id": ep_id,
        "n_frames": n_frames, "state_dim": state_dim, "action_dim": action_dim,
        "success": bool(task_success), "bowl_pos": bowl_pos, "plate_pos": plate_pos,
        "h5_path": str(h5_path) if h5_path else None,
    }
    (out_dir / f"episode_{ep_id}_summary.json").write_text(json.dumps(summary, indent=2))
    return task_success, n_frames


@parser.wrap()
def main(cfg: EvalPipelineConfig):
    device = get_safe_torch_device(cfg.policy.device, log=True)
    set_seed(cfg.seed)

    print(f"====== POLICY DEMO COLLECTION: n_episodes={N_EPISODES} start_seed={cfg.seed} "
          f"start_ep_id={START_EPISODE_ID} band={BAND} max_steps={MAX_STEPS} "
          f"target_successes={TARGET_SUCCESSES} ======", flush=True)

    envs = make_env(
        cfg.env,
        n_envs=cfg.eval.batch_size,
        use_async_envs=cfg.eval.use_async_envs,
        trust_remote_code=cfg.trust_remote_code,
    )
    env = list(envs.values())[0][0]  # {suite: {0: IsaacLabEnvWrapper}} -> wrapper

    policy = make_policy(cfg=cfg.policy, env_cfg=cfg.env, rename_map=cfg.rename_map)
    policy.eval()

    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=cfg.policy,
        pretrained_path=cfg.policy.pretrained_path,
        preprocessor_overrides={
            "device_processor": {"device": str(policy.config.device)},
            "rename_observations_processor": {"rename_map": cfg.rename_map},
        },
    )
    env_preprocessor, env_postprocessor = make_env_pre_post_processors(
        env_cfg=cfg.env, policy_cfg=cfg.policy
    )

    out_dir = Path(cfg.output_dir) / BAND
    out_dir.mkdir(parents=True, exist_ok=True)

    max_steps = MAX_STEPS
    try:
        ms = env.call("_max_episode_steps")[0]
        if ms and ms > 0:
            max_steps = min(max_steps, int(ms))
    except Exception:
        pass

    success_count = 0
    fail_count = 0
    for i in range(N_EPISODES):
        if TARGET_SUCCESSES > 0 and success_count >= TARGET_SUCCESSES:
            print(f"=== Reached target: {success_count} successes ===", flush=True)
            break
        ep_seed = cfg.seed + i
        ep_id = START_EPISODE_ID + i
        print(f"=== Episode {ep_id}: seed={ep_seed} (successes so far: {success_count}) ===", flush=True)
        try:
            task_success, n_frames = run_one_episode(
                env, policy, preprocessor, postprocessor, env_preprocessor, env_postprocessor,
                ep_seed, ep_id, max_steps, out_dir)
        except Exception as e:
            import traceback
            print(f"  -> CRASH (episode {ep_id}, seed={ep_seed}): {e!r}", flush=True)
            traceback.print_exc()
            task_success, n_frames = False, 0
        if task_success:
            success_count += 1
            print(f"  -> SUCCESS #{success_count} (episode {ep_id}, seed={ep_seed}, n_frames={n_frames})", flush=True)
        else:
            fail_count += 1
            print(f"  -> fail (episode {ep_id}, seed={ep_seed}, n_frames={n_frames})", flush=True)

    print(f"COLLECTION_DONE successes={success_count} fails={fail_count} "
          f"total={success_count + fail_count}", flush=True)


if __name__ == "__main__":
    main()
    # Flush stdout (os._exit skips stdio flushing) then hard-exit.
    import sys as _sys
    _sys.stdout.flush()
    _sys.stderr.flush()
    import os as _os
    _os._exit(0)
