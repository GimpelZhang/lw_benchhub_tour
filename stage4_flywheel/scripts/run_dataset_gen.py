"""Generate one fine-tuning demonstration episode via the DoublePiper PnP pipeline.

Boots Isaac Sim once, builds the DoublePiperKitchenPnpPipeline with a per-seed
scene config, enables per-step dataset recording (state + action + 3 cameras),
runs the full PnP, and saves the trajectory as HDF5.

Usage:
    python run_dataset_gen.py --seed 48 --difficulty hard --episode_id 0 \
        --output_dir /mnt/robot/stage4_flywheel/datasets/raw
"""

import argparse
import json
import os
from pathlib import Path

# AppLauncher MUST be created before importing autosim_examples / isaaclab envs.
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Generate one DoublePiper PnP demonstration episode.")
parser.add_argument("--seed", type=int, required=True, help="Scene seed (controls object placement).")
parser.add_argument("--difficulty", type=str, required=True, choices=["easy", "medium", "hard"])
parser.add_argument("--episode_id", type=int, required=True, help="Episode index within the difficulty band.")
parser.add_argument("--output_dir", type=str, default="/mnt/robot/stage4_flywheel/datasets/raw")
parser.add_argument("--template_config", type=str, default="/mnt/robot/stage4_flywheel/configs/hard_scene.yml")
parser.add_argument("--pipeline_id", type=str, default="AutoSimPipeline-DoublePiperKitchenPnp-v0")
parser.add_argument("--head_view_dir", type=str, default="/mnt/robot/stage4_flywheel/datasets/head_views")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher_args = vars(args_cli)
app_launcher = AppLauncher(app_launcher_args)
simulation_app = app_launcher.app

import sys
import h5py
import numpy as np

sys.path.insert(0, "/mnt/robot/AutoDataGen/source/autosim")
sys.path.insert(0, "/mnt/robot/AutoDataGen/source/autosim_examples")
import autosim_examples  # noqa: F401  (registers pipelines)
from autosim import make_pipeline


def write_scene_config(template_path: str, seed: int, out_path: str) -> None:
    """Materialize a per-seed scene yml from the hard_scene template."""
    text = Path(template_path).read_text()
    # Replace the seed line.
    out_lines = []
    replaced = False
    for line in text.splitlines():
        if line.strip().startswith("seed:"):
            out_lines.append(f"seed: {seed}")
            replaced = True
        else:
            out_lines.append(line)
    if not replaced:
        out_lines.append(f"seed: {seed}")
    Path(out_path).write_text("\n".join(out_lines) + "\n")


def normalize_camera_frame(f) -> np.ndarray:
    """Coerce one camera frame to uint8 [H, W, 3]."""
    if f is None:
        return None
    f = np.asarray(f)
    if f.ndim == 4 and f.shape[0] == 1:
        f = f.squeeze(0)
    if f.dtype in (np.float32, np.float64):
        f = (f * 255).astype(np.uint8) if float(f.max()) <= 1.0 else f.astype(np.uint8)
    if f.ndim == 3 and f.shape[-1] == 4:
        f = f[..., :3]
    return f


def main():
    out_dir = Path(args_cli.output_dir)
    diff_dir = out_dir / args_cli.difficulty
    diff_dir.mkdir(parents=True, exist_ok=True)
    (Path(args_cli.head_view_dir) / args_cli.difficulty).mkdir(parents=True, exist_ok=True)

    # Materialize per-seed scene config.
    scene_cfg_path = diff_dir / f"scene_seed{args_cli.seed}.yml"
    write_scene_config(args_cli.template_config, args_cli.seed, str(scene_cfg_path))

    print(f"====== DATASET GEN: difficulty={args_cli.difficulty} seed={args_cli.seed} "
          f"episode_id={args_cli.episode_id} ======")

    pipeline = make_pipeline(
        args_cli.pipeline_id,
        config_path=str(scene_cfg_path),
        output_dir=args_cli.head_view_dir,
    )
    pipeline._app_launcher_ref = app_launcher
    pipeline._scene_label = f"{args_cli.difficulty}_seed{args_cli.seed}"
    pipeline._run_id = args_cli.episode_id + 1
    pipeline.enable_dataset_recording()

    success = False
    err = None
    try:
        output = pipeline.run()
        success = bool(getattr(output, "success", False))
    except Exception as e:
        err = repr(e)
        print(f"[run_dataset_gen] pipeline.run() raised: {err}")

    rec = pipeline.get_episode_record()
    n_frames = len(rec["states"])
    print(f"[run_dataset_gen] recorded {n_frames} frames; pipeline success={success}; err={err}")

    # Sanity dims.
    state_dim = action_dim = 0
    if n_frames > 0:
        state_dim = int(np.asarray(rec["states"][0]).shape[0])
        action_dim = int(np.asarray(rec["actions"][0]).shape[0])

    # Joint names (for dataset meta).
    try:
        joint_names = list(pipeline._robot.data.joint_names)
    except Exception:
        joint_names = []

    # Save HDF5.
    h5_path = diff_dir / f"episode_{args_cli.episode_id}.h5"
    with h5py.File(h5_path, "w") as h5:
        if n_frames > 0:
            states = np.stack([np.asarray(s, dtype=np.float32) for s in rec["states"]], axis=0)
            actions = np.stack([np.asarray(a, dtype=np.float32) for a in rec["actions"]], axis=0)
            h5.create_dataset("observations/qpos", data=states)
            h5.create_dataset("actions", data=actions)
            for cam_key, cam_frames in (
                ("left_hand_camera_rgb", rec["left_hand_camera_rgb"]),
                ("right_hand_camera_rgb", rec["right_hand_camera_rgb"]),
                ("first_person_camera_rgb", rec["first_person_camera_rgb"]),
            ):
                frames = [normalize_camera_frame(f) for f in cam_frames]
                if any(f is None for f in frames):
                    print(f"[run_dataset_gen] WARNING: camera '{cam_key}' missing for some frames.")
                    continue
                arr = np.stack(frames, axis=0)
                h5.create_dataset(f"observations/{cam_key}", data=arr)
        meta = h5.create_group("meta")
        meta.attrs["seed"] = args_cli.seed
        meta.attrs["difficulty"] = args_cli.difficulty
        meta.attrs["episode_id"] = args_cli.episode_id
        meta.attrs["n_frames"] = n_frames
        meta.attrs["state_dim"] = state_dim
        meta.attrs["action_dim"] = action_dim
        meta.attrs["fps"] = 50
        meta.attrs["task"] = "L90K1PutTheBlackBowlOnThePlate"
        meta.attrs["robot"] = "DoublePiper-Abs"
        meta.attrs["success"] = int(success)
        meta.attrs["error"] = str(err) if err else ""
        if joint_names:
            meta.create_dataset("joint_names", data=np.array(joint_names, dtype="S"))

    summary = {
        "difficulty": args_cli.difficulty,
        "seed": args_cli.seed,
        "episode_id": args_cli.episode_id,
        "n_frames": n_frames,
        "state_dim": state_dim,
        "action_dim": action_dim,
        "success": success,
        "error": err,
        "h5_path": str(h5_path),
        "joint_names": joint_names,
    }
    summary_path = diff_dir / f"episode_{args_cli.episode_id}_summary.json"
    Path(summary_path).write_text(json.dumps(summary, indent=2))
    print(f"[run_dataset_gen] SAVED {h5_path} ({n_frames} frames, state={state_dim}, action={action_dim})")
    print(f"[run_dataset_gen] SUMMARY {summary_path}")

    # Stash a single-line status for the orchestrator to grep.
    print(f"DATASET_GEN_DONE difficulty={args_cli.difficulty} seed={args_cli.seed} "
          f"episode_id={args_cli.episode_id} n_frames={n_frames} success={success}")


if __name__ == "__main__":
    main()
    # Hard exit — simulation_app.close() can hang after the data is already saved.
    # The orchestrator's pkill between episodes cleans up GPU memory.
    import os
    os._exit(0)
